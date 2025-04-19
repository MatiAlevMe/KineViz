import json # Importar json
import logging
from kineviz.database.repositories import StudyRepository
# El validador antiguo se eliminará, la validación se hará en el diálogo/nuevo validador
# from kineviz.ui.utils.validators import validate_study_data

logger = logging.getLogger(__name__)

class StudyService:
    def __init__(self):
        self.repo = StudyRepository()

    def create_study(self, study_data):
        """
        Crea un nuevo estudio.

        :param study_data: Diccionario con datos del estudio, incluyendo
                           'independent_variables' (list/dict) y opcionalmente 'aliases' (dict).
        :return: ID del estudio creado.
        :raises ValueError: Si los datos son inválidos o el nombre ya existe.
        :raises Exception: Para otros errores.
        """
        # La validación principal se hará en el diálogo usando el nuevo validador.
        # Aquí convertimos a JSON para el repositorio.
        try:
            data_for_repo = study_data.copy()
            # Convertir VIs a JSON string. Asumir lista vacía si no existe.
            data_for_repo['independent_variables'] = json.dumps(
                study_data.get('independent_variables', [])
            )
            # Convertir Aliases a JSON string. Asumir dict vacío si no existe.
            data_for_repo['aliases'] = json.dumps(
                study_data.get('aliases', {})
            )

            # Llamar al repositorio para crear
            study_id = self.repo.create_study(data_for_repo)
            logger.info(f"Estudio {study_id} ('{study_data['name']}') creado en servicio.")
            return study_id
        except json.JSONDecodeError as e:
            logger.error(f"Error convirtiendo datos a JSON para nuevo estudio: {e}", exc_info=True)
            raise ValueError(f"Error interno al procesar datos del estudio: {e}")
        # Dejar que repo.create_study maneje ValueError por nombre duplicado
        # y otros errores de DB.

    def get_studies(self):
        """
        Obtiene la lista de todos los estudios
        
        :return: Lista de estudios
        """
        return self.repo.get_all_studies()
    
    def get_study_details(self, study_id):
        """
        Obtiene los detalles de un estudio específico
        :param study_id: ID del estudio.
        :return: Diccionario con detalles del estudio, con 'independent_variables'
                 y 'aliases' como estructuras Python (list/dict).
        :raises ValueError: Si el estudio no se encuentra.
        :raises Exception: Para otros errores.
        """
        try:
            study_details_raw = self.repo.get_study_by_id(study_id)

            # Parsear JSON strings a estructuras Python
            try:
                study_details_raw['independent_variables'] = json.loads(
                    study_details_raw.get('independent_variables') or '[]' # Default a JSON array vacío
                )
            except (json.JSONDecodeError, TypeError) as e_iv:
                logger.error(f"Error parseando JSON 'independent_variables' para estudio {study_id}: {e_iv}. Usando lista vacía.", exc_info=True)
                study_details_raw['independent_variables'] = []

            try:
                study_details_raw['aliases'] = json.loads(
                    study_details_raw.get('aliases') or '{}' # Default a JSON object vacío
                )
            except (json.JSONDecodeError, TypeError) as e_al:
                logger.error(f"Error parseando JSON 'aliases' para estudio {study_id}: {e_al}. Usando dict vacío.", exc_info=True)
                study_details_raw['aliases'] = {}

            return study_details_raw
        except ValueError: # Relanzar error de estudio no encontrado
            raise
        except Exception as e:
            logger.error(f"Error inesperado obteniendo detalles estudio {study_id}: {e}", exc_info=True)
            raise # Relanzar otros errores

    def delete_study(self, study_id):
        """
        Elimina un estudio
        
        :param study_id: ID del estudio a eliminar
        """
        self.repo.delete_study(study_id)

    def has_studies(self):
        """
        Verifica si existe al menos un estudio en la base de datos.

        :return: True si hay estudios, False en caso contrario.
        """
        # Delega la llamada al repositorio
        return self.repo.count_studies() > 0

    def get_studies_paginated(self, page: int, per_page: int, search_term: str = None):
        """
        Obtiene una lista paginada de estudios, opcionalmente filtrada por término de búsqueda.

        :param page: Número de página (base 1).
        :param per_page: Número de estudios por página.
        :param search_term: Término para buscar en el nombre del estudio (opcional).
        :return: Lista de diccionarios de estudios para la página solicitada.
        """
        if page < 1:
            page = 1
        offset = (page - 1) * per_page
        return self.repo.get_studies_paginated(limit=per_page, offset=offset, search_term=search_term)

    def get_total_studies_count(self, search_term: str = None):
        """
        Obtiene el número total de estudios, opcionalmente filtrado por término de búsqueda.

        :param search_term: Término para buscar en el nombre del estudio (opcional).
        :return: Número total de estudios que coinciden.
        """
        return self.repo.get_total_studies_count(search_term=search_term)

    def update_study(self, study_id: int, study_data: dict):
        """
        Actualiza los datos de un estudio existente.

        :param study_id: ID del estudio a actualizar.
        :param study_data: Diccionario con los nuevos datos del estudio,
                           incluyendo 'independent_variables' (list/dict) y 'aliases' (dict).
        :raises ValueError: Si los datos son inválidos, el estudio no existe o el nombre ya está en uso.
        :raises Exception: Para otros errores.
        """
        # La validación principal se hará en el diálogo.
        # Convertir a JSON para el repositorio.
        try:
            # Obtener nombre original para renombrar carpeta si es necesario
            # Usar get_study_details para obtener datos parseados
            original_study = self.get_study_details(study_id)
            original_name = original_study['name']

            data_for_repo = study_data.copy()
            # Convertir VIs a JSON string
            data_for_repo['independent_variables'] = json.dumps(
                study_data.get('independent_variables', [])
            )
            # Convertir Aliases a JSON string
            data_for_repo['aliases'] = json.dumps(
                study_data.get('aliases', {})
            )

            # Llamar al repositorio para actualizar
            self.repo.update_study(study_id, data_for_repo)
            logger.info(f"Estudio {study_id} actualizado en servicio.")

            # Renombrar carpeta si el nombre cambió
            new_name = study_data['name']
            if original_name != new_name:
                # Asegurarse de que el nuevo nombre no esté vacío
                if not new_name:
                     logger.error(f"Intento de renombrar estudio {study_id} a un nombre vacío. Omitiendo renombrado de carpeta.")
                     # Podríamos lanzar un error aquí si el nombre vacío no fue validado antes
                else:
                     self.repo.rename_study_folder(original_name, new_name)

        except json.JSONDecodeError as e:
            logger.error(f"Error convirtiendo datos a JSON para actualizar estudio {study_id}: {e}", exc_info=True)
            raise ValueError(f"Error interno al procesar datos del estudio: {e}")
        except ValueError as ve: # Capturar errores de repo (no encontrado, nombre duplicado)
            logger.warning(f"Error de validación/DB al actualizar estudio {study_id}: {ve}")
            raise # Relanzar
        except Exception as e:
            logger.error(f"Error inesperado actualizando estudio {study_id}: {e}", exc_info=True)
            raise

    # --- Métodos específicos para Aliases (si se gestionan aquí) ---
    # Estos métodos asumen que los alias se cargan/guardan junto con el estudio.

    def get_study_aliases(self, study_id: int) -> dict:
        """Obtiene el diccionario de alias para un estudio específico."""
        try:
            study_details = self.get_study_details(study_id)
            # get_study_details ya parsea el JSON
            return study_details.get('aliases', {})
        except ValueError: # Estudio no encontrado
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo alias para estudio {study_id}: {e}", exc_info=True)
            return {}

    def update_study_aliases(self, study_id: int, aliases: dict):
        """Actualiza solo los alias de un estudio específico."""
        try:
            # Obtener datos actuales para no perder VIs, etc.
            study_details = self.get_study_details(study_id)
            # Actualizar solo los alias
            study_details['aliases'] = aliases
            # Llamar a update_study con todos los datos (convertirá a JSON)
            self.update_study(study_id, study_details)
            logger.info(f"Aliases actualizados para estudio {study_id}.")
        except ValueError: # Estudio no encontrado
            raise
        except Exception as e:
            logger.error(f"Error actualizando alias para estudio {study_id}: {e}", exc_info=True)
            raise
        if original_name != new_name:
            self.repo.rename_study_folder(original_name, new_name)
