from tkinter import ttk, Toplevel, messagebox
from kineviz.ui.utils.validators import validate_study_data

class StudyDialog(Toplevel):
    def __init__(self, parent, study_service):
        super().__init__(parent)
        self.study_service = study_service
        self.title("Nuevo Estudio")
        self.geometry("600x800")
        
        self.create_form()
    
    def create_form(self):
        # Frame principal con scroll
        canvas = ttk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Variables para campos
        self.var_nombre = ttk.StringVar()
        self.var_num_sujetos = ttk.StringVar()
        self.var_tipos_prueba = ttk.StringVar()
        self.var_periodos_prueba = ttk.StringVar()
        self.var_cantidad_intentos = ttk.StringVar()
        
        # Campos del formulario
        ttk.Label(scroll_frame, text="Nombre del estudio:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_nombre).pack(pady=5)
        
        ttk.Label(scroll_frame, text="Número de Sujetos:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_num_sujetos).pack(pady=5)
        
        ttk.Label(scroll_frame, text="Tipos de Prueba:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_tipos_prueba).pack(pady=5)
        
        ttk.Label(scroll_frame, text="Periodos de Prueba:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_periodos_prueba).pack(pady=5)

        ttk.Label(scroll_frame, text="Cantidad de Intentos:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_cantidad_intentos).pack(pady=5)
        
        ttk.Button(scroll_frame, text="Guardar", command=self.save).pack(pady=20)
        
        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def save(self):
        # Preparar datos del estudio
        study_data = {
            'name': self.var_nombre.get(),
            'num_subjects': self.var_num_sujetos.get(),
            'test_types': self.var_tipos_prueba.get(),
            'test_periods': self.var_periodos_prueba.get(),
            'attempts_count': self.var_cantidad_intentos.get()
        }
        
        # Validar datos
        if validate_study_data(study_data):
            try:
                self.study_service.create_study(study_data)
                messagebox.showinfo("Éxito", "Estudio creado correctamente")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
