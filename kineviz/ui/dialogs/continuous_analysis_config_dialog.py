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

        self.title("Configurar Análisis Continuo")
        # Definir un tamaño inicial, se puede ajustar
        self.geometry("600x400")
        # Hacer modal
        self.grab_set()
        self.transient(parent)

        self.result = None # Para almacenar la configuración si se guarda

        # --- Variables de Tkinter ---
        self.selected_frequency = tk.StringVar()
        self.selected_variable = tk.StringVar()
        # Añadir más StringVars para otras selecciones (grupos, etc.)

        self.create_widgets()
        self.load_frequencies() # Cargar frecuencias después de crear widgets

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
        freq_frame = ttk.LabelFrame(main_frame, text="1. Seleccionar Tipo de Datos")
        freq_frame.pack(fill=tk.X, padx=5, pady=(0, 10))

        ttk.Label(freq_frame, text="Tipo de Dato:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.frequency_combobox = ttk.Combobox(
            freq_frame,
            textvariable=self.selected_frequency,
            state="readonly",
            width=25 # Ajustar ancho según sea necesario
        )
        self.frequency_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.frequency_combobox.bind("<<ComboboxSelected>>", self.on_frequency_selected)

        # --- Sección de Selección de Variable ---
        var_frame = ttk.LabelFrame(main_frame, text="2. Seleccionar Variable a Analizar")
        var_frame.pack(fill=tk.X, padx=5, pady=(0, 10))

        ttk.Label(var_frame, text="Variable:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.variable_combobox = ttk.Combobox(
            var_frame,
            textvariable=self.selected_variable,
            state="disabled", # Inicialmente deshabilitado
            width=35 # Ajustar ancho
        )
        self.variable_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        # Opcional: self.variable_combobox.bind("<<ComboboxSelected>>", self.on_variable_selected)

        # Placeholder para futuras secciones (Grupos)
        ttk.Label(main_frame, text="Más opciones de configuración (Grupos de Sub-valores) - En desarrollo").pack(pady=10)


        # --- Botones de Acción ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)

        ttk.Button(button_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.RIGHT, padx=(5,0))
        ttk.Button(button_frame, text="Aceptar", command=self._on_accept, style="Accent.TButton").pack(side=tk.RIGHT) # Estilo opcional

    def _on_accept(self):
        """Acción al presionar Aceptar."""
        selected_freq = self.selected_frequency.get()
        selected_var = self.selected_variable.get()
        from tkinter import messagebox # Mover import aquí

        if not selected_freq:
            messagebox.showwarning("Advertencia", "Debe seleccionar una frecuencia.", parent=self)
            return
        
        if not selected_var: # Validar que se haya seleccionado una variable
            messagebox.showwarning("Advertencia", "Debe seleccionar una variable a analizar.", parent=self)
            return

        # Aquí se recolectaría la configuración completa
        self.result = {
            "frequency": selected_freq,
            "variable": selected_var
            # Añadir más parámetros a medida que se implementen
        }
        logger.info(f"Configuración de análisis continuo guardada: {self.result} para estudio {self.study_id}.")
        self.destroy()

    def load_frequencies(self):
        """Carga las frecuencias disponibles en el Combobox."""
        try:
            frequencies = self.analysis_service.get_available_frequencies_for_study(self.study_id)
            if frequencies:
                self.frequency_combobox['values'] = frequencies
                if len(frequencies) == 1: # Si solo hay una, seleccionarla
                    self.selected_frequency.set(frequencies[0])
                    self.on_frequency_selected() # Cargar variables automáticamente
                # Opcional: seleccionar la primera por defecto si hay varias y no se autoseleccionó una única
                # elif frequencies:
                #    self.selected_frequency.set(frequencies[0]) # Podrías comentar esto si no quieres preselección
                #    self.on_frequency_selected()
            else: # No hay frecuencias disponibles
                self.frequency_combobox['values'] = []
                self.selected_frequency.set("")
                self.variable_combobox['values'] = [] # Limpiar variables
                self.selected_variable.set("")
                self.variable_combobox.config(state="disabled") # Deshabilitar variables
        except Exception as e:
            logger.error(f"Error cargando frecuencias para estudio {self.study_id}: {e}", exc_info=True)
            self.frequency_combobox['values'] = []
            self.selected_frequency.set("")
            self.variable_combobox['values'] = []
            self.selected_variable.set("")
            self.variable_combobox.config(state="disabled")
            # Mostrar error al usuario si es necesario

    def on_frequency_selected(self, event=None):
        """Llamado cuando se selecciona una frecuencia. Carga las variables/columnas."""
        selected_freq = self.selected_frequency.get()
        self.selected_variable.set("") # Limpiar selección de variable anterior
        self.variable_combobox['values'] = [] # Limpiar lista de variables

        if selected_freq:
            logger.debug(f"Tipo de Dato seleccionada: {selected_freq}. Cargando variables...")
            self.load_variables_for_frequency(selected_freq)
        else:
            self.variable_combobox.config(state="disabled") # Deshabilitar si no hay frecuencia

    def load_variables_for_frequency(self, frequency: str):
        """Carga las variables/columnas disponibles para la frecuencia seleccionada."""
        try:
            variables = self.analysis_service.get_data_columns_for_frequency(self.study_id, frequency)
            if variables:
                self.variable_combobox['values'] = variables
                self.variable_combobox.config(state="readonly")
                # Opcional: seleccionar la primera variable por defecto
                # if variables: # Podrías comentar esto si no quieres preselección
                #    self.selected_variable.set(variables[0])
            else: # No hay variables para la frecuencia seleccionada
                self.variable_combobox.config(state="disabled")
                logger.warning(f"No se encontraron variables para la frecuencia '{frequency}' en estudio {self.study_id}.")
        except Exception as e:
            logger.error(f"Error cargando variables para frecuencia {frequency}, estudio {self.study_id}: {e}", exc_info=True)
            self.variable_combobox['values'] = []
            self.selected_variable.set("")
            self.variable_combobox.config(state="disabled")
            # Mostrar error al usuario si es necesario

    # def on_variable_selected(self, event=None):
    # """Llamado cuando se selecciona una variable. Podría usarse para cargar algo más."""
    # selected_var = self.selected_variable.get()
    # if selected_var:
    # logger.debug(f"Variable seleccionada: {selected_var}")
    # # Aquí se podría cargar la siguiente sección, por ejemplo, grupos de descriptores
    # else:
    # # Limpiar la siguiente sección si la variable se deselecciona
    # pass


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
        # Añadir métodos que el diálogo podría llamar en el futuro
        def get_available_frequencies_for_study(self, study_id):
            logger.info(f"Dummy: get_available_frequencies_for_study({study_id})")
            return ["Cinematica", "Cinetica"]

        def get_data_columns_for_frequency(self, study_id, frequency):
            logger.info(f"Dummy: get_data_columns_for_frequency({study_id}, {frequency})")
            if frequency == "Cinematica":
                return ["LAnkleAngles_X", "LAnkleAngles_Y", "LAnkleAngles_Z", "RKneeAngles_X"]
            return []

        def get_study_groups_for_comparison(self, study_id):
            logger.info(f"Dummy: get_study_groups_for_comparison({study_id})")
            return [("Grupo A - Cond1", "VI1=A;VI2=Cond1"), ("Grupo B - Cond2", "VI1=B;VI2=Cond2")]

    dummy_service = DummyAnalysisService()
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
