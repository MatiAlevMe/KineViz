import json # Importar json
import logging
from pathlib import Path # Import Path
from kineviz.database.repositories import StudyRepository
from kineviz.core.backup_manager import create_backup # Import for automatic backups
from kineviz.config.settings import AppSettings # Import AppSettings
from kineviz.core.undo_manager import UndoManager, DB_FILENAME # Import UndoManager and DB_FILENAME
from kineviz.utils.paths import get_application_base_dir # Import for base directory

# El validador antiguo se eliminará, la validación se hará en el diálogo/nuevo validador
# from kineviz.ui.utils.validators import validate_study_data

logger = logging.getLogger(__name__)

MAX_PINNED_STUDIES = 5

class StudyService:
    def __init__(self, settings: AppSettings, undo_manager: UndoManager):
        app_base_dir = get_application_base_dir()
        absolute_db_path = app_base_dir / DB_FILENAME
        self.repo = StudyRepository(db_path=str(absolute_db_path))
        self.db_path = str(absolute_db_path) # Expose db_path, ensuring it's the absolute one
        self.settings = settings # Use passed AppSettings instance
        self.undo_manager = undo_manager # Use passed UndoManager instance

    def create_study(self, study_data):
        """
        Crea un nuevo estudio.

        :param study_data: Diccionario con datos del estudio. La validación principal
                           (ej. estructura de VIs) debe hacerse antes de llamar a este método.
                           Se espera que 'independent_variables' y 'aliases' sean estructuras Python.
        :return: ID del estudio creado.
        :raises ValueError: Si la conversión a JSON falla o el nombre ya existe.
        :raises Exception: Para otros errores.
        """
        # La validación principal se hará en el diálogo usando el nuevo validador.
        # Convertir estructuras Python a JSON para almacenamiento en DB.
        try:
            data_for_repo = study_data.copy()
            # Convertir VIs a JSON string. Asumir lista vacía si no existe o no es lista/dict.
            iv_data = study_data.get('independent_variables', [])
            data_for_repo['independent_variables'] = json.dumps(iv_data) if isinstance(iv_data, (list, dict)) else '[]'

            # Convertir Aliases a JSON string. Asumir dict vacío si no existe o no es dict.
            alias_data = study_data.get('aliases', {})
            data_for_repo['aliases'] = json.dumps(alias_data) if isinstance(alias_data, dict) else '{}'

            # Comentario se pasa tal cual (ya es string o None)
            data_for_repo['comentario'] = study_data.get('comentario', None)

        except (json.JSONDecodeError, TypeError) as e: # Capturar TypeError también
            logger.error(f"Error convirtiendo datos a JSON para nuevo estudio '{study_data.get('name', 'N/A')}': {e}", exc_info=True)
            raise ValueError(f"Error interno al procesar datos del estudio (JSON): {e}")

        # Llamar al repositorio para crear
        try:
            study_id = self.repo.create_study(data_for_repo)
            logger.info(f"Estudio {study_id} ('{study_data['name']}') creado en servicio.")
            return study_id
        except ValueError as ve: # Capturar error de nombre duplicado del repo
            logger.warning(f"Error al crear estudio '{study_data['name']}': {ve}")
            raise # Relanzar
        except Exception as e: # Otros errores de DB o creación de carpeta
            logger.error(f"Error inesperado al crear estudio '{study_data['name']}': {e}", exc_info=True)
            raise

    def get_studies(self):
        """
        Obtiene la lista de todos los estudios
        
        :return: Lista de estudios
        """
        studies = self.repo.get_all_studies()
        # Ensure 'comentario' is part of the returned dict, even if None
        return [{'id': s['id'], 'name': s['name'], 'is_pinned': s['is_pinned'], 'comentario': s.get('comentario')} for s in studies]
    
    def get_study_details(self, study_id):
        """
        Obtiene los detalles de un estudio específico
        Obtiene los detalles de un estudio específico, parseando JSON a estructuras Python.

        :param study_id: ID del estudio.
        :return: Diccionario con detalles del estudio. 'independent_variables' será una lista
                 y 'aliases' un diccionario. Si el parseo falla, serán lista/dict vacíos.
        :raises ValueError: Si el estudio no se encuentra.
        :raises Exception: Para otros errores.
        """
        try:
            study_details = self.repo.get_study_by_id(study_id) # Ahora devuelve un dict-like

            # Parsear JSON 'independent_variables' a lista Python
            iv_json = study_details.get('independent_variables')
            try:
                # Usar or '[]' para manejar None o string vacío antes de json.loads
                parsed_ivs = json.loads(iv_json or '[]')
                # Asegurar que sea una lista después del parseo y añadir defaults para nuevas flags
                if isinstance(parsed_ivs, list):
                    for iv in parsed_ivs:
                        if isinstance(iv, dict): # Asegurar que el elemento sea un diccionario
                            iv.setdefault('allows_combination', False)
                            iv.setdefault('is_mandatory', False)
                            # Si allows_combination es False, is_mandatory también debe serlo
                            if not iv['allows_combination']:
                                iv['is_mandatory'] = False
                        else: # Si un elemento no es dict, la estructura está corrupta
                            logger.warning(f"Elemento no diccionario encontrado en 'independent_variables' para estudio {study_id}.")
                            # Podríamos intentar filtrar o marcar como error. Por ahora, se mantendrá si es parte de la lista.
                    study_details['independent_variables'] = parsed_ivs
                else:
                    logger.warning(f"Campo 'independent_variables' para estudio {study_id} no es una lista JSON válida. Usando lista vacía.")
                    study_details['independent_variables'] = []
            except (json.JSONDecodeError, TypeError) as e_iv:
                logger.error(f"Error parseando JSON 'independent_variables' para estudio {study_id}: {e_iv}. Usando lista vacía.", exc_info=True)
                study_details['independent_variables'] = []

            # Parsear JSON 'aliases' a dict Python
            aliases_json = study_details.get('aliases')
            try:
                # Usar or '{}' para manejar None o string vacío antes de json.loads
                study_details['aliases'] = json.loads(aliases_json or '{}')
                # Asegurar que sea un diccionario después del parseo
                if not isinstance(study_details['aliases'], dict):
                     logger.warning(f"Campo 'aliases' para estudio {study_id} no es un objeto JSON válido. Usando dict vacío.")
                     study_details['aliases'] = {}
            except (json.JSONDecodeError, TypeError) as e_al:
                logger.error(f"Error parseando JSON 'aliases' para estudio {study_id}: {e_al}. Usando dict vacío.", exc_info=True)
                study_details['aliases'] = {}

            # Comentario ya es string o None desde el repo
            # study_details['comentario'] = study_details.get('comentario') # No es necesario, ya está

            # Convertir la fila (Row object) a un diccionario estándar antes de devolver
            return dict(study_details)

        except ValueError: # Relanzar error de estudio no encontrado del repo
            raise
        except Exception as e:
            logger.error(f"Error inesperado obteniendo detalles estudio {study_id}: {e}", exc_info=True)
            raise # Relanzar otros errores

    def get_study_comment(self, study_id: int) -> str | None:
        """
        Obtiene el comentario de un estudio específico.

        :param study_id: ID del estudio.
        :return: El comentario como string, o None si no existe o hay error.
        """
        try:
            study_details = self.get_study_details(study_id) # Lanza ValueError si no existe
            return study_details.get('comentario')
        except ValueError: # Estudio no encontrado
            logger.warning(f"Estudio {study_id} no encontrado al obtener comentario.")
            return None
        except Exception as e: # Otros errores inesperados
            logger.error(f"Error inesperado obteniendo comentario para estudio {study_id}: {e}", exc_info=True)
            return None

    def _delete_study_internal(self, study_id: int):
        """
        Internal helper to delete a single study, caching it for undo if enabled.
        Assumes prepare_undo_cache has been called by the public method if part of a batch.
        """
        try:
            study_details = self.repo.get_study_by_id(study_id) # Get details before deletion
            study_name = study_details['name']
            # Ensure studies_base_dir is a Path object
            study_dir_path = Path(self.repo.studies_base_dir) / study_name

            if self.undo_manager.is_undo_enabled():
                if study_dir_path.exists() and study_dir_path.is_dir():
                    if not self.undo_manager.cache_item_for_undo(str(study_dir_path), "study_directory"):
                        # Logged by UndoManager, but we might want to reconsider aborting here in future.
                        logger.warning(f"Failed to cache study directory {study_dir_path} for undo. Deletion will proceed but undo might be partial.")
                else:
                    logger.warning(f"Study directory {study_dir_path} not found or not a directory. Cannot cache for undo. Study ID: {study_id}")
            
            self.repo.delete_study(study_id) # This deletes DB record and directory
            logger.info(f"Study ID {study_id} ('{study_name}') deleted by internal method.")

        except ValueError as ve: # e.g., study not found by get_study_by_id
            logger.error(f"Error in _delete_study_internal for study ID {study_id}: {ve}", exc_info=True)
            raise # Re-raise to be handled by the caller
        except Exception as e:
            logger.error(f"Unexpected error in _delete_study_internal for study ID {study_id}: {e}", exc_info=True)
            raise # Re-raise to be handled by the caller

    def update_study_comment(self, study_id: int, comment: str | None):
        """
        Actualiza solo el comentario de un estudio específico.
        Valida la longitud del comentario (máximo 150 caracteres).

        :param study_id: ID del estudio.
        :param comment: Nuevo comentario (string o None).
        :raises ValueError: Si el comentario excede los 150 caracteres,
                           o si el estudio no se encuentra.
        :raises Exception: Para otros errores de base de datos.
        """
        if comment is not None and len(comment) > 150:
            raise ValueError("El comentario no puede exceder los 150 caracteres.")

        try:
            # Validar que el estudio exista primero (get_study_by_id lo hace)
            self.repo.get_study_by_id(study_id)
            self.repo.update_study_comment(study_id, comment)
            logger.info(f"Comentario actualizado para estudio {study_id}.")
        except ValueError as ve: # Capturar error de estudio no encontrado
            logger.error(f"Error al actualizar comentario para estudio {study_id}: {ve}", exc_info=True)
            raise
        except Exception as e: # Otros errores inesperados
            logger.error(f"Error inesperado actualizando comentario para estudio {study_id}: {e}", exc_info=True)
            raise

    def delete_study(self, study_id):
        """
        Elimina un estudio. Triggers automatic backup and prepares undo cache.
        
        :param study_id: ID del estudio a eliminar
        """
        try:
            create_backup(backup_type='automatic')
        except Exception as e_backup:
            logger.error(f"Error creating automatic backup before deleting study {study_id}: {e_backup}", exc_info=True)
            # Log and continue

        if self.undo_manager.is_undo_enabled():
            if not self.undo_manager.prepare_undo_cache():
                logger.error(f"Failed to prepare undo cache for deleting study {study_id}. Aborting delete operation.")
                # Optionally, raise an exception here to stop the operation
                # For now, if prepare fails, we might still proceed with deletion without undo.
                # Or, more safely, abort:
                raise Exception(f"Failed to prepare undo cache for deleting study {study_id}. Deletion aborted.")

        try:
            self._delete_study_internal(study_id)
        except Exception as e:
            logger.error(f"Error during deletion of study {study_id} after undo preparation: {e}", exc_info=True)
            # If _delete_study_internal fails, the undo cache might be in a prepared state.
            # It will be cleared on the next prepare_undo_cache call.
            raise # Re-raise the exception from _delete_study_internal

    def delete_studies_by_ids(self, study_ids: list[int]):
        """
        Elimina múltiples estudios por sus IDs.
        Itera y llama a delete_study para cada uno para asegurar que la lógica de
        eliminación de carpetas también se ejecute.

        :param study_ids: Lista de IDs de estudios a eliminar.
        :raises Exception: Si ocurre un error durante la eliminación de alguno de los estudios.
        """
        if not study_ids:
            return

        # Single backup and undo prep for the entire batch operation
        try:
            create_backup(backup_type='automatic')
        except Exception as e_backup:
            logger.error(f"Error creating automatic backup before deleting multiple studies: {e_backup}", exc_info=True)
            # Log and continue

        if self.undo_manager.is_undo_enabled():
            if not self.undo_manager.prepare_undo_cache():
                logger.error("Failed to prepare undo cache for deleting multiple studies. Aborting batch delete operation.")
                raise Exception("Failed to prepare undo cache for batch deletion. Operation aborted.")
        
        errors = []
        for study_id in study_ids:
            try:
                self._delete_study_internal(study_id) # Call internal method directly
                logger.info(f"Estudio ID {study_id} processed for batch deletion.")
            except Exception as e:
                logger.error(f"Error deleting study ID {study_id} during batch operation: {e}", exc_info=True)
                errors.append(f"Error deleting study ID {study_id}: {e}")
                # Continue with other studies in the batch
        
        if errors:
            # If any error occurred, the undo cache might be for a partially completed operation.
            # The user should be informed.
            error_message = "Ocurrieron errores durante la eliminación masiva de estudios:\n" + "\n".join(errors)
            logger.error(error_message)
            # Depending on severity, we might want to clear undo cache or leave it.
            # For now, leave it; perform_undo will attempt to restore what it can.
            raise Exception(error_message)
        logger.info(f"Batch deletion of {len(study_ids)} studies completed.")

    def has_studies(self):
        """
        Verifica si existe al menos un estudio en la base de datos.

        :return: True si hay estudios, False en caso contrario.
        """
        # Delega la llamada al repositorio
        return self.repo.count_studies() > 0

    def get_studies_paginated(self, page: int, per_page: int, search_term: str = None):
        """
        Obtiene una lista paginada de estudios, opcionalmente filtrada por término de búsqueda en el nombre.

        :param page: Número de página (base 1).
        :param per_page: Número de estudios por página.
        :param search_term: Término para buscar en el nombre del estudio (opcional).
        :return: Lista de diccionarios de estudios para la página solicitada.
        """
        if page < 1:
            page = 1
        offset = (page - 1) * per_page
        studies = self.repo.get_studies_paginated(limit=per_page, offset=offset, search_term=search_term)
        # Ensure 'comentario' is part of the returned dict
        return [{'id': s['id'], 'name': s['name'], 'is_pinned': s['is_pinned'], 'comentario': s.get('comentario')} for s in studies]


    def get_total_studies_count(self, search_term: str = None):
        """
        Obtiene el número total de estudios, opcionalmente filtrado por término de búsqueda en el nombre.

        :param search_term: Término para buscar en el nombre del estudio (opcional).
        :return: Número total de estudios que coinciden.
        """
        return self.repo.get_total_studies_count(search_term=search_term)

    def update_study(self, study_id: int, study_data: dict):
        """
        Actualiza los datos de un estudio existente, convirtiendo VIs/aliases a JSON.

        :param study_id: ID del estudio a actualizar.
        :param study_data: Diccionario con los nuevos datos del estudio. Se espera que
                           'independent_variables' y 'aliases' sean estructuras Python.
        :raises ValueError: Si la conversión a JSON falla, el estudio no existe o el nombre ya está en uso.
        :raises Exception: Para otros errores.
        """
        # Obtener nombre original ANTES de intentar la actualización en DB
        try:
            original_study = self.get_study_details(study_id) # Lanza ValueError si no existe
            original_name = original_study['name']
        except ValueError:
            raise # Relanzar si el estudio no existe

        # Convertir estructuras Python a JSON para almacenamiento en DB.
        try:
            data_for_repo = study_data.copy()
            # Convertir VIs a JSON string. Asumir lista vacía si no existe o no es lista/dict.
            iv_data = study_data.get('independent_variables', [])
            data_for_repo['independent_variables'] = json.dumps(iv_data) if isinstance(iv_data, (list, dict)) else '[]'

            # Convertir Aliases a JSON string. Asumir dict vacío si no existe o no es dict.
            alias_data = study_data.get('aliases', {})
            data_for_repo['aliases'] = json.dumps(alias_data) if isinstance(alias_data, dict) else '{}'

            # Comentario se pasa tal cual (ya es string o None)
            # Validar longitud del comentario si se está actualizando aquí
            comment_data = study_data.get('comentario', None)
            if comment_data is not None and len(comment_data) > 150:
                raise ValueError("El comentario no puede exceder los 150 caracteres.")
            data_for_repo['comentario'] = comment_data


        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error convirtiendo datos a JSON para actualizar estudio {study_id}: {e}", exc_info=True)
            raise ValueError(f"Error interno al procesar datos del estudio (JSON): {e}")

        # Llamar al repositorio para actualizar
        try:
            self.repo.update_study(study_id, data_for_repo) # Lanza ValueError si no existe o nombre duplicado
            logger.info(f"Estudio {study_id} actualizado en servicio.")
        except ValueError as ve: # Capturar errores de repo (no encontrado, nombre duplicado)
            logger.warning(f"Error de validación/DB al actualizar estudio {study_id}: {ve}")
            raise # Relanzar
        except Exception as e: # Otros errores de DB
            logger.error(f"Error inesperado al actualizar estudio {study_id} en DB: {e}", exc_info=True)
            raise

        # Renombrar carpeta si el nombre cambió y la actualización DB fue exitosa
        new_name = study_data.get('name', '').strip() # Obtener nuevo nombre y limpiar
        if original_name != new_name:
            if not new_name:
                 logger.error(f"Intento de renombrar estudio {study_id} a un nombre vacío. Omitiendo renombrado de carpeta.")
                 # Considerar lanzar un error si la validación previa falló
            else:
                 try:
                     self.repo.rename_study_folder(original_name, new_name)
                 except Exception as e_rename:
                     # Loggear error de renombrado pero no relanzar necesariamente,
                     # ya que la DB se actualizó. Podría requerir intervención manual.
                     logger.error(f"Error al renombrar carpeta del estudio {study_id} de '{original_name}' a '{new_name}': {e_rename}", exc_info=True)
                     # Podríamos añadir un mensaje al usuario aquí
            # Eliminar el 'raise' incorrecto que estaba aquí

    # --- Métodos específicos para Aliases por Estudio ---

    def get_study_aliases(self, study_id: int) -> dict:
        """
        Obtiene el diccionario de alias para un estudio específico.

        :param study_id: ID del estudio.
        :return: Diccionario de alias. Devuelve dict vacío si no se encuentra el estudio o hay error.
        """
        try:
            study_details = self.get_study_details(study_id) # Lanza ValueError si no existe
            # get_study_details ya parsea el JSON y devuelve dict vacío si falla
            return study_details.get('aliases', {})
        except ValueError: # Estudio no encontrado
            logger.warning(f"Estudio {study_id} no encontrado al obtener alias.")
            return {}
        except Exception as e: # Otros errores inesperados
            logger.error(f"Error inesperado obteniendo alias para estudio {study_id}: {e}", exc_info=True)
            return {}

    def update_study_aliases(self, study_id: int, aliases: dict):
        """
        Actualiza solo los alias de un estudio específico en la base de datos.

        :param study_id: ID del estudio.
        :param aliases: Diccionario con los nuevos alias.
        :raises ValueError: Si el estudio no se encuentra o hay error al convertir/guardar.
        :raises Exception: Para otros errores de base de datos.
        """
        if not isinstance(aliases, dict):
            raise ValueError("Los alias deben ser proporcionados como un diccionario.")

        try:
            # Obtener datos actuales para no perder VIs, etc.
            # Esto también valida que el estudio exista
            study_details = self.get_study_details(study_id)

            # Actualizar solo los alias en el diccionario de detalles
            study_details['aliases'] = aliases

            # Llamar a update_study con todos los datos (se encargará de convertir a JSON y guardar)
            # No es necesario renombrar carpeta aquí
            self.update_study(study_id, study_details)
            logger.info(f"Aliases actualizados para estudio {study_id}.")

        except ValueError as ve: # Capturar errores de get_study_details o update_study
            logger.error(f"Error al actualizar alias para estudio {study_id}: {ve}", exc_info=True)
            raise # Relanzar
        except Exception as e: # Otros errores inesperados
            logger.error(f"Error inesperado actualizando alias para estudio {study_id}: {e}", exc_info=True)
            raise

    def toggle_study_pin_status(self, study_id: int) -> bool:
        """
        Cambia el estado de 'pinned' de un estudio.
        No permite pinear más de MAX_PINNED_STUDIES estudios.

        :param study_id: ID del estudio a actualizar.
        :return: True si el estado se cambió, False si se alcanzó el límite de pineados.
        :raises ValueError: Si el estudio no se encuentra.
        """
        try:
            study_details = self.repo.get_study_by_id(study_id) # Verifica si el estudio existe
            current_is_pinned = study_details.get('is_pinned', 0) == 1
            new_is_pinned = not current_is_pinned

            if new_is_pinned: # Si se va a pinear
                pinned_count = self.repo.count_pinned_studies()
                if pinned_count >= MAX_PINNED_STUDIES:
                    logger.info(f"Intento de pinear estudio {study_id} denegado. Límite de {MAX_PINNED_STUDIES} pineados alcanzado.")
                    return False # Límite alcanzado

            self.repo.update_study_pin_status(study_id, new_is_pinned)
            logger.info(f"Estado de pin para estudio {study_id} cambiado a {new_is_pinned}.")
            return True
        except ValueError as ve: # Estudio no encontrado por get_study_by_id o update_study_pin_status
            logger.error(f"Error al cambiar pin para estudio {study_id}: {ve}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error inesperado al cambiar pin para estudio {study_id}: {e}", exc_info=True)
            # Podríamos relanzar una excepción más genérica o específica del servicio
            raise RuntimeError(f"Error inesperado al cambiar el estado de pin del estudio: {e}")


    def can_undo_last_operation(self) -> bool:
        """
        Checks if an undo operation is available via the UndoManager.
        :return: True if an undo operation can be performed, False otherwise.
        """
        if not self.settings.enable_undo_delete: # Check global setting first
            return False
        return self.undo_manager.can_undo()

    def undo_last_operation(self) -> bool:
        """
        Attempts to perform an undo operation via the UndoManager.
        :return: True if the undo operation was successful, False otherwise.
        """
        if not self.can_undo_last_operation(): # Relies on can_undo_last_operation to check global setting
            logger.warning("Undo last operation called, but no undo operation is available or undo is disabled.")
            return False
        
        success = self.undo_manager.perform_undo()
        if success:
            logger.info("Undo last operation performed successfully by StudyService.")
        else:
            logger.error("Undo last operation failed when called by StudyService.")
        return success
