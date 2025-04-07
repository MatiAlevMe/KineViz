import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd # Necesario para leer y procesar datos

# Importar servicios y helpers
from .file_service import FileService
from .study_service import StudyService
from kineviz.ui.widgets import charting # Importar nuestro módulo de gráficos
from kineviz.core.data_processing import file_handlers # Para obtener nombre paciente si es necesario

# Importar reportlab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch # Para tamaños

class AnalysisService:
    def __init__(self, study_service: StudyService, file_service: FileService):
        """
        Inicializa el AnalysisService.

        :param study_service: Instancia de StudyService.
        :param file_service: Instancia de FileService.
        """
        self.study_service = study_service
        self.file_service = file_service

    def get_analysis_parameters(self, study_id: int) -> dict:
        """
        Obtiene los parámetros disponibles para análisis de un estudio, incluyendo cálculos.

        :param study_id: ID del estudio.
        :return: Diccionario con sets de parámetros disponibles
                 {'patients': set(), 'frequencies': set(), 'types': set(), 'periods': set()}
                 Retorna sets vacíos si no se encuentran parámetros o hay error.
        """
        try:
            # Obtener parámetros únicos del FileService
            params = self.file_service.get_unique_study_parameters(study_id)
            # Añadir cálculos fijos
            params['calculations'] = {'Maximo', 'Minimo', 'Rango'}
            return params
        except Exception as e:
            print(f"Error obteniendo parámetros de análisis para estudio {study_id}: {e}")
            # Devolver vacío en caso de error para que la UI no falle
            return {'patients': set(), 'frequencies': set(), 'types': set(), 'periods': set(), 'calculations': set()}

    def _read_processed_file_data(self, file_path: Path) -> pd.DataFrame | None:
        """
        Lee los datos numéricos de un archivo procesado (.txt separado por ';').
        Omite las primeras 4 líneas de encabezado y las últimas 3 de estadísticas.
        Devuelve un DataFrame con los datos numéricos o None si hay error.
        """
        try:
            # Leer todas las líneas primero para poder omitir las últimas
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) <= 7: # 4 header + 3 stats = 7. Necesita al menos 1 fila de datos.
                print(f"Advertencia: Archivo {file_path.name} no contiene suficientes líneas para extraer datos.")
                return None

            # Omitir encabezado y estadísticas
            data_lines = lines[4:-3]

            # Usar pandas para leer los datos, especificando el separador
            # Necesitamos pasar las líneas como un stream o archivo temporal
            from io import StringIO
            data_io = StringIO("".join(data_lines))

            # Leer la tercera línea para obtener los nombres de columna correctos
            col_names = lines[2].strip().split(';')
            # Asegurar que no haya nombres vacíos que pandas pueda interpretar mal
            col_names = [f"col_{i}" if not name else name for i, name in enumerate(col_names)]

            df = pd.read_csv(data_io, sep=';', header=None, names=col_names, na_values=[''], keep_default_na=True)

            # Seleccionar solo columnas numéricas (intentar convertir y ver qué falla)
            numeric_cols = []
            for col in df.columns:
                 # Intentar convertir a numérico, ignorando la columna 'Tiempo' si existe
                 if col.lower() == 'tiempo':
                     numeric_cols.append(col)
                     continue
                 try:
                     pd.to_numeric(df[col])
                     numeric_cols.append(col)
                 except (ValueError, TypeError):
                     pass # Ignorar columnas no numéricas

            return df[numeric_cols]

        except FileNotFoundError:
            print(f"Error: Archivo no encontrado al leer datos: {file_path}")
            return None
        except Exception as e:
            print(f"Error leyendo datos de {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_data_for_parameters(self, study_id: int, parameters: dict) -> dict:
        """
        Obtiene y estructura los datos numéricos de los archivos que coinciden
        con los parámetros seleccionados.

        :param study_id: ID del estudio.
        :param parameters: Diccionario con listas de 'patients', 'frequencies', 'types', 'periods'.
        :return: Diccionario anidado:
                 {
                     'frequency1': {
                         'type1_period1': {
                             'patient1': DataFrame,
                             'patient2': DataFrame, ...
                         }, ...
                     }, ...
                 }
                 Retorna diccionario vacío si no se encuentran datos o hay error.
        """
        structured_data = {}
        study_path = self.file_service._get_study_path(study_id) # Usar método protegido para obtener ruta
        if not study_path:
            return {}

        selected_patients = parameters.get('patients', [])
        selected_frequencies = parameters.get('frequencies', [])
        selected_types = parameters.get('types', [])
        selected_periods = parameters.get('periods', [])

        # Obtener criterios del estudio para construir nombres de archivo
        try:
            study_details = self.study_service.get_study_details(study_id)
            types_list = [t.strip() for t in (study_details.get('test_types') or '').split(',') if t.strip()]
            periods_list = [p.strip() for p in (study_details.get('test_periods') or '').split(',') if p.strip()]
        except Exception as e:
            print(f"Error obteniendo detalles del estudio {study_id} para buscar datos: {e}")
            return {}


        for patient in selected_patients:
            patient_path = study_path / patient
            if not patient_path.is_dir(): continue

            for freq in selected_frequencies:
                freq_path = patient_path / freq
                if not freq_path.is_dir(): continue

                if freq not in structured_data:
                    structured_data[freq] = {}

                # Iterar sobre todos los archivos en la carpeta de frecuencia
                for file_path in freq_path.glob('*.txt'): # Asumiendo extensión .txt para procesados
                    filename = file_path.name

                    # Extraer tipo y periodo del nombre de archivo para comparar
                    # Asume formato PteXX TIPO PERIODO NN_Frecuencia.txt o similar
                    base_name = filename.split(f'_{freq}')[0]
                    parts = base_name.replace('_', ' ').split()

                    file_type = None
                    file_period = None

                    # Lógica de extracción basada en si tipos/periodos están definidos
                    if types_list and periods_list and len(parts) >= 4:
                        if parts[1] in types_list and parts[2] in periods_list:
                            file_type = parts[1]
                            file_period = parts[2]
                        elif parts[1] in periods_list and parts[2] in types_list:
                            file_period = parts[1]
                            file_type = parts[2]
                    elif (types_list or periods_list) and len(parts) >= 3:
                        if types_list and parts[1] in types_list:
                            file_type = parts[1]
                        elif periods_list and parts[1] in periods_list:
                            file_period = parts[1]
                    # Caso sin tipos ni periodos: file_type y file_period permanecen None

                    # Comprobar si el tipo y periodo del archivo coinciden con la selección
                    # Si no hay tipos/periodos seleccionados, se incluyen todos los archivos de esa frecuencia/paciente
                    type_match = (not selected_types) or (file_type in selected_types)
                    period_match = (not selected_periods) or (file_period in selected_periods)

                    if type_match and period_match:
                        # Crear clave combinada para tipo/periodo
                        type_period_key = f"{file_type or 'NT'}_{file_period or 'NP'}" # NT: No Type, NP: No Period

                        if type_period_key not in structured_data[freq]:
                            structured_data[freq][type_period_key] = {}

                        # Leer datos del archivo
                        df_data = self._read_processed_file_data(file_path)
                        if df_data is not None and not df_data.empty:
                            # Acumular datos si ya existe una entrada para este paciente/freq/tipo/periodo
                            # Esto podría pasar si hay múltiples intentos (01, 02, etc.)
                            if patient not in structured_data[freq][type_period_key]:
                                structured_data[freq][type_period_key][patient] = df_data
                            else:
                                # Concatenar DataFrames (ignorar índice para evitar duplicados)
                                structured_data[freq][type_period_key][patient] = pd.concat(
                                    [structured_data[freq][type_period_key][patient], df_data],
                                    ignore_index=True
                                )
                        else:
                             print(f"Advertencia: No se pudieron leer datos válidos de {filename}")


        return structured_data

    def _calculate_statistic(self, df: pd.DataFrame, calculation: str) -> pd.Series | None:
        """Calcula una estadística ('Maximo', 'Minimo', 'Rango') para cada columna numérica del DataFrame."""
        if df is None or df.empty:
            return None

        # Seleccionar solo columnas numéricas (excluir 'Tiempo' si existe)
        numeric_df = df.select_dtypes(include=np.number)
        if 'Tiempo' in numeric_df.columns:
             numeric_df = numeric_df.drop(columns=['Tiempo'])

        if numeric_df.empty:
             return None

        if calculation == "Maximo":
            return numeric_df.max(skipna=True)
        elif calculation == "Minimo":
            return numeric_df.min(skipna=True)
        elif calculation == "Rango":
            return numeric_df.max(skipna=True) - numeric_df.min(skipna=True)
        else:
            print(f"Advertencia: Cálculo no soportado '{calculation}'")
            return None

    def perform_analysis(self, study_id: int, parameters: dict):
        """
        Realiza un análisis basado en los parámetros proporcionados.
        Calcula las estadísticas seleccionadas para los datos agrupados.

        :param study_id: ID del estudio a analizar.
        :param parameters: Diccionario con los parámetros de análisis.
        :return: Diccionario con resultados del análisis, agrupados por
                 frecuencia -> tipo_periodo -> calculo -> paciente -> Serie de resultados.
                 Ej: {'Cinematica': {'CMJ_PRE': {'Maximo': {'P01': pd.Series, 'P02': pd.Series}}}}
        """
        print(f"Realizando análisis para estudio {study_id} con parámetros: {parameters}")
        structured_data = self._get_data_for_parameters(study_id, parameters)
        analysis_results = {}
        selected_calculations = parameters.get('calculations', [])

        if not structured_data:
            print("No se encontraron datos para los parámetros seleccionados.")
            return {}

        for freq, type_period_data in structured_data.items():
            analysis_results[freq] = {}
            for type_period_key, patient_data in type_period_data.items():
                analysis_results[freq][type_period_key] = {}
                for calc in selected_calculations:
                    analysis_results[freq][type_period_key][calc] = {}
                    for patient, df in patient_data.items():
                        stats = self._calculate_statistic(df, calc)
                        if stats is not None:
                            analysis_results[freq][type_period_key][calc][patient] = stats

        print("Análisis completado.")
        return analysis_results


    def generate_report(self, study_id: int, parameters: dict, output_path_str: str):
        """
        Genera un reporte PDF del análisis.

        :param study_id: ID del estudio.
        :param parameters: Parámetros del análisis.
        :param output_path_str: Ruta (string) donde guardar el reporte PDF.
        """
        print(f"Generando reporte para estudio {study_id} en {output_path_str}...")
        output_path = Path(output_path_str)
        output_path.parent.mkdir(parents=True, exist_ok=True) # Asegurar que directorio exista

        # --- Obtener Datos y Detalles ---
        try:
            study_details = self.study_service.get_study_details(study_id)
            study_name = study_details.get('name', f'Estudio {study_id}')
        except Exception as e:
            raise ValueError(f"No se pudieron obtener detalles del estudio {study_id}: {e}")

        # Obtener datos estructurados (agrupados por paciente)
        structured_data = self._get_data_for_parameters(study_id, parameters)
        selected_calculations = parameters.get('calculations', [])
        selected_patients = parameters.get('patients', [])

        if not structured_data:
            raise ValueError("No se encontraron datos para generar el reporte con los parámetros seleccionados.")

        # --- Crear Directorio Temporal para Gráficos ---
        # Usar tempfile para mayor seguridad y limpieza automática si falla
        with tempfile.TemporaryDirectory(prefix=f"kineviz_report_{study_id}_") as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            print(f"Directorio temporal para gráficos: {temp_dir}")

            # --- Configurar PDF con ReportLab ---
            doc = SimpleDocTemplate(output_path_str, pagesize=letter,
                                    leftMargin=0.75*inch, rightMargin=0.75*inch,
                                    topMargin=1*inch, bottomMargin=1*inch)
            styles = getSampleStyleSheet()
            story = []

            # --- Título y Metadatos ---
            story.append(Paragraph(f"Reporte de Análisis - {study_name}", styles['h1']))
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

            # Parámetros Usados
            story.append(Paragraph("<b>Parámetros Seleccionados:</b>", styles['h3']))
            param_text = f"""
                <b>Pacientes:</b> {', '.join(parameters.get('patients',[]))}<br/>
                <b>Frecuencias:</b> {', '.join(parameters.get('frequencies',[]))}<br/>
                <b>Tipos Prueba:</b> {', '.join(parameters.get('types',[]) or ['Todos'])}<br/>
                <b>Periodos Prueba:</b> {', '.join(parameters.get('periods',[]) or ['Todos'])}<br/>
                <b>Cálculos:</b> {', '.join(parameters.get('calculations',[]))}
            """
            story.append(Paragraph(param_text, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            # --- Iterar y Generar Contenido ---
            plot_counter = 0
            for freq, type_period_data in structured_data.items():
                story.append(Paragraph(f"Resultados para Frecuencia: {freq}", styles['h2']))
                story.append(Spacer(1, 0.1*inch))

                for type_period_key, patient_data in type_period_data.items():
                    # Extraer tipo y periodo de la clave
                    tp_parts = type_period_key.split('_')
                    type_str = tp_parts[0] if tp_parts[0] != 'NT' else 'N/A'
                    period_str = tp_parts[1] if tp_parts[1] != 'NP' else 'N/A'
                    story.append(Paragraph(f"Tipo: {type_str}, Periodo: {period_str}", styles['h3']))
                    story.append(Spacer(1, 0.1*inch))

                    # --- Boxplot General por Paciente (para esta freq/tipo/periodo) ---
                    # Necesitamos agrupar todos los valores numéricos por paciente
                    boxplot_data = {}
                    all_numeric_columns = set()
                    for patient, df in patient_data.items():
                        numeric_df = df.select_dtypes(include=np.number)
                        if 'Tiempo' in numeric_df.columns:
                             numeric_df = numeric_df.drop(columns=['Tiempo'])
                        if not numeric_df.empty:
                             # Usar todos los valores de todas las columnas numéricas para el boxplot general
                             boxplot_data[patient] = numeric_df.values.flatten()
                             all_numeric_columns.update(numeric_df.columns)

                    if boxplot_data:
                        plot_counter += 1
                        boxplot_filename = temp_dir / f"boxplot_{plot_counter}.png"
                        charting.create_boxplot(
                            data_dict=boxplot_data,
                            title=f"Distribución General - {freq} ({type_str}/{period_str})",
                            ylabel="Valor Medición",
                            output_path=boxplot_filename
                        )
                        if boxplot_filename.exists():
                            story.append(Image(str(boxplot_filename), width=6*inch, height=4*inch)) # Ajustar tamaño
                            story.append(Spacer(1, 0.2*inch))
                        else:
                             story.append(Paragraph(f"<i>Error generando boxplot {plot_counter}</i>", styles['Italic']))
                    else:
                         story.append(Paragraph("<i>No hay datos suficientes para el boxplot general.</i>", styles['Italic']))


                    # --- Cálculos y Gráficos de Barras ---
                    for calc in selected_calculations:
                        story.append(Paragraph(f"<b>Cálculo: {calc}</b>", styles['Normal']))
                        story.append(Spacer(1, 0.05*inch))

                        calc_results_by_patient = {}
                        valid_columns_for_calc = set()
                        for patient, df in patient_data.items():
                            stats = self._calculate_statistic(df, calc)
                            if stats is not None and not stats.empty:
                                calc_results_by_patient[patient] = stats
                                valid_columns_for_calc.update(stats.index)

                        if calc_results_by_patient:
                            # --- Gráfico de Barras (Promedio por Paciente) ---
                            # Calcular promedio del cálculo para cada paciente sobre todas las columnas válidas
                            avg_calc_per_patient = {
                                patient: results.mean(skipna=True)
                                for patient, results in calc_results_by_patient.items()
                                if results is not None
                            }
                            # Filtrar pacientes sin promedio válido
                            valid_avg_calc = {p: v for p, v in avg_calc_per_patient.items() if pd.notna(v)}

                            if valid_avg_calc:
                                plot_counter += 1
                                barchart_filename = temp_dir / f"barchart_{plot_counter}.png"
                                charting.create_barchart(
                                    data_dict=valid_avg_calc,
                                    title=f"{calc} Promedio - {freq} ({type_str}/{period_str})",
                                    xlabel="Paciente",
                                    ylabel=f"{calc} Promedio",
                                    output_path=barchart_filename
                                )
                                if barchart_filename.exists():
                                    story.append(Image(str(barchart_filename), width=6*inch, height=4*inch))
                                    story.append(Spacer(1, 0.1*inch))
                                else:
                                     story.append(Paragraph(f"<i>Error generando barchart {plot_counter}</i>", styles['Italic']))
                            else:
                                 story.append(Paragraph(f"<i>No hay datos suficientes para el gráfico de barras de {calc}.</i>", styles['Italic']))


                            # --- Tabla de Resultados Detallados ---
                            # Crear tabla con pacientes como filas y columnas de medición como columnas
                            if valid_columns_for_calc:
                                sorted_columns = sorted(list(valid_columns_for_calc))
                                table_data = [['Paciente'] + sorted_columns] # Cabecera
                                for patient in selected_patients: # Iterar en orden de selección
                                    if patient in calc_results_by_patient:
                                        results = calc_results_by_patient[patient]
                                        row = [patient] + [f"{results.get(col, 'N/A'):.3f}" if pd.notna(results.get(col)) else 'N/A' for col in sorted_columns]
                                        table_data.append(row)
                                    # else: # Opcional: añadir fila indicando que no hay datos
                                    #     table_data.append([patient] + ['N/A'] * len(sorted_columns))

                                if len(table_data) > 1: # Si hay datos además de la cabecera
                                    table = Table(table_data, hAlign='LEFT')
                                    table.setStyle(TableStyle([
                                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                    ]))
                                    story.append(table)
                                    story.append(Spacer(1, 0.2*inch))
                                else:
                                     story.append(Paragraph(f"<i>No hay resultados detallados para {calc}.</i>", styles['Italic']))
                            else:
                                 story.append(Paragraph(f"<i>No hay columnas válidas para mostrar resultados detallados de {calc}.</i>", styles['Italic']))

                        else:
                            story.append(Paragraph(f"<i>No se pudieron calcular resultados para {calc}.</i>", styles['Italic']))
                        story.append(Spacer(1, 0.1*inch)) # Espacio después de cada cálculo

                    story.append(Spacer(1, 0.2*inch)) # Espacio después de cada tipo/periodo

            # --- Construir PDF ---
            try:
                 doc.build(story)
                 print(f"Reporte PDF generado exitosamente en {output_path}")
            except Exception as build_e:
                 print(f"Error construyendo el PDF: {build_e}")
                 raise # Relanzar error de construcción

        # El directorio temporal se limpia automáticamente al salir del 'with'

    # --- Métodos para Gestión de Reportes ---

    def list_reports(self, study_id: int) -> list[dict]:
        """
        Lista los archivos PDF de reportes generados para un estudio.

        :param study_id: ID del estudio.
        :return: Lista de diccionarios, cada uno con 'name' y 'path' del reporte.
                 Retorna lista vacía si no hay reportes o hay error.
        """
        reports = []
        try:
            study_path = self.file_service._get_study_path(study_id)
            if not study_path: return []

            reports_dir = study_path / "reportes"
            if reports_dir.exists() and reports_dir.is_dir():
                for item in reports_dir.glob("*.pdf"):
                    if item.is_file():
                        reports.append({'name': item.name, 'path': str(item)})
                # Ordenar por nombre (o fecha si se extrae del nombre)
                reports.sort(key=lambda x: x['name'], reverse=True)
        except Exception as e:
            print(f"Error listando reportes para estudio {study_id}: {e}")
        return reports

    def delete_report(self, report_path_str: str):
        """
        Elimina un archivo de reporte específico.

        :param report_path_str: Ruta completa (string) del archivo PDF a eliminar.
        :raises FileNotFoundError: Si el archivo no existe.
        :raises OSError: Si ocurre un error al eliminar.
        """
        report_path = Path(report_path_str)
        if not report_path.exists():
            raise FileNotFoundError(f"El archivo de reporte no existe: {report_path}")
        if not report_path.is_file():
            raise ValueError(f"La ruta no es un archivo: {report_path}")

        try:
            report_path.unlink()
            print(f"Reporte eliminado: {report_path}")
        except OSError as e:
            print(f"Error al eliminar el reporte {report_path}: {e}")
            raise
