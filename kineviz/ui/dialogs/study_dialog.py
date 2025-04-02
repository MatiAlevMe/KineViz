import tkinter as tk # Usar tk en lugar de solo ttk para StringVar, etc.
from tkinter import ttk, Toplevel, messagebox, Canvas, Scrollbar, Frame # Importar explícitamente
from kineviz.ui.utils.validators import validate_study_data # Asumiendo que este validador es adecuado

class StudyDialog(Toplevel):
    # Añadir study_to_edit y on_save_callback
    def __init__(self, parent, study_service, study_to_edit=None, on_save_callback=None):
        super().__init__(parent)
        self.study_service = study_service
        self.study_to_edit = study_to_edit # Guardar el estudio a editar (o None si es nuevo)
        self.on_save_callback = on_save_callback # Callback a llamar después de guardar

        # Configurar título y geometría
        self.title("Editar Estudio" if study_to_edit else "Nuevo Estudio")
        self.geometry("600x450") # Ajustar tamaño si es necesario, 800 es muy alto
        self.resizable(False, False) # Evitar redimensionar por ahora

        # Variables para campos (usar tk.StringVar)
        self.var_nombre = tk.StringVar()
        self.var_num_sujetos = tk.StringVar()
        self.var_tipos_prueba = tk.StringVar()
        self.var_periodos_prueba = tk.StringVar()
        self.var_cantidad_intentos = tk.StringVar()

        # Si estamos editando, cargar datos existentes
        if self.study_to_edit:
            self._load_study_data()

        self.create_form()

        # Centrar diálogo en la ventana padre
        self.transient(parent)
        self.grab_set()
        # Calcular posición para centrar (opcional pero mejora UX)
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = 600
        dialog_height = 450
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')


    def _load_study_data(self):
        """Carga los datos del estudio existente en las variables del formulario."""
        try:
            # Obtener detalles del estudio usando el servicio
            study_details = self.study_service.get_study_details(self.study_to_edit['id']) # Asumiendo que study_to_edit tiene 'id'
            self.var_nombre.set(study_details.get('name', ''))
            self.var_num_sujetos.set(str(study_details.get('num_subjects', '')))
            self.var_tipos_prueba.set(study_details.get('test_types', '') or '') # Usar '' si es None
            self.var_periodos_prueba.set(study_details.get('test_periods', '') or '') # Usar '' si es None
            self.var_cantidad_intentos.set(str(study_details.get('attempts_count', '')))
        except Exception as e:
            messagebox.showerror("Error al Cargar", f"No se pudieron cargar los datos del estudio:\n{e}", parent=self)
            self.destroy() # Cerrar diálogo si no se pueden cargar datos


    def create_form(self):
        # Usar un Frame normal, el scroll no parece necesario para esta cantidad de campos
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configurar grid layout para mejor alineación
        main_frame.columnconfigure(1, weight=1) # Columna de Entries expandible

        row_idx = 0

        # Campos del formulario con grid
        ttk.Label(main_frame, text="Nombre del estudio:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_nombre).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Número de Sujetos:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_num_sujetos).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Tipos de Prueba (separados por coma):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_tipos_prueba).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Periodos de Prueba (separados por coma):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_periodos_prueba).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Cantidad de Intentos por Prueba:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_cantidad_intentos).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        # Frame para botones (Guardar, Cancelar)
        button_frame = ttk.Frame(main_frame)
        # Alinear botones a la derecha
        button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="e", pady=20, padx=5)

        ttk.Button(button_frame, text="Guardar", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT) # Botón Cancelar

    def save(self):
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
        # Preparar datos del estudio, limpiando tipos y periodos
        # Dividir por comas, quitar espacios y filtrar vacíos
        cleaned_types = [t.strip() for t in self.var_tipos_prueba.get().split(',') if t.strip()]
        cleaned_periods = [p.strip() for p in self.var_periodos_prueba.get().split(',') if p.strip()]

        study_data = {
            'name': self.var_nombre.get().strip(), # También quitar espacios del nombre
            'num_subjects': self.var_num_sujetos.get().strip(),
            'test_types': ','.join(cleaned_types), # Unir los valores limpios
            'test_periods': ','.join(cleaned_periods), # Unir los valores limpios
            'attempts_count': self.var_cantidad_intentos.get().strip()
        }

        # Validar datos (usar el validador importado, que también debe limpiar)
        is_valid, error_message = validate_study_data(study_data) # Asumiendo que devuelve (bool, str)
        if not is_valid:
            messagebox.showerror("Datos Inválidos", error_message, parent=self) # Mostrar error en el diálogo
            return

        try:
            if self.study_to_edit:
                # Llamar al método de actualización real en el servicio
                self.study_service.update_study(self.study_to_edit['id'], study_data)
                messagebox.showinfo("Éxito", "Estudio actualizado correctamente", parent=self)
            else:
                # Crear nuevo estudio
                self.study_service.create_study(study_data)
                messagebox.showinfo("Éxito", "Estudio creado correctamente", parent=self)

            # Llamar al callback si existe
            if self.on_save_callback:
                self.on_save_callback()

            self.destroy() # Cerrar el diálogo

        except ValueError as ve: # Capturar errores específicos si es posible
             messagebox.showerror("Error de Validación", str(ve), parent=self)
        except Exception as e: # Capturar errores generales del servicio o DB
            # Imprimir traceback para debugging
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error al Guardar", f"Ocurrió un error inesperado:\n{str(e)}", parent=self)
