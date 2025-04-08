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
        self.mock_study_service = MagicMock()
        self.mock_file_service = MagicMock()

        # Configurar mocks con valores de retorno básicos
        self.study_id = 1
        self.study_name = "Test_Study"
        self.study_path = Path("/fake/studies/Test_Study")
        self.mock_study_service.get_study_details.return_value = {
            'id': self.study_id, 'name': self.study_name,
            'test_types': 'CMJ,SJ', 'test_periods': 'PRE,POST'
        }
        self.mock_file_service._get_study_path.return_value = self.study_path
        self.mock_file_service.get_unique_study_parameters.return_value = {
            'patients': {'P01', 'P02'}, 'frequencies': {'Cinematica'},
            'types': {'CMJ'}, 'periods': {'PRE'}
        }

        self.analysis_service = AnalysisService(self.mock_study_service, self.mock_file_service)

        # Crear un DataFrame de ejemplo
        self.dummy_df = pd.DataFrame({
            'Tiempo': [0.0, 0.1, 0.2],
            'Val1': [1, 2, 3],
            'Val2': [4, 5, 6]
        })
        self.dummy_stats_series = pd.Series({'Val1': 3, 'Val2': 6}) # Ejemplo de resultado de cálculo

    def test_get_analysis_parameters(self):
        """Prueba obtener parámetros de análisis."""
        params = self.analysis_service.get_analysis_parameters(self.study_id)
        self.mock_file_service.get_unique_study_parameters.assert_called_once_with(self.study_id)
        self.assertIn('patients', params)
        self.assertIn('frequencies', params)
        self.assertIn('types', params)
        self.assertIn('periods', params)
        self.assertIn('calculations', params)
        self.assertEqual(params['calculations'], {'Maximo', 'Minimo', 'Rango'})
        self.assertEqual(params['patients'], {'P01', 'P02'}) # Valor del mock

    def test_get_analysis_parameters_error(self):
        """Prueba el manejo de errores al obtener parámetros."""
        self.mock_file_service.get_unique_study_parameters.side_effect = Exception("Error simulado")
        params = self.analysis_service.get_analysis_parameters(self.study_id)
        self.assertEqual(params, {'patients': set(), 'frequencies': set(), 'types': set(), 'periods': set(), 'calculations': set()})

    def test_read_processed_file_data_valid(self):
        """Prueba leer datos de un archivo procesado simulado válido."""
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
            self.assertListEqual(list(df.columns), ['Tiempo', 'Val1', 'Val2'])
            self.assertEqual(len(df), 3)
            pd.testing.assert_frame_equal(df[['Val1', 'Val2']], self.dummy_df[['Val1', 'Val2']])

    def test_read_processed_file_data_sanitized_columns(self):
        """Prueba la sanitización de nombres de columna duplicados o vacíos."""
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
            # Esperamos: Tiempo, Val1, Unnamed_3, Val1_1 (o similar)
            self.assertIn('Tiempo', df.columns)
            self.assertIn('Val1', df.columns)
            self.assertTrue(any(col.startswith('Unnamed_') for col in df.columns))
            self.assertTrue(any(col.startswith('Val1_') for col in df.columns))
            self.assertEqual(len(df.columns), 4) # Tiempo + 3 columnas de datos

    def test_read_processed_file_data_not_enough_lines(self):
        """Prueba leer un archivo con menos de 7 líneas."""
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

        pd.testing.assert_series_equal(max_res, pd.Series({'Val1': 3.0, 'Val2': 6.0}), check_names=False)
        pd.testing.assert_series_equal(min_res, pd.Series({'Val1': 1.0, 'Val2': 4.0}), check_names=False)
        pd.testing.assert_series_equal(range_res, pd.Series({'Val1': 2.0, 'Val2': 2.0}), check_names=False)
        self.assertIsNone(invalid_res)

    def test_calculate_statistic_empty_or_nan(self):
        """Prueba cálculos con DataFrame vacío o solo NaN."""
        empty_df = pd.DataFrame()
        nan_df = pd.DataFrame({'A': [np.nan, np.nan], 'B': [np.nan, np.nan]})
        self.assertIsNone(self.analysis_service._calculate_statistic(empty_df, "Maximo"))
        self.assertIsNone(self.analysis_service._calculate_statistic(nan_df, "Maximo"))
        self.assertIsNone(self.analysis_service._calculate_statistic(None, "Maximo"))

    # Mockear _read_processed_file_data para las pruebas de nivel superior
    @patch('kineviz.core.services.analysis_service.AnalysisService._read_processed_file_data')
    def test_get_data_for_parameters(self, mock_read_data):
        """Prueba la estructuración de datos basada en parámetros."""
        mock_read_data.return_value = self.dummy_df
        params = {'patients': ['P01'], 'frequencies': ['Cinematica'], 'types': ['CMJ'], 'periods': ['PRE']}

        # Simular estructura de archivos usando mock_file_service._get_study_path y patch('pathlib.Path.glob')
        mock_patient_path = self.study_path / "P01"
        mock_freq_path = mock_patient_path / "Cinematica"
        mock_file = mock_freq_path / "P01 CMJ PRE 01_Cinematica.txt"

        # Configurar mocks para simular la existencia de directorios y archivos
        with patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.glob', return_value=[mock_file]): # Simular glob encontrando el archivo

            structured_data = self.analysis_service._get_data_for_parameters(self.study_id, params)

            self.assertIn('Cinematica', structured_data)
            self.assertIn('CMJ_PRE', structured_data['Cinematica'])
            self.assertIn('P01', structured_data['Cinematica']['CMJ_PRE'])
            pd.testing.assert_frame_equal(structured_data['Cinematica']['CMJ_PRE']['P01'], self.dummy_df)
            # Verificar que _read_processed_file_data fue llamado
            mock_read_data.assert_called_once_with(mock_file)

    @patch('kineviz.core.services.analysis_service.AnalysisService._get_data_for_parameters')
    @patch('kineviz.core.services.analysis_service.AnalysisService._calculate_statistic')
    def test_perform_analysis(self, mock_calculate, mock_get_data):
        """Prueba el flujo completo de perform_analysis."""
        # Simular datos estructurados devueltos por _get_data_for_parameters
        mock_get_data.return_value = {
            'Cinematica': {
                'CMJ_PRE': {
                    'P01': self.dummy_df,
                    'P02': self.dummy_df.copy() # Otra instancia
                }
            }
        }
        # Simular resultado de _calculate_statistic
        mock_calculate.return_value = self.dummy_stats_series

        params = {'patients': ['P01', 'P02'], 'frequencies': ['Cinematica'],
                  'types': ['CMJ'], 'periods': ['PRE'], 'calculations': ['Maximo']}

        results = self.analysis_service.perform_analysis(self.study_id, params)

        mock_get_data.assert_called_once_with(self.study_id, params)
        # Verificar que _calculate_statistic fue llamado para cada paciente y cálculo
        self.assertEqual(mock_calculate.call_count, 2) # P01 y P02
        mock_calculate.assert_has_calls([
            call(self.dummy_df, 'Maximo'),
            call(ANY, 'Maximo') # ANY para el df copiado de P02
        ], any_order=True)

        # Verificar estructura del resultado
        self.assertIn('Cinematica', results)
        self.assertIn('CMJ_PRE', results['Cinematica'])
        self.assertIn('Maximo', results['Cinematica']['CMJ_PRE'])
        self.assertIn('P01', results['Cinematica']['CMJ_PRE']['Maximo'])
        self.assertIn('P02', results['Cinematica']['CMJ_PRE']['Maximo'])
        pd.testing.assert_series_equal(results['Cinematica']['CMJ_PRE']['Maximo']['P01'], self.dummy_stats_series)

    # Mockear dependencias para generate_report
    @patch('kineviz.core.services.analysis_service.AnalysisService._get_data_for_parameters')
    @patch('kineviz.core.services.analysis_service.AnalysisService._calculate_statistic')
    @patch('kineviz.ui.widgets.charting.create_boxplot')
    @patch('kineviz.ui.widgets.charting.create_barchart')
    @patch('reportlab.platypus.SimpleDocTemplate') # Mockear el constructor del PDF
    @patch('pathlib.Path.mkdir') # Mockear creación de directorios
    def test_generate_report(self, mock_mkdir, mock_doc_template, mock_barchart, mock_boxplot, mock_calculate, mock_get_data):
        """Prueba la generación de reportes (flujo y llamadas a mocks)."""
        # Simular datos y cálculos
        mock_get_data.return_value = {'Cinematica': {'CMJ_PRE': {'P01': self.dummy_df, 'P02': self.dummy_df}}}
        mock_calculate.return_value = self.dummy_stats_series
        # Simular que los gráficos se crean exitosamente
        mock_boxplot.side_effect = lambda **kwargs: kwargs['output_path'].touch()
        mock_barchart.side_effect = lambda **kwargs: kwargs['output_path'].touch()

        # Mockear el método build del documento PDF
        mock_pdf_doc = MagicMock()
        mock_doc_template.return_value = mock_pdf_doc

        params = {'patients': ['P01', 'P02'], 'frequencies': ['Cinematica'],
                  'types': ['CMJ'], 'periods': ['PRE'], 'calculations': ['Maximo']}
        output_path = "/fake/report.pdf"

        # Usar tempfile.TemporaryDirectory real para que los archivos de gráficos se creen y limpien
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch tempfile.TemporaryDirectory para devolver nuestra ruta temporal controlada
            with patch('tempfile.TemporaryDirectory') as mock_tempdir_context:
                # Configurar el context manager simulado
                mock_tempdir_instance = MagicMock()
                mock_tempdir_instance.__enter__.return_value = temp_dir # Devolver la ruta real
                mock_tempdir_context.return_value = mock_tempdir_instance

                self.analysis_service.generate_report(self.study_id, params, output_path)

                # Verificar llamadas
                mock_get_data.assert_called_once_with(self.study_id, params)
                self.assertTrue(mock_calculate.called)
                self.assertTrue(mock_boxplot.called)
                self.assertTrue(mock_barchart.called)
                mock_doc_template.assert_called_once_with(output_path, pagesize=ANY, leftMargin=ANY, rightMargin=ANY, topMargin=ANY, bottomMargin=ANY)
                mock_pdf_doc.build.assert_called_once() # Verificar que se intentó construir el PDF

    def test_generate_report_no_data(self):
        """Prueba generar reporte cuando no hay datos."""
        with patch('kineviz.core.services.analysis_service.AnalysisService._get_data_for_parameters', return_value={}):
            with self.assertRaisesRegex(ValueError, "No se encontraron datos"):
                self.analysis_service.generate_report(self.study_id, {}, "/fake/report.pdf")

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.glob')
    def test_list_reports(self, mock_glob, mock_is_dir, mock_exists):
        """Prueba listar reportes existentes."""
        mock_reports_dir = self.study_path / "reportes"
        mock_report_file = mock_reports_dir / "reporte_1.pdf"

        # Simular existencia de directorio y archivo
        mock_exists.side_effect = lambda: str(Path(mock_exists.call_args[0][0])) in [str(mock_reports_dir), str(mock_report_file)]
        mock_is_dir.side_effect = lambda: str(Path(mock_is_dir.call_args[0][0])) == str(mock_reports_dir)
        mock_glob.return_value = [mock_report_file] # Simular glob encontrando el archivo

        # Mockear stat para evitar error al obtener fecha
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = datetime.now().timestamp()
        with patch('pathlib.Path.stat', return_value=mock_stat_result):
             reports = self.analysis_service.list_reports(self.study_id)

        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]['name'], "reporte_1.pdf")
        self.assertEqual(reports[0]['path'], str(mock_report_file))
        self.mock_file_service._get_study_path.assert_called_once_with(self.study_id)

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
