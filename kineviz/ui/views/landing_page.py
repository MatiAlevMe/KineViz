import tkinter as tk
from tkinter import ttk, messagebox

class LandingPage:
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window
        # Usar padding en el frame principal como en interfaz.py
        # El frame se empaqueta aquí para asegurar que llene la ventana
        self.frame = ttk.Frame(root, padding="20")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.create_ui()

    def create_ui(self):
        """Crea los elementos de la UI para la Landing Page."""
        # Título - Usar estilo definido en MainWindow
        # Asegurarse de que el estilo 'Title.TLabel' esté definido en MainWindow.configure_styles
        title_label = ttk.Label(self.frame, text="KineViz", style='Title.TLabel')
        # Centrar título usando pack
        title_label.pack(pady=(40, 20)) # Aumentar padding superior

        # Frame para botones centrado
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=20) # pady para espaciar del título

        # Botones con comandos de MainWindow y estilo TButton
        # Usar el estilo 'TButton' configurado en MainWindow
        button_style = 'TButton'
        button_padding = {'pady': 10, 'ipadx': 10, 'ipady': 5} # Padding para botones

        ttk.Button(button_frame, text='Empieza Aquí',
                  command=self.main_window.show_welcome_message, style=button_style).pack(**button_padding)

        ttk.Button(button_frame, text='Manual de Usuario',
                  command=self.main_window.open_user_manual, style=button_style).pack(**button_padding)

        ttk.Button(button_frame, text='Crear Nuevo Estudio',
                  # Pasar None para study_to_edit explícitamente
                  command=lambda: self.main_window.show_create_study_dialog(study_to_edit=None),
                  style=button_style).pack(**button_padding)

        # Botón para ir a la vista principal si hay estudios
        # Verificar si el servicio y el método existen antes de llamar
        if hasattr(self.main_window, 'study_service') and hasattr(self.main_window.study_service, 'has_studies') and self.main_window.study_service.has_studies():
             ttk.Button(button_frame, text='Ver Estudios Existentes',
                       command=self.main_window.show_main_view, style=button_style).pack(**button_padding)

        ttk.Button(button_frame, text='Restaurar Copia de Seguridad',
                  command=self.main_window.show_backup_restore_dialog_from_landing, style=button_style).pack(**button_padding)

        ttk.Button(button_frame, text='Reproducir DEMO',
                  command=self.main_window.play_demo_video, style=button_style).pack(**button_padding)


    # El método destroy es llamado por MainWindow.clear_window
    def destroy(self):
         """Destruye el frame principal de esta vista."""
         if self.frame:
             try:
                 self.frame.destroy()
             except tk.TclError:
                 # Ignorar si ya está destruido
                 pass
             self.frame = None # Evitar referencias dangling
