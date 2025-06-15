import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk

from kineviz.ui.widgets.file_browser import FileBrowser
from kineviz.core.services.file_service import FileService

class TestFileBrowser(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.mock_file_service = MagicMock(spec=FileService)
        # Mock the return of get_study_files to be a tuple (list_of_files, total_count)
        self.mock_file_service.get_study_files.return_value = ([], 0) 

        self.file_browser = FileBrowser(self.root, self.mock_file_service, study_id=1, files_per_page=5)

    def tearDown(self):
        if self.file_browser: # Ensure it exists before trying to destroy
            self.file_browser.destroy()
        if self.root:
            self.root.destroy()
        self.root = None

    def test_load_files_refresh(self):
        """Test load_files (called by refresh button) calls service and updates tree."""
        # Simulate some files returned by the service
        mock_files_data = [
            {'patient': 'P01', 'name': 'file1.txt', 'type': 'Processed', 'frequency': 'Cinematica', 'path': 'path/to/file1.txt'},
            {'patient': 'P02', 'name': 'file2.csv', 'type': 'Original', 'frequency': 'N/A', 'path': 'path/to/file2.csv'}
        ]
        self.mock_file_service.get_study_files.return_value = (mock_files_data, 2)

        # Call load_files, which is what the refresh button does
        self.file_browser.load_files()

        # Assert that the service was called
        self.mock_file_service.get_study_files.assert_called_with(
            study_id=1,
            page=1, # Assuming it resets to page 1 on refresh/load
            per_page=5,
            search_term=None, # Default search term
            file_type=None,   # Default file_type filter ("Todos" maps to None)
            frequency=None    # Default frequency filter ("Todos" maps to None)
        )
        
        # Assert that the treeview was populated
        # Check number of items in tree, should match number of files returned
        self.assertEqual(len(self.file_browser.tree.get_children()), 2)
        
        # Check values of the first item
        first_item_id = self.file_browser.tree.get_children()[0]
        first_item_values = self.file_browser.tree.item(first_item_id, 'values')
        self.assertEqual(first_item_values[0], 'P01') # Patient
        self.assertEqual(first_item_values[1], 'file1.txt') # Name

if __name__ == '__main__':
    unittest.main()
