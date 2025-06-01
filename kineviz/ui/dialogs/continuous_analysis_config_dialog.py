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
        # Añadir más StringVars para otras selecciones (variable, grupos, etc.)

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

        # --- Sección de Selección de Frecuencia ---
        freq_frame = ttk.LabelFrame(main_frame, text="1. Seleccionar Frecuencia de Datos")
        freq_frame.pack(fill=tk.X, padx=5, pady=(0, 10))

        ttk.Label(freq_frame, text="Frecuencia:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.frequency_combobox = ttk.Combobox(
            freq_frame,
            textvariable=self.selected_frequency,
            state="readonly",
            width=25 # Ajustar ancho según sea necesario
        )
        self.frequency_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        # self.frequency_combobox.bind("<<ComboboxSelected>>", self.on_frequency_selected) # Para cargar variables después

        # Placeholder para futuras secciones (Variable, Grupos)
        ttk.Label(main_frame, text="Más opciones de configuración (Variable, Grupos) - En desarrollo").pack(pady=10)


        # --- Botones de Acción ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)

        ttk.Button(button_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.RIGHT, padx=(5,0))
        ttk.Button(button_frame, text="Aceptar", command=self._on_accept, style="Accent.TButton").pack(side=tk.RIGHT) # Estilo opcional

    def _on_accept(self):
        """Acción al presionar Aceptar."""
        selected_freq = self.selected_frequency.get()
        if not selected_freq:
            # Usar messagebox de tkinter
            from tkinter import messagebox
            messagebox.showwarning("Advertencia", "Debe seleccionar una frecuencia.", parent=self)
            return

        # Aquí se recolectaría la configuración completa
        self.result = {
            "frequency": selected_freq
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
                # Opcional: seleccionar la primera por defecto
                # self.selected_frequency.set(frequencies[0])
                # self.on_frequency_selected() # Cargar variables si se selecciona una por defecto
            else:
                self.frequency_combobox['values'] = []
                self.selected_frequency.set("")
                # Considerar deshabilitar el combobox o mostrar mensaje
                # self.frequency_combobox.config(state="disabled")
                # (Manejar caso donde no hay frecuencias)
        except Exception as e:
            logger.error(f"Error cargando frecuencias para estudio {self.study_id}: {e}", exc_info=True)
            self.frequency_combobox['values'] = []
            self.selected_frequency.set("")
            # Mostrar error al usuario si es necesario

    # def on_frequency_selected(self, event=None):
    #     """Llamado cuando se selecciona una frecuencia. Carga las variables/columnas."""
    #     selected_freq = self.selected_frequency.get()
    #     if selected_freq:
    #         logger.debug(f"Frecuencia seleccionada: {selected_freq}. Cargando variables...")
    #         # Aquí se llamaría a cargar las variables/columnas para esta frecuencia
    #         # self.load_variables_for_frequency(selected_freq)
    #     else:
    #         # Limpiar combobox de variables si no hay frecuencia
    #         # self.variable_combobox['values'] = []
    #         # self.selected_variable.set("")
    #         pass


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
