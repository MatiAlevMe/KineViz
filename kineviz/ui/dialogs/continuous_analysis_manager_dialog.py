import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Text
import logging
from pathlib import Path
import json
import os # For os.startfile on Windows
import sys # For platform check
import subprocess # For open/xdg-open
from datetime import datetime # For formatting dates

from kineviz.core.services.analysis_service import AnalysisService
from kineviz.ui.dialogs.continuous_analysis_config_dialog import ContinuousAnalysisConfigDialog
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # Import font utilities

logger = logging.getLogger(__name__)

class ContinuousAnalysisManagerDialog(Toplevel):
    """
    Dialog for managing (listing, creating, viewing, deleting) continuous analyses.
    """
    def __init__(self, parent, analysis_service: AnalysisService, study_id: int, main_window_instance):
        super().__init__(parent)
        self.parent = parent
        self.analysis_service = analysis_service
        self.study_id = study_id
        self.main_window = main_window_instance # Correctly assign MainWindow instance

        self.title(f"Gestor de Análisis Continuos - Estudio {study_id}")
        self.geometry("950x700") # Adjusted size for filters
        self.grab_set() # Restored to make the dialog modal
        self.transient(parent) # Keeps it on top of parent

        # Store all analyses data
        self.all_analyses_data = []
        self.study_vis = []
        self.study_aliases = {}

        # Filter related StringVars
        self.search_term_var = tk.StringVar()
        self.filter_vi_count_var = tk.StringVar(value="No filtrar")
        self.current_page = 1 # For pagination
        self.total_pages = 1  # For pagination
        self.items_per_page = main_window_instance.settings.analysis_items_per_page # Use main_window_instance
        self.filter_vi1_name_var = tk.StringVar()
        self.filter_vi1_desc_var = tk.StringVar()
        self.filter_vi2_name_var = tk.StringVar()
        self.filter_vi2_desc_var = tk.StringVar()
        self.filter_variable_var = tk.StringVar(value="Todos") # For Variable Analizada filter

        self._load_study_vi_data() # Load VIs and aliases for filters

        # --- Fixed Panes Setup ---
        # Top fixed pane for filters
        self.top_fixed_filters_frame = ttk.Frame(self, padding=(10,10,10,0)) # Pad bottom 0
        self.top_fixed_filters_frame.pack(side=tk.TOP, fill=tk.X)

        # Bottom fixed panes (packed in reverse visual order)
        self.bottom_fixed_delete_actions_frame = ttk.Frame(self, padding=(10,5,10,10)) # Pad top 5
        self.bottom_fixed_delete_actions_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.bottom_fixed_pagination_frame = ttk.Frame(self, padding=(10,5,10,0)) # Pad top 5, bottom 0
        self.bottom_fixed_pagination_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.bottom_fixed_folder_actions_frame = ttk.Frame(self, padding=(10,5,10,0))
        self.bottom_fixed_folder_actions_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.bottom_fixed_view_actions_frame = ttk.Frame(self, padding=(10,10,10,0)) # Pad top 10, bottom 0
        self.bottom_fixed_view_actions_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # --- Scrollable Middle Area (Canvas) ---
        canvas_container = ttk.Frame(self) # Takes remaining space
        canvas_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=0) # No vertical padding for container itself

        self.canvas = tk.Canvas(canvas_container, highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        
        self.scrollable_main_frame = ttk.Frame(self.canvas, padding="10") # Content goes here

        self.scrollable_main_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")) if hasattr(self, 'canvas') and self.canvas.winfo_exists() else None
        )
        
        self.canvas_interior_id = self.canvas.create_window((0, 0), window=self.scrollable_main_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        self.canvas.bind("<Configure>", self._dynamic_canvas_item_width_configure)

        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        # --- End Scrollable Area Setup ---
        
        self.create_widgets() # Populates the fixed and scrollable frames
        self._populate_filter_vi_comboboxes() 
        self.load_analyses() 

        # Center dialog
        self.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        position_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        position_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"+{position_x}+{position_y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", self._on_close)

        # Set minsize after widgets are created
        self.update_idletasks()
        # Simplified minsize - set a reasonable fixed minimum
        self.minsize(600, 400)
        # Initial geometry can also be set here if desired, e.g., self.geometry("950x700")


    # _show_input_help was already added in the previous commit, this block is to ensure it's present.
    # If it was missing, this would add it. Since it's there, this block might be reported as not matching
    # if the content is identical to what's already in the file.
    # For safety, I'll assume it might be missing if the traceback occurred.
    def _show_input_help(self, title: str, message: str):
        """Muestra un popup de ayuda simple."""
        messagebox.showinfo(title, message, parent=self)

    def _dynamic_canvas_item_width_configure(self, event):
        """Adjusts the width of the scrollable_frame_content to match the canvas width or content width."""
        canvas_width = event.width
        if hasattr(self, 'scrollable_main_frame') and self.scrollable_main_frame.winfo_exists():
            self.scrollable_main_frame.update_idletasks()
            content_natural_width = self.scrollable_main_frame.winfo_reqwidth()
        else:
            content_natural_width = canvas_width
            
        effective_width = max(content_natural_width, canvas_width)
        
        if hasattr(self, 'canvas_interior_id') and self.canvas_interior_id and \
           hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.itemconfig(self.canvas_interior_id, width=effective_width)

    def create_widgets(self):
        """Populates the fixed and scrollable frames."""
        # --- Populate Top Fixed Filters Frame ---
        # search_filter_frame is now self.top_fixed_filters_frame
        search_filter_frame = ttk.LabelFrame(self.top_fixed_filters_frame, text="Buscar y Filtrar Análisis", padding="10")
        search_filter_frame.pack(fill=tk.X, expand=True) # Pack it inside the top fixed frame
        search_filter_frame.columnconfigure(1, weight=1) 
        search_filter_frame.columnconfigure(3, weight=1)
        search_filter_frame.columnconfigure(5, weight=1)


        # Search
        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.main_window.settings.font_scale)
        ttk.Label(search_filter_frame, text="Buscar:").grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")
        search_entry = ttk.Entry(search_filter_frame, textvariable=self.search_term_var, width=30, font=scaled_font)
        search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        search_entry.bind("<Return>", lambda event: self._apply_filters_and_search())
        # Search button is moved to filter_action_buttons_frame

        # Filter by Variable Analizada
        ttk.Label(search_filter_frame, text="Variable Analizada:").grid(row=1, column=0, padx=(0,5), pady=5, sticky="w")
        self.filter_variable_combo = ttk.Combobox(search_filter_frame, textvariable=self.filter_variable_var, state="readonly", width=40, font=scaled_font)
        self.filter_variable_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.filter_variable_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters_and_search())

        # Filter by VI count
        ttk.Label(search_filter_frame, text="Filtrar por VIs:").grid(row=2, column=0, padx=(0,5), pady=5, sticky="w")
        self.filter_vi_count_combo = ttk.Combobox(search_filter_frame, textvariable=self.filter_vi_count_var,
                                                  values=["No filtrar", "1 VI", "2 VIs"], state="readonly", width=12, font=scaled_font)
        self.filter_vi_count_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.filter_vi_count_combo.bind("<<ComboboxSelected>>", self._on_filter_vi_count_change)

        # VI 1 Filter
        self.filter_vi1_frame = ttk.Frame(search_filter_frame)
        self.filter_vi1_frame.grid(row=3, column=0, columnspan=3, pady=5, sticky="ew") # Adjusted row
        self.filter_vi1_frame.columnconfigure(1, weight=1)
        self.filter_vi1_frame.columnconfigure(3, weight=1)

        ttk.Label(self.filter_vi1_frame, text="VI 1:").grid(row=0, column=0, padx=(0,5), pady=2, sticky="w")
        self.filter_vi1_name_combo = ttk.Combobox(self.filter_vi1_frame, textvariable=self.filter_vi1_name_var, state="readonly", width=15, font=scaled_font)
        self.filter_vi1_name_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.filter_vi1_name_combo.bind("<<ComboboxSelected>>", lambda e: self._update_filter_descriptor_combobox(1))
        
        ttk.Label(self.filter_vi1_frame, text="Sub-valor VI 1:").grid(row=0, column=2, padx=(10,5), pady=2, sticky="w")
        self.filter_vi1_desc_combo = ttk.Combobox(self.filter_vi1_frame, textvariable=self.filter_vi1_desc_var, state="readonly", width=15, font=scaled_font)
        self.filter_vi1_desc_combo.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        # VI 2 Filter (initially hidden)
        self.filter_vi2_frame = ttk.Frame(search_filter_frame)
        self.filter_vi2_frame.grid(row=4, column=0, columnspan=3, pady=5, sticky="ew") # Adjusted row
        self.filter_vi2_frame.columnconfigure(1, weight=1)
        self.filter_vi2_frame.columnconfigure(3, weight=1)

        ttk.Label(self.filter_vi2_frame, text="VI 2:").grid(row=0, column=0, padx=(0,5), pady=2, sticky="w")
        self.filter_vi2_name_combo = ttk.Combobox(self.filter_vi2_frame, textvariable=self.filter_vi2_name_var, state="readonly", width=15, font=scaled_font)
        self.filter_vi2_name_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.filter_vi2_name_combo.bind("<<ComboboxSelected>>", lambda e: self._update_filter_descriptor_combobox(2))

        ttk.Label(self.filter_vi2_frame, text="Sub-valor VI 2:").grid(row=0, column=2, padx=(10,5), pady=2, sticky="w")
        self.filter_vi2_desc_combo = ttk.Combobox(self.filter_vi2_frame, textvariable=self.filter_vi2_desc_var, state="readonly", width=15, font=scaled_font)
        self.filter_vi2_desc_combo.grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        
        self.filter_vi1_frame.grid_remove() # Hide VI1 frame initially
        self.filter_vi2_frame.grid_remove() # Hide VI2 frame initially

        # Filter Action Buttons (moved to a new row)
        filter_action_buttons_frame = ttk.Frame(search_filter_frame)
        filter_action_buttons_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(5,0)) # New row for these buttons
        
        apply_button_filters = ttk.Button(filter_action_buttons_frame, text="Aplicar Filtros", command=self._apply_filters_and_search, style="Celeste.TButton")
        apply_button_filters.pack(side=tk.LEFT, padx=(0,5)) # Adjusted padding
        Tooltip(apply_button_filters, text="Aplicar todos los filtros seleccionados.", short_text="Aplicar filtros.", enabled=self.main_window.settings.enable_hover_tooltips)

        clear_button_filters = ttk.Button(filter_action_buttons_frame, text="Limpiar Filtros", command=self._clear_filters)
        clear_button_filters.pack(side=tk.LEFT, padx=(0,5))
        Tooltip(clear_button_filters, text="Limpiar todos los filtros y mostrar todos los análisis.", short_text="Limpiar filtros.", enabled=self.main_window.settings.enable_hover_tooltips)

        # Spacer to push subsequent buttons to the right
        ttk.Frame(filter_action_buttons_frame).pack(side=tk.LEFT, expand=True, fill=tk.X)

        refresh_button_list = ttk.Button(filter_action_buttons_frame, text="Refrescar Lista", command=self.load_analyses)
        refresh_button_list.pack(side=tk.RIGHT, padx=(0,0)) # Rightmost, no right padding from itself
        Tooltip(refresh_button_list, text="Recargar la lista de análisis guardados.", short_text="Refrescar lista.", enabled=self.main_window.settings.enable_hover_tooltips)

        search_button_moved_cont = ttk.Button(filter_action_buttons_frame, text="Buscar", command=self._apply_filters_and_search, style="Celeste.TButton")
        search_button_moved_cont.pack(side=tk.RIGHT, padx=(0,5)) # To the left of Refresh, 5px padding on its right
        Tooltip(search_button_moved_cont, text="Buscar análisis por nombre o variable analizada.", short_text="Buscar.", enabled=self.main_window.settings.enable_hover_tooltips)


        # --- Treeview for listing analyses (inside self.scrollable_main_frame) ---
        tree_frame = ttk.LabelFrame(self.scrollable_main_frame, text="Análisis Guardados")
        tree_frame.pack(fill=tk.BOTH, expand=True) # Pack it to fill the scrollable area
        # tree_frame.rowconfigure(0, weight=1) # Removed to respect treeview height
        tree_frame.columnconfigure(0, weight=1)

        columns = ("name", "column", "groups", "date")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended", height=self.items_per_page)

        self.tree.heading("name", text="Nombre Análisis")
        self.tree.heading("column", text="Variable Analizada")
        self.tree.heading("groups", text="Grupos Comparados")
        self.tree.heading("date", text="Fecha Creación/Modif.")

        self.tree.column("name", width=200, anchor=tk.W)
        self.tree.column("column", width=250, anchor=tk.W)
        self.tree.column("groups", width=300, anchor=tk.W)
        self.tree.column("date", width=150, anchor=tk.CENTER)

        # Treeview's own scrollbars are removed. Main canvas scrollbars will be used.
        # Pack to fill horizontally, but let height be determined by items_per_page
        self.tree.pack(fill=tk.X, expand=True) 

        self.tree.bind("<<TreeviewSelect>>", self._on_analysis_selected)
        self.tree.bind("<Double-1>", self._view_plot)

        # --- Populate Bottom Fixed View Actions Frame ---
        # (Ver Gráfico SPM (PNG), Ver Gráfico Interactivo SPM, Ver Configuración, Nuevo Análisis...)
        self.view_plot_button = ttk.Button(self.bottom_fixed_view_actions_frame, text="Ver Gráfico SPM (PNG)", command=self._view_plot, state=tk.DISABLED, style="Green.TButton")
        self.view_plot_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.view_plot_button, text="Abrir el gráfico SPM estático (PNG) del análisis seleccionado.", short_text="Ver gráfico SPM.", enabled=self.main_window.settings.enable_hover_tooltips)

        self.view_interactive_plot_button = ttk.Button(self.bottom_fixed_view_actions_frame, text="Ver Gráfico Interactivo SPM", command=self._view_interactive_plot, state=tk.DISABLED, style="Green.TButton")
        self.view_interactive_plot_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.view_interactive_plot_button, text="Abrir el gráfico SPM interactivo (HTML) del análisis seleccionado en un navegador.", short_text="Ver interactivo SPM.", enabled=self.main_window.settings.enable_hover_tooltips)

        self.view_config_button = ttk.Button(self.bottom_fixed_view_actions_frame, text="Ver Configuración", command=self._view_config, state=tk.DISABLED, style="Celeste.TButton")
        self.view_config_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.view_config_button, text="Ver la configuración detallada del análisis SPM seleccionado en un archivo de texto.", short_text="Ver config. SPM.", enabled=self.main_window.settings.enable_hover_tooltips)

        # --- Populate Bottom Fixed Folder Actions Frame ---
        # (Abrir Carpeta, Abrir Carpeta de Análisis Continuos)
        self.open_folder_button = ttk.Button(self.bottom_fixed_folder_actions_frame, text="Abrir Carpeta", command=self._open_folder, state=tk.DISABLED)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.open_folder_button, text="Abrir la carpeta que contiene los archivos del análisis SPM seleccionado.", short_text="Abrir carpeta análisis.", enabled=self.main_window.settings.enable_hover_tooltips)

        self.open_main_continuous_folder_button = ttk.Button(
            self.bottom_fixed_folder_actions_frame,
            text="Abrir Carpeta de Análisis Continuos",
            command=self._open_main_continuous_analyses_folder
        )
        self.open_main_continuous_folder_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.open_main_continuous_folder_button, text="Abrir la carpeta principal donde se guardan todos los análisis continuos (SPM) de este estudio.", short_text="Abrir carpeta principal.", enabled=self.main_window.settings.enable_hover_tooltips)

        ttk.Frame(self.bottom_fixed_folder_actions_frame).pack(side=tk.LEFT, expand=True, fill=tk.X) # Spacer

        new_analysis_button_cont = ttk.Button(self.bottom_fixed_folder_actions_frame, text="Nuevo Análisis...", command=self._open_new_analysis_dialog, style="Green.TButton")
        new_analysis_button_cont.pack(side=tk.RIGHT, padx=5)
        Tooltip(new_analysis_button_cont, text="Abrir el diálogo para configurar y generar un nuevo análisis continuo (SPM).", short_text="Nuevo análisis SPM.", enabled=self.main_window.settings.enable_hover_tooltips)

        # --- Populate Bottom Fixed Pagination Frame ---
        # This is done by _update_pagination_controls, which now needs to target self.bottom_fixed_pagination_frame
        # self.pagination_controls_frame is now self.bottom_fixed_pagination_frame

        # --- Populate Bottom Fixed Delete Actions Frame ---
        # (Eliminar Todos los Análisis Continuos, Eliminar Seleccionado(s), Cerrar)
        self.delete_all_button = ttk.Button(
            self.bottom_fixed_delete_actions_frame,
            text="Eliminar Todos los Análisis Continuos",
            command=self._confirm_delete_all_continuous_analyses,
            style="Danger.TButton"
        )
        self.delete_all_button.pack(side=tk.LEFT, padx=(0, 5))
        Tooltip(self.delete_all_button, text="Eliminar TODOS los análisis continuos (SPM) guardados para este estudio. ¡Acción irreversible!", short_text="Eliminar todo.", enabled=self.main_window.settings.enable_hover_tooltips)

        self.delete_selected_button = ttk.Button(
            self.bottom_fixed_delete_actions_frame,
            text="Eliminar Seleccionado(s)",
            command=self._confirm_delete_selected_analyses,
            state=tk.DISABLED,
            style="Danger.TButton"
        )
        self.delete_selected_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.delete_selected_button, text="Eliminar los análisis continuos (SPM) seleccionados en la lista.", short_text="Eliminar selección.", enabled=self.main_window.settings.enable_hover_tooltips)

        close_button_cont = ttk.Button(self.bottom_fixed_delete_actions_frame, text="Cerrar", command=self._on_close)
        close_button_cont.pack(side=tk.RIGHT, padx=5)
        Tooltip(close_button_cont, text="Cerrar el gestor de análisis continuos.", short_text="Cerrar.", enabled=self.main_window.settings.enable_hover_tooltips)

        # self.delete_all_button = ttk.Button( # OLD
        #     bottom_action_frame,
        # text="Eliminar Todos los Análisis Continuos", # REMOVED ORPHANED LINES
        # command=self._confirm_delete_all_continuous_analyses, # REMOVED ORPHANED LINES
        # style="Danger.TButton" # REMOVED ORPHANED LINES
        # ) # REMOVED ORPHANED LINES
        # self.delete_all_button.pack(side=tk.LEFT, padx=(0, 5)) # REMOVED ORPHANED LINES
        
        # self.delete_selected_button = ttk.Button( # OLD
        # bottom_action_frame, # OLD
        # text="Eliminar Seleccionado(s)", # REMOVED ORPHANED LINES
        # command=self._confirm_delete_selected_analyses, # Nuevo método # REMOVED ORPHANED LINES
        # state=tk.DISABLED, # REMOVED ORPHANED LINES
        # style="Danger.TButton" # REMOVED ORPHANED LINES
        # ) # REMOVED ORPHANED LINES
        # self.delete_selected_button.pack(side=tk.LEFT, padx=5) # REMOVED ORPHANED LINES

        # El botón individual "Eliminar Análisis" ya no es necesario
        # self.delete_button = ttk.Button(bottom_action_frame, text="Eliminar Análisis", command=self._delete_analysis, state=tk.DISABLED) # OLD
        # self.delete_button.pack(side=tk.LEFT, padx=5) # OLD

        # ttk.Button(bottom_action_frame, text="Cerrar", command=self._on_close).pack(side=tk.RIGHT, padx=5) # OLD

    def _confirm_delete_all_continuous_analyses(self):
        """Muestra confirmación y luego elimina todos los análisis continuos."""
        study_name = "ID Desconocido"
        try:
            study_details = self.analysis_service.study_service.get_study_details(self.study_id)
            study_name = study_details.get('name', f"ID {self.study_id}")
        except Exception:
            logger.error(f"No se pudo obtener el nombre del estudio {self.study_id} para el diálogo de confirmación.")

        if messagebox.askyesno("Confirmar Eliminación Total de Análisis Continuos",
                               f"¿Está SEGURO de que desea eliminar TODOS los análisis continuos (SPM) guardados "
                               f"para el estudio '{study_name}'?\n\n"
                               "Esta acción es IRREVERSIBLE.",
                               icon='warning', parent=self):
            try:
                deleted_count = self.analysis_service.delete_all_continuous_analyses(self.study_id)
                messagebox.showinfo("Eliminación Completada",
                                    f"{deleted_count} análisis continuos han sido eliminados.",
                                    parent=self)
                self.load_analyses() # Recargar la lista
            except Exception as e:
                logger.error(f"Error al eliminar todos los análisis continuos para estudio {self.study_id}: {e}", exc_info=True)
                messagebox.showerror("Error al Eliminar Análisis",
                                     f"Ocurrió un error al eliminar los análisis:\n{e}",
                                     parent=self)

    def _load_study_vi_data(self):
        """Loads VI names and their descriptors for the current study."""
        try:
            details = self.analysis_service.study_service.get_study_details(self.study_id)
            self.study_vis = details.get('independent_variables', [])
            self.study_aliases = details.get('aliases', {})
            logger.debug(f"Loaded VIs for study {self.study_id}: {self.study_vis}")
        except Exception as e:
            logger.error(f"Error loading VI data for study {self.study_id}: {e}", exc_info=True)
            self.study_vis = []
            self.study_aliases = {}

    def _populate_filter_vi_comboboxes(self):
        """Populates the VI name comboboxes for filtering."""
        vi_names = [vi['name'] for vi in self.study_vis if vi.get('name')]
        self.filter_vi1_name_combo['values'] = sorted(vi_names)
        self.filter_vi2_name_combo['values'] = sorted(vi_names)

    def _update_filter_descriptor_combobox(self, vi_num: int):
        """Updates the descriptor combobox for the specified VI filter."""
        selected_vi_name = ""
        desc_combo = None
        desc_var = None

        if vi_num == 1:
            selected_vi_name = self.filter_vi1_name_var.get()
            desc_combo = self.filter_vi1_desc_combo
            desc_var = self.filter_vi1_desc_var
        elif vi_num == 2:
            selected_vi_name = self.filter_vi2_name_var.get()
            desc_combo = self.filter_vi2_desc_combo
            desc_var = self.filter_vi2_desc_var
        
        if not desc_combo or not desc_var: return

        desc_var.set("")
        descriptors_for_vi = []
        if selected_vi_name:
            for vi_info in self.study_vis:
                if vi_info.get('name') == selected_vi_name:
                    descriptors_for_vi = [
                        f"{d} ({self.study_aliases.get(d)})" if self.study_aliases.get(d) else d
                        for d in vi_info.get('descriptors', [])
                    ]
                    break
        desc_combo['values'] = sorted(descriptors_for_vi)

    def _on_filter_vi_count_change(self, event=None):
        """Handles changes in the VI count filter selection."""
        count_mode = self.filter_vi_count_var.get()
        self.filter_vi1_name_var.set("")
        self.filter_vi1_desc_var.set("")
        self.filter_vi2_name_var.set("")
        self.filter_vi2_desc_var.set("")
        self._update_filter_descriptor_combobox(1) # Clear descriptors for VI1
        self._update_filter_descriptor_combobox(2) # Clear descriptors for VI2

        if count_mode == "1 VI":
            self.filter_vi1_frame.grid()
            self.filter_vi2_frame.grid_remove()
        elif count_mode == "2 VIs":
            self.filter_vi1_frame.grid()
            self.filter_vi2_frame.grid()
        else: # "No filtrar"
            self.filter_vi1_frame.grid_remove()
            self.filter_vi2_frame.grid_remove()
        self._apply_filters_and_search() # Apply immediately

    def _get_descriptor_original_value(self, display_name: str) -> str:
        """Converts a display name (e.g., 'Desc (Alias)') back to original descriptor."""
        if not display_name: return ""
        # Check if it has an alias part " (Alias)"
        if " (" in display_name and display_name.endswith(")"):
            original_candidate = display_name.rsplit(" (", 1)[0]
            # Verify if this original_candidate maps to the display_name via aliases
            if self.study_aliases.get(original_candidate) == display_name.rsplit(" (", 1)[1][:-1]:
                return original_candidate
        return display_name # Assume it's already the original if no alias matches pattern

    def _apply_filters_and_search(self):
        search_term = self.search_term_var.get().lower()
        selected_variable_filter = self.filter_variable_var.get()
        filter_mode = self.filter_vi_count_var.get()
        
        vi1_name_filter = self.filter_vi1_name_var.get()
        vi1_desc_display_filter = self.filter_vi1_desc_var.get()
        vi1_desc_original_filter = self._get_descriptor_original_value(vi1_desc_display_filter)
        
        vi2_name_filter = self.filter_vi2_name_var.get()
        vi2_desc_display_filter = self.filter_vi2_desc_var.get()
        vi2_desc_original_filter = self._get_descriptor_original_value(vi2_desc_display_filter)

        target_filter_key1 = f"{vi1_name_filter}={vi1_desc_original_filter}" if vi1_name_filter and vi1_desc_original_filter else None
        target_filter_key2 = f"{vi2_name_filter}={vi2_desc_original_filter}" if vi2_name_filter and vi2_desc_original_filter else None

        filtered_analyses = []
        for analysis_info in self.all_analyses_data:
            # 1. Apply search term
            matches_search = True
            if search_term:
                name_match = search_term in analysis_info.get('name', '').lower()
                column_match = search_term in analysis_info.get('config', {}).get('column', '').lower()
                
                # For groups_str, we need to reconstruct it as it would be displayed
                # This is a bit redundant but ensures search matches what user sees
                temp_config = analysis_info.get('config', {})
                temp_group_keys = temp_config.get('groups', [])
                temp_mode = temp_config.get('grouping_mode')
                temp_primary_vi = temp_config.get('primary_vi_name')
                temp_fixed_vi = temp_config.get('fixed_vi_name')
                temp_fixed_desc_display = temp_config.get('fixed_descriptor_display')
                
                temp_group_display_parts = self._format_analysis_groups_for_display(
                    temp_group_keys, temp_mode, temp_primary_vi, temp_fixed_vi, temp_fixed_desc_display
                )
                groups_str_match = search_term in (" vs ".join(temp_group_display_parts)).lower()
                
                matches_search = name_match or column_match or groups_str_match
            
            if not matches_search:
                continue

            # 2. Apply Variable Analizada filter
            variable_match = True
            if selected_variable_filter != "Todos":
                if analysis_info.get('config', {}).get('column', '') != selected_variable_filter:
                    variable_match = False
            
            if not variable_match:
                continue

            # 3. Apply VI filters
            matches_filters = True
            if filter_mode != "No filtrar":
                analysis_config_groups = analysis_info.get('config', {}).get('groups', []) # These are effective keys
                
                if target_filter_key1:
                    key1_found = any(target_filter_key1 == key_part for group_key in analysis_config_groups for key_part in group_key.split(';'))
                    if not key1_found: matches_filters = False
                
                if matches_filters and filter_mode == "2 VIs" and target_filter_key2:
                    key2_found = any(target_filter_key2 == key_part for group_key in analysis_config_groups for key_part in group_key.split(';'))
                    if not key2_found: matches_filters = False
            
            if matches_filters:
                filtered_analyses.append(analysis_info)
        
        self._populate_treeview(filtered_analyses)


    def _clear_filters(self):
        self.search_term_var.set("")
        self.filter_variable_var.set("Todos")
        self.filter_vi_count_var.set("No filtrar")
        self._on_filter_vi_count_change() # This will clear sub-filters and re-apply (which calls _apply_filters_and_search)

    def _format_analysis_groups_for_display(self, group_keys, mode, primary_vi, fixed_vi, fixed_desc_display):
        """Helper to format group keys for display, using aliases."""
        group_display_parts = []
        if mode == "1VI" and primary_vi and group_keys:
            for desc_key_part in group_keys: # e.g., "Edad=Joven" (this is an effective key from config)
                try:
                    # desc_key_part should already be in "VI=Descriptor" format for 1VI mode from config
                    vi_name_part, desc_val_part = desc_key_part.split("=",1)
                    if vi_name_part == primary_vi: # Ensure it's the primary VI
                        alias = self.study_aliases.get(desc_val_part, desc_val_part)
                        group_display_parts.append(f"{primary_vi}: {alias}")
                    else: # Should not happen if config['groups'] is correctly set for 1VI
                        group_display_parts.append(desc_key_part) 
                except ValueError: 
                    group_display_parts.append(desc_key_part) # Fallback
        elif mode == "2VIs" and fixed_vi and fixed_desc_display and group_keys:
            # group_keys contains full keys like "VI_Fija=ValorFijo;VI_Variable=ValorVariable"
            fixed_desc_original = self._get_descriptor_original_value(fixed_desc_display)
            fixed_pair_to_format = f"{fixed_vi}={fixed_desc_original}"
            
            # Format the fixed part once (with alias)
            fixed_vi_alias = self.study_aliases.get(fixed_desc_original, fixed_desc_original)
            formatted_fixed_part = f"{fixed_vi}: {fixed_vi_alias}"

            for full_key_item in group_keys: # e.g., "Salto=CMJ;Condicion=PRE"
                variable_part_display_segments = []
                # Iterate through parts of the full key to find the variable one(s)
                for part_of_full_key in full_key_item.split(';'):
                    if part_of_full_key != fixed_pair_to_format: # This is the variable part
                        try:
                            vi_name_var, desc_val_var = part_of_full_key.split('=',1)
                            alias_var = self.study_aliases.get(desc_val_var, desc_val_var)
                            variable_part_display_segments.append(f"{vi_name_var}: {alias_var}")
                        except ValueError: 
                            variable_part_display_segments.append(part_of_full_key) # Fallback
                
                if variable_part_display_segments:
                    # Combine fixed part with variable part(s)
                    full_display_for_group = f"{formatted_fixed_part}, {', '.join(variable_part_display_segments)}"
                    group_display_parts.append(full_display_for_group)
                else: # Should only be the fixed part, which isn't a comparison group itself
                    group_display_parts.append(formatted_fixed_part) # Fallback, though unusual
        else: # Fallback for combined or unknown mode
            for key in group_keys:
                parts = []
                for item_part in key.split(';'):
                    try:
                        vi_name, desc_val = item_part.split('=', 1)
                        alias = self.study_aliases.get(desc_val, desc_val)
                        parts.append(f"{vi_name}: {alias}")
                    except ValueError: parts.append(item_part)
                group_display_parts.append(", ".join(parts))
        return group_display_parts

    def _populate_treeview(self, analyses_to_display):
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Pagination logic
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        paginated_analyses = analyses_to_display[start_index:end_index]

        if not paginated_analyses and analyses_to_display: # If current page is empty but there is data
            # This can happen if filters reduce items such that current_page is too high
            self.current_page = max(1, self.total_pages) # Go to last valid page or 1
            start_index = (self.current_page - 1) * self.items_per_page
            end_index = start_index + self.items_per_page
            paginated_analyses = analyses_to_display[start_index:end_index]
        
        for analysis_info in paginated_analyses:
            name = analysis_info.get('name', 'N/A')
            config = analysis_info.get('config', {})
            column = config.get('column', 'N/A')
            
            group_keys = config.get('groups', [])
            mode = config.get('grouping_mode')
            primary_vi = config.get('primary_vi_name')
            fixed_vi = config.get('fixed_vi_name')
            fixed_desc_display = config.get('fixed_descriptor_display')
            
            group_display_parts = self._format_analysis_groups_for_display(
                group_keys, mode, primary_vi, fixed_vi, fixed_desc_display
            )
            groups_str = " vs ".join(group_display_parts) if group_display_parts else "N/A"
            
            mtime = analysis_info.get('mtime')
            date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M') if mtime else "N/A"
            
            # Use the unique path string as iid
            analysis_path_str = str(analysis_info.get('path', name)) # Fallback to name if path is missing
            
            # Ensure iid is unique even if path somehow is duplicated (should not happen)
            # or if name is used as fallback and is duplicated.
            # This is a defensive measure for treeview stability.
            final_iid = analysis_path_str
            counter = 0
            while self.tree.exists(final_iid):
                counter += 1
                final_iid = f"{analysis_path_str}_{counter}"
                logger.warning(f"Duplicate iid detected for continuous analysis. Using '{final_iid}' instead of '{analysis_path_str}'. This might indicate an issue with analysis name uniqueness or path retrieval.")

            self.tree.insert("", tk.END, values=(name, column, groups_str, date_str), iid=final_iid)
        
        self._update_pagination_controls(len(analyses_to_display))
        self._on_analysis_selected() # Update button states

    def load_analyses(self):
        """Fetches all analyses and then applies current filters/search to populate the tree."""
        try:
            self.all_analyses_data = self.analysis_service.list_continuous_analyses(self.study_id)
            # Analyses are already sorted by mtime in list_continuous_analyses
            logger.debug(f"Cargados {len(self.all_analyses_data)} análisis continuos para estudio {self.study_id}.")
        except Exception as e:
            logger.error(f"Error obteniendo lista completa de análisis continuos para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron obtener los análisis continuos:\n{e}", parent=self)
            self.all_analyses_data = []

        # Populate Variable Analizada filter
        variables = sorted(list(set(
            info.get('config', {}).get('column', '') 
            for info in self.all_analyses_data 
            if info.get('config', {}).get('column')
        )))
        self.filter_variable_combo['values'] = ["Todos"] + variables
        
        self._apply_filters_and_search() # Populate tree with (initially unfiltered) data
        self._update_pagination_controls(len(self.all_analyses_data)) # Initial pagination setup


    def get_selected_analyses_info(self) -> list[dict]:
        """
        Obtiene una lista de diccionarios de información para los análisis seleccionados.
        Retorna lista vacía si no hay selección válida.
        """
        selected_analyses = []
        selected_item_iids = self.tree.selection()

        if not selected_item_iids:
            return []

        for selected_item_iid in selected_item_iids:
            found_info = None
            for analysis_info in self.all_analyses_data:
                analysis_path_str = str(analysis_info.get('path', ''))
                if selected_item_iid == analysis_path_str or selected_item_iid.startswith(f"{analysis_path_str}_"):
                    found_info = analysis_info
                    break
            
            if not found_info: # Fallback por nombre
                for analysis_info in self.all_analyses_data:
                    # Assuming 'name' is stored in tree.item(iid, "values")[0] or similar if iid is not path
                    # However, iid IS the path string or path_counter, so this fallback might be less critical
                    # but kept for robustness if iid generation changes.
                    # For now, this fallback is less likely to be hit if iid is path.
                    if analysis_info.get('name') == selected_item_iid: # This fallback is weak if iid is path
                        logger.warning(f"Selected iid '{selected_item_iid}' matched by name (fallback). Path might be missing for this item.")
                        found_info = analysis_info
                        break
            
            if found_info:
                selected_analyses.append(found_info)
            else:
                logger.warning(f"Análisis seleccionado con iid '{selected_item_iid}' no encontrado en self.all_analyses_data.")
        
        return selected_analyses

    def _on_analysis_selected(self, event=None):
        selected_info_list = self.get_selected_analyses_info()
        can_act_single = len(selected_info_list) == 1
        can_act_multiple = len(selected_info_list) > 0

        # Buttons requiring single selection
        self.view_plot_button.config(state=tk.NORMAL if can_act_single and selected_info_list[0].get("plot_path") else tk.DISABLED)
        self.view_interactive_plot_button.config(state=tk.NORMAL if can_act_single and selected_info_list[0].get("interactive_plot_path") else tk.DISABLED)
        self.view_config_button.config(state=tk.NORMAL if can_act_single and selected_info_list[0].get("config_path") else tk.DISABLED)
        self.open_folder_button.config(state=tk.NORMAL if can_act_single and selected_info_list[0].get("path") else tk.DISABLED)
        
        # Button for multiple (or single) selection
        self.delete_selected_button.config(state=tk.NORMAL if can_act_multiple else tk.DISABLED)
        # self.delete_button.config(state=tk.NORMAL if can_act_single else tk.DISABLED) # Old single delete button

    def _open_new_analysis_dialog(self):
        # --- Pre-validation for participant and VI diversity for Continuous Analysis ---
        # This check is against processed files for 'Cinematica'.
        
        # Check 1: Are there any 'Cinematica' files processed?
        available_frequencies = self.analysis_service.get_available_frequencies_for_study(self.study_id)
        if "Cinematica" not in available_frequencies:
            messagebox.showwarning("Datos No Disponibles",
                                   "El análisis continuo requiere datos procesados de 'Cinematica'.\n"
                                   "No se encontraron archivos cinemáticos procesados en este estudio.",
                                   parent=self)
            return

        # Check 2: Potential for at least two comparison groups based on VIs.
        # This is a simplified check.
        try:
            # For continuous, groups are formed based on VIs from processed files.
            # We use get_filtered_discrete_analysis_groups with mode='1VI' and a dummy primary_vi
            # just to see if *any* groups can be formed. This is an approximation.
            # A more accurate check would be to see if AnalysisService can form at least two groups
            # from the actual processed files for 'Cinematica'.
            # For now, check if there's at least one VI with at least two descriptors.
            study_details = self.analysis_service.study_service.get_study_details(self.study_id)
            vis = study_details.get('independent_variables', [])
            can_form_groups = False
            if len(vis) >= 2: # If 2+ VIs, high chance of forming groups
                can_form_groups = True
            elif len(vis) == 1 and len(vis[0].get('descriptors', [])) >= 2: # If 1 VI with 2+ descriptors
                can_form_groups = True
            
            if not can_form_groups:
                 messagebox.showwarning("Datos Insuficientes",
                                       "No hay suficientes Variables Independientes (VIs) o sub-valores definidos "
                                       "en el estudio para formar al menos dos grupos de comparación para el análisis continuo.",
                                       parent=self)
                 return
        except Exception as e_group_check:
            logger.error(f"Error al verificar VIs para pre-validación de análisis continuo: {e_group_check}", exc_info=True)
            messagebox.showerror("Error de Pre-validación",
                                 f"Ocurrió un error al verificar las VIs para el análisis:\n{e_group_check}",
                                 parent=self)
            return
        
        # This is where ContinuousAnalysisConfigDialog is launched
        dialog = ContinuousAnalysisConfigDialog(self, self.analysis_service, self.study_id, self.main_window.settings) # Pass settings
        
        # Check if dialog was destroyed immediately (e.g. error in its __init__)
        if not dialog.winfo_exists():
            logger.error("ContinuousAnalysisConfigDialog fue destruido inmediatamente después de la creación. No se puede esperar.")
            # Optionally, show a generic error to the user here
            # messagebox.showerror("Error", "No se pudo abrir el diálogo de configuración de análisis continuo.", parent=self)
            self.load_analyses() # Refresh list in case something changed or to reset state
            return

        self.wait_window(dialog) # Ensure manager waits for config dialog to close

        # After wait_window, check if dialog.result exists and if dialog itself wasn't prematurely destroyed
        # (though winfo_exists might be false now if it closed normally)
        # The key is whether dialog.result was set.
        if hasattr(dialog, 'result') and dialog.result:
            logger.info(f"Configuración recibida del diálogo de análisis continuo: {dialog.result}")
            
            # --- Validación de Nombre Duplicado ---
            analysis_name_to_check = dialog.result.get('analysis_name')
            variable_analyzed_full = dialog.result.get('column') # e.g., "LAnkleAngles/X/deg"
            
            variable_folder_name_for_check = "VariableDesconocida"
            if variable_analyzed_full:
                parts = variable_analyzed_full.split('/')
                variable_folder_name_for_check = " ".join(parts[:2]).replace("/", "_")

            if self.analysis_service.does_continuous_analysis_exist(self.study_id, variable_folder_name_for_check, analysis_name_to_check):
                messagebox.showerror("Nombre Duplicado", 
                                     f"Ya existe un análisis continuo con el nombre '{analysis_name_to_check}' para la variable '{variable_folder_name_for_check}'.\n"
                                     "Por favor, elija un nombre diferente.", 
                                     parent=self)
                # Re-open config dialog with previous values? Or just abort? For now, abort.
                return 
            # --- Fin Validación ---

            try:
                analysis_results = self.analysis_service.perform_continuous_analysis(self.study_id, dialog.result)
                logger.info(f"Resultado de perform_continuous_analysis: {analysis_results}")

                status = analysis_results.get("status", "error")
                message = analysis_results.get("message", "Error desconocido durante el análisis.")
                
                if "error" in status:
                    messagebox.showerror("Error de Análisis Continuo", message, parent=self)
                elif status == "partial_success":
                    messagebox.showwarning("Análisis Continuo Parcial", message, parent=self)
                else: # success
                    success_msg = f"Análisis continuo '{dialog.result.get('analysis_name')}' completado.\n{message}"
                    if analysis_results.get("output_dir"):
                        try:
                            # Try to get a shorter relative path for display
                            study_root_path = self.analysis_service.file_service.project_root
                            output_dir_path = Path(analysis_results.get('output_dir'))
                            relative_output_dir = output_dir_path.relative_to(study_root_path)
                            success_msg += f"\n\nResultados guardados en:\n.../{relative_output_dir}"
                        except Exception: # Fallback to full path if relative fails
                             success_msg += f"\n\nResultados guardados en la carpeta del estudio:\n{analysis_results.get('output_dir')}"
                    
                    plot_path_str = analysis_results.get("continuous_plot_path") # Static PNG
                    interactive_plot_path_str = analysis_results.get("continuous_interactive_plot_path") # Interactive HTML

                    open_static = False
                    open_interactive = False

                    if interactive_plot_path_str and Path(interactive_plot_path_str).exists():
                        if messagebox.askyesno("Análisis Completado",
                                               f"{success_msg}\n\n¿Desea abrir el gráfico interactivo (HTML)?",
                                               parent=self):
                            open_interactive = True
                    elif plot_path_str and Path(plot_path_str).exists(): # Fallback to static if interactive not available/chosen
                        if messagebox.askyesno("Análisis Completado",
                                               f"{success_msg}\n\nEl gráfico interactivo no está disponible o no se generó.\n¿Desea abrir el gráfico estático (PNG)?",
                                               parent=self):
                            open_static = True
                    else: # No plots available or user chose not to open
                        messagebox.showinfo("Análisis Completado", success_msg, parent=self)

                    if open_interactive:
                        plot_to_open = Path(interactive_plot_path_str)
                        open_type = "gráfico interactivo"
                    elif open_static:
                        plot_to_open = Path(plot_path_str)
                        open_type = "gráfico estático"
                    else:
                        plot_to_open = None
                        open_type = ""
                    
                    if plot_to_open:
                        try:
                            if sys.platform == "win32": os.startfile(plot_to_open)
                            elif sys.platform == "darwin": subprocess.run(["open", plot_to_open], check=True)
                            else: subprocess.run(["xdg-open", plot_to_open], check=True)
                        except Exception as e_open:
                            messagebox.showerror("Error", f"No se pudo abrir el {open_type}:\n{e_open}", parent=self)
                            logger.error(f"Error abriendo {open_type} {plot_to_open}: {e_open}", exc_info=True)
                
                self.load_analyses() # Recargar la lista
            except Exception as e:
                logger.critical(f"Excepción al llamar perform_continuous_analysis o procesar su resultado: {e}", exc_info=True)
                messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado al procesar el análisis continuo:\n{e}", parent=self)
        else:
            logger.info(f"Diálogo de configuración de análisis continuo cancelado para estudio {self.study_id}.")


    def _view_plot(self, event=None): # Add event=None for double-click binding
        selected_items = self.tree.selection()
        if not selected_items or len(selected_items) > 1:
            if not event: # Only show warning if called by button, not double-click
                messagebox.showwarning("Selección Múltiple", "Por favor, seleccione un único análisis para ver su gráfico.", parent=self)
            return

        selected_info_list = self.get_selected_analyses_info()
        if not selected_info_list:
            if not event:
                 messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis para ver su gráfico.", parent=self)
            return
        selected_info = selected_info_list[0]

        if selected_info and selected_info.get("plot_path"):
            plot_path = Path(selected_info["plot_path"])
            if plot_path.exists():
                try:
                    if sys.platform == "win32": os.startfile(plot_path)
                    elif sys.platform == "darwin": subprocess.run(["open", plot_path], check=True)
                    else: subprocess.run(["xdg-open", plot_path], check=True)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir el gráfico:\n{e}", parent=self)
                    logger.error(f"Error abriendo gráfico {plot_path}: {e}", exc_info=True)
            else:
                messagebox.showwarning("Archivo no encontrado", "El archivo del gráfico SPM no existe.", parent=self)
        elif event: # If called by double-click but no plot
             pass # Do nothing if double-click on item without plot
        else: # Called by button
            messagebox.showinfo("Información", "No hay gráfico SPM (PNG) para el análisis seleccionado o el análisis no está seleccionado.", parent=self)

    def _view_interactive_plot(self):
        selected_items = self.tree.selection()
        if not selected_items or len(selected_items) > 1:
            messagebox.showwarning("Selección Múltiple", "Por favor, seleccione un único análisis para ver su gráfico interactivo.", parent=self)
            return

        selected_info_list = self.get_selected_analyses_info()
        if not selected_info_list:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis para ver su gráfico interactivo.", parent=self)
            return
        selected_info = selected_info_list[0]

        if selected_info and selected_info.get("interactive_plot_path"):
            plot_path = Path(selected_info["interactive_plot_path"])
            if plot_path.exists():
                try:
                    if sys.platform == "win32": os.startfile(plot_path)
                    elif sys.platform == "darwin": subprocess.run(["open", plot_path], check=True)
                    else: subprocess.run(["xdg-open", plot_path], check=True)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir el gráfico interactivo:\n{e}", parent=self)
                    logger.error(f"Error abriendo gráfico interactivo {plot_path}: {e}", exc_info=True)
            else:
                messagebox.showwarning("Archivo no encontrado", "El archivo del gráfico interactivo SPM no existe.", parent=self)
        else:
            messagebox.showinfo("Información", "No hay gráfico interactivo SPM para el análisis seleccionado o el análisis no está seleccionado.", parent=self)

    def _view_config(self):
        selected_items = self.tree.selection()
        if not selected_items or len(selected_items) > 1:
            messagebox.showwarning("Selección Múltiple", "Por favor, seleccione un único análisis para ver su configuración.", parent=self)
            return

        selected_info_list = self.get_selected_analyses_info()
        if not selected_info_list:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis para ver su configuración.", parent=self)
            return
        selected_info = selected_info_list[0]

        if selected_info and selected_info.get("config_path"):
            config_path = Path(selected_info["config_path"])
            if config_path.exists():
                try:
                    # Correctly get the config dictionary from selected_info
                    config_data = selected_info.get("config") 
                    
                    # Correctly get the config dictionary from selected_info
                    config_data = selected_info.get("config")
                    analysis_name = selected_info.get("name", "configuracion_desconocida")
                    analysis_folder_path = selected_info.get("path") # This is the Path object to the analysis folder

                    if not config_data:
                        messagebox.showerror("Error", "No hay datos de configuración para mostrar.", parent=self)
                        return
                    if not analysis_folder_path:
                        messagebox.showerror("Error", "No se pudo determinar la carpeta del análisis.", parent=self)
                        return

                    # --- Generate Text Content ---
                    text_lines = []
                    text_lines.append(f"Configuración del Análisis: {analysis_name}\n")
                    text_lines.append("=" * (len(text_lines[0]) -1) + "\n") # Underline for the title

                    aliases = self.main_window.study_service.get_study_aliases(self.study_id)
                    key_translations = {
                        "analysis_name": "Nombre del Análisis", "data_type": "Tipo de Dato",
                        "column": "Variable Analizada", "grouping_mode": "Modo de Agrupación",
                        "primary_vi_name": "VI Primaria (Modo 1VI)",
                        "fixed_vi_name": "VI Fija (Modo 2VIs)",
                        "fixed_descriptor_display": "Valor Fijo de VI (Modo 2VIs)",
                        "groups": "Grupos Comparados",
                        "show_std_dev": "Mostrar Desviación Estándar (DE)",
                        "show_conf_int": "Mostrar Intervalos de Confianza (IC)",
                        "show_sem": "Mostrar Error Estándar de la Media (EEM)",
                        "annotate_spm_clusters_bottom": "Anotar Clusters SPM (Gráfico Inferior)",
                        "annotate_spm_range_top": "Anotar Rango SPM (Gráfico Superior)",
                        "delimit_time_range": "Delimitar Rango de Tiempo Mostrado",
                        "time_min": "Tiempo Mínimo (%)", "time_max": "Tiempo Máximo (%)",
                        "show_full_time_with_delimiters": "Mostrar Tiempo Completo con Delimitadores",
                        "add_time_range_label": "Añadir Etiqueta de Rango de Tiempo",
                        "time_range_label_text": "Texto de Etiqueta de Rango de Tiempo"
                    }
                    display_order = [
                        "analysis_name", "data_type", "column", "grouping_mode",
                        "primary_vi_name", "fixed_vi_name", "fixed_descriptor_display", "groups",
                        "show_std_dev", "show_conf_int", "show_sem",
                        "annotate_spm_clusters_bottom", "annotate_spm_range_top",
                        "delimit_time_range", "time_min", "time_max",
                        "show_full_time_with_delimiters", "add_time_range_label", "time_range_label_text"
                    ]

                    for key in display_order:
                        if key not in config_data: continue
                        translated_key = key_translations.get(key, key)
                        raw_value = config_data.get(key)
                        display_value_str = ""

                        if isinstance(raw_value, bool):
                            display_value_str = "Sí" if raw_value else "No"
                        elif key == "groups":
                            group_display_parts = []
                            mode = config_data.get('grouping_mode')
                            primary_vi = config_data.get('primary_vi_name')
                            fixed_vi = config_data.get('fixed_vi_name')
                            fixed_desc_original = None
                            if config_data.get('fixed_descriptor_display'):
                                fixed_desc_original = config_data.get('fixed_descriptor_display').split(" (")[0]

                            for group_key_item in raw_value: # raw_value is list of group keys
                                if mode == "1VI" and primary_vi:
                                    try:
                                        _, desc_val = group_key_item.split("=", 1)
                                        alias = aliases.get(desc_val, desc_val)
                                        group_display_parts.append(f"{primary_vi}: {alias}")
                                    except ValueError: group_display_parts.append(group_key_item)
                                elif mode == "2VIs" and fixed_vi and fixed_desc_original:
                                    # This logic is from the Treeview display, adapt for text file
                                    fixed_pair_str_to_match = f"{fixed_vi}={fixed_desc_original}"
                                    fixed_vi_alias = aliases.get(fixed_desc_original, fixed_desc_original)
                                    formatted_fixed_part = f"{fixed_vi}: {fixed_vi_alias}"
                                    
                                    variable_part_display_segments = []
                                    for part_of_full_key in group_key_item.split(';'):
                                        if part_of_full_key != fixed_pair_str_to_match:
                                            try:
                                                vi_name_var, desc_val_var = part_of_full_key.split('=',1)
                                                alias_var = aliases.get(desc_val_var, desc_val_var)
                                                variable_part_display_segments.append(f"{vi_name_var}: {alias_var}")
                                            except ValueError: 
                                                variable_part_display_segments.append(part_of_full_key)
                                    if variable_part_display_segments:
                                        full_display_for_group = f"{formatted_fixed_part}, {', '.join(variable_part_display_segments)}"
                                        group_display_parts.append(full_display_for_group)
                                    else:
                                        group_display_parts.append(formatted_fixed_part)
                                else: # Combined mode or fallback
                                    parts = []
                                    for item_part in group_key_item.split(';'):
                                        try:
                                            vi_name_iter, desc_val_iter = item_part.split('=',1)
                                            alias_iter = aliases.get(desc_val_iter, desc_val_iter)
                                            parts.append(f"{vi_name_iter}: {alias_iter}")
                                        except ValueError: parts.append(item_part)
                                    group_display_parts.append(" & ".join(parts)) # Keep " & " for combined parts of one group
                            # Join the formatted group display parts with " vs "
                            display_value_str = " vs ".join(group_display_parts) if group_display_parts else "N/A"
                        elif raw_value is None:
                            display_value_str = "No especificado"
                        else:
                            display_value_str = str(raw_value)
                        
                        # Format as "Key: Value"
                        if key == "groups" and "\n" in display_value_str: # Handle multi-line groups
                            group_lines = display_value_str.split("\n")
                            text_lines.append(f"{translated_key}: {group_lines[0]}")
                            for group_line in group_lines[1:]:
                                text_lines.append(f"  {group_line}") # Indent subsequent group lines
                        else:
                            text_lines.append(f"{translated_key}: {display_value_str}")

                    # --- Add Claves de Archivo Completas Contribuyentes por Grupo Comparado ---
                    text_lines.append("\n" + "-" * 40)
                    text_lines.append("Claves de Archivo Completas Contribuyentes por Grupo Comparado:")
                    text_lines.append("-" * 40)

                    # config_data['groups'] for continuous analysis:
                    #   - 1VI mode: stores *effective partial keys* (e.g., ["Edad=Adulto", "Edad=Mayor"])
                    #   - 2VI mode: stores *full keys* (e.g., ["Peso=OS;Edad=Adulto", "Peso=OS;Edad=Mayor"])
                    comparison_groups_keys_cont = config_data.get('groups', [])
                    mode_cfg_cont = config_data.get('grouping_mode')
                    primary_vi_cfg_cont = config_data.get('primary_vi_name')
                    fixed_vi_cfg_cont = config_data.get('fixed_vi_name')
                    fixed_desc_display_cfg_cont = config_data.get('fixed_descriptor_display')
                    frequency_cfg_cont = config_data.get('data_type', 'Cinematica') # 'data_type' in continuous config

                    # Get the display names for these comparison groups
                    formatted_comparison_groups_display_cont = self._format_analysis_groups_for_display(
                        comparison_groups_keys_cont, mode_cfg_cont, primary_vi_cfg_cont,
                        fixed_vi_cfg_cont, fixed_desc_display_cfg_cont
                    )

                    if not comparison_groups_keys_cont:
                        text_lines.append("  No se definieron grupos para la comparación.")
                    else:
                        for i, comp_group_key_from_config_cont in enumerate(comparison_groups_keys_cont):
                            required_parts_for_lookup_cont = []
                            if mode_cfg_cont == '1VI':
                                # comp_group_key_from_config_cont is the partial key, e.g., "Edad=Adulto"
                                required_parts_for_lookup_cont = [comp_group_key_from_config_cont]
                            else: # 2VIs mode
                                # comp_group_key_from_config_cont is a full key, e.g., "Peso=OS;Edad=Adulto"
                                required_parts_for_lookup_cont = comp_group_key_from_config_cont.split(';')
                            
                            contributing_full_keys_cont = self.analysis_service._get_contributing_full_keys(
                                self.study_id, frequency_cfg_cont, required_parts_for_lookup_cont
                            )

                            current_comparison_group_display_name_cont = formatted_comparison_groups_display_cont[i] if i < len(formatted_comparison_groups_display_cont) else comp_group_key_from_config_cont
                            text_lines.append(f"\n  Para Grupo Comparado '{current_comparison_group_display_name_cont}':")
                            if contributing_full_keys_cont:
                                for cfk_idx_cont, full_key_cont in enumerate(contributing_full_keys_cont):
                                    text_lines.append(f"    - {full_key_cont}")
                            else:
                                text_lines.append("    (No se encontraron archivos contribuyentes con estas VIs exactas)")
                    
                    # Add other parameters from JSON
                    text_lines.append("\n" + "-" * 40)
                    text_lines.append("Otros Parámetros (desde JSON)")
                    text_lines.append("-" * 40 + "\n")
                    other_params_added = False
                    for key, value in config_data.items():
                        if key not in display_order:
                            translated_key = key_translations.get(key, key.replace("_", " ").capitalize())
                            text_lines.append(f"{translated_key}: {value}")
                            other_params_added = True
                    if not other_params_added:
                        text_lines.append("(Ninguno)")
                    
                    text_content = "\n".join(text_lines)

                    # --- Save to Text File ---
                    # analysis_folder_path is already a Path object
                    txt_config_path = analysis_folder_path / "configuracion_detallada.txt" # Changed extension
                    with open(txt_config_path, 'w', encoding='utf-8') as f_txt:
                        f_txt.write(text_content)
                    
                    logger.info(f"Archivo de configuración de texto generado en: {txt_config_path}")

                    # --- Open the Text File ---
                    try:
                        if sys.platform == "win32": os.startfile(txt_config_path)
                        elif sys.platform == "darwin": subprocess.run(["open", txt_config_path], check=True)
                        else: subprocess.run(["xdg-open", txt_config_path], check=True)
                    except Exception as e_open:
                        messagebox.showerror("Error al Abrir", f"No se pudo abrir el archivo de configuración de texto:\n{txt_config_path}\n\nError: {e_open}", parent=self)
                        logger.error(f"Error abriendo archivo de texto {txt_config_path}: {e_open}", exc_info=True)
                
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo generar o mostrar el archivo de configuración:\n{e}", parent=self)
                    logger.error(f"Error generando/mostrando config de texto para {config_path}: {e}", exc_info=True)
            else:
                messagebox.showwarning("Archivo no encontrado", "El archivo de configuración JSON original no existe.", parent=self)
        else:
            messagebox.showinfo("Información", "No hay archivo de configuración para el análisis seleccionado o el análisis no está seleccionado.", parent=self)

    def _open_folder(self):
        selected_items = self.tree.selection()
        if not selected_items or len(selected_items) > 1:
            messagebox.showwarning("Selección Múltiple", "Por favor, seleccione un único análisis para abrir su carpeta.", parent=self)
            return

        selected_info_list = self.get_selected_analyses_info()
        if not selected_info_list:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis para abrir su carpeta.", parent=self)
            return
        selected_info = selected_info_list[0]

        if selected_info and selected_info.get("path"):
            folder_path = Path(selected_info["path"])
            if folder_path.exists() and folder_path.is_dir():
                # Use main_window.open_folder if available, otherwise direct call
                if hasattr(self.main_window, 'open_folder') and callable(self.main_window.open_folder):
                    self.main_window.open_folder(str(folder_path))
                else: # Fallback if main_window.open_folder is not available
                    try:
                        if sys.platform == "win32": os.startfile(folder_path)
                        elif sys.platform == "darwin": subprocess.run(["open", folder_path], check=True)
                        else: subprocess.run(["xdg-open", folder_path], check=True)
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{e}", parent=self)
                        logger.error(f"Error abriendo carpeta {folder_path}: {e}", exc_info=True)
            else:
                messagebox.showwarning("Carpeta no encontrada", "La carpeta del análisis no existe.", parent=self)
        else:
            messagebox.showinfo("Información", "No hay carpeta para el análisis seleccionado o el análisis no está seleccionado.", parent=self)

    def _confirm_delete_selected_analyses(self):
        """Muestra confirmación y elimina los análisis continuos seleccionados."""
        selected_analyses_info = self.get_selected_analyses_info()
        if not selected_analyses_info:
            messagebox.showwarning("Sin Selección", "No hay análisis seleccionados para eliminar.", parent=self)
            return

        num_selected = len(selected_analyses_info)
        # analysis_names = [info.get('name', 'Desconocido') for info in selected_analyses_info] # No longer needed for message
        
        confirm_message = (f"¿Está seguro de que desea eliminar los {num_selected} análisis continuos seleccionados?\n"
                           "Esta acción es IRREVERSIBLE.")

        if messagebox.askyesno("Confirmar Eliminación Múltiple", confirm_message, icon='warning', parent=self):
            paths_to_delete = [info['path'] for info in selected_analyses_info if 'path' in info and isinstance(info['path'], Path)]
            
            if not paths_to_delete:
                messagebox.showerror("Error", "No se pudieron obtener las rutas de los análisis seleccionados.", parent=self)
                return

            success_count, errors = self.analysis_service.delete_selected_continuous_analyses(paths_to_delete)

            if errors:
                error_details = "\n".join(errors[:3])
                if len(errors) > 3:
                    error_details += f"\n... y {len(errors) - 3} más."
                messagebox.showerror("Errores en Eliminación",
                                     f"Se eliminaron {success_count} análisis, pero ocurrieron errores con {len(errors)} análisis:\n{error_details}",
                                     parent=self)
            elif success_count > 0:
                messagebox.showinfo("Éxito", f"{success_count} análisis eliminado(s) correctamente.", parent=self)
            else:
                messagebox.showinfo("Información", "No se eliminó ningún análisis.", parent=self)
            
            self.load_analyses()

    # _delete_analysis (singular) is removed.

    def _open_main_continuous_analyses_folder(self):
        """Abre la carpeta principal de todos los análisis continuos para el estudio."""
        try:
            # _get_continuous_analysis_base_dir returns .../Analisis Continuo
            base_dir = self.analysis_service._get_continuous_analysis_base_dir(self.study_id)
            if base_dir and base_dir.exists():
                if hasattr(self.main_window, 'open_folder') and callable(self.main_window.open_folder):
                    self.main_window.open_folder(str(base_dir))
                else: # Fallback if main_window.open_folder is not available
                    logger.warning("Fallback: self.main_window.open_folder no disponible para carpeta principal, usando os.startfile/open.")
                    if sys.platform == "win32": os.startfile(base_dir)
                    elif sys.platform == "darwin": subprocess.run(["open", base_dir], check=True)
                    else: subprocess.run(["xdg-open", base_dir], check=True)
            elif base_dir:
                 messagebox.showinfo("Información", f"La carpeta principal de análisis continuos ({base_dir.name}) aún no ha sido creada o no contiene análisis.", parent=self)
            else:
                messagebox.showerror("Error", "No se pudo determinar la ruta de la carpeta principal de análisis continuos.", parent=self)
        except Exception as e:
            logger.error(f"Error al intentar abrir carpeta principal de análisis continuos para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir la carpeta principal de análisis continuos:\n{e}", parent=self)

    def _on_close(self, event=None):
        self.destroy()

    def _update_pagination_controls(self, total_items_in_filter):
        """Actualiza los controles de paginación en self.bottom_fixed_pagination_frame."""
        for widget in self.bottom_fixed_pagination_frame.winfo_children(): # Target new frame
            widget.destroy()

        self.total_pages = (total_items_in_filter // self.items_per_page) + \
                           (1 if total_items_in_filter % self.items_per_page else 0)
        self.total_pages = max(1, self.total_pages)

        if self.total_pages <= 1:
            return 

        # --- Left-aligned buttons ---
        first_page_btn_cont = ttk.Button(self.bottom_fixed_pagination_frame, text="<<", command=lambda: self._go_to_page(1),
                                         state=tk.DISABLED if self.current_page == 1 else tk.NORMAL)
        first_page_btn_cont.pack(side=tk.LEFT, padx=2)
        Tooltip(first_page_btn_cont, text="Ir a la primera página.", short_text="Primera.", enabled=self.main_window.settings.enable_hover_tooltips)

        prev_page_btn_cont = ttk.Button(self.bottom_fixed_pagination_frame, text="<", command=lambda: self._go_to_page(self.current_page - 1),
                                        state=tk.DISABLED if self.current_page == 1 else tk.NORMAL)
        prev_page_btn_cont.pack(side=tk.LEFT, padx=2)
        Tooltip(prev_page_btn_cont, text="Ir a la página anterior.", short_text="Anterior.", enabled=self.main_window.settings.enable_hover_tooltips)

        # --- Right-aligned buttons (packed in reverse visual order) ---
        last_page_btn_cont = ttk.Button(self.bottom_fixed_pagination_frame, text=">>", command=lambda: self._go_to_page(self.total_pages),
                                        state=tk.DISABLED if self.current_page == self.total_pages else tk.NORMAL)
        last_page_btn_cont.pack(side=tk.RIGHT, padx=2)
        Tooltip(last_page_btn_cont, text="Ir a la última página.", short_text="Última.", enabled=self.main_window.settings.enable_hover_tooltips)

        next_page_btn_cont = ttk.Button(self.bottom_fixed_pagination_frame, text=">", command=lambda: self._go_to_page(self.current_page + 1),
                                        state=tk.DISABLED if self.current_page == self.total_pages else tk.NORMAL)
        next_page_btn_cont.pack(side=tk.RIGHT, padx=2)
        Tooltip(next_page_btn_cont, text="Ir a la página siguiente.", short_text="Siguiente.", enabled=self.main_window.settings.enable_hover_tooltips)

        # --- Center-aligned label (fills remaining space) ---
        page_info_label_cont = ttk.Label(self.bottom_fixed_pagination_frame, text=f"Página {self.current_page} de {self.total_pages}")
        page_info_label_cont.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)


    def _go_to_page(self, page_number):
        """Navega a una página específica y repopula el treeview."""
        if 1 <= page_number <= self.total_pages:
            self.current_page = page_number
            self._apply_filters_and_search() # This will repopulate based on current filters and new page
        else:
            logger.warning(f"Intento de ir a página inválida {page_number} (Total: {self.total_pages})")


# Dummy main for testing
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Dummy Main Window for Manager")
    # root.geometry("900x700")

    class DummyStudyService:
        def get_study_details(self, study_id): return {'aliases': {}}
        def get_study_aliases(self, study_id): return {'CMJ': 'Salto CMJ', 'PRE': 'Antes'}

    class DummyFileService:
        def _get_study_path(self, study_id): return Path(f"/tmp/study_{study_id}")

    class DummyAnalysisService:
        def __init__(self):
            self.study_service = DummyStudyService()
            self.file_service = DummyFileService()
            self.continuous_analyses_store = {}

        def list_continuous_analyses(self, study_id):
            logger.info(f"Dummy Manager: list_continuous_analyses para estudio {study_id}")
            base_path = self.file_service._get_study_path(study_id) / "Analisis Continuo"
            if study_id not in self.continuous_analyses_store:
                 self.continuous_analyses_store[study_id] = {}
                 for i in range(1, 3):
                    name = f"SPM_Managed_Test_{i}"
                    analysis_path = base_path / name; analysis_path.mkdir(parents=True, exist_ok=True)
                    config_data = {"analysis_name": name, "column": f"Var{i}", "groups": [f"G{i}A", f"G{i}B"], "grouping_mode": "1VI", "primary_vi_name": "Cond", "mtime": datetime.now().timestamp() - (i * 3600)}
                    with open(analysis_path / "config_continuous.json", 'w') as f: json.dump(config_data, f)
                    (analysis_path / "spm_plot.png").touch()
                    (analysis_path / "spm_plot_interactive.html").touch() # Dummy interactive plot
                    self.continuous_analyses_store[study_id][name] = {
                        'name': name, 'path': analysis_path, 'config': config_data, 
                        'mtime': config_data['mtime'], 
                        'plot_path': analysis_path / "spm_plot.png", 
                        'interactive_plot_path': analysis_path / "spm_plot_interactive.html",
                        'config_path': analysis_path / "config_continuous.json"
                    }
            return list(self.continuous_analyses_store.get(study_id, {}).values())

        def delete_continuous_analysis(self, study_id, analysis_name):
            logger.info(f"Dummy Manager: delete_continuous_analysis ({study_id}, {analysis_name})")
            # Simplified deletion for dummy
            if study_id in self.continuous_analyses_store and analysis_name in self.continuous_analyses_store[study_id]:
                del self.continuous_analyses_store[study_id][analysis_name]
            else: raise FileNotFoundError("Not found in dummy store")
        
        def perform_continuous_analysis(self, study_id, config): # Needed by _open_new_analysis_dialog
            logger.info(f"Dummy Manager: perform_continuous_analysis for {study_id} with {config}")
            name = config.get("analysis_name")
            if not name: return {"status": "error", "message": "Dummy: Name required."}
            # Simulate saving
            if study_id not in self.continuous_analyses_store: self.continuous_analyses_store[study_id] = {}
            base_path = self.file_service._get_study_path(study_id) / "Analisis Continuo"
            analysis_path = base_path / name; analysis_path.mkdir(parents=True, exist_ok=True)
            config['mtime'] = datetime.now().timestamp()
            with open(analysis_path / "config_continuous.json", 'w') as f: json.dump(config, f)
            (analysis_path / "spm_plot.png").touch()
            (analysis_path / "spm_plot_interactive.html").touch() # Dummy interactive plot
            self.continuous_analyses_store[study_id][name] = {
                'name': name, 'path': analysis_path, 'config': config, 
                'mtime': config['mtime'], 
                'plot_path': analysis_path / "spm_plot.png",
                'interactive_plot_path': analysis_path / "spm_plot_interactive.html",
                'config_path': analysis_path / "config_continuous.json"
            }
            return {"status": "success", "message": "Dummy analysis completed.", 
                    "output_dir": str(analysis_path),
                    "continuous_plot_path": str(analysis_path / "spm_plot.png"),
                    "continuous_interactive_plot_path": str(analysis_path / "spm_plot_interactive.html")}

        # Methods for ContinuousAnalysisConfigDialog
        def get_available_frequencies_for_study(self, study_id): return ["Cinematica"]
        def get_data_columns_for_frequency(self, study_id, frequency): return ["LAnkleAngles/X/deg", "RKneeAngles/Y/deg"]
        def get_filtered_discrete_analysis_groups(self, study_id, frequency, mode, primary_vi_name=None, fixed_vi_name=None, fixed_descriptor_value=None):
            if mode == "1VI": return {f"{primary_vi_name}=A": f"{primary_vi_name}: A", f"{primary_vi_name}=B": f"{primary_vi_name}: B"}
            return {}

    class DummyMainWindowForManager: # To act as parent.master
        def __init__(self):
            self.study_service = DummyStudyService()
        def open_folder(self, path_str): logger.info(f"DummyMainWindowForManager: open_folder({path_str})")

    # Setup for the dialog
    dummy_main_window_ref = DummyMainWindowForManager()
    # The dialog's parent is root, its master (for main_window access) is dummy_main_window_ref
    # This is a bit of a hack for testing; in real app, parent is a widget in MainWindow.root
    # So, self.main_window = parent.master would correctly get MainWindow instance.
    # For this dummy, we pass root as parent, and the dialog will try self.parent.master
    # We need to ensure root.master is set.
    # root.master = dummy_main_window_ref # No longer strictly needed for main_window assignment in dialog

    dummy_analysis_service_ref = DummyAnalysisService()
    test_study_id_for_manager = 1
    
    # Button to open the manager dialog
    ttk.Button(root, text="Open Continuous Analysis Manager",
               command=lambda: ContinuousAnalysisManagerDialog(root, dummy_analysis_service_ref, test_study_id_for_manager, main_window_instance=dummy_main_window_ref)
              ).pack(padx=20, pady=20)

    root.mainloop()
