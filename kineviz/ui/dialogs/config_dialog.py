import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, StringVar

# Importar AppSettings para type hinting
from kineviz.config.settings import AppSettings
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip
from kineviz.ui.dialogs.backup_restore_dialog import BackupRestoreDialog # Import new dialog
from kineviz.core import backup_manager # Import backup_manager module
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # Import font utilities

class ConfigDialog(Toplevel):
    """Diálogo para configurar los ajustes de la aplicación."""

    def __init__(self, parent, settings: AppSettings, reset_callback=None):
        """
        Inicializa el diálogo de configuración.

        :param parent: La ventana padre.
        :param settings: Instancia de AppSettings para cargar/guardar.
        :param reset_callback: Función a llamar cuando se presiona "Restablecer Valores por Defecto".
        """
        super().__init__(parent)
        self.settings = settings
        self.reset_callback = reset_callback # Callback para la acción de reseteo global

        self.title("Configuración")
        # self.geometry("450x380") # Initial size will be determined by content or set after widgets are created
        self.resizable(True, True) # Allow resizing

        # Variables para los campos de entrada
        self.var_studies_per_page = StringVar()
        self.var_files_per_page = StringVar()
        self.var_analysis_items_per_page = StringVar() # Renamed from var_pdfs_per_page
        self.var_discrete_tables_per_page = StringVar() # New variable
        self.var_font_scale = StringVar()
        self.var_theme = StringVar()
        self.var_show_factory_reset = tk.BooleanVar() # New variable for the switch
        self.var_enable_hover_tooltips = tk.BooleanVar() # New variable for hover tooltips
        self.var_max_auto_backups = StringVar()
        self.var_max_manual_backups = StringVar()
        self.var_auto_backup_cooldown = StringVar()


        self.load_current_settings()
        
        self.create_widgets()
        self._toggle_factory_reset_visibility() # Set initial visibility

        # Centrar diálogo
        self.transient(parent)
        self.grab_set()
        # Código para centrar (opcional, similar a StudyDialog)
        # ...

    def _show_input_help(self, title: str, message: str):
        """Muestra un popup de ayuda simple."""
        messagebox.showinfo(title, message, parent=self)

    def load_current_settings(self):
        """Carga los valores actuales desde AppSettings a las variables."""
        self.var_studies_per_page.set(str(self.settings.studies_per_page))
        self.var_files_per_page.set(str(self.settings.files_per_page))
        self.var_analysis_items_per_page.set(str(self.settings.analysis_items_per_page)) # Renamed
        self.var_discrete_tables_per_page.set(str(self.settings.discrete_tables_per_page)) # Load new setting
        self.var_font_scale.set(str(self.settings.font_scale))
        self.var_theme.set(self.settings.theme)
        self.var_show_factory_reset.set(self.settings.show_factory_reset_button) # Load new setting
        self.var_enable_hover_tooltips.set(self.settings.enable_hover_tooltips) # Load new setting
        self.var_max_auto_backups.set(str(self.settings.max_automatic_backups))
        self.var_max_manual_backups.set(str(self.settings.max_manual_backups))
        self.var_auto_backup_cooldown.set(str(self.settings.automatic_backup_cooldown_seconds))

    def create_widgets(self):
        """Crea los widgets del diálogo usando un Notebook para pestañas y un marco desplazable."""
        # Frame principal que contendrá el Notebook y los botones Guardar/Cancelar
        outer_frame = ttk.Frame(self, padding="10")
        outer_frame.pack(fill=tk.BOTH, expand=True)

        # --- Scrollable Area Setup ---
        # This container_frame will hold the notebook and will be placed inside the canvas
        self.container_for_notebook = ttk.Frame(outer_frame)
        self.canvas = tk.Canvas(self.container_for_notebook, highlightthickness=0)
        self.scrollbar_v = ttk.Scrollbar(self.container_for_notebook, orient="vertical", command=self.canvas.yview)
        self.scrollbar_h = ttk.Scrollbar(self.container_for_notebook, orient="horizontal", command=self.canvas.xview)
        
        # This is the frame that will actually be scrolled, and will contain the notebook
        self.scrollable_content_frame = ttk.Frame(self.canvas)

        self.scrollable_content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_v.set, xscrollcommand=self.scrollbar_h.set)

        self.container_for_notebook.grid_rowconfigure(0, weight=1)
        self.container_for_notebook.grid_columnconfigure(0, weight=1)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        # Scrollbars will be gridded by _update_scrollbars as needed

        self.container_for_notebook.pack(fill=tk.BOTH, expand=True, pady=(0,10)) # Pack before buttons

        # Crear el Notebook DENTRO del scrollable_content_frame
        notebook = ttk.Notebook(self.scrollable_content_frame) # Changed parent
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # Add some padding

        # --- Pestaña General ---
        tab_general = ttk.Frame(notebook, padding="10")
        notebook.add(tab_general, text="General")
        self._create_general_tab_widgets(tab_general)

        # --- Pestaña Paginación ---
        tab_pagination = ttk.Frame(notebook, padding="10")
        notebook.add(tab_pagination, text="Paginación")
        self._create_pagination_tab_widgets(tab_pagination)

        # --- Pestaña Copias de Seguridad ---
        tab_backups = ttk.Frame(notebook, padding="10")
        notebook.add(tab_backups, text="Copias de Seguridad")
        self._create_backups_tab_widgets(tab_backups)
        
        # --- Pestaña Avanzado ---
        tab_advanced = ttk.Frame(notebook, padding="10")
        notebook.add(tab_advanced, text="Avanzado")
        self._create_advanced_tab_widgets(tab_advanced)

        # --- Botones Guardar/Cancelar (fuera del Notebook y del área desplazable) ---
        button_frame = ttk.Frame(outer_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10,0))
        
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=0)

        # Apply scaled font to buttons
        scaled_button_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
        ttk.Button(button_frame, text="Guardar", command=self.save_settings, style="Accent.TButton").grid(row=0, column=2, padx=5, sticky="e")
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).grid(row=0, column=1, padx=5, sticky="e")
        
        # Apply font to buttons if style doesn't cover it or for consistency
        for child in button_frame.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(font=scaled_button_font)


        self.update_idletasks()
        self.minsize(500, 420) 
        self._update_scrollbars() # Initial scrollbar check
        self.bind("<Configure>", lambda e: self._update_scrollbars()) # Update on resize

    def _update_scrollbars(self, event=None):
        """Muestra u oculta las barras de desplazamiento según sea necesario."""
        self.update_idletasks() # Asegurar que las dimensiones de los widgets estén actualizadas

        content_req_width = self.scrollable_content_frame.winfo_reqwidth()
        content_req_height = self.scrollable_content_frame.winfo_reqheight()
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        v_scroll_needed = content_req_height > canvas_height
        h_scroll_needed = content_req_width > canvas_width
        
        # Vertical scrollbar
        if v_scroll_needed:
            if not self.scrollbar_v.winfo_ismapped(): self.scrollbar_v.grid(row=0, column=1, sticky="ns")
        elif self.scrollbar_v.winfo_ismapped(): self.scrollbar_v.grid_remove()
        
        # Horizontal scrollbar
        if h_scroll_needed:
            if not self.scrollbar_h.winfo_ismapped(): self.scrollbar_h.grid(row=1, column=0, sticky="ew")
        elif self.scrollbar_h.winfo_ismapped(): self.scrollbar_h.grid_remove()
        
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def _create_general_tab_widgets(self, parent_frame: ttk.Frame):
        """Crea los widgets para la pestaña 'General'."""
        # Apply scaled font to labels and specific widgets in this tab
        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
        
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=3)
        row_idx = 0

        # --- Tamaño de Fuente ---
        label_font_scale = ttk.Label(parent_frame, text="Tamaño de Fuente (escala):", font=scaled_font)
        label_font_scale.grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        font_scale_frame = ttk.Frame(parent_frame)
        font_scale_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        font_scale_options = ["0.8", "0.9", "1.0", "1.1", "1.2", "1.3", "1.5", "1.75", "2.0"]
        font_scale_combo = ttk.Combobox(font_scale_frame, textvariable=self.var_font_scale, values=font_scale_options, width=5, state="readonly", font=scaled_font)
        font_scale_combo.pack(side=tk.LEFT, padx=(0,5))
        font_scale_long_text = ("Ajusta el tamaño general del texto en la aplicación.\n"
                                "1.0 es el tamaño normal. Valores mayores agrandan el texto, menores lo achican.")
        font_scale_short_text = "Ajusta el tamaño del texto en la aplicación."
        font_scale_help_btn = ttk.Button(font_scale_frame, text="?", width=3, style="Help.TButton",
                                         command=lambda: self._show_input_help("Ayuda: Tamaño de Fuente", font_scale_long_text))
        font_scale_help_btn.pack(side=tk.LEFT)
        Tooltip(font_scale_help_btn, text=font_scale_long_text, short_text=font_scale_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Tema de Aplicación ---
        label_theme = ttk.Label(parent_frame, text="Tema de Aplicación:", font=scaled_font)
        label_theme.grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        theme_frame = ttk.Frame(parent_frame)
        theme_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        theme_options = ["Light", "Dark"]
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.var_theme, values=theme_options, width=10, state="readonly", font=scaled_font)
        theme_combo.pack(side=tk.LEFT, padx=(0,5))
        theme_long_text = ("Cambia la apariencia visual de la aplicación (colores).\n"
                           "Light: Tema claro (predeterminado).\n"
                           "Dark: Tema oscuro.")
        theme_short_text = "Cambia la apariencia visual (colores)."
        theme_help_btn = ttk.Button(theme_frame, text="?", width=3, style="Help.TButton",
                                    command=lambda: self._show_input_help("Ayuda: Tema de Aplicación", theme_long_text))
        theme_help_btn.pack(side=tk.LEFT)
        Tooltip(theme_help_btn, text=theme_long_text, short_text=theme_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        # --- Switch para habilitar/deshabilitar tooltips por hover ---
        enable_tooltips_frame = ttk.Frame(parent_frame)
        enable_tooltips_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10, 5), sticky="w")
        enable_tooltips_cb = ttk.Checkbutton(
            enable_tooltips_frame,
            text="Habilitar Tooltips por Hover (Accesibilidad)",
            variable=self.var_enable_hover_tooltips
        )
        enable_tooltips_cb.pack(side=tk.LEFT, padx=(0,5))
        # Apply font to Checkbutton text if style doesn't cover it
        # enable_tooltips_cb.configure(font=scaled_font) # Usually handled by style or default
        enable_tooltips_long_text = ("Activa o desactiva los tooltips que aparecen al pasar el cursor sobre ciertos elementos.\n"
                                     "Estos tooltips respetan la configuración de tamaño de fuente.\n"
                                     "Los popups de ayuda por clic seguirán funcionando independientemente de esta opción.")
        enable_tooltips_short_text = "Activa/desactiva tooltips por hover (accesibilidad)."
        enable_tooltips_help_btn = ttk.Button(enable_tooltips_frame, text="?", width=3, style="Help.TButton",
                                              command=lambda: self._show_input_help("Ayuda: Habilitar Tooltips por Hover", enable_tooltips_long_text))
        enable_tooltips_help_btn.pack(side=tk.LEFT)
        Tooltip(enable_tooltips_help_btn, text=enable_tooltips_long_text, short_text=enable_tooltips_short_text, enabled=self.settings.enable_hover_tooltips)

    def _create_pagination_tab_widgets(self, parent_frame: ttk.Frame):
        """Crea los widgets para la pestaña 'Paginación'."""
        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=3)
        row_idx = 0

        label_studies_pp = ttk.Label(parent_frame, text="Estudios por página:", font=scaled_font)
        label_studies_pp.grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        studies_frame = ttk.Frame(parent_frame)
        studies_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        studies_entry = ttk.Entry(studies_frame, textvariable=self.var_studies_per_page, width=7, font=scaled_font)
        studies_entry.pack(side=tk.LEFT, padx=(0,5))
        studies_long_text = "Número de estudios a mostrar por página en la vista principal."
        studies_short_text = "Estudios por página."
        studies_help_btn = ttk.Button(studies_frame, text="?", width=3, style="Help.TButton",
                                      command=lambda: self._show_input_help("Ayuda: Estudios por Página", studies_long_text))
        studies_help_btn.pack(side=tk.LEFT)
        Tooltip(studies_help_btn, text=studies_long_text, short_text=studies_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        label_files_pp = ttk.Label(parent_frame, text="Archivos por página (vista estudio):", font=scaled_font)
        label_files_pp.grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        files_frame = ttk.Frame(parent_frame)
        files_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        files_entry = ttk.Entry(files_frame, textvariable=self.var_files_per_page, width=7, font=scaled_font)
        files_entry.pack(side=tk.LEFT, padx=(0,5))
        files_long_text = "Número de archivos a mostrar por página en el navegador de archivos de la vista de estudio."
        files_short_text = "Archivos por página (vista estudio)."
        files_help_btn = ttk.Button(files_frame, text="?", width=3, style="Help.TButton",
                                    command=lambda: self._show_input_help("Ayuda: Archivos por Página", files_long_text))
        files_help_btn.pack(side=tk.LEFT)
        Tooltip(files_help_btn, text=files_long_text, short_text=files_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        label_discrete_tables_pp = ttk.Label(parent_frame, text="Tablas resumen discreto por página:", font=scaled_font)
        label_discrete_tables_pp.grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        discrete_tables_frame = ttk.Frame(parent_frame)
        discrete_tables_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        discrete_tables_entry = ttk.Entry(discrete_tables_frame, textvariable=self.var_discrete_tables_per_page, width=7, font=scaled_font)
        discrete_tables_entry.pack(side=tk.LEFT, padx=(0,5))
        discrete_tables_long_text = "Número de tablas de resumen (ej. Maximo_Cinematica_...) a mostrar por página en la vista de 'Análisis Discreto'."
        discrete_tables_short_text = "Tablas resumen discreto por página."
        discrete_tables_help_btn = ttk.Button(discrete_tables_frame, text="?", width=3, style="Help.TButton",
                                              command=lambda: self._show_input_help("Ayuda: Tablas de Resumen Discreto por Página", discrete_tables_long_text))
        discrete_tables_help_btn.pack(side=tk.LEFT)
        Tooltip(discrete_tables_help_btn, text=discrete_tables_long_text, short_text=discrete_tables_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        label_analysis_items_pp = ttk.Label(parent_frame, text="Elementos por página (gestores análisis):", font=scaled_font)
        label_analysis_items_pp.grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        analysis_items_frame = ttk.Frame(parent_frame)
        analysis_items_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        analysis_items_entry = ttk.Entry(analysis_items_frame, textvariable=self.var_analysis_items_per_page, width=7, font=scaled_font)
        analysis_items_entry.pack(side=tk.LEFT, padx=(0,5))
        analysis_items_long_text = "Número de elementos (análisis guardados) a mostrar por página en los gestores de análisis discreto y continuo."
        analysis_items_short_text = "Elementos por página (gestores análisis)."
        analysis_items_help_btn = ttk.Button(analysis_items_frame, text="?", width=3, style="Help.TButton",
                                             command=lambda: self._show_input_help("Ayuda: Elementos por Página (Gestores de Análisis)", analysis_items_long_text))
        analysis_items_help_btn.pack(side=tk.LEFT)
        Tooltip(analysis_items_help_btn, text=analysis_items_long_text, short_text=analysis_items_short_text, enabled=self.settings.enable_hover_tooltips)

    def _create_backups_tab_widgets(self, parent_frame: ttk.Frame):
        """Crea los widgets para la pestaña 'Copias de Seguridad'."""
        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=3)
        row_idx = 0

        label_max_auto = ttk.Label(parent_frame, text="Máx. copias automáticas:", font=scaled_font)
        label_max_auto.grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        max_auto_frame = ttk.Frame(parent_frame)
        max_auto_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        max_auto_entry = ttk.Entry(max_auto_frame, textvariable=self.var_max_auto_backups, width=7, font=scaled_font)
        max_auto_entry.pack(side=tk.LEFT, padx=(0,5))
        max_auto_long_text = ("Número máximo de copias de seguridad automáticas a conservar (0 para desactivar y eliminar todas).\n"
                              "El límite se aplica cuando se crea una nueva copia automática; las más antiguas se eliminan en ese momento.")
        max_auto_short_text = "Máx. copias automáticas (limpieza en nueva creación)."
        max_auto_help_btn = ttk.Button(max_auto_frame, text="?", width=3, style="Help.TButton",
                                       command=lambda: self._show_input_help("Ayuda: Máx. Copias Automáticas", max_auto_long_text))
        max_auto_help_btn.pack(side=tk.LEFT)
        Tooltip(max_auto_help_btn, text=max_auto_long_text, short_text=max_auto_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        label_max_manual = ttk.Label(parent_frame, text="Máx. copias manuales:", font=scaled_font)
        label_max_manual.grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        max_manual_frame = ttk.Frame(parent_frame)
        max_manual_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        max_manual_entry = ttk.Entry(max_manual_frame, textvariable=self.var_max_manual_backups, width=7, font=scaled_font)
        max_manual_entry.pack(side=tk.LEFT, padx=(0,5))
        max_manual_long_text = ("Número máximo de copias de seguridad manuales a conservar (0 para desactivar y eliminar todas).\n"
                                "El límite se aplica cuando se crea una nueva copia manual; las más antiguas se eliminan automáticamente en ese momento.") # Clarified tooltip
        max_manual_short_text = "Máx. copias manuales (limpieza auto. en nueva creación)." # Clarified tooltip
        max_manual_help_btn = ttk.Button(max_manual_frame, text="?", width=3, style="Help.TButton",
                                         command=lambda: self._show_input_help("Ayuda: Máx. Copias Manuales", max_manual_long_text))
        max_manual_help_btn.pack(side=tk.LEFT)
        Tooltip(max_manual_help_btn, text=max_manual_long_text, short_text=max_manual_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        label_cooldown = ttk.Label(parent_frame, text="Enfriamiento copias automáticas (seg):", font=scaled_font)
        label_cooldown.grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        cooldown_frame = ttk.Frame(parent_frame)
        cooldown_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        cooldown_entry = ttk.Entry(cooldown_frame, textvariable=self.var_auto_backup_cooldown, width=7, font=scaled_font)
        cooldown_entry.pack(side=tk.LEFT, padx=(0,5))
        cooldown_long_text = "Tiempo mínimo (en segundos) que debe pasar después de una copia automática antes de que se pueda iniciar otra. 0 para permitir inmediatamente después de que termine la anterior (si no hay bloqueo)."
        cooldown_short_text = "Enfriamiento copias automáticas (seg)."
        cooldown_help_btn = ttk.Button(cooldown_frame, text="?", width=3, style="Help.TButton",
                                       command=lambda: self._show_input_help("Ayuda: Enfriamiento Copias Automáticas", cooldown_long_text))
        cooldown_help_btn.pack(side=tk.LEFT)
        Tooltip(cooldown_help_btn, text=cooldown_long_text, short_text=cooldown_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        manage_backups_frame = ttk.Frame(parent_frame)
        manage_backups_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10,5), sticky="w")
        manage_backups_button = ttk.Button(
            manage_backups_frame, 
            text="Gestionar Copias de Seguridad", 
            command=self.open_backup_restore_dialog, 
            style="Accent.TButton",
            font=get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale, weight="bold") # Set font in constructor
        )
        manage_backups_button.pack(side=tk.LEFT, padx=(0,5))
        # Removed: manage_backups_button.configure(font=...)

        manage_backups_long_text = "Abre una nueva ventana para crear, restaurar, renombrar y eliminar copias de seguridad manuales, y ver copias automáticas."
        manage_backups_short_text = "Gestionar copias de seguridad."
        manage_backups_help_btn = ttk.Button(manage_backups_frame, text="?", width=3, style="Help.TButton",
                                             command=lambda: self._show_input_help("Ayuda: Gestionar Copias de Seguridad", manage_backups_long_text))
        manage_backups_help_btn.pack(side=tk.LEFT)
        Tooltip(manage_backups_help_btn, text=manage_backups_long_text, short_text=manage_backups_short_text, enabled=self.settings.enable_hover_tooltips)

    def _create_advanced_tab_widgets(self, parent_frame: ttk.Frame):
        """Crea los widgets para la pestaña 'Avanzado'."""
        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
        parent_frame.columnconfigure(0, weight=1) # Allow labels/buttons to take space
        # No column 1 needed if elements span or are packed left
        row_idx = 0

        # --- Switch para mostrar/ocultar botón de Restauración de Fábrica ---
        show_factory_reset_frame = ttk.Frame(parent_frame)
        show_factory_reset_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10, 5), sticky="w")
        show_factory_reset_cb = ttk.Checkbutton(
            show_factory_reset_frame,
            text="Mostrar opción de Restauración de Fábrica (Avanzado)",
            variable=self.var_show_factory_reset,
            command=self._toggle_factory_reset_visibility
        )
        show_factory_reset_cb.pack(side=tk.LEFT, padx=(0,5))
        # Apply font to Checkbutton text
        # show_factory_reset_cb.configure(font=scaled_font) # Usually handled by style
        show_factory_reset_long_text = ("Activa o desactiva la visibilidad del botón 'Restaurar KineViz a Estado de Fábrica'.\n"
                                        "Esta opción es peligrosa y está oculta por defecto para prevenir borrados accidentales.")
        show_factory_reset_short_text = "Muestra/oculta botón de Restauración de Fábrica (Avanzado)."
        show_factory_reset_help_btn = ttk.Button(show_factory_reset_frame, text="?", width=3, style="Help.TButton",
                                                 command=lambda: self._show_input_help("Ayuda: Mostrar Restauración de Fábrica", show_factory_reset_long_text))
        show_factory_reset_help_btn.pack(side=tk.LEFT)
        Tooltip(show_factory_reset_help_btn, text=show_factory_reset_long_text, short_text=show_factory_reset_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        # --- Botón Restablecer Ajustes a Predeterminados ---
        reset_settings_frame = ttk.Frame(parent_frame)
        reset_settings_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10, 5), sticky="w")
        reset_settings_button = ttk.Button(reset_settings_frame, text="Restablecer Ajustes a Predeterminados", command=self.reset_config_settings_to_default_action)
        reset_settings_button.pack(side=tk.LEFT, padx=(0,5))
        reset_settings_button.configure(font=scaled_font) # Apply font
        reset_settings_long_text = ("Revierte todas las opciones de esta ventana (elementos por página, fuente, tema) "
                                    "a sus valores originales de fábrica.\n"
                                    "Esto NO afecta sus estudios ni datos guardados.\n"
                                    "Los cambios se aplicarán inmediatamente al archivo de configuración. "
                                    "Haga clic en 'Guardar' para cerrar este diálogo con los ajustes predeterminados aplicados, "
                                    "o 'Cancelar' para cerrar sin aplicar otros cambios que haya hecho manualmente antes de presionar este botón.")
        reset_settings_short_text = "Revierte ajustes de esta ventana a predeterminados (no afecta datos)."
        reset_settings_help_btn = ttk.Button(reset_settings_frame, text="?", width=3, style="Help.TButton",
                                             command=lambda: self._show_input_help("Ayuda: Restablecer Ajustes a Predeterminados", reset_settings_long_text))
        reset_settings_help_btn.pack(side=tk.LEFT)
        Tooltip(reset_settings_help_btn, text=reset_settings_long_text, short_text=reset_settings_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Botón Restaurar KineViz a Estado de Fábrica (visibilidad controlada) ---
        self.factory_reset_frame = ttk.Frame(parent_frame) 
        self.factory_reset_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10, 5), sticky="w")
        factory_reset_button = ttk.Button(
            self.factory_reset_frame, 
            text="Restaurar KineViz a Estado de Fábrica", 
            command=self.trigger_factory_reset_callback, 
            style="Danger.TButton",
            font=get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale, weight="bold") # Set font in constructor
        )
        factory_reset_button.pack(side=tk.LEFT, padx=(0,5))
        # Removed: factory_reset_button.configure(font=...)
        factory_reset_long_text = ("¡ADVERTENCIA! ESTA ACCIÓN ES IRREVERSIBLE.\n\n"
                                   "Restaurar KineViz a estado de fábrica eliminará TODA la información de la aplicación, incluyendo:\n"
                                   "- TODOS los estudios y sus archivos asociados.\n"
                                   "- TODOS los análisis guardados (discretos y continuos).\n"
                                   "- La base de datos completa de KineViz.\n"
                                   "- Todas las configuraciones personalizadas se revertirán a los valores iniciales.\n\n"
                                   "La aplicación podría requerir un reinicio después de esta operación.\n"
                                   "ÚSELA CON EXTREMA PRECAUCIÓN.")
        factory_reset_short_text = "¡PELIGRO! Elimina TODOS los datos y estudios. Irreversible."
        factory_reset_help_btn = ttk.Button(self.factory_reset_frame, text="?", width=3, style="Help.TButton",
                                            command=lambda: self._show_input_help("Ayuda: Restaurar KineViz a Estado de Fábrica", factory_reset_long_text))
        factory_reset_help_btn.pack(side=tk.LEFT)
        Tooltip(factory_reset_help_btn, text=factory_reset_long_text, short_text=factory_reset_short_text, enabled=self.settings.enable_hover_tooltips)
        # Ensure the factory reset button's visibility is correctly set initially
        self._toggle_factory_reset_visibility()


    def validate_input(self) -> bool:
        """Valida que los valores ingresados sean enteros positivos."""
        inputs_int = {
            "Estudios por página": self.var_studies_per_page.get(),
            "Archivos por página": self.var_files_per_page.get(),
            "Elementos por página (gestores análisis)": self.var_analysis_items_per_page.get(), # Changed label
            "Tablas resumen discreto por página": self.var_discrete_tables_per_page.get(), # New field
            "Máx. copias automáticas": self.var_max_auto_backups.get(),
            "Máx. copias manuales": self.var_max_manual_backups.get(),
            "Enfriamiento copias automáticas (seg)": self.var_auto_backup_cooldown.get()
        }
        for label, value_str in inputs_int.items():
            try:
                value_int = int(value_str)
                if value_int <= 0:
                    messagebox.showerror("Valor Inválido", f"'{label}' debe ser un número entero positivo.", parent=self)
                    return False
            except ValueError:
                messagebox.showerror("Valor Inválido", f"'{label}' debe ser un número entero válido.", parent=self)
                return False

        # Validar Escala de Fuente
        try:
            font_scale_val = float(self.var_font_scale.get())
            if font_scale_val <= 0:
                messagebox.showerror("Valor Inválido", "'Tamaño de Fuente (escala)' debe ser un número positivo.", parent=self)
                return False
        except ValueError:
            messagebox.showerror("Valor Inválido", "'Tamaño de Fuente (escala)' debe ser un número válido.", parent=self)
            return False
        
        # Tema no necesita validación si se usa Combobox con state="readonly"
        return True

    def save_settings(self):
        """Valida y guarda las configuraciones usando AppSettings."""
        if not self.validate_input():
            return

        try:
            # Actualizar el objeto settings en memoria
            self.settings.studies_per_page = int(self.var_studies_per_page.get())
            self.settings.files_per_page = int(self.var_files_per_page.get())
            self.settings.analysis_items_per_page = int(self.var_analysis_items_per_page.get()) # Renamed
            self.settings.discrete_tables_per_page = int(self.var_discrete_tables_per_page.get()) # Save new setting
            self.settings.font_scale = float(self.var_font_scale.get())
            self.settings.theme = self.var_theme.get()
            self.settings.show_factory_reset_button = self.var_show_factory_reset.get() # Save new setting
            self.settings.enable_hover_tooltips = self.var_enable_hover_tooltips.get() # Save new setting
            self.settings.max_automatic_backups = int(self.var_max_auto_backups.get())
            self.settings.max_manual_backups = int(self.var_max_manual_backups.get())
            self.settings.automatic_backup_cooldown_seconds = int(self.var_auto_backup_cooldown.get())

            # Guardar en el archivo config.ini
            self.settings.save_settings()
            messagebox.showinfo("Éxito", "Configuraciones guardadas correctamente.\nAlgunos cambios pueden requerir reiniciar la aplicación para verlos reflejados.", parent=self)
            self.destroy() # Cerrar diálogo después de guardar

        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudieron guardar las configuraciones:\n{e}", parent=self)

    def reset_config_settings_to_default_action(self):
        """
        Restablece los ajustes de configuración (solo los de este diálogo) a sus valores
        predeterminados y actualiza la UI del diálogo.
        Los cambios se guardan inmediatamente en config.ini.
        """
        if messagebox.askokcancel("Confirmar Restablecimiento de Ajustes",
                                 "¿Está seguro de que desea restablecer todos los ajustes de esta ventana a sus valores predeterminados?\n\n"
                                 "Esto afectará opciones como elementos por página, tamaño de fuente y tema. "
                                 "Sus estudios y datos no serán eliminados.",
                                 icon='question', parent=self):
            try:
                self.settings.reset_to_defaults() # Esto guarda en config.ini
                self.load_current_settings() # Recargar en la UI del diálogo
                self._toggle_factory_reset_visibility() # Actualizar visibilidad del botón de fábrica
                messagebox.showinfo("Ajustes Restablecidos",
                                    "Los ajustes de configuración han sido restablecidos a sus valores predeterminados y guardados.\n"
                                    "Puede cerrar este diálogo con 'Guardar' o 'Cancelar'.",
                                    parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron restablecer los ajustes:\n{e}", parent=self)

    def _toggle_factory_reset_visibility(self):
        """Muestra u oculta el frame del botón de restauración de fábrica."""
        if hasattr(self, 'factory_reset_frame'): # Ensure frame exists
            if self.var_show_factory_reset.get():
                self.factory_reset_frame.grid()
            else:
                self.factory_reset_frame.grid_remove()

    def open_backup_restore_dialog(self):
        """Abre el diálogo de gestión de copias de seguridad."""
        # Pass self.settings which is an AppSettings instance
        dialog = BackupRestoreDialog(self, app_settings=self.settings)
        # No wait_window here, as it's a top-level dialog that can be managed independently.
        # Or, if it should be modal to ConfigDialog:
        # self.wait_window(dialog) 

    def trigger_factory_reset_callback(self):
        """Llama al callback de reseteo de fábrica con doble confirmación."""
        if self.reset_callback:
            # Primera confirmación
            confirm1 = messagebox.askyesno(
                "Confirmar Restauración de Fábrica - Paso 1 de 2",
                "Está a punto de restaurar KineViz a su estado de fábrica.\n"
                "Esto eliminará TODOS los estudios, datos, análisis y configuraciones personalizadas.\n\n"
                "¿Está SEGURO de que desea continuar?",
                icon='warning', parent=self
            )
            if not confirm1:
                return

            # Segunda confirmación (más enfática)
            confirm2 = messagebox.askyesno(
                "Confirmar Restauración de Fábrica - Paso 2 de 2",
                "¡ADVERTENCIA FINAL!\n\n"
                "Esta acción es IRREVERSIBLE y borrará PERMANENTEMENTE toda la información de KineViz.\n"
                "TODOS LOS ESTUDIOS, ARCHIVOS, ANÁLISIS Y CONFIGURACIONES SERÁN ELIMINADOS.\n\n"
                "¿Está ABSOLUTAMENTE SEGURO de que desea proceder con la restauración completa a estado de fábrica?",
                icon='error', default=messagebox.NO, parent=self # Default a NO por seguridad
            )

            if confirm2:
                try:
                    self.reset_callback() # Llama a MainWindow.reset_to_defaults
                    # MainWindow.reset_to_defaults se encarga de mensajes y de cerrar/reiniciar la app si es necesario.
                    # El diálogo de configuración se cerrará si el reseteo es exitoso y la app se reinicia o va a landing.
                    self.destroy() # Cerrar este diálogo
                except Exception as e:
                     messagebox.showerror("Error Crítico", f"Ocurrió un error catastrófico durante la restauración de fábrica:\n{e}", parent=self)
        else:
            messagebox.showwarning("No Implementado", "La función de restauración de fábrica no está conectada.", parent=self)

# Para pruebas directas (si es necesario)
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw() # Ocultar ventana raíz

    # Crear instancia dummy de AppSettings
    dummy_settings = AppSettings(config_filename='config_test.ini') # Usar archivo de prueba

    def dummy_factory_reset():
        print("CALLBACK: Restauración de Fábrica llamada!")
        # Simular la lógica de MainWindow.reset_to_defaults
        # En una app real, esto eliminaría DB, archivos, etc.
        # Aquí, solo reseteamos los settings en AppSettings para la prueba del botón.
        dummy_settings.reset_to_defaults() # Esto ya resetea config.ini a los defaults de AppSettings
        messagebox.showinfo("Restauración Simulada", "Restauración de fábrica simulada.\nSettings de config.ini restablecidos.", parent=root)
        # En la app real, MainWindow podría cerrar y reiniciar o ir a landing page.


    dialog = ConfigDialog(root, dummy_settings, reset_callback=dummy_factory_reset)
    root.wait_window(dialog)

    # Verificar si los settings se guardaron (opcional)
    print("\nSettings después de cerrar diálogo:")
    print(f"Studies per page: {dummy_settings.studies_per_page}")
    print(f"Files per page: {dummy_settings.files_per_page}")
    print(f"PDFs per page: {dummy_settings.pdfs_per_page}")

    # Limpiar archivo de prueba
    if dummy_settings.config_path.exists():
         dummy_settings.config_path.unlink()

    root.destroy()
