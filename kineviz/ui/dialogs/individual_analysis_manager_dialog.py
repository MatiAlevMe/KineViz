import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
import os
import sys
import subprocess
from datetime import datetime # Para formatear fecha
import numpy as np # Importar numpy
import webbrowser # Para abrir HTML

# Importar servicios y otros diálogos necesarios
from kineviz.core.services.analysis_service import AnalysisService
from kineviz.ui.dialogs.configure_individual_analysis_dialog import ConfigureIndividualAnalysisDialog
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # Import font utilities


logger = logging.getLogger(__name__)


class IndividualAnalysisManagerDialog(tk.Toplevel):
    """Diálogo para gestionar (listar, crear, eliminar) análisis individuales."""

    def __init__(self, parent, analysis_service: AnalysisService, study_id: int):
        super().__init__(parent)
        self.parent = parent
        self.analysis_service = analysis_service
        self.study_id = study_id
        self.settings = parent.main_window.settings # Get settings from parent's main_window

        self.title(f"Gestor de Análisis Discretos - Estudio {study_id}")
        self.geometry("950x700") # Adjusted size for filters
        self.grab_set()  # Hacer modal

        self.all_analyses_data = []  # Store all analyses data
        self.analysis_tree = None
        self.study_vis = [] # Store VI definitions for the study
        self.study_aliases = {} # Store aliases for the study

        # Filter related StringVars
        self.search_term_var = tk.StringVar()
        self.filter_vi_count_var = tk.StringVar(value="No filtrar")
        self.current_page = 1 # For pagination
        self.total_pages = 1  # For pagination
        self.items_per_page = parent.main_window.settings.analysis_items_per_page # Get from settings
        self.filter_vi1_name_var = tk.StringVar()
        self.filter_vi1_desc_var = tk.StringVar()
        self.filter_vi2_name_var = tk.StringVar()
        self.filter_vi2_desc_var = tk.StringVar()
        self.filter_variable_var = tk.StringVar(value="Todos") # For Variable Analizada filter
        self.filter_calc_var = tk.StringVar(value="Todos") # For Cálculo filter

        # Column definitions - Updated for new display
        self.columns = ("Nombre Análisis", "Cálculo", "Variable Analizada", "Grupos Comparados",
                        "Valores Clave", "Fecha Creación/Modif.")

        self._load_study_vi_data() # Load VIs and aliases for filters

        # --- Fixed Panes Setup ---
        self.top_fixed_filters_frame = ttk.Frame(self, padding=(10,10,10,0))
        self.top_fixed_filters_frame.pack(side=tk.TOP, fill=tk.X)

        self.bottom_fixed_delete_actions_frame = ttk.Frame(self, padding=(10,5,10,10))
        self.bottom_fixed_delete_actions_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.bottom_fixed_pagination_frame = ttk.Frame(self, padding=(10,5,10,0))
        self.bottom_fixed_pagination_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.bottom_fixed_folder_actions_frame = ttk.Frame(self, padding=(10,5,10,0))
        self.bottom_fixed_folder_actions_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.bottom_fixed_view_actions_frame = ttk.Frame(self, padding=(10,10,10,0))
        self.bottom_fixed_view_actions_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Scrollable Middle Area (Canvas) ---
        canvas_container = ttk.Frame(self)
        canvas_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=0)

        self.canvas = tk.Canvas(canvas_container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        
        self.scrollable_main_frame = ttk.Frame(self.canvas, padding="10")

        self.scrollable_main_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")) if hasattr(self, 'canvas') and self.canvas.winfo_exists() else None
        )
        
        self.canvas_interior_id = self.canvas.create_window((0, 0), window=self.scrollable_main_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.canvas.bind("<Configure>", self._dynamic_canvas_item_width_configure)

        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        # --- End Scrollable Area Setup ---
        
        self.create_widgets() # Populates fixed and scrollable frames
        self._populate_filter_vi_comboboxes() 
        self.load_analyses() 

    def _update_pagination_controls(self, total_items_in_filter):
        """Actualiza los controles de paginación en self.bottom_fixed_pagination_frame."""
        for widget in self.bottom_fixed_pagination_frame.winfo_children(): # Target new frame
            widget.destroy()

        self.total_pages = (total_items_in_filter // self.items_per_page) + \
                           (1 if total_items_in_filter % self.items_per_page else 0)
        self.total_pages = max(1, self.total_pages)

        if self.total_pages <= 1:
            return # No mostrar controles si hay 1 página o menos

        # --- Left-aligned buttons ---
        first_page_btn = ttk.Button(self.bottom_fixed_pagination_frame, text="<<", command=lambda: self._go_to_page(1),
                                    state=tk.DISABLED if self.current_page == 1 else tk.NORMAL)
        first_page_btn.pack(side=tk.LEFT, padx=2)
        Tooltip(first_page_btn, text="Ir a la primera página.", short_text="Primera.", enabled=self.settings.enable_hover_tooltips)

        prev_page_btn = ttk.Button(self.bottom_fixed_pagination_frame, text="<", command=lambda: self._go_to_page(self.current_page - 1),
                                   state=tk.DISABLED if self.current_page == 1 else tk.NORMAL)
        prev_page_btn.pack(side=tk.LEFT, padx=2)
        Tooltip(prev_page_btn, text="Ir a la página anterior.", short_text="Anterior.", enabled=self.settings.enable_hover_tooltips)

        # --- Right-aligned buttons (packed in reverse visual order) ---
        last_page_btn = ttk.Button(self.bottom_fixed_pagination_frame, text=">>", command=lambda: self._go_to_page(self.total_pages),
                                   state=tk.DISABLED if self.current_page == self.total_pages else tk.NORMAL)
        last_page_btn.pack(side=tk.RIGHT, padx=2)
        Tooltip(last_page_btn, text="Ir a la última página.", short_text="Última.", enabled=self.settings.enable_hover_tooltips)

        next_page_btn = ttk.Button(self.bottom_fixed_pagination_frame, text=">", command=lambda: self._go_to_page(self.current_page + 1),
                                   state=tk.DISABLED if self.current_page == self.total_pages else tk.NORMAL)
        next_page_btn.pack(side=tk.RIGHT, padx=2)
        Tooltip(next_page_btn, text="Ir a la página siguiente.", short_text="Siguiente.", enabled=self.settings.enable_hover_tooltips)

        # --- Center-aligned label (fills remaining space) ---
        page_info_label = ttk.Label(self.bottom_fixed_pagination_frame, text=f"Página {self.current_page} de {self.total_pages}")
        page_info_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)


    def _go_to_page(self, page_number):
        """Navega a una página específica y repopula el treeview."""
        if 1 <= page_number <= self.total_pages:
            self.current_page = page_number
            self._apply_filters_and_search() 
        else:
            logger.warning(f"Intento de ir a página inválida {page_number} (Total: {self.total_pages})")

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
        search_filter_frame = ttk.LabelFrame(self.top_fixed_filters_frame, text="Buscar y Filtrar Análisis", padding="10")
        search_filter_frame.pack(fill=tk.X, expand=True)
        search_filter_frame.columnconfigure(1, weight=1)
        search_filter_frame.columnconfigure(3, weight=1)
        search_filter_frame.columnconfigure(5, weight=1)

        # Search
        scaled_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
        ttk.Label(search_filter_frame, text="Buscar:").grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")
        search_entry = ttk.Entry(search_filter_frame, textvariable=self.search_term_var, width=30, font=scaled_font)
        search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        search_entry.bind("<Return>", lambda event: self._apply_filters_and_search())
        # Search button is moved to filter_action_buttons_frame

        # Filter by Cálculo
        ttk.Label(search_filter_frame, text="Cálculo:").grid(row=1, column=0, padx=(0,5), pady=5, sticky="w")
        self.filter_calc_combo = ttk.Combobox(search_filter_frame, textvariable=self.filter_calc_var, state="readonly", width=15, font=scaled_font)
        self.filter_calc_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.filter_calc_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters_and_search())

        # Filter by Variable Analizada
        ttk.Label(search_filter_frame, text="Variable Analizada:").grid(row=2, column=0, padx=(0,5), pady=5, sticky="w")
        self.filter_variable_combo = ttk.Combobox(search_filter_frame, textvariable=self.filter_variable_var, state="readonly", width=40, font=scaled_font)
        self.filter_variable_combo.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.filter_variable_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters_and_search())

        # Filter by VI count
        ttk.Label(search_filter_frame, text="Filtrar por VIs:").grid(row=3, column=0, padx=(0,5), pady=5, sticky="w") # Adjusted row
        self.filter_vi_count_combo = ttk.Combobox(search_filter_frame, textvariable=self.filter_vi_count_var,
                                                  values=["No filtrar", "1 VI", "2 VIs"], state="readonly", width=12, font=scaled_font)
        self.filter_vi_count_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w") # Adjusted row
        self.filter_vi_count_combo.bind("<<ComboboxSelected>>", self._on_filter_vi_count_change)

        # VI 1 Filter
        self.filter_vi1_frame = ttk.Frame(search_filter_frame)
        self.filter_vi1_frame.grid(row=4, column=0, columnspan=3, pady=5, sticky="ew") # Adjusted row
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
        self.filter_vi2_frame.grid(row=5, column=0, columnspan=3, pady=5, sticky="ew") # Adjusted row
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
        filter_action_buttons_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(5,0)) # New row for these buttons
        
        apply_button = ttk.Button(filter_action_buttons_frame, text="Aplicar Filtros", command=self._apply_filters_and_search, style="Celeste.TButton")
        apply_button.pack(side=tk.LEFT, padx=(0,5)) # Adjusted padding
        Tooltip(apply_button, text="Aplicar todos los filtros seleccionados.", short_text="Aplicar filtros.", enabled=self.settings.enable_hover_tooltips)
        
        clear_button = ttk.Button(filter_action_buttons_frame, text="Limpiar Filtros", command=self._clear_filters)
        clear_button.pack(side=tk.LEFT, padx=(0,5))
        Tooltip(clear_button, text="Limpiar todos los filtros y mostrar todos los análisis.", short_text="Limpiar filtros.", enabled=self.settings.enable_hover_tooltips)

        # Spacer to push subsequent buttons to the right
        ttk.Frame(filter_action_buttons_frame).pack(side=tk.LEFT, expand=True, fill=tk.X)

        refresh_button = ttk.Button(filter_action_buttons_frame, text="Refrescar Lista", command=self.load_analyses)
        refresh_button.pack(side=tk.RIGHT, padx=(0,0)) # Rightmost, no right padding from itself
        Tooltip(refresh_button, text="Recargar la lista de análisis guardados.", short_text="Refrescar lista.", enabled=self.settings.enable_hover_tooltips)

        search_button_moved = ttk.Button(filter_action_buttons_frame, text="Buscar", command=self._apply_filters_and_search, style="Celeste.TButton")
        search_button_moved.pack(side=tk.RIGHT, padx=(0,5)) # To the left of Refresh, 5px padding on its right
        Tooltip(search_button_moved, text="Buscar análisis por nombre, cálculo o variable analizada.", short_text="Buscar.", enabled=self.settings.enable_hover_tooltips)


        # --- Lista de Análisis (Treeview) - Goes into self.scrollable_main_frame ---
        tree_frame = ttk.LabelFrame(self.scrollable_main_frame, text="Análisis Guardados")
        tree_frame.pack(fill=tk.BOTH, expand=True) # Pack it to fill the scrollable area
        # tree_frame.rowconfigure(0, weight=1) # Removed to respect treeview height
        tree_frame.columnconfigure(0, weight=1)

        # Columnas definidas en __init__
        self.analysis_tree = ttk.Treeview(
            tree_frame,
            columns=self.columns, # Usar self.columns
            show="headings",
            selectmode="extended", # Permitir selección múltiple
            height=self.items_per_page # Set height
        )
        self.analysis_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Cabeceras iniciales - Updated for new display
        self.analysis_tree.heading("Nombre Análisis", text="Nombre Análisis")
        self.analysis_tree.heading("Cálculo", text="Cálculo") # Added Cálculo
        self.analysis_tree.heading("Variable Analizada", text="Variable Analizada")
        self.analysis_tree.heading("Grupos Comparados", text="Grupos Comparados")
        self.analysis_tree.heading("Valores Clave", text="Resultado Test")
        self.analysis_tree.heading("Fecha Creación/Modif.", text="Fecha Creación/Modif.")


        # Ancho columnas (ajustar según necesidad) - Updated for new display
        self.analysis_tree.column("Nombre Análisis", width=180, anchor=tk.W)
        self.analysis_tree.column("Cálculo", width=80, anchor=tk.W) # Added Cálculo
        self.analysis_tree.column("Variable Analizada", width=220, anchor=tk.W)
        self.analysis_tree.column("Grupos Comparados", width=250, anchor=tk.W)
        self.analysis_tree.column("Valores Clave", width=120, anchor=tk.W)
        self.analysis_tree.column("Fecha Creación/Modif.", width=130, anchor=tk.CENTER)

        # Treeview's own scrollbars are removed. Main canvas scrollbars will be used.
        
        self.analysis_tree.bind("<<TreeviewSelect>>", self._on_selection_changed) 
        self.analysis_tree.bind("<Double-1>", lambda e: self.view_analysis_plot()) 

        # --- Populate Bottom Fixed View Actions Frame ---
        self.view_plot_button = ttk.Button(self.bottom_fixed_view_actions_frame, text="Ver/Abrir Gráfico", command=self.view_analysis_plot, state=tk.DISABLED, style="Green.TButton")
        self.view_plot_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.view_plot_button, text="Abrir el gráfico estático (PNG) del análisis seleccionado.", short_text="Ver gráfico.", enabled=self.settings.enable_hover_tooltips)

        self.view_interactive_button = ttk.Button(self.bottom_fixed_view_actions_frame, text="Ver Gráfico Interactivo", command=self.view_interactive_plot, state=tk.DISABLED, style="Green.TButton")
        self.view_interactive_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.view_interactive_button, text="Abrir el gráfico interactivo (HTML) del análisis seleccionado en un navegador.", short_text="Ver interactivo.", enabled=self.settings.enable_hover_tooltips)

        self.view_config_button = ttk.Button(self.bottom_fixed_view_actions_frame, text="Ver Configuración", command=self._view_config, state=tk.DISABLED, style="Celeste.TButton")
        self.view_config_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.view_config_button, text="Ver la configuración detallada del análisis seleccionado en un archivo de texto.", short_text="Ver config.", enabled=self.settings.enable_hover_tooltips)

        # --- Populate Bottom Fixed Folder Actions Frame ---
        self.open_folder_button = ttk.Button(self.bottom_fixed_folder_actions_frame, text="Abrir Carpeta", command=self.open_analysis_folder, state=tk.DISABLED)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.open_folder_button, text="Abrir la carpeta que contiene los archivos del análisis seleccionado.", short_text="Abrir carpeta análisis.", enabled=self.settings.enable_hover_tooltips)

        self.open_main_discrete_folder_button = ttk.Button(
            self.bottom_fixed_folder_actions_frame,
            text="Abrir Carpeta de Análisis Discretos",
            command=self._open_main_discrete_analyses_folder
        )
        self.open_main_discrete_folder_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.open_main_discrete_folder_button, text="Abrir la carpeta principal donde se guardan todos los análisis discretos individuales de este estudio.", short_text="Abrir carpeta principal.", enabled=self.settings.enable_hover_tooltips)

        ttk.Frame(self.bottom_fixed_folder_actions_frame).pack(side=tk.LEFT, expand=True, fill=tk.X) # Spacer
        
        new_analysis_button = ttk.Button(self.bottom_fixed_folder_actions_frame, text="Nuevo Análisis...", command=self.open_new_analysis_dialog, style="Green.TButton")
        new_analysis_button.pack(side=tk.RIGHT, padx=5)
        Tooltip(new_analysis_button, text="Abrir el diálogo para configurar y generar un nuevo análisis discreto individual.", short_text="Nuevo análisis.", enabled=self.settings.enable_hover_tooltips)

        # --- Populate Bottom Fixed Pagination Frame ---
        # This is done by _update_pagination_controls, which now needs to target self.bottom_fixed_pagination_frame
        # self.pagination_controls_frame is now self.bottom_fixed_pagination_frame

        # --- Populate Bottom Fixed Delete Actions Frame ---
        self.delete_all_button = ttk.Button(
            self.bottom_fixed_delete_actions_frame,
            text="Eliminar Todos los Análisis Discretos",
            command=self._confirm_delete_all_individual_analyses,
            style="Danger.TButton"
        )
        self.delete_all_button.pack(side=tk.LEFT, padx=(0, 5))
        Tooltip(self.delete_all_button, text="Eliminar TODOS los análisis discretos individuales guardados para este estudio. ¡Acción irreversible!", short_text="Eliminar todo.", enabled=self.settings.enable_hover_tooltips)

        self.delete_selected_button = ttk.Button(
            self.bottom_fixed_delete_actions_frame,
            text="Eliminar Seleccionado(s)",
            command=self._confirm_delete_selected_analyses,
            state=tk.DISABLED,
            style="Danger.TButton"
        )
        self.delete_selected_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.delete_selected_button, text="Eliminar los análisis discretos seleccionados en la lista.", short_text="Eliminar selección.", enabled=self.settings.enable_hover_tooltips)

        close_button = ttk.Button(self.bottom_fixed_delete_actions_frame, text="Cerrar", command=self.destroy)
        close_button.pack(side=tk.RIGHT, padx=5)
        Tooltip(close_button, text="Cerrar el gestor de análisis discretos.", short_text="Cerrar.", enabled=self.settings.enable_hover_tooltips)

        # self.delete_all_button = ttk.Button( # OLD
        #     bottom_action_frame,
        # text="Eliminar Todos los Análisis Discretos", # REMOVED ORPHANED LINES
        # command=self._confirm_delete_all_individual_analyses, # REMOVED ORPHANED LINES
        # style="Danger.TButton" # REMOVED ORPHANED LINES
        # ) # REMOVED ORPHANED LINES
        # self.delete_all_button.pack(side=tk.LEFT, padx=(0, 5)) # REMOVED ORPHANED LINES
        
        # self.delete_selected_button = ttk.Button( # OLD
        # bottom_action_frame, # OLD
        # text="Eliminar Seleccionado(s)", # REMOVED ORPHANED LINES
        # command=self._confirm_delete_selected_analyses, # Nuevo método # REMOVED ORPHANED LINES
        # state=tk.DISABLED, # REMOVED ORPHANED LINES
        # style="Danger.TButton" # Usar estilo de peligro # REMOVED ORPHANED LINES
        # ) # REMOVED ORPHANED LINES
        # self.delete_selected_button.pack(side=tk.LEFT, padx=5) # REMOVED ORPHANED LINES

        # El botón individual "Eliminar Análisis" ya no es necesario si "Eliminar Seleccionado(s)" maneja ambos casos.
        # self.delete_button = ttk.Button(bottom_action_frame, text="Eliminar Análisis", command=self.delete_analysis, state=tk.DISABLED) # OLD
        # self.delete_button.pack(side=tk.LEFT, padx=5) # OLD

        # ttk.Button(bottom_action_frame, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT, padx=5) # OLD

        # Set minsize after widgets are created
        self.update_idletasks()
        # Simplified minsize - set a reasonable fixed minimum
        self.minsize(600, 400) 
        # Initial geometry can also be set here if desired, e.g., self.geometry("950x700")


    def _confirm_delete_all_individual_analyses(self):
        """Muestra confirmación y luego elimina todos los análisis individuales."""
        study_name = "ID Desconocido"
        try:
            # Assuming analysis_service has study_service to get details
            study_details = self.analysis_service.study_service.get_study_details(self.study_id)
            study_name = study_details.get('name', f"ID {self.study_id}")
        except Exception:
            logger.error(f"No se pudo obtener el nombre del estudio {self.study_id} para el diálogo de confirmación.")

        if messagebox.askyesno("Confirmar Eliminación Total de Análisis Discretos",
                               f"¿Está SEGURO de que desea eliminar TODOS los análisis discretos individuales guardados "
                               f"para el estudio '{study_name}'?\n\n"
                               "Esta acción es IRREVERSIBLE.",
                               icon='warning', parent=self):
            try:
                deleted_count = self.analysis_service.delete_all_individual_analyses(self.study_id)
                messagebox.showinfo("Eliminación Completada",
                                    f"{deleted_count} análisis individuales han sido eliminados.",
                                    parent=self)
                self.load_analyses() # Recargar la lista
            except Exception as e:
                logger.error(f"Error al eliminar todos los análisis individuales para estudio {self.study_id}: {e}", exc_info=True)
                messagebox.showerror("Error al Eliminar Análisis",
                                     f"Ocurrió un error al eliminar los análisis:\n{e}",
                                     parent=self)

    def _load_study_vi_data(self):
        """Loads VI names and their descriptors for the current study."""
        try:
            details = self.analysis_service.study_service.get_study_details(self.study_id)
            self.study_vis = details.get('independent_variables', [])
            self.study_aliases = self.analysis_service.study_service.get_study_aliases(self.study_id) # Use service method
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
        self._update_filter_descriptor_combobox(1)
        self._update_filter_descriptor_combobox(2)

        if count_mode == "1 VI":
            self.filter_vi1_frame.grid()
            self.filter_vi2_frame.grid_remove()
        elif count_mode == "2 VIs":
            self.filter_vi1_frame.grid()
            self.filter_vi2_frame.grid()
        else: # "No filtrar"
            self.filter_vi1_frame.grid_remove()
            self.filter_vi2_frame.grid_remove()
        self._apply_filters_and_search()

    def _get_descriptor_original_value(self, display_name: str) -> str:
        """Converts a display name (e.g., 'Desc (Alias)') back to original descriptor."""
        if not display_name: return ""
        if " (" in display_name and display_name.endswith(")"):
            original_candidate = display_name.rsplit(" (", 1)[0]
            if self.study_aliases.get(original_candidate) == display_name.rsplit(" (", 1)[1][:-1]:
                return original_candidate
        return display_name

    def _apply_filters_and_search(self):
        search_term = self.search_term_var.get().lower()
        selected_calc_filter = self.filter_calc_var.get() # Get Cálculo filter
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
            config = analysis_info.get('config', {})
            
            # 1. Apply search term
            matches_search = True
            if search_term:
                name_match = search_term in analysis_info.get('name', '').lower()
                calc_match = search_term in config.get('calculation', '').lower()
                column_match = search_term in config.get('column', '').lower()
                
                groups_str_match = False
                if 'groups' in config:
                    formatted_groups = self._format_analysis_groups_for_display(config.get('groups', []))
                    groups_str_match = search_term in (" vs ".join(formatted_groups)).lower()
                
                matches_search = name_match or calc_match or column_match or groups_str_match
            
            if not matches_search:
                continue

            # 2. Apply Variable Analizada filter
            variable_match = True
            if selected_variable_filter != "Todos":
                if config.get('column', '') != selected_variable_filter:
                    variable_match = False
            
            if not variable_match:
                continue

            # 3. Apply Cálculo filter
            calc_match = True
            if selected_calc_filter != "Todos":
                if config.get('calculation', '') != selected_calc_filter:
                    calc_match = False
            
            if not calc_match:
                continue

            # 4. Apply VI filters
            matches_filters = True
            if filter_mode != "No filtrar":
                analysis_config_groups = config.get('groups', []) # List of group keys like "VI1=DescA;VI2=DescB"
                
                if target_filter_key1:
                    key1_found = any(target_filter_key1 in group_key.split(';') for group_key in analysis_config_groups)
                    if not key1_found: matches_filters = False
                
                if matches_filters and filter_mode == "2 VIs" and target_filter_key2:
                    key2_found = any(target_filter_key2 in group_key.split(';') for group_key in analysis_config_groups)
                    if not key2_found: matches_filters = False
            
            if matches_filters:
                filtered_analyses.append(analysis_info)
        
        self._populate_treeview(filtered_analyses)

    def _clear_filters(self):
        self.search_term_var.set("")
        self.filter_calc_var.set("Todos") # Reset Cálculo filter
        self.filter_variable_var.set("Todos")
        self.filter_vi_count_var.set("No filtrar")
        self._on_filter_vi_count_change()

    def _format_analysis_groups_for_display(self, group_keys_from_config: list, mode: str | None, 
                                            primary_vi_name: str | None, 
                                            fixed_vi_name: str | None, 
                                            fixed_descriptor_display: str | None) -> list[str]:
        """
        Formats group keys for display based on the analysis mode.
        Uses self.study_aliases and self._get_descriptor_original_value.
        """
        formatted_parts = []
        for key_from_config in group_keys_from_config:
            if mode == "1VI" and primary_vi_name:
                # key_from_config is a full key, e.g., "VI1=DescA;VI2=DescB"
                # We need to find the part that matches primary_vi_name.
                found_primary_vi_part = False
                for part_of_key in key_from_config.split(';'): # part_of_key is "VI=Desc"
                    try:
                        vi_name_in_part, descriptor_value_in_part = part_of_key.split('=', 1)
                        if vi_name_in_part == primary_vi_name:
                            alias = self.study_aliases.get(descriptor_value_in_part, descriptor_value_in_part)
                            formatted_parts.append(f"{primary_vi_name}: {alias}")
                            found_primary_vi_part = True
                            break # Found the relevant part for this key_from_config
                    except ValueError:
                        # This part_of_key is malformed, log it and continue to the next part
                        logger.warning(f"Modo 1VI: Parte malformada '{part_of_key}' en clave '{key_from_config}'.")
                        continue 
                
                if not found_primary_vi_part:
                    # If the primary VI part was not found in this key_from_config,
                    # this indicates an issue or an unexpected key structure.
                    logger.warning(f"Modo 1VI: VI primaria '{primary_vi_name}' no encontrada en la clave de configuración '{key_from_config}'. Se usará la clave completa como fallback.")
                    # Fallback: format the full key as best as possible
                    display_sub_parts_fallback = []
                    for item_part_fallback in key_from_config.split(';'):
                        try:
                            vi_name_fb, desc_val_fb = item_part_fallback.split('=', 1)
                            alias_fb = self.study_aliases.get(desc_val_fb, desc_val_fb)
                            display_sub_parts_fallback.append(f"{vi_name_fb}: {alias_fb}")
                        except ValueError: 
                            display_sub_parts_fallback.append(item_part_fallback)
                    formatted_parts.append(", ".join(display_sub_parts_fallback) if display_sub_parts_fallback else key_from_config)

            elif mode == "2VIs" and fixed_vi_name and fixed_descriptor_display:
                # key_from_config is a full key, e.g., "VI_Fija=ValorFijo;VI_Variable=ValorVariable"
                fixed_desc_original = self._get_descriptor_original_value(fixed_descriptor_display)
                fixed_pair_str_to_match = f"{fixed_vi_name}={fixed_desc_original}" # The part that IS fixed

                # Format the fixed part once (with alias)
                fixed_vi_alias = self.study_aliases.get(fixed_desc_original, fixed_desc_original)
                formatted_fixed_part = f"{fixed_vi_name}: {fixed_vi_alias}"

                variable_part_display_segments = []
                # Iterate through parts of the full key to find the variable one(s)
                for part_of_full_key in key_from_config.split(';'):
                    if part_of_full_key != fixed_pair_str_to_match: # This is the variable part
                        try:
                            vi_name_var, desc_val_var = part_of_full_key.split('=',1)
                            alias_var = self.study_aliases.get(desc_val_var, desc_val_var)
                            variable_part_display_segments.append(f"{vi_name_var}: {alias_var}")
                        except ValueError: 
                            variable_part_display_segments.append(part_of_full_key) # Fallback
                
                if variable_part_display_segments:
                    # Combine fixed part with variable part(s)
                    full_display_for_group = f"{formatted_fixed_part}, {', '.join(variable_part_display_segments)}"
                    formatted_parts.append(full_display_for_group)
                else: # Should only be the fixed part, which isn't a comparison group itself
                      # This case is unlikely if config['groups'] stores the full keys of the compared groups.
                    formatted_parts.append(formatted_fixed_part) # Fallback
            
            else: # Fallback for "combined" mode or if mode info is missing
                display_sub_parts = []
                for item_part in key_from_config.split(';'):
                    try:
                        vi_name, desc_val = item_part.split('=', 1)
                        alias = self.study_aliases.get(desc_val, desc_val)
                        display_sub_parts.append(f"{vi_name}: {alias}")
                    except ValueError: 
                        display_sub_parts.append(item_part)
                formatted_parts.append(", ".join(display_sub_parts) if display_sub_parts else key_from_config)
        
        return formatted_parts

    def _populate_treeview(self, analyses_to_display: list):
        """Populates the treeview with the given list of analyses."""
        for item in self.analysis_tree.get_children():
            self.analysis_tree.delete(item)

        self.analysis_tree["columns"] = self.columns
        for col_name in self.columns: # Use col_name for clarity
            header_text = self.analysis_tree.heading(col_name, 'text') or col_name
            self.analysis_tree.heading(col_name, text=header_text) # Use col_name here

        # Pagination logic
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        paginated_analyses = analyses_to_display[start_index:end_index]

        if not paginated_analyses and analyses_to_display: # If current page is empty but there is data
            self.current_page = max(1, self.total_pages)
            start_index = (self.current_page - 1) * self.items_per_page
            end_index = start_index + self.items_per_page
            paginated_analyses = analyses_to_display[start_index:end_index]

        if not paginated_analyses:
            num_empty_cols = len(self.columns) - 1
            empty_values = tuple(["No hay análisis que coincidan con los filtros."] + [""] * num_empty_cols)
            self.analysis_tree.insert("", tk.END, text="NoAnalyses", values=empty_values, iid="NoAnalysesPlaceholder")
        else:
            for analysis_info in paginated_analyses:
                config = analysis_info.get('config', {})
                analysis_name = analysis_info.get('name', 'N/A')
                date_str = "N/A"
                if 'mtime' in analysis_info:
                    date_str = datetime.fromtimestamp(analysis_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')
                freq = config.get('frequency', '?')
                calc = config.get('calculation', '?') # Not displayed directly, but used for config view
                col_full = config.get('column', '?') # This is the "Variable Analizada"
                # Supuestos (parametric, paired) are not displayed directly in table, but in config view
                
                stats_results = config.get('stats_results')
                valores_clave_str = "N/A"
                if stats_results:
                    test_name = stats_results.get('test_name', 'Test')
                    p_value = stats_results.get('p_value')
                    if p_value is not None and not isinstance(p_value, str) and not np.isnan(p_value):
                        if p_value < 0.001: p_text = "p < 0.001"
                        else: p_text = f"p = {p_value:.3f}"
                        valores_clave_str = f"{test_name}: {p_text}"
                    elif p_value is not None: valores_clave_str = f"{test_name}: p=NaN"
                    else: valores_clave_str = f"{test_name}: N/A"
                elif 'test_name' in config: valores_clave_str = f"{config.get('test_name', 'Test')}: ?"
                
                group_keys_from_config = config.get('groups', [])
                grouping_mode = config.get('grouping_mode')
                primary_vi_name = config.get('primary_vi_name')
                fixed_vi_name = config.get('fixed_vi_name')
                fixed_descriptor_display = config.get('fixed_descriptor_display')

                formatted_group_display_list = self._format_analysis_groups_for_display(
                    group_keys_from_config, grouping_mode, 
                    primary_vi_name, fixed_vi_name, fixed_descriptor_display
                )
                grupos_comparados_str = " vs ".join(formatted_group_display_list)

                # Values for the new column order
                values = (analysis_name, calc, col_full, grupos_comparados_str, # Added calc
                          valores_clave_str, date_str)
                
                # Use the unique path string as iid
                analysis_path_str = str(analysis_info.get('path', analysis_name)) # Fallback to name if path is missing
                
                final_iid = analysis_path_str
                counter = 0
                while self.analysis_tree.exists(final_iid):
                    counter += 1
                    final_iid = f"{analysis_path_str}_{counter}"
                    logger.warning(f"Duplicate iid detected for individual analysis. Using '{final_iid}' instead of '{analysis_path_str}'. This might indicate an issue with analysis name uniqueness or path retrieval.")

                self.analysis_tree.insert("", tk.END, iid=final_iid, text=analysis_name, values=values)
        
        self._update_pagination_controls(len(analyses_to_display))
        self._on_selection_changed()

    def load_analyses(self):
        """Carga la lista de análisis individuales guardados y aplica filtros."""
        try:
            self.all_analyses_data = self.analysis_service.list_individual_analyses(self.study_id)
            logger.debug(f"Cargados {len(self.all_analyses_data)} análisis individuales para estudio {self.study_id}.")
        except Exception as e:
             logger.error(f"Error cargando lista de análisis individuales: {e}", exc_info=True)
             messagebox.showerror("Error", f"No se pudo cargar la lista de análisis:\n{e}", parent=self)
             self.all_analyses_data = []

        # Populate Variable Analizada filter
        variables = sorted(list(set(
            info.get('config', {}).get('column', '')
            for info in self.all_analyses_data
            if info.get('config', {}).get('column')
        )))
        self.filter_variable_combo['values'] = ["Todos"] + variables

        # Populate Cálculo filter
        calcs = sorted(list(set(
            info.get('config', {}).get('calculation', '')
            for info in self.all_analyses_data
            if info.get('config', {}).get('calculation')
        )))
        self.filter_calc_combo['values'] = ["Todos"] + calcs
        
        self._apply_filters_and_search()
        self._update_pagination_controls(len(self.all_analyses_data)) # Initial pagination setup


    def open_new_analysis_dialog(self):
        """Abre el diálogo para configurar un nuevo análisis."""
        # --- Pre-validation for participant and VI diversity for Discrete Analysis ---
        # This check is against the summary tables.
        # We need at least two distinct groups to compare.
        # The actual check for data sufficiency for specific groups happens later.
        
        # Check 1: Do summary tables exist at all?
        if not self.analysis_service.get_discrete_analysis_tables_path(self.study_id):
            messagebox.showwarning("Sin Tablas de Resumen",
                                   "No hay tablas de resumen (.xlsx) generadas para este estudio.\n\n"
                                   "Por favor, genere las tablas de resumen primero usando el botón "
                                   "'Generar/Actualizar Tablas Resumen' en la vista de 'Análisis Discreto'.",
                                   parent=self)
            return

        # Check 2: Potential for at least two comparison groups.
        # This is a simplified check. A full check would involve looking at actual data.
        # We query available groups for 'Cinematica' (as it's default/always checked) and any calculation.
        # If less than 2 groups can be formed, it's likely not possible to do a comparison.
        try:
            # Use a common calculation type like "Maximo" for this check.
            # The frequency is fixed to "Cinematica" for discrete analysis config.
            available_groups_for_check = self.analysis_service.get_discrete_analysis_groups(
                self.study_id, frequency="Cinematica" 
            )
            if len(available_groups_for_check) < 2:
                messagebox.showwarning("Datos Insuficientes",
                                       "No hay suficientes grupos distintos (basados en VIs y sub-valores) en las tablas de resumen "
                                       "para realizar un análisis comparativo.\n\n"
                                       "Asegúrese de que el estudio tenga datos procesados para al menos dos condiciones/grupos diferentes.",
                                       parent=self)
                return
        except Exception as e_group_check:
            logger.error(f"Error al verificar grupos disponibles para pre-validación de análisis discreto: {e_group_check}", exc_info=True)
            messagebox.showerror("Error de Pre-validación",
                                 f"Ocurrió un error al verificar la disponibilidad de grupos para el análisis:\n{e_group_check}",
                                 parent=self)
            return

        dialog = ConfigureIndividualAnalysisDialog(self, self.analysis_service, self.study_id, self.parent.main_window.settings) # Pass settings
        
        # Check if dialog was destroyed during its __init__ (e.g., if initial data load failed)
        if not dialog.winfo_exists():
            logger.warning("ConfigureIndividualAnalysisDialog was destroyed during initialization. Aborting new analysis configuration.")
            self.load_analyses() # Refresh list in case state changed before dialog fully closed
            return 

        # Esperar a que el diálogo se cierre y luego refrescar la lista
        self.wait_window(dialog)
        
        if dialog.result: # Check if the configuration dialog was accepted
            # --- Validación de Nombre Duplicado ---
            analysis_name_to_check = dialog.result.get('name')
            variable_analyzed_full = dialog.result.get('column') # e.g., "Attribute/Column/Unit"
            
            variable_folder_name_for_check = "VariableDesconocida"
            if variable_analyzed_full:
                parts = variable_analyzed_full.split('/')
                if len(parts) >= 2:
                    variable_folder_name_for_check = " ".join(parts[:2]).replace("/", "_")
                else: # Fallback if format is unexpected
                    variable_folder_name_for_check = variable_analyzed_full.replace("/", "_")


            analysis_creation_proceed = True # Flag to control execution
            if self.analysis_service.does_individual_analysis_exist(self.study_id, variable_folder_name_for_check, analysis_name_to_check):
                messagebox.showerror("Nombre Duplicado", 
                                     f"Ya existe un análisis discreto con el nombre '{analysis_name_to_check}' para la variable '{variable_folder_name_for_check}'.\n"
                                     "Por favor, elija un nombre diferente.", 
                                     parent=self)
                # self.load_analyses() # Moved to the end of the if dialog.result block
                analysis_creation_proceed = False
                # The return statement is removed; flow control relies on analysis_creation_proceed
            
            if analysis_creation_proceed:
                try:
                    # perform_individual_analysis is expected to return a dict with 'plot_path' and 'config_path'
                    analysis_results = self.analysis_service.perform_individual_analysis(self.study_id, dialog.result)
                
                    plot_path_str = analysis_results.get('plot_path')
                    analysis_name = dialog.result.get('name', 'Análisis sin nombre')
                    
                    success_message = f"Análisis discreto '{analysis_name}' completado y guardado."

                    if plot_path_str and Path(plot_path_str).exists():
                        if messagebox.askyesno("Análisis Completado", 
                                               f"{success_message}\n\n¿Desea abrir el gráfico generado?", 
                                               parent=self):
                            plot_path_obj = Path(plot_path_str)
                            try:
                                if sys.platform == "win32": os.startfile(plot_path_obj)
                                elif sys.platform == "darwin": subprocess.run(["open", plot_path_obj], check=True)
                                else: subprocess.run(["xdg-open", plot_path_obj], check=True)
                            except Exception as e_open:
                                messagebox.showerror("Error al Abrir Gráfico", f"No se pudo abrir el gráfico:\n{e_open}", parent=self)
                                logger.error(f"Error abriendo gráfico {plot_path_obj}: {e_open}", exc_info=True)
                    else:
                        messagebox.showinfo("Análisis Completado", success_message, parent=self)

                except FileNotFoundError as fnf_error:
                    logger.error(f"Error al realizar análisis individual (archivo no encontrado): {fnf_error}", exc_info=True)
                    messagebox.showerror("Error de Análisis", f"No se pudo completar el análisis. Archivo requerido no encontrado:\n{fnf_error}", parent=self)
                except ValueError as val_error:
                    logger.error(f"Error de validación o datos al realizar análisis individual: {val_error}", exc_info=True)
                    messagebox.showerror("Error de Análisis", f"No se pudo completar el análisis. Problema con los datos o configuración:\n{val_error}", parent=self)
                except Exception as e:
                    logger.critical(f"Error inesperado al realizar análisis individual: {e}", exc_info=True)
                    messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado al realizar el análisis:\n{e}", parent=self)
        
        self.load_analyses()  # Recargar por si se creó uno nuevo o para reflejar cualquier estado

    def _on_selection_changed(self, event=None):
        """Actualiza el estado de los botones de acción basado en la selección."""
        selected_info_list = self.get_selected_analyses_info() # Corrected method name
        can_act_single = len(selected_info_list) == 1
        can_act_multiple = len(selected_info_list) > 0
        
        self.view_plot_button.config(state=tk.NORMAL if can_act_single and selected_info_list[0].get("plot_path") else tk.DISABLED)
        self.view_config_button.config(state=tk.NORMAL if can_act_single and selected_info_list[0].get("config") else tk.DISABLED)
        self.view_interactive_button.config(state=tk.NORMAL if can_act_single and selected_info_list[0].get("interactive_plot_path") else tk.DISABLED)
        self.open_folder_button.config(state=tk.NORMAL if can_act_single and selected_info_list[0].get("path") else tk.DISABLED)
        self.delete_selected_button.config(state=tk.NORMAL if can_act_multiple else tk.DISABLED)


    def get_selected_analyses_info(self) -> list[dict]:
        """
        Obtiene una lista de diccionarios de información para los análisis seleccionados.
        Retorna lista vacía si no hay selección válida.
        """
        selected_analyses = []
        selected_item_iids = self.analysis_tree.selection() # Obtener todos los iids seleccionados

        if not selected_item_iids:
            return []

        for selected_item_iid in selected_item_iids:
            if selected_item_iid == "NoAnalyses": # Ignorar placeholder
                continue
            
            found_info = None
            # Buscar la info completa en self.all_analyses_data usando el iid (path)
            for analysis_info in self.all_analyses_data:
                analysis_path_str = str(analysis_info.get('path', ''))
                if selected_item_iid == analysis_path_str or selected_item_iid.startswith(f"{analysis_path_str}_"):
                    found_info = analysis_info
                    break
            
            if not found_info: # Fallback por nombre si no se encontró por path
                analysis_name_from_text = self.analysis_tree.item(selected_item_iid, "text")
                for analysis_info in self.all_analyses_data:
                    if analysis_info.get('name') == analysis_name_from_text:
                        logger.warning(f"Selected iid '{selected_item_iid}' matched by name '{analysis_name_from_text}' (fallback). Path might be missing for this item.")
                        found_info = analysis_info
                        break
            
            if found_info:
                selected_analyses.append(found_info)
            else:
                logger.error(f"No se encontró información para análisis seleccionado con iid: {selected_item_iid}")
        
        return selected_analyses

    def _view_config(self):
        """Genera y abre un archivo .txt con la configuración detallada del análisis seleccionado."""
        selected_items = self.analysis_tree.selection()
        if not selected_items or len(selected_items) > 1:
            messagebox.showwarning("Selección Múltiple", "Por favor, seleccione un único análisis para ver su configuración.", parent=self)
            return
        
        # get_selected_analyses_info devuelve una lista, tomar el primer (y único) elemento
        selected_info_list = self.get_selected_analyses_info()
        if not selected_info_list:
             messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis para ver su configuración.", parent=self)
             return
        selected_info = selected_info_list[0]
        if not selected_info:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis para ver su configuración.", parent=self)
            return

        config_data = selected_info.get("config")
        analysis_name_for_file = selected_info.get("name", "configuracion_desconocida")
        analysis_folder_path = selected_info.get("path") # Path object to the analysis folder

        if not config_data:
            messagebox.showerror("Error", "No hay datos de configuración para mostrar.", parent=self)
            return
        if not analysis_folder_path:
            messagebox.showerror("Error", "No se pudo determinar la carpeta del análisis para guardar el archivo de configuración.", parent=self)
            return

        # --- Generate Text Content ---
        text_lines = []
        text_lines.append(f"Configuración del Análisis Discreto: {analysis_name_for_file}\n")
        text_lines.append("=" * (len(text_lines[0]) -1) + "\n")

        # Translations and order for display (adapt from Continuous if needed, or define new)
        key_translations = {
            "name": "Nombre del Análisis",
            "frequency": "Tipo de Dato",
            "calculation": "Cálculo Aplicado",
            "column": "Variable Analizada",
            "groups": "Grupos Comparados", # Removed (Claves Originales)
            "parametric": "Supuesto: Datos Paramétricos",
            "paired": "Supuesto: Muestras Pareadas",
            "grouping_mode": "Modo de Agrupación de VIs",
            "primary_vi_name": "VI Primaria (Modo 1VI)",
            "fixed_vi_name": "VI Fija (Modo 2VIs)",
            "fixed_descriptor_display": "Valor Fijo de VI (Modo 2VIs)",
            "stats_results": "Resultados Estadísticos"
        }
        
        display_order = [
            "name", "frequency", "calculation", "column", "groups", 
            "parametric", "paired", "grouping_mode", 
            "primary_vi_name", "fixed_vi_name", "fixed_descriptor_display",
            "stats_results"
        ]

        for key in display_order:
            if key not in config_data: continue
            translated_key = key_translations.get(key, key.replace("_", " ").capitalize())
            raw_value = config_data.get(key)
            display_value_str = ""

            if isinstance(raw_value, bool):
                display_value_str = "Sí" if raw_value else "No"
            elif key == "groups":
                # For 'groups', show the raw keys and then the formatted display version
                raw_keys_str = ", ".join(raw_value) if isinstance(raw_value, list) else str(raw_value)
                
                # Get formatted display for these groups
                mode_cfg = config_data.get('grouping_mode')
                primary_vi_cfg = config_data.get('primary_vi_name')
                fixed_vi_cfg = config_data.get('fixed_vi_name')
                fixed_desc_display_cfg = config_data.get('fixed_descriptor_display')
                
                formatted_display_list = self._format_analysis_groups_for_display(
                    raw_value, mode_cfg, primary_vi_cfg, fixed_vi_cfg, fixed_desc_display_cfg
                )
                formatted_display_str = " vs ".join(formatted_display_list)
                display_value_str = formatted_display_str # Removed (Claves: {raw_keys_str})
            elif key == "stats_results" and isinstance(raw_value, dict):
                test_name = raw_value.get('test_name', 'N/A')
                p_val = raw_value.get('p_value')
                if p_val is not None and not np.isnan(p_val):
                    p_text = f"p < 0.001" if p_val < 0.001 else f"p = {p_val:.4f}"
                    display_value_str = f"{test_name}: {p_text}"
                elif p_val is not None: # is NaN
                    display_value_str = f"{test_name}: p=NaN (No calculable)"
                else:
                    display_value_str = f"{test_name}: No disponible"
            elif raw_value is None:
                display_value_str = "No especificado"
            else:
                display_value_str = str(raw_value)
            
            text_lines.append(f"{translated_key}: {display_value_str}")
        
        # --- Add Claves de Archivo Completas Contribuyentes por Grupo Comparado ---
        calculation_cfg = config_data.get('calculation', 'Desconocido') # Get the calculation
        text_lines.append("\n" + "-" * 40)
        text_lines.append(f"Claves de Archivo Completas Contribuyentes (para Cálculo: {calculation_cfg}) por Grupo Comparado:")
        text_lines.append("-" * 40)

        comparison_groups_keys = config_data.get('groups', []) # These are the keys defining the comparison groups
        mode_cfg = config_data.get('grouping_mode')
        primary_vi_cfg = config_data.get('primary_vi_name')
        # We need the frequency, which is stored in config_data as 'frequency'
        frequency_cfg = config_data.get('frequency', 'Cinematica') # Default to Cinematica if not found

        formatted_comparison_groups_display = self._format_analysis_groups_for_display(
            comparison_groups_keys, mode_cfg, primary_vi_cfg, 
            config_data.get('fixed_vi_name'), config_data.get('fixed_descriptor_display')
        )

        if not comparison_groups_keys:
            text_lines.append("  No se definieron grupos para la comparación.")
        else:
            for i, comp_group_key_from_config in enumerate(comparison_groups_keys):
                # comp_group_key_from_config is partial for 1VI, full for 2VI/Combined
                
                required_parts_for_lookup = []
                if mode_cfg == '1VI':
                    # comp_group_key_from_config is already the partial key, e.g., "Edad=Adulto"
                    required_parts_for_lookup = [comp_group_key_from_config]
                else: # 2VIs or Combined mode
                    # comp_group_key_from_config is a full key, e.g., "Peso=OS;Edad=Adulto"
                    required_parts_for_lookup = comp_group_key_from_config.split(';')

                contributing_full_keys = self.analysis_service._get_contributing_full_keys(
                    self.study_id, frequency_cfg, required_parts_for_lookup
                )
                
                # Use the formatted display name for this comparison group
                current_comparison_group_display_name = formatted_comparison_groups_display[i] if i < len(formatted_comparison_groups_display) else comp_group_key_from_config
                text_lines.append(f"\n  Para Grupo Comparado '{current_comparison_group_display_name}':")
                if contributing_full_keys:
                    for cfk_idx, full_key in enumerate(contributing_full_keys):
                        text_lines.append(f"    - {full_key}")
                else:
                    text_lines.append("    (No se encontraron archivos contribuyentes con estas VIs exactas)")
        
        # Add any other parameters from config_data not in display_order
        other_params_added = False
        for key, value in config_data.items():
            if key not in display_order:
                if not other_params_added:
                    text_lines.append("\n" + "-" * 40)
                    text_lines.append("Otros Parámetros en Configuración:")
                    text_lines.append("-" * 40)
                    other_params_added = True
                translated_key = key_translations.get(key, key.replace("_", " ").capitalize())
                text_lines.append(f"{translated_key}: {value}")
        
        text_content = "\n".join(text_lines)

        # --- Save to Text File ---
        txt_config_path = analysis_folder_path / "configuracion_detallada_discreto.txt"
        try:
            with open(txt_config_path, 'w', encoding='utf-8') as f_txt:
                f_txt.write(text_content)
            logger.info(f"Archivo de configuración de texto (discreto) generado en: {txt_config_path}")

            # --- Open the Text File ---
            if sys.platform == "win32": os.startfile(txt_config_path)
            elif sys.platform == "darwin": subprocess.run(["open", txt_config_path], check=True)
            else: subprocess.run(["xdg-open", txt_config_path], check=True)
        except Exception as e_open:
            messagebox.showerror("Error al Abrir/Guardar", f"No se pudo abrir/guardar el archivo de configuración:\n{txt_config_path}\n\nError: {e_open}", parent=self)
            logger.error(f"Error abriendo/guardando archivo de texto {txt_config_path}: {e_open}", exc_info=True)


    def view_interactive_plot(self):
        """Abre el gráfico HTML interactivo del análisis seleccionado."""
        selected_items = self.analysis_tree.selection()
        if not selected_items or len(selected_items) > 1:
            messagebox.showwarning("Selección Múltiple", "Por favor, seleccione un único análisis para ver su gráfico interactivo.", parent=self)
            return

        analysis_info_list = self.get_selected_analyses_info()
        if not analysis_info_list:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis de la lista.", parent=self)
            return
        analysis_info = analysis_info_list[0]

        # Buscar la ruta interactiva en la info cargada
        interactive_plot_path_obj = analysis_info.get('interactive_plot_path')

        if not interactive_plot_path_obj or not interactive_plot_path_obj.exists():
            messagebox.showwarning("No Disponible",
                                   f"No se encontró archivo de gráfico interactivo "
                                   f"para '{analysis_info['name']}'.\n"
                                   f"(Es posible que Plotly no esté instalado o "
                                   f"haya fallado la generación).", parent=self)
            return

        try:
            # Convertir Path a string y luego a URL file://
            interactive_plot_url = interactive_plot_path_obj.as_uri()
            logger.info(f"Intentando abrir gráfico interactivo: {interactive_plot_url}")
            webbrowser.open(interactive_plot_url, new=2) # new=2: nueva pestaña si es posible
        except Exception as e:
            logger.error(f"Error abriendo gráfico interactivo para {analysis_info['name']}: "
                         f"{e}", exc_info=True)
            messagebox.showerror("Error al Abrir",
                                   f"No se pudo abrir el gráfico interactivo:\n{e}",
                                   parent=self)

    def view_analysis_plot(self):
        """Abre el gráfico PNG del análisis seleccionado."""
        selected_items = self.analysis_tree.selection()
        if not selected_items or len(selected_items) > 1:
            messagebox.showwarning("Selección Múltiple", "Por favor, seleccione un único análisis para ver su gráfico.", parent=self)
            return
        
        analysis_info_list = self.get_selected_analyses_info()
        if not analysis_info_list:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis de la lista.", parent=self)
            return
        analysis_info = analysis_info_list[0]

        plot_path = analysis_info.get('plot_path')  # Obtener ruta del gráfico

        if not plot_path or not plot_path.exists():
            messagebox.showerror("Error",
                                   f"No se encontró archivo de gráfico para "
                                   f"'{analysis_info['name']}'.", parent=self)
            return

        try:
            logger.info(f"Intentando abrir gráfico: {plot_path}")
            if sys.platform == "win32":
                os.startfile(plot_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", plot_path], check=True)
            else:  # linux variants
                subprocess.run(["xdg-open", plot_path], check=True)
        except Exception as e:
            logger.error(f"Error abriendo gráfico para {analysis_info['name']}: "
                         f"{e}", exc_info=True)
            messagebox.showerror("Error al Abrir",
                                   f"No se pudo abrir el gráfico:\n{e}",
                                   parent=self)

    def _confirm_delete_selected_analyses(self):
        """Muestra confirmación y elimina los análisis seleccionados."""
        selected_analyses_info = self.get_selected_analyses_info() # Lista de dicts
        if not selected_analyses_info:
            messagebox.showwarning("Sin Selección", "No hay análisis seleccionados para eliminar.", parent=self)
            return

        num_selected = len(selected_analyses_info)
        # analysis_names = [info.get('name', 'Desconocido') for info in selected_analyses_info] # No longer needed for message
        
        confirm_message = (f"¿Está seguro de que desea eliminar los {num_selected} análisis seleccionados?\n"
                           "Esta acción es IRREVERSIBLE.")


        if messagebox.askyesno("Confirmar Eliminación Múltiple", confirm_message, icon='warning', parent=self):
            paths_to_delete = [info['path'] for info in selected_analyses_info if 'path' in info and isinstance(info['path'], Path)]
            
            if not paths_to_delete:
                messagebox.showerror("Error", "No se pudieron obtener las rutas de los análisis seleccionados.", parent=self)
                return

            success_count, errors = self.analysis_service.delete_selected_individual_analyses(paths_to_delete)

            if errors:
                error_details = "\n".join(errors[:3]) # Mostrar hasta 3 errores
                if len(errors) > 3:
                    error_details += f"\n... y {len(errors) - 3} más."
                messagebox.showerror("Errores en Eliminación",
                                     f"Se eliminaron {success_count} análisis, pero ocurrieron errores con {len(errors)} análisis:\n{error_details}",
                                     parent=self)
            elif success_count > 0:
                messagebox.showinfo("Éxito", f"{success_count} análisis eliminado(s) correctamente.", parent=self)
            else: # No errors, no successes (e.g. paths_to_delete was empty after filtering)
                messagebox.showinfo("Información", "No se eliminó ningún análisis.", parent=self)
            
            self.load_analyses() # Recargar la lista

    # delete_analysis (singular) is removed as _confirm_delete_selected_analyses handles single and multiple.

    def open_analysis_folder(self):
        """Abre la carpeta que contiene los archivos del análisis."""
        selected_items = self.analysis_tree.selection()
        if not selected_items or len(selected_items) > 1:
            messagebox.showwarning("Selección Múltiple", "Por favor, seleccione un único análisis para abrir su carpeta.", parent=self)
            return

        analysis_info_list = self.get_selected_analyses_info()
        if not analysis_info_list:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis para abrir su carpeta.", parent=self)
            return
        analysis_info = analysis_info_list[0]

        analysis_dir = analysis_info.get('path')  # Obtener ruta del directorio

        if not analysis_dir or not analysis_dir.exists():
            messagebox.showerror("Error",
                                   f"No se encontró carpeta para análisis "
                                   f"'{analysis_info['name']}'.", parent=self)
            return

        try:
            logger.info(f"Intentando abrir carpeta: {analysis_dir}")
            # Access main_window through parent (DiscreteAnalysisView)
            if hasattr(self.parent, 'main_window') and hasattr(self.parent.main_window, 'open_folder'):
                self.parent.main_window.open_folder(str(analysis_dir))
            else: # Fallback if direct open_folder is not available
                logger.warning("Fallback: self.parent.main_window.open_folder no disponible, usando os.startfile/open.")
                if sys.platform == "win32":
                    os.startfile(analysis_dir)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", analysis_dir], check=True)
                else:  # linux variants
                    subprocess.run(["xdg-open", analysis_dir], check=True)
        except Exception as e:
            logger.error(f"Error abriendo carpeta para {analysis_info['name']}: "
                         f"{e}", exc_info=True)
            messagebox.showerror("Error al Abrir",
                                   f"No se pudo abrir la carpeta:\n{e}",
                                   parent=self)

    def _open_main_discrete_analyses_folder(self):
        """Abre la carpeta principal de todos los análisis discretos para el estudio."""
        try:
            # _get_individual_analysis_base_dir returns .../Analisis Discreto/Graficos
            base_dir = self.analysis_service._get_individual_analysis_base_dir(self.study_id)
            if base_dir and base_dir.exists():
                if hasattr(self.parent, 'main_window') and hasattr(self.parent.main_window, 'open_folder'):
                    self.parent.main_window.open_folder(str(base_dir))
                else:
                    logger.warning("Fallback: self.parent.main_window.open_folder no disponible para carpeta principal, usando os.startfile/open.")
                    if sys.platform == "win32": os.startfile(base_dir)
                    elif sys.platform == "darwin": subprocess.run(["open", base_dir], check=True)
                    else: subprocess.run(["xdg-open", base_dir], check=True)
            elif base_dir:
                 messagebox.showinfo("Información", f"La carpeta principal de análisis discretos ({base_dir.name}) aún no ha sido creada o no contiene análisis.", parent=self)
            else:
                messagebox.showerror("Error", "No se pudo determinar la ruta de la carpeta principal de análisis discretos.", parent=self)
        except Exception as e:
            logger.error(f"Error al intentar abrir carpeta principal de análisis discretos para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir la carpeta principal de análisis discretos:\n{e}", parent=self)

if __name__ == '__main__':
    # Necesitamos Path para el dummy
    from pathlib import Path
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal

    # --- Dummies ---
    class DummyAnalysisService:
        # Añadir study_service dummy para get_study_aliases
        def __init__(self):
            class DummyStudyService:
                 def get_study_aliases(self, study_id):
                     print(f"DummyStudyService: get_study_aliases({study_id})")
                     return {'CMJ': 'Salto CM', 'PRE': 'Antes', 'POST': 'Despues',
                             'SJ_TipoA': 'SJ A', 'SJ_TipoB': 'SJ B', 'SJ_TipoC': 'SJ C'}
                 def get_study_details(self, study_id): # Needed for _load_study_vi_data
                     return {'independent_variables': [{'name': 'Condicion', 'descriptors': ['PRE', 'POST']}],
                             'aliases': self.get_study_aliases(study_id)}

            self.study_service = DummyStudyService()

        def list_individual_analyses(self, study_id):
            print(f"Dummy: list_individual_analyses({study_id})")
            # Simular algunos análisis con plot_path e interactive_plot_path
            base = Path(f'/fake/study_{study_id}/Analisis Discreto/Individual')
            analysis1_path = base / 'Comp_Costo_Mortal_Antes_Despues' # Usar alias
            analysis2_path = base / 'Comp_SJ_Tipos'
            analysis3_path = base / 'Sin_Plotly' # Simular uno sin HTML
            # Simular claves de grupo con formato VI=Desc
            return [
                {'name': 'Comp_SaltoCM_Cond', 'path': analysis1_path,
                 'config': {'calculation': 'Maximo',
                            'column': 'H Salto/Alt/cm',
                            'groups': ['Tipo=CMJ;Cond=PRE', 'Tipo=CMJ;Cond=POST'], # Claves nuevas
                            'parametric': True, 'paired': True,
                            'stats_results': {'test_name': 'T-test rel.', 'p_value': 0.0005}},
                 'mtime': 1678886400.0,
                 'plot_path': analysis1_path / 'boxplot.png',
                 'interactive_plot_path': analysis1_path / 'boxplot_interactive.html'},
                {'name': 'Comp_SJ_Tipos', 'path': analysis2_path,
                 'config': {'calculation': 'Rango',
                            'column': 'Art1/VelX/m/s',
                            'groups': ['Tipo=SJ;Cond=TipoA', 'Tipo=SJ;Cond=TipoB', 'Tipo=SJ;Cond=TipoC'], # Claves nuevas
                            'parametric': False, 'paired': False,
                            'stats_results': {'test_name': 'Kruskal', 'p_value': 0.06}},
                 'mtime': 1678972800.0,
                 'plot_path': analysis2_path / 'boxplot.png',
                 'interactive_plot_path': analysis2_path / 'boxplot_interactive.html'},
                 {'name': 'Sin_Plotly', 'path': analysis3_path,
                 'config': {'calculation': 'Minimo',
                            'column': 'Art2/PosY/mm',
                            'groups': ['Cond=PRE', 'Cond=POST'], # Asumiendo solo una VI 'Cond'
                            'parametric': True, 'paired': False,
                            'stats_results': {'test_name': 'T-test indep.', 'p_value': 0.87}},
                 'mtime': 1678999999.0,
                 'plot_path': analysis3_path / 'boxplot.png',
                 'interactive_plot_path': None},
            ]

        # Los dummies de get_discrete_analysis_groups y get_common_columns_for_groups
        # ya están en ConfigureIndividualAnalysisDialog, no se necesitan aquí.

        def delete_individual_analysis(self, study_id, analysis_name):
            # Corregir el print para usar las variables disponibles
            print(f"Dummy: delete_individual_analysis(study_id={study_id}, "
                  f"analysis_name='{analysis_name}')")
            # El return anterior no tenía sentido aquí, lo eliminamos o devolvemos None
            return None

        def perform_individual_analysis(self, study_id, config):
            print(f"Dummy: perform_individual_analysis({study_id}, {config})")
            # Simular éxito y devolver ambas rutas
            fake_path = Path(f'/fake/study_{study_id}/Analisis Discreto/'
                             f'Individual/{config["name"]}')
            # Asegurarse que el dummy devuelva la ruta interactiva
            return {'plot_path': str(fake_path / 'boxplot.png'),
                    'config_path': str(fake_path / 'config.json'),
                    'interactive_plot_path': str(fake_path / 'boxplot_interactive.html')}


        def delete_individual_analysis(self, study_id, analysis_name):
            print(f"Dummy: delete_individual_analysis({study_id}, "
                  f"{analysis_name})")
            # Simular éxito

    # --- Ejecutar Diálogo ---
    dummy_service = DummyAnalysisService()

    # Need a dummy main_window for settings
    class DummyMainWindow:
        def __init__(self):
            class DummySettings:
                analysis_items_per_page = 5 # Example value
            self.settings = DummySettings()
    
    # The parent of IndividualAnalysisManagerDialog is DiscreteAnalysisView,
    # which has a main_window attribute.
    class DummyDiscreteAnalysisView:
        def __init__(self):
            self.main_window = DummyMainWindow()
            # Add a dummy analysis_service to the dummy parent view if needed by dialog's __init__
            self.analysis_service = dummy_service 


    dummy_parent_view = DummyDiscreteAnalysisView()
    dialog = IndividualAnalysisManagerDialog(dummy_parent_view, dummy_service, 1)
    root.mainloop()
