import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from kineviz.ui.views.study_view import StudyView
from kineviz.ui.main_window import MainWindow
from kineviz.core.services.study_service import StudyService
from kineviz.core.services.file_service import FileService
from kineviz.config.settings import AppSettings
from kineviz.ui.widgets.file_browser import FileBrowser


class TestStudyView(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.mock_main_window = MagicMock(spec=MainWindow)
        self.mock_main_window.root = self.root
        self.mock_main_window.study_service = MagicMock(spec=StudyService)
        self.mock_main_window.file_service = MagicMock(spec=FileService) # Added file_service mock
        self.mock_main_window.settings = MagicMock(spec=AppSettings)
        # self.mock_main_window.settings.files_per_page = 5 # This was for AppSettings mock
        self.mock_main_window.files_per_page = 5 # Set directly on mock_main_window
        self.mock_main_window.style = ttk.Style()
        
        # Mock study details that StudyView constructor will try to fetch
        self.mock_main_window.study_service.get_study_details.return_value = {
            'id': 1, 'name': 'Test Study', 'num_subjects': 1, 'attempts_count': 1,
            'independent_variables': [], 'aliases': {}
        }
        # Mock get_study_aliases for update_alias_display
        self.mock_main_window.study_service.get_study_aliases.return_value = {}


        # Mock FileBrowser instance that StudyView creates
        self.mock_file_browser_instance = MagicMock(spec=FileBrowser)

        with patch('kineviz.ui.views.study_view.FileBrowser', return_value=self.mock_file_browser_instance):
            self.study_view = StudyView(self.root, self.mock_main_window, study_id=1, file_service=self.mock_main_window.file_service)

    def tearDown(self):
        if self.root:
            self.root.destroy()
        self.root = None

    @patch('kineviz.ui.views.study_view.messagebox')
    def test_confirm_delete_all_files_confirmed(self, mock_messagebox):
        """Test _confirm_delete_all_files when user confirms."""
        mock_messagebox.askyesno.return_value = True # User confirms deletion
        
        # Call the method
        self.study_view._confirm_delete_all_files()

        # Assert that file_service.delete_all_files_in_study was called
        self.mock_main_window.file_service.delete_all_files_in_study.assert_called_once_with(self.study_view.study_id)
        # Assert that success message was shown
        mock_messagebox.showinfo.assert_called_once()
        # Assert that file list was refreshed
        self.mock_file_browser_instance.load_files.assert_called_once()


    @patch('kineviz.ui.views.study_view.messagebox')
    def test_confirm_delete_all_files_cancelled(self, mock_messagebox):
        """Test _confirm_delete_all_files when user cancels."""
        mock_messagebox.askyesno.return_value = False # User cancels deletion
        
        self.study_view._confirm_delete_all_files()

        self.mock_main_window.file_service.delete_all_files_in_study.assert_not_called()
        mock_messagebox.showinfo.assert_not_called()
        self.mock_file_browser_instance.load_files.assert_not_called()

    def test_refresh_file_list(self):
        """Test refresh_file_list calls load_files on FileBrowser."""
        self.study_view.refresh_file_list()
        self.mock_file_browser_instance.load_files.assert_called_once()

if __name__ == '__main__':
    unittest.main()
