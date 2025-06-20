import os
import shutil
import logging # Importar logging
from pathlib import Path
from tkinter import messagebox
from kineviz.core.backup_manager import create_backup # Import for automatic backups
# Importar validador a nivel de módulo
from kineviz.ui.utils.validators import validate_filename_for_study_criteria

# Asume que StudyRepository está disponible para obtener detalles del estudio si es necesario
from typing import Dict, Set, Tuple, List, Optional # Añadir tipos necesarios
from kineviz.config.settings import AppSettings # Import AppSettings
from kineviz.core.undo_manager import UndoManager # Import UndoManager
from kineviz.utils.paths import get_application_base_dir # Import for application base directory
# O que se pasa la ruta base de los estudios.
logger = logging.getLogger(__name__) # Logger para este módulo
# Por simplicidad inicial, asumiremos que la estructura de carpetas es conocida.

class FileService:
    def __init__(self, study_service, settings: AppSettings):
        """
        Inicializa el FileService.

        :param study_service: Una instancia de StudyService para obtener detalles del estudio.
        :param settings: Una instancia de AppSettings.
        """
        self.study_service = study_service
        self.settings = settings # Use passed AppSettings instance
        # Use get_application_base_dir() for studies_base_dir
        app_base = get_application_base_dir()
        self.studies_base_dir = app_base / "estudios"
        # Initialize UndoManager, passing the settings instance
        # FileService gets db_path via its study_service instance
        self.undo_manager = UndoManager(settings=self.settings, study_repository_db_path=str(self.study_service.db_path))


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

    def _delete_file_no_backup(self, file_path: Path | str, study_id: int):
        """
        Core logic to delete a file and clean up empty parent directories. No backup trigger here.
        Called by public delete_file or batch operations.
        """
        # Backup is now handled by the public method or batch operation
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

    def delete_file(self, file_path: Path | str, study_id: int):
        """
        Elimina un archivo específico, triggering an automatic backup first.
        Then calls the core logic to delete the file and clean up empty directories.

        :param file_path: Ruta completa (Path o str) del archivo a eliminar.
        :param study_id: ID del estudio al que pertenece el archivo.
        :raises FileNotFoundError: Si el archivo no existe.
        :raises OSError: Si ocurre un error al eliminar el archivo o directorio.
        """
        try:
            create_backup(backup_type='automatic')
        except Exception as e_backup:
            logger.error(f"Error creating automatic backup before deleting file {file_path}: {e_backup}", exc_info=True)
            # Log and continue

        if self.undo_manager.is_undo_enabled():
            if not self.undo_manager.prepare_undo_cache():
                logger.error(f"Failed to prepare undo cache for deleting file {file_path}. Aborting delete operation.")
                raise Exception(f"Failed to prepare undo cache for deleting file {file_path}. Deletion aborted.")
            
            # Cache the item for undo
            # Ensure file_path is a string for cache_item_for_undo
            original_path_str = str(file_path)
            if not self.undo_manager.cache_item_for_undo(original_path_str, "study_file"):
                logger.warning(f"Failed to cache file {original_path_str} for undo. Deletion will proceed but undo might be partial.")
        
        try:
            self._delete_file_no_backup(file_path, study_id)
        except Exception as e:
            logger.error(f"Error during deletion of file {file_path} after undo preparation: {e}", exc_info=True)
            raise

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

            logger.info(f"Tipos de Datos procesadas para {source_file_path.name}: {processed_frequencies or 'Ninguna'}")

    # La definición correcta de add_files_to_study empieza aquí
    def add_files_to_study(self, study_id: int, file_paths: list[str]) -> dict:
        """
        Agrega y procesa una lista de archivos para un estudio específico.

        :param study_id: ID del estudio.
        :param file_paths: Lista de rutas absolutas (como strings) de los archivos a agregar.
        :return: Diccionario con resultados: {'success': count, 'errors': [error_messages]}
        """
        # Ya no es necesario importar pandas aquí, se importa dentro de _process_and_copy_file
        # El validador se importa a nivel de módulo ahora
        import copy # Para deepcopy
        # Importar el nuevo validador de reglas de VI
        from kineviz.ui.utils.validators import validate_files_for_vi_rules


        results = {'success': 0, 'errors': []}
        study_path = self._get_study_path(study_id)
        if not study_path:
            results['errors'].append(f"No se pudo encontrar la ruta para el estudio ID {study_id}.")
            return results

        # Obtener detalles del estudio (VIs, num_subjects, attempts_count)
        try:
            study_details = self.study_service.get_study_details(study_id)
            independent_variables = study_details.get('independent_variables', [])
            max_subjects_allowed = study_details.get('num_subjects')
            max_attempts_allowed = study_details.get('attempts_count')

            if max_subjects_allowed is None or max_attempts_allowed is None:
                 raise ValueError("No se pudo obtener el número máximo de sujetos o intentos del estudio.")

            logger.info(f"Estudio {study_id}: Máx Sujetos={max_subjects_allowed}, Máx Intentos={max_attempts_allowed}")

        except Exception as e:
            error_msg = f"Error al obtener detalles/límites del estudio {study_id}: {e}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
            return results

        # --- Validación Preliminar (Sujetos e Intentos) ---
        try:
            # 1. Obtener estado actual de sujetos e intentos
            existing_subjects_attempts, current_num_subjects, _ = self._get_study_file_details(study_id)
            # Crear una copia profunda para simular la adición
            simulated_subjects_attempts = copy.deepcopy(existing_subjects_attempts)

            # 2. Validar nombres y extraer info de archivos a añadir
            # files_to_process ahora almacenará diccionarios con más info
            files_to_process_info = [] # [{'source_path': Path, 'filename': str, 'subject_id': str, 'attempt_num': int, 'descriptors': List[Optional[str]]}]
            validation_errors = [] # Errores específicos de esta validación
            new_subjects_in_batch = set() # Sujetos nuevos solo en este lote

            for file_path_str in file_paths:
                source_file_path = Path(file_path_str)
                file_name = source_file_path.name
                logger.debug(f"Validando preliminarmente: '{file_name}'")

                is_valid_name, subject_id, extracted_descriptors, attempt_num = validate_filename_for_study_criteria(
                    file_name, independent_variables
                )

                if not is_valid_name or not subject_id or attempt_num is None:
                    msg = f"Nombre de archivo '{file_name}' inválido o no sigue el formato esperado (PteXX ... Sub-valores ... NN)."
                    logger.warning(msg)
                    validation_errors.append(msg)
                    continue # Saltar al siguiente archivo

                # Añadir a la simulación para conteo de sujetos/intentos
                if subject_id not in simulated_subjects_attempts:
                    simulated_subjects_attempts[subject_id] = set()
                    if subject_id not in existing_subjects_attempts and subject_id not in new_subjects_in_batch:
                         new_subjects_in_batch.add(subject_id)
                simulated_subjects_attempts[subject_id].add(attempt_num)
                
                # Guardar info completa para la validación de reglas de VI y procesamiento posterior
                files_to_process_info.append({
                    'source_path': source_file_path,
                    'filename': file_name,
                    'subject_id': subject_id,
                    'attempt_num': attempt_num,
                    'descriptors': extracted_descriptors
                })

            # 3. Realizar validaciones de conteo con los datos simulados
            simulated_num_subjects = len(simulated_subjects_attempts)
            if simulated_num_subjects > max_subjects_allowed:
                msg = (f"Se excede el número máximo de sujetos ({max_subjects_allowed}). "
                       f"Actualmente hay {current_num_subjects}, se intentarían añadir {len(new_subjects_in_batch)} nuevos, "
                       f"resultando en {simulated_num_subjects} total.")
                logger.warning(msg)
                validation_errors.append(msg)

            max_attempts_violation = False
            for subject_id, attempts_set in simulated_subjects_attempts.items():
                if len(attempts_set) > max_attempts_allowed:
                    msg = (f"Se excede el número máximo de intentos ({max_attempts_allowed}) para el sujeto '{subject_id}'. "
                           f"Se encontraron {len(attempts_set)} intentos.")
                    logger.warning(msg)
                    validation_errors.append(msg)
                    max_attempts_violation = True # Marcar que hubo al menos una violación

            # 4. Si hubo errores de validación de conteo, añadirlos a results y retornar
            if validation_errors:
                results['errors'].extend(validation_errors)
                logger.warning(f"Validación de conteo de sujetos/intentos fallida para estudio {study_id}. Errores: {validation_errors}")
                # No retornar aún, continuar con validación de reglas de VI si no hay errores fatales aquí.
                # O sí retornar si es crítico. Por ahora, acumulamos errores.

        except Exception as e_val_count:
            error_msg = f"Error durante la validación de conteo de archivos: {e_val_count}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
            return results # Error crítico, no continuar

        # --- Validación de Reglas de VI (Solo si no hay errores de conteo y hay archivos para procesar) ---
        if not results['errors'] and files_to_process_info:
            try:
                logger.info(f"Iniciando validación de reglas de VI para {len(files_to_process_info)} archivos.")
                existing_files_data = self._get_all_study_files_descriptors(study_id)
                
                # Preparar files_to_add_info para el validador
                # El validador espera: {'subject_id': str, 'descriptors': List[Optional[str]], 'filename': str}
                # files_to_process_info ya tiene 'subject_id', 'descriptors', 'filename'.
                
                vi_rule_errors = validate_files_for_vi_rules(
                    files_to_process_info, # Ya tiene la estructura correcta
                    existing_files_data,
                    independent_variables
                )

                if vi_rule_errors:
                    logger.warning(f"Validación de reglas de VI fallida para estudio {study_id}. Errores específicos:")
                    for err in vi_rule_errors:
                        logger.warning(f"- {err}")
                    # Añadir un error genérico para la UI
                    results['errors'].append("No se cumplen las especificaciones de manejo de sub-valores para el estudio.")
                    return results # Detener procesamiento

            except Exception as e_val_vi:
                error_msg = f"Error durante la validación de reglas de VI: {e_val_vi}"
                logger.error(error_msg, exc_info=True)
                results['errors'].append(error_msg)
                return results # Error crítico

        # --- Procesamiento de Archivos (Solo si TODAS las validaciones pasaron) ---
        if results['errors']: # Si hubo algún error en cualquier validación previa
            logger.warning(f"Procesamiento detenido debido a errores de validación previos para estudio {study_id}.")
            return results

        logger.info(f"Todas las validaciones exitosas. Procesando {len(files_to_process_info)} archivos para estudio {study_id}.")
        for file_info in files_to_process_info:
            source_file_path = file_info['source_path']
            file_name = file_info['filename']
            # subject_id = file_info['subject_id'] # No se usa directamente aquí
            # attempt_num = file_info['attempt_num'] # No se usa directamente aquí
            logger.debug(f"Procesando archivo validado: '{file_name}'")
            try:
                # Procesar y copiar el archivo
                self._process_and_copy_file(study_path, source_file_path)
                results['success'] += 1
                logger.info(f"Archivo '{file_name}' procesado y agregado exitosamente al estudio {study_id}.")

            except FileNotFoundError:
                 error_msg = f"Archivo no encontrado (durante procesamiento): {file_name}"
                 logger.error(error_msg)
                 results['errors'].append(error_msg)
            except ValueError as ve: # Errores de formato durante _process_and_copy
                 error_msg = f"Error de formato procesando '{file_name}': {ve}"
                 logger.warning(error_msg) # Ya se loggeó error en _process_and_copy si ocurrió ahí
                 results['errors'].append(error_msg)
            except Exception as e:
                 # Capturar otros errores durante el procesamiento
                 error_msg = f"Error inesperado procesando '{file_name}': {e}"
                 logger.error(error_msg, exc_info=True) # Usar exc_info para traceback
                 results['errors'].append(error_msg)

        logger.info(f"Proceso de agregado finalizado para estudio {study_id}. Éxitos: {results['success']}, Errores: {len(results['errors'])}.")
        return results

    def _get_study_file_details(self, study_id: int) -> Tuple[Dict[str, Set[int]], int, int]:
        """
        Analiza los archivos procesados de un estudio para obtener detalles sobre sujetos e intentos.

        :param study_id: ID del estudio.
        :return: Tupla:
                 - Dict[str, Set[int]]: Mapeo de subject_id a un set de sus attempt_nums.
                 - int: Número total de sujetos únicos encontrados.
                 - int: Número máximo de intentos encontrado para cualquier sujeto.
        :raises Exception: Si no se pueden obtener los detalles del estudio o VIs.
        """
        subjects_attempts: Dict[str, Set[int]] = {}
        study_path = self._get_study_path(study_id)
        if not study_path:
            return {}, 0, 0 # No hay ruta, no hay detalles

        # Obtener VIs para usar el validador
        try:
            study_details = self.study_service.get_study_details(study_id)
            independent_variables = study_details.get('independent_variables', [])
        except Exception as e:
            logger.error(f"Error al obtener VIs del estudio {study_id} para detalles de archivo: {e}", exc_info=True)
            raise # Relanzar, es necesario para la validación

        processed_folders = ["Cinematica", "Cinetica", "Electromiografica"]
        logger.debug(f"Buscando detalles de archivos para estudio {study_id} en {study_path}")

        for patient_dir in study_path.iterdir():
            if patient_dir.is_dir() and not patient_dir.name.lower() in ["reportes", "temp", "og"]:
                for freq_folder_name in processed_folders:
                    freq_folder_path = patient_dir / freq_folder_name
                    if freq_folder_path.exists() and freq_folder_path.is_dir():
                        for file_path in freq_folder_path.iterdir():
                            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.csv']:
                                filename = file_path.name
                                # Validar y extraer info
                                is_valid, subject_id, _, attempt_num = validate_filename_for_study_criteria(
                                    filename, independent_variables
                                )
                                if is_valid and subject_id and attempt_num is not None:
                                    if subject_id not in subjects_attempts:
                                        subjects_attempts[subject_id] = set()
                                    subjects_attempts[subject_id].add(attempt_num)

        num_unique_subjects = len(subjects_attempts)
        max_attempts_found = 0
        for attempts_set in subjects_attempts.values():
            if len(attempts_set) > max_attempts_found:
                max_attempts_found = len(attempts_set)

        logger.debug(f"Detalles encontrados: {num_unique_subjects} sujetos, máx {max_attempts_found} intentos. Data: {subjects_attempts}")
        return subjects_attempts, num_unique_subjects, max_attempts_found

    def _get_all_study_files_descriptors(self, study_id: int) -> Dict[str, List[List[Optional[str]]]]:
        """
        Recopila los sub-valores extraídos de todos los archivos procesados válidos para un estudio.

        :param study_id: ID del estudio.
        :return: Dict mapeando subject_id a una lista de sus listas de sub-valores.
                 Ej: {"Pte01": [["CMJ", "PRE"], ["SJ", "PRE"]]}
        """
        all_files_data: Dict[str, List[List[Optional[str]]]] = {}
        study_path = self._get_study_path(study_id)
        if not study_path:
            return {}

        try:
            study_details = self.study_service.get_study_details(study_id)
            independent_variables = study_details.get('independent_variables', [])
        except Exception as e:
            logger.error(f"Error al obtener VIs del estudio {study_id} para _get_all_study_files_descriptors: {e}", exc_info=True)
            return {} # No se pueden validar nombres sin VIs

        processed_folders = ["Cinematica", "Cinetica", "Electromiografica"]
        for patient_dir in study_path.iterdir():
            if patient_dir.is_dir() and not patient_dir.name.lower() in ["reportes", "temp", "og"]:
                for freq_folder_name in processed_folders:
                    freq_folder_path = patient_dir / freq_folder_name
                    if freq_folder_path.exists() and freq_folder_path.is_dir():
                        for file_path in freq_folder_path.iterdir():
                            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.csv']:
                                filename = file_path.name
                                is_valid, subject_id, extracted_descriptors, _ = validate_filename_for_study_criteria(
                                    filename, independent_variables
                                )
                                if is_valid and subject_id:
                                    if subject_id not in all_files_data:
                                        all_files_data[subject_id] = []
                                    all_files_data[subject_id].append(extracted_descriptors)
        return all_files_data

    def get_unique_study_parameters(self, study_id: int) -> dict:
        """
        Obtiene conjuntos de parámetros únicos (pacientes, frecuencias, sub-valores por VI)
        basados en los archivos procesados válidos de un estudio.

        :param study_id: ID del estudio.
        :return: Diccionario {'patients': set(), 'frequencies': set(), 'descriptors_by_vi': dict{int: set()}}
                 o un diccionario vacío si hay error o no hay archivos.
                 'descriptors_by_vi' mapea el índice de la VI (0-based) a un set de sub-valores únicos encontrados para esa posición.
        """
        # Ya no se necesita obtener_nombre_paciente aquí
        # from kineviz.core.data_processing.file_handlers import obtener_nombre_paciente

        study_path = self._get_study_path(study_id)
        if not study_path:
            # Devolver estructura vacía esperada
            return {'patients': set(), 'frequencies': set(), 'descriptors_by_vi': {}}

        # Obtener estructura de VIs para validación y referencia
        try:
            study_details = self.study_service.get_study_details(study_id)
            # Obtener la estructura de VIs
            independent_variables = study_details.get('independent_variables', [])
            num_vis = len(independent_variables)
        except Exception as e:
            logger.error(f"Error al obtener VIs del estudio {study_id} para parámetros: {e}", exc_info=True)
            # Devolver estructura vacía esperada
            return {'patients': set(), 'frequencies': set(), 'descriptors_by_vi': {}}

        # Inicializar estructura de parámetros
        parameters = {
            'patients': set(),
            'frequencies': set(),
            'descriptors_by_vi': {i: set() for i in range(num_vis)} # Inicializar sets por posición de VI
        }
        logger.debug(f"Buscando parámetros únicos para estudio {study_id} en {study_path} con {num_vis} VIs")
        processed_folders = ["Cinematica", "Cinetica", "Electromiografica"]

        # 1. Iterar para encontrar pacientes existentes (basado en carpetas)
        for patient_dir in study_path.iterdir():
            # Ignorar carpetas especiales y archivos a nivel de estudio
            if patient_dir.is_dir() and not patient_dir.name.lower() in ["reportes", "temp", "og"]:
                patient_name = patient_dir.name
                # No añadir frecuencia aquí todavía. Se añadirá solo si se encuentra un archivo válido.
                # has_any_freq_folder = False
                # for freq_folder_name in processed_folders:
                #     freq_folder_path = patient_dir / freq_folder_name
                #     if freq_folder_path.exists() and freq_folder_path.is_dir():
                #         # parameters['frequencies'].add(freq_folder_name) # NO AÑADIR AQUÍ
                #         has_any_freq_folder = True
                # Añadir paciente si la carpeta del paciente existe (simplificado)
                # La lógica de si tiene archivos válidos se maneja en el paso 2
                if patient_dir.exists() and patient_dir.is_dir():
                    parameters['patients'].add(patient_name)

        # 2. Iterar de nuevo para encontrar frecuencias y sub-valores por posición *solo* de archivos válidos
        patients_found_step1 = list(parameters['patients'])
        parameters['patients'] = set() # Resetear, se añadirán solo si tienen archivos válidos
        parameters['frequencies'] = set() # Resetear

        logger.debug(f"Paso 2: Validando archivos para pacientes {patients_found_step1} en frecuencias {processed_folders}")
        for patient_name in patients_found_step1:
            patient_dir = study_path / patient_name
            if not patient_dir.is_dir(): continue

            for freq_folder_name in processed_folders:
                 freq_folder_path = patient_dir / freq_folder_name
                 if freq_folder_path.exists() and freq_folder_path.is_dir():
                     logger.debug(f"Escaneando carpeta: {freq_folder_path}")
                     for file_path in freq_folder_path.iterdir():
                         if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.csv']:
                             filename = file_path.name
                             logger.debug(f"Validando archivo: {filename}")
                             # Validar nombre usando la estructura de VIs y desempaquetar los 4 valores
                             is_valid_name, _, extracted_descriptors, _ = validate_filename_for_study_criteria(
                                 filename, independent_variables
                             )
                             # Solo necesitamos is_valid_name y extracted_descriptors aquí
                             logger.debug(f"Resultado validación para '{filename}': {is_valid_name}, Extraído: {extracted_descriptors}")

                             if is_valid_name:
                                 # Si el archivo es válido, añadir paciente y frecuencia
                                 logger.debug(f"Archivo válido encontrado: {filename}. Añadiendo paciente '{patient_name}' y frecuencia '{freq_folder_name}'.")
                                 parameters['patients'].add(patient_name)
                                 parameters['frequencies'].add(freq_folder_name)

                                 # Añadir sub-valores extraídos (no None) a su posición correspondiente
                                 if len(extracted_descriptors) == num_vis:
                                     for vi_index, descriptor_value in enumerate(extracted_descriptors):
                                         if descriptor_value is not None: # Ignorar los 'Nulo' (representados por None)
                                             if vi_index in parameters['descriptors_by_vi']:
                                                 parameters['descriptors_by_vi'][vi_index].add(descriptor_value)
                                             else:
                                                 # Esto no debería ocurrir si se inicializó correctamente
                                                 logger.warning(f"Índice de VI {vi_index} no encontrado en estructura de parámetros para archivo {filename}.")
                                 else:
                                     # Esto tampoco debería ocurrir si la validación es correcta
                                     logger.warning(f"Número de sub-valores extraídos ({len(extracted_descriptors)}) no coincide con número de VIs ({num_vis}) para archivo válido {filename}.")

        logger.debug(f"Parámetros únicos encontrados: {parameters}")
        return parameters

    def delete_all_files_in_study(self, study_id: int):
        """
        Elimina todos los archivos (originales y procesados) dentro de un estudio específico.
        También limpia las carpetas de frecuencia y paciente si quedan vacías.

        :param study_id: ID del estudio.
        :raises ValueError: Si no se puede obtener la ruta del estudio.
        :raises OSError: Si ocurren errores durante la eliminación.
        """
        try:
            create_backup(backup_type='automatic')
        except Exception as e_backup:
            logger.error(f"Error creating automatic backup before deleting all files in study {study_id}: {e_backup}", exc_info=True)
            # Log and continue

        study_path = self._get_study_path(study_id)
        if not study_path:
            raise ValueError(f"No se pudo obtener la ruta del estudio {study_id} para eliminar archivos.")

        logger.info(f"Iniciando eliminación de todos los archivos en el estudio: {study_path.name} (ID: {study_id})")
        
        files_to_cache_for_undo = []
        # First, identify all files that will be deleted to cache them
        if self.undo_manager.is_undo_enabled():
            frequency_folders_to_scan_for_cache = ["Cinematica", "Cinetica", "Electromiografica", "Desconocida", "OG"]
            for patient_dir_item_cache in study_path.iterdir():
                if patient_dir_item_cache.is_dir() and patient_dir_item_cache.name.lower() not in ["reportes", "temp", "analisis discreto", "analisis continuo"]:
                    patient_path_cache = patient_dir_item_cache
                    for freq_folder_name_cache in frequency_folders_to_scan_for_cache:
                        freq_path_cache = patient_path_cache / freq_folder_name_cache
                        if freq_path_cache.exists() and freq_path_cache.is_dir():
                            for file_item_cache in freq_path_cache.iterdir():
                                if file_item_cache.is_file():
                                    files_to_cache_for_undo.append(file_item_cache)
                elif patient_dir_item_cache.is_file(): # Loose files in study folder
                    files_to_cache_for_undo.append(patient_dir_item_cache)
            
            if not self.undo_manager.prepare_undo_cache():
                logger.error(f"Failed to prepare undo cache for deleting all files in study {study_id}. Aborting delete operation.")
                raise Exception(f"Failed to prepare undo cache for deleting all files in study {study_id}. Deletion aborted.")

            for file_to_cache in files_to_cache_for_undo:
                if not self.undo_manager.cache_item_for_undo(str(file_to_cache), "study_file"):
                    logger.warning(f"Failed to cache file {file_to_cache} for undo during 'delete all files'. Deletion will proceed but undo might be partial.")

        # Now, proceed with deletion
        deleted_files_count = 0
        frequency_folders_to_scan_for_delete = ["Cinematica", "Cinetica", "Electromiografica", "Desconocida", "OG"]
        for patient_dir_item_delete in study_path.iterdir():
            if patient_dir_item_delete.is_dir() and patient_dir_item_delete.name.lower() not in ["reportes", "temp", "analisis discreto", "analisis continuo"]:
                patient_path_delete = patient_dir_item_delete
                logger.debug(f"Procesando carpeta de participante para eliminación: {patient_path_delete.name}")
                
                for freq_folder_name_delete in frequency_folders_to_scan_for_delete:
                    freq_path_delete = patient_path_delete / freq_folder_name_delete
                    if freq_path_delete.exists() and freq_path_delete.is_dir():
                        logger.debug(f"  Escaneando carpeta de frecuencia para eliminación: {freq_path_delete.name}")
                        for file_item_delete in list(freq_path_delete.iterdir()): 
                            if file_item_delete.is_file():
                                try:
                                    file_item_delete.unlink()
                                    deleted_files_count += 1
                                    logger.info(f"    Archivo eliminado: {file_item_delete}")
                                except OSError as e:
                                    logger.error(f"    Error eliminando archivo {file_item_delete}: {e}", exc_info=True)
                        
                        if not any(freq_path_delete.iterdir()): 
                            try:
                                freq_path_delete.rmdir()
                                logger.info(f"  Carpeta de frecuencia vacía eliminada: {freq_path_delete}")
                            except OSError as e:
                                logger.error(f"  Error eliminando carpeta de frecuencia vacía {freq_path_delete}: {e}", exc_info=True)
                
                if not any(patient_path_delete.iterdir()):
                    try:
                        patient_path_delete.rmdir()
                        logger.info(f"Carpeta de participante vacía eliminada: {patient_path_delete}")
                    except OSError as e:
                        logger.error(f"Error eliminando carpeta de participante vacía {patient_path_delete}: {e}", exc_info=True)
            elif patient_dir_item_delete.is_file(): 
                try:
                    patient_dir_item_delete.unlink() 
                    deleted_files_count +=1
                    logger.warning(f"Archivo suelto eliminado de la carpeta del estudio: {patient_dir_item_delete}")
                except OSError as e:
                    logger.error(f"Error eliminando archivo suelto {patient_dir_item_delete} de la carpeta del estudio: {e}", exc_info=True)

        logger.info(f"Eliminación de todos los archivos completada para estudio {study_id}. Total eliminados: {deleted_files_count}.")


    def delete_selected_files(self, study_id: int, file_paths: list[Path]):
        """
        Elimina una lista de archivos específicos y limpia directorios vacíos.

        :param study_id: ID del estudio al que pertenecen los archivos.
        :param file_paths: Lista de objetos Path de los archivos a eliminar.
        :raises Exception: Si ocurre un error durante la eliminación de alguno de los archivos.
        """
        if not file_paths:
            return

        try:
            create_backup(backup_type='automatic')
        except Exception as e_backup:
            logger.error(f"Error creating automatic backup before deleting selected files for study {study_id}: {e_backup}", exc_info=True)
            # Log and continue
            
        if self.undo_manager.is_undo_enabled():
            if not self.undo_manager.prepare_undo_cache():
                logger.error(f"Failed to prepare undo cache for deleting selected files in study {study_id}. Aborting delete operation.")
                raise Exception(f"Failed to prepare undo cache for deleting selected files in study {study_id}. Deletion aborted.")
            
            for file_to_cache in file_paths:
                if not self.undo_manager.cache_item_for_undo(str(file_to_cache), "study_file"):
                    logger.warning(f"Failed to cache file {file_to_cache} for undo during 'delete selected files'. Deletion will proceed but undo might be partial.")

        errors = []
        for file_path in file_paths:
            try:
                self._delete_file_no_backup(file_path, study_id) # Call the no-backup version
                logger.info(f"Archivo {file_path} eliminado como parte de una operación masiva para estudio {study_id}.")
            except Exception as e:
                logger.error(f"Error eliminando archivo {file_path} en operación masiva para estudio {study_id}: {e}", exc_info=True)
                errors.append(f"Error eliminando archivo {file_path.name}: {e}")
        
        if errors:
            # Podríamos acumular errores y lanzar una excepción agregada o solo loguear.
            # Por ahora, lanzamos una excepción general si hubo algún error.
            raise Exception("Ocurrieron errores durante la eliminación masiva de archivos:\n" + "\n".join(errors))


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
