import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk

from kineviz.ui.views.discrete_analysis_view import DiscreteAnalysisView
from kineviz.ui.main_window import MainWindow
from kineviz.core.services.analysis_service import AnalysisService
from kineviz.core.services.study_service import StudyService # For mocking study_service within analysis_service
from kineviz.config.settings import AppSettings


class TestDiscreteAnalysisView(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.mock_main_window = MagicMock(spec=MainWindow)
        self.mock_main_window.root = self.root
        
        self.mock_analysis_service = MagicMock(spec=AnalysisService)
        # Mock the nested study_service if methods like get_study_details are called through it
        self.mock_analysis_service.study_service = MagicMock(spec=StudyService)
        self.mock_analysis_service.study_service.get_study_details.return_value = {'name': 'Test Study'}
        self.mock_analysis_service.study_service.get_study_aliases.return_value = {}


        self.mock_settings = MagicMock(spec=AppSettings)
        self.mock_settings.discrete_tables_per_page = 5

        # Patch AppSettings instantiation within DiscreteAnalysisView
        with patch('kineviz.ui.views.discrete_analysis_view.AppSettings', return_value=self.mock_settings):
            # Mock methods called during __init__
            self.mock_analysis_service.get_discrete_analysis_tables_path.return_value = MagicMock(exists=lambda: False) # No tables initially
            self.mock_analysis_service.study_service.get_study_details.return_value = {'independent_variables': [], 'aliases': {}}


            self.discrete_view = DiscreteAnalysisView(
                self.root, self.mock_main_window, self.mock_analysis_service, study_id=1
            )
            # Ensure _fetch_all_table_files_data is called and doesn't error if tables_path is None or not exists
            self.mock_analysis_service.get_discrete_analysis_tables_path.return_value.iterdir.return_value = []


    def tearDown(self):
        if self.root:
            self.root.destroy()
        self.root = None

    @patch('kineviz.ui.views.discrete_analysis_view.messagebox')
    def test_confirm_delete_all_summary_tables_confirmed(self, mock_messagebox):
        mock_messagebox.askyesno.return_value = True
        self.mock_analysis_service.delete_all_discrete_summary_tables.return_value = 3 # Simulate 3 tables deleted
        
        # Mock _fetch_all_table_files_data and apply_filters as they are called after deletion
        with patch.object(self.discrete_view, '_fetch_all_table_files_data') as mock_fetch, \
             patch.object(self.discrete_view, 'apply_filters') as mock_apply:
            
            self.discrete_view._confirm_delete_all_summary_tables()

            self.mock_analysis_service.delete_all_discrete_summary_tables.assert_called_once_with(self.discrete_view.study_id)
            mock_messagebox.showinfo.assert_called_once()
            mock_fetch.assert_called_once()
            mock_apply.assert_called_once()

    @patch('kineviz.ui.views.discrete_analysis_view.messagebox')
    def test_confirm_delete_all_summary_tables_cancelled(self, mock_messagebox):
        mock_messagebox.askyesno.return_value = False
        
        self.discrete_view._confirm_delete_all_summary_tables()

        self.mock_analysis_service.delete_all_discrete_summary_tables.assert_not_called()
        mock_messagebox.showinfo.assert_not_called()

    def test_refresh_table_list_action(self):
        """Test refresh_table_list_action calls _fetch_all_table_files_data and apply_filters."""
        with patch.object(self.discrete_view, '_fetch_all_table_files_data') as mock_fetch, \
             patch.object(self.discrete_view, 'apply_filters') as mock_apply:
            
            self.discrete_view.refresh_table_list_action()
            
            mock_fetch.assert_called_once()
            mock_apply.assert_called_once()

if __name__ == '__main__':
    unittest.main()
