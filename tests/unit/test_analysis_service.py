import unittest
from unittest.mock import MagicMock, patch, call, ANY # ANY es útil para argumentos flexibles
import tempfile
from pathlib import Path
import sys
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime

# Añadir el directorio raíz del proyecto al sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Asegurar que el logger esté configurado (aunque sea básico)
import logging
logging.basicConfig(level=logging.CRITICAL)

# Importar la clase a probar
from kineviz.core.services.analysis_service import AnalysisService
# Importar dependencias para type hinting en mocks si es necesario
# from kineviz.core.services.study_service import StudyService
# from kineviz.core.services.file_service import FileService

# --- Mockear dependencias externas ANTES de importar AnalysisService si es necesario ---
# Mockear matplotlib y reportlab para evitar errores de importación o ejecución real
# sys.modules['matplotlib'] = MagicMock()
# sys.modules['matplotlib.pyplot'] = MagicMock()
# sys.modules['reportlab'] = MagicMock()
# sys.modules['reportlab.platypus'] = MagicMock()
# sys.modules['reportlab.lib'] = MagicMock()
# sys.modules['reportlab.lib.styles'] = MagicMock()
# sys.modules['reportlab.lib.pagesizes'] = MagicMock()
# sys.modules['reportlab.lib.colors'] = MagicMock()
# sys.modules['reportlab.lib.units'] = MagicMock()
# sys.modules['kineviz.ui.widgets.charting'] = MagicMock() # Mockear nuestro módulo de charting

class TestAnalysisService(unittest.TestCase):

    def setUp(self):
        """Configura mocks y la instancia de AnalysisService para cada prueba."""
        # Crear directorio temporal real
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name) # Definir self.temp_path

        self.mock_study_service = MagicMock()
        self.mock_file_service = MagicMock()

        # Configurar mocks con valores de retorno básicos
        self.study_id = 1
        self.study_name = "Test_Study"
        self.study_path = self.temp_path / "studies" / self.study_name
        self.study_path.mkdir(parents=True) # Crear el directorio del estudio real

        # Actualizar mock para usar descriptores
        self.study_descriptors = ['CMJ', 'SJ', 'PRE', 'POST']
        self.mock_study_service.get_study_details.return_value = {
            'id': self.study_id, 'name': self.study_name,
            'descriptores': ','.join(self.study_descriptors) # Guardado como string
        }
        # Asegurar que el mock de file_service devuelva la ruta real
        self.mock_file_service._get_study_path.return_value = self.study_path
        # Configurar el project_root y studies_base_dir en el mock de file_service también
        self.mock_file_service.project_root = self.temp_path
        self.mock_file_service.studies_base_dir = self.temp_path / "studies"

        # Actualizar mock para devolver descriptores
        self.mock_file_service.get_unique_study_parameters.return_value = {
            'patients': {'P01', 'P02'}, 'frequencies': {'Cinematica'},
            'descriptors': {'CMJ', 'PRE'} # Descriptores encontrados en archivos
        }

        self.analysis_service = AnalysisService(self.mock_study_service, self.mock_file_service)

        # Crear un DataFrame de ejemplo
        self.dummy_df = pd.DataFrame({
            'Tiempo': [0.0, 0.1, 0.2],
            'Val1': [1, 2, 3],
            'Val2': [4, 5, 6]
        })
        self.dummy_stats_series = pd.Series({'Val1': 3, 'Val2': 6}) # Ejemplo de resultado de cálculo

    def tearDown(self):
        """Limpia el directorio temporal después de cada prueba."""
        self.temp_dir.cleanup()

    def test_get_analysis_parameters(self):
        """Prueba obtener parámetros de análisis."""
        params = self.analysis_service.get_analysis_parameters(self.study_id)
        self.mock_file_service.get_unique_study_parameters.assert_called_once_with(self.study_id)
        self.assertIn('patients', params)
        self.assertIn('frequencies', params)
        self.assertIn('descriptors', params) # Verificar descriptors
        self.assertNotIn('types', params) # Asegurar que ya no existen
        self.assertNotIn('periods', params) # Asegurar que ya no existen
        self.assertIn('calculations', params)
        self.assertEqual(params['calculations'], {'Maximo', 'Minimo', 'Rango'})
        self.assertEqual(params['patients'], {'P01', 'P02'}) # Valor del mock

    def test_get_analysis_parameters_error(self):
        """Prueba el manejo de errores al obtener parámetros."""
        self.mock_file_service.get_unique_study_parameters.side_effect = Exception("Error simulado")
        params = self.analysis_service.get_analysis_parameters(self.study_id)
        # Verificar estructura vacía con descriptors
        self.assertEqual(params, {'patients': set(), 'frequencies': set(), 'descriptors': set(), 'calculations': set()})

    def test_read_processed_file_data_valid(self):
        """Prueba leer datos de un archivo procesado simulado válido."""
        # Archivo procesado ahora empieza con num_frames
        file_content = (
            "Desc\n"
            "100\n" # Frecuencia (no usada directamente aquí)
            ";;Val1;Val2\n" # Columnas
            ";;m;m\n" # Unidades
            "0.0;1;4\n"
            "0.1;2;5\n"
            "0.2;3;6\n"
            ";;MAXIMO;3;6\n" # Stats
            ";;MINIMO;1;4\n"
            ";;RANGO;2;2\n"
        )
        mock_file_path = Path("/fake/study/P01/Cinematica/P01_CMJ_PRE_01_Cinematica.txt")

        # Usar patch para simular open()
        with patch("builtins.open", unittest.mock.mock_open(read_data=file_content)) as mock_open:
            df = self.analysis_service._read_processed_file_data(mock_file_path)
            mock_open.assert_called_once_with(mock_file_path, 'r', encoding='utf-8')
            self.assertIsNotNone(df)
            self.assertIsInstance(df, pd.DataFrame)
            # Los nombres ahora vienen de la línea 2 del archivo procesado
            self.assertListEqual(list(df.columns), ['Meta_1', 'Meta_2', 'Val1', 'Val2'])
            self.assertEqual(len(df), 3)
            # Seleccionar por nombre para la comparación
            pd.testing.assert_frame_equal(df[['Val1', 'Val2']], self.dummy_df[['Val1', 'Val2']])

    def test_read_processed_file_data_sanitized_columns(self):
        """Prueba la sanitización de nombres de columna duplicados o vacíos."""
        # Archivo procesado ahora empieza con num_frames
        file_content = (
            "Desc\n"
            "100\n"
            ";;Val1;;Val1\n" # Columnas con duplicado y vacío
            ";;m;;m\n"
            "0.0;1;99;4\n" # Dato para columna vacía
            "0.1;2;99;5\n"
            "0.2;3;99;6\n"
            ";;MAXIMO;3;99;6\n"
            ";;MINIMO;1;99;4\n"
            ";;RANGO;2;0;2\n"
        )
        mock_file_path = Path("/fake/file.txt")
        with patch("builtins.open", unittest.mock.mock_open(read_data=file_content)):
            df = self.analysis_service._read_processed_file_data(mock_file_path)
            self.assertIsNotNone(df)
            # Esperamos: Meta_1, Meta_2, Val1, Unnamed_3, Val1_1
            self.assertIn('Meta_1', df.columns)
            self.assertIn('Meta_2', df.columns)
            self.assertIn('Val1', df.columns)
            self.assertIn('Unnamed_3', df.columns) # Nombre saneado para columna vacía
            self.assertIn('Val1_1', df.columns) # Nombre saneado para duplicado
            self.assertEqual(len(df.columns), 5) # 5 columnas en total

    def test_read_processed_file_data_not_enough_lines(self):
        """Prueba leer un archivo con menos de 7 líneas (4 header + 3 stats)."""
        file_content = "Line1\nLine2\nLine3\nLine4\nLine5\nLine6\n"
        mock_file_path = Path("/fake/short_file.txt")
        with patch("builtins.open", unittest.mock.mock_open(read_data=file_content)):
            df = self.analysis_service._read_processed_file_data(mock_file_path)
            self.assertIsNone(df)

    def test_read_processed_file_data_file_not_found(self):
        """Prueba leer un archivo que no existe."""
        mock_file_path = Path("/fake/non_existent.txt")
        # Simular FileNotFoundError al abrir
        with patch("builtins.open", side_effect=FileNotFoundError):
            df = self.analysis_service._read_processed_file_data(mock_file_path)
            self.assertIsNone(df)

    def test_calculate_statistic(self):
        """Prueba los cálculos de estadísticas."""
        max_res = self.analysis_service._calculate_statistic(self.dummy_df, "Maximo")
        min_res = self.analysis_service._calculate_statistic(self.dummy_df, "Minimo")
        range_res = self.analysis_service._calculate_statistic(self.dummy_df, "Rango")
        invalid_res = self.analysis_service._calculate_statistic(self.dummy_df, "Mediana") # No soportado

        # Usar enteros en la serie esperada para que coincida el dtype
        pd.testing.assert_series_equal(max_res, pd.Series({'Val1': 3, 'Val2': 6}), check_names=False)
        pd.testing.assert_series_equal(min_res, pd.Series({'Val1': 1, 'Val2': 4}), check_names=False)
        pd.testing.assert_series_equal(range_res, pd.Series({'Val1': 2, 'Val2': 2}), check_names=False)
        self.assertIsNone(invalid_res)

    def test_calculate_statistic_empty_or_nan(self):
        """Prueba cálculos con DataFrame vacío o solo NaN."""
        empty_df = pd.DataFrame()
        nan_df = pd.DataFrame({'A': [np.nan, np.nan], 'B': [np.nan, np.nan]})
        # Ahora esperamos None porque el dataframe numérico estará vacío
        self.assertIsNone(self.analysis_service._calculate_statistic(empty_df, "Maximo"))
        self.assertIsNone(self.analysis_service._calculate_statistic(nan_df, "Maximo"))
        self.assertIsNone(self.analysis_service._calculate_statistic(None, "Maximo"))

    # Mockear _read_processed_file_data para las pruebas de nivel superior
    # Patch validate_filename_for_study_criteria también
    @patch('kineviz.core.services.analysis_service.validate_filename_for_study_criteria')
    @patch('kineviz.core.services.analysis_service.AnalysisService._read_processed_file_data')
    def test_get_data_for_parameters(self, mock_read_data, mock_validate_filename):
        """Prueba la estructuración de datos basada en descriptores."""
        mock_read_data.return_value = self.dummy_df
        mock_validate_filename.return_value = True # Asumir que todos los nombres son válidos
        # Usar descriptores en los parámetros
        params = {'patients': ['P01'], 'frequencies': ['Cinematica'], 'descriptors': ['CMJ', 'PRE']}

        # Simular estructura de archivos
        mock_patient_path = self.study_path / "P01"
        mock_freq_path = mock_patient_path / "Cinematica"
        mock_file = mock_freq_path / "P01 CMJ PRE 01_Cinematica.txt"

        # Configurar mocks para simular la existencia de directorios y archivos
        with patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.glob', return_value=[mock_file]): # Simular glob encontrando el archivo

            structured_data = self.analysis_service._get_data_for_parameters(self.study_id, params)

            # Verificar que validate_filename fue llamado
            mock_validate_filename.assert_called_once_with(mock_file.name, self.study_descriptors)

            # Verificar estructura con clave de descriptores
            self.assertIn('Cinematica', structured_data)
            self.assertIn('CMJ_PRE', structured_data['Cinematica']) # Clave ahora es 'CMJ_PRE'
            self.assertIn('P01', structured_data['Cinematica']['CMJ_PRE'])
            pd.testing.assert_frame_equal(structured_data['Cinematica']['CMJ_PRE']['P01'], self.dummy_df)
            # Verificar que _read_processed_file_data fue llamado
            mock_read_data.assert_called_once_with(mock_file)

    @patch('kineviz.core.services.analysis_service.AnalysisService._get_data_for_parameters')
    @patch('kineviz.core.services.analysis_service.AnalysisService._calculate_statistic')
    def test_perform_analysis(self, mock_calculate, mock_get_data):
        """Prueba el flujo completo de perform_analysis."""
        # Simular datos estructurados devueltos por _get_data_for_parameters
        # Simular datos estructurados con clave de descriptores
        mock_get_data.return_value = {
            'Cinematica': {
                'CMJ_PRE': { # Clave basada en descriptores
                    'P01': self.dummy_df,
                    'P02': self.dummy_df.copy()
                }
            }
        }
        # Simular resultado de cálculo
        mock_calculate.return_value = self.dummy_stats_series

        # Usar descriptores en los parámetros
        params = {'patients': ['P01', 'P02'], 'frequencies': ['Cinematica'],
                  'descriptors': ['CMJ', 'PRE'], 'calculations': ['Maximo']}

        results = self.analysis_service.perform_analysis(self.study_id, params)

        mock_get_data.assert_called_once_with(self.study_id, params)
        # Verificar que _calculate_statistic fue llamado para cada paciente y cálculo
        self.assertEqual(mock_calculate.call_count, 2) # P01 y P02
        mock_calculate.assert_has_calls([
            call(self.dummy_df, 'Maximo'),
            call(ANY, 'Maximo') # ANY para el df copiado de P02
        ], any_order=True)

        # Verificar estructura del resultado con clave de descriptores
        self.assertIn('Cinematica', results)
        self.assertIn('CMJ_PRE', results['Cinematica']) # Clave de descriptores
        self.assertIn('Maximo', results['Cinematica']['CMJ_PRE'])
        self.assertIn('P01', results['Cinematica']['CMJ_PRE']['Maximo'])
        self.assertIn('P02', results['Cinematica']['CMJ_PRE']['Maximo'])
        pd.testing.assert_series_equal(results['Cinematica']['CMJ_PRE']['Maximo']['P01'], self.dummy_stats_series)

    # Mockear dependencias para generate_report
    @patch('kineviz.core.services.analysis_service.AnalysisService._get_data_for_parameters')
    @patch('kineviz.core.services.analysis_service.AnalysisService._calculate_statistic')
    @patch('kineviz.ui.widgets.charting.create_boxplot') # Mockear función de charting
    @patch('kineviz.ui.widgets.charting.create_barchart') # Mockear función de charting
    @patch('reportlab.platypus.SimpleDocTemplate') # Mockear clase de reportlab
    @patch('reportlab.platypus.Image') # Mockear clase Image para evitar lectura de archivo
    @patch('pathlib.Path.mkdir') # Mockear método de Path
    def test_generate_report(self, mock_mkdir, mock_image, mock_doc_template, mock_barchart, mock_boxplot, mock_calculate, mock_get_data):
        """Prueba la generación de reportes (flujo y llamadas a mocks)."""
        # Simular datos con clave de descriptores
        mock_get_data.return_value = {'Cinematica': {'CMJ_PRE': {'P01': self.dummy_df, 'P02': self.dummy_df}}}
        mock_calculate.return_value = self.dummy_stats_series
        # Simular mocks de gráficos
        mock_boxplot.side_effect = None
        mock_barchart.side_effect = None
        # Configurar el mock de Image para que no falle
        mock_image.return_value = MagicMock() # Devolver un mock simple para Image

        # Mockear el método build del documento PDF
        mock_pdf_doc = MagicMock()
        mock_doc_template.return_value = mock_pdf_doc

        # Usar descriptores en los parámetros
        params = {'patients': ['P01', 'P02'], 'frequencies': ['Cinematica'],
                  'descriptors': ['CMJ', 'PRE'], 'calculations': ['Maximo']}
        # Usar ruta temporal
        output_path = self.temp_path / "test_report.pdf"

        # Usar tempfile.TemporaryDirectory real para que los archivos de gráficos se creen y limpien
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch tempfile.TemporaryDirectory para devolver nuestra ruta temporal controlada
            with patch('tempfile.TemporaryDirectory') as mock_tempdir_context:
                # Configurar el context manager simulado
                mock_tempdir_instance = MagicMock()
                mock_tempdir_instance.__enter__.return_value = temp_dir # Devolver la ruta real
                mock_tempdir_context.return_value = mock_tempdir_instance

                # Pasar la ruta como string
                self.analysis_service.generate_report(self.study_id, params, str(output_path))

                # Verificar llamadas
                mock_get_data.assert_called_once_with(self.study_id, params)
                self.assertTrue(mock_calculate.called)
                self.assertTrue(mock_boxplot.called)
                self.assertTrue(mock_barchart.called)
                # Verificar que se llamó con la ruta string
                mock_doc_template.assert_called_once_with(str(output_path), pagesize=ANY, leftMargin=ANY, rightMargin=ANY, topMargin=ANY, bottomMargin=ANY)
                mock_pdf_doc.build.assert_called_once() # Verificar que se intentó construir el PDF

    def test_generate_report_no_data(self):
        """Prueba generar reporte cuando no hay datos."""
        # Usar una ruta dentro del directorio temporal
        output_path_in_temp = self.analysis_service.file_service.project_root / "report_no_data.pdf"
        with patch('kineviz.core.services.analysis_service.AnalysisService._get_data_for_parameters', return_value={}):
            # Mockear mkdir para evitar el error de sistema de archivos de solo lectura
            with patch('pathlib.Path.mkdir'):
                with self.assertRaisesRegex(ValueError, "No se encontraron datos"):
                    self.analysis_service.generate_report(self.study_id, {}, str(output_path_in_temp))

    # No necesitamos mockear Path.glob, exists, is_dir si creamos la estructura real
    @patch('pathlib.Path.stat') # Solo mockear stat si es necesario para la fecha
    def test_list_reports(self, mock_stat):
        """Prueba listar reportes existentes."""
        # Crear estructura real dentro del directorio temporal
        reports_dir = self.study_path / "reportes"
        reports_dir.mkdir()
        report_file_path = reports_dir / "reporte_1.pdf"
        report_file_path.touch() # Crear archivo dummy

        # Configurar el mock de stat para devolver una fecha
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = datetime.now().timestamp()
        mock_stat.return_value = mock_stat_result

        # Llamar a la función bajo prueba
        reports = self.analysis_service.list_reports(self.study_id)

        # Verificar resultados
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]['name'], "reporte_1.pdf")
        self.assertEqual(reports[0]['path'], str(report_file_path)) # Verificar ruta real
        self.mock_file_service._get_study_path.assert_called_once_with(self.study_id)
        mock_stat.assert_called_once_with(report_file_path) # Verificar que stat fue llamado

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.unlink')
    def test_delete_report_success(self, mock_unlink, mock_is_file, mock_exists):
        """Prueba eliminar un reporte exitosamente."""
        mock_report_path_str = "/fake/studies/Test_Study/reportes/reporte_a_borrar.pdf"
        mock_exists.return_value = True
        mock_is_file.return_value = True

        self.analysis_service.delete_report(mock_report_path_str)
        mock_unlink.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_delete_report_not_found(self, mock_exists):
        """Prueba eliminar un reporte que no existe."""
        mock_report_path_str = "/fake/studies/Test_Study/reportes/no_existe.pdf"
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.analysis_service.delete_report(mock_report_path_str)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_delete_report_not_a_file(self, mock_is_file, mock_exists):
        """Prueba eliminar algo que no es un archivo."""
        mock_report_path_str = "/fake/studies/Test_Study/reportes/" # Un directorio
        mock_exists.return_value = True
        mock_is_file.return_value = False
        with self.assertRaises(ValueError):
            self.analysis_service.delete_report(mock_report_path_str)


if __name__ == '__main__':
    unittest.main()
