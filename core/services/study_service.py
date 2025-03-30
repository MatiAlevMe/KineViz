from database.repositories import StudyRepository
from ..utils.validators import validate_study_data

class StudyService:
    def __init__(self):
        self.repo = StudyRepository()
    
    def create_study(self, study_data):
        """
        Crea un nuevo estudio
        
        :param study_data: Diccionario con datos del estudio
        :return: ID del estudio creado
        """
        # Validar datos antes de crear
        if not validate_study_data(study_data):
            raise ValueError("Datos de estudio inválidos")
        
        # Crear directorio para el estudio
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
