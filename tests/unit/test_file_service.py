import unittest
from unittest.mock import MagicMock, patch, call # Importar mocks
import tempfile
from pathlib import Path
import shutil
import sys
import os

# Añadir el directorio raíz del proyecto al sys.path para importar kineviz
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Asegurar que el logger esté configurado (aunque sea básico)
import logging
logging.basicConfig(level=logging.CRITICAL) # Suprimir logs durante las pruebas

# Importar la clase a probar y sus dependencias (para mocking)
from kineviz.core.services.file_service import FileService
# No necesitamos importar StudyService real, lo simularemos

# Dummy data processing functions to avoid import errors if mocked methods are called unexpectedly
# We will primarily patch these out where needed.
def dummy_validate_filename(*args, **kwargs):
    return True
def dummy_process_and_copy(*args, **kwargs):
    pass
def dummy_obtener_nombre_paciente(filename):
    return filename.split(" ")[0] if " " in filename else "P_Desconocido"


class TestFileService(unittest.TestCase):

    def setUp(self):
        """Configura un entorno temporal y mocks para cada prueba."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_studies_base_dir = self.temp_path / "estudios_test"
        self.test_studies_base_dir.mkdir()

        # Crear mock para StudyService
        self.mock_study_service = MagicMock()

        # Instanciar FileService con el mock y la ruta temporal
        # Sobrescribir project_root y studies_base_dir en FileService para usar rutas temporales
        self.file_service = FileService(self.mock_study_service)
        self.file_service.project_root = self.temp_path
        self.file_service.studies_base_dir = self.test_studies_base_dir

        # Datos de estudio simulados comunes
        self.study_id_1 = 1
        self.study_name_1 = "Estudio_FS_1"
        self.study_details_1 = {
            'id': self.study_id_1, 'name': self.study_name_1,
            'test_types': 'CMJ,SJ', 'test_periods': 'PRE,POST',
            'num_subjects': 2, 'attempts_count': 3
        }
        self.study_path_1 = self.test_studies_base_dir / self.study_name_1

        # Configurar el mock para devolver detalles del estudio
        self.mock_study_service.get_study_details.return_value = self.study_details_1

        # Crear directorio del estudio para pruebas
        self.study_path_1.mkdir()


    def tearDown(self):
        """Limpia el entorno temporal después de cada prueba."""
        self.temp_dir.cleanup()

    def test_get_study_path_success(self):
        """Prueba obtener la ruta del estudio exitosamente."""
        path = self.file_service._get_study_path(self.study_id_1)
        self.assertEqual(path, self.study_path_1)
        self.mock_study_service.get_study_details.assert_called_once_with(self.study_id_1)

    def test_get_study_path_failure(self):
        """Prueba obtener la ruta cuando get_study_details falla."""
        self.mock_study_service.get_study_details.side_effect = Exception("DB error simulado")
        # Suprimir messagebox durante la prueba
        with patch('kineviz.core.services.file_service.messagebox.showerror'):
            path = self.file_service._get_study_path(self.study_id_1)
            self.assertIsNone(path)

    def _create_dummy_file_structure(self):
        """Crea una estructura de archivos simulada para pruebas."""
        p1_path = self.study_path_1 / "P01"
        p2_path = self.study_path_1 / "P02"
        p1_cin_path = p1_path / "Cinematica"
        p1_og_path = p1_path / "OG"
        p2_cin_path = p2_path / "Cinetica" # Frecuencia diferente para P02

        for p in [p1_cin_path, p1_og_path, p2_cin_path]:
            p.mkdir(parents=True, exist_ok=True)

        # Archivos P01
        (p1_cin_path / "P01 CMJ PRE 01_Cinematica.txt").touch()
        (p1_cin_path / "P01 SJ POST 01_Cinematica.txt").touch()
        (p1_og_path / "P01 CMJ PRE 01.txt").touch() # Archivo original
        (p1_og_path / "Archivo_Raro_P01.csv").touch()

        # Archivos P02
        (p2_cin_path / "P02 CMJ PRE 01_Cinetica.txt").touch()

    def test_get_study_files_no_filters(self):
        """Prueba obtener archivos sin filtros y con paginación."""
        self._create_dummy_file_structure()
        # Página 1, 2 por página (debería haber 5 archivos en total)
        files, total = self.file_service.get_study_files(self.study_id_1, page=1, per_page=2)
        self.assertEqual(total, 5)
        self.assertEqual(len(files), 2)
        # Página 2, 2 por página
        files, total = self.file_service.get_study_files(self.study_id_1, page=2, per_page=2)
        self.assertEqual(total, 5)
        self.assertEqual(len(files), 2)
        # Página 3, 2 por página
        files, total = self.file_service.get_study_files(self.study_id_1, page=3, per_page=2)
        self.assertEqual(total, 5)
        self.assertEqual(len(files), 1)

    def test_get_study_files_filter_type(self):
        """Prueba filtrar archivos por tipo."""
        self._create_dummy_file_structure()
        files, total = self.file_service.get_study_files(self.study_id_1, file_type="Processed")
        self.assertEqual(total, 3) # 2 Cinematica + 1 Cinetica
        self.assertEqual(len(files), 3) # Asumiendo per_page >= 3
        files, total = self.file_service.get_study_files(self.study_id_1, file_type="Original")
        self.assertEqual(total, 2) # 1 OG + 1 Raro
        self.assertEqual(len(files), 2)

    def test_get_study_files_filter_frequency(self):
        """Prueba filtrar archivos por frecuencia."""
        self._create_dummy_file_structure()
        files, total = self.file_service.get_study_files(self.study_id_1, frequency="Cinematica")
        self.assertEqual(total, 2)
        files, total = self.file_service.get_study_files(self.study_id_1, frequency="Cinetica")
        self.assertEqual(total, 1)
        files, total = self.file_service.get_study_files(self.study_id_1, frequency="N/A") # OG
        self.assertEqual(total, 2)

    def test_get_study_files_search_term(self):
        """Prueba filtrar archivos por término de búsqueda."""
        self._create_dummy_file_structure()
        # Buscar por paciente
        files, total = self.file_service.get_study_files(self.study_id_1, search_term="P01")
        self.assertEqual(total, 4) # 2 Cinematica + 2 OG
        # Buscar por nombre de archivo
        files, total = self.file_service.get_study_files(self.study_id_1, search_term="CMJ PRE")
        self.assertEqual(total, 3) # 1 Cinematica P01, 1 OG P01, 1 Cinetica P02
        # Buscar por parte del nombre
        files, total = self.file_service.get_study_files(self.study_id_1, search_term="Raro")
        self.assertEqual(total, 1)

    def test_delete_file_and_cleanup(self):
        """Prueba eliminar un archivo y la limpieza de directorios vacíos."""
        p1_path = self.study_path_1 / "P01"
        p1_cin_path = p1_path / "Cinematica"
        p1_cin_path.mkdir(parents=True, exist_ok=True)
        file_to_delete = p1_cin_path / "P01 CMJ PRE 01_Cinematica.txt"
        file_to_delete.touch()

        self.assertTrue(file_to_delete.exists())
        self.assertTrue(p1_cin_path.exists())
        self.assertTrue(p1_path.exists())

        self.file_service.delete_file(file_to_delete, self.study_id_1)

        self.assertFalse(file_to_delete.exists())
        # Los directorios padres deberían haber sido eliminados porque estaban vacíos
        self.assertFalse(p1_cin_path.exists())
        self.assertFalse(p1_path.exists())
        # El directorio del estudio no debe eliminarse
        self.assertTrue(self.study_path_1.exists())

    def test_delete_file_no_cleanup_if_not_empty(self):
        """Prueba que la limpieza no elimina directorios no vacíos."""
        p1_path = self.study_path_1 / "P01"
        p1_cin_path = p1_path / "Cinematica"
        p1_og_path = p1_path / "OG" # Otro directorio no vacío
        p1_cin_path.mkdir(parents=True, exist_ok=True)
        p1_og_path.mkdir(parents=True, exist_ok=True)
        file_to_delete = p1_cin_path / "P01 CMJ PRE 01_Cinematica.txt"
        other_file = p1_og_path / "otro.txt"
        file_to_delete.touch()
        other_file.touch()

        self.file_service.delete_file(file_to_delete, self.study_id_1)

        self.assertFalse(file_to_delete.exists())
        self.assertFalse(p1_cin_path.exists()) # Cinematica se elimina
        self.assertTrue(p1_path.exists()) # P01 NO se elimina porque contiene OG
        self.assertTrue(p1_og_path.exists())
        self.assertTrue(other_file.exists())

    def test_delete_file_not_found(self):
        """Prueba eliminar un archivo que no existe."""
        non_existent_file = self.study_path_1 / "no_existe.txt"
        with self.assertRaises(FileNotFoundError):
            self.file_service.delete_file(non_existent_file, self.study_id_1)

    # Patch data processing functions for add_files tests
    # El target ahora es correcto porque la función se importa en el módulo file_service
    @patch('kineviz.core.services.file_service.validate_filename_for_study_criteria', side_effect=dummy_validate_filename)
    @patch('kineviz.core.services.file_service.FileService._process_and_copy_file', side_effect=dummy_process_and_copy)
    def test_add_files_to_study_success(self, mock_process_copy, mock_validate):
        """Prueba agregar archivos válidos."""
        # Crear archivos fuente temporales
        source_dir = self.temp_path / "source_files"
        source_dir.mkdir()
        file1_path = source_dir / "P01 CMJ PRE 01.txt"
        file2_path = source_dir / "P02 SJ POST 01.txt"
        file1_path.touch()
        file2_path.touch()

        file_paths_str = [str(file1_path), str(file2_path)]
        results = self.file_service.add_files_to_study(self.study_id_1, file_paths_str)

        self.assertEqual(results['success'], 2)
        self.assertEqual(len(results['errors']), 0)
        # Verificar que la validación y el procesamiento fueron llamados
        self.assertEqual(mock_validate.call_count, 2)
        self.assertEqual(mock_process_copy.call_count, 2)
        # Verificar llamadas a _process_and_copy_file con los argumentos correctos
        mock_process_copy.assert_has_calls([
            call(self.study_path_1, file1_path),
            call(self.study_path_1, file2_path)
        ], any_order=True)

    # El target ahora es correcto
    @patch('kineviz.core.services.file_service.validate_filename_for_study_criteria')
    @patch('kineviz.core.services.file_service.FileService._process_and_copy_file', side_effect=dummy_process_and_copy)
    def test_add_files_to_study_invalid_name(self, mock_process_copy, mock_validate):
        """Prueba agregar un archivo con nombre inválido."""
        mock_validate.side_effect = lambda name, types, periods: "INVALIDO" not in name

        source_dir = self.temp_path / "source_files"
        source_dir.mkdir()
        file1_path = source_dir / "P01 CMJ PRE 01.txt" # Válido
        file2_path = source_dir / "P02 INVALIDO POST 01.txt" # Inválido
        file1_path.touch()
        file2_path.touch()

        file_paths_str = [str(file1_path), str(file2_path)]
        results = self.file_service.add_files_to_study(self.study_id_1, file_paths_str)

        self.assertEqual(results['success'], 1)
        self.assertEqual(len(results['errors']), 1)
        self.assertIn("Nombre de archivo 'P02 INVALIDO POST 01.txt' no cumple los criterios", results['errors'][0])
        # Verificar que la validación fue llamada para ambos
        self.assertEqual(mock_validate.call_count, 2)
        # Verificar que el procesamiento solo fue llamado para el válido
        mock_process_copy.assert_called_once_with(self.study_path_1, file1_path)

    # El target ahora es correcto
    @patch('kineviz.core.services.file_service.validate_filename_for_study_criteria', side_effect=dummy_validate_filename)
    @patch('kineviz.core.services.file_service.FileService._process_and_copy_file')
    def test_add_files_to_study_processing_error(self, mock_process_copy, mock_validate):
        """Prueba el manejo de errores durante el procesamiento."""
        mock_process_copy.side_effect = Exception("Error simulado en procesamiento")

        source_dir = self.temp_path / "source_files"
        source_dir.mkdir()
        file1_path = source_dir / "P01 CMJ PRE 01.txt"
        file1_path.touch()

        file_paths_str = [str(file1_path)]
        results = self.file_service.add_files_to_study(self.study_id_1, file_paths_str)

        self.assertEqual(results['success'], 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertIn("Error procesando 'P01 CMJ PRE 01.txt': Error simulado en procesamiento", results['errors'][0])
        mock_validate.assert_called_once()
        mock_process_copy.assert_called_once_with(self.study_path_1, file1_path)

    # El target ahora es correcto
    @patch('kineviz.core.services.file_service.validate_filename_for_study_criteria', side_effect=dummy_validate_filename)
    def test_get_unique_study_parameters(self, mock_validate):
        """Prueba obtener parámetros únicos de archivos procesados válidos."""
        # Crear estructura más compleja
        p1_path = self.study_path_1 / "P01"
        p2_path = self.study_path_1 / "P02"
        p1_cin_path = p1_path / "Cinematica"
        p1_ele_path = p1_path / "Electromiografica"
        p2_cin_path = p2_path / "Cinematica"
        p1_og_path = p1_path / "OG" # Debe ser ignorado

        for p in [p1_cin_path, p1_ele_path, p2_cin_path, p1_og_path]:
            p.mkdir(parents=True, exist_ok=True)

        # Archivos válidos (según mock_validate)
        (p1_cin_path / "P01 CMJ PRE 01_Cinematica.txt").touch()
        (p1_cin_path / "P01 SJ POST 01_Cinematica.txt").touch()
        (p1_ele_path / "P01 CMJ PRE 01_Electromiografica.txt").touch() # Mismo tipo/periodo, diferente freq
        (p2_cin_path / "P02 CMJ PRE 01_Cinematica.txt").touch() # Mismo tipo/periodo, diferente paciente

        # Archivo inválido (será filtrado por mock_validate si lo configuramos)
        # (p2_cin_path / "P02 INVALIDO PRE 01_Cinematica.txt").touch()
        # Archivo OG (ignorado por la lógica de carpetas)
        (p1_og_path / "P01 CMJ PRE 01.txt").touch()

        # Configurar mock_validate para que falle con "INVALIDO"
        mock_validate.side_effect = lambda name, types, periods: "INVALIDO" not in name

        params = self.file_service.get_unique_study_parameters(self.study_id_1)

        self.assertEqual(params['patients'], {'P01', 'P02'})
        self.assertEqual(params['frequencies'], {'Cinematica', 'Electromiografica'})
        self.assertEqual(params['types'], {'CMJ', 'SJ'})
        self.assertEqual(params['periods'], {'PRE', 'POST'})


if __name__ == '__main__':
    unittest.main()
