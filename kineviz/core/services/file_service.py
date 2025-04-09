import os
import shutil
import logging # Importar logging
from pathlib import Path
from tkinter import messagebox
# Importar validador a nivel de módulo
from kineviz.ui.utils.validators import validate_filename_for_study_criteria

# Asume que StudyRepository está disponible para obtener detalles del estudio si es necesario
# O que se pasa la ruta base de los estudios.
logger = logging.getLogger(__name__) # Logger para este módulo
# Por simplicidad inicial, asumiremos que la estructura de carpetas es conocida.

class FileService:
    def __init__(self, study_service):
        """
        Inicializa el FileService.

        :param study_service: Una instancia de StudyService para obtener detalles del estudio.
        """
        self.study_service = study_service
        # Determinar la ruta raíz del proyecto para construir rutas absolutas
        self.project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.studies_base_dir = self.project_root / "estudios"

    def _get_study_path(self, study_id: int) -> Path | None:
        """Obtiene la ruta de la carpeta de un estudio por su ID."""
        try:
            study_details = self.study_service.get_study_details(study_id)
            study_name = study_details['name']
            return self.studies_base_dir / study_name
        except Exception as e:
            logger.error(f"Error al obtener la ruta del estudio {study_id}: {e}", exc_info=True)
            messagebox.showerror("Error Interno", f"No se pudo encontrar la ruta para el estudio ID {study_id}.")
            return None

    def get_study_files(self, study_id: int, page: int = 1, per_page: int = 10,
                        search_term: str = None, file_type: str = None, frequency: str = None) -> tuple[list, int]:
        """
        Obtiene una lista paginada y filtrada de archivos para un estudio.

        :param study_id: ID del estudio.
        :param page: Número de página (base 1).
        :param per_page: Número de archivos por página.
        :param search_term: Término para buscar en nombre de paciente o archivo (case-insensitive).
        :param file_type: Filtrar por tipo ('Processed', 'Original').
        :param frequency: Filtrar por frecuencia ('Cinematica', 'Cinetica', 'Electromiografica', 'N/A').
        :return: Tupla (lista de archivos en la página, número total de archivos que coinciden con los filtros).
                 Ej: ([{'patient': 'P01', ...}, ...], 53)
        """
        study_path = self._get_study_path(study_id)
        if not study_path or not study_path.exists():
            return [], 0

        all_files = []
        # Definir las carpetas a escanear y sus propiedades
        scan_folders = {
            "Cinematica": {"type": "Processed", "frequency": "Cinematica"},
            "Cinetica": {"type": "Processed", "frequency": "Cinetica"},
            "Electromiografica": {"type": "Processed", "frequency": "Electromiografica"},
            "OG": {"type": "Original", "frequency": "N/A"} # Archivos originales
        }

        # Recorrer pacientes dentro del estudio
        for patient_dir in study_path.iterdir():
            if patient_dir.is_dir() and not patient_dir.name.lower() in ["reportes", "temp"]: # Ignorar carpetas especiales
                patient_name = patient_dir.name
                # Recorrer las carpetas de tipo/frecuencia dentro de cada paciente
                for folder_name, props in scan_folders.items():
                    type_folder_path = patient_dir / folder_name
                    if type_folder_path.exists() and type_folder_path.is_dir():
                        for file_path in type_folder_path.iterdir():
                            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.csv']:
                                all_files.append({ # Usar all_files en lugar de files_list
                                    'patient': patient_name,
                                    'name': file_path.name,
                                    'type': props["type"],
                                    'frequency': props["frequency"],
                                    'path': file_path
                                })

        # --- Filtrado ---
        filtered_files = all_files
        if search_term:
            search_lower = search_term.lower()
            filtered_files = [
                f for f in filtered_files
                if search_lower in f['name'].lower() or search_lower in f['patient'].lower()
            ]
        if file_type and file_type != "Todos":
            filtered_files = [f for f in filtered_files if f['type'] == file_type]
        if frequency and frequency != "Todos":
            filtered_files = [f for f in filtered_files if f['frequency'] == frequency]

        # --- Paginación ---
        total_matching_files = len(filtered_files)
        if page < 1:
            page = 1
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        files_on_page = filtered_files[start_index:end_index]

        return files_on_page, total_matching_files

    def delete_file(self, file_path: Path | str, study_id: int):
        """
        Elimina un archivo específico y limpia directorios vacíos si es necesario.

        :param file_path: Ruta completa (Path o str) del archivo a eliminar.
        :raises FileNotFoundError: Si el archivo no existe.
        :param file_path: Ruta completa (Path o str) del archivo a eliminar.
        :param study_id: ID del estudio al que pertenece el archivo (para obtener ruta base).
        :raises FileNotFoundError: Si el archivo no existe.
        :raises OSError: Si ocurre un error al eliminar el archivo o directorio.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Obtener la ruta base del estudio usando el ID proporcionado
        study_path = self._get_study_path(study_id)
        if not study_path:
             # No lanzar error aquí, pero sí advertir. La limpieza de directorios no funcionará.
             print(f"Advertencia: No se pudo obtener la ruta del estudio {study_id} para la limpieza de directorios de {file_path}")
             # Permitir que la eliminación del archivo continúe si es posible

        if not file_path.exists():
            raise FileNotFoundError(f"El archivo no existe: {file_path}")
        if not file_path.is_file():
             raise ValueError(f"La ruta no es un archivo: {file_path}")

        try:
            file_path.unlink()  # Eliminar el archivo
            logger.info(f"Archivo eliminado: {file_path}")

            # Intentar eliminar directorios padres si están vacíos, hasta la carpeta del estudio
            # Solo proceder si pudimos obtener study_path
            if study_path and study_path.exists():
                parent_dir = file_path.parent
                # Asegurarse de que parent_dir sea subdirectorio de study_path antes de empezar
                if parent_dir.is_relative_to(study_path):
                    while parent_dir.exists() and parent_dir != study_path:
                        try:
                            # Verificar si el directorio está vacío (solo contiene directorios vacíos o ningún archivo)
                            # is_empty = not any(item for item in parent_dir.iterdir() if item.is_file() or (item.is_dir() and any(item.iterdir()))) # Complex check removed
                            # O una forma más simple: verificar si está vacío después de eliminar el archivo
                            is_empty_simple = not any(parent_dir.iterdir())

                            if is_empty_simple:
                                parent_dir.rmdir()
                                logger.info(f"Directorio vacío eliminado: {parent_dir}")
                                parent_dir = parent_dir.parent # Moverse al siguiente nivel superior
                            else:
                                logger.debug(f"Directorio no vacío, deteniendo limpieza: {parent_dir}")
                                break # Detener si el directorio no está vacío
                        except OSError as e:
                            logger.warning(f"No se pudo eliminar o verificar el directorio {parent_dir}: {e}")
                            break # Detener si hay un error (ej. permisos, directorio no vacío)
            else:
                 logger.warning(f"No se pudo determinar la ruta del estudio para la limpieza de directorios de {file_path}")

        except OSError as e:
            logger.error(f"Error al eliminar el archivo {file_path}: {e}", exc_info=True)
            raise # Relanzar la excepción

    # Removed study_id_from_path as it's unreliable and caused errors.
    # study_id should be passed directly to delete_file.

    def _process_and_copy_file(self, study_path: Path, source_file_path: Path):
        """
        Procesa un único archivo: copia a OG, lee secciones, calcula y guarda en carpetas de frecuencia.
        Adaptado de lectura.leer_archivo_csv_o_txt.

        :param study_path: Ruta base de la carpeta del estudio.
        :param source_file_path: Ruta del archivo original a procesar.
        :raises Exception: Si ocurre algún error durante el procesamiento.
        """
        # Importar helpers necesarios aquí para evitar dependencia circular a nivel de módulo
        from kineviz.core.data_processing import directory_manager, processors, file_handlers
        # Importar pandas aquí porque se usa para crear el DataFrame
        import pandas as pd

        # 1. Obtener nombre del paciente
        # Usar el nombre del archivo original para extraer el paciente
        nombre_paciente = file_handlers.obtener_nombre_paciente(source_file_path.name)

        # 2. Crear estructura de paciente si no existe (directory_manager se encarga de exist_ok)
        paciente_path = directory_manager.crear_estructura_paciente(study_path, nombre_paciente)

        # 3. Copiar archivo original a OG
        ruta_og = paciente_path / "OG"
        archivo_og = ruta_og / source_file_path.name
        directory_manager.copiar_archivo_origen(source_file_path, archivo_og)

        # 4. Procesar archivo sección por sección
        with open(source_file_path, 'r', encoding='utf-8') as file: # Asegurar encoding
            processed_frequencies = set() # Para loggear qué frecuencias se procesaron
            while True:
                # Leer la línea de descripción/identificador
                linea_descripcion = file.readline()
                if not linea_descripcion: break # Fin del archivo
                linea_descripcion = linea_descripcion.rstrip("\n") # Quitar salto de línea

                # Leer número de frames (con validación básica)
                linea_num_frames = file.readline()
                if not linea_num_frames: break # EOF inesperado
                linea_num_frames = linea_num_frames.rstrip()
                if not linea_num_frames.isdigit():
                    # Podría ser el inicio de otra sección (ej. "Model Outputs")
                    # Si la línea de descripción anterior era "Model Outputs", esto es esperado.
                    if "Model Outputs" in linea_descripcion:
                         # Asumimos que la siguiente línea es num_frames para Cinemática
                         linea_num_frames = file.readline()
                         if not linea_num_frames: break # EOF
                         linea_num_frames = linea_num_frames.rstrip()
                         if not linea_num_frames.isdigit():
                              raise ValueError(f"Formato inválido después de 'Model Outputs': Se esperaba número de frames, se obtuvo '{linea_num_frames}' en {source_file_path.name}")
                    else:
                         # Si no era "Model Outputs", es un error de formato
                         raise ValueError(f"Formato inválido: Se esperaba número de frames, se obtuvo '{linea_num_frames}' en {source_file_path.name}")

                num_frames = int(linea_num_frames)

                # Generar ruta base para el archivo procesado (sin frecuencia)
                # El nombre final y la carpeta se determinarán en leer_seccion
                ruta_base_procesado = paciente_path / source_file_path.name

                # Leer sección usando file_handlers
                # Pasar el file handle, num_frames, la línea de descripción leída y la ruta base
                try:
                    mediciones, columnas, tipo_frecuencia_determinado = file_handlers.leer_seccion(
                        file,
                        num_frames,
                        linea_descripcion,
                        ruta_base_procesado # Pasamos la ruta base, leer_seccion construye la final
                    )
                    processed_frequencies.add(tipo_frecuencia_determinado)

                    # Calcular estadísticas usando processors si hay datos
                    if mediciones:
                        # La ruta final ahora se construye dentro de leer_seccion
                        nombre_archivo_procesado = ruta_base_procesado.name.replace(".txt", f"_{tipo_frecuencia_determinado}.txt").replace(".csv", f"_{tipo_frecuencia_determinado}.csv")
                        ruta_archivo_seccion_final = paciente_path / tipo_frecuencia_determinado / nombre_archivo_procesado

                        df = pd.DataFrame(mediciones, columns=columnas)
                        # Renombrar columnas duplicadas si existen
                        if df.columns.duplicated().any():
                            df.columns = [f'{col}_{i}' if df.columns.duplicated()[i] else col for i, col in enumerate(df.columns)]

                        maximos, minimos, rangos = processors.calcular_max_min_rango(df, columnas)

                        # Exportar cálculos al archivo ya creado por leer_seccion
                        with open(ruta_archivo_seccion_final, 'a', encoding='utf-8') as output_file:
                            processors.exportar_calculos(output_file, maximos, minimos, rangos)
                    else:
                        logger.warning(f"No se encontraron mediciones en la sección {tipo_frecuencia_determinado} de {source_file_path.name}")

                except Exception as e_seccion:
                     # Loggear error de sección pero continuar si es posible con otras secciones
                     logger.error(f"Error procesando una sección ({num_frames} frames) de {source_file_path.name}: {e_seccion}", exc_info=True)
                     # ¿Cómo avanzar el puntero del archivo si falla la lectura de sección?
                     # Podríamos intentar leer las líneas restantes de esa sección fallida para posicionarnos para la siguiente.
                     # Por ahora, si falla, probablemente el bucle while termine o falle en la siguiente iteración.
                     # Considerar añadir un manejo más robusto para saltar secciones corruptas.
                     raise # Relanzar por ahora para no ocultar el error

            logger.info(f"Frecuencias procesadas para {source_file_path.name}: {processed_frequencies or 'Ninguna'}")


    def add_files_to_study(self, study_id: int, file_paths: list[str]) -> dict:
                    df = pd.DataFrame(mediciones, columns=columnas)
                    # Renombrar columnas duplicadas si existen (aunque no debería pasar con la inserción de 'Tiempo')
                    if df.columns.duplicated().any():
                         df.columns = [f'{col}_{i}' if df.columns.duplicated()[i] else col for i, col in enumerate(df.columns)]

                    maximos, minimos, rangos = processors.calcular_max_min_rango(df, columnas)

                    # Exportar cálculos al mismo archivo
                    with open(ruta_archivo_seccion, 'a') as output_file:
                        processors.exportar_calculos(output_file, maximos, minimos, rangos)
                else:
                     logger.warning(f"No se encontraron mediciones en una sección de {source_file_path.name}")


    def add_files_to_study(self, study_id: int, file_paths: list[str]) -> dict:
        """
        Agrega y procesa una lista de archivos para un estudio específico.

        :param study_id: ID del estudio.
        :param file_paths: Lista de rutas absolutas (como strings) de los archivos a agregar.
        :return: Diccionario con resultados: {'success': count, 'errors': [error_messages]}
        """
        # Ya no es necesario importar pandas aquí, se importa dentro de _process_and_copy_file
        # El validador se importa a nivel de módulo ahora

        results = {'success': 0, 'errors': []}
        study_path = self._get_study_path(study_id)
        if not study_path:
            results['errors'].append(f"No se pudo encontrar la ruta para el estudio ID {study_id}.")
            return results

        # Obtener criterios del estudio para validación
        try:
            study_details = self.study_service.get_study_details(study_id)
            types_str = study_details.get('test_types', '') or ''
            periods_str = study_details.get('test_periods', '') or ''
            valid_types = [t.strip() for t in types_str.split(',') if t.strip()]
            valid_periods = [p.strip() for p in periods_str.split(',') if p.strip()]
        except Exception as e:
            error_msg = f"Error al obtener criterios del estudio {study_id}: {e}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
            return results

        logger.info(f"Iniciando proceso de agregado de {len(file_paths)} archivos al estudio {study_id}.")
        for file_path_str in file_paths:
            source_file_path = Path(file_path_str)
            file_name = source_file_path.name
            try:
                # 1. Validar nombre de archivo
                if not validate_filename_for_study_criteria(file_name, valid_types, valid_periods):
                    raise ValueError(f"Nombre de archivo '{file_name}' no cumple los criterios del estudio.")

                # 2. Procesar y copiar el archivo
                self._process_and_copy_file(study_path, source_file_path)
                results['success'] += 1
                logger.info(f"Archivo '{file_name}' procesado y agregado exitosamente al estudio {study_id}.")

            except FileNotFoundError:
                 error_msg = f"Archivo no encontrado: {file_name}"
                 logger.error(error_msg)
                 results['errors'].append(error_msg)
            except ValueError as ve: # Errores de formato o validación
                 error_msg = f"{file_name}: {ve}"
                 logger.warning(f"Error de validación/formato para {error_msg}")
                 results['errors'].append(error_msg)
            except Exception as e:
                 # Capturar otros errores durante el procesamiento
                 error_msg = f"Error procesando '{file_name}': {e}"
                 logger.error(error_msg, exc_info=True) # Usar exc_info para traceback
                 results['errors'].append(error_msg)
                 # Ya no es necesario traceback.print_exc()

        logger.info(f"Proceso de agregado finalizado para estudio {study_id}. Éxitos: {results['success']}, Errores: {len(results['errors'])}.")
        return results

    def get_unique_study_parameters(self, study_id: int) -> dict:
        """
        Obtiene conjuntos de parámetros únicos (pacientes, frecuencias, tipos, periodos)
        basados en los archivos procesados válidos de un estudio.

        :param study_id: ID del estudio.
        :return: Diccionario {'patients': set(), 'frequencies': set(), 'types': set(), 'periods': set()}
                 o un diccionario vacío si hay error o no hay archivos.
        """
        # El validador se importa a nivel de módulo ahora
        from kineviz.core.data_processing.file_handlers import obtener_nombre_paciente # Necesitamos esta función

        study_path = self._get_study_path(study_id)
        if not study_path:
            return {'patients': set(), 'frequencies': set(), 'types': set(), 'periods': set()}

        # Obtener criterios del estudio para validación de nombres
        try:
            study_details = self.study_service.get_study_details(study_id)
            types_str = study_details.get('test_types', '') or ''
            periods_str = study_details.get('test_periods', '') or ''
            valid_types_list = [t.strip() for t in types_str.split(',') if t.strip()]
            valid_periods_list = [p.strip() for p in periods_str.split(',') if p.strip()]
        except Exception as e:
            logger.error(f"Error al obtener criterios del estudio {study_id} para parámetros: {e}", exc_info=True)
            return {'patients': set(), 'frequencies': set(), 'types': set(), 'periods': set()}

        parameters = {'patients': set(), 'frequencies': set(), 'types': set(), 'periods': set()}
        logger.debug(f"Buscando parámetros únicos para estudio {study_id} en {study_path}")
        processed_folders = ["Cinematica", "Cinetica", "Electromiografica"]

        for patient_dir in study_path.iterdir():
            if patient_dir.is_dir() and not patient_dir.name.lower() in ["reportes", "temp", "og"]:
                patient_name = patient_dir.name
                # No añadir paciente aquí, hacerlo solo si se encuentra un archivo válido dentro
                # has_processed_folder = any((patient_dir / pf).exists() for pf in processed_folders)
                # if has_processed_folder:
                #      parameters['patients'].add(patient_name)

                for freq_folder_name in processed_folders:
                    freq_folder_path = patient_dir / freq_folder_name
                    if freq_folder_path.exists() and freq_folder_path.is_dir():
                        for file_path in freq_folder_path.iterdir():
                            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.csv']:
                                filename = file_path.name
                                # Validar nombre antes de extraer parámetros
                                # Validar nombre ANTES de extraer parámetros y añadir frecuencia/paciente
                                # Esto asegura que solo contamos parámetros de archivos válidos
                                if validate_filename_for_study_criteria(filename, valid_types_list, valid_periods_list):
                                    # Si el archivo es válido, añadir su frecuencia y paciente (si no existe ya)
                                    parameters['frequencies'].add(freq_folder_name)
                                    parameters['patients'].add(patient_name) # Añadir paciente solo si tiene archivos válidos

                                    # Extraer tipo y periodo del nombre (simplificado)
                                    # Asume formato PteXX TIPO PERIODO NN_Frecuencia.ext
                                    base_name = filename.split(f'_{freq_folder_name}')[0]
                                    parts = base_name.replace('_', ' ').split()
                                    if len(parts) == 4:
                                        # Asignar basado en si está en la lista válida
                                        if parts[1] in valid_types_list:
                                            parameters['types'].add(parts[1])
                                        elif parts[1] in valid_periods_list:
                                             parameters['periods'].add(parts[1])

                                        if parts[2] in valid_types_list:
                                            parameters['types'].add(parts[2])
                                        elif parts[2] in valid_periods_list:
                                             parameters['periods'].add(parts[2])
                                    elif len(parts) == 3:
                                         if parts[1] in valid_types_list:
                                             parameters['types'].add(parts[1])
                                         elif parts[1] in valid_periods_list:
                                             parameters['periods'].add(parts[1])
                                    # Ignorar caso de 2 partes (sin tipo/periodo)

        return parameters


# Ejemplo de cómo podría usarse (requiere StudyService y estructura de carpetas)
# if __name__ == '__main__':
#     # Esto es solo para prueba y requiere configuración
#     from kineviz.core.services.study_service import StudyService
#     study_service_instance = StudyService() # Asume que StudyService puede ser instanciado así
#     file_service_instance = FileService(study_service_instance)
#
#     # Reemplazar con un ID de estudio válido existente
#     test_study_id = 1
#
#     print(f"Archivos para estudio ID {test_study_id}:")
#     files = file_service_instance.get_study_files(test_study_id)
#     for f in files:
#         print(f"- Paciente: {f['patient']}, Nombre: {f['name']}, Tipo: {f['type']}, Freq: {f['frequency']}, Path: {f['path']}")
#
#     # Ejemplo de eliminación (¡CUIDADO!)
#     # if files:
#     #     file_to_delete = files[0]['path']
#     #     print(f"\nIntentando eliminar: {file_to_delete}")
#     #     try:
#     #         file_service_instance.delete_file(file_to_delete)
#     #         print("Eliminación exitosa (simulada o real).")
#     #     except Exception as e:
#     #         print(f"Error durante la eliminación: {e}")
