import tkinter as tk
from tkinter import ttk

class LandingPage:
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window
        self.frame = ttk.Frame(root)
        self.frame.pack(fill='both', expand=True)
        
        self.create_ui()
    
    def create_ui(self):
        # Título
        title_label = ttk.Label(self.frame, text="KineViz", style='Title.TLabel')
        title_label.pack(pady=20)
        
        # Botones
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.pack(pady=20)
        
        ttk.Button(buttons_frame, text="Nuevo Estudio", 
                   command=self.main_window.show_create_study_dialog).pack(pady=5)
        
        ttk.Button(buttons_frame, text="Ver Estudios", 
                   command=self.show_studies).pack(pady=5)
    
    def show_studies(self):
        # Obtener lista de estudios y mostrar
        studies = self.main_window.study_service.get_studies()
        if studies:
            # Mostrar primera vista de estudio o diálogo de selección
            self.main_window.show_study_view(studies[0]['id'])
        else:
            tk.messagebox.showinfo("Información", "No hay estudios disponibles")
    
    def destroy(self):
        self.frame.destroy()
