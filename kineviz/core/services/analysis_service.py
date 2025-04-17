import os
import tempfile
import shutil
import logging # Importar logging
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd # Necesario para leer y procesar datos

# Importar servicios y helpers
from .file_service import FileService
from .study_service import StudyService
from kineviz.ui.widgets import charting # Importar nuestro módulo de gráficos
from kineviz.core.data_processing import file_handlers # Para obtener nombre paciente si es necesario
# Importar el validador de nombres de archivo
from kineviz.ui.utils.validators import validate_filename_for_study_criteria

# Importar AppSettings para type hinting
from kineviz.config.settings import AppSettings

# Importar reportlab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch  # Para tamaños
import itertools  # Para combinaciones de descriptores
import json  # Para guardar/cargar configuraciones de análisis
import shutil  # Para eliminar directorios

# Importar scipy para tests estadísticos
try:
    from scipy import stats
except ImportError:
    logger.warning("Scipy no está instalado. Las pruebas estadísticas no estarán disponibles.")
    stats = None


logger = logging.getLogger(__name__)  # Logger para este módulo


class AnalysisService:
    def __init__(self, study_service: StudyService, file_service: FileService, app_settings: AppSettings):
        """
        Inicializa el AnalysisService.

        :param study_service: Instancia de StudyService.
        :param file_service: Instancia de FileService.
        :param app_settings: Instancia de AppSettings para acceder a alias.
        """
        self.study_service = study_service
        self.file_service = file_service
        self.settings = app_settings # Guardar referencia a AppSettings

    def get_analysis_parameters(self, study_id: int) -> dict:
        """
        Obtiene los parámetros disponibles para análisis de un estudio, incluyendo cálculos.

        :param study_id: ID del estudio.
        :return: Diccionario con sets de parámetros disponibles
                 {'patients': set(), 'frequencies': set(), 'descriptors': set(), 'calculations': set()}
                 Retorna sets vacíos si no se encuentran parámetros o hay error.
        """
        try:
            # Obtener parámetros únicos del FileService
            # Obtener parámetros únicos del FileService (ahora incluye 'descriptors')
            params = self.file_service.get_unique_study_parameters(study_id)
            # Añadir cálculos fijos
            params['calculations'] = {'Maximo', 'Minimo', 'Rango'}
            # Asegurar que 'descriptors' exista aunque esté vacío
            if 'descriptors' not in params:
                params['descriptors'] = set()
            return params
        except Exception as e:
            logger.error(f"Error obteniendo parámetros de análisis para estudio {study_id}: {e}", exc_info=True)
            # Devolver vacío en caso de error para que la UI no falle
            return {'patients': set(), 'frequencies': set(), 'descriptors': set(), 'calculations': set()}

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
                logger.warning(f"Archivo {file_path.name} no contiene suficientes líneas para extraer datos.")
                return None

            # Omitir encabezado y estadísticas
            data_lines = lines[4:-3]

            # Usar pandas para leer los datos, especificando el separador
            # Necesitamos pasar las líneas como un stream o archivo temporal
            from io import StringIO
            data_io = StringIO("".join(data_lines))

            # --- Determinar número de columnas de los datos reales ---
            if not data_lines:
                 logger.warning(f"Archivo {file_path.name} no contiene líneas de datos después de quitar cabecera/pie.")
                 return None
            first_data_line_parts = data_lines[0].strip().split(';')
            num_data_cols = len(first_data_line_parts)
            # Add debug for first data line content
            logger.debug(f"Primera línea de datos: '{data_lines[0].strip()}'")
            logger.debug(f"Detectadas {num_data_cols} columnas en la primera línea de datos de {file_path.name}")

            if num_data_cols == 0:
                 logger.warning(f"No se detectaron columnas de datos en {file_path.name}")
                 return None

            # --- Generar nombres de columna basados en la línea 3 (ahora separada por ';') ---
            # Leer la línea de nombres de columna (índice 2)
            col_names_line = lines[2].strip()
            raw_col_names_from_header = col_names_line.split(';')
            logger.debug(f"Nombres crudos leídos de línea 3: {raw_col_names_from_header}")

            # Validar si el número de nombres coincide con el número de columnas de datos
            if len(raw_col_names_from_header) != num_data_cols:
                 logger.warning(f"Discrepancia en {file_path.name}: "
                                f"Nombres en línea 3 ({len(raw_col_names_from_header)}) != "
                                f"Columnas en datos ({num_data_cols}). Se usarán los nombres de la línea 3 truncados/rellenados.")
                 # Podríamos decidir fallar aquí si la discrepancia es un problema grave

            # Sanear nombres de columna leídos para asegurar unicidad y no vacíos
            final_col_names = [] # Renombrado de sanitized_base_names
            counts = {}
            # Sanitize names from the header line
            for i, name in enumerate(raw_col_names_from_header):
                clean_name = name.strip()
                # Handle empty names
                if not clean_name:
                     clean_name = f"Unnamed_{i}" # Usar nombre genérico simple

                # Add suffix if the name is duplicated
                if clean_name in counts:
                    counts[clean_name] += 1
                    unique_name = f"{clean_name}_{counts[clean_name]}"
                else:
                    counts[clean_name] = 0
                    unique_name = clean_name
                final_col_names.append(unique_name)
            logger.debug(f"Nombres saneados ({len(final_col_names)}): {final_col_names}")

            # Ajustar la lista final si hubo discrepancia con num_data_cols
            if len(final_col_names) > num_data_cols:
                 final_col_names = final_col_names[:num_data_cols] # Truncar
            elif len(final_col_names) < num_data_cols:
                 # Pad con nombres genéricos
                 for i in range(len(final_col_names), num_data_cols):
                     final_col_names.append(f"Data_Col_{i}")

            logger.debug(f"Nombres de columna finales ajustados para {file_path.name} ({len(final_col_names)}): {final_col_names}")
            # --- Fin ajuste de nombres ---

            try:
                df = pd.read_csv(data_io, sep=';', header=None, names=final_col_names, na_values=[''], keep_default_na=True)
            except pd.errors.ParserError as pe:
                 # Añadir más contexto al error de pandas
                 logger.error(f"Error de Pandas al parsear {file_path.name} con {len(final_col_names)} columnas esperadas: {pe}", exc_info=True)
                 raise # Relanzar para que se maneje en el bloque exterior

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
            logger.error(f"Archivo no encontrado al leer datos: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error leyendo datos de {file_path.name}: {e}", exc_info=True)
            # import traceback # Ya no es necesario
            # traceback.print_exc() # Reemplazado por exc_info=True
            return None

    def _get_data_for_parameters(self, study_id: int, parameters: dict) -> dict:
        """
        Obtiene y estructura los datos numéricos de los archivos que coinciden
        con los parámetros seleccionados.

        :param study_id: ID del estudio.
        :param parameters: Diccionario con listas de 'patients', 'frequencies', 'descriptors', 'calculations'.
        :return: Diccionario anidado:
                 {
                     'frequency1': {
                         'descriptor_combo_key': { # Clave basada en descriptores encontrados
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
        selected_descriptors = parameters.get('descriptors', []) # Usar 'descriptors'

        # Obtener descriptores definidos del estudio para validación y extracción
        try:
            study_details = self.study_service.get_study_details(study_id)
            descriptors_str = study_details.get('descriptores', '') or ''
            defined_descriptors = [d.strip() for d in descriptors_str.split(',') if d.strip()]
        except Exception as e:
            logger.error(f"Error obteniendo descriptores del estudio {study_id} para buscar datos: {e}", exc_info=True)
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

                    # Validar nombre de archivo ANTES de procesar
                    if not validate_filename_for_study_criteria(filename, defined_descriptors):
                        continue # Omitir archivo si no cumple criterios

                    # Extraer descriptores del nombre de archivo
                    base_name = filename.split(f'_{freq}')[0]
                    parts = base_name.replace('_', ' ').split()
                    file_descriptors = parts[1:-1] # Descriptores están entre PteXX y NN

                    # Comprobar si los descriptores del archivo coinciden con la selección
                    # Si no se seleccionaron descriptores, incluir todos los archivos válidos.
                    # Si se seleccionaron, el archivo debe contener TODOS los seleccionados.
                    descriptors_match = (not selected_descriptors) or \
                                        all(desc in file_descriptors for desc in selected_descriptors)

                    if descriptors_match:
                        # Crear clave combinada para los descriptores encontrados en el archivo,
                        # ordenados alfabéticamente para consistencia.
                        descriptor_key = "_".join(sorted(file_descriptors)) if file_descriptors else "NoDesc"

                        if descriptor_key not in structured_data[freq]:
                            structured_data[freq][descriptor_key] = {}

                        # Leer datos del archivo
                        df_data = self._read_processed_file_data(file_path)
                        if df_data is not None and not df_data.empty:
                            # Acumular datos si ya existe una entrada para este paciente/freq/descriptor_key
                            if patient not in structured_data[freq][descriptor_key]:
                                structured_data[freq][descriptor_key][patient] = df_data
                            else:
                                # Concatenar DataFrames
                                structured_data[freq][descriptor_key][patient] = pd.concat(
                                    [structured_data[freq][descriptor_key][patient], df_data],
                                    ignore_index=True
                                )
                        else:
                             logger.warning(f"No se pudieron leer datos válidos de {filename}")

        return structured_data

    def _calculate_statistic(self, df: pd.DataFrame, calculation: str) -> pd.Series | None:
        """Calcula una estadística ('Maximo', 'Minimo', 'Rango') para cada columna numérica del DataFrame."""
        if df is None or df.empty:
            return None

        # Seleccionar solo columnas numéricas (excluir 'Tiempo' si existe)
        numeric_df = df.select_dtypes(include=np.number)
        if 'Tiempo' in numeric_df.columns:
             numeric_df = numeric_df.drop(columns=['Tiempo'])

        # Devolver None si no quedan columnas numéricas O si todas las celdas son NaN
        if numeric_df.empty or numeric_df.isnull().all().all():
             return None

        if calculation == "Maximo":
            return numeric_df.max(skipna=True)
        elif calculation == "Minimo":
            return numeric_df.min(skipna=True)
        elif calculation == "Rango":
            return numeric_df.max(skipna=True) - numeric_df.min(skipna=True)
        else:
            logger.warning(f"Cálculo no soportado '{calculation}'")
            return None

    def perform_analysis(self, study_id: int, parameters: dict):
        """
        Realiza un análisis basado en los parámetros proporcionados.
        Calcula las estadísticas seleccionadas para los datos agrupados.

        :param study_id: ID del estudio a analizar.
        :param parameters: Diccionario con los parámetros de análisis ('patients', 'frequencies', 'descriptors', 'calculations').
        :return: Diccionario con resultados del análisis, agrupados por
                 frecuencia -> descriptor_key -> calculo -> paciente -> Serie de resultados.
                 Ej: {'Cinematica': {'CMJ_PRE': {'Maximo': {'P01': pd.Series, 'P02': pd.Series}}}}
        """
        logger.info(f"Realizando análisis para estudio {study_id} con parámetros: {parameters}")
        structured_data = self._get_data_for_parameters(study_id, parameters)
        analysis_results = {}
        selected_calculations = parameters.get('calculations', [])

        if not structured_data:
            logger.warning(f"No se encontraron datos para los parámetros de análisis seleccionados en estudio {study_id}.")
            return {}

        for freq, descriptor_data in structured_data.items():
            analysis_results[freq] = {}
            for descriptor_key, patient_data in descriptor_data.items():
                analysis_results[freq][descriptor_key] = {}
                for calc in selected_calculations:
                    analysis_results[freq][descriptor_key][calc] = {}
                    for patient, df in patient_data.items():
                        stats = self._calculate_statistic(df, calc)
                        if stats is not None:
                            analysis_results[freq][descriptor_key][calc][patient] = stats

        logger.info(f"Análisis completado para estudio {study_id}.")
        return analysis_results


    def generate_report(self, study_id: int, parameters: dict, output_path_str: str):
        """
        Genera un reporte PDF del análisis.

        :param study_id: ID del estudio.
        :param parameters: Parámetros del análisis.
        :param output_path_str: Ruta (string) donde guardar el reporte PDF.
        """
        logger.info(f"Generando reporte para estudio {study_id} en {output_path_str}...")
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
            logger.debug(f"Directorio temporal para gráficos: {temp_dir}")

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
            # Mostrar alias para descriptores seleccionados
            selected_descriptors_orig = parameters.get('descriptors', [])
            selected_descriptors_display = [
                self.settings.get_descriptor_alias(d) or d for d in selected_descriptors_orig
            ]
            param_text = f"""
                <b>Pacientes:</b> {', '.join(parameters.get('patients',[]))}<br/>
                <b>Frecuencias:</b> {', '.join(parameters.get('frequencies',[]))}<br/>
                <b>Descriptores:</b> {', '.join(selected_descriptors_display or ['Todos'])}<br/>
                <b>Cálculos:</b> {', '.join(parameters.get('calculations',[]))}
            """
            story.append(Paragraph(param_text, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            # --- Iterar y Generar Contenido ---
            plot_counter = 0
            for freq, descriptor_data in structured_data.items():
                story.append(Paragraph(f"Resultados para Frecuencia: {freq}", styles['h2']))
                story.append(Spacer(1, 0.1*inch))

                for descriptor_key, patient_data in descriptor_data.items():
                    # Obtener alias para cada parte de la clave de descriptor
                    descriptor_parts = descriptor_key.split('_')
                    descriptor_display_parts = [self.settings.get_descriptor_alias(part) or part for part in descriptor_parts]
                    descriptor_display = ', '.join(descriptor_display_parts) if descriptor_key != "NoDesc" else "Sin Descriptores Específicos"
                    story.append(Paragraph(f"Descriptores: {descriptor_display}", styles['h3']))
                    story.append(Spacer(1, 0.1*inch))

                    # --- Boxplot General por Paciente (para esta freq/combinación de descriptores) ---
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
                        # Usar descriptor_display (con alias) en el título del gráfico
                        charting.create_boxplot(
                            data_dict=boxplot_data,
                            title=f"Distribución General - {freq} ({descriptor_display})",
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
                                # Usar descriptor_display (con alias) en el título del gráfico
                                charting.create_barchart(
                                    data_dict=valid_avg_calc,
                                    title=f"{calc} Promedio - {freq} ({descriptor_display})",
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
                 logger.info(f"Reporte PDF generado exitosamente en {output_path}")
            except Exception as build_e:
                 logger.error(f"Error construyendo el PDF para estudio {study_id}: {build_e}", exc_info=True)
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
            logger.error(f"Error listando reportes para estudio {study_id}: {e}", exc_info=True)
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
            logger.info(f"Reporte eliminado: {report_path}")
        except OSError as e:
            logger.error(f"Error al eliminar el reporte {report_path}: {e}", exc_info=True)
            raise

    # --- Métodos para Análisis Discreto (Fase 6) ---

    def get_discrete_analysis_tables_path(self, study_id: int) -> Path | None:
        """
        Obtiene la ruta base donde se guardan las tablas de resumen discreto.

        :param study_id: ID del estudio.
        :return: Path al directorio de tablas o None si no se puede determinar.
        """
        try:
            study_path = self.file_service._get_study_path(study_id)
            if not study_path:
                logger.warning(f"No se pudo obtener la ruta del estudio {study_id} para buscar tablas discretas.")
                return None
            # Asume la estructura definida en generate_discrete_summary_tables
            # Nota: Podríamos hacerlo más robusto guardando esta ruta relativa en config o similar.
            tables_path = study_path / "Analisis Discreto" / "Tablas"
            return tables_path
        except Exception as e:
            logger.error(f"Error obteniendo la ruta de tablas discretas para estudio {study_id}: {e}", exc_info=True)
            return None

    def delete_discrete_summary_table(self, table_path_str: str):
        """
        Elimina un archivo de tabla de resumen discreto específico.

        :param table_path_str: Ruta completa (string) del archivo CSV a eliminar.
        :raises FileNotFoundError: Si el archivo no existe.
        :raises ValueError: Si la ruta no es un archivo.
        :raises OSError: Si ocurre un error al eliminar.
        """
        table_path = Path(table_path_str)
        if not table_path.exists():
            raise FileNotFoundError(f"El archivo de tabla no existe: {table_path}")
        if not table_path.is_file():
            raise ValueError(f"La ruta no es un archivo: {table_path}")
        if not table_path.name.endswith('.csv'):
             raise ValueError(f"El archivo no parece ser una tabla CSV: {table_path}")

        try:
            table_path.unlink()
            logger.info(f"Tabla de resumen discreto eliminada: {table_path}")
            # Opcional: Limpiar directorios vacíos (Frecuencia, Analisis Discreto) si es necesario.
            # Esto requeriría lógica adicional para verificar si las carpetas padre están vacías.
        except OSError as e:
            logger.error(f"Error al eliminar la tabla {table_path}: {e}", exc_info=True)
            raise

    def _extract_stats_from_processed_file(self, file_path: Path, calculation: str) -> list | None:
        """Lee las últimas líneas de un archivo procesado y extrae la fila de datos para el cálculo especificado."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) < 3: # Necesita al menos las 3 líneas de stats
                logger.warning(f"Archivo {file_path.name} no tiene suficientes líneas para extraer estadísticas.")
                return None

            # Buscar la línea del cálculo (Maximo, Minimo, Rango) en las últimas 3 líneas
            calc_line_prefix = f";;{calculation.upper()};"
            for line in reversed(lines[-3:]):
                if line.startswith(calc_line_prefix):
                    # Quitar prefijo y dividir por ';'
                    # Devolver los valores como lista de strings (incluyendo vacíos)
                    return line.strip()[len(calc_line_prefix):].split(';')
            logger.warning(f"No se encontró la línea de cálculo '{calculation}' en {file_path.name}")
            return None
        except Exception as e:
            logger.error(f"Error extrayendo estadísticas de {file_path.name} para cálculo {calculation}: {e}", exc_info=True)
            return None

    def _parse_processed_file_headers(self, file_path: Path) -> tuple[list, list, list] | None:
        """Lee las líneas 1, 2 y 3 (atributos, columnas, unidades) de un archivo procesado."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) < 4: # Necesita num_frames, attr, col, unit
                logger.warning(f"Archivo {file_path.name} no tiene suficientes líneas de cabecera.")
                return None
            # Líneas 1, 2, 3 (índices 1, 2, 3)
            atributos = lines[1].strip().split(';')[3:] # Omitir Frame, SubFrame, Tiempo
            columnas = lines[2].strip().split(';')[3:]
            unidades = lines[3].strip().split(';')[3:]

            # Asegurar que todas las listas tengan la misma longitud (la más larga)
            max_len = max(len(atributos), len(columnas), len(unidades))
            atributos.extend([''] * (max_len - len(atributos)))
            columnas.extend([''] * (max_len - len(columnas)))
            unidades.extend([''] * (max_len - len(unidades)))

            return atributos, columnas, unidades
        except Exception as e:
            logger.error(f"Error parseando cabeceras de {file_path.name}: {e}", exc_info=True)
            return None

    def generate_discrete_summary_tables(self, study_id: int):
        """
        Genera tablas resumen CSV para cálculos discretos (Max, Min, Rango)
        agrupados por frecuencia y combinación de descriptores.
        Enfocado inicialmente en 'Cinematica'.

        :param study_id: ID del estudio.
        :return: Diccionario con rutas de los archivos generados o errores.
                 {'success': [path_str], 'errors': [error_msg]}
        """
        logger.info(f"Iniciando generación de tablas de resumen discreto para estudio {study_id}")
        results = {'success': [], 'errors': []}
        target_frequency = "Cinematica" # Enfocarse en Cinemática por ahora
        calculations = ["Maximo", "Minimo", "Rango"]

        try:
            study_path = self.file_service._get_study_path(study_id)
            if not study_path:
                results['errors'].append(f"No se pudo encontrar la ruta del estudio {study_id}.")
                return results

            study_details = self.study_service.get_study_details(study_id)
            defined_descriptors = [d.strip() for d in (study_details.get('descriptores', '') or '').split(',') if d.strip()]

            # 1. Encontrar y agrupar archivos procesados de Cinemática
            files_by_descriptor_combo = {} # { 'Desc1_Desc2': [path1, path2,...], ... }
            processed_files, _ = self.file_service.get_study_files(
                study_id=study_id,
                page=1,
                per_page=10000, # Obtener todos los archivos
                file_type='Processed',
                frequency=target_frequency
            )

            if not processed_files:
                 results['errors'].append(f"No se encontraron archivos procesados de '{target_frequency}' para el estudio {study_id}.")
                 return results

            for file_info in processed_files:
                file_path = file_info['path']
                filename = file_path.name

                # Validar nombre (ya filtrado por frecuencia, pero re-validar por si acaso)
                if not validate_filename_for_study_criteria(filename, defined_descriptors):
                    logger.warning(f"Omitiendo archivo con nombre inválido: {filename}")
                    continue

                # Extraer descriptores del nombre base
                base_name = filename.split(f'_{target_frequency}')[0]
                parts = base_name.replace('_', ' ').split()
                file_descriptors = sorted(parts[1:-1]) # Descriptores ordenados
                descriptor_key = "_".join(file_descriptors) if file_descriptors else "SinDescriptores"

                if descriptor_key not in files_by_descriptor_combo:
                    files_by_descriptor_combo[descriptor_key] = []
                files_by_descriptor_combo[descriptor_key].append(file_path)

            if not files_by_descriptor_combo:
                 results['errors'].append(f"No se encontraron archivos válidos agrupables por descriptores para '{target_frequency}'.")
                 return results

            # 2. Generar tabla para cada combinación de descriptores y cálculo
            output_base_dir = study_path / "Analisis Discreto" / "Tablas" / target_frequency
            output_base_dir.mkdir(parents=True, exist_ok=True)

            for descriptor_key, file_paths in files_by_descriptor_combo.items():
                if not file_paths: continue

                # Leer cabeceras desde el primer archivo del grupo
                headers = self._parse_processed_file_headers(file_paths[0])
                if not headers:
                    results['errors'].append(f"No se pudieron leer las cabeceras para el grupo '{descriptor_key}'.")
                    continue
                atributos, columnas, unidades = headers
                num_value_cols = len(columnas) # Número de columnas de datos (sin Frame, Sub, Tiempo)

                # Crear MultiIndex para las columnas
                multi_index_tuples = []
                last_attr = ""
                for i in range(num_value_cols):
                    attr = atributos[i] if atributos[i] else last_attr # Propagar atributo si está vacío
                    multi_index_tuples.append((attr, columnas[i], unidades[i])) # Añadir unidad
                    last_attr = attr
                # Crear MultiIndex con tres niveles: Atributo, Columna, Unidad
                column_multi_index = pd.MultiIndex.from_tuples(
                    multi_index_tuples,
                    names=["Atributo", "Columna", "Unidad"]
                )


                for calc in calculations:
                    table_data = []
                    file_basenames = []

                    for file_path in file_paths:
                        stats_row = self._extract_stats_from_processed_file(file_path, calc)
                        if stats_row and len(stats_row) == num_value_cols:
                            table_data.append(stats_row)
                            file_basenames.append(file_path.stem.split(f'_{target_frequency}')[0]) # Nombre base sin frecuencia
                        else:
                            logger.warning(f"Datos de '{calc}' inconsistentes o faltantes en {file_path.name}. Se omitirá del archivo {calc}_{target_frequency}_{descriptor_key}.csv")
                            # Opcional: añadir fila de NaNs?
                            # table_data.append([np.nan] * num_value_cols)
                            # file_basenames.append(file_path.stem.split(f'_{target_frequency}')[0] + " (Error)")

                    if table_data:
                        try:
                            # Crear DataFrame
                            df = pd.DataFrame(table_data, columns=column_multi_index, index=file_basenames)
                            df.index.name = "ARCHIVO"

                            # Convertir a numérico, forzando errores a NaN y usando coma decimal
                            for col in df.columns:
                                 # Intentar reemplazar coma por punto ANTES de convertir
                                 if df[col].dtype == 'object':
                                     df[col] = df[col].str.replace(',', '.', regex=False)
                                 df[col] = pd.to_numeric(df[col], errors='coerce')


                            # Guardar CSV
                            output_filename = f"{calc}_{target_frequency}_{descriptor_key}.csv"
                            output_csv_path = output_base_dir / output_filename
                            df.to_csv(output_csv_path, sep=',', decimal=',', encoding='utf-8')
                            results['success'].append(str(output_csv_path))
                            logger.info(f"Tabla de resumen generada: {output_csv_path}")

                        except Exception as e_df:
                            error_msg = f"Error creando o guardando DataFrame para {calc}_{target_frequency}_{descriptor_key}: {e_df}"
                            logger.error(error_msg, exc_info=True)
                            results['errors'].append(error_msg)
                    else:
                         logger.warning(f"No se encontraron datos válidos para generar la tabla {calc}_{target_frequency}_{descriptor_key}.csv")


        except Exception as e:
            error_msg = f"Error inesperado durante la generación de tablas discretas para estudio {study_id}: {e}"
            logger.critical(error_msg, exc_info=True)
            results['errors'].append(error_msg)

        logger.info(f"Generación de tablas discretas finalizada para estudio {study_id}. Éxitos: {len(results['success'])}, Errores: {len(results['errors'])}")
        return results

    # --- Métodos para Análisis Individual (Fase 6) ---

    def _identify_study_groups(self, study_id: int, frequency: str = "Cinematica") -> tuple[dict[str, str], set[str]]:
        """
        Identifica los grupos únicos basados en descriptores de archivos procesados.

        :param study_id: ID del estudio.
        :param frequency: Frecuencia a considerar (por defecto 'Cinematica').
        :return: Tupla:
                 - Diccionario mapeando nombre base de archivo a su clave de grupo (ej: {'Pte01_Intento1': 'Desc1_Desc2'}).
                 - Set de claves de grupo únicas encontradas (ej: {'Desc1_Desc2', 'Desc1_Desc3'}).
        :raises ValueError: Si no se pueden obtener detalles del estudio o archivos.
        """
        logger.debug(f"Identificando grupos para estudio {study_id}, frecuencia {frequency}")
        groups_by_file_base = {}
        unique_group_keys = set()

        try:
            study_details = self.study_service.get_study_details(study_id)
            if not study_details:
                raise ValueError(f"No se pudieron obtener detalles del estudio {study_id}")
            defined_descriptors = [d.strip() for d in (study_details.get('descriptores', '') or '').split(',') if d.strip()]

            processed_files, _ = self.file_service.get_study_files(
                study_id=study_id,
                page=1,
                per_page=10000, # Obtener todos
                file_type='Processed',
                frequency=frequency
            )

            if not processed_files:
                logger.warning(f"No se encontraron archivos procesados de '{frequency}' para identificar grupos en estudio {study_id}.")
                return {}, set()

            for file_info in processed_files:
                file_path = file_info['path']
                filename = file_path.name

                if not validate_filename_for_study_criteria(filename, defined_descriptors):
                    continue

                # Extraer nombre base y descriptores
                try:
                    base_name = filename.split(f'_{frequency}')[0]
                    parts = base_name.replace('_', ' ').split()
                    # Asumiendo formato PteXX_Desc1_Desc2_..._IntentoNN
                    # O PteXX_IntentoNN si no hay descriptores
                    patient_id = parts[0]
                    attempt_suffix = parts[-1]
                    # Los descriptores son lo que queda en medio
                    file_descriptors = sorted(parts[1:-1])
                    descriptor_key = "_".join(file_descriptors) if file_descriptors else "SinDescriptores"

                    # Usar nombre base sin frecuencia ni extensión como clave
                    file_base_key = file_path.stem.split(f'_{frequency}')[0]

                    groups_by_file_base[file_base_key] = descriptor_key
                    unique_group_keys.add(descriptor_key)
                except IndexError:
                    logger.warning(f"No se pudo parsear el nombre de archivo para extraer grupo: {filename}")
                    continue

            logger.debug(f"Grupos identificados ({len(unique_group_keys)}): {unique_group_keys}")
            return groups_by_file_base, unique_group_keys

        except Exception as e:
            logger.error(f"Error identificando grupos para estudio {study_id}: {e}", exc_info=True)
            raise ValueError(f"Error identificando grupos: {e}")


    def get_discrete_analysis_groups(self, study_id: int, frequency: str = "Cinematica") -> list[str]:
        """
        Obtiene la lista de claves de grupos únicos para análisis discreto.

        :param study_id: ID del estudio.
        :param frequency: Frecuencia a considerar.
        :return: Lista ordenada de claves de grupo únicas (ej: ['Desc1_Desc2', 'SinDescriptores']).
        """
        try:
            _, unique_group_keys = self._identify_study_groups(study_id, frequency)
            # Devolver lista ordenada para consistencia en la UI
            return sorted(list(unique_group_keys))
        except ValueError as e:
            logger.warning(f"No se pudieron obtener grupos para estudio {study_id}: {e}")
            return [] # Devolver vacío si hay error

    def get_common_columns_for_groups(self, study_id: int, frequency: str, calculation: str, group_keys: list[str]) -> list[str]:
        """
        Encuentra las columnas de datos comunes presentes en las tablas de resumen
        discreto para una combinación específica de frecuencia, cálculo y grupos.

        :param study_id: ID del estudio.
        :param frequency: Frecuencia (ej: 'Cinematica').
        :param calculation: Cálculo (ej: 'Maximo').
        :param group_keys: Lista de claves de grupo (ej: ['CMJ_PRE', 'CMJ_POST']).
        :return: Lista de nombres de columnas comunes (formato 'Atributo/Columna/Unidad').
                 Retorna lista vacía si no hay columnas comunes o si algún archivo no existe.
        """
        logger.debug(f"Buscando columnas comunes para estudio {study_id}, freq={frequency}, calc={calculation}, grupos={group_keys}")
        common_columns = None
        tables_path = self.get_discrete_analysis_tables_path(study_id)

        if not tables_path or not group_keys:
            return []

        freq_path = tables_path / frequency
        if not freq_path.exists():
            logger.warning(f"Directorio de frecuencia no encontrado: {freq_path}")
            return []

        for group_key in group_keys:
            table_filename = f"{calculation}_{frequency}_{group_key}.csv"
            table_path = freq_path / table_filename

            if not table_path.exists():
                logger.warning(f"Tabla de resumen no encontrada: {table_path}")
                return [] # Si falta una tabla, no hay columnas comunes

            try:
                # Leer solo las cabeceras para obtener columnas
                # Asumiendo que las primeras 3 filas son Atributo, Columna, Unidad después de la columna índice
                df_header = pd.read_csv(table_path, sep=',', decimal=',', encoding='utf-8', header=[0, 1, 2], index_col=0, nrows=0)
                # Crear nombres combinados 'Atributo/Columna/Unidad'
                current_columns = set([f"{attr}/{col}/{unit}" for attr, col, unit in df_header.columns])

                if common_columns is None:
                    common_columns = current_columns
                else:
                    common_columns.intersection_update(current_columns)

                if not common_columns:
                    logger.warning(f"No se encontraron columnas comunes después de procesar {table_filename}")
                    return [] # Si la intersección es vacía, terminar

            except Exception as e:
                logger.error(f"Error leyendo cabeceras de {table_path}: {e}", exc_info=True)
                return [] # Error al leer una tabla

        if common_columns is None:
            return []

        # Devolver lista ordenada
        return sorted(list(common_columns))

    def perform_individual_analysis(self, study_id: int, config: dict):
        """
        Realiza un análisis individual basado en la configuración, genera un gráfico
        y guarda la configuración.

        :param study_id: ID del estudio.
        :param config: Diccionario con la configuración del análisis:
                       {'name': str, 'frequency': str, 'calculation': str,
                        'column': str, 'groups': list[str],
                        'parametric': bool, 'paired': bool}
        :return: Diccionario con rutas al gráfico y archivo de config generados.
                 {'plot_path': str, 'config_path': str}
        :raises ValueError: Si la configuración es inválida o faltan datos/archivos.
        :raises Exception: Si ocurre un error durante el análisis o graficación.
        """
        logger.info(f"Iniciando análisis individual para estudio {study_id}: {config.get('name', 'N/A')}")

        # --- Validación de Configuración ---
        required_keys = ['name', 'frequency', 'calculation', 'column', 'groups', 'parametric', 'paired']
        if not all(key in config for key in required_keys):
            raise ValueError("Configuración de análisis incompleta.")
        if len(config['groups']) < 2:
            raise ValueError("Se requieren al menos dos grupos para la comparación.")
        if not config['name'] or not config['name'].strip():
             raise ValueError("El nombre del análisis no puede estar vacío.")
        # Validar caracteres inválidos en el nombre para usarlo en rutas
        analysis_name = config['name'].strip()
        invalid_chars = r'<>:"/\|?*'
        if any(char in analysis_name for char in invalid_chars):
            raise ValueError(f"El nombre del análisis contiene caracteres inválidos: {invalid_chars}")


        # --- Preparar Rutas ---
        study_path = self.file_service._get_study_path(study_id)
        if not study_path:
            raise ValueError(f"No se pudo encontrar la ruta del estudio {study_id}.")

        analysis_output_dir = study_path / "Analisis Discreto" / "Individual" / analysis_name
        try:
            analysis_output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"No se pudo crear el directorio de salida para el análisis: {analysis_output_dir}\n{e}")

        plot_path = analysis_output_dir / "boxplot.png"
        config_path = analysis_output_dir / "config.json"

        # --- Leer Datos ---
        frequency = config['frequency']
        calculation = config['calculation']
        target_column_parts = config['column'].split('/') # Atributo/Columna/Unidad
        if len(target_column_parts) != 3:
             raise ValueError(f"Formato de columna inválido: {config['column']}. Se esperaba 'Atributo/Columna/Unidad'.")
        target_multi_index_col = tuple(target_column_parts) # (Atributo, Columna, Unidad)

        data_by_group = []
        group_names = config['groups']
        tables_path = self.get_discrete_analysis_tables_path(study_id)
        freq_path = tables_path / frequency

        # Identificar mapeo archivo -> grupo
        files_to_groups, _ = self._identify_study_groups(study_id, frequency)

        for group_key in group_names:
            table_filename = f"{calculation}_{frequency}_{group_key}.csv"
            table_path = freq_path / table_filename
            if not table_path.exists():
                raise FileNotFoundError(f"No se encontró la tabla de resumen requerida: {table_path}")

            try:
                df = pd.read_csv(table_path, sep=',', decimal=',', encoding='utf-8', header=[0, 1, 2], index_col=0)
                # Verificar si la columna existe
                if target_multi_index_col not in df.columns:
                     raise ValueError(f"La columna '{config['column']}' no se encontró en la tabla {table_filename}")

                # Extraer la serie de datos para la columna y grupo actual
                # Filtrar NaNs
                group_data = df[target_multi_index_col].dropna().tolist()

                # --- Manejo de Datos Pareados ---
                # Si es pareado, necesitamos asegurarnos de que los datos estén alineados por paciente/intento
                # Esto es complejo si los intentos no son consistentes entre grupos.
                # Por ahora, si es pareado, asumimos que el índice (ARCHIVO) representa la unidad de emparejamiento
                # y que todas las tablas tienen los mismos índices en el mismo orden.
                # Una implementación más robusta requeriría un merge explícito.
                if config['paired']:
                     # TODO: Implementar lógica de emparejamiento robusta si es necesario.
                     # Por ahora, simplemente añadimos los datos asumiendo orden consistente.
                     logger.warning("El manejo de datos pareados asume índices consistentes entre tablas. Se requiere verificación.")
                     pass # Continuar con group_data tal cual

                if not group_data:
                     logger.warning(f"No se encontraron datos válidos para el grupo '{group_key}' y columna '{config['column']}' en {table_filename}")
                     # Añadir lista vacía para mantener correspondencia con group_names
                     data_by_group.append([])
                else:
                     data_by_group.append(group_data)

            except Exception as e:
                logger.error(f"Error procesando la tabla {table_path} para el grupo {group_key}: {e}", exc_info=True)
                raise ValueError(f"Error leyendo datos para el grupo {group_key}: {e}")

        # Verificar si tenemos datos para graficar
        if not any(data_by_group):
            raise ValueError("No se encontraron datos válidos en ninguna de las tablas para los grupos y columna seleccionados.")

        # --- Realizar Análisis Estadístico ---
        stats_results = None
        if stats:  # Verificar si scipy.stats está disponible
                try:
                    n_groups = len(data_by_group)
                    is_paired = config['paired']
                    is_parametric = config['parametric']
                    test_name = "N/A"
                    p_value = np.nan

                    if n_groups == 2:
                        group1_data = np.array(data_by_group[0])
                        group2_data = np.array(data_by_group[1])

                        if is_paired:
                            # Asegurar misma longitud para tests pareados
                            min_len = min(len(group1_data), len(group2_data))
                            if min_len < 1:
                                raise ValueError("Datos insuficientes para test pareado.")
                            group1_data = group1_data[:min_len]
                            group2_data = group2_data[:min_len]

                            if is_parametric:
                                test_name = "T-test relacionado"
                                stat, p_value = stats.ttest_rel(group1_data, group2_data, nan_policy='omit')
                            else:
                                test_name = "Wilcoxon signed-rank"
                                # Wilcoxon requiere > 0 diferencias, y maneja NaNs internamente si se usa la versión más reciente
                                try:
                                    stat, p_value = stats.wilcoxon(group1_data, group2_data, nan_policy='omit')
                                except ValueError as e:
                                    logger.warning(f"No se pudo ejecutar Wilcoxon para {analysis_name}: {e}")
                                    p_value = np.nan # Marcar como no calculable
                        else: # Independiente
                            if is_parametric:
                                test_name = "T-test independiente"
                                stat, p_value = stats.ttest_ind(group1_data, group2_data, equal_var=False, nan_policy='omit') # Welch's t-test por defecto
                            else:
                                test_name = "Mann-Whitney U"
                                stat, p_value = stats.mannwhitneyu(group1_data, group2_data, alternative='two-sided', nan_policy='omit')

                    elif n_groups > 2:
                        # Filtrar grupos vacíos antes de pasar a ANOVA/Kruskal
                        valid_data_for_test = [np.array(g) for g in data_by_group if len(g) > 0]
                        if len(valid_data_for_test) < 2:
                            raise ValueError("Se necesitan al menos dos grupos con datos para comparar.")

                        if is_paired: # ANOVA de medidas repetidas / Friedman
                            # Nota: ANOVA de medidas repetidas es más complejo y requiere paquetes como statsmodels o pingouin.
                            # Implementaremos Friedman como alternativa no paramétrica.
                            if is_parametric:
                                test_name = "ANOVA medidas repetidas (NO IMPLEMENTADO)"
                                logger.warning(f"{test_name} para {analysis_name}. Usando Friedman en su lugar.")
                                # Intentar Friedman de todas formas
                                try:
                                    stat, p_value = stats.friedmanchisquare(*valid_data_for_test)
                                    test_name = "Friedman (usado como fallback)"
                                except ValueError as e:
                                    logger.warning(f"No se pudo ejecutar Friedman para {analysis_name}: {e}")
                                    p_value = np.nan
                            else:
                                test_name = "Friedman"
                                try:
                                    stat, p_value = stats.friedmanchisquare(*valid_data_for_test)
                                except ValueError as e:
                                    logger.warning(f"No se pudo ejecutar Friedman para {analysis_name}: {e}")
                                    p_value = np.nan
                        else: # ANOVA de un factor / Kruskal-Wallis
                            if is_parametric:
                                test_name = "ANOVA (un factor)"
                                stat, p_value = stats.f_oneway(*valid_data_for_test)
                            else:
                                test_name = "Kruskal-Wallis"
                                stat, p_value = stats.kruskal(*valid_data_for_test, nan_policy='omit')

                    if not np.isnan(p_value):
                        stats_results = {'test_name': test_name, 'p_value': p_value}
                        logger.info(f"Análisis estadístico para {analysis_name}: {test_name}, p-valor = {p_value:.4f}")
                    else:
                        logger.warning(f"No se pudo calcular p-valor para {analysis_name} con test {test_name}.")

                except ValueError as ve:
                    logger.error(f"Error en datos para análisis estadístico de {analysis_name}: {ve}")
                    # stats_results permanece None
                except Exception as e_stat:
                    logger.error(f"Error inesperado durante análisis estadístico de {analysis_name}: {e_stat}", exc_info=True)
                    # stats_results permanece None
        else:
            logger.warning("Scipy no encontrado. Omitiendo pruebas estadísticas.")

        # --- Generar Gráfico ---
        try:
            # Usar alias para nombres de grupo si están disponibles
            group_display_names = []
            for g_key in group_names:
                    parts = g_key.split('_')
                    aliased_parts = [self.settings.get_descriptor_alias(p) or p for p in parts]
                    display_name = ', '.join(aliased_parts) if g_key != "SinDescriptores" else "Sin Descriptores"
                    group_display_names.append(display_name)

            chart_title = f"{config['calculation']} - {config['column']}\n({analysis_name})"
            chart_ylabel = f"{config['calculation']} ({target_column_parts[2]})" # Usar unidad de la columna

            charting.create_comparison_boxplot(
                data_by_group=data_by_group,
                group_names=group_display_names, # Usar nombres con alias
                title=chart_title,
                ylabel=chart_ylabel,
                output_path=plot_path,
                stats_results=stats_results # Pasar resultados estadísticos (None por ahora)
            )
            logger.info(f"Gráfico boxplot generado en: {plot_path}")
        except Exception as e:
            logger.error(f"Error generando el gráfico para el análisis {analysis_name}: {e}", exc_info=True)
            raise Exception(f"Error generando el gráfico: {e}")

        # --- Guardar Configuración ---
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Configuración de análisis guardada en: {config_path}")
        except Exception as e:
            logger.error(f"Error guardando la configuración del análisis {analysis_name}: {e}", exc_info=True)
            # No relanzar necesariamente, el gráfico ya se generó
            # Podríamos intentar eliminar el gráfico si falla el guardado de config?

        return {'plot_path': str(plot_path), 'config_path': str(config_path)}

    def _get_individual_analysis_base_dir(self, study_id: int) -> Path | None:
        """Obtiene el directorio base para los análisis individuales de un estudio."""
        study_path = self.file_service._get_study_path(study_id)
        if not study_path:
            logger.error(f"No se pudo encontrar la ruta del estudio {study_id} para análisis individual.")
            return None
        return study_path / "Analisis Discreto" / "Individual"

    def get_individual_analysis_path(self, study_id: int, analysis_name: str) -> Path | None:
        """Obtiene la ruta completa al directorio de un análisis individual específico."""
        base_dir = self._get_individual_analysis_base_dir(study_id)
        if not base_dir:
            return None
        # Validar nombre por si acaso (aunque ya se hizo al crear)
        invalid_chars = r'<>:"/\|?*'
        if any(char in analysis_name for char in invalid_chars):
            logger.error(f"Nombre de análisis inválido solicitado: {analysis_name}")
            return None
        return base_dir / analysis_name

    def list_individual_analyses(self, study_id: int) -> list[dict]:
        """
        Lista los análisis individuales guardados para un estudio.

        :param study_id: ID del estudio.
        :return: Lista de diccionarios, cada uno con:
                {'name': str, 'path': Path, 'config': dict, 'mtime': float}
        """
        analyses = []
        base_dir = self._get_individual_analysis_base_dir(study_id)
        if not base_dir or not base_dir.exists():
            return []

        for item_path in base_dir.iterdir():
            if item_path.is_dir():
                analysis_name = item_path.name
                config_path = item_path / "config.json"
                plot_path = item_path / "boxplot.png" # Asumir nombre fijo

                if config_path.exists() and config_path.is_file():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        # Usar mtime del config.json como referencia
                        mtime = config_path.stat().st_mtime
                        analyses.append({
                            'name': analysis_name,
                            'path': item_path,
                            'config': config_data,
                            'mtime': mtime,
                            'plot_path': plot_path # Añadir ruta al gráfico
                        })
                    except json.JSONDecodeError:
                        logger.error(f"Error leyendo config.json para análisis '{analysis_name}' en estudio {study_id}.")
                    except Exception as e:
                        logger.error(f"Error procesando análisis '{analysis_name}' en estudio {study_id}: {e}", exc_info=True)
                else:
                    logger.warning(f"Directorio de análisis '{analysis_name}' encontrado sin config.json en estudio {study_id}.")

        # Ordenar por fecha de modificación (más reciente primero)
        analyses.sort(key=lambda x: x['mtime'], reverse=True)
        return analyses

    def delete_individual_analysis(self, study_id: int, analysis_name: str):
        """
        Elimina la carpeta y contenido de un análisis individual específico.

        :param study_id: ID del estudio.
        :param analysis_name: Nombre del análisis a eliminar.
        :raises ValueError: Si el nombre del análisis es inválido.
        :raises FileNotFoundError: Si el directorio del análisis no existe.
        :raises OSError: Si ocurre un error al eliminar el directorio.
        """
        analysis_dir = self.get_individual_analysis_path(study_id, analysis_name)
        if not analysis_dir:
            # get_individual_analysis_path ya loggea el error si el nombre es inválido
            raise ValueError(f"Nombre de análisis inválido o ruta de estudio no encontrada: {analysis_name}")

        if not analysis_dir.exists():
            raise FileNotFoundError(f"El directorio del análisis no existe: {analysis_dir}")
        if not analysis_dir.is_dir():
            raise ValueError(f"La ruta del análisis no es un directorio: {analysis_dir}")

        try:
            shutil.rmtree(analysis_dir)
            logger.info(f"Análisis individual eliminado: {analysis_dir}")
            # Opcional: Limpiar directorios padre si quedan vacíos ('Individual', 'Analisis Discreto')
        except OSError as e:
            logger.error(f"Error eliminando el directorio del análisis {analysis_dir}: {e}", exc_info=True)
            raise
