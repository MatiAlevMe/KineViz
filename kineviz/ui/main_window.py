"""
KineViz: Main Window Module

This module contains the main application window and core UI initialization logic.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import configparser
import sqlite3
import os

from .landing_page import show_landing_page
from .study_management import setup_database, hay_estudios
from .file_management import abrir_carpeta, abrir_manual_usuario
from .analysis import mostrar_analisis_estudio

class KineVizApp:
    def __init__(self, root):
        self.root = root
        self.root.title('KineViz')
        
        # Load settings from config file
        self.load_config()
        
        # Variables for dynamic fields
        self.current_page = 1
        self.current_file_page = 1
        self.current_pdf_page = 1

        # Configure the database
        setup_database()
        
        # Check if studies exist
        if hay_estudios():
            self.mostrar_main_page()
        else:
            show_landing_page(self)

    def load_config(self):
        self.config = configparser.ConfigParser()
        try:
            self.config.read('config.ini')
            self.estudios_por_pagina = int(self.config['SETTINGS']['estudios_por_pagina'])
            self.files_per_page = int(self.config['SETTINGS']['files_per_page'])
            self.pdfs_per_page = int(self.config['SETTINGS'].get('pdfs_per_page', 10))
        except Exception as e:
            # Handle errors (e.g., file not found, invalid values)
            messagebox.showerror("Error", f"Error loading configuration: {str(e)}")
            self.estudios_por_pagina = 10  # Default value
            self.files_per_page = 10  # Default value for files_per_page
            self.pdfs_per_page = 10  # Default value for pdfs_per_page

    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def mostrar_main_page(self):
        # Implement main page logic here
        pass

def main():
    root = tk.Tk()
    root.title('KineViz')
    root.geometry('1000x600')
    app = KineVizApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
