import unittest
import sqlite3
import tempfile
from pathlib import Path
import shutil
import sys
import os

# Añadir el directorio raíz del proyecto al sys.path para importar kineviz
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Asegurar que el logger esté configurado (aunque sea básico) para evitar errores si se llama
import logging
logging.basicConfig(level=logging.CRITICAL) # Suprimir logs durante las pruebas normales

from kineviz.database.repositories import StudyRepository

class TestStudyRepository(unittest.TestCase):

    def setUp(self):
        """Configura un entorno temporal para cada prueba."""
        # Crear directorio temporal para la base de datos y los estudios
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Ruta a la base de datos de prueba
        self.test_db_path = self.temp_path / "test_kineviz.db"
        # Ruta al directorio de estudios de prueba
        self.test_studies_dir = self.temp_path / "test_estudios"
        self.test_studies_dir.mkdir()

        # Instanciar el repositorio con las rutas temporales
        self.repo = StudyRepository(db_path=str(self.test_db_path), studies_base_dir=str(self.test_studies_dir))

        # Datos de ejemplo (actualizados para usar 'sub-valores')
        self.study_data_1 = {
            'name': 'Estudio_Prueba_1', 'num_subjects': '5',
            'sub-valores': 'CMJ,PRE', 'attempts_count': '3'
        }
        self.study_data_2 = {
            'name': 'Estudio_Prueba_2', 'num_subjects': '10',
            'sub-valores': 'SJ,POST', 'attempts_count': '1'
        }
        self.study_data_3 = {
            'name': 'Otro_Estudio_3', 'num_subjects': '2',
            'sub-valores': '', 'attempts_count': '2'
        }


    def tearDown(self):
        """Limpia el entorno temporal después de cada prueba."""
        # Cerrar la conexión a la base de datos si estuviera abierta (aunque el repo usa 'with')
        # Eliminar el directorio temporal y su contenido
        self.temp_dir.cleanup()

    def test_create_study(self):
        """Prueba la creación de un estudio y su directorio."""
        study_id = self.repo.create_study(self.study_data_1)
        self.assertIsInstance(study_id, int)
        self.assertGreater(study_id, 0)

        # Verificar en la base de datos
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre_estudio FROM estudios WHERE id_estudio = ?", (study_id,))
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], self.study_data_1['name'])

        # Verificar creación del directorio
        study_folder = self.test_studies_dir / self.study_data_1['name']
        self.assertTrue(study_folder.exists())
        self.assertTrue(study_folder.is_dir())

    def test_get_study_by_id(self):
        """Prueba obtener un estudio por su ID."""
        study_id = self.repo.create_study(self.study_data_1)
        retrieved_study = self.repo.get_study_by_id(study_id)

        self.assertIsNotNone(retrieved_study)
        self.assertEqual(retrieved_study['id'], study_id)
        self.assertEqual(retrieved_study['name'], self.study_data_1['name'])
        self.assertEqual(retrieved_study['num_subjects'], int(self.study_data_1['num_subjects']))
        self.assertEqual(retrieved_study['sub-valores'], self.study_data_1['sub-valores']) # Usar 'sub-valores'
        self.assertEqual(retrieved_study['attempts_count'], int(self.study_data_1['attempts_count']))

    def test_get_study_by_id_not_found(self):
        """Prueba obtener un estudio inexistente por ID."""
        with self.assertRaises(ValueError):
            self.repo.get_study_by_id(999)

    def test_get_all_studies_empty(self):
        """Prueba obtener todos los estudios cuando la base está vacía."""
        studies = self.repo.get_all_studies()
        self.assertEqual(studies, [])

    def test_get_all_studies(self):
        """Prueba obtener todos los estudios."""
        id1 = self.repo.create_study(self.study_data_1)
        id2 = self.repo.create_study(self.study_data_2)
        studies = self.repo.get_all_studies()
        self.assertEqual(len(studies), 2)
        study_names = {s['name'] for s in studies}
        self.assertIn(self.study_data_1['name'], study_names)
        self.assertIn(self.study_data_2['name'], study_names)

    def test_delete_study(self):
        """Prueba eliminar un estudio y su directorio."""
        study_id = self.repo.create_study(self.study_data_1)
        study_folder = self.test_studies_dir / self.study_data_1['name']
        self.assertTrue(study_folder.exists()) # Verificar que existe antes

        self.repo.delete_study(study_id)

        # Verificar que ya no está en la DB
        with self.assertRaises(ValueError):
            self.repo.get_study_by_id(study_id)

        # Verificar que el directorio fue eliminado
        self.assertFalse(study_folder.exists())

    def test_delete_study_not_found(self):
        """Prueba eliminar un estudio inexistente (no debe lanzar error)."""
        # El método actual loggea una advertencia pero no lanza error, lo cual está bien.
        try:
            self.repo.delete_study(999)
        except Exception as e:
            self.fail(f"delete_study lanzó una excepción inesperada: {e}")

    def test_count_studies(self):
        """Prueba contar estudios."""
        self.assertEqual(self.repo.count_studies(), 0)
        self.repo.create_study(self.study_data_1)
        self.assertEqual(self.repo.count_studies(), 1)
        self.repo.create_study(self.study_data_2)
        self.assertEqual(self.repo.count_studies(), 2)

    def test_update_study(self):
        """Prueba actualizar los datos de un estudio."""
        study_id = self.repo.create_study(self.study_data_1)
        update_data = {
            'name': 'Estudio_Actualizado',
            'num_subjects': '8',
            'sub-valores': 'SJ,DropJump,MID', # Usar 'sub-valores'
            'attempts_count': '5'
        }
        # Asegurar que el update_data tenga el mismo nombre inicial para esta prueba específica
        update_data['name'] = self.study_data_1['name']

        self.repo.update_study(study_id, update_data)
        updated_study = self.repo.get_study_by_id(study_id)

        self.assertEqual(updated_study['name'], update_data['name'])
        self.assertEqual(updated_study['num_subjects'], int(update_data['num_subjects']))
        self.assertEqual(updated_study['sub-valores'], update_data['sub-valores']) # Usar 'sub-valores'
        self.assertEqual(updated_study['attempts_count'], int(update_data['attempts_count']))

    def test_update_study_not_found(self):
        """Prueba actualizar un estudio inexistente."""
        update_data = {
            'name': 'Estudio_Fallido', 'num_subjects': '1',
            'test_types': '', 'test_periods': '', 'attempts_count': '1'
        }
        with self.assertRaises(ValueError):
            self.repo.update_study(999, update_data)

    def test_rename_study_folder(self):
        """Prueba renombrar la carpeta de un estudio."""
        old_name = self.study_data_1['name']
        new_name = "Estudio_Renombrado"
        study_id = self.repo.create_study(self.study_data_1) # Crea la carpeta old_name

        old_folder = self.test_studies_dir / old_name
        new_folder = self.test_studies_dir / new_name
        self.assertTrue(old_folder.exists())
        self.assertFalse(new_folder.exists())

        # Actualizar DB primero (simulando flujo de StudyService)
        update_data = self.study_data_1.copy()
        update_data['name'] = new_name
        self.repo.update_study(study_id, update_data)

        # Luego renombrar carpeta
        self.repo.rename_study_folder(old_name, new_name)

        self.assertFalse(old_folder.exists())
        self.assertTrue(new_folder.exists())
        self.assertTrue(new_folder.is_dir())

    def test_rename_study_folder_original_not_found(self):
        """Prueba renombrar una carpeta que no existe (no debe fallar)."""
        old_name = "Carpeta_Inexistente"
        new_name = "Nuevo_Nombre"
        # El método actual loggea una advertencia pero no falla.
        try:
            self.repo.rename_study_folder(old_name, new_name)
        except Exception as e:
            self.fail(f"rename_study_folder lanzó una excepción inesperada: {e}")

    def test_pagination_and_search(self):
        """Prueba la paginación y búsqueda de estudios."""
        self.repo.create_study(self.study_data_1) # Estudio_Prueba_1
        self.repo.create_study(self.study_data_2) # Estudio_Prueba_2
        self.repo.create_study(self.study_data_3) # Otro_Estudio_3

        # Total sin filtro
        self.assertEqual(self.repo.get_total_studies_count(), 3)

        # Página 1, 2 por página
        page1 = self.repo.get_studies_paginated(limit=2, offset=0)
        self.assertEqual(len(page1), 2)
        # Ordenados por nombre: Estudio_Prueba_1, Estudio_Prueba_2
        self.assertEqual(page1[0]['name'], self.study_data_1['name'])
        self.assertEqual(page1[1]['name'], self.study_data_2['name'])


        # Página 2, 2 por página
        page2 = self.repo.get_studies_paginated(limit=2, offset=2)
        self.assertEqual(len(page2), 1)
        self.assertEqual(page2[0]['name'], self.study_data_3['name']) # El último es Otro_Estudio_3

        # Búsqueda "Prueba"
        search_term = "Prueba"
        self.assertEqual(self.repo.get_total_studies_count(search_term=search_term), 2)
        search_results = self.repo.get_studies_paginated(limit=10, offset=0, search_term=search_term)
        self.assertEqual(len(search_results), 2)
        result_names = {s['name'] for s in search_results}
        self.assertIn(self.study_data_1['name'], result_names)
        self.assertIn(self.study_data_2['name'], result_names)

        # Búsqueda "Otro"
        search_term_otro = "Otro"
        self.assertEqual(self.repo.get_total_studies_count(search_term=search_term_otro), 1)
        search_results_otro = self.repo.get_studies_paginated(limit=10, offset=0, search_term=search_term_otro)
        self.assertEqual(len(search_results_otro), 1)
        self.assertEqual(search_results_otro[0]['name'], self.study_data_3['name'])

        # Búsqueda sin resultados
        search_term_none = "Inexistente"
        self.assertEqual(self.repo.get_total_studies_count(search_term=search_term_none), 0)
        search_results_none = self.repo.get_studies_paginated(limit=10, offset=0, search_term=search_term_none)
        self.assertEqual(len(search_results_none), 0)


if __name__ == '__main__':
    unittest.main()
