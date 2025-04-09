from kineviz.database.repositories import StudyRepository
from kineviz.ui.utils.validators import validate_study_data

class StudyService:
    def __init__(self):
        self.repo = StudyRepository()
    
    def create_study(self, study_data):
        """
        Crea un nuevo estudio
        
        :param study_data: Diccionario con datos del estudio
        :return: ID del estudio creado
        """
        # La validación ahora se hace en el diálogo antes de llamar al servicio,
        # pero podríamos revalidar aquí por seguridad.
        # is_valid, error_message = validate_study_data(study_data)
        # if not is_valid:
        #     raise ValueError(f"Datos de estudio inválidos: {error_message}")

        # Llamar al repositorio para crear
        study_id = self.repo.create_study(study_data)
        return study_id
    
    def get_studies(self):
        """
        Obtiene la lista de todos los estudios
        
        :return: Lista de estudios
        """
        return self.repo.get_all_studies()
    
    def get_study_details(self, study_id):
        """
        Obtiene los detalles de un estudio específico
        
        :param study_id: ID del estudio
        :return: Diccionario con detalles del estudio
        """
        return self.repo.get_study_by_id(study_id)
    
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
        (Implementación básica, necesita validación y manejo de carpetas)

        :param study_id: ID del estudio a actualizar.
        :param study_data: Diccionario con los nuevos datos del estudio.
        """
        # La validación ahora se hace en el diálogo.
        # is_valid, error_message = validate_study_data(study_data)
        # if not is_valid:
        #     raise ValueError(f"Datos de estudio inválidos: {error_message}")

        # Obtener nombre original para renombrar carpeta si es necesario
        original_study = self.repo.get_study_by_id(study_id)
        original_name = original_study['name']

        # Llamar al repositorio para actualizar
        self.repo.update_study(study_id, study_data)

        # Renombrar carpeta si el nombre cambió
        new_name = study_data['name']
        if original_name != new_name:
            self.repo.rename_study_folder(original_name, new_name)
