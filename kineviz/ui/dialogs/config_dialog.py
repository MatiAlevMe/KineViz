import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, StringVar

# Importar AppSettings para type hinting
from kineviz.config.settings import AppSettings
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip
from kineviz.ui.dialogs.backup_restore_dialog import BackupRestoreDialog # Import new dialog
from kineviz.core import backup_manager # Import backup_manager module
from kineviz.utils import logger as logger_utils # Import the logger module for its functions
from kineviz.config.settings import AppSettings, VALID_LOG_LEVELS # Import VALID_LOG_LEVELS
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # For direct font scaling
import logging # Import logging
import os # For opening files
import sys # For platform check
import subprocess # For opening files
from pathlib import Path # For path operations, though settings.config_path is already a Path

logger = logging.getLogger(__name__) # Add logger for this module

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
        self.var_backups_per_page = StringVar() # New variable for backup pagination
        self.var_font_scale = StringVar()
        self.var_theme = StringVar()
        self.var_show_factory_reset = tk.BooleanVar() # New variable for the switch
        self.var_enable_hover_tooltips = tk.BooleanVar() # New variable for hover tooltips
        self.var_max_auto_backups = StringVar()
        self.var_max_manual_backups = StringVar()
        self.var_auto_backup_cooldown = StringVar()
        self.var_enable_automatic_backups = tk.BooleanVar()
        self.var_max_auto_backups = StringVar()
        self.var_auto_backup_cooldown = StringVar()

        # Pre-restore ("Respaldo") backup settings
        self.var_enable_pre_restore_backups = tk.BooleanVar()
        self.var_max_pre_restore_backups = StringVar()
        self.var_pre_restore_backup_cooldown = StringVar()

        # Manual backup settings
        self.var_enable_manual_backups = tk.BooleanVar()
        self.var_max_manual_backups = StringVar()
        
        self.var_show_advanced_backup_opts = tk.BooleanVar(value=False) # New, defaults to False, not loaded from settings

        # Undo Delete setting
        self.var_enable_undo_delete = tk.BooleanVar() # New for Undo Delete
        self.var_undo_cache_timeout_seconds = StringVar() # New for Undo Cache Timeout

        # Logging settings
        self.var_log_level = StringVar() # New for Log Level
        self.var_show_support_options = tk.BooleanVar() # New for toggling support/logging options

        # Calculate scaled font once for direct application
        self.scaled_font_tuple = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)

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
        self.var_backups_per_page.set(str(self.settings.backups_per_page)) # Load new setting
        self.var_font_scale.set(str(self.settings.font_scale))
        self.var_theme.set(self.settings.theme)
        self.var_show_factory_reset.set(self.settings.show_factory_reset_button) # Load new setting
        self.var_enable_hover_tooltips.set(self.settings.enable_hover_tooltips) # Load new setting
        self.var_max_auto_backups.set(str(self.settings.max_automatic_backups))
        self.var_max_manual_backups.set(str(self.settings.max_manual_backups))
        self.var_auto_backup_cooldown.set(str(self.settings.automatic_backup_cooldown_seconds))
        self.var_enable_automatic_backups.set(self.settings.enable_automatic_backups)
        self.var_max_auto_backups.set(str(self.settings.max_automatic_backups))
        self.var_auto_backup_cooldown.set(str(self.settings.automatic_backup_cooldown_seconds))

        self.var_enable_pre_restore_backups.set(self.settings.enable_pre_restore_backups)
        self.var_max_pre_restore_backups.set(str(self.settings.max_pre_restore_backups))
        self.var_pre_restore_backup_cooldown.set(str(self.settings.pre_restore_backup_cooldown_seconds))

        self.var_enable_manual_backups.set(self.settings.enable_manual_backups)
        self.var_max_manual_backups.set(str(self.settings.max_manual_backups))
        
        # self.var_show_advanced_backup_opts is not loaded from settings, defaults to False.
        self.var_enable_undo_delete.set(self.settings.enable_undo_delete) # Load Undo Delete setting
        self.var_undo_cache_timeout_seconds.set(str(self.settings.undo_cache_timeout_seconds)) # Load Undo Cache Timeout
        self.var_log_level.set(self.settings.log_level) # Load Log Level
        # self.var_show_support_options.set(False) # Default to hidden, or load from settings if persisted

    def create_widgets(self):
        """Crea los widgets del diálogo usando un Notebook para pestañas."""
        # Frame principal que contendrá el Notebook y los botones Guardar/Cancelar
        outer_frame = ttk.Frame(self, padding="10")
        outer_frame.pack(fill=tk.BOTH, expand=True)

        # Crear el Notebook
        notebook = ttk.Notebook(outer_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

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

        # --- Botones Guardar/Cancelar (fuera del Notebook) ---
        button_frame = ttk.Frame(outer_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10,0)) # Empaquetar al final
        
        # Centrar botones en el button_frame
        button_frame.columnconfigure(0, weight=1) # Columna vacía para empujar a la derecha
        button_frame.columnconfigure(1, weight=0) # Columna para Guardar
        button_frame.columnconfigure(2, weight=0) # Columna para Cancelar

        ttk.Button(button_frame, text="Guardar", style="Green.TButton", command=self.save_settings).grid(row=0, column=2, padx=5, sticky="e")
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).grid(row=0, column=1, padx=5, sticky="e")


        # After all widgets are created, set a minimum size based on font scale
        self.update_idletasks()
        # Calculate dynamic minsize
        base_min_width = 500
        base_min_height = 420 # Adjusted base height to accommodate more content potentially
        
        # Increase min_width slightly less aggressively than min_height with font_scale
        # Ensure font_scale is positive, default to 1.0 if not sensible
        current_font_scale = 1.0
        try:
            current_font_scale = float(self.var_font_scale.get())
            if current_font_scale <= 0: current_font_scale = 1.0
        except ValueError:
            pass # current_font_scale remains 1.0

        dynamic_min_width = int(base_min_width * (1 + (current_font_scale - 1) * 0.25)) # Scale width by 25% of scale delta
        dynamic_min_height = int(base_min_height * (1 + (current_font_scale - 1) * 0.5)) # Scale height by 50% of scale delta
        
        self.minsize(max(base_min_width, dynamic_min_width), max(base_min_height, dynamic_min_height))
        # self.geometry(f"{max(base_min_width, dynamic_min_width)}x{max(base_min_height, dynamic_min_height)}") # Optionally set initial geometry too

    def _create_general_tab_widgets(self, parent_frame: ttk.Frame):
        """Crea los widgets para la pestaña 'General'."""
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=3)
        row_idx = 0

        # --- Tamaño de Fuente ---
        ttk.Label(parent_frame, text="Tamaño de Fuente (escala):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        font_scale_frame = ttk.Frame(parent_frame)
        font_scale_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        font_scale_options = ["0.8", "0.9", "1.0", "1.1", "1.2", "1.3", "1.5", "1.75", "2.0"]
        font_scale_combo = ttk.Combobox(font_scale_frame, textvariable=self.var_font_scale, values=font_scale_options, state="readonly", font=self.scaled_font_tuple) # Added font
        font_scale_combo.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        font_scale_long_text = ("Ajusta el tamaño general del texto en la aplicación.\n"
                                "1.0 es el tamaño normal. Valores mayores agrandan el texto, menores lo achican.")
        font_scale_short_text = "Ajusta el tamaño del texto en la aplicación."
        font_scale_help_btn = ttk.Button(font_scale_frame, text="?", width=3, style="Help.TButton",
                                         command=lambda: self._show_input_help("Ayuda: Tamaño de Fuente", font_scale_long_text))
        font_scale_help_btn.pack(side=tk.LEFT)
        Tooltip(font_scale_help_btn, text=font_scale_long_text, short_text=font_scale_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Tema de Aplicación ---
        ttk.Label(parent_frame, text="Tema de Aplicación:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        theme_frame = ttk.Frame(parent_frame)
        theme_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        theme_options = ["Claro", "Oscuro"] # Changed theme names
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.var_theme, values=theme_options, state="readonly", font=self.scaled_font_tuple) # Added font
        theme_combo.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        theme_long_text = ("Cambia la apariencia visual de la aplicación (colores).\n"
                           "Claro: Tema claro (predeterminado).\n"
                           "Oscuro: Tema oscuro.")
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
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=3)
        row_idx = 0

        ttk.Label(parent_frame, text="Estudios por página:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        studies_frame = ttk.Frame(parent_frame)
        studies_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5) # Changed sticky to ew
        studies_entry = ttk.Entry(studies_frame, textvariable=self.var_studies_per_page, font=self.scaled_font_tuple) # Added font
        studies_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        studies_long_text = "Número de estudios a mostrar por página en la vista principal."
        studies_short_text = "Estudios por página."
        studies_help_btn = ttk.Button(studies_frame, text="?", width=3, style="Help.TButton",
                                      command=lambda: self._show_input_help("Ayuda: Estudios por Página", studies_long_text))
        studies_help_btn.pack(side=tk.LEFT)
        Tooltip(studies_help_btn, text=studies_long_text, short_text=studies_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        ttk.Label(parent_frame, text="Archivos por página (vista estudio):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        files_frame = ttk.Frame(parent_frame)
        files_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5) # Changed sticky to ew
        files_entry = ttk.Entry(files_frame, textvariable=self.var_files_per_page, font=self.scaled_font_tuple) # Added font
        files_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        files_long_text = "Número de archivos a mostrar por página en el navegador de archivos de la vista de estudio."
        files_short_text = "Archivos por página (vista estudio)."
        files_help_btn = ttk.Button(files_frame, text="?", width=3, style="Help.TButton",
                                    command=lambda: self._show_input_help("Ayuda: Archivos por Página", files_long_text))
        files_help_btn.pack(side=tk.LEFT)
        Tooltip(files_help_btn, text=files_long_text, short_text=files_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        ttk.Label(parent_frame, text="Tablas resumen discreto por página:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        discrete_tables_frame = ttk.Frame(parent_frame)
        discrete_tables_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5) # Changed sticky to ew
        discrete_tables_entry = ttk.Entry(discrete_tables_frame, textvariable=self.var_discrete_tables_per_page, font=self.scaled_font_tuple) # Added font
        discrete_tables_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        discrete_tables_long_text = "Número de tablas de resumen (ej. Maximo_Cinematica_...) a mostrar por página en la vista de 'Análisis Discreto'."
        discrete_tables_short_text = "Tablas resumen discreto por página."
        discrete_tables_help_btn = ttk.Button(discrete_tables_frame, text="?", width=3, style="Help.TButton",
                                              command=lambda: self._show_input_help("Ayuda: Tablas de Resumen Discreto por Página", discrete_tables_long_text))
        discrete_tables_help_btn.pack(side=tk.LEFT)
        Tooltip(discrete_tables_help_btn, text=discrete_tables_long_text, short_text=discrete_tables_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        ttk.Label(parent_frame, text="Elementos por página (gestores análisis):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        analysis_items_frame = ttk.Frame(parent_frame)
        analysis_items_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5) # Changed sticky to ew
        analysis_items_entry = ttk.Entry(analysis_items_frame, textvariable=self.var_analysis_items_per_page, font=self.scaled_font_tuple) # Added font
        analysis_items_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        analysis_items_long_text = "Número de elementos (análisis guardados) a mostrar por página en los gestores de análisis discreto y continuo."
        analysis_items_short_text = "Elementos por página (gestores análisis)."
        analysis_items_help_btn = ttk.Button(analysis_items_frame, text="?", width=3, style="Help.TButton",
                                             command=lambda: self._show_input_help("Ayuda: Elementos por Página (Gestores de Análisis)", analysis_items_long_text))
        analysis_items_help_btn.pack(side=tk.LEFT)
        Tooltip(analysis_items_help_btn, text=analysis_items_long_text, short_text=analysis_items_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx +=1 # Increment row_idx for the next item

        ttk.Label(parent_frame, text="Copias de seguridad por página:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        backups_page_frame = ttk.Frame(parent_frame)
        backups_page_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5) # Changed sticky to ew
        backups_page_entry = ttk.Entry(backups_page_frame, textvariable=self.var_backups_per_page, font=self.scaled_font_tuple) # Added font
        backups_page_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        backups_page_long_text = "Número de copias de seguridad a mostrar por página en el gestor de copias de seguridad."
        backups_page_short_text = "Copias de seguridad por página."
        backups_page_help_btn = ttk.Button(backups_page_frame, text="?", width=3, style="Help.TButton",
                                             command=lambda: self._show_input_help("Ayuda: Copias de Seguridad por Página", backups_page_long_text))
        backups_page_help_btn.pack(side=tk.LEFT)
        Tooltip(backups_page_help_btn, text=backups_page_long_text, short_text=backups_page_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx +=1 

        # Placeholder labels for testing dialog resizing (REMOVED)


    def _create_backups_tab_widgets(self, parent_frame: ttk.Frame):
        """Crea los widgets para la pestaña 'Copias de Seguridad'."""
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=3) # Column for entry fields
        row_idx = 0

        # --- SECTION: Automatic Backups ---
        auto_backup_enable_frame = ttk.Frame(parent_frame)
        auto_backup_enable_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=(5,0))
        auto_backup_cb = ttk.Checkbutton(
            auto_backup_enable_frame,
            text="Habilitar copias de seguridad automáticas",
            variable=self.var_enable_automatic_backups,
            command=self._toggle_backup_options_visibility
        )
        auto_backup_cb.pack(side=tk.LEFT, padx=(0,5))
        auto_backup_enable_long_text = "Activa o desactiva la creación automática de copias de seguridad en momentos clave (ej. antes de eliminaciones masivas)."
        auto_backup_enable_short_text = "Habilitar/deshabilitar copias automáticas."
        auto_backup_enable_help_btn = ttk.Button(auto_backup_enable_frame, text="?", width=3, style="Help.TButton",
                                                 command=lambda: self._show_input_help("Ayuda: Habilitar Copias Automáticas", auto_backup_enable_long_text))
        auto_backup_enable_help_btn.pack(side=tk.LEFT)
        Tooltip(auto_backup_enable_help_btn, text=auto_backup_enable_long_text, short_text=auto_backup_enable_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        self.max_auto_frame = ttk.Frame(parent_frame)
        self.max_auto_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=(20,5), pady=0) # Indent
        ttk.Label(self.max_auto_frame, text="Máx. copias automáticas:").pack(side=tk.LEFT, pady=5, padx=0)
        max_auto_entry_frame = ttk.Frame(self.max_auto_frame)
        max_auto_entry_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        max_auto_entry = ttk.Entry(max_auto_entry_frame, textvariable=self.var_max_auto_backups, font=self.scaled_font_tuple)
        max_auto_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        max_auto_long_text = ("Número máximo de copias de seguridad automáticas a conservar (debe ser > 0).\n"
                              "El límite se aplica cuando se crea una nueva copia automática; las más antiguas se eliminan.")
        max_auto_short_text = "Máx. copias automáticas (>0)."
        max_auto_help_btn = ttk.Button(max_auto_entry_frame, text="?", width=3, style="Help.TButton",
                                       command=lambda: self._show_input_help("Ayuda: Máx. Copias Automáticas", max_auto_long_text))
        max_auto_help_btn.pack(side=tk.LEFT)
        Tooltip(max_auto_help_btn, text=max_auto_long_text, short_text=max_auto_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        self.cooldown_auto_frame = ttk.Frame(parent_frame) # Renamed from self.cooldown_frame
        self.cooldown_auto_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=(20,5), pady=0) # Indent
        ttk.Label(self.cooldown_auto_frame, text="Enfriamiento copias automáticas (seg):").pack(side=tk.LEFT, pady=5, padx=0)
        cooldown_auto_entry_frame = ttk.Frame(self.cooldown_auto_frame)
        cooldown_auto_entry_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        cooldown_auto_entry = ttk.Entry(cooldown_auto_entry_frame, textvariable=self.var_auto_backup_cooldown, font=self.scaled_font_tuple)
        cooldown_auto_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        cooldown_auto_long_text = "Tiempo mínimo (en segundos, >=0) que debe pasar después de una copia automática antes de que se pueda iniciar otra."
        cooldown_auto_short_text = "Enfriamiento copias automáticas (seg, >=0)."
        cooldown_auto_help_btn = ttk.Button(cooldown_auto_entry_frame, text="?", width=3, style="Help.TButton",
                                       command=lambda: self._show_input_help("Ayuda: Enfriamiento Copias Automáticas", cooldown_auto_long_text))
        cooldown_auto_help_btn.pack(side=tk.LEFT)
        Tooltip(cooldown_auto_help_btn, text=cooldown_auto_long_text, short_text=cooldown_auto_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- SECTION: Pre-Restore ("Respaldo") Backups ---
        pre_restore_enable_frame = ttk.Frame(parent_frame)
        pre_restore_enable_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=(10,0)) # Add some top padding
        pre_restore_cb = ttk.Checkbutton(
            pre_restore_enable_frame,
            text="Habilitar copias de respaldo (pre-restauración)",
            variable=self.var_enable_pre_restore_backups,
            command=self._toggle_backup_options_visibility
        )
        pre_restore_cb.pack(side=tk.LEFT, padx=(0,5))
        pre_restore_enable_long_text = ("Si está activado, se creará una copia de seguridad tipo 'Respaldo' del estado actual del sistema\n"
                                        "justo antes de que se inicie una operación de restauración desde otra copia. Recomendado.")
        pre_restore_enable_short_text = "Habilitar/deshabilitar copias de respaldo pre-restauración."
        pre_restore_enable_help_btn = ttk.Button(pre_restore_enable_frame, text="?", width=3, style="Help.TButton",
                                                 command=lambda: self._show_input_help("Ayuda: Habilitar Copias de Respaldo", pre_restore_enable_long_text))
        pre_restore_enable_help_btn.pack(side=tk.LEFT)
        Tooltip(pre_restore_enable_help_btn, text=pre_restore_enable_long_text, short_text=pre_restore_enable_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        self.max_pre_restore_frame = ttk.Frame(parent_frame)
        self.max_pre_restore_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=(20,5), pady=0) # Indent
        ttk.Label(self.max_pre_restore_frame, text="Máx. copias de respaldo:").pack(side=tk.LEFT, pady=5, padx=0)
        max_pre_restore_entry_frame = ttk.Frame(self.max_pre_restore_frame)
        max_pre_restore_entry_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        max_pre_restore_entry = ttk.Entry(max_pre_restore_entry_frame, textvariable=self.var_max_pre_restore_backups, font=self.scaled_font_tuple)
        max_pre_restore_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        max_pre_restore_long_text = ("Número máximo de copias de seguridad tipo 'Respaldo' a conservar (debe ser >= 1).\n"
                                     "El límite se aplica cuando se crea una nueva copia de respaldo; las más antiguas se eliminan.")
        max_pre_restore_short_text = "Máx. copias de respaldo (>=1)."
        max_pre_restore_help_btn = ttk.Button(max_pre_restore_entry_frame, text="?", width=3, style="Help.TButton",
                                              command=lambda: self._show_input_help("Ayuda: Máx. Copias de Respaldo", max_pre_restore_long_text))
        max_pre_restore_help_btn.pack(side=tk.LEFT)
        Tooltip(max_pre_restore_help_btn, text=max_pre_restore_long_text, short_text=max_pre_restore_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        self.cooldown_pre_restore_frame = ttk.Frame(parent_frame)
        self.cooldown_pre_restore_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=(20,5), pady=0) # Indent
        ttk.Label(self.cooldown_pre_restore_frame, text="Enfriamiento copias de respaldo (seg):").pack(side=tk.LEFT, pady=5, padx=0)
        cooldown_pre_restore_entry_frame = ttk.Frame(self.cooldown_pre_restore_frame)
        cooldown_pre_restore_entry_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        cooldown_pre_restore_entry = ttk.Entry(cooldown_pre_restore_entry_frame, textvariable=self.var_pre_restore_backup_cooldown, font=self.scaled_font_tuple)
        cooldown_pre_restore_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        cooldown_pre_restore_long_text = "Tiempo mínimo (en segundos, >=0) que debe pasar después de una copia de respaldo antes de que se pueda iniciar otra."
        cooldown_pre_restore_short_text = "Enfriamiento copias de respaldo (seg, >=0)."
        cooldown_pre_restore_help_btn = ttk.Button(cooldown_pre_restore_entry_frame, text="?", width=3, style="Help.TButton",
                                                   command=lambda: self._show_input_help("Ayuda: Enfriamiento Copias de Respaldo", cooldown_pre_restore_long_text))
        cooldown_pre_restore_help_btn.pack(side=tk.LEFT)
        Tooltip(cooldown_pre_restore_help_btn, text=cooldown_pre_restore_long_text, short_text=cooldown_pre_restore_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        # --- SECTION: Manual Backups ---
        manual_backup_enable_frame = ttk.Frame(parent_frame)
        manual_backup_enable_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=(10,0)) # Add some top padding
        manual_backup_cb = ttk.Checkbutton(
            manual_backup_enable_frame,
            text="Habilitar copias de seguridad manuales",
            variable=self.var_enable_manual_backups,
            command=self._toggle_backup_options_visibility
        )
        manual_backup_cb.pack(side=tk.LEFT, padx=(0,5))
        manual_backup_enable_long_text = "Permite la creación y gestión manual de copias de seguridad."
        manual_backup_enable_short_text = "Habilitar/deshabilitar copias manuales."
        manual_backup_enable_help_btn = ttk.Button(manual_backup_enable_frame, text="?", width=3, style="Help.TButton",
                                                 command=lambda: self._show_input_help("Ayuda: Habilitar Copias Manuales", manual_backup_enable_long_text))
        manual_backup_enable_help_btn.pack(side=tk.LEFT)
        Tooltip(manual_backup_enable_help_btn, text=manual_backup_enable_long_text, short_text=manual_backup_enable_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        self.max_manual_frame = ttk.Frame(parent_frame)
        self.max_manual_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=(20,5), pady=0) # Indent
        ttk.Label(self.max_manual_frame, text="Máx. copias manuales:").pack(side=tk.LEFT, pady=5, padx=0)
        max_manual_entry_frame = ttk.Frame(self.max_manual_frame)
        max_manual_entry_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        max_manual_entry = ttk.Entry(max_manual_entry_frame, textvariable=self.var_max_manual_backups, font=self.scaled_font_tuple)
        max_manual_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        max_manual_long_text = ("Número máximo de copias de seguridad manuales a conservar (debe ser > 0).\n"
                                "Si se alcanza el límite, se impedirá crear nuevas copias hasta liberar espacio.")
        max_manual_short_text = "Máx. copias manuales (>0)."
        max_manual_help_btn = ttk.Button(max_manual_entry_frame, text="?", width=3, style="Help.TButton",
                                         command=lambda: self._show_input_help("Ayuda: Máx. Copias Manuales", max_manual_long_text))
        max_manual_help_btn.pack(side=tk.LEFT)
        Tooltip(max_manual_help_btn, text=max_manual_long_text, short_text=max_manual_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        # --- SECTION: Manage Backups Button ---
        self.manage_backups_frame = ttk.Frame(parent_frame)
        self.manage_backups_frame.grid(row=row_idx, column=0, columnspan=2, pady=(15,5), sticky="w") # Added more top padding
        manage_backups_button = ttk.Button(self.manage_backups_frame, text="Gestionar Copias de Seguridad", command=self.open_backup_restore_dialog, style="Green.TButton")
        manage_backups_button.pack(side=tk.LEFT, padx=(0,5))
        manage_backups_long_text = "Abre una nueva ventana para crear, restaurar y gestionar copias de seguridad."
        manage_backups_short_text = "Gestionar copias de seguridad."
        manage_backups_help_btn = ttk.Button(self.manage_backups_frame, text="?", width=3, style="Help.TButton",
                                             command=lambda: self._show_input_help("Ayuda: Gestionar Copias de Seguridad", manage_backups_long_text))
        manage_backups_help_btn.pack(side=tk.LEFT)
        Tooltip(manage_backups_help_btn, text=manage_backups_long_text, short_text=manage_backups_short_text, enabled=self.settings.enable_hover_tooltips)

        # Call to set initial visibility
        self._toggle_backup_options_visibility()


    def _toggle_backup_options_visibility(self, event=None):
        """Muestra u oculta las opciones de backup según los checkboxes de habilitación."""
        show_auto_options = self.var_enable_automatic_backups.get()
        show_pre_restore_options = self.var_enable_pre_restore_backups.get()
        show_manual_options = self.var_enable_manual_backups.get()

        # Automatic backup options
        if hasattr(self, 'max_auto_frame'):
            if show_auto_options: self.max_auto_frame.grid()
            else: self.max_auto_frame.grid_remove()
        
        if hasattr(self, 'cooldown_auto_frame'): # Renamed from cooldown_frame
            if show_auto_options: self.cooldown_auto_frame.grid()
            else: self.cooldown_auto_frame.grid_remove()

        # Pre-restore backup options
        if hasattr(self, 'max_pre_restore_frame'):
            if show_pre_restore_options: self.max_pre_restore_frame.grid()
            else: self.max_pre_restore_frame.grid_remove()

        if hasattr(self, 'cooldown_pre_restore_frame'):
            if show_pre_restore_options: self.cooldown_pre_restore_frame.grid()
            else: self.cooldown_pre_restore_frame.grid_remove()
        
        # Manual backup options
        if hasattr(self, 'max_manual_frame'):
            if show_manual_options: self.max_manual_frame.grid()
            else: self.max_manual_frame.grid_remove()
        
        # Manage backups button
        if hasattr(self, 'manage_backups_frame'):
            if show_auto_options or show_pre_restore_options or show_manual_options:
                self.manage_backups_frame.grid()
            else:
                self.manage_backups_frame.grid_remove()


    def _create_advanced_tab_widgets(self, parent_frame: ttk.Frame):
        """Crea los widgets para la pestaña 'Avanzado'."""
        # Main frame for the tab, allows canvas and scrollbar to fill
        tab_content_frame = ttk.Frame(parent_frame)
        tab_content_frame.pack(fill=tk.BOTH, expand=True)
        tab_content_frame.columnconfigure(0, weight=1) # Canvas column
        tab_content_frame.rowconfigure(0, weight=1) # Canvas row

        # Create a canvas
        canvas = tk.Canvas(tab_content_frame, highlightthickness=0) # Use tk.Canvas for better scrollbar integration
        canvas.grid(row=0, column=0, sticky="nsew")

        # Create a vertical scrollbar
        scrollbar = ttk.Scrollbar(tab_content_frame, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create a frame inside the canvas to hold the content
        scrollable_frame = ttk.Frame(canvas, padding="10") # Add padding to the scrollable content
        scrollable_frame.columnconfigure(0, weight=1) # Allow labels/buttons to take space
        scrollable_frame.columnconfigure(1, weight=0) # For help buttons, fixed width

        # Add the scrollable frame to a window in the canvas
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event=None):
            canvas_width = event.width
            canvas.itemconfig(canvas.create_window((0,0), window=scrollable_frame, anchor='nw'), width=canvas_width)

        scrollable_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind('<Configure>', _on_canvas_configure)


        row_idx = 0

        # --- Switch para mostrar opciones de Soporte Técnico (Logging) ---
        show_support_opts_frame = ttk.Frame(scrollable_frame) # Changed parent_frame to scrollable_frame
        show_support_opts_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10,5), sticky="w")
        show_support_opts_cb = ttk.Checkbutton(
            show_support_opts_frame,
            text="Mostrar opciones avanzadas de soporte técnico",
            variable=self.var_show_support_options,
            command=self._toggle_support_options_visibility
        )
        show_support_opts_cb.pack(side=tk.LEFT, padx=(0,5))
        show_support_opts_long_text = "Muestra opciones avanzadas relacionadas con la generación de logs y diagnóstico, útiles para soporte técnico."
        show_support_opts_short_text = "Opciones de logging y diagnóstico."
        show_support_opts_help_btn = ttk.Button(show_support_opts_frame, text="?", width=3, style="Help.TButton",
                                            command=lambda: self._show_input_help("Ayuda: Opciones de Soporte Técnico", show_support_opts_long_text))
        show_support_opts_help_btn.pack(side=tk.LEFT)
        Tooltip(show_support_opts_help_btn, text=show_support_opts_long_text, short_text=show_support_opts_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Log Level (conditionally visible) ---
        self.log_level_outer_frame = ttk.Frame(scrollable_frame) # Outer frame for visibility control
        self.log_level_outer_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=(0,5), padx=(20,0)) # Indent
        
        ttk.Label(self.log_level_outer_frame, text="Nivel de logging:").grid(row=0, column=0, sticky="w", padx=(0,5), pady=2)
        
        log_level_combo_frame = ttk.Frame(self.log_level_outer_frame) # Frame for combobox and help button
        log_level_combo_frame.grid(row=0, column=1, sticky="ew", padx=(0,5), pady=2)
        log_level_combo_frame.columnconfigure(0, weight=1) # Combobox expands

        log_level_combo = ttk.Combobox(log_level_combo_frame, textvariable=self.var_log_level, values=VALID_LOG_LEVELS, state="readonly", font=self.scaled_font_tuple)
        log_level_combo.grid(row=0, column=0, sticky="ew", padx=(0,5))
        
        log_level_long_text = (
            "Establece el nivel de detalle de los mensajes guardados en los archivos de log.\n"
            "DEBUG: Muy detallado, útil para desarrolladores o para reportar errores complejos.\n"
            "INFO: Información general sobre el funcionamiento.\n"
            "WARNING: Advertencias sobre posibles problemas (predeterminado).\n"
            "ERROR: Solo errores críticos.\n\n"
            "Cambiar esta opción requiere reiniciar la aplicación para que tenga efecto."
        )
        log_level_short_text = "Nivel de detalle de los logs (requiere reinicio)."
        log_level_help_btn = ttk.Button(log_level_combo_frame, text="?", width=3, style="Help.TButton",
                                        command=lambda: self._show_input_help("Ayuda: Nivel de Logging", log_level_long_text))
        log_level_help_btn.grid(row=0, column=1, sticky="e", padx=(0,0))
        Tooltip(log_level_help_btn, text=log_level_long_text, short_text=log_level_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Open Logs Folder Button (conditionally visible) ---
        self.open_logs_button_frame = ttk.Frame(scrollable_frame) # Outer frame for visibility
        self.open_logs_button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=(5,0), padx=(20,0)) # Indent
        # self.open_logs_button_frame.columnconfigure(0, weight=1) # Removed to prevent button expansion

        open_logs_btn = ttk.Button(self.open_logs_button_frame, text="Abrir carpeta de logs", command=logger_utils.open_logs_folder)
        open_logs_btn.grid(row=0, column=0, sticky="w", padx=(0,5), pady=2) # Changed sticky to "w"
        open_logs_long_text = "Abre la carpeta donde se guardan los archivos de log de KineViz. Estos archivos son útiles para diagnosticar problemas."
        open_logs_short_text = "Abrir carpeta de logs."
        open_logs_help_btn = ttk.Button(self.open_logs_button_frame, text="?", width=3, style="Help.TButton",
                                        command=lambda: self._show_input_help("Ayuda: Abrir Carpeta de Logs", open_logs_long_text))
        open_logs_help_btn.grid(row=0, column=1, sticky="e", padx=(0,5), pady=2)
        Tooltip(open_logs_help_btn, text=open_logs_long_text, short_text=open_logs_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Export Logs Button (conditionally visible) ---
        self.export_logs_button_frame = ttk.Frame(scrollable_frame) # Outer frame for visibility
        self.export_logs_button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=(5,5), padx=(20,0)) # Indent, reduced bottom padding
        # self.export_logs_button_frame.columnconfigure(0, weight=1) # Removed to prevent button expansion

        export_logs_btn = ttk.Button(self.export_logs_button_frame, text="Exportar logs...", command=lambda: logger_utils.export_logs(self))
        export_logs_btn.grid(row=0, column=0, sticky="w", padx=(0,5), pady=2) # Changed sticky to "w"
        export_logs_long_text = "Comprime la carpeta de logs en un archivo .zip. Esto es útil para enviar los logs al equipo de soporte si se encuentra un problema."
        export_logs_short_text = "Exportar logs como .zip."
        export_logs_help_btn = ttk.Button(self.export_logs_button_frame, text="?", width=3, style="Help.TButton",
                                          command=lambda: self._show_input_help("Ayuda: Exportar Logs", export_logs_long_text))
        export_logs_help_btn.grid(row=0, column=1, sticky="e", padx=(0,5), pady=2)
        Tooltip(export_logs_help_btn, text=export_logs_long_text, short_text=export_logs_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Open config.ini Button (conditionally visible) ---
        self.open_config_button_frame = ttk.Frame(scrollable_frame) # Outer frame for visibility
        self.open_config_button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=(5,10), padx=(20,0)) # Indent, add bottom padding

        open_config_btn = ttk.Button(self.open_config_button_frame, text="Abrir config.ini", command=self._open_config_ini_action)
        open_config_btn.grid(row=0, column=0, sticky="w", padx=(0,5), pady=2)
        open_config_long_text = "Abre el archivo de configuración 'config.ini' en el editor de texto predeterminado. Útil para diagnóstico."
        open_config_short_text = "Abrir config.ini."
        open_config_help_btn = ttk.Button(self.open_config_button_frame, text="?", width=3, style="Help.TButton",
                                          command=lambda: self._show_input_help("Ayuda: Abrir config.ini", open_config_long_text))
        open_config_help_btn.grid(row=0, column=1, sticky="e", padx=(0,5), pady=2)
        Tooltip(open_config_help_btn, text=open_config_long_text, short_text=open_config_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        # --- Switch para mostrar opciones avanzadas de backup ---
        show_adv_backup_frame = ttk.Frame(scrollable_frame) # Changed parent_frame to scrollable_frame
        show_adv_backup_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10,5), sticky="w")
        show_adv_backup_cb = ttk.Checkbutton(
            show_adv_backup_frame,
            text="Mostrar opciones avanzadas de copias de seguridad",
            variable=self.var_show_advanced_backup_opts,
            command=self._toggle_advanced_backup_options_visibility
        )
        show_adv_backup_cb.pack(side=tk.LEFT, padx=(0,5))
        show_adv_backup_long_text = "Muestra opciones adicionales para la gestión de copias de seguridad, como la limpieza de archivos .bak."
        show_adv_backup_short_text = "Opciones avanzadas de backup."
        show_adv_backup_help_btn = ttk.Button(show_adv_backup_frame, text="?", width=3, style="Help.TButton",
                                            command=lambda: self._show_input_help("Ayuda: Opciones Avanzadas de Backup", show_adv_backup_long_text))
        show_adv_backup_help_btn.pack(side=tk.LEFT)
        Tooltip(show_adv_backup_help_btn, text=show_adv_backup_long_text, short_text=show_adv_backup_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Botón Limpiar Archivos .bak (visibilidad controlada) ---
        self.clean_bak_files_frame = ttk.Frame(scrollable_frame) # Changed parent_frame to scrollable_frame
        self.clean_bak_files_frame.grid(row=row_idx, column=0, columnspan=2, pady=(0,10), sticky="ew", padx=(20,0)) # Indent, remove top padding, add bottom
        # self.clean_bak_files_frame.columnconfigure(0, weight=1) # Removed to prevent button expansion

        clean_bak_button = ttk.Button(self.clean_bak_files_frame, text="Limpiar archivos .bak residuales", command=self._clean_bak_files_action)
        clean_bak_button.grid(row=0, column=0, sticky="w", padx=(0,5), pady=2) # Changed sticky to "w"
        clean_bak_long_text = ("Elimina los archivos y carpetas con extensión '.bak' de la raíz del proyecto.\n"
                            "Estos archivos se crean como medida de seguridad durante las restauraciones.\n"
                            "Es seguro eliminarlos si la aplicación funciona correctamente y no necesita revertir una restauración fallida.")
        clean_bak_short_text = "Eliminar archivos .bak."
        clean_bak_help_btn = ttk.Button(self.clean_bak_files_frame, text="?", width=3, style="Help.TButton",
                                        command=lambda: self._show_input_help("Ayuda: Limpiar Archivos .bak", clean_bak_long_text))
        clean_bak_help_btn.grid(row=0, column=1, sticky="e", padx=(0,5), pady=2)
        Tooltip(clean_bak_help_btn, text=clean_bak_long_text, short_text=clean_bak_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Botón Limpiar Caché de Deshacer (visibilidad controlada) ---
        self.clear_undo_cache_frame = ttk.Frame(scrollable_frame) # Changed parent_frame to scrollable_frame
        self.clear_undo_cache_frame.grid(row=row_idx, column=0, columnspan=2, pady=(0,10), sticky="ew", padx=(20,0)) # Indent

        clear_undo_cache_button = ttk.Button(self.clear_undo_cache_frame, text="Limpiar caché de deshacer", command=self._clear_undo_cache_action)
        clear_undo_cache_button.grid(row=0, column=0, sticky="w", padx=(0,5), pady=2)
        clear_undo_cache_long_text = ("Elimina el contenido de la carpeta de caché de 'Deshacer Eliminación'.\n"
                                      "Esto borrará cualquier estado guardado para deshacer la última operación de eliminación.\n"
                                      "Es seguro hacerlo si no necesita deshacer ninguna acción reciente o si desea liberar espacio.")
        clear_undo_cache_short_text = "Eliminar caché de deshacer."
        clear_undo_cache_help_btn = ttk.Button(self.clear_undo_cache_frame, text="?", width=3, style="Help.TButton",
                                               command=lambda: self._show_input_help("Ayuda: Limpiar Caché de Deshacer", clear_undo_cache_long_text))
        clear_undo_cache_help_btn.grid(row=0, column=1, sticky="e", padx=(0,5), pady=2)
        Tooltip(clear_undo_cache_help_btn, text=clear_undo_cache_long_text, short_text=clear_undo_cache_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Botón Abrir Carpeta Caché de Deshacer (visibilidad controlada) ---
        self.open_undo_cache_dir_frame = ttk.Frame(scrollable_frame) # Changed parent_frame to scrollable_frame
        self.open_undo_cache_dir_frame.grid(row=row_idx, column=0, columnspan=2, pady=(0,10), sticky="ew", padx=(20,0)) # Indent

        open_undo_cache_dir_button = ttk.Button(self.open_undo_cache_dir_frame, text="Abrir carpeta de caché de deshacer", command=self._open_undo_cache_dir_action)
        open_undo_cache_dir_button.grid(row=0, column=0, sticky="w", padx=(0,5), pady=2)
        open_undo_cache_dir_long_text = "Abre la carpeta donde se almacenan temporalmente los datos para la función 'Deshacer Eliminación'."
        open_undo_cache_dir_short_text = "Abrir carpeta de caché de Deshacer."
        open_undo_cache_dir_help_btn = ttk.Button(self.open_undo_cache_dir_frame, text="?", width=3, style="Help.TButton",
                                               command=lambda: self._show_input_help("Ayuda: Abrir Carpeta Caché de Deshacer", open_undo_cache_dir_long_text))
        open_undo_cache_dir_help_btn.grid(row=0, column=1, sticky="e", padx=(0,5), pady=2)
        Tooltip(open_undo_cache_dir_help_btn, text=open_undo_cache_dir_long_text, short_text=open_undo_cache_dir_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        # --- Switch para habilitar/deshabilitar Deshacer Eliminación ---
        enable_undo_delete_frame = ttk.Frame(scrollable_frame) # Changed parent_frame to scrollable_frame
        enable_undo_delete_frame.grid(row=row_idx, column=0, columnspan=2, pady=(5, 5), sticky="w") # Adjusted padding
        enable_undo_delete_cb = ttk.Checkbutton(
            enable_undo_delete_frame,
            text="Habilitar 'deshacer eliminación' (experimental)",
            variable=self.var_enable_undo_delete,
            command=self._toggle_undo_options_visibility # Add command
        )
        enable_undo_delete_cb.pack(side=tk.LEFT, padx=(0, 5))
        enable_undo_delete_long_text = (
            "Permite deshacer la última operación de eliminación de estudios, archivos o resultados de análisis.\n"
            "La opción 'Deshacer' aparecerá en el menú 'Editar' si está habilitada y hay una operación para deshacer.\n"
            "La información para deshacer se guarda en una caché temporal. Esta caché se limpia automáticamente:\n"
            "1. Al iniciar una nueva operación que pueda ser deshecha (ej. otra eliminación).\n"
            "2. Si el 'Timeout caché deshacer' está configurado (>0) y el tiempo ha expirado al iniciar la aplicación.\n"
            "La caché se limpia al reabrir KineViz luego de que el timeout se cumpla.\n"
            "Esta función es experimental. Úsela con precaución.\n\n"
            "Nota: La preparación para una *nueva* operación de 'Deshacer' puede requerir un reinicio de la aplicación (o tiempo de espera en la aplicación) después de un uso previo o cambio de esta configuración."
        )
        enable_undo_delete_short_text = "Habilita/deshabilita la función 'Deshacer Eliminación'."
        enable_undo_delete_help_btn = ttk.Button(
            enable_undo_delete_frame, text="?", width=3, style="Help.TButton",
            command=lambda: self._show_input_help("Ayuda: Deshacer Eliminación", enable_undo_delete_long_text)
        )
        enable_undo_delete_help_btn.pack(side=tk.LEFT)
        Tooltip(enable_undo_delete_help_btn, text=enable_undo_delete_long_text, short_text=enable_undo_delete_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Timeout para Caché de Deshacer ---
        self.undo_timeout_frame = ttk.Frame(scrollable_frame) # Store frame for visibility toggle
        self.undo_timeout_frame.grid(row=row_idx, column=0, columnspan=2, pady=(0, 5), padx=(20,0), sticky="w") # Indent
        
        ttk.Label(self.undo_timeout_frame, text="Timeout caché deshacer (seg):").pack(side=tk.LEFT, padx=(0,5))
        
        undo_timeout_entry_frame = ttk.Frame(self.undo_timeout_frame)
        undo_timeout_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        undo_timeout_entry = ttk.Entry(undo_timeout_entry_frame, textvariable=self.var_undo_cache_timeout_seconds, font=self.scaled_font_tuple)
        undo_timeout_entry.pack(side=tk.LEFT, padx=(0,5), fill=tk.X, expand=True)
        
        undo_timeout_long_text = (
            "Tiempo en segundos para que la caché de 'Deshacer Eliminación' se considere expirada.\n"
            "Si la caché ha expirado al iniciar la aplicación, la opción 'Deshacer' para la sesión anterior no estará disponible.\n"
            "Un valor de 0 deshabilita este chequeo por timeout (la caché solo se borrará al preparar una nueva operación de deshacer).\n"
            "Recomendado: 60-300 segundos."
        )
        undo_timeout_short_text = "Timeout para caché de deshacer (seg, 0=sin chequeo por timeout)."
        undo_timeout_help_btn = ttk.Button(
            undo_timeout_entry_frame, text="?", width=3, style="Help.TButton",
            command=lambda: self._show_input_help("Ayuda: Timeout Caché Deshacer", undo_timeout_long_text)
        )
        undo_timeout_help_btn.pack(side=tk.LEFT)
        Tooltip(undo_timeout_help_btn, text=undo_timeout_long_text, short_text=undo_timeout_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        # --- Switch para mostrar/ocultar botón de Restauración de Fábrica --- (NUEVO ORDEN: DESPUÉS DE BACKUP)
        show_factory_reset_frame = ttk.Frame(scrollable_frame) # Changed parent_frame to scrollable_frame
        show_factory_reset_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10,5), sticky="w")
        show_factory_reset_cb = ttk.Checkbutton(
            show_factory_reset_frame,
            text="Mostrar opción de restauración de fábrica (avanzado)",
            variable=self.var_show_factory_reset,
            command=self._toggle_factory_reset_visibility
        )
        show_factory_reset_cb.pack(side=tk.LEFT, padx=(0,5))
        show_factory_reset_long_text = ("Activa o desactiva la visibilidad del botón 'Restaurar KineViz a Estado de Fábrica'.\n"
                                        "Esta opción es peligrosa y está oculta por defecto para prevenir borrados accidentales.")
        show_factory_reset_short_text = "Muestra/oculta botón de Restauración de Fábrica (Avanzado)."
        show_factory_reset_help_btn = ttk.Button(show_factory_reset_frame, text="?", width=3, style="Help.TButton",
                                                command=lambda: self._show_input_help("Ayuda: Mostrar Restauración de Fábrica", show_factory_reset_long_text))
        show_factory_reset_help_btn.pack(side=tk.LEFT)
        Tooltip(show_factory_reset_help_btn, text=show_factory_reset_long_text, short_text=show_factory_reset_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1
        
        # --- Botón Restablecer Ajustes a Predeterminados --- (NUEVO ORDEN: DESPUÉS DE MOSTRAR OPCIÓN)
        reset_settings_frame = ttk.Frame(scrollable_frame) # Changed parent_frame to scrollable_frame
        reset_settings_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10,5), sticky="w")
        reset_settings_button = ttk.Button(reset_settings_frame, text="Restablecer Ajustes a Predeterminados", command=self.reset_config_settings_to_default_action)
        reset_settings_button.pack(side=tk.LEFT, padx=(0,5))
        reset_settings_long_text = ("Revierte todas las configuraciones de la aplicación (opciones en todas las pestañas de esta ventana) "
                                    "a sus valores originales de fábrica.\n"
                                    "Esto NO afecta sus estudios, archivos, análisis ni copias de seguridad guardadas.\n"
                                    "Los cambios se aplicarán inmediatamente y el diálogo se cerrará.")
        reset_settings_short_text = "Revierte ajustes de la aplicación a predeterminados (no afecta datos)."
        reset_settings_help_btn = ttk.Button(reset_settings_frame, text="?", width=3, style="Help.TButton",
                                            command=lambda: self._show_input_help("Ayuda: Restablecer Ajustes a Predeterminados", reset_settings_long_text))
        reset_settings_help_btn.pack(side=tk.LEFT)
        Tooltip(reset_settings_help_btn, text=reset_settings_long_text, short_text=reset_settings_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Botón Restaurar KineViz a Estado de Fábrica (visibilidad controlada) ---
        self.factory_reset_frame = ttk.Frame(scrollable_frame)  # Changed parent_frame to scrollable_frame
        self.factory_reset_frame.grid(row=row_idx, column=0, columnspan=2, pady=(10,5), sticky="w")
        factory_reset_button = ttk.Button(self.factory_reset_frame, text="Restaurar KineViz a Estado de Fábrica", command=self.trigger_factory_reset_callback, style="Danger.TButton")
        factory_reset_button.pack(side=tk.LEFT, padx=(0,5))
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
        row_idx += 1

        # Ensure initial visibility is set
        self._toggle_support_options_visibility() # New call
        self._toggle_advanced_backup_options_visibility()
        self._toggle_undo_options_visibility()
        self._toggle_factory_reset_visibility()


    def _toggle_support_options_visibility(self, event=None):
        """Muestra u oculta las opciones de Soporte Técnico (Logging)."""
        show = self.var_show_support_options.get()
        widgets_to_toggle = [
            getattr(self, 'log_level_outer_frame', None),
            getattr(self, 'open_logs_button_frame', None),
            getattr(self, 'export_logs_button_frame', None),
            getattr(self, 'open_config_button_frame', None) # Add new frame here
        ]
        for widget in widgets_to_toggle:
            if widget: # Check if attribute exists
                if show:
                    widget.grid()
                else:
                    widget.grid_remove()

    def _toggle_advanced_backup_options_visibility(self, event=None):
        """Muestra u oculta las opciones avanzadas de backup."""
        show = self.var_show_advanced_backup_opts.get()
        widgets_to_toggle = [
            getattr(self, 'clean_bak_files_frame', None),
            getattr(self, 'clear_undo_cache_frame', None),
            getattr(self, 'open_undo_cache_dir_frame', None) # Add new frame here
        ]
        for widget in widgets_to_toggle:
            if widget: # Check if attribute exists
                if show:
                    widget.grid()
                else:
                    widget.grid_remove()

    def _toggle_undo_options_visibility(self, event=None):
        """Muestra u oculta las opciones de Deshacer Eliminación según el checkbox de habilitación."""
        if hasattr(self, 'undo_timeout_frame'):
            if self.var_enable_undo_delete.get():
                self.undo_timeout_frame.grid()
            else:
                self.undo_timeout_frame.grid_remove()
    
    def _clean_bak_files_action(self):
        """Acción para limpiar archivos .bak con doble confirmación."""
        # Primera confirmación
        confirm1 = messagebox.askokcancel(
            "Confirmar Limpieza - Paso 1 de 2",
            "¿Está seguro de que desea eliminar todos los archivos y carpetas '.bak' de la raíz del proyecto?\n\n"
            "Esta acción no se puede deshacer.",
            icon='warning', 
            parent=self
        )
        
        if not confirm1:
            return
        
        # Segunda confirmación (más enfática)
        confirm2 = messagebox.askokcancel(
            "Confirmar Limpieza - Paso 2 de 2",
            "¡ADVERTENCIA FINAL!\n\n"
            "Está a punto de eliminar permanentemente todos los archivos de respaldo (.bak).\n"
            "Esta acción es IRREVERSIBLE y podría afectar su capacidad para restaurar datos.\n\n"
            "¿Está ABSOLUTAMENTE SEGURO de que desea proceder con la limpieza?",
            icon='error',
            parent=self
        )
        
        if confirm2:    
            try:
                # This method will need to be added to backup_manager
                deleted_count, error_count = backup_manager.cleanup_bak_files() 
                if error_count > 0:
                    messagebox.showwarning("Limpieza Parcial", 
                                           f"Se eliminaron {deleted_count} archivos/carpetas .bak.\n"
                                           f"No se pudieron eliminar {error_count} elementos (ver logs).", 
                                           parent=self)
                elif deleted_count > 0:
                    messagebox.showinfo("Limpieza Completada", f"Se eliminaron {deleted_count} archivos/carpetas .bak.", parent=self)
                else:
                    messagebox.showinfo("Limpieza Completada", "No se encontraron archivos .bak para eliminar.", parent=self)
            except Exception as e:
                logger.error(f"Error durante la limpieza de archivos .bak: {e}", exc_info=True)
                messagebox.showerror("Error", f"Ocurrió un error al limpiar los archivos .bak:\n{e}", parent=self)

    def _open_config_ini_action(self):
        """Abre el archivo config.ini con la aplicación predeterminada."""
        config_file_path = self.settings.config_path
        if not config_file_path.exists():
            messagebox.showerror("Error", f"El archivo de configuración no se encontró en:\n{config_file_path}", parent=self)
            logger.error(f"Archivo config.ini no encontrado en {config_file_path}")
            return

        try:
            logger.info(f"Intentando abrir archivo config.ini: {config_file_path}")
            if sys.platform == "win32":
                os.startfile(config_file_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", config_file_path], check=True)
            else:  # linux variants
                subprocess.run(["xdg-open", config_file_path], check=True)
        except FileNotFoundError:
             messagebox.showerror("Error", f"No se pudo encontrar el archivo config.ini:\n'{config_file_path}'", parent=self)
             logger.error(f"Archivo config.ini no encontrado al intentar abrir: {config_file_path}", exc_info=True)
        except PermissionError:
             messagebox.showerror("Error", f"No tiene permisos para acceder al archivo config.ini:\n'{config_file_path}'", parent=self)
             logger.error(f"Permiso denegado al abrir config.ini: {config_file_path}", exc_info=True)
        except subprocess.CalledProcessError as e:
             logger.error(f"Comando para abrir config.ini {config_file_path} falló: {e}", exc_info=True)
             messagebox.showerror("Error", f"El comando para abrir config.ini falló:\n{e}", parent=self)
        except Exception as e:
            logger.error(f"Error inesperado al abrir config.ini {config_file_path}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir config.ini '{config_file_path}':\n{str(e)}", parent=self)

    def _clear_undo_cache_action(self):
        """Acción para limpiar la caché de Deshacer con doble confirmación."""
        # Primera confirmación
        confirm1 = messagebox.askokcancel(
            "Confirmar Limpieza de Caché - Paso 1 de 2",
            "¿Está seguro de que desea eliminar el contenido de la caché de 'Deshacer Eliminación'?\n\n"
            "Esta acción borrará cualquier estado guardado para deshacer la última operación de eliminación.",
            icon='warning',
            parent=self
        )
        if not confirm1:
            return

        # Segunda confirmación (más enfática)
        confirm2 = messagebox.askokcancel(
            "Confirmar Limpieza de Caché - Paso 2 de 2",
            "¡ADVERTENCIA FINAL!\n\n"
            "Está a punto de eliminar permanentemente el contenido de la caché de 'Deshacer Eliminación'.\n"
            "Esta acción es IRREVERSIBLE y podría afectar su capacidad para deshacer la última eliminación.\n\n"
            "¿Está ABSOLUTAMENTE SEGURO de que desea proceder?",
            icon='error', # Use 'error' icon for more emphasis
            parent=self
        )
        if not confirm2:
            return

        try:
            # Access MainWindow instance via reset_callback, then its undo_manager
            if self.reset_callback and hasattr(self.reset_callback.__self__, 'undo_manager'):
                main_window_instance = self.reset_callback.__self__
                undo_manager_instance = main_window_instance.undo_manager
                if undo_manager_instance:
                    undo_manager_instance.clear_undo_cache()
                    messagebox.showinfo("Limpieza Completada", "La caché de 'Deshacer Eliminación' ha sido limpiada.", parent=self)
                else:
                    logger.error("UndoManager instance not found on MainWindow.")
                    messagebox.showerror("Error", "No se pudo encontrar el gestor de Deshacer.", parent=self)
            else:
                logger.error("Could not access MainWindow or UndoManager instance to clear cache.")
                messagebox.showerror("Error", "No se pudo acceder a la funcionalidad para limpiar la caché.", parent=self)
        except Exception as e:
            logger.error(f"Error durante la limpieza de la caché de Deshacer: {e}", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error al limpiar la caché de Deshacer:\n{e}", parent=self)

    def _open_undo_cache_dir_action(self):
        """Abre la carpeta de caché de Deshacer en el explorador de archivos."""
        try:
            if self.reset_callback and hasattr(self.reset_callback.__self__, 'undo_manager'):
                main_window_instance = self.reset_callback.__self__
                undo_manager_instance = main_window_instance.undo_manager
                if undo_manager_instance:
                    undo_cache_path = undo_manager_instance.get_undo_cache_dir_path()
                    if undo_cache_path.exists() and undo_cache_path.is_dir():
                        logger.info(f"Intentando abrir carpeta de caché de Deshacer: {undo_cache_path}")
                        if sys.platform == "win32":
                            os.startfile(undo_cache_path)
                        elif sys.platform == "darwin":  # macOS
                            subprocess.run(["open", undo_cache_path], check=True)
                        else:  # linux variants
                            subprocess.run(["xdg-open", undo_cache_path], check=True)
                    else:
                        messagebox.showwarning("Carpeta no Encontrada",
                                               f"La carpeta de caché de Deshacer no existe o no es un directorio:\n{undo_cache_path}",
                                               parent=self)
                        logger.warning(f"Carpeta de caché de Deshacer no encontrada o no es directorio: {undo_cache_path}")
                else:
                    logger.error("UndoManager instance not found on MainWindow for opening cache dir.")
                    messagebox.showerror("Error", "No se pudo encontrar el gestor de Deshacer.", parent=self)
            else:
                logger.error("Could not access MainWindow or UndoManager instance to open cache dir.")
                messagebox.showerror("Error", "No se pudo acceder a la funcionalidad para abrir la carpeta de caché.", parent=self)
        except FileNotFoundError:
             messagebox.showerror("Error", f"No se pudo encontrar la carpeta de caché de Deshacer.", parent=self)
             logger.error(f"Carpeta de caché de Deshacer no encontrada al intentar abrir.", exc_info=True)
        except PermissionError:
             messagebox.showerror("Error", f"No tiene permisos para acceder a la carpeta de caché de Deshacer.", parent=self)
             logger.error(f"Permiso denegado al abrir la carpeta de caché de Deshacer.", exc_info=True)
        except subprocess.CalledProcessError as e:
             logger.error(f"Comando para abrir la carpeta de caché de Deshacer falló: {e}", exc_info=True)
             messagebox.showerror("Error", f"El comando para abrir la carpeta de caché de Deshacer falló:\n{e}", parent=self)
        except Exception as e:
            logger.error(f"Error inesperado al abrir la carpeta de caché de Deshacer: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir la carpeta de caché de Deshacer:\n{str(e)}", parent=self)


    def validate_input(self) -> bool:
        """Valida que los valores ingresados sean enteros positivos."""
        inputs_int = {
            "Estudios por página": self.var_studies_per_page.get(),
            "Archivos por página": self.var_files_per_page.get(),
            "Elementos por página (gestores análisis)": self.var_analysis_items_per_page.get(), # Changed label
            "Tablas resumen discreto por página": self.var_discrete_tables_per_page.get(), # New field
            "Copias de seguridad por página": self.var_backups_per_page.get(), # New field
            "Máx. copias automáticas": self.var_max_auto_backups.get(),
            "Enfriamiento copias automáticas (seg)": self.var_auto_backup_cooldown.get(),
            "Máx. copias de respaldo": self.var_max_pre_restore_backups.get(),
            "Enfriamiento copias de respaldo (seg)": self.var_pre_restore_backup_cooldown.get(),
            "Máx. copias manuales": self.var_max_manual_backups.get(),
            "Timeout caché deshacer (seg)": self.var_undo_cache_timeout_seconds.get()
        }
        # Log level is validated by combobox choices

        for label, value_str in inputs_int.items():
            try:
                value_int = int(value_str)
                is_max_auto_backup = (label == "Máx. copias automáticas")
                is_cooldown_auto = (label == "Enfriamiento copias automáticas (seg)")
                is_max_pre_restore_backup = (label == "Máx. copias de respaldo")
                is_cooldown_pre_restore = (label == "Enfriamiento copias de respaldo (seg)")
                is_max_manual_backup = (label == "Máx. copias manuales")
                is_undo_timeout = (label == "Timeout caché deshacer (seg)")

                # Max values must be > 0 if their respective backup type is enabled, otherwise >= 1
                if (is_max_auto_backup and self.var_enable_automatic_backups.get()) or \
                   (is_max_pre_restore_backup and self.var_enable_pre_restore_backups.get()) or \
                   (is_max_manual_backup and self.var_enable_manual_backups.get()):
                    if value_int <= 0:
                        messagebox.showerror("Valor Inválido", f"'{label}' debe ser un número entero positivo (>0) cuando está habilitado.", parent=self)
                        return False
                elif is_max_auto_backup or is_max_pre_restore_backup or is_max_manual_backup:
                    if value_int < 1: # Enforce >=1 even if disabled
                        messagebox.showerror("Valor Inválido", f"'{label}' debe ser un número entero positivo (>=1).", parent=self)
                        return False
                elif is_cooldown_auto or is_cooldown_pre_restore or is_undo_timeout: # Cooldowns and timeout can be 0
                    if value_int < 0: 
                        messagebox.showerror("Valor Inválido", f"'{label}' debe ser un número entero no negativo (>=0).", parent=self)
                        return False
                elif value_int <= 0: # For other general integer settings (pagination, etc.)
                    messagebox.showerror("Valor Inválido", f"'{label}' debe ser un número entero positivo (>0).", parent=self)
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
            self.settings.backups_per_page = int(self.var_backups_per_page.get()) # Save new setting
            self.settings.font_scale = float(self.var_font_scale.get())
            self.settings.theme = self.var_theme.get()
            self.settings.show_factory_reset_button = self.var_show_factory_reset.get()
            self.settings.enable_hover_tooltips = self.var_enable_hover_tooltips.get()
            
            # Backup settings
            self.settings.enable_automatic_backups = self.var_enable_automatic_backups.get()
            self.settings.max_automatic_backups = int(self.var_max_auto_backups.get())
            self.settings.automatic_backup_cooldown_seconds = int(self.var_auto_backup_cooldown.get())

            self.settings.enable_pre_restore_backups = self.var_enable_pre_restore_backups.get()
            self.settings.max_pre_restore_backups = int(self.var_max_pre_restore_backups.get())
            self.settings.pre_restore_backup_cooldown_seconds = int(self.var_pre_restore_backup_cooldown.get())
            
            self.settings.enable_manual_backups = self.var_enable_manual_backups.get()
            self.settings.max_manual_backups = int(self.var_max_manual_backups.get())

            # self.settings.show_advanced_backup_options is not saved as it's transient UI state
            self.settings.enable_undo_delete = self.var_enable_undo_delete.get() # Save Undo Delete setting
            self.settings.undo_cache_timeout_seconds = int(self.var_undo_cache_timeout_seconds.get()) # Save Undo Cache Timeout
            
            # Logging settings
            new_log_level = self.var_log_level.get()
            log_level_changed = (new_log_level != self.settings.log_level)
            self.settings.log_level = new_log_level
            
            # Guardar en el archivo config.ini
            self.settings.save_settings()
            
            msg = "Configuraciones guardadas correctamente."
            if log_level_changed:
                msg += "\n\nEl cambio en el Nivel de Logging requiere reiniciar la aplicación para tener efecto."
            
            # Check if other settings that require restart were changed (e.g. font_scale, theme)
            # For simplicity, the general message about restart for some changes is often sufficient.
            # If specific tracking is needed, compare old vs new values for theme/font_scale.
            # For now, the log_level change is the most explicit one needing a restart message here.
            
            messagebox.showinfo("Éxito", msg, parent=self)
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
                                    "El diálogo se cerrará.",
                                    parent=self)
                self.destroy() # Close the dialog after resetting
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
        # Pass self.settings and a reference to MainWindow instance if available
        # The parent of ConfigDialog is MainWindow's root.
        # The MainWindow instance itself is needed for trigger_app_restart.
        main_window_ref = None
        # The most reliable way to get MainWindow instance is via the reset_callback's __self__ attribute
        if self.reset_callback and hasattr(self.reset_callback.__self__, 'trigger_app_restart'):
            main_window_ref = self.reset_callback.__self__
        elif hasattr(self.master, 'trigger_app_restart'): 
            # self.master is the parent widget (e.g., MainWindow.root tk.Tk() instance).
            # This is less likely to be the MainWindow instance itself unless MainWindow is the Toplevel's parent.
            main_window_ref = self.master

        dialog = BackupRestoreDialog(self, app_settings=self.settings, main_window_instance=main_window_ref)
        self.wait_window(dialog) # Make it modal to ConfigDialog

        if hasattr(dialog, 'restart_required_after_restore') and dialog.restart_required_after_restore:
            logger.info("BackupRestoreDialog indicated a restart is required. Closing ConfigDialog and triggering app restart via MainWindow.")
            self.destroy() # Close ConfigDialog
            
            # Use the determined main_window_ref or the reliable self.reset_callback.__self__
            if main_window_ref and hasattr(main_window_ref, 'trigger_app_restart'):
                main_window_ref.trigger_app_restart()
            elif self.reset_callback and hasattr(self.reset_callback.__self__, 'trigger_app_restart'):
                # Fallback specifically to reset_callback's object if main_window_ref wasn't set or was incorrect
                self.reset_callback.__self__.trigger_app_restart()
            else:
                logger.warning("ConfigDialog: Could not find trigger_app_restart on a known MainWindow reference. Restart manually.")

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
                    # Attempt to create a pre-restore backup before factory reset
                    if self.settings.enable_pre_restore_backups:
                        logger.info("Creando copia de seguridad tipo 'Respaldo' antes de la restauración de fábrica...")
                        pre_restore_backup_path = backup_manager.create_backup(backup_manager.PRE_RESTORE_BACKUP_SUBDIR)
                        if pre_restore_backup_path:
                            messagebox.showinfo("Copia de Respaldo Pre-Restauración de Fábrica",
                                                f"Se ha creado una copia de respaldo ('{pre_restore_backup_path.name}') antes de proceder con la restauración de fábrica.",
                                                parent=self)
                        else:
                            # Ask user if they want to continue without the pre-restore backup
                            if not messagebox.askyesno("Error en Copia de Respaldo",
                                                             "No se pudo crear la copia de seguridad de respaldo antes de la restauración de fábrica.\n"
                                                             "¿Desea continuar con la restauración de fábrica SIN esta copia de seguridad adicional?",
                                                             icon='error', parent=self):
                                return # User chose not to proceed with factory reset

                    # Proceed with factory reset
                    self.reset_callback() # Llama a MainWindow.reset_to_defaults
                    # MainWindow.reset_to_defaults se encarga de mensajes y de cerrar/reiniciar la app si es necesario.
                    # El diálogo de configuración se cerrará si el reseteo es exitoso y la app se reinicia o va a landing.
                    self.destroy() # ConfigDialog will destroy itself if reset_callback leads to app exit
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
