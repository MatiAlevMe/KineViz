import tkinter as tk
from tkinter import ttk
import logging

# Asegúrate de que AnalysisService esté disponible para type hinting si es necesario en el futuro
# from kineviz.core.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class ContinuousAnalysisConfigDialog(tk.Toplevel):
    """
    Diálogo para configurar los parámetros de un análisis continuo (SPM).
    """
    def __init__(self, parent, analysis_service, study_id: int):
        """
        Inicializa el diálogo de configuración de análisis continuo.

        :param parent: La ventana padre.
        :param analysis_service: Instancia de AnalysisService.
        :param study_id: ID del estudio para el cual se configura el análisis.
        """
        super().__init__(parent)
        self.parent = parent
        self.analysis_service = analysis_service
        self.study_id = study_id

        self.title("Configurar Análisis Continuo (Cinemática)")
        # Definir un tamaño inicial, se puede ajustar
        self.geometry("700x550") # Aumentar tamaño para grupos
        # Hacer modal
        self.grab_set()
        self.transient(parent)

        self.result = None # Para almacenar la configuración si se guarda

        # --- Variables de Tkinter ---
        self.selected_data_type = tk.StringVar()
        self.selected_variable = tk.StringVar()
        self.selected_groups_vars = [] # Para almacenar las StringVars de los selectores de grupo
        self.group_selector_frames = [] # Para almacenar los frames de los selectores de grupo
        self.group_display_to_key_map = {} # Para mapear display names a claves originales

        self.create_widgets()
        self.load_data_types()

        # Centrar el diálogo con respecto al padre
        self.parent.winfo_toplevel().update_idletasks() # Asegurar que las dimensiones del padre estén actualizadas
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        position_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        position_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        self.geometry(f"+{position_x}+{position_y}")


        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)

    def create_widgets(self):
        """Crea los widgets del diálogo."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- Sección de Selección de Tipo de Datos ---
        data_type_frame = ttk.LabelFrame(main_frame, text="1. Seleccionar Tipo de Dato")
        data_type_frame.pack(fill=tk.X, padx=5, pady=(0, 10))

        ttk.Label(data_type_frame, text="Tipo de Dato:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.data_type_combobox = ttk.Combobox(
            data_type_frame,
            textvariable=self.selected_data_type,
            state="readonly",
            width=25
        )
        self.data_type_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.data_type_combobox.bind("<<ComboboxSelected>>", self.on_data_type_selected)

        # --- Sección de Selección de Variable ---
        var_outer_frame = ttk.LabelFrame(main_frame, text="2. Seleccionar Variable a Analizar")
        var_outer_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        var_inner_frame = ttk.Frame(var_outer_frame, padding=(0,0,0,5)) # Padding interno
        var_inner_frame.pack(fill=tk.X)

        ttk.Label(var_inner_frame, text="Columna:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.variable_combobox = ttk.Combobox(
            var_inner_frame,
            textvariable=self.selected_variable,
            state="disabled", 
            width=45 # Ajustar ancho para formato Attr/Col/Unit
        )
        self.variable_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        var_inner_frame.columnconfigure(1, weight=1) # Hacer que el combobox se expanda
        self.variable_combobox.bind("<<ComboboxSelected>>", self.on_variable_selected)

        # --- Sección de Selección de Grupos de Sub-valores ---
        self.groups_frame_outer = ttk.LabelFrame(main_frame, text="3. Seleccionar Grupos de Sub-valores a Comparar")
        self.groups_frame_outer.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))
        
        # Canvas y Scrollbar para la sección de grupos
        self.groups_canvas = tk.Canvas(self.groups_frame_outer, borderwidth=0, highlightthickness=0)
        self.groups_inner_frame = ttk.Frame(self.groups_canvas) # Frame interior para los selectores
        self.groups_scrollbar = ttk.Scrollbar(self.groups_frame_outer, orient="vertical", command=self.groups_canvas.yview)
        self.groups_canvas.configure(yscrollcommand=self.groups_scrollbar.set)

        self.groups_scrollbar.pack(side="right", fill="y")
        self.groups_canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.groups_canvas.create_window((0, 0), window=self.groups_inner_frame, anchor="nw")

        self.groups_inner_frame.bind("<Configure>", lambda e: self.groups_canvas.configure(scrollregion=self.groups_canvas.bbox("all")))
        self.groups_canvas.bind('<Configure>', self._on_canvas_configure)


        # Botón para añadir más selectores de grupo
        self.add_group_button = ttk.Button(self.groups_frame_outer, text="Añadir Grupo", command=self.add_group_selector, state="disabled")
        self.add_group_button.pack(pady=(10,5), side=tk.BOTTOM) # Añadir padding superior


        # --- Botones de Acción ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)

        ttk.Button(button_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.RIGHT, padx=(5,0))
        ttk.Button(button_frame, text="Aceptar", command=self._on_accept, style="Accent.TButton").pack(side=tk.RIGHT) # Estilo opcional

    def _on_canvas_configure(self, event):
        """Ajusta el ancho del frame interior al del canvas."""
        canvas_width = event.width
        self.groups_canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_accept(self):
        """Acción al presionar Aceptar."""
        selected_dt = self.selected_data_type.get()
        selected_var = self.selected_variable.get()
        selected_group_keys = self.get_selected_group_keys()
        from tkinter import messagebox

        if not selected_dt:
            messagebox.showwarning("Advertencia", "Debe seleccionar un Tipo de Dato.", parent=self)
            return
        
        if not selected_var:
            messagebox.showwarning("Advertencia", "Debe seleccionar una Columna a analizar.", parent=self)
            return
        
        if len(selected_group_keys) < 2:
            messagebox.showwarning("Advertencia", "Debe seleccionar al menos dos grupos de sub-valores para comparar.", parent=self)
            return

        self.result = {
            "data_type": selected_dt,
            "variable": selected_var, # Esta es la columna en formato Attr/Col/Unit
            "groups": selected_group_keys # Estas son las claves originales de los grupos
        }
        logger.info(f"Configuración de análisis continuo guardada: {self.result} para estudio {self.study_id}.")
        self.destroy()

    def load_data_types(self):
        """Carga los Tipos de Dato disponibles (solo Cinemática)."""
        from tkinter import messagebox
        try:
            # Llama al método del servicio que ahora solo devuelve ["Cinematica"] o []
            data_types = self.analysis_service.get_available_frequencies_for_study(self.study_id)
            
            if "Cinematica" in data_types:
                self.data_type_combobox['values'] = ["Cinematica"]
                self.selected_data_type.set("Cinematica")
                self.on_data_type_selected() # Cargar variables automáticamente
            else: 
                self.data_type_combobox['values'] = []
                self.selected_data_type.set("")
                self.variable_combobox['values'] = []
                self.selected_variable.set("")
                self.variable_combobox.config(state="disabled")
                self.clear_group_selectors()
                self.add_group_button.config(state="disabled")
                messagebox.showwarning("No Disponible",
                                       "El análisis continuo actualmente solo está disponible para el Tipo de Dato 'Cinematica'.\n"
                                       "No se encontraron archivos cinemáticos procesados en este estudio.",
                                       parent=self)
        except Exception as e:
            logger.error(f"Error cargando Tipos de Dato para estudio {self.study_id}: {e}", exc_info=True)
            self.data_type_combobox['values'] = []
            self.selected_data_type.set("")
            self.variable_combobox.config(state="disabled")
            self.clear_group_selectors()
            self.add_group_button.config(state="disabled")
            messagebox.showerror("Error", f"Error cargando Tipos de Dato: {e}", parent=self)


    def on_data_type_selected(self, event=None):
        """Llamado cuando se selecciona un Tipo de Dato. Carga las variables/columnas."""
        selected_dt = self.selected_data_type.get()
        self.selected_variable.set("") 
        self.variable_combobox['values'] = []
        self.clear_group_selectors()
        self.add_group_button.config(state="disabled")


        if selected_dt: # Debería ser "Cinematica"
            logger.debug(f"Tipo de Dato seleccionada: {selected_dt}. Cargando variables...")
            self.load_variables_for_data_type(selected_dt)
        else:
            self.variable_combobox.config(state="disabled")

    def load_variables_for_data_type(self, data_type: str):
        """Carga las variables/columnas disponibles para el Tipo de Dato seleccionado."""
        try:
            # Llama al método del servicio que devuelve columnas en formato Attr/Col/Unit
            variables = self.analysis_service.get_data_columns_for_frequency(self.study_id, data_type)
            if variables:
                self.variable_combobox['values'] = variables
                self.variable_combobox.config(state="readonly")
            else: 
                self.variable_combobox.config(state="disabled")
                logger.warning(f"No se encontraron variables para el Tipo de Dato '{data_type}' en estudio {self.study_id}.")
            
            self.selected_variable.set("") # Limpiar selección previa de variable
            self.clear_group_selectors() # Limpiar grupos si las variables cambian
            self.add_group_button.config(state="disabled") # Deshabilitar hasta que se seleccione variable
        except Exception as e:
            logger.error(f"Error cargando variables para Tipo de Dato {data_type}, estudio {self.study_id}: {e}", exc_info=True)
            self.variable_combobox['values'] = []
            self.selected_variable.set("")
            self.variable_combobox.config(state="disabled")
            self.clear_group_selectors()
            self.add_group_button.config(state="disabled")

    def on_variable_selected(self, event=None):
        """Llamado cuando se selecciona una variable. Carga los selectores de grupo."""
        selected_var = self.selected_variable.get()
        self.clear_group_selectors() 

        if selected_var:
            logger.debug(f"Variable seleccionada: {selected_var}. Activando selectores de grupo...")
            self.add_group_button.config(state="normal")
            # Añadir dos selectores de grupo por defecto
            self.add_group_selector()
            self.add_group_selector()
        else:
            self.add_group_button.config(state="disabled")

    def add_group_selector(self, initial_value_key=""):
        """Añade una nueva fila para seleccionar un grupo de sub-valores."""
        group_var = tk.StringVar()
        
        self.selected_groups_vars.append(group_var)

        frame = ttk.Frame(self.groups_inner_frame)
        frame.pack(fill=tk.X, pady=2, padx=(0, 5)) # Añadir padx para que no pegue al scrollbar
        self.group_selector_frames.append(frame)

        # Obtener grupos disponibles (display_name, original_key)
        # Para continuo, siempre usamos "Cinematica" como tipo de dato para buscar grupos
        data_type_for_groups = self.selected_data_type.get()
        if not data_type_for_groups: # Fallback si no hay tipo de dato seleccionado (raro)
            data_type_for_groups = "Cinematica"

        available_groups_tuples = self.analysis_service.get_discrete_analysis_groups(self.study_id, data_type_for_groups)
        
        # Actualizar el mapeo y obtener solo los display names para el combobox
        self.group_display_to_key_map = {display: key for display, key in available_groups_tuples}
        group_display_names = [display for display, _ in available_groups_tuples]


        combo = ttk.Combobox(frame, textvariable=group_var, values=group_display_names, state="readonly", width=40)
        combo.pack(side=tk.LEFT, padx=(0,5), expand=True, fill=tk.X)
        
        if initial_value_key: # Si se provee una clave inicial (ej. al cargar config)
            display_for_initial_key = next((d for d, k in available_groups_tuples if k == initial_value_key), None)
            if display_for_initial_key:
                group_var.set(display_for_initial_key)
            else: 
                group_var.set("")


        remove_button = ttk.Button(frame, text="🗑️", command=lambda f=frame, v=group_var: self.remove_group_selector(f, v), width=3)
        remove_button.pack(side=tk.RIGHT)

        self.groups_inner_frame.update_idletasks()
        self.groups_canvas.config(scrollregion=self.groups_canvas.bbox("all"))


    def remove_group_selector(self, frame_to_remove, var_to_remove):
        """Elimina una fila de selector de grupo."""
        # No hay restricción mínima aquí, la validación es en _on_accept
        try:
            self.selected_groups_vars.remove(var_to_remove)
            self.group_selector_frames.remove(frame_to_remove)
            frame_to_remove.destroy()
            
            self.groups_inner_frame.update_idletasks()
            self.groups_canvas.config(scrollregion=self.groups_canvas.bbox("all"))
        except ValueError:
            logger.warning("Intento de eliminar un selector de grupo que ya no existe.")


    def clear_group_selectors(self):
        """Elimina todos los selectores de grupo."""
        for frame in self.group_selector_frames:
            frame.destroy()
        self.group_selector_frames.clear()
        self.selected_groups_vars.clear()
        self.groups_inner_frame.update_idletasks()
        self.groups_canvas.config(scrollregion=self.groups_canvas.bbox("all"))

    def get_selected_group_keys(self) -> list[str]:
        """Obtiene las claves originales de los grupos seleccionados, eliminando duplicados y vacíos."""
        selected_keys = set() 
        for group_var in self.selected_groups_vars:
            display_name = group_var.get()
            if display_name and display_name in self.group_display_to_key_map:
                selected_keys.add(self.group_display_to_key_map[display_name])
        return list(selected_keys)

    def _on_cancel(self, event=None):
        """Acción al presionar Cancelar o cerrar la ventana."""
        self.result = None
        self.destroy()

if __name__ == '__main__':
    # Ejemplo de cómo usar el diálogo (para pruebas)
    root = tk.Tk()
    root.title("Ventana Principal (Dummy)")

    # Crear un Dummy AnalysisService para probar
    class DummyAnalysisService:
        def __init__(self):
            logger.info("DummyAnalysisService inicializado.")
            self.dummy_study_details = { # Simulación de detalles de estudio para grupos
                'independent_variables': [
                    {'name': 'Condicion', 'sub_values': ['PRE', 'POST', 'CONTROL']},
                    {'name': 'Salto', 'sub_values': ['CMJ', 'SJ', 'DJ']}
                ]
            }
            self.dummy_aliases = {'PRE': 'Antes', 'POST': 'Después', 'CMJ': 'Salto CMJ'}
            # Simular algunas claves de grupo que podrían existir en el estudio
            self.dummy_unique_group_keys = {
                "Condicion=PRE;Salto=CMJ",
                "Condicion=POST;Salto=CMJ",
                "Condicion=CONTROL;Salto=SJ",
                "Condicion=PRE;Salto=DJ"
            }

        def get_available_frequencies_for_study(self, study_id): # Nombre antiguo, pero la lógica interna del dialog lo usa
            logger.info(f"Dummy: get_available_frequencies_for_study (para Tipos de Dato) ({study_id})")
            # return ["Cinematica", "Cinetica"] # Para probar si solo se muestra Cinemática
            return ["Cinematica"] # Caso normal
            # return ["Cinetica"] # Para probar el caso donde Cinemática no está disponible

        def get_data_columns_for_frequency(self, study_id, frequency): # Nombre antiguo
            logger.info(f"Dummy: get_data_columns_for_frequency (para Columnas) ({study_id}, {frequency})")
            if frequency == "Cinematica":
                return [
                    "LAnkleAngles/X/deg", "LAnkleAngles/Y/deg", "LAnkleAngles/Z/deg",
                    "RKneeAngles/X/deg", "RKneeAngles/Y/deg", "RKneeAngles/Z/deg",
                    "HipForce/Magnitude/N", "PelvisAngle/AnteriorTilt/deg"
                ]
            return []

        # Este método es crucial para poblar los selectores de grupo
        def get_discrete_analysis_groups(self, study_id, data_type): # data_type es el antiguo 'frequency'
            logger.info(f"Dummy: get_discrete_analysis_groups({study_id}, {data_type})")
            if data_type != "Cinematica": 
                return []

            groups_with_display_names = []
            sorted_group_keys = sorted(list(self.dummy_unique_group_keys))
            
            for i, group_key in enumerate(sorted_group_keys):
                display_parts = []
                if group_key != "SinGrupo":
                    for part in group_key.split(';'):
                        try:
                            vi_name, sub_val = part.split('=', 1)
                            alias = self.dummy_aliases.get(sub_val, sub_val)
                            display_parts.append(f"{vi_name}: {alias}")
                        except ValueError:
                            display_parts.append(part) # Fallback si el formato no es VI=SubValor
                base_display_name = ", ".join(display_parts) if display_parts else "Grupo General"
                full_display_name = f"Grupo {i+1} - {base_display_name}"
                groups_with_display_names.append((full_display_name, group_key))
            
            groups_with_display_names.sort(key=lambda x: x[0]) # Ordenar por nombre de display
            return groups_with_display_names

    dummy_service = DummyAnalysisService()
    # Para que el dummy de get_discrete_analysis_groups funcione correctamente si necesitara
    # acceder a study_service.get_study_aliases() o get_study_details() internamente (aunque el dummy actual no lo hace explícitamente)
    # se podría inyectar un study_service dummy aquí si fuera necesario.
    # Por ahora, el dummy_analysis_service es autosuficiente para los datos que provee.
    study_id_test = 1

    def open_dialog():
        dialog = ContinuousAnalysisConfigDialog(root, dummy_service, study_id_test)
        root.wait_window(dialog)
        if dialog.result:
            print("Configuración guardada:", dialog.result)
        else:
            print("Diálogo cancelado o cerrado.")

    ttk.Button(root, text="Abrir Diálogo de Análisis Continuo", command=open_dialog).pack(padx=20, pady=20)
    root.geometry("300x100")
    root.mainloop()
