"""
KineViz: Landing Page Module

This module handles the initial landing page of the application.
"""

import tkinter as tk
from tkinter import ttk

def show_landing_page(app):
    """
    Display the landing page of the KineViz application.
    
    Args:
        app (KineVizApp): The main application instance
    """
    app.limpiar_ventana()
    
    # Main frame with padding
    main_frame = ttk.Frame(app.root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    titulo = ttk.Label(main_frame, text="KineViz", font=('Helvetica', 24, 'bold'))
    titulo.pack(pady=20)
    
    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=20)
    
    # Buttons with consistent style
    ttk.Button(button_frame, text='Start Here', 
              command=lambda: app.mostrar_bienvenida()).pack(pady=5)
    
    ttk.Button(button_frame, text='User Manual', 
              command=lambda: app.abrir_manual_usuario()).pack(pady=5)
    
    ttk.Button(button_frame, text='Create New Study', 
              command=lambda: app.mostrar_crear_estudio()).pack(pady=5)
