import tkinter as tk
from tkinter import ttk, messagebox # Añadir messagebox
import logging
from typing import List, Tuple # Añadir Tuple y List

# Asegúrate de que AnalysisService esté disponible para type hinting si es necesario en el futuro
from kineviz.core.services.analysis_service import AnalysisService # Descomentar para type hint
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip
from kineviz.config.settings import AppSettings # Import AppSettings
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # Import font utilities

logger = logging.getLogger(__name__)

class ContinuousAnalysisConfigDialog(tk.Toplevel):
    """
    Diálogo para configurar los parámetros de un análisis continuo (SPM).
    """
    def __init__(self, parent, analysis_service: AnalysisService, study_id: int, settings: AppSettings):
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
        self.settings = settings # Store AppSettings instance

        self.title("Configurar Análisis Continuo") # Título más genérico
        # Defer grab_set and transient until after initial sizing
        self.parent_window = parent # Store parent for transient and centering
        self._is_adjusting_size = False # Flag to prevent recursion in size adjustment

        self.result = None # Para almacenar la configuración si se guarda

        # --- Variables de estado para el flujo de VIs (similar a ConfigureIndividualAnalysisDialog) ---
        self.vi_grouping_mode = tk.StringVar(value="") # '1VI' o '2VIs'
        self.primary_vi_var = tk.StringVar()
        self.fixed_vi_var = tk.StringVar()
        self.fixed_descriptor_var = tk.StringVar()
        self.all_vi_names = []
        self.all_descriptors_by_vi = {}
        self.study_aliases = {}

        # --- Variables existentes (algunas se reutilizan o adaptan) ---
        self.frequency_var = tk.StringVar() # NUEVO: Para Tipo de Dato (Frecuencia)
        self.selected_variable = tk.StringVar() # Renombrada a column_var más adelante para consistencia
        self.column_var = self.selected_variable # Alias para consistencia con discrete
        
        self.group_selector_frames = []
        self.group_selector_vars = [] # Renombrar selected_groups_vars
        self.group_selector_tooltips = [] # NUEVO: Para almacenar instancias de Tooltip
        self.available_groups_filtered = {} # Para grupos filtrados por VI
        # self.group_display_to_key_map ya no se usa directamente, se usa available_groups_filtered

        # Variables para la columna (reutilizada)
        self.available_columns = []

        # Variables para opciones de visualización
        self.show_std_dev_var = tk.BooleanVar(value=False)
        self.show_conf_int_var = tk.BooleanVar(value=False)
        self.show_sem_var = tk.BooleanVar(value=False) # Nueva variable para EEM
        self.generate_interactive_plot_var = tk.BooleanVar(value=True) # Opción para gráfico interactivo

        # Variables para opciones de anotación del gráfico
        self.annotate_spm_clusters_bottom_var = tk.BooleanVar(value=True)
        self.annotate_spm_range_top_var = tk.BooleanVar(value=True)
        self.delimit_time_range_var = tk.BooleanVar(value=False)
        self.time_min_var = tk.StringVar(value="0")
        self.time_max_var = tk.StringVar(value="100")
        self.show_full_time_with_delimiters_var = tk.BooleanVar(value=True)
        self.add_time_range_label_var = tk.BooleanVar(value=False)
        self.time_range_label_text_var = tk.StringVar()

        # Variable para el nombre del análisis
        self.analysis_name_var = tk.StringVar()

        # Definir estilo para el botón de ayuda
        style = ttk.Style()
        style.configure("Help.TButton", foreground="white", background="blue")

        # --- Setup for scrollable area ---
        self.container_frame = ttk.Frame(self)
        self.canvas = tk.Canvas(self.container_frame, highlightthickness=0) # Remove canvas border
        self.scrollbar = ttk.Scrollbar(self.container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, padding="15")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        # Removed problematic canvas.bind("<Configure>") that forced inner frame width
        # self.canvas.bind(
        #     "<Configure>",
        #     lambda e: self.canvas.itemconfig(self.canvas.nametowidget(e.widget).interior_id, width=e.width) if hasattr(self.canvas, 'interior_id') else None
        # )
        self.canvas.interior_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw") # Store interior_id if needed elsewhere, though not for width setting now
        self.canvas.configure(yscrollcommand=self.scrollbar.set) # Assuming self.scrollbar is for vertical

        # Add horizontal scrollbar
        self.h_scrollbar = ttk.Scrollbar(self.container_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)

        # Grid layout for canvas and scrollbars
        self.container_frame.grid_rowconfigure(0, weight=1)
        self.container_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        # Scrollbars are created but not gridded initially
        
        self.container_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_widgets(self.scrollable_frame) # Pass scrollable_frame as parent
        
        # Load initial data and check if successful
        if not self.load_initial_data():
            # If load_initial_data returned False, it means it likely called self.destroy()
            # or encountered a critical error. We should not proceed with further initialization.
            logger.warning("ContinuousAnalysisConfigDialog: load_initial_data failed. Aborting initialization.")
            # Ensure self.result is None if dialog is destroyed prematurely
            if not hasattr(self, 'result'): self.result = None
            # Do not call self.destroy() here again if load_initial_data already did.
            # If it didn't, then this return will prevent grab_set etc.
            return 

        self.update_idletasks()
        # Set a very small minsize initially to allow shrink-wrapping to content
        self.minsize(1, 1) 
        
        self._resize_to_content() # Set initial size based on content
        
        # Now set a practical minimum size for user manual resizing and future content changes
        # This prevents the dialog from becoming too small if content is very small or removed.
        self.minsize(200, 150) # Adjusted to a smaller practical minimum

        self._center_dialog() # Center after initial size is set

        self.grab_set()
        self.transient(self.parent_window)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)
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
        
        # scrollable_frame.winfo_reqwidth/height already includes its own padding
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
        
        # Determine canvas viewport size (dialog size minus scrollbar placeholders if they were gridded)
        # This is a bit of a simplification; actual canvas width might be slightly less if scrollbar is visible.
        canvas_viewport_width = current_dialog_width
        canvas_viewport_height = current_dialog_height

        v_scroll_needed = content_req_height > canvas_viewport_height
        h_scroll_needed = content_req_width > canvas_viewport_width
        
        if v_scroll_needed:
            if not self.scrollbar.winfo_ismapped(): self.scrollbar.grid(row=0, column=1, sticky="ns")
            canvas_viewport_width -= self.scrollbar.winfo_reqwidth() # Account for v_scroll taking space
        elif self.scrollbar.winfo_ismapped(): self.scrollbar.grid_remove()

        # Re-check h_scroll_needed if v_scroll is now visible and took space
        if not h_scroll_needed and v_scroll_needed: 
            h_scroll_needed = content_req_width > canvas_viewport_width

        if h_scroll_needed:
            if not self.h_scrollbar.winfo_ismapped(): self.h_scrollbar.grid(row=1, column=0, sticky="ew")
            canvas_viewport_height -= self.h_scrollbar.winfo_reqheight() # Account for h_scroll taking space
        elif self.h_scrollbar.winfo_ismapped(): self.h_scrollbar.grid_remove()

        # Re-check v_scroll_needed if h_scroll is now visible and took space
        if not v_scroll_needed and h_scroll_needed:
             v_scroll_needed = content_req_height > canvas_viewport_height
             if v_scroll_needed and not self.scrollbar.winfo_ismapped(): # Show v_scroll if needed now
                 self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _show_input_help(self, title: str, message: str):
        """Muestra un popup de ayuda simple."""
        messagebox.showinfo(title, message, parent=self)

    def create_widgets(self, parent_frame): # parent_frame is self.scrollable_frame
        """Crea los widgets del diálogo, similar a ConfigureIndividualAnalysisDialog."""
        main_frame = parent_frame # Use the passed scrollable_frame
        # main_frame.pack(fill=tk.BOTH, expand=True) # Not needed, canvas manages scrollable_frame
        main_frame.columnconfigure(1, weight=1)

        row_idx = 0
        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)

        # --- Tipo de Dato (Frecuencia) ---
        ttk.Label(main_frame, text="Tipo de Dato:").grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        freq_frame_cont = ttk.Frame(main_frame)
        freq_frame_cont.grid(row=row_idx, column=1, sticky="ew")
        self.freq_combo = ttk.Combobox(freq_frame_cont, textvariable=self.frequency_var, state="disabled", font=scaled_font)
        self.freq_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        freq_long_text = "Tipo de datos a analizar.\nPara análisis continuo (SPM), actualmente solo 'Cinematica' está soportado y se selecciona automáticamente."
        freq_short_text = "Tipo de datos (fijo a 'Cinematica' para SPM)."
        freq_help_btn = ttk.Button(freq_frame_cont, text="?", width=3, style="Help.TButton",
                                   command=lambda: self._show_input_help("Ayuda: Tipo de Dato", freq_long_text))
        freq_help_btn.pack(side=tk.LEFT)
        Tooltip(freq_help_btn, text=freq_long_text, short_text=freq_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- NUEVO: Selección de Modo de Agrupación (1 VI vs 2 VIs) ---
        vi_mode_frame = ttk.Frame(main_frame)
        vi_mode_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=10)

        label_agrupar_frame_cont = ttk.Frame(vi_mode_frame)
        label_agrupar_frame_cont.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(label_agrupar_frame_cont, text="Agrupar por:").pack(side=tk.LEFT)
        agrupar_long_text = ("Define cómo se formarán los grupos de series temporales para la comparación SPM:\n\n"
                             "1 Variable Independiente (1VI):\n"
                             "  Compara los diferentes sub-valores de UNA ÚNICA VI.\n"
                             "  Ej: Comparar 'PRE' vs 'POST' de la VI 'Condicion' para la variable 'LAnkleAngles/X/deg'.\n\n"
                             "2 Variables Independientes (2VIs):\n"
                             "  Compara los sub-valores de una VI, MANTENIENDO FIJO un sub-valor de OTRA VI.\n"
                             "  Ej: Comparar 'CMJ' vs 'SJ' (VI 'TipoSalto'), solo para 'PRE' (VI 'Condicion').")
        agrupar_short_text = "Modo de agrupar datos para SPM (1VI o 2VIs)."
        agrupar_help_btn = ttk.Button(label_agrupar_frame_cont, text="?", width=3, style="Help.TButton",
                                      command=lambda: self._show_input_help("Ayuda: Modo de Agrupación (Continuo)", agrupar_long_text))
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
        self.one_vi_config_frame.grid_remove() 
        self.one_vi_config_frame.columnconfigure(1, weight=1)
        ttk.Label(self.one_vi_config_frame, text="Agrupar por VI:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        primary_vi_frame_cont = ttk.Frame(self.one_vi_config_frame)
        primary_vi_frame_cont.grid(row=0, column=1, sticky="ew")
        self.primary_vi_combo = ttk.Combobox(primary_vi_frame_cont, textvariable=self.primary_vi_var, state="readonly", font=scaled_font)
        self.primary_vi_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.primary_vi_combo.bind("<<ComboboxSelected>>", self.update_available_groups)
        
        primary_vi_help_long_text = "Seleccione la Variable Independiente principal cuyos sub-valores (con alias) formarán los grupos de series temporales a comparar."
        primary_vi_help_short_text = "VI principal para agrupar series temporales."
        primary_vi_help_button = ttk.Button(primary_vi_frame_cont, text="?", width=3, style="Help.TButton",
                                            command=lambda: self._show_input_help("Ayuda: Agrupar por VI (Continuo)", primary_vi_help_long_text))
        primary_vi_help_button.pack(side=tk.LEFT)
        Tooltip(primary_vi_help_button, text=primary_vi_help_long_text, short_text=primary_vi_help_short_text, enabled=self.settings.enable_hover_tooltips)

        # Frame para selección de VI fija y sub-valor fijo (modo 2VIs)
        self.two_vi_config_frame = ttk.Frame(main_frame)
        self.two_vi_config_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=0)
        self.two_vi_config_frame.grid_remove()
        self.two_vi_config_frame.columnconfigure(1, weight=1)

        ttk.Label(self.two_vi_config_frame, text="VI a Fijar:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        fixed_vi_frame_cont = ttk.Frame(self.two_vi_config_frame)
        fixed_vi_frame_cont.grid(row=0, column=1, sticky="ew")
        self.fixed_vi_combo = ttk.Combobox(fixed_vi_frame_cont, textvariable=self.fixed_vi_var, state="readonly", font=scaled_font)
        self.fixed_vi_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.fixed_vi_combo.bind("<<ComboboxSelected>>", self._update_fixed_descriptor_options)
        fixed_vi_help_long_text = "Seleccione la Variable Independiente que permanecerá constante mientras se comparan los sub-valores de la otra VI."
        fixed_vi_help_short_text = "VI que se mantendrá constante."
        fixed_vi_help_btn = ttk.Button(fixed_vi_frame_cont, text="?", width=3, style="Help.TButton",
                                       command=lambda: self._show_input_help("Ayuda: VI a Fijar (Continuo)", fixed_vi_help_long_text))
        fixed_vi_help_btn.pack(side=tk.LEFT)
        Tooltip(fixed_vi_help_btn, text=fixed_vi_help_long_text, short_text=fixed_vi_help_short_text, enabled=self.settings.enable_hover_tooltips)


        self.fixed_descriptor_label = ttk.Label(self.two_vi_config_frame, text="Valor Fijo:")
        self.fixed_descriptor_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        fixed_desc_frame_cont = ttk.Frame(self.two_vi_config_frame)
        fixed_desc_frame_cont.grid(row=1, column=1, sticky="ew")
        self.fixed_descriptor_combo = ttk.Combobox(fixed_desc_frame_cont, textvariable=self.fixed_descriptor_var, state="readonly", font=scaled_font)
        self.fixed_descriptor_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.fixed_descriptor_combo.bind("<<ComboboxSelected>>", self.update_available_groups)
        fixed_desc_help_long_text = ("Seleccione el sub-valor (con alias) de la 'VI a Fijar' que se mantendrá constante.\n"
                                     "Los grupos a comparar se formarán con los sub-valores de la otra VI, dentro de este contexto.")
        fixed_desc_help_short_text = "Sub-valor constante de la VI a fijar."
        fixed_desc_help_btn = ttk.Button(fixed_desc_frame_cont, text="?", width=3, style="Help.TButton",
                                         command=lambda: self._show_input_help("Ayuda: Valor Fijo (Continuo)", fixed_desc_help_long_text))
        fixed_desc_help_btn.pack(side=tk.LEFT)
        Tooltip(fixed_desc_help_btn, text=fixed_desc_help_long_text, short_text=fixed_desc_help_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Selección Dinámica de Grupos ---
        self.group_selection_outer_frame = ttk.LabelFrame(main_frame, text="Selección de Grupos a Comparar")
        self.group_selection_outer_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=10)
        self.group_selection_outer_frame.columnconfigure(0, weight=1)
        self.group_selection_outer_frame.grid_remove()
        
        # Canvas y Scrollbar para la sección de grupos (adaptado de la versión anterior)
        # Intentar establecer el color de fondo del canvas para que coincida con el frame
        try:
            bg_color = ttk.Style().lookup('TFrame', 'background')
        except tk.TclError: # Fallback si el estilo no está disponible o TFrame no es conocido
            bg_color = self.cget('bg') # Usar el color de fondo del propio diálogo

        self.groups_canvas = tk.Canvas(self.group_selection_outer_frame, borderwidth=0, highlightthickness=0, height=100, bg=bg_color) # Altura inicial
        self.groups_inner_frame = ttk.Frame(self.groups_canvas) # Este frame debería tomar el bg de su padre (el canvas) o ser transparente
        self.groups_scrollbar = ttk.Scrollbar(self.group_selection_outer_frame, orient="vertical", command=self.groups_canvas.yview)
        self.groups_canvas.configure(yscrollcommand=self.groups_scrollbar.set)

        self.groups_scrollbar.pack(side="right", fill="y")
        self.groups_canvas.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5) # Ajustar padding
        self.canvas_window = self.groups_canvas.create_window((0, 0), window=self.groups_inner_frame, anchor="nw")

        self.groups_inner_frame.bind("<Configure>", lambda e: self.groups_canvas.configure(scrollregion=self.groups_canvas.bbox("all")) if hasattr(self, 'groups_canvas') and self.groups_canvas.winfo_exists() else None)
        # Removed: self.groups_canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.add_group_button = ttk.Button(self.group_selection_outer_frame, text="+ Añadir Grupo", command=self.add_group_selector)
        self.add_group_button.pack(pady=5, anchor='w', padx=5)
        Tooltip(self.add_group_button, text="Añadir otro grupo a la comparación SPM. Se requieren al menos dos grupos.", short_text="Añadir grupo.", enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Selección de Columna (Variable a Analizar) ---
        self.column_frame = ttk.LabelFrame(main_frame, text="Variable a Analizar")
        self.column_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.column_frame.columnconfigure(1, weight=1)
        self.column_frame.grid_remove()
        ttk.Label(self.column_frame, text="Columna:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        column_combo_frame_cont = ttk.Frame(self.column_frame)
        column_combo_frame_cont.grid(row=0, column=1, sticky="ew")
        self.column_combo = ttk.Combobox(column_combo_frame_cont, textvariable=self.column_var, state="readonly", width=45, font=scaled_font)
        self.column_combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.column_combo.bind("<<ComboboxSelected>>", self._on_column_selected)
        column_help_long_text = "Seleccione la columna de datos cinemáticos (variable dependiente) que contiene la serie temporal a analizar.\nEj: LAnkleAngles/X/deg"
        column_help_short_text = "Variable cinemática para análisis SPM."
        column_help_btn = ttk.Button(column_combo_frame_cont, text="?", width=3, style="Help.TButton",
                                     command=lambda: self._show_input_help("Ayuda: Variable a Analizar (Continuo)", column_help_long_text))
        column_help_btn.pack(side=tk.LEFT)
        Tooltip(column_help_btn, text=column_help_long_text, short_text=column_help_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Opciones de Visualización ---
        self.plot_options_frame = ttk.LabelFrame(main_frame, text="Opciones de Visualización del Gráfico")
        self.plot_options_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        self.plot_options_frame.grid_remove()

        # DE
        std_dev_frame = ttk.Frame(self.plot_options_frame)
        std_dev_frame.pack(anchor="w", padx=5)
        self.cb_std_dev = ttk.Checkbutton(std_dev_frame, text="Visualizar Desviación Estándar (DE)", variable=self.show_std_dev_var, command=lambda: self._on_viz_option_selected('std'))
        self.cb_std_dev.pack(side=tk.LEFT)
        std_dev_help_long_text = "Muestra la desviación estándar como una banda sombreada alrededor de la curva promedio del grupo."
        std_dev_help_short_text = "Mostrar DE en gráfico."
        std_dev_help_btn = ttk.Button(std_dev_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Desviación Estándar", std_dev_help_long_text))
        std_dev_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(std_dev_help_btn, text=std_dev_help_long_text, short_text=std_dev_help_short_text, enabled=self.settings.enable_hover_tooltips)

        # IC
        conf_int_frame = ttk.Frame(self.plot_options_frame)
        conf_int_frame.pack(anchor="w", padx=5)
        self.cb_conf_int = ttk.Checkbutton(conf_int_frame, text="Visualizar Intervalos de Confianza (IC)", variable=self.show_conf_int_var, command=lambda: self._on_viz_option_selected('ci'))
        self.cb_conf_int.pack(side=tk.LEFT)
        conf_int_help_long_text = "Muestra los intervalos de confianza (generalmente 95%) como una banda sombreada alrededor de la curva promedio."
        conf_int_help_short_text = "Mostrar IC en gráfico."
        conf_int_help_btn = ttk.Button(conf_int_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Intervalos de Confianza", conf_int_help_long_text))
        conf_int_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(conf_int_help_btn, text=conf_int_help_long_text, short_text=conf_int_help_short_text, enabled=self.settings.enable_hover_tooltips)
        
        # EEM
        sem_frame = ttk.Frame(self.plot_options_frame)
        sem_frame.pack(anchor="w", padx=5)
        self.cb_sem = ttk.Checkbutton(sem_frame, text="Visualizar Error Estándar de la Media (EEM)", variable=self.show_sem_var, command=lambda: self._on_viz_option_selected('sem'))
        self.cb_sem.pack(side=tk.LEFT)
        sem_help_long_text = "Muestra el error estándar de la media como una banda sombreada alrededor de la curva promedio."
        sem_help_short_text = "Mostrar EEM en gráfico."
        sem_help_btn = ttk.Button(sem_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Error Estándar de la Media", sem_help_long_text))
        sem_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(sem_help_btn, text=sem_help_long_text, short_text=sem_help_short_text, enabled=self.settings.enable_hover_tooltips)

        ttk.Separator(self.plot_options_frame, orient='horizontal').pack(fill='x', pady=5, padx=5)
        
        # Interactivo
        interactive_frame = ttk.Frame(self.plot_options_frame)
        interactive_frame.pack(anchor="w", padx=5, pady=(0,5))
        self.cb_interactive_plot = ttk.Checkbutton(interactive_frame, text="Generar Gráfico Interactivo (HTML)", variable=self.generate_interactive_plot_var)
        self.cb_interactive_plot.pack(side=tk.LEFT)
        interactive_help_long_text = "Genera una versión HTML interactiva del gráfico (usando Plotly) además del gráfico estático PNG."
        interactive_help_short_text = "Generar HTML interactivo."
        interactive_help_btn = ttk.Button(interactive_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Gráfico Interactivo", interactive_help_long_text))
        interactive_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(interactive_help_btn, text=interactive_help_long_text, short_text=interactive_help_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Opciones de Anotación del Gráfico ---
        self.annotation_options_frame = ttk.LabelFrame(main_frame, text="Opciones de Anotación del Gráfico")
        self.annotation_options_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        self.annotation_options_frame.grid_remove() # Ocultar inicialmente

        # Anotar clusters
        annotate_clusters_frame = ttk.Frame(self.annotation_options_frame)
        annotate_clusters_frame.pack(anchor="w", padx=5, pady=(5,0))
        ttk.Checkbutton(annotate_clusters_frame, text="Anotar clusters significativos SPM (gráfico inferior)", variable=self.annotate_spm_clusters_bottom_var).pack(side=tk.LEFT)
        annotate_clusters_help_long_text = "Si se encuentran clusters de tiempo donde la diferencia es estadísticamente significativa, se resaltarán en el panel inferior del gráfico SPM."
        annotate_clusters_help_short_text = "Resaltar clusters SPM."
        annotate_clusters_help_btn = ttk.Button(annotate_clusters_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Anotar Clusters SPM", annotate_clusters_help_long_text))
        annotate_clusters_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(annotate_clusters_help_btn, text=annotate_clusters_help_long_text, short_text=annotate_clusters_help_short_text, enabled=self.settings.enable_hover_tooltips)

        # Anotar rango
        annotate_range_frame = ttk.Frame(self.annotation_options_frame)
        annotate_range_frame.pack(anchor="w", padx=5)
        ttk.Checkbutton(annotate_range_frame, text="Anotar rango significativo SPM (gráfico superior)", variable=self.annotate_spm_range_top_var).pack(side=tk.LEFT)
        annotate_range_help_long_text = "Si se encuentra un rango de tiempo general donde la diferencia es significativa, se indicará en el panel superior del gráfico SPM."
        annotate_range_help_short_text = "Indicar rango SPM."
        annotate_range_help_btn = ttk.Button(annotate_range_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Anotar Rango SPM", annotate_range_help_long_text))
        annotate_range_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(annotate_range_help_btn, text=annotate_range_help_long_text, short_text=annotate_range_help_short_text, enabled=self.settings.enable_hover_tooltips)
        
        # Delimitar Rango de Tiempo
        delimit_time_frame = ttk.Frame(self.annotation_options_frame)
        delimit_time_frame.pack(anchor="w", padx=5, pady=(5,0))
        self.delimit_time_checkbox = ttk.Checkbutton(delimit_time_frame, text="Delimitar Rango de Tiempo Mostrado", variable=self.delimit_time_range_var, command=self._toggle_time_delimitation_widgets)
        self.delimit_time_checkbox.pack(side=tk.LEFT)
        delimit_time_help_long_text = "Permite especificar un sub-rango del ciclo normalizado (0-100%) para enfocar la visualización del gráfico.\nÚtil para examinar fases específicas del movimiento."
        delimit_time_help_short_text = "Enfocar gráfico en sub-rango."
        delimit_time_help_btn = ttk.Button(delimit_time_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Delimitar Rango de Tiempo", delimit_time_help_long_text))
        delimit_time_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(delimit_time_help_btn, text=delimit_time_help_long_text, short_text=delimit_time_help_short_text, enabled=self.settings.enable_hover_tooltips)

        self.time_delimitation_subframe = ttk.Frame(self.annotation_options_frame, padding=(15, 5, 5, 5)) # Subframe con indentación
        self.time_delimitation_subframe.pack(fill=tk.X, expand=True)
        # Los widgets dentro de este subframe se mostrarán/ocultarán dinámicamente

        row_idx += 1
        
        # --- Nombre del Análisis ---
        self.analysis_name_frame = ttk.LabelFrame(main_frame, text="Guardar Análisis Como")
        self.analysis_name_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.analysis_name_frame.columnconfigure(1, weight=1)
        self.analysis_name_frame.grid_remove()
        ttk.Label(self.analysis_name_frame, text="Nombre:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        analysis_name_entry_frame_cont = ttk.Frame(self.analysis_name_frame)
        analysis_name_entry_frame_cont.grid(row=0, column=1, sticky="ew")
        ttk.Entry(analysis_name_entry_frame_cont, textvariable=self.analysis_name_var, font=scaled_font).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        
        analysis_name_help_long_text = "Ingrese un nombre descriptivo para guardar este análisis continuo (SPM).\nEvite caracteres especiales como / \\ : * ? \" < > |"
        analysis_name_help_short_text = "Nombre para el análisis SPM."
        analysis_name_help_btn = ttk.Button(analysis_name_entry_frame_cont, text="?", width=3, style="Help.TButton",
                                            command=lambda: self._show_input_help("Ayuda: Nombre del Análisis (Continuo)", analysis_name_help_long_text))
        analysis_name_help_btn.pack(side=tk.LEFT)
        Tooltip(analysis_name_help_btn, text=analysis_name_help_long_text, short_text=analysis_name_help_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Botones de Acción ---
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="e", pady=10)
        self.button_frame.grid_remove()
        self.save_button = ttk.Button(self.button_frame, text="Generar Gráfico y Guardar", command=self._on_accept, state=tk.DISABLED, style="Green.TButton")
        self.save_button.pack(side=tk.RIGHT, padx=5)
        Tooltip(self.save_button, text="Generar el gráfico SPM y guardar la configuración del análisis.", short_text="Generar y guardar.", enabled=self.settings.enable_hover_tooltips)
        cancel_button_continuous = ttk.Button(self.button_frame, text="Cancelar", command=self._on_cancel)
        cancel_button_continuous.pack(side=tk.RIGHT)
        Tooltip(cancel_button_continuous, text="Cerrar este diálogo sin generar ni guardar el análisis.", short_text="Cancelar.", enabled=self.settings.enable_hover_tooltips)

        # Crear widgets de delimitación de tiempo (inicialmente no empaquetados)
        self._create_time_delimitation_widgets()
        self._toggle_time_delimitation_widgets() # Para asegurar estado inicial correcto


    # Removed: def _on_canvas_configure(self, event):
    # Removed _update_dialog_size_and_scrollbar method as per user request implicitly by new system

    def _on_accept(self):
        """Valida la config y guarda el resultado."""
        analysis_name = self.analysis_name_var.get().strip()
        selected_col = self.column_var.get()
        selected_group_keys = self.get_selected_group_keys()
        show_std_dev = self.show_std_dev_var.get()
        show_conf_int = self.show_conf_int_var.get()
        show_sem = self.show_sem_var.get()
        generate_interactive_plot = self.generate_interactive_plot_var.get()
        
        # Nuevas opciones de anotación
        annotate_spm_clusters_bottom = self.annotate_spm_clusters_bottom_var.get()
        annotate_spm_range_top = self.annotate_spm_range_top_var.get()
        delimit_time_range = self.delimit_time_range_var.get()
        time_min_str = self.time_min_var.get()
        time_max_str = self.time_max_var.get()
        show_full_time_with_delimiters = self.show_full_time_with_delimiters_var.get()
        add_time_range_label = self.add_time_range_label_var.get()
        time_range_label_text = self.time_range_label_text_var.get().strip()

        mode = self.vi_grouping_mode.get()
        primary_vi = self.primary_vi_var.get() if mode == '1VI' else None
        fixed_vi = self.fixed_vi_var.get() if mode == '2VIs' else None
        fixed_descriptor_display = self.fixed_descriptor_var.get() if mode == '2VIs' else None


        # --- Validaciones ---
        if not analysis_name:
            messagebox.showerror("Error de Validación", "Ingrese un nombre para el análisis.", parent=self)
            return
        
        invalid_chars = r'<>:"/\|?*'
        if any(char in analysis_name for char in invalid_chars):
            messagebox.showerror("Error de Validación", f"El nombre del análisis contiene caracteres inválidos: {invalid_chars}", parent=self)
            return

        if not mode:
            messagebox.showerror("Error de Validación", "Seleccione un modo de agrupación (1 VI o 2 VIs).", parent=self)
            return
            
        if len(selected_group_keys) < 2:
            messagebox.showerror("Error de Validación", "Seleccione al menos dos grupos válidos y distintos para comparar.", parent=self)
            return
        
        if not selected_col:
            messagebox.showerror("Error de Validación", "Seleccione la columna a analizar.", parent=self)
            return

        time_min, time_max = 0.0, 100.0
        if delimit_time_range:
            try:
                time_min = float(time_min_str)
                time_max = float(time_max_str)
                if not (0 <= time_min <= 100 and 0 <= time_max <= 100 and time_min < time_max):
                    messagebox.showerror("Error de Validación", "Tiempo Mínimo y Máximo deben estar entre 0 y 100, y Mínimo < Máximo.", parent=self)
                    return
            except ValueError:
                messagebox.showerror("Error de Validación", "Tiempo Mínimo y Máximo deben ser números.", parent=self)
                return
            if add_time_range_label and not time_range_label_text:
                messagebox.showerror("Error de Validación", "Ingrese el texto para la etiqueta de rango de tiempo.", parent=self)
                return


        self.result = {
            "analysis_name": analysis_name,
            "data_type": "Cinematica", # Fijo para análisis continuo por ahora
            "column": selected_col,
            "groups": selected_group_keys,
            "show_std_dev": show_std_dev,
            "show_conf_int": show_conf_int,
            "show_sem": show_sem,
            "generate_interactive_plot": generate_interactive_plot,
            "grouping_mode": mode,
            "primary_vi_name": primary_vi,
            "annotate_spm_clusters_bottom": annotate_spm_clusters_bottom,
            "annotate_spm_range_top": annotate_spm_range_top,
            "delimit_time_range": delimit_time_range,
            "time_min": time_min,
            "time_max": time_max,
            "show_full_time_with_delimiters": show_full_time_with_delimiters,
            "add_time_range_label": add_time_range_label,
            "time_range_label_text": time_range_label_text,
            "fixed_vi_name": fixed_vi,
            "fixed_descriptor_display": fixed_descriptor_display,
        }
        logger.info(f"Configuración de análisis continuo guardada: {self.result} para estudio {self.study_id}.")
        self.destroy()

    def _on_viz_option_selected(self, selected_option: str):
        """Asegura que solo una opción de visualización (DE, IC, EEM) esté activa."""
        if selected_option == 'std' and self.show_std_dev_var.get():
            self.show_conf_int_var.set(False)
            self.show_sem_var.set(False)
        elif selected_option == 'ci' and self.show_conf_int_var.get():
            self.show_std_dev_var.set(False)
            self.show_sem_var.set(False)
        elif selected_option == 'sem' and self.show_sem_var.get():
            self.show_std_dev_var.set(False)
            self.show_conf_int_var.set(False)

    def load_initial_data(self):
        """Carga datos iniciales: VIs, alias y verifica disponibilidad de Cinemática."""
        try:
            # Verificar si hay datos cinemáticos
            available_frequencies = self.analysis_service.get_available_frequencies_for_study(self.study_id)
            if "Cinematica" not in available_frequencies:
                messagebox.showwarning("No Disponible",
                                       "El análisis continuo actualmente solo está disponible para el Tipo de Dato 'Cinematica'.\n"
                                       "No se encontraron archivos cinemáticos procesados en este estudio.",
                                       parent=self)
                self.destroy()
                return False # Indicar que la inicialización no debe continuar

            # Si Cinemática está disponible, fijar el combobox
            self.frequency_var.set("Cinematica")
            self.freq_combo['values'] = ["Cinematica"]
            # El combobox ya está 'disabled' desde create_widgets

            # Cargar detalles del estudio (VIs y Alias)
            details = self.analysis_service.study_service.get_study_details(self.study_id)
            self.all_vi_names = [vi['name'] for vi in details.get('independent_variables', [])]
            self.all_descriptors_by_vi = {vi['name']: vi['descriptors'] for vi in details.get('independent_variables', [])}
            self.study_aliases = details.get('aliases', {})
            logger.debug(f"Datos iniciales cargados: VIs={self.all_vi_names}, Descriptores={self.all_descriptors_by_vi}, Alias={self.study_aliases}")

            # No es necesario cargar frecuencias en un combobox, ya que es fijo "Cinematica"
            # Los botones de modo VI se activan/desactivan en set_vi_grouping_mode
            # basado en self.all_vi_names

        except Exception as e:
            logger.error(f"Error cargando datos iniciales para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los datos iniciales del estudio: {e}", parent=self)
            self.destroy()
            return False # Indicar que la inicialización no debe continuar
        return True # Indicar que la inicialización fue exitosa

    def set_vi_grouping_mode(self, mode):
        """Configura la UI según se elija agrupar por 1 o 2 VIs."""
        self.vi_grouping_mode.set(mode)
        logger.info(f"Modo de agrupación seleccionado: {mode}")

        self.primary_vi_var.set("")
        self.fixed_vi_var.set("")
        self.fixed_descriptor_var.set("")
        self.available_groups_filtered = {}
        self._clear_group_selectors(update_columns=False)
        self.column_var.set("")
        if hasattr(self, 'column_combo'): self.column_combo['values'] = []
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)

        self.one_vi_config_frame.grid_remove()
        self.two_vi_config_frame.grid_remove()
        self.group_selection_outer_frame.grid_remove()
        self.column_frame.grid_remove()
        self.plot_options_frame.grid_remove()
        self.annotation_options_frame.grid_remove() # Ocultar nuevo frame
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()

        if mode == '1VI':
            self.one_vi_config_frame.grid()
            self.primary_vi_combo['values'] = self.all_vi_names
            self.one_vi_button.state(['pressed', 'disabled'])
            self.two_vi_button.state(['!pressed', '!disabled'])
        elif mode == '2VIs':
            if len(self.all_vi_names) < 2:
                 messagebox.showwarning("No disponible", "Se requieren al menos 2 Variables Independientes definidas en el estudio para agrupar por 2 VIs.", parent=self)
                 self.vi_grouping_mode.set("")
                 self.one_vi_button.state(['!pressed', '!disabled'])
                 self.two_vi_button.state(['!pressed', '!disabled'])
                 return
            self.two_vi_config_frame.grid()
            self.fixed_vi_combo['values'] = self.all_vi_names
            self.fixed_descriptor_combo['values'] = []
            self.one_vi_button.state(['!pressed', '!disabled'])
            self.two_vi_button.state(['pressed', 'disabled'])
        else:
             self.one_vi_button.state(['!pressed', '!disabled'])
             self.two_vi_button.state(['!pressed', '!disabled'])

    def _update_fixed_descriptor_options(self, event=None):
        """Actualiza el combobox de sub-valores fijos basado en la VI fija seleccionada."""
        fixed_vi_name = self.fixed_vi_var.get()
        self.fixed_descriptor_var.set("")
        self.fixed_descriptor_combo['values'] = []
        self.available_groups_filtered = {}
        self._clear_group_selectors(update_columns=False)

        if fixed_vi_name:
            descriptors = self.all_descriptors_by_vi.get(fixed_vi_name, [])
            display_descriptors = [f"{d} ({self.study_aliases.get(d)})" if self.study_aliases.get(d) else d for d in descriptors]
            self.fixed_descriptor_combo['values'] = sorted(display_descriptors)
            self.fixed_descriptor_label.config(text=f"Valor Fijo para '{fixed_vi_name}':")
        else:
             self.fixed_descriptor_label.config(text="Valor Fijo:")

        self.group_selection_outer_frame.grid_remove()
        self.column_frame.grid_remove()
        self.plot_options_frame.grid_remove()
        self.annotation_options_frame.grid_remove() # Ocultar nuevo frame
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)


    def update_available_groups(self, event=None):
        """Actualiza la lista de grupos FILTRADOS basados en las selecciones previas."""
        # Frecuencia es siempre "Cinematica" para continuo
        frequency = "Cinematica"
        mode = self.vi_grouping_mode.get()
        primary_vi = self.primary_vi_var.get() if mode == '1VI' else None
        fixed_vi = self.fixed_vi_var.get() if mode == '2VIs' else None
        fixed_descriptor_display = self.fixed_descriptor_var.get() if mode == '2VIs' else None

        if not mode or (mode == '1VI' and not primary_vi) or \
           (mode == '2VIs' and (not fixed_vi or not fixed_descriptor_display)):
            self.available_groups_filtered = {}
            self._clear_group_selectors(update_columns=False)
            self.group_selection_outer_frame.grid_remove()
            self.annotation_options_frame.grid_remove() # Ocultar nuevo frame
            logger.debug("Limpiando grupos: falta información previa.")
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
                study_id=self.study_id, frequency=frequency, mode=mode,
                primary_vi_name=primary_vi, fixed_vi_name=fixed_vi,
                fixed_descriptor_value=fixed_descriptor
            )
            self.available_groups_filtered = {display_name: key for key, display_name in filtered_groups.items()}
            logger.debug(f"Grupos filtrados disponibles: {self.available_groups_filtered}")

            self.group_selection_outer_frame.grid()
            self._update_group_combobox_values()

            if not self.group_selector_vars:
                 self.add_group_selector()
                 self.add_group_selector()

            self.column_frame.grid_remove()
            self.plot_options_frame.grid_remove()
            self.analysis_name_frame.grid_remove()
            self.button_frame.grid_remove()
            if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error actualizando grupos filtrados: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los grupos filtrados:\n{e}", parent=self)
            self.available_groups_filtered = {}
            self._clear_group_selectors(update_columns=False)
            self.group_selection_outer_frame.grid_remove()

    def _load_columns_for_analysis(self):
        """Carga las columnas/variables disponibles para el análisis (siempre Cinemática)."""
        # Este método es llamado después de que los grupos son seleccionados y válidos.
        # La frecuencia es fija "Cinematica". No se necesita el parámetro calculation.
        frequency = "Cinematica"
        selected_group_keys = self.get_selected_group_keys()

        if len(selected_group_keys) < 2: # Necesita al menos dos grupos para encontrar columnas comunes
            self.available_columns = []
            self.column_combo['values'] = []
            self.column_var.set("")
            self.column_frame.grid_remove()
            self._hide_final_steps()
            return

        try:
            # Para análisis continuo, no usamos get_common_columns_for_groups que depende de "calculation".
            # Usamos get_data_columns_for_frequency que lista todas las columnas numéricas de Cinemática.
            # La "comunalidad" se maneja al cargar los datos para SPM.
            all_cinematic_cols = self.analysis_service.get_data_columns_for_frequency(self.study_id, frequency)
            
            # Podríamos querer filtrar estas columnas si algunas no son adecuadas para SPM (ej. identificadores)
            # Por ahora, las usamos todas.
            self.available_columns = sorted(all_cinematic_cols)
            self.column_combo['values'] = self.available_columns
            logger.debug(f"Columnas cinemáticas disponibles para análisis continuo: {self.available_columns}")

            self.column_frame.grid()

            current_column = self.column_var.get()
            if current_column not in self.available_columns:
                self.column_var.set("")
                self._hide_final_steps()
            elif self.available_columns:
                self._show_final_steps() # Si hay columnas y la selección es válida o se acaba de seleccionar
            else:
                 self._hide_final_steps()
                 messagebox.showinfo("Sin Columnas", "No se encontraron columnas de datos cinemáticos.", parent=self)

        except Exception as e:
            logger.error(f"Error cargando columnas para análisis continuo: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar las columnas para análisis:\n{e}", parent=self)
            self.available_columns = []
            self.column_combo['values'] = []
            self.column_var.set("")
            self._hide_final_steps()


    def _on_column_selected(self, event=None):
        """Se llama cuando se selecciona una columna, muestra los pasos finales."""
        if self.column_var.get():
            self._show_final_steps()
        else:
            self._hide_final_steps()

    def _show_final_steps(self):
        """Muestra los frames de opciones de visualización, anotación, nombre y botones."""
        self.plot_options_frame.grid()
        self.annotation_options_frame.grid() # Mostrar nuevo frame
        self._toggle_time_delimitation_widgets() # Asegurar estado correcto de sub-widgets
        self.analysis_name_frame.grid()
        self.button_frame.grid()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.NORMAL)

    def _hide_final_steps(self):
        """Oculta los frames de opciones de visualización, anotación, nombre y botones."""
        self.plot_options_frame.grid_remove()
        self.annotation_options_frame.grid_remove() # Ocultar nuevo frame
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)

    def _create_time_delimitation_widgets(self):
        """Crea los widgets para la delimitación de tiempo, pero no los empaqueta."""
        # Tiempo Mínimo
        time_min_frame = ttk.Frame(self.time_delimitation_subframe)
        time_min_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        ttk.Label(time_min_frame, text="Tiempo Mínimo (%):").pack(side=tk.LEFT)
        self.time_min_entry = ttk.Entry(time_min_frame, textvariable=self.time_min_var, width=5)
        self.time_min_entry.pack(side=tk.LEFT, padx=(2,0))
        time_min_help_long_text = "Inicio del rango de tiempo a visualizar (0-100%). Debe ser menor que Tiempo Máximo."
        time_min_help_short_text = "Inicio del rango (0-100%)."
        time_min_help_btn = ttk.Button(time_min_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Tiempo Mínimo", time_min_help_long_text))
        time_min_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(time_min_help_btn, text=time_min_help_long_text, short_text=time_min_help_short_text, enabled=self.settings.enable_hover_tooltips)

        # Tiempo Máximo
        time_max_frame = ttk.Frame(self.time_delimitation_subframe)
        time_max_frame.grid(row=0, column=2, columnspan=2, sticky="w", padx=5, pady=2)
        ttk.Label(time_max_frame, text="Tiempo Máximo (%):").pack(side=tk.LEFT)
        self.time_max_entry = ttk.Entry(time_max_frame, textvariable=self.time_max_var, width=5)
        self.time_max_entry.pack(side=tk.LEFT, padx=(2,0))
        time_max_help_long_text = "Fin del rango de tiempo a visualizar (0-100%). Debe ser mayor que Tiempo Mínimo."
        time_max_help_short_text = "Fin del rango (0-100%)."
        time_max_help_btn = ttk.Button(time_max_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Tiempo Máximo", time_max_help_long_text))
        time_max_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(time_max_help_btn, text=time_max_help_long_text, short_text=time_max_help_short_text, enabled=self.settings.enable_hover_tooltips)

        # Checkbox Mostrar Tiempo Completo
        show_full_frame = ttk.Frame(self.time_delimitation_subframe)
        show_full_frame.grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=2)
        self.show_full_time_checkbox = ttk.Checkbutton(show_full_frame, text="Mostrar Tiempo Completo con Delimitadores", variable=self.show_full_time_with_delimiters_var)
        self.show_full_time_checkbox.pack(side=tk.LEFT)
        show_full_help_long_text = "Si está marcado, el gráfico mostrará el ciclo completo (0-100%) con el rango delimitado resaltado o indicado. Si no, solo mostrará el rango delimitado."
        show_full_help_short_text = "Mostrar ciclo completo o solo rango."
        show_full_help_btn = ttk.Button(show_full_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Mostrar Tiempo Completo", show_full_help_long_text))
        show_full_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(show_full_help_btn, text=show_full_help_long_text, short_text=show_full_help_short_text, enabled=self.settings.enable_hover_tooltips)
        
        # Checkbox Añadir Etiqueta de Rango
        add_label_frame = ttk.Frame(self.time_delimitation_subframe)
        add_label_frame.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=2)
        self.add_label_checkbox = ttk.Checkbutton(add_label_frame, text="Añadir Etiqueta de Rango de Tiempo", variable=self.add_time_range_label_var, command=self._toggle_time_label_entry)
        self.add_label_checkbox.pack(side=tk.LEFT)
        add_label_help_long_text = "Permite añadir un texto personalizado (ej. 'Fase de Apoyo') al gráfico para identificar el rango de tiempo delimitado."
        add_label_help_short_text = "Añadir etiqueta a rango."
        add_label_help_btn = ttk.Button(add_label_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Añadir Etiqueta de Rango", add_label_help_long_text))
        add_label_help_btn.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(add_label_help_btn, text=add_label_help_long_text, short_text=add_label_help_short_text, enabled=self.settings.enable_hover_tooltips)

        # Frame para Etiqueta de Rango (inicialmente oculto)
        self.time_label_entry_frame = ttk.Frame(self.time_delimitation_subframe) 
        self.time_label_entry_frame.grid(row=3, column=0, columnspan=4, sticky="ew", padx=(20, 5)) 
        
        label_text_frame = ttk.Frame(self.time_label_entry_frame) 
        label_text_frame.pack(fill=tk.X, expand=True)
        ttk.Label(label_text_frame, text="Texto de Etiqueta:").pack(side=tk.LEFT, padx=(0,5))
        self.time_label_text_entry = ttk.Entry(label_text_frame, textvariable=self.time_range_label_text_var, width=25)
        self.time_label_text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        label_text_help_long_text = "El texto que se mostrará en el gráfico para identificar el rango de tiempo delimitado."
        label_text_help_short_text = "Texto para etiqueta de rango."
        label_text_help_btn = ttk.Button(label_text_frame, text="?", style="Help.TButton", width=3, command=lambda: self._show_input_help("Ayuda: Texto de Etiqueta", label_text_help_long_text))
        label_text_help_btn.pack(side=tk.LEFT)
        Tooltip(label_text_help_btn, text=label_text_help_long_text, short_text=label_text_help_short_text, enabled=self.settings.enable_hover_tooltips)


    def _toggle_time_delimitation_widgets(self):
        """Muestra u oculta los widgets de delimitación de tiempo."""
        if self.delimit_time_range_var.get():
            # Make the subframe visible. Its gridded children will appear with it.
            self.time_delimitation_subframe.pack(fill=tk.X, expand=True)
            # Update visibility of the time label entry within the subframe
            self._toggle_time_label_entry()
        else:
            # Hide the entire subframe. Its children will disappear with it.
            self.time_delimitation_subframe.pack_forget()

    def _toggle_time_label_entry(self):
        """Muestra u oculta el campo de entrada para la etiqueta de rango de tiempo."""
        if self.delimit_time_range_var.get() and self.add_time_range_label_var.get():
            self.time_label_entry_frame.grid() # O pack()
        else:
            self.time_label_entry_frame.grid_remove() # O pack_forget()


    def add_group_selector(self, initial_value=""):
        """Añade un nuevo selector de grupo (Combobox + botón eliminar)."""
        if not self.groups_inner_frame.winfo_exists(): return # Prevenir error si el frame no existe

        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)

        selector_frame = ttk.Frame(self.groups_inner_frame)
        selector_frame.pack(fill=tk.X, pady=2, padx=(0,0)) # Ajustar padding

        group_var = tk.StringVar(value=initial_value)
        
        group_combo_frame_cont = ttk.Frame(selector_frame) # Frame para combo y botón de ayuda
        group_combo_frame_cont.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Ensure scaled_font is applied to the Combobox
        group_combo = ttk.Combobox(group_combo_frame_cont, textvariable=group_var, state="readonly",
                                   values=sorted(list(self.available_groups_filtered.keys())), width=30, font=scaled_font) 
        group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        group_combo.bind("<<ComboboxSelected>>", self._on_group_selection_change) # Cargar columnas al cambiar grupo
        
        group_select_help_long_text_cont = ("Seleccione un grupo (sub-valor o combinación de sub-valores con alias) para incluir en la comparación de series temporales.\n"
                                            "Debe seleccionar al menos dos grupos distintos.")
        group_select_help_short_text_cont = "Seleccionar grupo para comparar (SPM)."
        group_select_help_button_cont = ttk.Button(group_combo_frame_cont, text="?", width=3, style="Help.TButton",
                                                   command=lambda: self._show_input_help("Ayuda: Selección de Grupo (Continuo)", group_select_help_long_text_cont))
        group_select_help_button_cont.pack(side=tk.LEFT)
        help_tooltip = Tooltip(group_select_help_button_cont, text=group_select_help_long_text_cont, short_text=group_select_help_short_text_cont, enabled=self.settings.enable_hover_tooltips)
        

        remove_button = ttk.Button(selector_frame, text="🗑️", width=3,
                                   command=lambda f=selector_frame, v=group_var: self.remove_group_selector(f, v))
        remove_button.pack(side=tk.LEFT)
        Tooltip(remove_button, text="Quitar este grupo de la comparación SPM.", short_text="Quitar grupo.", enabled=self.settings.enable_hover_tooltips)

        self.group_selector_vars.append(group_var)
        self.group_selector_frames.append(selector_frame)
        self.group_selector_tooltips.append(help_tooltip) # Store the help button's tooltip
        self._update_remove_button_states()

        self.groups_inner_frame.update_idletasks()
        self.groups_canvas.config(scrollregion=self.groups_canvas.bbox("all"))
        
        self._on_group_selection_change() # Actualizar columnas
        self._refresh_group_combobox_options() # Actualizar opciones de todos los combos

    def _on_group_selection_change(self, event=None):
        """Llamado cuando la selección de un grupo cambia. Recarga las columnas y actualiza opciones de combo."""
        # Este método ahora llama a _load_columns_for_analysis
        # que es el equivalente a update_available_columns pero para continuo.
        self._load_columns_for_analysis()
        # Después de cargar columnas (que depende de las selecciones), refrescar opciones de combos de grupo
        self._refresh_group_combobox_options()


    def remove_group_selector(self, frame_to_remove, var_to_remove):
        """Elimina un selector de grupo."""
        if len(self.group_selector_vars) <= 2: # Mantener al menos dos, la validación final es en _on_accept
            messagebox.showwarning("Acción no permitida", "Se requieren al menos dos grupos para comparar.", parent=self)
            return

        try:
            index = self.group_selector_frames.index(frame_to_remove)
            self.group_selector_vars.pop(index)
            self.group_selector_frames.pop(index)
            if index < len(self.group_selector_tooltips): # Ensure index is valid before popping
                self.group_selector_tooltips.pop(index)
            frame_to_remove.destroy()
            self._update_remove_button_states()
            
            self.groups_inner_frame.update_idletasks()
            self.groups_canvas.config(scrollregion=self.groups_canvas.bbox("all"))

            self._on_group_selection_change() # Actualizar columnas
            self._refresh_group_combobox_options() # Actualizar opciones de todos los combos
        except (ValueError, IndexError):
            logger.warning("Intento de eliminar un selector de grupo que ya no existe o índice inválido.")

    def _update_remove_button_states(self):
        """Habilita o deshabilita los botones de eliminar grupo."""
        num_selectors = len(self.group_selector_frames)
        for i, frame in enumerate(self.group_selector_frames):
            if len(frame.winfo_children()) > 1:
                remove_button = frame.winfo_children()[1]
                if isinstance(remove_button, ttk.Button):
                    remove_button.config(state=tk.NORMAL if num_selectors > 2 else tk.DISABLED)


    def _clear_group_selectors(self, update_columns=True):
        """Limpia las opciones y valores de los selectores de grupo."""
        for frame in self.group_selector_frames:
            frame.destroy()
        self.group_selector_frames.clear()
        self.group_selector_vars.clear()
        self.group_selector_tooltips.clear() # Clear stored tooltips

        if hasattr(self, 'groups_inner_frame') and self.groups_inner_frame.winfo_exists():
            self.groups_inner_frame.update_idletasks()
            if hasattr(self, 'groups_canvas') and self.groups_canvas.winfo_exists():
                 self.groups_canvas.config(scrollregion=self.groups_canvas.bbox("all"))

        if update_columns:
            self._load_columns_for_analysis()
        # Siempre refrescar opciones de combo después de limpiar selectores
        self._refresh_group_combobox_options()


    def _refresh_group_combobox_options(self):
        """Actualiza las opciones de todos los combobox de grupo para evitar duplicados."""
        all_possible_options = sorted(list(self.available_groups_filtered.keys()))
        
        current_selections_in_all_combos = set()
        for sv in self.group_selector_vars:
            val = sv.get()
            if val:
                current_selections_in_all_combos.add(val)

        for i, combo_var in enumerate(self.group_selector_vars):
            if i >= len(self.group_selector_frames): continue

            # El frame del selector es self.group_selector_frames[i]
            # Dentro de este frame, el primer hijo es group_combo_frame_cont
            # Dentro de group_combo_frame_cont, el primer hijo es el Combobox
            try:
                group_combo_frame_cont = self.group_selector_frames[i].winfo_children()[0]
                combo_widget = group_combo_frame_cont.winfo_children()[0]
            except (IndexError, tk.TclError): # TclError if widget destroyed
                logger.warning(f"No se pudo acceder al combobox widget en el índice {i} al refrescar opciones.")
                continue # Saltar si el widget no se encuentra
            
            if not isinstance(combo_widget, ttk.Combobox): continue

            current_selection_this_combo = combo_var.get()
            
            options_for_this_combo = []
            for option in all_possible_options:
                is_selected_in_another_combo = False
                for other_idx, other_var in enumerate(self.group_selector_vars):
                    if i == other_idx: continue
                    if other_var.get() == option:
                        is_selected_in_another_combo = True
                        break
                
                if option == current_selection_this_combo or not is_selected_in_another_combo:
                    options_for_this_combo.append(option)
            
            combo_widget['values'] = options_for_this_combo

            # Re-apply font to ensure it's not lost during value updates
            scaled_font_refresh = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
            combo_widget.configure(font=scaled_font_refresh)
            
            if current_selection_this_combo and current_selection_this_combo not in options_for_this_combo:
                combo_var.set("")


    def _update_group_combobox_values(self):
        """Actualiza las opciones en todos los combobox de grupo existentes con los grupos FILTRADOS."""
        group_names = sorted(list(self.available_groups_filtered.keys()))
        
        # No limpiar selectores aquí, solo actualizar sus valores.
        # La limpieza y re-adición se maneja en update_available_groups.
        
        for i, var in enumerate(self.group_selector_vars):
             if i < len(self.group_selector_frames):
                 selector_frame = self.group_selector_frames[i]
                 if selector_frame.winfo_exists() and len(selector_frame.winfo_children()) > 0:
                     combo = selector_frame.winfo_children()[0]
                     if isinstance(combo, ttk.Combobox):
                         current_value = var.get()
                         combo['values'] = group_names
                         if current_value not in group_names: # Si el valor anterior ya no es válido
                             var.set("")
                         else:
                             var.set(current_value) # Mantener si es válido
             else:
                 logger.warning(f"Índice {i} fuera de rango para group_selector_frames al actualizar valores.")
        
        self._load_columns_for_analysis() # Actualizar columnas después de actualizar grupos
        self._refresh_group_combobox_options() # Asegurar que las opciones de combo se actualicen


    def get_selected_group_keys(self) -> List[str]:
        """Obtiene las claves originales de los grupos seleccionados y válidos de los FILTRADOS."""
        selected_keys = []
        selected_display_names = set()

        for group_var in self.group_selector_vars:
            display_name = group_var.get()
            if not display_name:
                continue

            if display_name in selected_display_names:
                # No mostrar messagebox aquí, la validación final es en _on_accept
                # Simplemente no añadir duplicados a la lista final de claves
                logger.warning(f"Grupo duplicado '{display_name}' detectado, se ignorará en la lista final de claves.")
                continue # No añadir duplicados

            selected_display_names.add(display_name)
            original_key = self.available_groups_filtered.get(display_name)
            if original_key:
                selected_keys.append(original_key)
            else:
                logger.error(f"Clave original no encontrada para el grupo filtrado seleccionado: '{display_name}'")
                # Si una clave no se encuentra, la selección es inválida
                messagebox.showerror("Error Interno", f"No se pudo encontrar la clave para el grupo '{display_name}'.", parent=self)
                return []
        
        # Eliminar duplicados de claves si por alguna razón pasaron (ej. dos display names diferentes apuntan a la misma clave)
        return list(dict.fromkeys(selected_keys))


    def _on_cancel(self, event=None):
        """Acción al presionar Cancelar o cerrar la ventana."""
        self.result = None
        self.destroy()

    # Removed _update_dialog_size_and_scrollbar method
    # Sizing is now simplified in __init__

    def _center_dialog(self):
        self.update_idletasks()
        
        ref_window = self.parent_window # self.parent_window was stored in __init__
        
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
        # Save button state will be handled by _show_final_steps or _hide_final_steps

        self.one_vi_config_frame.grid_remove()
        self.two_vi_config_frame.grid_remove()
        self.group_selection_outer_frame.grid_remove()
        self.column_frame.grid_remove()
        self.plot_options_frame.grid_remove()
        self.annotation_options_frame.grid_remove() 
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
                 self._resize_to_content() 
                 return
            self.two_vi_config_frame.grid()
            if hasattr(self, 'fixed_vi_combo'): self.fixed_vi_combo['values'] = self.all_vi_names
            if hasattr(self, 'fixed_descriptor_combo'): self.fixed_descriptor_combo['values'] = []
            if hasattr(self, 'one_vi_button'): self.one_vi_button.state(['!pressed', '!disabled'])
            if hasattr(self, 'two_vi_button'): self.two_vi_button.state(['pressed', 'disabled'])
        else: # Reset mode
             if hasattr(self, 'one_vi_button'): self.one_vi_button.state(['!pressed', '!disabled'])
             if hasattr(self, 'two_vi_button'): self.two_vi_button.state(['!pressed', '!disabled'])
        
        self._resize_to_content()


    def _update_fixed_descriptor_options(self, event=None):
        """Actualiza el combobox de sub-valores fijos basado en la VI fija seleccionada."""
        fixed_vi_name = self.fixed_vi_var.get()
        self.fixed_descriptor_var.set("")
        if hasattr(self, 'fixed_descriptor_combo'): self.fixed_descriptor_combo['values'] = [] # Check attribute existence
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
        self.plot_options_frame.grid_remove()
        self.annotation_options_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)
        
        self._resize_to_content()

    def update_available_groups(self, event=None):
        """Actualiza la lista de grupos FILTRADOS basados en las selecciones previas."""
        frequency = "Cinematica" # Fixed for continuous
        mode = self.vi_grouping_mode.get()
        primary_vi = self.primary_vi_var.get() if mode == '1VI' else None
        fixed_vi = self.fixed_vi_var.get() if mode == '2VIs' else None
        fixed_descriptor_display = self.fixed_descriptor_var.get() if mode == '2VIs' else None

        if not mode or (mode == '1VI' and not primary_vi) or \
           (mode == '2VIs' and (not fixed_vi or not fixed_descriptor_display)):
            self.available_groups_filtered = {}
            self._clear_group_selectors(update_columns=False)
            self.group_selection_outer_frame.grid_remove()
            # Ensure other dependent frames are also hidden
            self.column_frame.grid_remove()
            self.plot_options_frame.grid_remove()
            self.annotation_options_frame.grid_remove()
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
             if not fixed_descriptor: # If no alias match, assume it's original or original part
                 fixed_descriptor = fixed_descriptor_display.split(" (")[0]
        
        try:
            logger.debug(f"Actualizando grupos filtrados: mode={mode}, freq={frequency}, primary={primary_vi}, fixed_vi={fixed_vi}, fixed_desc={fixed_descriptor}")
            # This call should be to analysis_service
            filtered_groups_data = self.analysis_service.get_filtered_discrete_analysis_groups(
                study_id=self.study_id, frequency=frequency, mode=mode,
                primary_vi_name=primary_vi, fixed_vi_name=fixed_vi,
                fixed_descriptor_value=fixed_descriptor # Pass original descriptor value
            )
            self.available_groups_filtered = {display_name: key for key, display_name in filtered_groups_data.items()}
            logger.debug(f"Grupos filtrados disponibles: {self.available_groups_filtered}")

            self.group_selection_outer_frame.grid()
            self._update_group_combobox_values() # This will also call _load_columns_for_analysis

            if not self.group_selector_vars: # Add initial selectors if none exist
                 self.add_group_selector()
                 self.add_group_selector()
            
            # Hide subsequent sections until column is selected
            self.column_frame.grid_remove()
            self.plot_options_frame.grid_remove()
            self.annotation_options_frame.grid_remove()
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
        """Muestra los frames de opciones de visualización, anotación, nombre y botones."""
        self.plot_options_frame.grid()
        self.annotation_options_frame.grid() 
        self._toggle_time_delimitation_widgets() 
        self.analysis_name_frame.grid()
        self.button_frame.grid()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.NORMAL)
        self._resize_to_content()

    def _hide_final_steps(self):
        """Oculta los frames de opciones de visualización, anotación, nombre y botones."""
        self.plot_options_frame.grid_remove()
        self.annotation_options_frame.grid_remove() 
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        if hasattr(self, 'save_button'): self.save_button.config(state=tk.DISABLED)
        self._resize_to_content()

    def _toggle_time_delimitation_widgets(self):
        """Muestra u oculta los widgets de delimitación de tiempo."""
        if self.delimit_time_range_var.get():
            self.time_delimitation_subframe.pack(fill=tk.X, expand=True)
            self._toggle_time_label_entry()
        else:
            self.time_delimitation_subframe.pack_forget()
        self._resize_to_content()

    def _toggle_time_label_entry(self):
        """Muestra u oculta el campo de entrada para la etiqueta de rango de tiempo."""
        if self.delimit_time_range_var.get() and self.add_time_range_label_var.get():
            if hasattr(self, 'time_label_entry_frame'): self.time_label_entry_frame.grid() 
        else:
            if hasattr(self, 'time_label_entry_frame'): self.time_label_entry_frame.grid_remove()
        self._resize_to_content()

    def add_group_selector(self, initial_value=""):
        """Añade un nuevo selector de grupo (Combobox + botón eliminar)."""
        if not self.groups_inner_frame.winfo_exists(): 
            return 

        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
        selector_frame = ttk.Frame(self.groups_inner_frame)
        selector_frame.pack(fill=tk.X, pady=2, padx=(0,0)) 

        group_var = tk.StringVar(value=initial_value)
        
        group_combo_frame_cont = ttk.Frame(selector_frame) 
        group_combo_frame_cont.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        group_combo = ttk.Combobox(group_combo_frame_cont, textvariable=group_var, state="readonly",
                                   values=sorted(list(self.available_groups_filtered.keys())), width=30, font=scaled_font) 
        group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        group_combo.bind("<<ComboboxSelected>>", self._on_group_selection_change) 
        
        group_select_help_long_text_cont = ("Seleccione un grupo (sub-valor o combinación de sub-valores con alias) para incluir en la comparación de series temporales.\n"
                                            "Debe seleccionar al menos dos grupos distintos.")
        group_select_help_short_text_cont = "Seleccionar grupo para comparar (SPM)."
        group_select_help_button_cont = ttk.Button(group_combo_frame_cont, text="?", width=3, style="Help.TButton",
                                                   command=lambda: self._show_input_help("Ayuda: Selección de Grupo (Continuo)", group_select_help_long_text_cont))
        group_select_help_button_cont.pack(side=tk.LEFT)
        help_tooltip = Tooltip(group_select_help_button_cont, text=group_select_help_long_text_cont, short_text=group_select_help_short_text_cont, enabled=self.settings.enable_hover_tooltips)
        

        remove_button = ttk.Button(selector_frame, text="🗑️", width=3,
                                   command=lambda f=selector_frame, v=group_var: self.remove_group_selector(f, v))
        remove_button.pack(side=tk.LEFT)
        Tooltip(remove_button, text="Quitar este grupo de la comparación SPM.", short_text="Quitar grupo.", enabled=self.settings.enable_hover_tooltips)

        self.group_selector_vars.append(group_var)
        self.group_selector_frames.append(selector_frame)
        self.group_selector_tooltips.append(help_tooltip)
        self._update_remove_button_states()

        self.groups_inner_frame.update_idletasks()
        # self.groups_canvas.config(scrollregion=self.groups_canvas.bbox("all")) # Done by _adjust_dialog_layout
        
        self._on_group_selection_change() 
        self._refresh_group_combobox_options() 
        self._resize_to_content()

    def remove_group_selector(self, frame_to_remove, var_to_remove):
        """Elimina un selector de grupo."""
        if len(self.group_selector_vars) <= 2: 
            messagebox.showwarning("Acción no permitida", "Se requieren al menos dos grupos para comparar.", parent=self)
            return

        try:
            index = self.group_selector_frames.index(frame_to_remove)
            self.group_selector_vars.pop(index)
            self.group_selector_frames.pop(index)
            if index < len(self.group_selector_tooltips):
                self.group_selector_tooltips.pop(index)
            frame_to_remove.destroy()
            self._update_remove_button_states()
            
            self.groups_inner_frame.update_idletasks()
            # self.groups_canvas.config(scrollregion=self.groups_canvas.bbox("all")) # Done by _adjust_dialog_layout

            self._on_group_selection_change() 
            self._refresh_group_combobox_options() 
        except (ValueError, IndexError):
            logger.warning("Intento de eliminar un selector de grupo que ya no existe o índice inválido.")
        self._resize_to_content()

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Ventana Principal (Dummy)")
    root.withdraw() # Ocultar ventana principal para prueba de diálogo

    class DummyStudyService:
        def get_study_details(self, study_id):
            logger.info(f"DummyStudyService: get_study_details({study_id})")
            return {
                'independent_variables': [
                    {'name': 'Condicion', 'descriptors': ['PRE', 'POST', 'CONTROL']},
                    {'name': 'Salto', 'descriptors': ['CMJ', 'SJ', 'DJ']}
                ],
                'aliases': {'PRE': 'Antes', 'POST': 'Después', 'CMJ': 'Salto CMJ'}
            }
        def get_study_aliases(self, study_id): # Necesario si AnalysisService lo usa
             return self.get_study_details(study_id).get('aliases', {})


    class DummyAnalysisService:
        def __init__(self):
            logger.info("DummyAnalysisService inicializado.")
            self.study_service = DummyStudyService() # Inyectar study_service
            # Simular algunas claves de grupo que podrían existir en el estudio
            # Estas claves deben ser generadas por get_filtered_discrete_analysis_groups
            self.dummy_filtered_groups_1VI_Condicion = {
                "Condicion=PRE": "Condicion: Antes",
                "Condicion=POST": "Condicion: Después",
                "Condicion=CONTROL": "Condicion: CONTROL"
            }
            self.dummy_filtered_groups_2VIs_Condicion_PRE_Salto = {
                 "Salto=CMJ": "Salto: Salto CMJ", # Asumiendo que Condicion=PRE está fijo
                 "Salto=SJ": "Salto: SJ",
                 "Salto=DJ": "Salto: DJ"
            }


        def get_available_frequencies_for_study(self, study_id):
            logger.info(f"Dummy: get_available_frequencies_for_study ({study_id})")
            return ["Cinematica"] 

        def get_data_columns_for_frequency(self, study_id, frequency):
            logger.info(f"Dummy: get_data_columns_for_frequency ({study_id}, {frequency})")
            if frequency == "Cinematica":
                return [
                    "LAnkleAngles/X/deg", "LAnkleAngles/Y/deg", "LAnkleAngles/Z/deg",
                    "RKneeAngles/X/deg", "RKneeAngles/Y/deg", "RKneeAngles/Z/deg",
                ]
            return []

        def get_filtered_discrete_analysis_groups(self, study_id: int, frequency: str, mode: str,
                                              primary_vi_name=None,
                                              fixed_vi_name=None,
                                              fixed_descriptor_value=None) -> dict:
            logger.info(f"Dummy: get_filtered_discrete_analysis_groups call with mode: {mode}, primary_vi: {primary_vi_name}, fixed_vi: {fixed_vi_name}, fixed_desc: {fixed_descriptor_value}")
            # Devolver {original_key: display_name}
            if mode == "1VI":
                if primary_vi_name == "Condicion":
                    return {k: v for v, k in self.dummy_filtered_groups_1VI_Condicion.items()} # Invertir para el formato esperado
                elif primary_vi_name == "Salto":
                     return {"Salto=CMJ": "Salto: Salto CMJ", "Salto=SJ": "Salto: SJ", "Salto=DJ": "Salto: DJ"}
            elif mode == "2VIs":
                if fixed_vi_name == "Condicion" and fixed_descriptor_value == "PRE": # Asumiendo que 'PRE' es el valor original
                    return {k: v for v, k in self.dummy_filtered_groups_2VIs_Condicion_PRE_Salto.items()}
                # Añadir más casos para otras VIs fijas si es necesario para probar
            return {}


    dummy_service = DummyAnalysisService()
    study_id_test = 1

    # Crear una ventana raíz temporal si no existe (para messagebox)
    try:
        root_for_dialog = tk.Toplevel() # Usar Toplevel para que no interfiera con el mainloop de root
        root_for_dialog.withdraw()
        dialog = ContinuousAnalysisConfigDialog(root_for_dialog, dummy_service, study_id_test)
        # Centrar el diálogo (código de centrado omitido aquí por brevedad, ya está en __init__)
        root_for_dialog.wait_window(dialog) # Esperar a que el diálogo se cierre

        if dialog.result:
            print("Configuración guardada:", dialog.result)
        else:
            print("Diálogo cancelado o cerrado.")
        
        if root_for_dialog.winfo_exists():
             root_for_dialog.destroy()

    except tk.TclError as e:
        if "application has been destroyed" in str(e):
            print("Root window was destroyed, skipping dialog test.")
        else:
            raise
    
    if root.winfo_exists(): # Solo llamar mainloop si la ventana raíz principal aún existe
        root.mainloop()
    root.mainloop()
