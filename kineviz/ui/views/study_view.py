import tkinter as tk # Importar tk para fill/expand
from tkinter import ttk
# Ya no se necesita PaginatedTable aquí
from kineviz.ui.widgets.file_browser import FileBrowser
# Importar FileService para type hinting (opcional pero bueno)
from kineviz.core.services.file_service import FileService

class StudyView:
    # Añadir file_service al constructor
    def __init__(self, parent, main_window, study_id: int, file_service: FileService):
        self.parent = parent
        self.main_window = main_window
        self.study_id = study_id
        self.file_service = file_service # Guardar la instancia de FileService
        self.frame = ttk.Frame(parent)
        # Usar tk.BOTH y expand=True
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_ui()

    def create_ui(self):
        # --- Header ---
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, pady=(0, 10)) # Añadir padding inferior

        # Botón Volver (podría ir a MainView si hay estudios, o LandingPage si no)
        # Simplificado: siempre a main_view por ahora, refresh se encargará si no hay estudios
        back_command = self.main_window.show_main_view
        # Opcional: decidir basado en si hay estudios (más complejo)
        # back_command = self.main_window.show_main_view if self.main_window.study_service.has_studies() else self.main_window.show_landing_page
        ttk.Button(header_frame, text="<< Volver a Estudios",
                   command=back_command).pack(side=tk.LEFT, padx=(0, 10))

        # Botón Analizar - Corregir comando
        ttk.Button(header_frame, text="Analizar Estudio",
                   command=lambda: self.main_window.show_analysis_dialog(self.study_id)).pack(side=tk.LEFT, padx=(0, 10))

        # Botón Agregar Archivos (Movido desde interfaz.py)
        # Necesita un método en main_window o aquí para manejar la lógica
        # ttk.Button(header_frame, text="Agregar Archivos",
        #            command=self.add_files_dialog).pack(side=tk.LEFT, padx=(0, 10))

        # Botón Abrir Carpeta Estudio (Movido desde interfaz.py)
        ttk.Button(header_frame, text="Abrir Carpeta Estudio",
                   command=self.open_study_folder).pack(side=tk.LEFT, padx=(0, 10))


        # --- Detalles del estudio ---
        study_details = self.main_window.study_service.get_study_details(self.study_id)
        details_frame = ttk.LabelFrame(self.frame, text="Detalles del Estudio")
        details_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(details_frame, text=f"Nombre: {study_details['name']}").pack(anchor='w')
        ttk.Label(details_frame, text=f"Nombre: {study_details.get('name', 'N/A')}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Número de Sujetos: {study_details.get('num_subjects', 'N/A')}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Tipos Prueba: {study_details.get('test_types', 'N/A') or 'N/A'}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Periodos Prueba: {study_details.get('test_periods', 'N/A') or 'N/A'}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Intentos: {study_details.get('attempts_count', 'N/A')}").pack(anchor='w', padx=5, pady=2)

        # --- File browser ---
        # Pasar la instancia de file_service
        # Usar tk.BOTH y expand=True
        self.file_browser = FileBrowser(self.frame, self.file_service, self.study_id)
        self.file_browser.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    def open_study_folder(self):
        """Abre la carpeta del estudio actual."""
        try:
            study_details = self.main_window.study_service.get_study_details(self.study_id)
            study_name = study_details['name']
            # Construir la ruta relativa a la carpeta 'estudios'
            folder_path_str = f"estudios/{study_name}"
            self.main_window.open_folder(folder_path_str)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener la ruta del estudio: {e}", parent=self.frame)

    # def add_files_dialog(self):
    #     """Placeholder para abrir diálogo de agregar archivos."""
    #     # Aquí se llamaría a un FileDialog específico o a una función
    #     # que use tkinter.filedialog.askopenfilenames
    #     messagebox.showinfo("Información", "Diálogo para agregar archivos (Por implementar)", parent=self.frame)
    #     # La lógica de lectura y validación (leer_archivo_csv_o_txt)
    #     # debería moverse a FileService o StudyService.

    def destroy(self):
        """Destruye el frame principal de esta vista."""
        # Asegurarse de que el frame exista antes de destruirlo
        if self.frame and self.frame.winfo_exists():
             self.frame.destroy()
        self.frame = None # Limpiar referencia
