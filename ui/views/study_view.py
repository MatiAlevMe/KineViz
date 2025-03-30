from tkinter import ttk
from ..widgets.paginated_table import PaginatedTable
from ..widgets.file_browser import FileBrowser

class StudyView:
    def __init__(self, parent, main_window, study_id):
        self.parent = parent
        self.main_window = main_window
        self.study_id = study_id
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill='both', expand=True)
        
        self.create_ui()
    
    def create_ui(self):
        # Header
        header = ttk.Frame(self.frame)
        ttk.Button(header, text="Volver", 
                   command=self.main_window.show_landing_page).pack(side='left')
        ttk.Button(header, text="Analizar", 
                   command=lambda: self.main_window.show_analysis(self.study_id)).pack(side='left')
        header.pack(fill='x')
        
        # Detalles del estudio
        study_details = self.main_window.study_service.get_study_details(self.study_id)
        details_frame = ttk.LabelFrame(self.frame, text="Detalles del Estudio")
        details_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(details_frame, text=f"Nombre: {study_details['name']}").pack(anchor='w')
        ttk.Label(details_frame, text=f"Número de Sujetos: {study_details['num_subjects']}").pack(anchor='w')
        
        # File browser
        self.file_browser = FileBrowser(self.frame, self.main_window.study_service, self.study_id)
        self.file_browser.pack(fill='both', expand=True)
    
    def destroy(self):
        self.frame.destroy()
