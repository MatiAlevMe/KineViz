import os
import shutil
from pathlib import Path
from tkinter import messagebox

# Asume que StudyRepository está disponible para obtener detalles del estudio si es necesario
# O que se pasa la ruta base de los estudios.
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
            print(f"Error al obtener la ruta del estudio {study_id}: {e}")
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
                                files_list.append({
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

    def delete_file(self, file_path: Path | str):
        """
        Elimina un archivo específico y limpia directorios vacíos si es necesario.

        :param file_path: Ruta completa (Path o str) del archivo a eliminar.
        :raises FileNotFoundError: Si el archivo no existe.
        :raises OSError: Si ocurre un error al eliminar el archivo o directorio.
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"El archivo no existe: {file_path}")
        if not file_path.is_file():
             raise ValueError(f"La ruta no es un archivo: {file_path}")

        try:
            file_path.unlink() # Eliminar el archivo
            print(f"Archivo eliminado: {file_path}")

            # Intentar eliminar directorios padres si están vacíos
            parent_dir = file_path.parent
            # Detenerse antes de eliminar la carpeta base de estudios
            while parent_dir != self.studies_base_dir and parent_dir != self.project_root:
                try:
                    # Verificar si el directorio está vacío
                    if not any(parent_dir.iterdir()):
                        parent_dir.rmdir()
                        print(f"Directorio vacío eliminado: {parent_dir}")
                        parent_dir = parent_dir.parent # Moverse al siguiente nivel superior
                    else:
                        break # Detener si el directorio no está vacío
                except OSError as e:
                    print(f"No se pudo eliminar el directorio {parent_dir}: {e}")
                    break # Detener si hay un error (ej. permisos)
        except OSError as e:
            print(f"Error al eliminar el archivo {file_path}: {e}")
            raise # Relanzar la excepción


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
