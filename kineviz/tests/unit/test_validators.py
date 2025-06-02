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
            'sub-valores': ['CMJ', 'SJ', 'PRE', 'POST'], # Usar lista de sub-valores
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
            'sub-valores': [], # Lista vacía para sin sub-valores
            'attempts_count': '1'
        }
        is_valid, message = validate_study_data(valid_data)
        self.assertTrue(is_valid, f"Validación falló sin tipos/periodos: {message}")
        self.assertIsNone(message)

    def test_validate_study_data_invalid_name_empty(self):
        """Prueba nombre de estudio vacío."""
        invalid_data = {'name': ' ', 'num_subjects': '1', 'sub-valores': [], 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("nombre del estudio es obligatorio", message)

    def test_validate_study_data_invalid_name_short(self):
        """Prueba nombre de estudio demasiado corto."""
        invalid_data = {'name': 'AB', 'num_subjects': '1', 'sub-valores': [], 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("al menos 3 caracteres", message)

    def test_validate_study_data_invalid_subjects_empty(self):
        """Prueba número de sujetos vacío."""
        invalid_data = {'name': 'Test', 'num_subjects': '', 'sub-valores': [], 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("número de sujetos es obligatorio", message)

    def test_validate_study_data_invalid_subjects_zero(self):
        """Prueba número de sujetos cero."""
        invalid_data = {'name': 'Test', 'num_subjects': '0', 'sub-valores': [], 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("entero positivo", message)

    def test_validate_study_data_invalid_subjects_text(self):
        """Prueba número de sujetos no numérico."""
        invalid_data = {'name': 'Test', 'num_subjects': 'abc', 'sub-valores': [], 'attempts_count': '1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("número entero", message)

    def test_validate_study_data_invalid_attempts_empty(self):
        """Prueba cantidad de intentos vacía."""
        invalid_data = {'name': 'Test', 'num_subjects': '1', 'sub-valores': [], 'attempts_count': ''}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("cantidad de intentos es obligatoria", message)

    def test_validate_study_data_invalid_attempts_negative(self):
        """Prueba cantidad de intentos negativa."""
        invalid_data = {'name': 'Test', 'num_subjects': '1', 'sub-valores': [], 'attempts_count': '-1'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("entero positivo", message)

    def test_validate_study_data_invalid_attempts_text(self):
        """Prueba cantidad de intentos no numérico."""
        invalid_data = {'name': 'Test', 'num_subjects': '1', 'sub-valores': [], 'attempts_count': 'uno'}
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("número entero", message)

    def test_validate_study_data_duplicate_descriptors(self):
        """Prueba sub-valores duplicados."""
        invalid_data = {
            'name': 'Estudio Duplicado',
            'num_subjects': '2',
            'sub-valores': ['CMJ', 'PRE', 'CMJ'], # Sub-valor duplicado
            'attempts_count': '1'
        }
        is_valid, message = validate_study_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("sub-valores están duplicados", message)
        self.assertIn("CMJ", message)

    # --- Pruebas para validate_filename_for_study_criteria ---

    def test_validate_filename_valid_with_descriptors(self):
        """Prueba nombres válidos con sub-valores definidos."""
        descriptors = ['CMJ', 'PRE', 'GrupoA']
        # Todos los sub-valores presentes y en orden
        self.assertTrue(validate_filename_for_study_criteria("P01 CMJ PRE GrupoA 01_Cinematica.txt", descriptors))
        # Subconjunto de sub-valores en orden
        self.assertTrue(validate_filename_for_study_criteria("P02 CMJ PRE 02_Cinetica.txt", descriptors))
        self.assertTrue(validate_filename_for_study_criteria("P03 PRE GrupoA 03_Electromiografica.txt", descriptors))
        self.assertTrue(validate_filename_for_study_criteria("P04 CMJ 04_Cinematica.txt", descriptors))
        self.assertTrue(validate_filename_for_study_criteria("P05 GrupoA 05_Cinetica.txt", descriptors))
        # Con guiones bajos en lugar de espacios
        self.assertTrue(validate_filename_for_study_criteria("P06_CMJ_PRE_06_Cinematica.txt", descriptors))

    def test_validate_filename_invalid_wrong_descriptor(self):
        """Prueba nombre inválido (sub-valor incorrecto)."""
        descriptors = ['CMJ', 'PRE']
        self.assertFalse(validate_filename_for_study_criteria("P01 CMJ POST 01_Cinematica.txt", descriptors))
        self.assertFalse(validate_filename_for_study_criteria("P01 XYZ PRE 01_Cinematica.txt", descriptors))

    def test_validate_filename_invalid_wrong_order(self):
        """Prueba nombre inválido (orden incorrecto de sub-valores)."""
        descriptors = ['CMJ', 'PRE', 'GrupoA']
        self.assertFalse(validate_filename_for_study_criteria("P01 PRE CMJ GrupoA 01_Cinematica.txt", descriptors))
        self.assertFalse(validate_filename_for_study_criteria("P02 GrupoA PRE 02_Cinetica.txt", descriptors))

    def test_validate_filename_invalid_missing_descriptor_part(self):
        """Prueba nombre inválido (falta parte intermedia) con sub-valores definidos."""
        descriptors = ['CMJ', 'PRE']
        self.assertFalse(validate_filename_for_study_criteria("P01 01_Cinematica.txt", descriptors))

    def test_validate_filename_invalid_extra_descriptor_part(self):
        """Prueba nombre inválido (parte intermedia extra no definida)."""
        descriptors = ['CMJ', 'PRE']
        self.assertFalse(validate_filename_for_study_criteria("P01 CMJ PRE EXTRA 01_Cinematica.txt", descriptors))

    def test_validate_filename_valid_no_descriptors_defined(self):
        """Prueba nombre válido cuando no hay sub-valores definidos."""
        descriptors = []
        self.assertTrue(validate_filename_for_study_criteria("P01 01_Cinematica.txt", descriptors))
        self.assertTrue(validate_filename_for_study_criteria("Pte02 02_Cinetica.txt", descriptors))

    def test_validate_filename_invalid_no_descriptors_defined_extra_part(self):
        """Prueba nombre inválido (parte extra) sin sub-valores definidos."""
        descriptors = []
        self.assertFalse(validate_filename_for_study_criteria("P01 EXTRA 01_Cinematica.txt", descriptors))
        self.assertFalse(validate_filename_for_study_criteria("P02 CMJ 02_Cinetica.txt", descriptors))

    def test_validate_filename_invalid_format(self):
        """Prueba formatos de nombre inválidos (sin Pte, sin NN)."""
        descriptors = ['CMJ']
        self.assertFalse(validate_filename_for_study_criteria("Sujeto01 CMJ 01_Cinematica.txt", descriptors))
        self.assertFalse(validate_filename_for_study_criteria("P01 CMJ Uno_Cinematica.txt", descriptors))
        self.assertFalse(validate_filename_for_study_criteria("P01_Cinematica.txt", descriptors))
        self.assertFalse(validate_filename_for_study_criteria("P01_CMJ_Cinematica.txt", descriptors)) # Falta NN

    def test_validate_filename_non_processed_file_ignored(self):
        """Prueba que archivos no procesados (sin sufijo de frecuencia) se ignoren."""
        # La lógica actual del validador devuelve True si no detecta sufijo de frecuencia.
        # Esto es para no bloquear archivos OG, pero significa que no valida sub-valores en ellos.
        descriptors = ['CMJ', 'PRE']
        self.assertTrue(validate_filename_for_study_criteria("P01 CMJ PRE 01.txt", descriptors))
        self.assertTrue(validate_filename_for_study_criteria("OtroArchivo.csv", descriptors))
        self.assertTrue(validate_filename_for_study_criteria("reporte_final.pdf", descriptors))
        # Incluso si el nombre parece tener sub-valores pero no sufijo, se ignora la validación de sub-valores
        self.assertTrue(validate_filename_for_study_criteria("P01 CMJ POST 01.txt", descriptors)) # POST es inválido, pero pasa


if __name__ == '__main__':
    unittest.main()
