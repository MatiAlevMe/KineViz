import unittest
import sys
from pathlib import Path

# Añadir el directorio raíz del proyecto al sys.path para importar kineviz
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from kineviz.ui.utils.validators import validate_study_data, validate_filename_for_study_criteria

class TestValidators(unittest.TestCase):

    # --- Pruebas para validate_study_data ---

    def test_validate_study_data_valid(self):
        """Prueba datos de estudio válidos."""
        valid_data = {
            'name': 'Estudio Válido',
            'num_subjects': '5',
            'test_types': 'CMJ, SJ',
            'test_periods': 'PRE, POST',
            'attempts_count': '3'
        }
        is_valid, message = validate_study_data(valid_data)
        self.assertTrue(is_valid, f"Validación falló para datos válidos: {message}")
        self.assertIsNone(message)

    def test_validate_study_data_valid_no_types_periods(self):
        """Prueba datos válidos sin tipos ni periodos."""
        valid_data = {
            'name': 'Estudio Simple',
            'num_subjects': '1',
            'test_types': '',
            'test_periods': '',
            'attempts_count': '1'
        }
        is_valid, message = validate_study_data(valid_data)
        self.assertTrue(is_valid, f"Validación falló sin tipos/periodos: {message}")
        self.assertIsNone(message)

    def test_validate_study_data_invalid_name_empty(self):
        """Prueba nombre de estudio vacío."""
        invalid_data = {'name': ' ', 'num_subjects': '1', 'test_types': '', 'test_periods': '', 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("nombre del estudio es obligatorio", message)

    def test_validate_study_data_invalid_name_short(self):
        """Prueba nombre de estudio demasiado corto."""
        invalid_data = {'name': 'AB', 'num_subjects': '1', 'test_types': '', 'test_periods': '', 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("al menos 3 caracteres", message)

    def test_validate_study_data_invalid_subjects_empty(self):
        """Prueba número de sujetos vacío."""
        invalid_data = {'name': 'Test', 'num_subjects': '', 'test_types': '', 'test_periods': '', 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("número de sujetos es obligatorio", message)

    def test_validate_study_data_invalid_subjects_zero(self):
        """Prueba número de sujetos cero."""
        invalid_data = {'name': 'Test', 'num_subjects': '0', 'test_types': '', 'test_periods': '', 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("entero positivo", message)

    def test_validate_study_data_invalid_subjects_text(self):
        """Prueba número de sujetos no numérico."""
        invalid_data = {'name': 'Test', 'num_subjects': 'abc', 'test_types': '', 'test_periods': '', 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("número entero", message)

    def test_validate_study_data_invalid_attempts_empty(self):
        """Prueba cantidad de intentos vacía."""
        invalid_data = {'name': 'Test', 'num_subjects': '1', 'test_types': '', 'test_periods': '', 'attempts_count': ''}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("cantidad de intentos es obligatoria", message)

    def test_validate_study_data_invalid_attempts_negative(self):
        """Prueba cantidad de intentos negativa."""
        invalid_data = {'name': 'Test', 'num_subjects': '1', 'test_types': '', 'test_periods': '', 'attempts_count': '-1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("entero positivo", message)

    def test_validate_study_data_invalid_attempts_text(self):
        """Prueba cantidad de intentos no numérico."""
        invalid_data = {'name': 'Test', 'num_subjects': '1', 'test_types': '', 'test_periods': '', 'attempts_count': 'uno'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("número entero", message)

    def test_validate_study_data_duplicate_type_period(self):
        """Prueba valores duplicados entre tipos y periodos."""
        invalid_data = {
            'name': 'Estudio Duplicado',
            'num_subjects': '2',
            'test_types': 'CMJ, DUPLICADO',
            'test_periods': 'PRE, DUPLICADO',
            'attempts_count': '1'
        }
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("duplicados entre Tipos y Periodos", message)
        self.assertIn("DUPLICADO", message)

    # --- Pruebas para validate_filename_for_study_criteria ---

    def test_validate_filename_valid_both_criteria(self):
        """Prueba nombre válido con tipos y periodos definidos."""
        types = ['CMJ', 'SJ']
        periods = ['PRE', 'POST']
        self.assertTrue(validate_filename_for_study_criteria("P01 CMJ PRE 01_Cinematica.txt", types, periods))
        self.assertTrue(validate_filename_for_study_criteria("P02 SJ POST 02_Cinetica.txt", types, periods))
        # Orden inverso
        self.assertTrue(validate_filename_for_study_criteria("P03 PRE CMJ 03_Electromiografica.txt", types, periods))

    def test_validate_filename_invalid_both_criteria_wrong_type(self):
        """Prueba nombre inválido (tipo incorrecto) con tipos y periodos."""
        types = ['CMJ', 'SJ']
        periods = ['PRE', 'POST']
        self.assertFalse(validate_filename_for_study_criteria("P01 XYZ PRE 01_Cinematica.txt", types, periods))

    def test_validate_filename_invalid_both_criteria_wrong_period(self):
        """Prueba nombre inválido (periodo incorrecto) con tipos y periodos."""
        types = ['CMJ', 'SJ']
        periods = ['PRE', 'POST']
        self.assertFalse(validate_filename_for_study_criteria("P01 CMJ ABC 01_Cinematica.txt", types, periods))

    def test_validate_filename_invalid_both_criteria_missing_part(self):
        """Prueba nombre inválido (falta parte) con tipos y periodos."""
        types = ['CMJ', 'SJ']
        periods = ['PRE', 'POST']
        self.assertFalse(validate_filename_for_study_criteria("P01 CMJ 01_Cinematica.txt", types, periods)) # Falta periodo

    def test_validate_filename_valid_only_types(self):
        """Prueba nombre válido solo con tipos definidos."""
        types = ['CMJ', 'SJ']
        periods = []
        self.assertTrue(validate_filename_for_study_criteria("P01 CMJ 01_Cinematica.txt", types, periods))
        self.assertTrue(validate_filename_for_study_criteria("P02 SJ 02_Cinetica.txt", types, periods))

    def test_validate_filename_invalid_only_types_wrong_type(self):
        """Prueba nombre inválido (tipo incorrecto) solo con tipos."""
        types = ['CMJ', 'SJ']
        periods = []
        self.assertFalse(validate_filename_for_study_criteria("P01 XYZ 01_Cinematica.txt", types, periods))

    def test_validate_filename_invalid_only_types_extra_part(self):
        """Prueba nombre inválido (parte extra) solo con tipos."""
        types = ['CMJ', 'SJ']
        periods = []
        self.assertFalse(validate_filename_for_study_criteria("P01 CMJ EXTRA 01_Cinematica.txt", types, periods))

    def test_validate_filename_valid_only_periods(self):
        """Prueba nombre válido solo con periodos definidos."""
        types = []
        periods = ['PRE', 'POST']
        self.assertTrue(validate_filename_for_study_criteria("P01 PRE 01_Cinematica.txt", types, periods))
        self.assertTrue(validate_filename_for_study_criteria("P02 POST 02_Cinetica.txt", types, periods))

    def test_validate_filename_invalid_only_periods_wrong_period(self):
        """Prueba nombre inválido (periodo incorrecto) solo con periodos."""
        types = []
        periods = ['PRE', 'POST']
        self.assertFalse(validate_filename_for_study_criteria("P01 ABC 01_Cinematica.txt", types, periods))

    def test_validate_filename_valid_no_criteria(self):
        """Prueba nombre válido sin tipos ni periodos definidos."""
        types = []
        periods = []
        self.assertTrue(validate_filename_for_study_criteria("P01 01_Cinematica.txt", types, periods))
        self.assertTrue(validate_filename_for_study_criteria("P02 02_Cinetica.txt", types, periods))

    def test_validate_filename_invalid_no_criteria_extra_part(self):
        """Prueba nombre inválido (parte extra) sin tipos ni periodos."""
        types = []
        periods = []
        self.assertFalse(validate_filename_for_study_criteria("P01 EXTRA 01_Cinematica.txt", types, periods))

    def test_validate_filename_non_processed_file(self):
        """Prueba que archivos no procesados (sin sufijo de frecuencia) se consideren válidos."""
        types = ['CMJ']
        periods = ['PRE']
        # Archivos en OG o con nombres diferentes no deben ser invalidados por esta función
        self.assertTrue(validate_filename_for_study_criteria("P01 CMJ PRE 01.txt", types, periods))
        self.assertTrue(validate_filename_for_study_criteria("OtroArchivo.csv", types, periods))
        self.assertTrue(validate_filename_for_study_criteria("reporte_final.pdf", types, periods))


if __name__ == '__main__':
    unittest.main()
