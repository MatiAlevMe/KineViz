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
        self.filter_vi1_name_var = tk.StringVar()
        self.filter_vi1_desc_var = tk.StringVar()
        self.filter_vi2_name_var = tk.StringVar()
        self.filter_vi2_desc_var = tk.StringVar()

        self._load_study_vi_data() # Load VIs and aliases for filters
        self.create_widgets()
        self._populate_filter_vi_comboboxes() # Populate VI comboboxes after widgets are created
        self.load_analyses() # This will now fetch all and then apply current (empty) filters

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


    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Search and Filter Frame ---
        search_filter_frame = ttk.LabelFrame(main_frame, text="Buscar y Filtrar Análisis", padding="10")
        search_filter_frame.pack(fill=tk.X, pady=(0,10))
        search_filter_frame.columnconfigure(1, weight=1) # Allow search entry to expand
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
        filter_action_frame.grid(row=1, column=2, columnspan=4, sticky="e", padx=5, pady=5)
        ttk.Button(filter_action_frame, text="Aplicar Filtros", command=self._apply_filters_and_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_action_frame, text="Limpiar Filtros", command=self._clear_filters).pack(side=tk.LEFT, padx=5)


        # --- Header and New Analysis Button ---
        list_header_frame = ttk.Frame(main_frame) # Renamed from header_frame
        list_header_frame.pack(fill=tk.X, pady=(5,10)) # Added top padding
        ttk.Label(list_header_frame, text="Análisis Continuos Guardados:", font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        ttk.Button(list_header_frame, text="Nuevo Análisis Continuo...", command=self._open_new_analysis_dialog).pack(side=tk.RIGHT, padx=5)


        # --- Treeview for listing analyses ---
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))

        columns = ("name", "column", "groups", "date")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Nombre Análisis")
        self.tree.heading("column", text="Variable Analizada")
        self.tree.heading("groups", text="Grupos Comparados")
        self.tree.heading("date", text="Fecha Creación/Modif.")

        self.tree.column("name", width=200, anchor=tk.W)
        self.tree.column("column", width=250, anchor=tk.W)
        self.tree.column("groups", width=300, anchor=tk.W)
        self.tree.column("date", width=150, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_analysis_selected)
        self.tree.bind("<Double-1>", self._view_plot) # Double click to view plot

        # --- Action Buttons ---
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(5,0))

        self.view_plot_button = ttk.Button(action_frame, text="Ver Gráfico SPM", command=self._view_plot, state=tk.DISABLED)
        self.view_plot_button.pack(side=tk.LEFT, padx=5)

        self.view_config_button = ttk.Button(action_frame, text="Ver Configuración", command=self._view_config, state=tk.DISABLED)
        self.view_config_button.pack(side=tk.LEFT, padx=5)

        self.open_folder_button = ttk.Button(action_frame, text="Abrir Carpeta", command=self._open_folder, state=tk.DISABLED)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(action_frame, text="Eliminar Análisis", command=self._delete_analysis, state=tk.DISABLED)
        self.delete_button.pack(side=tk.RIGHT, padx=5) # Align to right

        # --- Close Button ---
        close_button_frame = ttk.Frame(main_frame) # Separate frame for close button
        close_button_frame.pack(fill=tk.X, pady=(10,0))
        ttk.Button(close_button_frame, text="Cerrar", command=self._on_close).pack(side=tk.RIGHT)


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

            # 2. Apply VI filters
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
        self.filter_vi_count_var.set("No filtrar")
        self._on_filter_vi_count_change() # This will clear sub-filters and re-apply

    def _format_analysis_groups_for_display(self, group_keys, mode, primary_vi, fixed_vi, fixed_desc_display):
        """Helper to format group keys for display, using aliases."""
        group_display_parts = []
        if mode == "1VI" and primary_vi and group_keys:
            for desc_key_part in group_keys: # e.g., "Edad=Joven"
                try:
                    _, desc_val = desc_key_part.split("=",1)
                    alias = self.study_aliases.get(desc_val, desc_val)
                    group_display_parts.append(f"{primary_vi}: {alias}")
                except ValueError: group_display_parts.append(desc_key_part)
        elif mode == "2VIs" and fixed_vi and fixed_desc_display and group_keys:
            fixed_desc_original = self._get_descriptor_original_value(fixed_desc_display)
            fixed_pair_str_to_remove = f"{fixed_vi}={fixed_desc_original}"
            for full_key_of_variable_part in group_keys: # e.g., "Salto=CMJ;Condicion=PRE"
                variable_part_display_inner = []
                for part in full_key_of_variable_part.split(';'):
                    if part != fixed_pair_str_to_remove:
                        try:
                            vi_name_inner, desc_val_inner = part.split('=',1)
                            alias_inner = self.study_aliases.get(desc_val_inner, desc_val_inner)
                            variable_part_display_inner.append(f"{vi_name_inner}: {alias_inner}")
                        except ValueError: variable_part_display_inner.append(part)
                group_display_parts.append(", ".join(variable_part_display_inner))
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
        
        for analysis_info in analyses_to_display:
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
                self.tree.insert("", tk.END, values=(name, column, groups_str, date_str), iid=name)
        
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
        
        self._apply_filters_and_search() # Populate tree with (initially unfiltered) data


    def get_selected_analysis_info(self) -> dict | None:
        selected_items = self.tree.selection()
        if not selected_items:
            return None
        analysis_name = selected_items[0] # This is the iid, which is the analysis name
        # Find the analysis in the master list
        for analysis_info in self.all_analyses_data:
            if analysis_info.get('name') == analysis_name:
                return analysis_info
        logger.warning(f"Análisis seleccionado '{analysis_name}' no encontrado en self.all_analyses_data.")
        return None

    def _on_analysis_selected(self, event=None):
        selected_info = self.get_selected_analysis_info()
        can_act = selected_info is not None
        self.view_plot_button.config(state=tk.NORMAL if can_act and selected_info.get("plot_path") else tk.DISABLED)
        self.view_config_button.config(state=tk.NORMAL if can_act and selected_info.get("config_path") else tk.DISABLED)
        self.open_folder_button.config(state=tk.NORMAL if can_act and selected_info.get("path") else tk.DISABLED)
        self.delete_button.config(state=tk.NORMAL if can_act else tk.DISABLED)

    def _open_new_analysis_dialog(self):
        # This is where ContinuousAnalysisConfigDialog is launched
        dialog = ContinuousAnalysisConfigDialog(self, self.analysis_service, self.study_id) # self (this Toplevel) is the parent
        self.wait_window(dialog) # Ensure manager waits for config dialog to close

        if dialog.result: # This will be checked after dialog closes
            logger.info(f"Configuración recibida del diálogo de análisis continuo: {dialog.result}")
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
                    
                    plot_path_str = analysis_results.get("continuous_plot_path")
                    if plot_path_str and Path(plot_path_str).exists():
                        if messagebox.askyesno("Análisis Completado",
                                               f"{success_msg}\n\n¿Desea abrir el gráfico generado?",
                                               parent=self):
                            plot_path_obj = Path(plot_path_str)
                            try:
                                if sys.platform == "win32": os.startfile(plot_path_obj)
                                elif sys.platform == "darwin": subprocess.run(["open", plot_path_obj], check=True)
                                else: subprocess.run(["xdg-open", plot_path_obj], check=True)
                            except Exception as e_open:
                                messagebox.showerror("Error", f"No se pudo abrir el gráfico:\n{e_open}", parent=self)
                                logger.error(f"Error abriendo gráfico {plot_path_obj}: {e_open}", exc_info=True)
                    else: # No plot path, or plot doesn't exist, or user chose not to open
                        messagebox.showinfo("Análisis Completado", success_msg, parent=self)
                
                self.load_analyses() # Recargar la lista
            except Exception as e:
                logger.critical(f"Excepción al llamar perform_continuous_analysis o procesar su resultado: {e}", exc_info=True)
                messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado al procesar el análisis continuo:\n{e}", parent=self)
        else:
            logger.info(f"Diálogo de configuración de análisis continuo cancelado para estudio {self.study_id}.")


    def _view_plot(self, event=None): # Add event=None for double-click binding
        selected_info = self.get_selected_analysis_info()
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
            messagebox.showinfo("Información", "No hay gráfico SPM para el análisis seleccionado o el análisis no está seleccionado.", parent=self)

    def _view_config(self):
        selected_info = self.get_selected_analysis_info()
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
                                    fixed_pair_to_remove = f"{fixed_vi}={fixed_desc_original}"
                                    variable_parts_inner = []
                                    for part in group_key_item.split(';'):
                                        if part != fixed_pair_to_remove:
                                            try:
                                                vi_n, d_v = part.split('=',1)
                                                a_i = aliases.get(d_v, d_v)
                                                variable_parts_inner.append(f"{vi_n}: {a_i}")
                                            except ValueError: variable_parts_inner.append(part)
                                    group_display_parts.append(", ".join(variable_parts_inner))
                                else: # Combined mode or fallback
                                    parts = []
                                    for item_part in group_key_item.split(';'):
                                        try:
                                            vi_name_iter, desc_val_iter = item_part.split('=',1)
                                            alias_iter = aliases.get(desc_val_iter, desc_val_iter)
                                            parts.append(f"{vi_name_iter}: {alias_iter}")
                                        except ValueError: parts.append(item_part)
                                    group_display_parts.append(" & ".join(parts))
                            display_value_str = ", ".join(group_display_parts) if group_display_parts else "N/A"
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

                    # Add other parameters from JSON
                    text_lines.append("\n" + "=" * (len(text_lines[0]) -1)) # Underline for the other title
                    text_lines.append("\nOtros Parámetros (desde JSON)")
                    text_lines.append("\n" + "-" * len(text_lines[-1]) + "\n") 
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
        selected_info = self.get_selected_analysis_info()
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

    def _delete_analysis(self):
        selected_info = self.get_selected_analysis_info()
        if not selected_info:
            messagebox.showinfo("Información", "Seleccione un análisis para eliminar.", parent=self)
            return

        analysis_name = selected_info.get('name')
        if messagebox.askyesno("Confirmar Eliminación",
                               f"¿Está seguro de que desea eliminar el análisis continuo '{analysis_name}'?\n"
                               "Esta acción no se puede deshacer.",
                               parent=self, icon='warning'):
            try:
                self.analysis_service.delete_continuous_analysis(self.study_id, analysis_name)
                messagebox.showinfo("Éxito", f"Análisis '{analysis_name}' eliminado correctamente.", parent=self)
                self.load_analyses()
            except FileNotFoundError:
                messagebox.showerror("Error", f"No se encontró el análisis '{analysis_name}' para eliminar.", parent=self)
                self.load_analyses()
            except Exception as e:
                logger.error(f"Error eliminando análisis continuo '{analysis_name}': {e}", exc_info=True)
                messagebox.showerror("Error", f"No se pudo eliminar el análisis '{analysis_name}':\n{e}", parent=self)

    def _on_close(self, event=None):
        self.destroy()

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
                    self.continuous_analyses_store[study_id][name] = {'name': name, 'path': analysis_path, 'config': config_data, 'mtime': config_data['mtime'], 'plot_path': analysis_path / "spm_plot.png", 'config_path': analysis_path / "config_continuous.json"}
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
            self.continuous_analyses_store[study_id][name] = {'name': name, 'path': analysis_path, 'config': config, 'mtime': config['mtime'], 'plot_path': analysis_path / "spm_plot.png", 'config_path': analysis_path / "config_continuous.json"}
            return {"status": "success", "message": "Dummy analysis completed.", "output_dir": str(analysis_path)}

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
