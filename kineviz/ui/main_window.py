from tkinter import ttk
from kineviz.ui.views.landing_page import LandingPage
from kineviz.ui.views.study_view import StudyView
from kineviz.ui.dialogs.study_dialog import StudyDialog
from kineviz.ui.dialogs.analysis_dialog import AnalysisDialog
from kineviz.core.services.study_service import StudyService
from kineviz.core.services.analysis_service import AnalysisService

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title('KineViz')
        self.study_service = StudyService()
        self.analysis_service = AnalysisService()
        self.current_view = None
        
        self.configure_styles()
        self.show_landing_page()

    def configure_styles(self):
        # Configuración de estilos
        self.style = ttk.Style()
        self.style.configure('TButton', padding=6)
        self.style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))

    def show_landing_page(self):
        self.clear_window()
        self.current_view = LandingPage(self.root, self)
        
    def show_study_view(self, study_id):
        self.clear_window()
        self.current_view = StudyView(self.root, self, study_id)
    
    def show_create_study_dialog(self):
        StudyDialog(self.root, self.study_service)
    
    def show_analysis(self, study_id):
        AnalysisDialog(self.root, self.analysis_service, study_id)
    
    def clear_window(self):
        if self.current_view:
            self.current_view.destroy()

    def configure_styles(self):
        # Configuración de estilos
        self.style = ttk.Style()
        self.style.configure('TButton', padding=6)
        self.style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))

    def show_landing_page(self):
        self.clear_window()
        self.current_view = LandingPage(self.root, self)
        
    def show_study_view(self, study_id):
        self.clear_window()
        self.current_view = StudyView(self.root, self, study_id)
    
    def show_create_study_dialog(self):
        StudyDialog(self.root, self.study_service)
    
    def show_analysis(self, study_id):
        AnalysisDialog(self.root, self.analysis_service, study_id)
    
    def clear_window(self):
        if self.current_view:
            self.current_view.destroy()
