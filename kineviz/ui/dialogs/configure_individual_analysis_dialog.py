import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Tuple # Añadir Tuple para type hint

from kineviz.core.services.analysis_service import AnalysisService
# Importar validador necesario
from kineviz.ui.utils.validators import validate_filename_for_study_criteria
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip
from kineviz.config.settings import AppSettings # Import AppSettings
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # Import font utilities

logger = logging.getLogger(__name__)


class ConfigureIndividualAnalysisDialog(tk.Toplevel):
    """Diálogo para configurar los parámetros de un análisis individual."""

    def __init__(self, parent, analysis_service: AnalysisService, study_id: int, settings: AppSettings):
        super().__init__(parent)
        self.parent = parent
        self.analysis_service = analysis_service
        self.study_id = study_id
        self.settings = settings # Store AppSettings instance

        self.title("Configurar Nuevo Análisis Individual")
        # Defer grab_set until after initial sizing
        self.parent_window = parent # Store parent for transient and centering
        self._is_adjusting_size = False # Flag to prevent recursion

        # --- Nuevas variables de estado para el flujo ---
        self.vi_grouping_mode = tk.StringVar(value="") # '1VI' o '2VIs'
        self.primary_vi_var = tk.StringVar() # VI seleccionada en modo 1VI
        self.fixed_vi_var = tk.StringVar() # VI a fijar en modo 2VIs
        self.fixed_descriptor_var = tk.StringVar() # Sub-valor a fijar en modo 2VIs
        self.all_vi_names = [] # Nombres de las VIs del estudio
        self.all_descriptors_by_vi = {} # {vi_name: [desc1, desc2]}
        self.study_aliases = {} # Alias del estudio

        # --- Variables existentes (algunas se reutilizan) ---
        self.frequency_var = tk.StringVar()
        self.calculation_var = tk.StringVar()
        self.available_frequencies = [] # Se carga dinámicamente
        self.available_calculations = ["Maximo", "Minimo", "Rango"] # Mantener fijos por ahora

        self.group_selector_frames = [] # Lista de frames para cada selector de grupo
        self.group_selector_vars = [] # Lista de StringVars para grupos seleccionados (reutilizado)
        self.available_groups_filtered = {} # Diccionario {display_name: original_key} - AHORA FILTRADO

        # Variables para la columna y supuestos (reutilizadas)
        self.column_var = tk.StringVar()
        self.available_columns = []
        self.parametric_var = tk.BooleanVar(value=True)
        self.paired_var = tk.BooleanVar(value=False)

        # Variable para el nombre del análisis (reutilizada)
        self.analysis_name_var = tk.StringVar()
        self.group_selector_tooltips = [] # NUEVO: Para almacenar instancias de Tooltip

        self.result = None # Initialize result attribute

        # Definir estilo para el botón de ayuda
        style = ttk.Style()
        style.configure("Help.TButton", foreground="white", background="blue")

        # --- Setup for scrollable area ---
        self.container_frame = ttk.Frame(self)
        self.canvas = tk.Canvas(self.container_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, padding="15")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        # Removed problematic canvas.bind("<Configure>") that forced inner frame width
        self.canvas.interior_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set) # Assuming self.scrollbar is vertical

        # Add horizontal scrollbar
        self.h_scrollbar = ttk.Scrollbar(self.container_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)

        # Grid layout for canvas and scrollbars
        self.container_frame.grid_rowconfigure(0, weight=1)
        self.container_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        # Scrollbars are created but not gridded initially

        self.container_frame.pack(fill=tk.BOTH, expand=True)

        self.create_widgets(self.scrollable_frame) 
        should_continue_init = self.load_initial_data() 
        
        if not should_continue_init:
            return 

        self.update_idletasks()
        # Set a very small minsize initially to allow shrink-wrapping to content
        self.minsize(1, 1)
        
        self._resize_to_content() # Set initial size based on content

        # Now set a practical minimum size for user manual resizing and future content changes
        # This prevents the dialog from becoming too small if content is very small or removed.
        self.minsize(200, 150) # Adjusted to a smaller practical minimum

        self._center_dialog() # Center after initial size
        
        self.grab_set()
        self.transient(self.parent_window)
        self.bind("<Configure>", self._on_manual_resize)


    def _on_manual_resize(self, event):
        # If the event is for the Toplevel window itself and we are not already adjusting size
        if event.widget == self and not self._is_adjusting_size:
            # Immediately try to resize to content. This will handle all cases:
            # - User tries to expand beyond content: snaps back.
            # - User tries to shrink: respects content size / minsize, adds scrollbars if needed.
            self._resize_to_content()
        # Note: _is_adjusting_size flag is set within _resize_to_content

    def _resize_to_content(self):
        if self._is_adjusting_size:
            return
        self._is_adjusting_size = True

        self.update_idletasks()
        min_dialog_width, min_dialog_height = self.wm_minsize()

        content_req_width = self.scrollable_frame.winfo_reqwidth()
        content_req_height = self.scrollable_frame.winfo_reqheight()
        
        target_dialog_width = max(content_req_width, min_dialog_width)
        target_dialog_height = max(content_req_height, min_dialog_height)

        max_screen_width = int(self.winfo_screenwidth() * 0.9)
        max_screen_height = int(self.winfo_screenheight() * 0.9)
        target_dialog_width = min(target_dialog_width, max_screen_width)
        target_dialog_height = min(target_dialog_height, max_screen_height)
        
        current_dialog_width = self.winfo_width()
        current_dialog_height = self.winfo_height()

        if target_dialog_width != current_dialog_width or \
           target_dialog_height != current_dialog_height:
            self.geometry(f"{target_dialog_width}x{target_dialog_height}")
            # self.update_idletasks() # Called in _update_scrollbars_and_region
            
        self._update_scrollbars_and_region()
        self._is_adjusting_size = False

    def _update_scrollbars_and_region(self):
        self.update_idletasks()

        content_req_width = self.scrollable_frame.winfo_reqwidth()
        content_req_height = self.scrollable_frame.winfo_reqheight()
        
        current_dialog_width = self.winfo_width()
        current_dialog_height = self.winfo_height()

        canvas_viewport_width = current_dialog_width
        canvas_viewport_height = current_dialog_height

        v_scroll_needed = content_req_height > canvas_viewport_height
        h_scroll_needed = content_req_width > canvas_viewport_width
        
        if v_scroll_needed:
            if not self.scrollbar.winfo_ismapped(): self.scrollbar.grid(row=0, column=1, sticky="ns")
            canvas_viewport_width -= self.scrollbar.winfo_reqwidth()
        elif self.scrollbar.winfo_ismapped(): self.scrollbar.grid_remove()

        if not h_scroll_needed and v_scroll_needed:
            h_scroll_needed = content_req_width > canvas_viewport_width

        if h_scroll_needed:
            if not self.h_scrollbar.winfo_ismapped(): self.h_scrollbar.grid(row=1, column=0, sticky="ew")
            canvas_viewport_height -= self.h_scrollbar.winfo_reqheight()
        elif self.h_scrollbar.winfo_ismapped(): self.h_scrollbar.grid_remove()
        
        if not v_scroll_needed and h_scroll_needed:
             v_scroll_needed = content_req_height > canvas_viewport_height
             if v_scroll_needed and not self.scrollbar.winfo_ismapped():
                 self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _show_input_help(self, title: str, message: str):
        """Muestra un popup de ayuda simple."""
        messagebox.showinfo(title, message, parent=self)

    def create_widgets(self, parent_frame): # parent_frame is self.scrollable_frame
        """Crea los widgets del diálogo."""
        main_frame = parent_frame # Use the passed scrollable_frame
        # main_frame.pack(fill=tk.BOTH, expand=True) # Not needed
        main_frame.columnconfigure(1, weight=1) # Columna de Combobox/Entry expandible

        row_idx = 0
        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)

        # --- Selección de Tipo de Dato y Cálculo ---
        ttk.Label(main_frame, text="Tipo de Dato:").grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        freq_frame = ttk.Frame(main_frame)
        freq_frame.grid(row=row_idx, column=1, sticky="ew")
        self.freq_combo = ttk.Combobox(freq_frame, textvariable=self.frequency_var, state="disabled", font=scaled_font) # Cambiado a disabled
        self.freq_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        freq_long_text_discrete = "Tipo de datos a analizar.\nPara análisis discreto, actualmente solo 'Cinematica' está soportado y se selecciona automáticamente."
        freq_short_text_discrete = "Tipo de datos (fijo a 'Cinematica' para discreto)."
        freq_help_btn_discrete = ttk.Button(freq_frame, text="?", width=3, style="Help.TButton",
                                            command=lambda: self._show_input_help("Ayuda: Tipo de Dato", freq_long_text_discrete))
        freq_help_btn_discrete.pack(side=tk.LEFT)
        Tooltip(freq_help_btn_discrete, text=freq_long_text_discrete, short_text=freq_short_text_discrete, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        ttk.Label(main_frame, text="Cálculo:").grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        calc_frame = ttk.Frame(main_frame)
        calc_frame.grid(row=row_idx, column=1, sticky="ew")
        self.calc_combo = ttk.Combobox(calc_frame, textvariable=self.calculation_var, values=self.available_calculations, state="readonly", font=scaled_font)
        self.calc_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.calc_combo.bind("<<ComboboxSelected>>", self.update_available_groups) # Actualizar grupos al seleccionar cálculo
        calc_long_text = "El tipo de cálculo (Maximo, Minimo, Rango) aplicado a los datos en las tablas de resumen que se usarán para el análisis."
        calc_short_text = "Cálculo (Maximo, Minimo, Rango) de tablas resumen."
        calc_help_btn = ttk.Button(calc_frame, text="?", width=3, style="Help.TButton",
                                   command=lambda: self._show_input_help("Ayuda: Cálculo", calc_long_text))
        calc_help_btn.pack(side=tk.LEFT)
        Tooltip(calc_help_btn, text=calc_long_text, short_text=calc_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- NUEVO: Selección de Modo de Agrupación (1 VI vs 2 VIs) ---
        vi_mode_frame = ttk.Frame(main_frame)
        vi_mode_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=10)
        
        label_agrupar_frame = ttk.Frame(vi_mode_frame)
        label_agrupar_frame.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(label_agrupar_frame, text="Agrupar por:").pack(side=tk.LEFT)
        agrupar_long_text = ("Define cómo se formarán los grupos para la comparación:\n\n"
                             "1 Variable Independiente (1VI):\n"
                             "  Compara los diferentes sub-valores de UNA ÚNICA VI.\n"
                             "  Ej: Comparar 'PRE' vs 'POST' de la VI 'Condicion'.\n\n"
                             "2 Variables Independientes (2VIs):\n"
                             "  Compara los sub-valores de una VI, MANTENIENDO FIJO un sub-valor de OTRA VI.\n"
                             "  Ej: Comparar 'CMJ' vs 'SJ' de la VI 'TipoSalto', pero solo para la condición 'PRE' de la VI 'Condicion'.")
        agrupar_short_text = "Modo de agrupar datos (1VI o 2VIs)."
        agrupar_help_btn = ttk.Button(label_agrupar_frame, text="?", width=3, style="Help.TButton",
                                      command=lambda: self._show_input_help("Ayuda: Modo de Agrupación", agrupar_long_text))
        agrupar_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(agrupar_help_btn, text=agrupar_long_text, short_text=agrupar_short_text, enabled=self.settings.enable_hover_tooltips)
        
        self.one_vi_button = ttk.Button(vi_mode_frame, text="1 Variable Independiente", command=lambda: self.set_vi_grouping_mode('1VI'))
        self.one_vi_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.one_vi_button, text="Agrupar datos comparando los sub-valores de una única Variable Independiente.", short_text="Agrupar por 1 VI.", enabled=self.settings.enable_hover_tooltips)
        self.two_vi_button = ttk.Button(vi_mode_frame, text="2 Variables Independientes", command=lambda: self.set_vi_grouping_mode('2VIs'))
        self.two_vi_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.two_vi_button, text="Agrupar datos comparando sub-valores de una VI, manteniendo fijo un sub-valor de otra VI.", short_text="Agrupar por 2 VIs.", enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Contenedores para los pasos siguientes (inicialmente ocultos) ---
        # Frame para selección de VI primaria (modo 1VI)
        self.one_vi_config_frame = ttk.Frame(main_frame)
        self.one_vi_config_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=0)
        self.one_vi_config_frame.grid_remove() # Ocultar inicialmente
        self.one_vi_config_frame.columnconfigure(1, weight=1) # Permitir que el combo se expanda
        ttk.Label(self.one_vi_config_frame, text="Agrupar por VI:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        primary_vi_frame = ttk.Frame(self.one_vi_config_frame)
        primary_vi_frame.grid(row=0, column=1, sticky="ew")
        self.primary_vi_combo = ttk.Combobox(primary_vi_frame, textvariable=self.primary_vi_var, state="readonly", font=scaled_font)
        self.primary_vi_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.primary_vi_combo.bind("<<ComboboxSelected>>", self.update_available_groups) # Actualizar grupos al seleccionar VI primaria
        primary_vi_help_long_text = "Seleccione la Variable Independiente principal cuyos sub-valores (con alias) formarán los grupos a comparar."
        primary_vi_help_short_text = "VI principal para agrupar."
        primary_vi_help_btn = ttk.Button(primary_vi_frame, text="?", width=3, style="Help.TButton",
                                         command=lambda: self._show_input_help("Ayuda: Agrupar por VI", primary_vi_help_long_text))
        primary_vi_help_btn.pack(side=tk.LEFT)
        Tooltip(primary_vi_help_btn, text=primary_vi_help_long_text, short_text=primary_vi_help_short_text, enabled=self.settings.enable_hover_tooltips)

        # Frame para selección de VI fija y sub-valor fijo (modo 2VIs)
        self.two_vi_config_frame = ttk.Frame(main_frame)
        self.two_vi_config_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=0)
        self.two_vi_config_frame.grid_remove() # Ocultar inicialmente
        self.two_vi_config_frame.columnconfigure(1, weight=1)

        ttk.Label(self.two_vi_config_frame, text="VI a Fijar:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        fixed_vi_frame = ttk.Frame(self.two_vi_config_frame)
        fixed_vi_frame.grid(row=0, column=1, sticky="ew")
        self.fixed_vi_combo = ttk.Combobox(fixed_vi_frame, textvariable=self.fixed_vi_var, state="readonly", font=scaled_font)
        self.fixed_vi_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.fixed_vi_combo.bind("<<ComboboxSelected>>", self._update_fixed_descriptor_options) # Actualizar sub-valores al seleccionar VI fija
        fixed_vi_help_long_text = "Seleccione la Variable Independiente que permanecerá constante mientras se comparan los sub-valores de la otra VI."
        fixed_vi_help_short_text = "VI que se mantendrá constante."
        fixed_vi_help_btn = ttk.Button(fixed_vi_frame, text="?", width=3, style="Help.TButton",
                                       command=lambda: self._show_input_help("Ayuda: VI a Fijar", fixed_vi_help_long_text))
        fixed_vi_help_btn.pack(side=tk.LEFT)
        Tooltip(fixed_vi_help_btn, text=fixed_vi_help_long_text, short_text=fixed_vi_help_short_text, enabled=self.settings.enable_hover_tooltips)

        self.fixed_descriptor_label = ttk.Label(self.two_vi_config_frame, text="Valor Fijo:")
        self.fixed_descriptor_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        fixed_desc_frame = ttk.Frame(self.two_vi_config_frame)
        fixed_desc_frame.grid(row=1, column=1, sticky="ew")
        self.fixed_descriptor_combo = ttk.Combobox(fixed_desc_frame, textvariable=self.fixed_descriptor_var, state="readonly", font=scaled_font)
        self.fixed_descriptor_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.fixed_descriptor_combo.bind("<<ComboboxSelected>>", self.update_available_groups) # Actualizar grupos al seleccionar descriptor fijo
        fixed_desc_help_long_text = ("Seleccione el sub-valor (con alias) de la 'VI a Fijar' que se mantendrá constante.\n"
                                     "Los grupos a comparar se formarán con los sub-valores de la otra VI, dentro de este contexto.")
        fixed_desc_help_short_text = "Sub-valor constante de la VI a fijar."
        fixed_desc_help_btn = ttk.Button(fixed_desc_frame, text="?", width=3, style="Help.TButton",
                                         command=lambda: self._show_input_help("Ayuda: Valor Fijo", fixed_desc_help_long_text))
        fixed_desc_help_btn.pack(side=tk.LEFT)
        Tooltip(fixed_desc_help_btn, text=fixed_desc_help_long_text, short_text=fixed_desc_help_short_text, enabled=self.settings.enable_hover_tooltips)

        row_idx += 1 # Incrementar fila para el siguiente elemento

        # --- Selección Dinámica de Grupos (Reutilizado, pero dentro de su propio frame) ---
        self.group_selection_outer_frame = ttk.LabelFrame(main_frame, text="Selección de Grupos a Comparar")
        self.group_selection_outer_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=10)
        self.group_selection_outer_frame.columnconfigure(0, weight=1)
        self.group_selection_outer_frame.grid_remove() # Ocultar inicialmente
        # Frame interno para los selectores (el que se usaba antes como group_frame)
        self.group_selectors_frame = ttk.Frame(self.group_selection_outer_frame)
        self.group_selectors_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Botón para añadir más grupos (movido aquí)
        add_group_button = ttk.Button(self.group_selection_outer_frame, text="+ Añadir Grupo",
                                      command=self.add_group_selector)
        add_group_button.pack(pady=5, anchor='w', padx=5) # Anclar a la izquierda
        Tooltip(add_group_button, text="Añadir otro grupo a la comparación. Se requieren al menos dos grupos.", short_text="Añadir grupo.", enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Selección de Columna (En su propio frame) ---
        self.column_frame = ttk.LabelFrame(main_frame, text="Variable a Analizar") # Usar LabelFrame
        self.column_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.column_frame.columnconfigure(1, weight=1)
        self.column_frame.grid_remove() # Ocultar inicialmente
        ttk.Label(self.column_frame, text="Columna:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        column_combo_frame = ttk.Frame(self.column_frame)
        column_combo_frame.grid(row=0, column=1, sticky="ew")
        self.column_combo = ttk.Combobox(column_combo_frame, textvariable=self.column_var, state="readonly", width=45, font=scaled_font) # Ajustar width si es necesario
        self.column_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.column_combo.bind("<<ComboboxSelected>>", self._on_column_selected) # Llamar al seleccionar columna
        column_help_long_text = ("Seleccione la columna de datos (variable dependiente) de las tablas de resumen que desea analizar.\n"
                                 "Las opciones se filtran a columnas comunes entre los grupos seleccionados.")
        column_help_short_text = "Variable dependiente a analizar."
        column_help_btn = ttk.Button(column_combo_frame, text="?", width=3, style="Help.TButton",
                                     command=lambda: self._show_input_help("Ayuda: Variable a Analizar", column_help_long_text))
        column_help_btn.pack(side=tk.LEFT)
        Tooltip(column_help_btn, text=column_help_long_text, short_text=column_help_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Supuestos Estadísticos (En su propio frame) ---
        self.assumptions_frame = ttk.LabelFrame(main_frame, text="Supuestos Estadísticos")
        self.assumptions_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        self.assumptions_frame.grid_remove() # Ocultar inicialmente

        parametric_frame = ttk.Frame(self.assumptions_frame)
        parametric_frame.pack(anchor="w", padx=5)
        ttk.Checkbutton(parametric_frame, text="Datos Paramétricos (Normalidad/Homocedasticidad)", variable=self.parametric_var).pack(side=tk.LEFT)
        parametric_help_long_text = ("Marque si sus datos cumplen los supuestos para pruebas paramétricas (ej. t-test, ANOVA):\n"
                                     "- Aproximadamente distribuidos normalmente.\n"
                                     "- Homogeneidad de varianzas (homocedasticidad) entre grupos.\n"
                                     "Si no se cumplen, se usarán pruebas no paramétricas (ej. Wilcoxon, Kruskal-Wallis).")
        parametric_help_short_text = "Cumplimiento de supuestos paramétricos."
        parametric_help_btn = ttk.Button(parametric_frame, text="?", width=3, style="Help.TButton",
                                         command=lambda: self._show_input_help("Ayuda: Datos Paramétricos", parametric_help_long_text))
        parametric_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(parametric_help_btn, text=parametric_help_long_text, short_text=parametric_help_short_text, enabled=self.settings.enable_hover_tooltips)

        paired_frame = ttk.Frame(self.assumptions_frame)
        paired_frame.pack(anchor="w", padx=5)
        ttk.Checkbutton(paired_frame, text="Muestras Pareadas (Mismos sujetos en todos los grupos)", variable=self.paired_var).pack(side=tk.LEFT)
        paired_help_long_text = ("Marque si los datos en los grupos a comparar provienen de los mismos participantes (medidas repetidas).\n"
                                 "Ej: Comparar 'PRE' vs 'POST' para los mismos sujetos.\n"
                                 "Si los grupos son independientes (diferentes sujetos), no marque esta opción.")
        paired_help_short_text = "Datos de muestras pareadas/repetidas."
        paired_help_btn = ttk.Button(paired_frame, text="?", width=3, style="Help.TButton",
                                     command=lambda: self._show_input_help("Ayuda: Muestras Pareadas", paired_help_long_text))
        paired_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(paired_help_btn, text=paired_help_long_text, short_text=paired_help_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Nombre del Análisis (En su propio frame) ---
        self.analysis_name_frame = ttk.LabelFrame(main_frame, text="Guardar Análisis Como") # Usar LabelFrame
        self.analysis_name_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.analysis_name_frame.columnconfigure(1, weight=1)
        self.analysis_name_frame.grid_remove() # Ocultar inicialmente
        ttk.Label(self.analysis_name_frame, text="Nombre:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        analysis_name_entry_frame = ttk.Frame(self.analysis_name_frame)
        analysis_name_entry_frame.grid(row=0, column=1, sticky="ew")
        ttk.Entry(analysis_name_entry_frame, textvariable=self.analysis_name_var, font=scaled_font).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        analysis_name_help_long_text = "Ingrese un nombre descriptivo para guardar este análisis.\nEvite caracteres especiales como / \\ : * ? \" < > |"
        analysis_name_help_short_text = "Nombre para guardar el análisis."
        analysis_name_help_btn = ttk.Button(analysis_name_entry_frame, text="?", width=3, style="Help.TButton",
                                            command=lambda: self._show_input_help("Ayuda: Nombre del Análisis", analysis_name_help_long_text))
        analysis_name_help_btn.pack(side=tk.LEFT)
        Tooltip(analysis_name_help_btn, text=analysis_name_help_long_text, short_text=analysis_name_help_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Botones de Acción (En su propio frame) ---
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="e", pady=10)
        self.button_frame.grid_remove() # Ocultar inicialmente
        self.save_button = ttk.Button(self.button_frame, text="Aceptar y Guardar Configuración", command=self._save_configuration_and_close, state=tk.DISABLED, style="Green.TButton") # Actualizado comando
        self.save_button.pack(side=tk.RIGHT, padx=5)
        Tooltip(self.save_button, text="Guardar la configuración actual del análisis y cerrar este diálogo.", short_text="Guardar config.", enabled=self.settings.enable_hover_tooltips)
        cancel_button_individual = ttk.Button(self.button_frame, text="Cancelar", command=self.destroy)
        cancel_button_individual.pack(side=tk.RIGHT)
        Tooltip(cancel_button_individual, text="Cerrar este diálogo sin guardar la configuración.", short_text="Cancelar.", enabled=self.settings.enable_hover_tooltips)


    def set_vi_grouping_mode(self, mode):
        """Configura la UI según se elija agrupar por 1 o 2 VIs."""
        self.vi_grouping_mode.set(mode)
        logger.info(f"Modo de agrupación seleccionado: {mode}")

        # Resetear selecciones dependientes
        self.primary_vi_var.set("")
        self.fixed_vi_var.set("")
        self.fixed_descriptor_var.set("")
        self.available_groups_filtered = {}
        self._clear_group_selectors(update_columns=False) # No actualizar columnas aún
        self.column_var.set("")
        self.column_combo['values'] = []
        self.save_button.config(state=tk.DISABLED)

        # Ocultar todos los frames de configuración específicos
        self.one_vi_config_frame.grid_remove()
        self.two_vi_config_frame.grid_remove()
        self.group_selection_outer_frame.grid_remove()
        self.column_frame.grid_remove()
        self.assumptions_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()

        # Mostrar el frame correspondiente al modo seleccionado
        if mode == '1VI':
            self.one_vi_config_frame.grid()
            self.primary_vi_combo['values'] = self.all_vi_names
            # Habilitar/deshabilitar botón 2VI
            self.one_vi_button.state(['pressed', 'disabled'])
            self.two_vi_button.state(['!pressed', '!disabled'])
        elif mode == '2VIs':
            if len(self.all_vi_names) < 2:
                 messagebox.showwarning("No disponible", "Se requieren al menos 2 Variables Independientes definidas en el estudio para agrupar por 2 VIs.", parent=self)
                 self.vi_grouping_mode.set("") # Resetear modo
                 if hasattr(self, 'one_vi_button'): self.one_vi_button.state(['!pressed', '!disabled']) 
                 if hasattr(self, 'two_vi_button'): self.two_vi_button.state(['!pressed', '!disabled'])
                 self._resize_to_content()
                 return
            self.two_vi_config_frame.grid()
            if hasattr(self, 'fixed_vi_combo'): self.fixed_vi_combo['values'] = self.all_vi_names
            if hasattr(self, 'fixed_descriptor_combo'): self.fixed_descriptor_combo['values'] = [] 
            if hasattr(self, 'one_vi_button'): self.one_vi_button.state(['!pressed', '!disabled'])
            if hasattr(self, 'two_vi_button'): self.two_vi_button.state(['pressed', 'disabled'])
        else: 
             if hasattr(self, 'one_vi_button'): self.one_vi_button.state(['!pressed', '!disabled'])
             if hasattr(self, 'two_vi_button'): self.two_vi_button.state(['!pressed', '!disabled'])
        
        self._resize_to_content()


    def _update_fixed_descriptor_options(self, event=None):
        """Actualiza el combobox de sub-valores fijos basado en la VI fija seleccionada."""
        fixed_vi_name = self.fixed_vi_var.get()
        self.fixed_descriptor_var.set("") # Limpiar selección anterior
        self.fixed_descriptor_combo['values'] = []
        self.available_groups_filtered = {} # Limpiar grupos disponibles
        self._clear_group_selectors(update_columns=False) # No actualizar columnas aún

        if fixed_vi_name:
            descriptors = self.all_descriptors_by_vi.get(fixed_vi_name, [])
            # Mostrar alias si existen
            display_descriptors = [f"{d} ({self.study_aliases.get(d)})" if self.study_aliases.get(d) else d for d in descriptors]
            self.fixed_descriptor_combo['values'] = sorted(display_descriptors)
            self.fixed_descriptor_label.config(text=f"Valor Fijo para '{fixed_vi_name}':") # Actualizar label
        else:
             self.fixed_descriptor_label.config(text="Valor Fijo:")

        # Ocultar/mostrar pasos siguientes
        self.group_selection_outer_frame.grid_remove()
        self.column_frame.grid_remove()
        self.assumptions_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)
        self._resize_to_content()


    def load_initial_data(self):
        """Carga datos iniciales: VIs, alias, frecuencias."""
        try:
            # Cargar detalles del estudio (VIs y Alias)
            details = self.analysis_service.study_service.get_study_details(self.study_id)
            self.all_vi_names = [vi['name'] for vi in details.get('independent_variables', [])]
            self.all_descriptors_by_vi = {vi['name']: vi['descriptors'] for vi in details.get('independent_variables', [])}
            self.study_aliases = details.get('aliases', {})
            logger.debug(f"Datos iniciales cargados: VIs={self.all_vi_names}, Sub-valores={self.all_descriptors_by_vi}, Alias={self.study_aliases}")

            # Cargar frecuencias (sin cambios)
            # Cargar y fijar frecuencia a "Cinematica"
            if not self._load_and_fix_frequency(): # Modify to return bool
                self.destroy() # Ensure dialog is closed if frequency setup fails critically
                return False # Indicate __init__ should not proceed

        except Exception as e:
            logger.error(f"Error cargando datos iniciales para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los datos iniciales del estudio: {e}", parent=self)
            self.destroy()
            return False # Indicate __init__ should not proceed
        return True # Indicate __init__ can proceed


    def update_available_groups(self, event=None):
        """Actualiza la lista de grupos FILTRADOS basados en las selecciones previas."""
        frequency = self.frequency_var.get()
        mode = self.vi_grouping_mode.get()
        primary_vi = self.primary_vi_var.get() if mode == '1VI' else None
        fixed_vi = self.fixed_vi_var.get() if mode == '2VIs' else None
        fixed_descriptor_display = self.fixed_descriptor_var.get() if mode == '2VIs' else None

        # Limpiar si falta información clave
        if not frequency or not mode or (mode == '1VI' and not primary_vi) or \
           (mode == '2VIs' and (not fixed_vi or not fixed_descriptor_display)):
            self.available_groups_filtered = {}
            self._clear_group_selectors(update_columns=False) # No actualizar columnas aún
            self.group_selection_outer_frame.grid_remove() # Ocultar frame de grupos
            logger.debug("Limpiando grupos: falta información previa.")
            self._resize_to_content()
            return

        # Obtener el descriptor original si hay alias
        fixed_descriptor = None
        if fixed_descriptor_display:
             # Buscar descriptor original que coincide con el display name (con o sin alias)
             for desc_orig, alias in self.study_aliases.items():
                 if f"{desc_orig} ({alias})" == fixed_descriptor_display:
                     fixed_descriptor = desc_orig
                     break
             if not fixed_descriptor: # Si no tenía alias o no se encontró
                 # Asumir que es el original si no tiene formato de alias
                 fixed_descriptor = fixed_descriptor_display.split(" (")[0]


        try:
            logger.debug(f"Actualizando grupos filtrados: mode={mode}, freq={frequency}, primary={primary_vi}, fixed_vi={fixed_vi}, fixed_desc={fixed_descriptor}")

            # LLAMAR A NUEVO MÉTODO DEL SERVICIO
            filtered_groups = self.analysis_service.get_filtered_discrete_analysis_groups(
                study_id=self.study_id,
                frequency=frequency,
                mode=mode,
                primary_vi_name=primary_vi,
                fixed_vi_name=fixed_vi,
                fixed_descriptor_value=fixed_descriptor
            ) # For 1VI, this now returns {partial_key: display_name}
              # For 2VIs, this returns {original_full_key: display_name_of_variable_part}

            # Mapear display_name -> key (partial_key for 1VI, original_full_key for 2VIs)
            self.available_groups_filtered = {display_name: key for key, display_name in filtered_groups.items()}
            logger.debug(f"Grupos filtrados disponibles para UI (display_name -> key): {self.available_groups_filtered}")

            # Mostrar el frame de selección de grupos y actualizar combos
            self.group_selection_outer_frame.grid()
            self._update_group_combobox_values()

            # Añadir selectores iniciales si no existen
            if not self.group_selector_vars:
                 self.add_group_selector()
                 self.add_group_selector()

            # Ocultar/mostrar pasos siguientes
            self.column_frame.grid_remove()
            self.assumptions_frame.grid_remove()
            self.analysis_name_frame.grid_remove()
            self.button_frame.grid_remove()
            self.save_button.config(state=tk.DISABLED)


        except Exception as e:
            logger.error(f"Error actualizando grupos filtrados: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los grupos filtrados:\n{e}", parent=self)
            self.available_groups_filtered = {}
            self._clear_group_selectors(update_columns=False) # No actualizar columnas
            self.group_selection_outer_frame.grid_remove()
        self._resize_to_content()

    def _load_and_fix_frequency(self) -> bool:
        """Verifica la disponibilidad de 'Cinematica' y la fija como Tipo de Dato. Retorna True si exitoso."""
        logger.debug(f"Verificando disponibilidad de 'Cinematica' para estudio {self.study_id}")
        self.frequency_var.set("")
        self.freq_combo['values'] = []
        # self.freq_combo.config(state="disabled") # Already set in create_widgets

        try:
            tables_path = self.analysis_service.get_discrete_analysis_tables_path(self.study_id)
            cinematica_path = tables_path / "Cinematica" if tables_path else None

            if cinematica_path and cinematica_path.exists() and cinematica_path.is_dir():
                self.available_frequencies = ["Cinematica"]
                self.frequency_var.set("Cinematica")
                self.freq_combo['values'] = ["Cinematica"]
                # El combobox ya está 'disabled' desde create_widgets
                logger.info("Tipo de Dato fijado a 'Cinematica' para análisis discreto.")
                # El flujo normal es: Freq (fijo) -> Calc -> Modo VI -> ...
                # El usuario seleccionará el cálculo y luego el modo VI.
            else:
                logger.warning(f"Directorio de tablas resumen para 'Cinematica' no encontrado en {tables_path}.")
                messagebox.showwarning("No Disponible",
                                       "El análisis discreto actualmente solo está disponible si existen datos procesados de 'Cinematica'.\n"
                                       "No se encontraron tablas resumen para 'Cinematica' en este estudio.",
                                       parent=self)
                # Si Cinemática no está disponible, es un error que impide continuar.
                self.one_vi_button.config(state=tk.DISABLED)
                self.two_vi_button.config(state=tk.DISABLED)
                self.calc_combo.config(state=tk.DISABLED)
                return False # Indicar fallo

        except Exception as e:
            logger.error(f"Error verificando frecuencia 'Cinematica' para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo verificar la disponibilidad de 'Cinematica':\n{e}", parent=self)
            self.freq_combo['values'] = []
            self.one_vi_button.config(state=tk.DISABLED)
            self.two_vi_button.config(state=tk.DISABLED)
            self.calc_combo.config(state=tk.DISABLED)
            return False # Indicar fallo
        return True # Indicar éxito

    def add_group_selector(self, initial_value=""):
        """Añade un nuevo selector de grupo (Combobox + botón eliminar)."""
        if not self.group_selectors_frame: return

        selector_frame = ttk.Frame(self.group_selectors_frame)
        selector_frame.pack(fill=tk.X, pady=2)

        group_var = tk.StringVar(value=initial_value)
        
        group_combo_frame = ttk.Frame(selector_frame) # Frame para combo y botón de ayuda
        group_combo_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale) # Define scaled_font here
        group_combo = ttk.Combobox(group_combo_frame, textvariable=group_var, state="readonly",
                                   values=sorted(list(self.available_groups_filtered.keys())), font=scaled_font)
        group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        group_combo.bind("<<ComboboxSelected>>", self.update_available_columns)
        
        group_select_help_long_text = ("Seleccione un grupo (sub-valor o combinación de sub-valores con alias) para incluir en la comparación.\n"
                                       "Debe seleccionar al menos dos grupos distintos.")
        group_select_help_short_text = "Seleccionar grupo para comparar."
        group_select_help_button = ttk.Button(group_combo_frame, text="?", width=3, style="Help.TButton",
                                              command=lambda: self._show_input_help("Ayuda: Selección de Grupo", group_select_help_long_text))
        group_select_help_button.pack(side=tk.LEFT)
        help_tooltip = Tooltip(group_select_help_button, text=group_select_help_long_text, short_text=group_select_help_short_text, enabled=self.settings.enable_hover_tooltips)
        

        # Botón para eliminar este selector (icono basura)
        remove_button = ttk.Button(selector_frame, text="🗑️", width=3, # Usar icono
                                   command=lambda f=selector_frame, v=group_var: self.remove_group_selector(f, v))
        remove_button.pack(side=tk.LEFT)
        Tooltip(remove_button, text="Quitar este grupo de la comparación.", short_text="Quitar grupo.", enabled=self.settings.enable_hover_tooltips)

        # Deshabilitar botón si solo quedan 2 selectores
        # Note: This logic for remove_button state is complex and might be better handled by a dedicated _update_remove_button_states method
        if len(self.group_selector_vars) < 2:
             remove_button.config(state=tk.DISABLED)
        # Habilitar botones de los anteriores si ahora hay más de 2
        elif len(self.group_selector_vars) == 2:
             # Habilitar botón del segundo selector (índice 1)
             if len(self.group_selector_frames) > 1 and self.group_selector_frames[1].winfo_exists(): # Check frame exists
                 second_frame = self.group_selector_frames[1]
                 if len(second_frame.winfo_children()) > 1: # Check button exists
                     # Assuming the second child is the remove button
                     btn_widget = second_frame.winfo_children()[1]
                     if isinstance(btn_widget, ttk.Button):
                        btn_widget.config(state=tk.NORMAL)


        self.group_selector_vars.append(group_var)
        self.group_selector_frames.append(selector_frame) # Guardar frame
        self.group_selector_tooltips.append(help_tooltip) # Store the help button's tooltip
        self._refresh_group_combobox_options() # Actualizar opciones de todos los combos

    def remove_group_selector(self, frame_to_remove, var_to_remove):
        """Elimina un selector de grupo."""
        if len(self.group_selector_vars) <= 2:
            messagebox.showwarning("Acción no permitida", "Debe seleccionar al menos dos grupos para comparar.", parent=self)
            return

        try:
            index = self.group_selector_frames.index(frame_to_remove)
            self.group_selector_vars.pop(index)
            self.group_selector_frames.pop(index)
            if index < len(self.group_selector_tooltips): # Ensure index is valid before popping
                self.group_selector_tooltips.pop(index)
            frame_to_remove.destroy()

            # Deshabilitar botón de eliminar si solo quedan 2
            # Note: This logic for remove_button state is complex and might be better handled by a dedicated _update_remove_button_states method
            if len(self.group_selector_vars) == 2:
                 for i in range(min(2, len(self.group_selector_frames))): # Iterate safely
                     if self.group_selector_frames[i].winfo_exists() and \
                        len(self.group_selector_frames[i].winfo_children()) > 1:
                         # Assuming the second child is the remove button
                         button_widget = self.group_selector_frames[i].winfo_children()[1]
                         if isinstance(button_widget, ttk.Button):
                            button_widget.config(state=tk.DISABLED)


            self.update_available_columns()
            self._refresh_group_combobox_options() # Actualizar opciones de todos los combos
        except (ValueError, IndexError):
            logger.warning("Intento de eliminar un selector de grupo que ya no existe o índice inválido.")

    def _refresh_group_combobox_options(self):
        """Actualiza las opciones de todos los combobox de grupo para evitar duplicados."""
        all_possible_options = sorted(list(self.available_groups_filtered.keys()))
        
        # Obtener todas las selecciones actuales de todos los combos
        current_selections_in_all_combos = set()
        for sv in self.group_selector_vars:
            val = sv.get()
            if val:
                current_selections_in_all_combos.add(val)

        for i, combo_var in enumerate(self.group_selector_vars):
            if i >= len(self.group_selector_frames): continue # Safety check

            combo_frame_container = self.group_selector_frames[i].winfo_children()[0] # This is group_combo_frame
            combo_widget = combo_frame_container.winfo_children()[0] # This is the actual Combobox
            
            if not isinstance(combo_widget, ttk.Combobox): continue

            current_selection_this_combo = combo_var.get()
            
            options_for_this_combo = []
            for option in all_possible_options:
                # Una opción está disponible si:
                # 1. Es la selección actual de ESTE combobox.
                # 2. O NO está seleccionada en NINGÚN OTRO combobox.
                is_selected_in_another_combo = False
                for other_idx, other_var in enumerate(self.group_selector_vars):
                    if i == other_idx: continue # No comparar consigo mismo
                    if other_var.get() == option:
                        is_selected_in_another_combo = True
                        break
                
                if option == current_selection_this_combo or not is_selected_in_another_combo:
                    options_for_this_combo.append(option)
            
            combo_widget['values'] = options_for_this_combo
            
            # Re-apply font to ensure it's not lost during value updates
            scaled_font_refresh = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
            combo_widget.configure(font=scaled_font_refresh)
            
            # Re-validar la selección actual del combo
            if current_selection_this_combo and current_selection_this_combo not in options_for_this_combo:
                combo_var.set("") # Limpiar si ya no es válida (debería ser raro con la lógica anterior)


    def _update_group_combobox_values(self):
        """Actualiza las opciones en todos los combobox de grupo existentes con los grupos FILTRADOS."""
        group_names = sorted(list(self.available_groups_filtered.keys()))
        # Limpiar combos existentes antes de actualizar
        self._clear_group_selectors(update_columns=False) # No actualizar columnas todavía

        # Re-añadir selectores si es necesario (mínimo 2)
        while len(self.group_selector_vars) < 2:
             self.add_group_selector()

        # Actualizar valores en los combos existentes
        for i, var in enumerate(self.group_selector_vars):
             # Encontrar el combo asociado a esta variable (asumiendo orden)
             # Necesitamos iterar sobre los frames guardados
             if i < len(self.group_selector_frames):
                 selector_frame = self.group_selector_frames[i]
                 combo = selector_frame.winfo_children()[0]
                 if isinstance(combo, ttk.Combobox):
                     combo['values'] = group_names
             else:
                 logger.warning(f"Índice {i} fuera de rango para group_selector_frames al actualizar valores.")


        # Disparar actualización de columnas ahora que los combos están listos
        self.update_available_columns()
        self._refresh_group_combobox_options() # Asegurar que las opciones de combo se actualicen


    def _clear_group_selectors(self, update_columns=True):
        """Limpia las opciones y valores de los selectores de grupo."""
        # Destruir frames existentes y limpiar variables
        for frame in self.group_selector_frames:
            frame.destroy()
        self.group_selector_frames.clear() # Use clear() for lists
        self.group_selector_vars.clear()
        self.group_selector_tooltips.clear() # Clear stored tooltips

        if update_columns:
            self.update_available_columns() # Columnas dependen de grupos


    def get_selected_group_keys(self) -> List[str]:
        """Obtiene las claves originales de los grupos seleccionados y válidos de los FILTRADOS."""
        selected_keys = []
        selected_display_names = set()
        
        for group_var in self.group_selector_vars:
            display_name = group_var.get()
            if not display_name: # Si un campo está vacío, la selección general no es válida para proceder
                # messagebox.showwarning("Selección Incompleta", "Por favor, seleccione un grupo en todos los campos.", parent=self)
                return [] # Devolver lista vacía indica selección inválida/incompleta

            if display_name in selected_display_names:
                # Esta validación de duplicados se maneja ahora previniendo la selección.
                # Pero si aun así ocurre, es un error.
                logger.error(f"Error: Grupo duplicado '{display_name}' detectado a pesar de los filtros del combobox.")
                messagebox.showerror("Error de Selección", f"El grupo '{display_name}' está seleccionado más de una vez. Corrija la selección.", parent=self)
                return [] 
            
            selected_display_names.add(display_name)
            original_key = self.available_groups_filtered.get(display_name)
            if original_key:
                selected_keys.append(original_key)
            else:
                logger.error(f"Clave original no encontrada para el grupo filtrado seleccionado: '{display_name}'")
                # Si una clave no se encuentra, la selección es inválida
                messagebox.showerror("Error Interno", f"No se pudo encontrar la clave para el grupo '{display_name}'.", parent=self)
                return []

        return selected_keys


    def update_available_columns(self, event=None):
        """Actualiza la lista de columnas comunes y muestra los siguientes pasos."""
        # Primero, refrescar las opciones de los combobox de grupo
        self._refresh_group_combobox_options()

        frequency = self.frequency_var.get()
        calculation = self.calculation_var.get()
        selected_group_keys = self.get_selected_group_keys()

        # Limpiar columnas y ocultar pasos siguientes si falta info o grupos
        if not frequency or not calculation or len(selected_group_keys) < 2:
            self.available_columns = []
            self.column_combo['values'] = []
            self.column_var.set("")
            self.column_frame.grid_remove()
            self.assumptions_frame.grid_remove()
            self.analysis_name_frame.grid_remove()
            self.button_frame.grid_remove()
            if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)
            logger.debug("Limpiando columnas y ocultando pasos: falta info o grupos.")
            self._resize_to_content()
            return

        try:
            logger.debug(f"Actualizando columnas para freq={frequency}, calc={calculation}, grupos={selected_group_keys}")
            common_columns = self.analysis_service.get_common_columns_for_groups(
                self.study_id, frequency, calculation, selected_group_keys
            )
            self.available_columns = sorted(common_columns)
            self.column_combo['values'] = self.available_columns
            logger.debug(f"Columnas comunes encontradas: {self.available_columns}")

            # Mostrar frame de columna
            self.column_frame.grid()

            # Mantener selección si aún es válida, sino limpiar y ocultar resto
            current_column = self.column_var.get()
            if current_column not in self.available_columns:
                self.column_var.set("")
                self._hide_final_steps() # Ocultar pasos finales
            elif self.available_columns: # Si hay columnas y la selección es válida (o se acaba de seleccionar)
                self._show_final_steps() # Mostrar pasos finales
            else: # Si no hay columnas comunes
                 self._hide_final_steps()
                 messagebox.showwarning( # Changed to showwarning
                     "Sin Columnas Comunes",
                     "No se encontraron columnas de datos comunes para la combinación de cálculo y grupos seleccionada.\n\n"
                     "Posibles razones:\n"
                     "- Los grupos seleccionados no comparten ninguna variable numérica en sus tablas de resumen.\n"
                     "- Las tablas de resumen para los grupos seleccionados podrían estar vacías o corruptas.\n"
                     "- Algún archivo de tabla de resumen (.xlsx o .csv interno) podría haber sido eliminado o modificado manualmente.",
                     parent=self)


        except Exception as e:
            logger.error(f"Error actualizando columnas comunes: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar las columnas comunes:\n{e}", parent=self)
            self.available_columns = []
            self.column_combo['values'] = []
            self.column_var.set("")
            self._hide_final_steps() # Ocultar pasos finales en caso de error
        self._resize_to_content()


    def _on_column_selected(self, event=None):
        """Se llama cuando se selecciona una columna, muestra los pasos finales."""
        if self.column_var.get():
            self._show_final_steps()
        else:
            self._hide_final_steps()

    def _show_final_steps(self):
        """Muestra los frames de supuestos, nombre y botones."""
        self.assumptions_frame.grid()
        self.analysis_name_frame.grid()
        self.button_frame.grid()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.NORMAL) 
        self._resize_to_content()

    def _hide_final_steps(self):
        """Oculta los frames de supuestos, nombre y botones."""
        self.assumptions_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED) 
        self._resize_to_content()


    def _save_configuration_and_close(self):
        """Valida la configuración, la establece en self.result y cierra el diálogo."""
        analysis_name = self.analysis_name_var.get().strip()
        selected_freq = self.frequency_var.get()
        selected_calc = self.calculation_var.get()
        selected_col = self.column_var.get()
        selected_group_keys = self.get_selected_group_keys()
        is_parametric = self.parametric_var.get()
        is_paired = self.paired_var.get()

        # --- Validaciones ---
        if not analysis_name:
            messagebox.showerror("Error de Validación",
                                   "Ingrese un nombre para el análisis.",
                                   parent=self)
            return
        # Validar caracteres inválidos en nombre (repetido de AnalysisService)
        invalid_chars = r'<>:"/\|?*'
        if any(char in analysis_name for char in invalid_chars):
            messagebox.showerror(
                "Error de Validación",
                f"El nombre del análisis contiene caracteres inválidos: "
                f"{invalid_chars}",
                parent=self)
            return

        if not selected_freq or not selected_calc:
            messagebox.showerror("Error de Validación",
                                   "Seleccione Tipo de Dato y Cálculo.",
                                   parent=self)
            return
        if len(selected_group_keys) < 2:
            messagebox.showerror(
                "Error de Validación",
                "Seleccione al menos dos grupos válidos y distintos.",
                parent=self)
            return
        if not selected_col:
            messagebox.showerror("Error de Validación",
                                   "Seleccione la columna a analizar.",
                                   parent=self)
            return

        # --- Crear Configuración ---
        config = {
            "name": analysis_name,
            "frequency": selected_freq,
            "calculation": selected_calc,
            "column": selected_col,
            "groups": selected_group_keys,  # Guardar las claves originales
            "parametric": is_parametric,}
        is_parametric = self.parametric_var.get()
        is_paired = self.paired_var.get()
        mode = self.vi_grouping_mode.get() # Obtener modo
        primary_vi = self.primary_vi_var.get() if mode == '1VI' else None
        fixed_vi = self.fixed_vi_var.get() if mode == '2VIs' else None
        fixed_descriptor_display = self.fixed_descriptor_var.get() if mode == '2VIs' else None

        # --- Validaciones (igual que antes) ---
        if not analysis_name:
            messagebox.showerror("Error de Validación",
                                   "Ingrese un nombre para el análisis.",
                                   parent=self)
            return
        # Validar caracteres inválidos en nombre (repetido de AnalysisService)
        invalid_chars = r'<>:"/\|?*'
        if any(char in analysis_name for char in invalid_chars):
            messagebox.showerror(
                "Error de Validación",
                f"El nombre del análisis contiene caracteres inválidos: "
                f"{invalid_chars}",
                parent=self)
            return

        if not selected_freq or not selected_calc:
            messagebox.showerror("Error de Validación",
                                   "Seleccione Tipo de Dato y Cálculo.",
                                   parent=self)
            return
        if len(selected_group_keys) < 2:
            messagebox.showerror(
                "Error de Validación",
                "Seleccione al menos dos grupos válidos y distintos.",
                parent=self)
            return
        if not selected_col:
            messagebox.showerror("Error de Validación",
                                   "Seleccione la columna a analizar.",
                                   parent=self)
            return

        # --- Crear Configuración (añadir modo y VIs seleccionadas) ---
        config = {
            "name": analysis_name, # Cambiado de analysis_name a name
            "frequency": selected_freq,
            "calculation": selected_calc,
            "groups": selected_group_keys,  # Guardar las claves originales
            "column": selected_col,
            "parametric": is_parametric,
            "paired": is_paired,
            # Nuevos campos para reconstruir título/leyenda y para lógica interna
            "grouping_mode": mode,
            "primary_vi_name": primary_vi,
            "fixed_vi_name": fixed_vi,
            "fixed_descriptor_display": fixed_descriptor_display, # Guardar display name con alias
        }


        # --- Validar mínimo de participantes y diversidad de VIs ---
        # This validation should ideally be done by AnalysisService before attempting analysis,
        # or here if we have enough info. For now, let's add a basic check.
        # This requires knowing how many unique participants contribute to the selected groups
        # and if they represent at least two different effective VI combinations.
        # This is complex to check accurately at this stage without querying data.
        # A simpler check: ensure at least two groups are selected. This is already done.
        # A more advanced check would involve AnalysisService.
        # For now, we rely on AnalysisService to handle data sufficiency errors.

        # --- Establecer Resultado y Cerrar ---
        # No se llama al servicio aquí. Solo se guarda la configuración.
        self.result = config
        logger.info(f"Configuración de análisis individual lista para ser devuelta: {self.result}")
        self.destroy() # Cerrar el diálogo de configuración

    # Removed _update_dialog_size_and_scrollbar method (implicitly by new system)

    def _center_dialog(self):
        self.update_idletasks()
        ref_window = self.parent_window
        
        parent_x = ref_window.winfo_rootx()
        parent_y = ref_window.winfo_rooty()
        parent_width = ref_window.winfo_width()
        parent_height = ref_window.winfo_height()
        
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        position_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        position_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        position_x = max(0, min(position_x, screen_width - dialog_width))
        position_y = max(0, min(position_y, screen_height - dialog_height))

        self.geometry(f"+{int(position_x)}+{int(position_y)}")

    # --- Calls to _update_dialog_size_and_scrollbar ---
    def set_vi_grouping_mode(self, mode):
        """Configura la UI según se elija agrupar por 1 o 2 VIs."""
        # ... (existing code for set_vi_grouping_mode) ...
        # super_set_vi_grouping_mode_result = super().set_vi_grouping_mode(mode) if hasattr(super(), 'set_vi_grouping_mode') else None
        self.vi_grouping_mode.set(mode)
        logger.info(f"Modo de agrupación seleccionado: {mode}")

        self.primary_vi_var.set("")
        self.fixed_vi_var.set("")
        self.fixed_descriptor_var.set("")
        self.available_groups_filtered = {}
        self._clear_group_selectors(update_columns=False) 
        self.column_var.set("")
        if hasattr(self, 'column_combo'): self.column_combo['values'] = []
        # Save button state handled by _show_final_steps or _hide_final_steps

        self.one_vi_config_frame.grid_remove()
        self.two_vi_config_frame.grid_remove()
        self.group_selection_outer_frame.grid_remove()
        self.column_frame.grid_remove()
        self.assumptions_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()

        if mode == '1VI':
            self.one_vi_config_frame.grid()
            if hasattr(self, 'primary_vi_combo'): self.primary_vi_combo['values'] = self.all_vi_names
            if hasattr(self, 'one_vi_button'): self.one_vi_button.state(['pressed', 'disabled'])
            if hasattr(self, 'two_vi_button'): self.two_vi_button.state(['!pressed', '!disabled'])
        elif mode == '2VIs':
            if len(self.all_vi_names) < 2:
                 messagebox.showwarning("No disponible", "Se requieren al menos 2 Variables Independientes definidas en el estudio para agrupar por 2 VIs.", parent=self)
                 self.vi_grouping_mode.set("") 
                 if hasattr(self, 'one_vi_button'): self.one_vi_button.state(['!pressed', '!disabled']) 
                 if hasattr(self, 'two_vi_button'): self.two_vi_button.state(['!pressed', '!disabled'])
                 self._adjust_dialog_layout()
                 return
            self.two_vi_config_frame.grid()
            if hasattr(self, 'fixed_vi_combo'): self.fixed_vi_combo['values'] = self.all_vi_names
            if hasattr(self, 'fixed_descriptor_combo'): self.fixed_descriptor_combo['values'] = []
            if hasattr(self, 'one_vi_button'): self.one_vi_button.state(['!pressed', '!disabled'])
            if hasattr(self, 'two_vi_button'): self.two_vi_button.state(['pressed', 'disabled'])
        else: 
             if hasattr(self, 'one_vi_button'): self.one_vi_button.state(['!pressed', '!disabled'])
             if hasattr(self, 'two_vi_button'): self.two_vi_button.state(['!pressed', '!disabled'])
        
        self._resize_to_content()

    def _update_fixed_descriptor_options(self, event=None):
        """Actualiza el combobox de sub-valores fijos basado en la VI fija seleccionada."""
        fixed_vi_name = self.fixed_vi_var.get()
        self.fixed_descriptor_var.set("") 
        if hasattr(self, 'fixed_descriptor_combo'): self.fixed_descriptor_combo['values'] = []
        self.available_groups_filtered = {} 
        self._clear_group_selectors(update_columns=False) 

        if fixed_vi_name:
            descriptors = self.all_descriptors_by_vi.get(fixed_vi_name, [])
            display_descriptors = [f"{d} ({self.study_aliases.get(d)})" if self.study_aliases.get(d) else d for d in descriptors]
            if hasattr(self, 'fixed_descriptor_combo'): self.fixed_descriptor_combo['values'] = sorted(display_descriptors)
            if hasattr(self, 'fixed_descriptor_label'): self.fixed_descriptor_label.config(text=f"Valor Fijo para '{fixed_vi_name}':")
        else:
             if hasattr(self, 'fixed_descriptor_label'): self.fixed_descriptor_label.config(text="Valor Fijo:")

        self.group_selection_outer_frame.grid_remove()
        self.column_frame.grid_remove()
        self.assumptions_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)
        
        self._resize_to_content()

    def update_available_groups(self, event=None):
        """Actualiza la lista de grupos FILTRADOS basados en las selecciones previas."""
        frequency = self.frequency_var.get()
        mode = self.vi_grouping_mode.get()
        primary_vi = self.primary_vi_var.get() if mode == '1VI' else None
        fixed_vi = self.fixed_vi_var.get() if mode == '2VIs' else None
        fixed_descriptor_display = self.fixed_descriptor_var.get() if mode == '2VIs' else None

        if not frequency or not mode or (mode == '1VI' and not primary_vi) or \
           (mode == '2VIs' and (not fixed_vi or not fixed_descriptor_display)):
            self.available_groups_filtered = {}
            self._clear_group_selectors(update_columns=False) 
            self.group_selection_outer_frame.grid_remove() 
            # Ensure other dependent frames are also hidden
            self.column_frame.grid_remove()
            self.assumptions_frame.grid_remove()
            self.analysis_name_frame.grid_remove()
            self.button_frame.grid_remove()
            logger.debug("Limpiando grupos: falta información previa.")
            self._resize_to_content()
            return

        fixed_descriptor = None
        if fixed_descriptor_display:
             for desc_orig, alias in self.study_aliases.items():
                 if f"{desc_orig} ({alias})" == fixed_descriptor_display:
                     fixed_descriptor = desc_orig
                     break
             if not fixed_descriptor: 
                 fixed_descriptor = fixed_descriptor_display.split(" (")[0]

        try:
            logger.debug(f"Actualizando grupos filtrados: mode={mode}, freq={frequency}, primary={primary_vi}, fixed_vi={fixed_vi}, fixed_desc={fixed_descriptor}")
            filtered_groups = self.analysis_service.get_filtered_discrete_analysis_groups(
                study_id=self.study_id,
                frequency=frequency,
                mode=mode,
                primary_vi_name=primary_vi,
                fixed_vi_name=fixed_vi,
                fixed_descriptor_value=fixed_descriptor
            ) 
            self.available_groups_filtered = {display_name: key for key, display_name in filtered_groups.items()}
            logger.debug(f"Grupos filtrados disponibles para UI (display_name -> key): {self.available_groups_filtered}")

            self.group_selection_outer_frame.grid()
            self._update_group_combobox_values()

            if not self.group_selector_vars:
                 self.add_group_selector()
                 self.add_group_selector()
            
            self.column_frame.grid_remove()
            self.assumptions_frame.grid_remove()
            self.analysis_name_frame.grid_remove()
            self.button_frame.grid_remove()
            if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error actualizando grupos filtrados: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los grupos filtrados:\n{e}", parent=self)
            self.available_groups_filtered = {}
            self._clear_group_selectors(update_columns=False) 
            self.group_selection_outer_frame.grid_remove()
        
        self._resize_to_content()

    def _show_final_steps(self):
        """Muestra los frames de supuestos, nombre y botones."""
        self.assumptions_frame.grid()
        self.analysis_name_frame.grid()
        self.button_frame.grid()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.NORMAL) 
        self._resize_to_content()

    def _hide_final_steps(self):
        """Oculta los frames de supuestos, nombre y botones."""
        self.assumptions_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED) 
        self._resize_to_content()

    def add_group_selector(self, initial_value=""):
        """Añade una nueva fila para seleccionar un grupo."""
        if not self.group_selectors_frame: 
            return

        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
        selector_frame = ttk.Frame(self.group_selectors_frame)
        selector_frame.pack(fill=tk.X, pady=2)

        group_var = tk.StringVar(value=initial_value)
        
        group_combo_frame = ttk.Frame(selector_frame) 
        group_combo_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        group_combo = ttk.Combobox(group_combo_frame, textvariable=group_var, state="readonly",
                                   values=sorted(list(self.available_groups_filtered.keys())), font=scaled_font)
        group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        group_combo.bind("<<ComboboxSelected>>", self.update_available_columns)
        
        group_select_help_long_text = ("Seleccione un grupo (sub-valor o combinación de sub-valores con alias) para incluir en la comparación.\n"
                                       "Debe seleccionar al menos dos grupos distintos.")
        group_select_help_short_text = "Seleccionar grupo para comparar."
        group_select_help_button = ttk.Button(group_combo_frame, text="?", width=3, style="Help.TButton",
                                              command=lambda: self._show_input_help("Ayuda: Selección de Grupo", group_select_help_long_text))
        group_select_help_button.pack(side=tk.LEFT)
        help_tooltip = Tooltip(group_select_help_button, text=group_select_help_long_text, short_text=group_select_help_short_text, enabled=self.settings.enable_hover_tooltips)
        

        remove_button = ttk.Button(selector_frame, text="🗑️", width=3, 
                                   command=lambda f=selector_frame, v=group_var: self.remove_group_selector(f, v))
        remove_button.pack(side=tk.LEFT)
        Tooltip(remove_button, text="Quitar este grupo de la comparación.", short_text="Quitar grupo.", enabled=self.settings.enable_hover_tooltips)
        
        self.group_selector_vars.append(group_var)
        self.group_selector_frames.append(selector_frame) 
        self.group_selector_tooltips.append(help_tooltip)

        # Update all remove buttons
        for idx, frame_item in enumerate(self.group_selector_frames):
            if frame_item.winfo_exists() and len(frame_item.winfo_children()) > 1:
                btn = frame_item.winfo_children()[1] # Assuming remove button is the second child
                if isinstance(btn, ttk.Button): 
                    btn.config(state=tk.NORMAL if len(self.group_selector_vars) > 2 else tk.DISABLED)
        
        self._refresh_group_combobox_options() 
        self.update_available_columns() 
        self._resize_to_content()


    def remove_group_selector(self, frame_to_remove, var_to_remove):
        """Elimina una fila de selector de grupo."""
        if len(self.group_selector_vars) <= 2:
            messagebox.showwarning("Acción no permitida", "Debe seleccionar al menos dos grupos para comparar.", parent=self)
            return

        try:
            index = self.group_selector_frames.index(frame_to_remove)
            self.group_selector_vars.pop(index)
            self.group_selector_frames.pop(index)
            if index < len(self.group_selector_tooltips):
                self.group_selector_tooltips.pop(index)
            frame_to_remove.destroy()

            # Update all remove buttons
            for idx, frame_item in enumerate(self.group_selector_frames):
                 if frame_item.winfo_exists() and len(frame_item.winfo_children()) > 1:
                    btn = frame_item.winfo_children()[1] # Assuming remove button is the second child
                    if isinstance(btn, ttk.Button):
                        btn.config(state=tk.NORMAL if len(self.group_selector_vars) > 2 else tk.DISABLED)

            self.update_available_columns()
            self._refresh_group_combobox_options() 
            self._resize_to_content()
        except (ValueError, IndexError):
            logger.warning("Intento de eliminar un selector de grupo que ya no existe o índice inválido.")


# Para pruebas rápidas
if __name__ == '__main__':
    from pathlib import Path  # Importar Path para el dummy
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal

    # --- Dummies (igual que en el manager) ---
    class DummyAnalysisService:
        def __init__(self):
            # Simular StudyService anidado para alias y VIs
            class DummyStudyService:
                 def get_study_details(self, study_id):
                     print(f"DummyStudyService: get_study_details({study_id})")
                     # Simular VIs para _identify_study_groups
                     return {'independent_variables': [
                                 {'name': 'Tipo', 'descriptors': ['CMJ', 'SJ']},
                                 {'name': 'Cond', 'descriptors': ['PRE', 'POST', 'TipoA', 'TipoB', 'TipoC']}
                             ]}
                 def get_study_aliases(self, study_id):
                     print(f"DummyStudyService: get_study_aliases({study_id})")
                     return {'CMJ': 'Salto CM', 'PRE': 'Antes', 'POST': 'Despues'}
            self.study_service = DummyStudyService()
            # Simular FileService mínimo
            class DummyFileService:
                def _get_study_path(self, study_id): return Path(f'/fake/study_{study_id}')
                def get_study_files(self, study_id, page, per_page, file_type, frequency):
                    # Simular algunos archivos válidos
                    return ([
                        {'path': Path('/fake/study_1/Pte01/Cinematica/Pte01_CMJ_PRE_01_Cinematica.txt')},
                        {'path': Path('/fake/study_1/Pte01/Cinematica/Pte01_CMJ_POST_01_Cinematica.txt')},
                        {'path': Path('/fake/study_1/Pte02/Cinematica/Pte02_SJ_TipoA_01_Cinematica.txt')},
                        {'path': Path('/fake/study_1/Pte02/Cinematica/Pte02_SJ_TipoB_01_Cinematica.txt')},
                    ], 4)
            self.file_service = DummyFileService()

        # Reimplementar _identify_study_groups aquí para el dummy
        def _identify_study_groups(self, study_id: int, frequency: str = "Cinematica") -> tuple[dict[str, str], set[str]]:
            groups_by_file_base = {}
            unique_group_keys = set()
            study_details = self.study_service.get_study_details(study_id)
            independent_variables = study_details.get('independent_variables', [])
            processed_files, _ = self.file_service.get_study_files(study_id, 1, 1000, 'Processed', frequency)
            for file_info in processed_files:
                filename = file_info['path'].name
                is_valid, extracted = validate_filename_for_study_criteria(filename, independent_variables)
                if is_valid:
                    group_parts = []
                    for i, desc in enumerate(extracted):
                        vi_name = independent_variables[i].get('name', f'VI{i+1}')
                        value = desc if desc is not None else "Nulo"
                        group_parts.append(f"{vi_name}={value}")
                    group_key = ";".join(group_parts) if group_parts else "SinGrupo"
                    file_base_key = file_info['path'].stem.split(f'_{frequency}')[0]
                    groups_by_file_base[file_base_key] = group_key
                    unique_group_keys.add(group_key)
            return groups_by_file_base, unique_group_keys

        def get_discrete_analysis_groups(self, study_id, frequency):
            print(f"Dummy: get_discrete_analysis_groups({study_id}, {frequency})")
            # Usar _identify_study_groups del dummy
            _, unique_group_keys = self._identify_study_groups(study_id, frequency)
            aliases = self.study_service.get_study_aliases(study_id)
            groups = []
            for group_key in unique_group_keys:
                display_parts = []
                if group_key != "SinGrupo":
                    for part in group_key.split(';'):
                        vi_name, desc_value = part.split('=', 1)
                        alias = aliases.get(desc_value, desc_value)
                        display_parts.append(f"{vi_name}: {alias}")
                display_name = ", ".join(display_parts) if display_parts else "Grupo General"
                groups.append((display_name, group_key))
            groups.sort()
            return groups

        def get_common_columns_for_groups(self, study_id, frequency,
                                          calculation, group_keys):
            print(f"Dummy: get_common_columns_for_groups({study_id}, "
                  f"{frequency}, {calculation}, {group_keys})")
            # Simular que solo hay columnas si se eligen 2 grupos
            if len(group_keys) == 2:
                return ['Art1/PosX/mm', 'Art1/PosY/mm', 'Art2/VelX/m/s',
                        'H Salto/Alt/cm']
            else:
                return []

        def perform_individual_analysis(self, study_id, config):
            print(f"Dummy: perform_individual_analysis({study_id}, {config})")
            # Simular éxito
            fake_path = Path(f'/fake/study_{study_id}/Analisis Discreto/'
                             f'Individual/{config["name"]}')
            # Crear directorios dummy para que no falle el messagebox
            # fake_path.mkdir(parents=True, exist_ok=True)
            return {'plot_path': str(fake_path / 'boxplot.png'),
                    'config_path': str(fake_path / 'config.json')}

    # --- Ejecutar Diálogo ---
    dummy_service = DummyAnalysisService()
    dialog = ConfigureIndividualAnalysisDialog(root, dummy_service, 1)
    root.mainloop()
