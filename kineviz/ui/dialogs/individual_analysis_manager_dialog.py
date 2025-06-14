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


logger = logging.getLogger(__name__)


class IndividualAnalysisManagerDialog(tk.Toplevel):
    """Diálogo para gestionar (listar, crear, eliminar) análisis individuales."""

    def __init__(self, parent, analysis_service: AnalysisService, study_id: int):
        super().__init__(parent)
        self.parent = parent
        self.analysis_service = analysis_service
        self.study_id = study_id

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
        self.filter_vi1_name_var = tk.StringVar()
        self.filter_vi1_desc_var = tk.StringVar()
        self.filter_vi2_name_var = tk.StringVar()
        self.filter_vi2_desc_var = tk.StringVar()

        # Column definitions
        self.columns = ("Nombre", "Fecha", "Tipo de Dato", "Cálculo",
                        "Columna Analizada", "Supuestos", "Valores Clave",
                        "Grupos Comparados")

        self._load_study_vi_data() # Load VIs and aliases for filters
        self.create_widgets()
        self._populate_filter_vi_comboboxes() # Populate VI comboboxes after widgets are created
        self.load_analyses() # This will now fetch all and then apply current (empty) filters

    def create_widgets(self):
        """Crea los widgets del diálogo."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(2, weight=1)  # Adjust row for treeview expansion
        main_frame.columnconfigure(0, weight=1)

        # --- Search and Filter Frame ---
        search_filter_frame = ttk.LabelFrame(main_frame, text="Buscar y Filtrar Análisis", padding="10")
        search_filter_frame.grid(row=0, column=0, sticky="ew", pady=(0,10))
        search_filter_frame.columnconfigure(1, weight=1)
        search_filter_frame.columnconfigure(3, weight=1)
        search_filter_frame.columnconfigure(5, weight=1)

        # Search
        ttk.Label(search_filter_frame, text="Buscar:").grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")
        search_entry = ttk.Entry(search_filter_frame, textvariable=self.search_term_var, width=30)
        search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        search_entry.bind("<Return>", lambda event: self._apply_filters_and_search())
        ttk.Button(search_filter_frame, text="Buscar", command=self._apply_filters_and_search).grid(row=0, column=2, padx=5, pady=5, sticky="e")

        # Filter by VI count
        ttk.Label(search_filter_frame, text="Filtrar por VIs:").grid(row=1, column=0, padx=(0,5), pady=5, sticky="w")
        self.filter_vi_count_combo = ttk.Combobox(search_filter_frame, textvariable=self.filter_vi_count_var,
                                                  values=["No filtrar", "1 VI", "2 VIs"], state="readonly", width=12)
        self.filter_vi_count_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.filter_vi_count_combo.bind("<<ComboboxSelected>>", self._on_filter_vi_count_change)

        # VI 1 Filter
        self.filter_vi1_frame = ttk.Frame(search_filter_frame)
        self.filter_vi1_frame.grid(row=2, column=0, columnspan=3, pady=5, sticky="ew")
        self.filter_vi1_frame.columnconfigure(1, weight=1)
        self.filter_vi1_frame.columnconfigure(3, weight=1)

        ttk.Label(self.filter_vi1_frame, text="VI 1:").grid(row=0, column=0, padx=(0,5), pady=2, sticky="w")
        self.filter_vi1_name_combo = ttk.Combobox(self.filter_vi1_frame, textvariable=self.filter_vi1_name_var, state="readonly", width=15)
        self.filter_vi1_name_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.filter_vi1_name_combo.bind("<<ComboboxSelected>>", lambda e: self._update_filter_descriptor_combobox(1))
        
        ttk.Label(self.filter_vi1_frame, text="Sub-valor VI 1:").grid(row=0, column=2, padx=(10,5), pady=2, sticky="w")
        self.filter_vi1_desc_combo = ttk.Combobox(self.filter_vi1_frame, textvariable=self.filter_vi1_desc_var, state="readonly", width=15)
        self.filter_vi1_desc_combo.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        # VI 2 Filter (initially hidden)
        self.filter_vi2_frame = ttk.Frame(search_filter_frame)
        self.filter_vi2_frame.grid(row=3, column=0, columnspan=3, pady=5, sticky="ew")
        self.filter_vi2_frame.columnconfigure(1, weight=1)
        self.filter_vi2_frame.columnconfigure(3, weight=1)

        ttk.Label(self.filter_vi2_frame, text="VI 2:").grid(row=0, column=0, padx=(0,5), pady=2, sticky="w")
        self.filter_vi2_name_combo = ttk.Combobox(self.filter_vi2_frame, textvariable=self.filter_vi2_name_var, state="readonly", width=15)
        self.filter_vi2_name_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.filter_vi2_name_combo.bind("<<ComboboxSelected>>", lambda e: self._update_filter_descriptor_combobox(2))

        ttk.Label(self.filter_vi2_frame, text="Sub-valor VI 2:").grid(row=0, column=2, padx=(10,5), pady=2, sticky="w")
        self.filter_vi2_desc_combo = ttk.Combobox(self.filter_vi2_frame, textvariable=self.filter_vi2_desc_var, state="readonly", width=15)
        self.filter_vi2_desc_combo.grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        
        self.filter_vi1_frame.grid_remove() # Hide VI1 frame initially
        self.filter_vi2_frame.grid_remove() # Hide VI2 frame initially

        # Filter Action Buttons
        filter_action_frame = ttk.Frame(search_filter_frame)
        filter_action_frame.grid(row=1, column=2, columnspan=4, sticky="e", padx=5, pady=5) # Adjusted column
        ttk.Button(filter_action_frame, text="Aplicar Filtros", command=self._apply_filters_and_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_action_frame, text="Limpiar Filtros", command=self._clear_filters).pack(side=tk.LEFT, padx=5)

        # --- Acciones (Nuevo Análisis) ---
        new_analysis_frame = ttk.Frame(main_frame)
        new_analysis_frame.grid(row=1, column=0, sticky="ew", pady=(5, 10))
        ttk.Button(new_analysis_frame, text="Nuevo Análisis...",
                   command=self.open_new_analysis_dialog).pack(side=tk.LEFT, padx=0) # No padx needed if it's the only button on left

        # --- Lista de Análisis (Treeview) ---
        tree_frame = ttk.LabelFrame(main_frame, text="Análisis Guardados")
        tree_frame.grid(row=2, column=0, sticky="nsew") # Adjusted row
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Columnas definidas en __init__
        self.analysis_tree = ttk.Treeview(
            tree_frame,
            columns=self.columns, # Usar self.columns
            show="headings"
        )
        self.analysis_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Cabeceras iniciales
        self.analysis_tree.heading("Nombre", text="Nombre Análisis")
        self.analysis_tree.heading("Fecha", text="Fecha Creación")
        self.analysis_tree.heading("Tipo de Dato", text="Tipo de Dato")
        self.analysis_tree.heading("Cálculo", text="Cálculo")
        self.analysis_tree.heading("Columna Analizada", text="Columna")
        self.analysis_tree.heading("Supuestos", text="Supuestos")
        # Añadir cabecera para Valores Clave
        self.analysis_tree.heading("Valores Clave", text="Resultado Test")
        self.analysis_tree.heading("Grupos Comparados", text="Grupos Comparados") # Renombrar Sub-valores

        # Ancho columnas (ajustar según necesidad)
        self.analysis_tree.column("Nombre", width=150, anchor=tk.W)
        self.analysis_tree.column("Fecha", width=140, anchor=tk.CENTER)
        self.analysis_tree.column("Tipo de Dato", width=80, anchor=tk.W)
        self.analysis_tree.column("Cálculo", width=80, anchor=tk.W)
        self.analysis_tree.column("Columna Analizada", width=150, anchor=tk.W)
        self.analysis_tree.column("Supuestos", width=140, anchor=tk.W)
        # Añadir ancho para Valores Clave
        self.analysis_tree.column("Valores Clave", width=120, anchor=tk.W)
        self.analysis_tree.column("Grupos Comparados", width=250, anchor=tk.W) # Renombrar Sub-valores

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.analysis_tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        self.analysis_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.analysis_tree.xview)
        hsb.grid(row=1, column=0, sticky='ew', padx=5) # Añadir padx
        self.analysis_tree.configure(xscrollcommand=hsb.set)
        
        self.analysis_tree.bind("<<TreeviewSelect>>", self._on_selection_changed) # Bind selection event
        self.analysis_tree.bind("<Double-1>", lambda e: self.view_analysis_plot()) # Double click to view plot


        # --- Botones de Acción para Selección ---
        selection_action_frame = ttk.Frame(main_frame)
        selection_action_frame.grid(row=3, column=0, sticky="ew", pady=(10,0))

        self.view_plot_button = ttk.Button(selection_action_frame, text="Ver/Abrir Gráfico", command=self.view_analysis_plot, state=tk.DISABLED)
        self.view_plot_button.pack(side=tk.LEFT, padx=5)
        
        self.view_interactive_button = ttk.Button(selection_action_frame, text="Ver Gráfico Interactivo", command=self.view_interactive_plot, state=tk.DISABLED)
        self.view_interactive_button.pack(side=tk.LEFT, padx=5)

        self.open_folder_button = ttk.Button(selection_action_frame, text="Abrir Carpeta", command=self.open_analysis_folder, state=tk.DISABLED)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(selection_action_frame, text="Eliminar Análisis", command=self.delete_analysis, state=tk.DISABLED)
        self.delete_button.pack(side=tk.RIGHT, padx=5) # Align to right


        # --- Botón Cerrar ---
        ttk.Button(main_frame, text="Cerrar", command=self.destroy) \
            .grid(row=4, column=0, sticky="e", pady=(10, 0)) # Adjusted row

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

            # 2. Apply VI filters
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
        self.filter_vi_count_var.set("No filtrar")
        self._on_filter_vi_count_change()

    def _format_analysis_groups_for_display(self, group_keys: list) -> list[str]:
        """Helper to format group keys for display, using aliases."""
        # group_keys are original keys like "VI1=DescA;VI2=DescB"
        group_display_names = []
        sorted_group_keys = sorted(group_keys) # Sort for consistent display order
        for i, group_key in enumerate(sorted_group_keys):
            display_parts = []
            if group_key != "SinGrupo":
                for part in group_key.split(';'):
                    try:
                        vi_name, desc_value = part.split('=', 1)
                        alias = self.study_aliases.get(desc_value, desc_value)
                        display_parts.append(f"{vi_name}: {alias}")
                    except ValueError:
                        display_parts.append(part) # Fallback
            base_display_name = ", ".join(display_parts) if display_parts else "General"
            full_display_name = f"Grupo {i+1} - {base_display_name}"
            group_display_names.append(full_display_name)
        return group_display_names

    def _populate_treeview(self, analyses_to_display: list):
        """Populates the treeview with the given list of analyses."""
        for item in self.analysis_tree.get_children():
            self.analysis_tree.delete(item)

        self.analysis_tree["columns"] = self.columns
        for col in self.columns:
            header_text = self.analysis_tree.heading(col, 'text') or col
            self.analysis_tree.heading(col, text=header_text)

        if not analyses_to_display:
            num_empty_cols = len(self.columns) - 1
            empty_values = tuple(["No hay análisis que coincidan con los filtros."] + [""] * num_empty_cols)
            self.analysis_tree.insert("", tk.END, text="NoAnalyses", values=empty_values)
        else:
            for analysis_info in analyses_to_display:
                config = analysis_info.get('config', {})
                analysis_name = analysis_info.get('name', 'N/A')
                date_str = "N/A"
                if 'mtime' in analysis_info:
                    date_str = datetime.fromtimestamp(analysis_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')
                freq = config.get('frequency', '?')
                calc = config.get('calculation', '?')
                col_full = config.get('column', '?')
                parametric = config.get('parametric', True)
                paired = config.get('paired', False)
                supuestos_str = (f"{'Pareado' if paired else 'No Pareado'}, "
                                 f"{'Paramétrico' if parametric else 'No Paramétrico'}")
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
                formatted_group_display_list = self._format_analysis_groups_for_display(group_keys_from_config)
                grupos_comparados_str = " vs ".join(formatted_group_display_list)

                values = (analysis_name, date_str, freq, calc, col_full,
                          supuestos_str, valores_clave_str, grupos_comparados_str)
                self.analysis_tree.insert("", tk.END, text=analysis_name, values=values)
        
        self._on_selection_changed() # Update button states based on current selection (if any)

    def load_analyses(self):
        """Carga la lista de análisis individuales guardados y aplica filtros."""
        try:
            self.all_analyses_data = self.analysis_service.list_individual_analyses(self.study_id)
            logger.debug(f"Cargados {len(self.all_analyses_data)} análisis individuales para estudio {self.study_id}.")
        except Exception as e:
             logger.error(f"Error cargando lista de análisis individuales: {e}", exc_info=True)
             messagebox.showerror("Error", f"No se pudo cargar la lista de análisis:\n{e}", parent=self)
             self.all_analyses_data = []
        
        self._apply_filters_and_search()


    def open_new_analysis_dialog(self):
        """Abre el diálogo para configurar un nuevo análisis."""
        dialog = ConfigureIndividualAnalysisDialog(self, self.analysis_service, self.study_id)
        # Esperar a que el diálogo se cierre y luego refrescar la lista
        self.wait_window(dialog)
        self.load_analyses()  # Recargar por si se creó uno nuevo

    def _on_selection_changed(self, event=None):
        """Actualiza el estado de los botones de acción basado en la selección."""
        selected_info = self.get_selected_analysis_info()
        can_act = selected_info is not None
        
        self.view_plot_button.config(state=tk.NORMAL if can_act and selected_info.get("plot_path") else tk.DISABLED)
        self.view_interactive_button.config(state=tk.NORMAL if can_act and selected_info.get("interactive_plot_path") else tk.DISABLED)
        self.open_folder_button.config(state=tk.NORMAL if can_act and selected_info.get("path") else tk.DISABLED)
        self.delete_button.config(state=tk.NORMAL if can_act else tk.DISABLED)


    def get_selected_analysis_info(self) -> dict | None:
        """Obtiene el diccionario de información del análisis seleccionado.
        Retorna None si no hay selección válida, sin mostrar message box.
        """
        selected_item = self.analysis_tree.focus()
        if not selected_item:
            return None # No item focused
        
        analysis_name = self.analysis_tree.item(selected_item, "text")
        if analysis_name == "NoAnalyses":  # Verificar si es el placeholder
            return None # Placeholder is not a valid selection

        # Buscar la info completa en self.all_analyses_data
        for analysis_info in self.all_analyses_data:
            if analysis_info['name'] == analysis_name:
                return analysis_info
        logger.error(f"No se encontró información para análisis seleccionado: "
                      f"{analysis_name}")
        return None

    def view_interactive_plot(self):
        """Abre el gráfico HTML interactivo del análisis seleccionado."""
        analysis_info = self.get_selected_analysis_info()
        if not analysis_info:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis de la lista.", parent=self)
            return

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
        analysis_info = self.get_selected_analysis_info()
        if not analysis_info:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis de la lista.", parent=self)
            return

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

    def delete_analysis(self):
        """Elimina el análisis seleccionado (carpeta y contenido)."""
        analysis_info = self.get_selected_analysis_info()
        if not analysis_info:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis para eliminar.", parent=self)
            return
        analysis_name = analysis_info['name']

        if not messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Está seguro de que desea eliminar permanentemente el "
                f"análisis '{analysis_name}' y todos sus archivos?",
                parent=self):
            return

        try:
            self.analysis_service.delete_individual_analysis(self.study_id,
                                                             analysis_name)
            messagebox.showinfo("Eliminación Exitosa",
                                f"El análisis '{analysis_name}' ha sido eliminado.",
                                parent=self)
            self.load_analyses()  # Recargar lista
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Error al intentar eliminar análisis "
                         f"{analysis_name}: {e}")
            messagebox.showerror("Error al Eliminar", f"{e}", parent=self)
            self.load_analyses()  # Recargar por si el estado cambió
        except Exception as e:
            logger.error(f"Error eliminando análisis {analysis_name}: {e}",
                         exc_info=True)
            messagebox.showerror("Error al Eliminar",
                                   f"No se pudo eliminar el análisis:\n{e}",
                                   parent=self)

    def open_analysis_folder(self):
        """Abre la carpeta que contiene los archivos del análisis."""
        analysis_info = self.get_selected_analysis_info()
        if not analysis_info:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis para abrir su carpeta.", parent=self)
            return

        analysis_dir = analysis_info.get('path')  # Obtener ruta del directorio

        if not analysis_dir or not analysis_dir.exists():
            messagebox.showerror("Error",
                                   f"No se encontró carpeta para análisis "
                                   f"'{analysis_info['name']}'.", parent=self)
            return

        try:
            logger.info(f"Intentando abrir carpeta: {analysis_dir}")
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


# Para pruebas rápidas
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
    dialog = IndividualAnalysisManagerDialog(root, dummy_service, 1)
    root.mainloop()
