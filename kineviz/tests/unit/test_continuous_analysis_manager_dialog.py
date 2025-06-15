import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk

from kineviz.ui.dialogs.continuous_analysis_manager_dialog import ContinuousAnalysisManagerDialog
from kineviz.core.services.analysis_service import AnalysisService
from kineviz.core.services.study_service import StudyService # For mocking study_service

class TestContinuousAnalysisManagerDialog(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.mock_analysis_service = MagicMock(spec=AnalysisService)
        self.mock_analysis_service.study_service = MagicMock(spec=StudyService)
        self.mock_analysis_service.study_service.get_study_details.return_value = {'name': 'Test Study', 'independent_variables': [], 'aliases': {}}
        self.mock_analysis_service.list_continuous_analyses.return_value = []

        self.mock_main_window = MagicMock() # For main_window_instance

        self.dialog = ContinuousAnalysisManagerDialog(
            self.root, self.mock_analysis_service, study_id=1, main_window_instance=self.mock_main_window
        )

    def tearDown(self):
        if self.dialog:
            self.dialog.destroy()
        if self.root:
            self.root.destroy()
        self.root = None

    @patch('kineviz.ui.dialogs.continuous_analysis_manager_dialog.messagebox')
    def test_confirm_delete_all_continuous_analyses_confirmed(self, mock_messagebox):
        mock_messagebox.askyesno.return_value = True
        self.mock_analysis_service.delete_all_continuous_analyses.return_value = 1
        
        with patch.object(self.dialog, 'load_analyses') as mock_load_analyses:
            self.dialog._confirm_delete_all_continuous_analyses()

            self.mock_analysis_service.delete_all_continuous_analyses.assert_called_once_with(self.dialog.study_id)
            mock_messagebox.showinfo.assert_called_once()
            mock_load_analyses.assert_called_once()

    @patch('kineviz.ui.dialogs.continuous_analysis_manager_dialog.messagebox')
    def test_confirm_delete_all_continuous_analyses_cancelled(self, mock_messagebox):
        mock_messagebox.askyesno.return_value = False
        
        self.dialog._confirm_delete_all_continuous_analyses()
        
        self.mock_analysis_service.delete_all_continuous_analyses.assert_not_called()

    def test_load_analyses_refresh(self):
        """Test load_analyses (called by refresh button) calls service and populates."""
        self.mock_analysis_service.list_continuous_analyses.return_value = [
            {'name': 'Test SPM 1', 'config': {'column': 'VarY'}, 'mtime': 67890}
        ]
        with patch.object(self.dialog, '_populate_treeview') as mock_populate:
            self.dialog.load_analyses()
            
            self.mock_analysis_service.list_continuous_analyses.assert_called_with(self.dialog.study_id)
            mock_populate.assert_called_once() # _apply_filters_and_search calls _populate_treeview

if __name__ == '__main__':
    unittest.main()
