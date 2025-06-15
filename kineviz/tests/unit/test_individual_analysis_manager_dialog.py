import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk

from kineviz.ui.dialogs.individual_analysis_manager_dialog import IndividualAnalysisManagerDialog
from kineviz.core.services.analysis_service import AnalysisService
from kineviz.core.services.study_service import StudyService # For mocking study_service within analysis_service


class TestIndividualAnalysisManagerDialog(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.mock_analysis_service = MagicMock(spec=AnalysisService)
        self.mock_analysis_service.study_service = MagicMock(spec=StudyService) # Mock nested service
        self.mock_analysis_service.study_service.get_study_details.return_value = {'name': 'Test Study', 'independent_variables': [], 'aliases': {}}
        self.mock_analysis_service.study_service.get_study_aliases.return_value = {}
        self.mock_analysis_service.list_individual_analyses.return_value = [] # No analyses initially

        # Instantiate the dialog
        self.dialog = IndividualAnalysisManagerDialog(self.root, self.mock_analysis_service, study_id=1)

    def tearDown(self):
        if self.dialog:
            self.dialog.destroy()
        if self.root:
            self.root.destroy()
        self.root = None

    @patch('kineviz.ui.dialogs.individual_analysis_manager_dialog.messagebox')
    def test_confirm_delete_all_individual_analyses_confirmed(self, mock_messagebox):
        mock_messagebox.askyesno.return_value = True
        self.mock_analysis_service.delete_all_individual_analyses.return_value = 2 # Simulate 2 deleted
        
        with patch.object(self.dialog, 'load_analyses') as mock_load_analyses:
            self.dialog._confirm_delete_all_individual_analyses()

            self.mock_analysis_service.delete_all_individual_analyses.assert_called_once_with(self.dialog.study_id)
            mock_messagebox.showinfo.assert_called_once()
            mock_load_analyses.assert_called_once()

    @patch('kineviz.ui.dialogs.individual_analysis_manager_dialog.messagebox')
    def test_confirm_delete_all_individual_analyses_cancelled(self, mock_messagebox):
        mock_messagebox.askyesno.return_value = False
        
        self.dialog._confirm_delete_all_individual_analyses()
        
        self.mock_analysis_service.delete_all_individual_analyses.assert_not_called()

    def test_load_analyses_refresh(self):
        """Test load_analyses (called by refresh button) calls service and populates."""
        self.mock_analysis_service.list_individual_analyses.return_value = [
            {'name': 'Test Analysis 1', 'config': {'column': 'VarX'}, 'mtime': 12345}
        ]
        with patch.object(self.dialog, '_populate_treeview') as mock_populate:
            self.dialog.load_analyses()
            
            self.mock_analysis_service.list_individual_analyses.assert_called_with(self.dialog.study_id)
            mock_populate.assert_called_once() # _apply_filters_and_search calls _populate_treeview

if __name__ == '__main__':
    unittest.main()
