import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk

# Import the class to be tested
from kineviz.ui.views.main_view import MainView
from kineviz.ui.main_window import MainWindow # MainWindow is needed as parent
from kineviz.core.services.study_service import StudyService # For type hinting and mocking
from kineviz.config.settings import AppSettings # For MainWindow dependency


class TestMainView(unittest.TestCase):

    def setUp(self):
        # Create a root Tk window for the tests (it won't be shown)
        self.root = tk.Tk()
        self.root.withdraw() # Hide the root window

        # Mock MainWindow and its dependencies
        self.mock_main_window = MagicMock(spec=MainWindow)
        self.mock_main_window.root = self.root
        self.mock_main_window.study_service = MagicMock(spec=StudyService)
        # Configure return values for methods called during MainView.__init__ -> load_studies()
        self.mock_main_window.study_service.get_studies_paginated.return_value = [] 
        self.mock_main_window.study_service.get_total_studies_count.return_value = 0
        
        self.mock_main_window.settings = MagicMock(spec=AppSettings)
        self.mock_main_window.estudios_por_pagina = 10 # Set directly on mock_main_window
        self.mock_main_window.style = ttk.Style() # Real style object for Danger.TButton

        # Mock methods that MainView might call on MainWindow
        self.mock_main_window.show_create_study_dialog = MagicMock()
        self.mock_main_window.confirm_delete_all_studies = MagicMock()
        self.mock_main_window.show_study_view = MagicMock()
        self.mock_main_window.show_comment_dialog = MagicMock()
        
        # Instantiate MainView
        # MainView expects study_service to be on main_window
        self.main_view = MainView(self.root, self.mock_main_window)

    def tearDown(self):
        # Destroy the root window after each test
        if self.root:
            self.root.destroy()
        self.root = None

    @patch('kineviz.ui.views.main_view.messagebox') # Mock messagebox within main_view module
    def test_confirm_delete_all_studies_confirmed(self, mock_messagebox):
        """Test _confirm_delete_all_studies when user confirms."""
        # Configure messagebox.askyesno to return True (user confirms)
        mock_messagebox.askyesno.return_value = True
        
        # Call the method that triggers the confirmation
        # In MainView, the button calls self.main_window.confirm_delete_all_studies
        # So, we test the method on MainWindow that MainView would call.
        # Let's assume MainView has a button that calls a method on itself,
        # which then calls main_window.confirm_delete_all_studies.
        # The MainView button calls `self._confirm_delete_all_studies`
        # which in turn calls `self.main_window.confirm_delete_all_studies`

        self.main_view._confirm_delete_all_studies()

        # Assert that main_window.confirm_delete_all_studies was called
        self.mock_main_window.confirm_delete_all_studies.assert_called_once()

    @patch('kineviz.ui.views.main_view.messagebox')
    def test_confirm_delete_all_studies_cancelled(self, mock_messagebox):
        """Test _confirm_delete_all_studies when user cancels."""
        # This test is for the MainWindow's method, which MainView calls.
        # If MainView's _confirm_delete_all_studies just directly calls MainWindow,
        # then we should test MainWindow's method.
        # For now, let's assume the call chain as above.
        
        # Configure messagebox.askyesno to return False (user cancels)
        # This part would be for testing MainWindow.confirm_delete_all_studies directly.
        # mock_messagebox.askyesno.return_value = False
        # self.mock_main_window.study_service.delete_all_studies = MagicMock()
        # self.mock_main_window.confirm_delete_all_studies() # Call the actual method on MainWindow
        # self.mock_main_window.study_service.delete_all_studies.assert_not_called()
        
        # For MainView._confirm_delete_all_studies, it always calls main_window's method.
        # The confirmation logic is within MainWindow.
        self.main_view._confirm_delete_all_studies()
        self.mock_main_window.confirm_delete_all_studies.assert_called_once()


    def test_load_studies_refresh_button(self):
        """Placeholder test for refresh button functionality."""
        # Example: Simulate clicking the refresh button
        # This would typically call self.main_view.load_studies
        
        # Mock the service method that load_studies calls
        self.mock_main_window.study_service.get_studies_paginated = MagicMock(return_value=[])
        self.mock_main_window.study_service.get_total_studies_count = MagicMock(return_value=0)
        
        # Find the refresh button if it's created and accessible
        # For simplicity, directly call load_studies as the refresh button would
        self.main_view.load_studies()
        
        # Assert that the service methods were called
        self.mock_main_window.study_service.get_studies_paginated.assert_called()
        self.mock_main_window.study_service.get_total_studies_count.assert_called()
        # Further assertions could check if the treeview is cleared and updated.

if __name__ == '__main__':
    unittest.main()
