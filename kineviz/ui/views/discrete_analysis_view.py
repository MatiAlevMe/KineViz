import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import subprocess
import sys
import math  # Para ceil en paginación
from pathlib import Path
from datetime import datetime
from kineviz.core.services.analysis_service import AnalysisService
# Importar AppSettings para leer configuración
from kineviz.config.settings import AppSettings
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # Import font utilities


logger = logging.getLogger(__name__)


class DiscreteAnalysisView(ttk.Frame):
    """Vista para gestionar y visualizar el análisis discreto (Fase 6)."""

    def __init__(self, parent, main_window,
                 analysis_service: AnalysisService, study_id: int, settings: AppSettings):
        super().__init__(parent)
        self.parent = parent
        self.main_window = main_window
        self.analysis_service = analysis_service
        self.study_id = study_id
        self.settings = settings # Use passed AppSettings instance
        self.tables_per_page = self.settings.discrete_tables_per_page

        # Estado de UI y datos
        self.tables_tree = None
        self.all_tables_data = [] # Lista para todos los datos de tablas analizadas
        self.filtered_tables_data = [] # Lista para datos después de aplicar filtros
        self.current_page = 1
        self.total_tables = 0
        self.total_pages = 1
        
        # Study VIs and Aliases
        self.study_vis = []
        self.study_aliases = {}

        # Variables de control para filtros y búsqueda
        self.search_var = tk.StringVar()
        self.filter_type_var = tk.StringVar(value="Todos") # Re-add missing filter_type_var
        self.calc_filter_var = tk.StringVar(value="Todos") # Initialize to "Todos"
        # self.format_filter_var no longer needed

        # VI Filter related StringVars
        self.filter_vi_count_var = tk.StringVar(value="No filtrar")
        self.filter_vi1_name_var = tk.StringVar()
        self.filter_vi1_desc_var = tk.StringVar()
        self.filter_vi2_name_var = tk.StringVar()
        self.filter_vi2_desc_var = tk.StringVar()

        # Empaquetar el frame principal (self) - esto lo hace MainWindow
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Top Fixed Frames ---
        self.top_fixed_header_frame = ttk.Frame(self)
        self.top_fixed_header_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        self.top_fixed_actions_frame = ttk.Frame(self)
        self.top_fixed_actions_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        self.top_fixed_filters_frame = ttk.Frame(self)
        self.top_fixed_filters_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        # --- Bottom Fixed Frames (Order of packing matters) ---
        self.bottom_fixed_table_actions_frame = ttk.Frame(self)
        self.bottom_fixed_table_actions_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self.bottom_fixed_pagination_frame = ttk.Frame(self)
        self.bottom_fixed_pagination_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # --- Scrollable Middle Area (Canvas) ---
        canvas_container = ttk.Frame(self) # Takes remaining space
        canvas_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        
        self.scrollable_frame_content = ttk.Frame(self.canvas) # Content goes here

        self.scrollable_frame_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")) if hasattr(self, 'canvas') and self.canvas.winfo_exists() else None
        )
        
        self.canvas_interior_id = self.canvas.create_window((0, 0), window=self.scrollable_frame_content, anchor="nw")
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.canvas.bind("<Configure>", self._dynamic_canvas_item_width_configure) # Bind to make h-scrollbar work

        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self._load_study_vi_data()
        self.create_widgets() 
        self._populate_filter_vi_comboboxes()
        self._fetch_all_table_files_data() 
        self.apply_filters() 

    def create_widgets(self): 
        # create_widgets is called from __init__
        # It populates the pre-defined fixed frames and the scrollable_frame_content.
        self.create_ui_content_discrete_view()

    def _dynamic_canvas_item_width_configure(self, event):
        """
        Adjusts the width of the scrollable_frame_content (canvas window item)
        to be the maximum of its natural content width and the canvas's current width.
        """
        canvas_width = event.width
        if hasattr(self, 'scrollable_frame_content') and self.scrollable_frame_content.winfo_exists():
            self.scrollable_frame_content.update_idletasks()
            content_natural_width = self.scrollable_frame_content.winfo_reqwidth()
        else:
            content_natural_width = canvas_width
            
        effective_width = max(content_natural_width, canvas_width)
        
        if hasattr(self, 'canvas_interior_id') and self.canvas_interior_id and \
           hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.itemconfig(self.canvas_interior_id, width=effective_width)

    def create_ui_content_discrete_view(self): # Removed parent_frame argument
        """Crea los widgets para la vista de análisis discreto."""
        # --- Populate Top Fixed Header Frame ---
        header_frame = ttk.Frame(self.top_fixed_header_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Botón Volver
        back_button = ttk.Button(
            header_frame, text="<< Volver al Estudio",
            command=lambda: self.main_window.show_study_view(self.study_id)
        )
        back_button.pack(side=tk.LEFT, padx=(0, 10))
        Tooltip(back_button, text="Regresar a la vista detallada del estudio.", short_text="Volver al estudio.", enabled=self.settings.enable_hover_tooltips)

        ttk.Label(
            header_frame, text=f"Análisis Discreto - Estudio {self.study_id}",
            style='Header.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 20))

        # --- Populate Top Fixed Actions Frame ---
        action_frame = ttk.Frame(self.top_fixed_actions_frame)
        action_frame.pack(fill=tk.X, pady=0) # No pady for the frame itself, children will have

        generate_tables_button = ttk.Button(
            action_frame, text="Generar/Actualizar Tablas Resumen",
            command=self.generate_tables,
            style="Green.TButton"
        )
        generate_tables_button.pack(side=tk.LEFT, padx=5)
        Tooltip(generate_tables_button, text="Genera o actualiza las tablas de resumen (.xlsx) con cálculos (Max, Min, Rango) para los datos procesados.", short_text="Generar tablas.", enabled=self.settings.enable_hover_tooltips)

        self.open_manager_button = ttk.Button( # Store as instance variable
            action_frame, text="Gestor de Análisis Discretos",
            command=self.open_individual_analysis_manager, style="Green.TButton"
        )
        self.open_manager_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.open_manager_button, text="Abrir el gestor para crear, ver y eliminar análisis discretos individuales (boxplots, tests estadísticos).", short_text="Gestor análisis.", enabled=self.settings.enable_hover_tooltips)

        # TODO: Añadir botón "Reporte General" (Fase 6)

        open_folder_button = ttk.Button(
            action_frame, text="Abrir Carpeta de Tablas Resumen",
            command=self._open_summary_tables_folder
        )
        open_folder_button.pack(side=tk.LEFT, padx=5)
        Tooltip(open_folder_button, text="Abrir la carpeta donde se guardan las tablas de resumen (.xlsx) generadas.", short_text="Abrir carpeta.", enabled=self.settings.enable_hover_tooltips)

        # --- Populate Top Fixed Filters Frame ---
        filter_frame = ttk.Frame(self.top_fixed_filters_frame)
        filter_frame.pack(fill=tk.X, pady=0)
        filter_frame.columnconfigure(1, weight=1) 

        # Row 0: Search and main non-VI filters (Tipo de Dato, Cálculo)
        top_filter_row = ttk.Frame(filter_frame)
        top_filter_row.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0,5))
        
        scaled_font_tuple = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)

        ttk.Label(top_filter_row, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(top_filter_row, textvariable=self.search_var, width=25, font=scaled_font_tuple)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", lambda e: self.apply_filters())

        # Re-add Tipo de Dato filter
        ttk.Label(top_filter_row, text="Tipo de Dato:").pack(side=tk.LEFT, padx=(10, 5))
        self.type_combo = ttk.Combobox(top_filter_row, textvariable=self.filter_type_var, state="readonly", width=12, font=scaled_font_tuple)
        self.type_combo.pack(side=tk.LEFT, padx=5)
        self.type_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        ttk.Label(top_filter_row, text="Cálculo:").pack(side=tk.LEFT, padx=(10, 5))
        self.calc_filter_combo = ttk.Combobox(
            top_filter_row, textvariable=self.calc_filter_var,
            values=["Todos", "Maximo", "Minimo", "Rango"],
            state="readonly", width=10, font=scaled_font_tuple
        )
        self.calc_filter_combo.set("Todos") # Default value
        self.calc_filter_combo.pack(side=tk.LEFT, padx=5)
        self.calc_filter_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        # Row 1: VI Filter Controls (Label, VI count combo, Apply/Clear buttons)
        vi_controls_row = ttk.Frame(filter_frame)
        vi_controls_row.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(5,0))

        ttk.Label(vi_controls_row, text="Filtrar por VIs:").pack(side=tk.LEFT, padx=(0,5))
        self.filter_vi_count_combo = ttk.Combobox(vi_controls_row, textvariable=self.filter_vi_count_var,
                                                  values=["No filtrar", "1 VI", "2 VIs"], state="readonly", width=12, font=scaled_font_tuple)
        self.filter_vi_count_combo.pack(side=tk.LEFT, padx=(0,10))
        self.filter_vi_count_combo.bind("<<ComboboxSelected>>", self._on_filter_vi_count_change)
        
        # Spacer to push buttons to the right
        ttk.Frame(vi_controls_row).pack(side=tk.LEFT, expand=True, fill=tk.X)

        refresh_button = ttk.Button(vi_controls_row, text="Refrescar Lista", command=self.refresh_table_list_action)
        refresh_button.pack(side=tk.LEFT, padx=5)
        Tooltip(refresh_button, text="Recargar la lista de tablas desde el sistema de archivos.", short_text="Refrescar lista.", enabled=self.settings.enable_hover_tooltips)

        apply_filters_button = ttk.Button(vi_controls_row, text="Aplicar Todos los Filtros", command=self.apply_filters, style="Celeste.TButton")
        apply_filters_button.pack(side=tk.LEFT, padx=5)
        Tooltip(apply_filters_button, text="Aplicar todos los filtros de búsqueda y VIs seleccionados.", short_text="Aplicar filtros.", enabled=self.settings.enable_hover_tooltips)
        
        clear_filters_button = ttk.Button(vi_controls_row, text="Limpiar Todos los Filtros", command=self.clear_filters)
        clear_filters_button.pack(side=tk.LEFT, padx=5)
        Tooltip(clear_filters_button, text="Limpiar todos los filtros y mostrar todas las tablas.", short_text="Limpiar filtros.", enabled=self.settings.enable_hover_tooltips)


        # Row 2: VI 1 Filter Section (managed by grid_remove/grid)
        self.filter_vi1_frame = ttk.Frame(filter_frame)
        self.filter_vi1_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=(5,0))
        # self.filter_vi1_frame.columnconfigure(1, weight=1) # Optional: if combos need to expand more
        # self.filter_vi1_frame.columnconfigure(3, weight=1)
        scaled_font_tuple = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale) # Re-get for this scope if needed
        ttk.Label(self.filter_vi1_frame, text="VI 1:").grid(row=0, column=0, padx=(0,2), pady=2, sticky="w")
        self.filter_vi1_name_combo = ttk.Combobox(self.filter_vi1_frame, textvariable=self.filter_vi1_name_var, state="readonly", width=15, font=scaled_font_tuple)
        self.filter_vi1_name_combo.grid(row=0, column=1, padx=(0,5), pady=2, sticky="ew")
        self.filter_vi1_name_combo.bind("<<ComboboxSelected>>", lambda e: self._update_filter_descriptor_combobox(1))
        ttk.Label(self.filter_vi1_frame, text="Sub-valor:").grid(row=0, column=2, padx=(5,2), pady=2, sticky="w")
        self.filter_vi1_desc_combo = ttk.Combobox(self.filter_vi1_frame, textvariable=self.filter_vi1_desc_var, state="readonly", width=15, font=scaled_font_tuple)
        self.filter_vi1_desc_combo.grid(row=0, column=3, padx=(0,5), pady=2, sticky="ew")
        self.filter_vi1_frame.grid_remove() # Initially hidden

        # Row 3: VI 2 Filter Section (managed by grid_remove/grid)
        self.filter_vi2_frame = ttk.Frame(filter_frame)
        self.filter_vi2_frame.grid(row=3, column=0, columnspan=4, sticky="ew", padx=5, pady=(5,0))
        # self.filter_vi2_frame.columnconfigure(1, weight=1)
        # self.filter_vi2_frame.columnconfigure(3, weight=1)
        ttk.Label(self.filter_vi2_frame, text="VI 2:").grid(row=0, column=0, padx=(0,2), pady=2, sticky="w")
        self.filter_vi2_name_combo = ttk.Combobox(self.filter_vi2_frame, textvariable=self.filter_vi2_name_var, state="readonly", width=15, font=scaled_font_tuple)
        self.filter_vi2_name_combo.grid(row=0, column=1, padx=(0,5), pady=2, sticky="ew")
        self.filter_vi2_name_combo.bind("<<ComboboxSelected>>", lambda e: self._update_filter_descriptor_combobox(2))
        ttk.Label(self.filter_vi2_frame, text="Sub-valor:").grid(row=0, column=2, padx=(5,2), pady=2, sticky="w")
        self.filter_vi2_desc_combo = ttk.Combobox(self.filter_vi2_frame, textvariable=self.filter_vi2_desc_var, state="readonly", width=15, font=scaled_font_tuple)
        self.filter_vi2_desc_combo.grid(row=0, column=3, padx=(0,5), pady=2, sticky="ew")
        self.filter_vi2_frame.grid_remove() # Initially hidden

        # --- Lista de Tablas Generadas (Treeview) - Goes into scrollable_frame_content ---
        list_frame = ttk.LabelFrame(self.scrollable_frame_content, text="Tablas Generadas (.xlsx)")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        list_frame.columnconfigure(0, weight=1) 
        # list_frame.rowconfigure(0, weight=1) # Removed to respect treeview height    

        # Updated columns
        self.tables_tree = ttk.Treeview(
            list_frame,
            columns=("Nombre Archivo", "Cálculo", "Sub-valores", "Fecha Creación/Modif."),
            show="headings",
            selectmode="extended", # Permitir selección múltiple
            height=self.tables_per_page # Set height
        )
        self.tables_tree.grid(row=0, column=0, sticky='nsew', padx=5, pady=(5, 0))
        self.tables_tree.bind("<<TreeviewSelect>>", self._on_selection_change) # Bind selection event

        # Updated headings and sort commands
        cols_map = {
            "Nombre Archivo": "name",
            "Cálculo": "calc",
            "Sub-valores": "sub_values_display", # Use a display-formatted key for sorting
            "Fecha Creación/Modif.": "mtime"
        }
        for col_display, col_key in cols_map.items():
            self.tables_tree.heading(
                col_display, text=col_display,
                command=lambda k=col_key: self.sort_column(k, False) # Sort by internal key
            )

        # Updated column widths
        self.tables_tree.column("Nombre Archivo", width=300, anchor=tk.W)
        self.tables_tree.column("Cálculo", width=100, anchor=tk.W)
        self.tables_tree.column("Sub-valores", width=300, anchor=tk.W)
        self.tables_tree.column("Fecha Creación/Modif.", width=150, anchor=tk.CENTER)

        # Scrollbars for Treeview are removed, main canvas scrollbars will be used.
        # vsb.grid(row=0, column=1, sticky='ns', pady=(5, 0)) # Removed
        # hsb.grid(row=1, column=0, sticky='ew', padx=5) # Removed

        # --- Populate Bottom Fixed Pagination Frame ---
        # Pagination controls are created by self.update_pagination_controls()
        # and placed in self.bottom_fixed_pagination_frame.

        # --- Populate Bottom Fixed Table Actions Frame ---
        delete_all_tables_button = ttk.Button(
            self.bottom_fixed_table_actions_frame,
            text="Eliminar Todas las Tablas de Resumen",
            command=self._confirm_delete_all_summary_tables,
            style="Danger.TButton"
        )
        delete_all_tables_button.pack(side=tk.LEFT, padx=5)
        Tooltip(delete_all_tables_button, text="Eliminar TODAS las tablas de resumen (.xlsx) de este estudio. ¡Acción irreversible!", short_text="Eliminar todas las tablas.", enabled=self.settings.enable_hover_tooltips)

        self.delete_selected_button = ttk.Button(
            self.bottom_fixed_table_actions_frame,
            text="Eliminar Seleccionado(s)",
            command=self._confirm_delete_selected_tables,
            state=tk.DISABLED,
            style="Danger.TButton"
        )
        self.delete_selected_button.pack(side=tk.LEFT, padx=5)
        Tooltip(self.delete_selected_button, text="Eliminar las tablas de resumen seleccionadas en la lista.", short_text="Eliminar seleccionadas.", enabled=self.settings.enable_hover_tooltips)
        
        self.view_table_button = ttk.Button(self.bottom_fixed_table_actions_frame, text="Ver Tabla Seleccionada",
                                            command=self.view_table, state=tk.DISABLED, style="Celeste.TButton")
        self.view_table_button.pack(side=tk.RIGHT, padx=5)
        Tooltip(self.view_table_button, text="Abrir la tabla de resumen (.xlsx) seleccionada con la aplicación predeterminada.", short_text="Ver tabla.", enabled=self.settings.enable_hover_tooltips)

        # --- Botones de Acción para Tablas (Now direct children of parent_frame) ---
        # This frame is now a child of parent_frame (self.scrollable_frame), packed AFTER list_frame
        # BUT for the desired effect, these should be children of self (DiscreteAnalysisView),
        # packed AFTER canvas_container.

        # The following buttons will be moved to a new frame, a direct child of self (DiscreteAnalysisView)
        # and packed after canvas_container.
        # For now, let's create the frame here and then move its packing logic.
        # This change will be split: 1. Create frame here. 2. Adjust packing in __init__ or main layout.

        # This frame will be created and packed outside the scrollable area.
        # The widgets below will be parented to this new frame.
        # This specific SEARCH/REPLACE block will remove them from list_frame.
        # A subsequent block will add them to the new fixed bottom frame.
        # table_action_frame = ttk.Frame(list_frame) # OLD: child of list_frame
        # table_action_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(0, 5)) # OLD

        # These buttons are moved out of list_frame.
        # Their creation and packing will be handled in a new fixed bottom frame.


    def _confirm_delete_all_summary_tables(self):
        """Muestra confirmación y luego elimina todas las tablas de resumen."""
        study_name = "ID Desconocido"
        try:
            study_details = self.analysis_service.study_service.get_study_details(self.study_id)
            study_name = study_details.get('name', f"ID {self.study_id}")
        except Exception:
            logger.error(f"No se pudo obtener el nombre del estudio {self.study_id} para el diálogo de confirmación.")

        if messagebox.askyesno("Confirmar Eliminación Total de Tablas",
                               f"¿Está SEGURO de que desea eliminar TODAS las tablas de resumen (.xlsx) "
                               f"para el estudio '{study_name}'?\n\n"
                               "Esta acción es IRREVERSIBLE.",
                               icon='warning', parent=self):
            try:
                deleted_count = self.analysis_service.delete_all_discrete_summary_tables(self.study_id)
                messagebox.showinfo("Eliminación Completada",
                                    f"{deleted_count} tablas de resumen han sido eliminadas.",
                                    parent=self)
                self._fetch_all_table_files_data() # Recargar datos base
                self.apply_filters() # Aplicar filtros para refrescar la vista
            except Exception as e:
                logger.error(f"Error al eliminar todas las tablas de resumen para estudio {self.study_id}: {e}", exc_info=True)
                messagebox.showerror("Error al Eliminar Tablas",
                                     f"Ocurrió un error al eliminar las tablas:\n{e}",
                                     parent=self)

    def refresh_table_list_action(self):
        """Acción del botón Refrescar: recarga todos los datos y aplica filtros."""
        self._fetch_all_table_files_data()
        self.apply_filters()

    def generate_tables(self):
        """Llama al servicio para generar las tablas resumen CSV."""
        logger.info(f"Solicitando generación de tablas discretas para estudio "
                    f"{self.study_id}")
        try:
            # TODO: Mostrar un mensaje de "procesando"
            results = self.analysis_service.generate_discrete_summary_tables(
                self.study_id
            )

            success_count = len(results.get('success', []))
            error_count = len(results.get('errors', []))

            message = "Generación de tablas completada.\n\n"
            message += f"Tablas generadas/actualizadas: {success_count}\n"
            if error_count > 0:
                message += f"Errores encontrados: {error_count}\n\n"
                message += "Errores detallados:\n"
                # Mostrar hasta 5 errores
                message += "\n".join([f"- {err}" for err in
                                      results['errors'][:5]])
                if error_count > 5:
                    message += f"\n... y {error_count - 5} más (ver logs)."
                messagebox.showwarning("Resultado Generación", message,
                                       parent=self)
            else:
                messagebox.showinfo("Resultado Generación", message, parent=self)

            # Refrescar la lista de tablas después de mostrar el mensaje
            self._fetch_all_table_files_data() # Re-fetch all data
            self.apply_filters() # Then apply filters to refresh view

        except Exception as e:
            logger.critical("Error crítico al llamar a "
                            f"generate_discrete_summary_tables: {e}",
                            exc_info=True)
            messagebox.showerror(
                "Error Crítico",
                f"Ocurrió un error inesperado al generar las tablas:\n{e}",
                parent=self)

    # _format_size is no longer needed as "Tamaño" column is removed.

    def _parse_table_filename(self, filename: str) -> tuple[str, str, list[str]]:
        """
        Parsea el nombre de archivo para extraer cálculo, tipo de dato (frecuencia),
        y lista de sub-valores en formato "VI_Nombre=Descriptor_Valor".
        El nombre de archivo usa '_' en lugar de '=' y '__' en lugar de ';'.
        Ejemplo: Maximo_Cinematica_Edad_Joven__Peso_OS.xlsx
        Retorna: (calculo, tipo_dato, ["Edad=Joven", "Peso=OS"])
        """
        name_part = filename.rsplit('.', 1)[0] # Quitar extensión
        
        file_parts = name_part.split('_')
        if len(file_parts) < 2: # Mínimo CALC_FREQ
            logger.warning(f"Nombre de archivo muy corto para parsear: {filename}")
            return "Desconocido", "Desconocido", []
        
        calc_type = file_parts[0]
        data_type = file_parts[1]
        
        # El resto son los sub-valores codificados
        # Ej: Edad_Joven__Peso_OS
        # Esto se une de file_parts[2:]
        encoded_sub_values_str = '_'.join(file_parts[2:])
        
        # Dividir por '__' para obtener partes individuales como "Edad_Joven", "Peso_OS"
        encoded_individual_sv_parts = encoded_sub_values_str.split('__') if encoded_sub_values_str else []
        
        reconstructed_sub_value_list = []
        # self.study_vis debería estar poblado con {'name': 'VI_NAME', ...}
        # Asumimos que los nombres de VI no contienen '_' y son prefijos únicos.
        
        for encoded_sv_part in encoded_individual_sv_parts:
            parsed_correctly = False
            # Eliminar posible '_' al inicio si la separación por '__' lo dejó (de '___')
            current_encoded_part = encoded_sv_part.lstrip('_')

            for vi_definition in self.study_vis:
                vi_name = vi_definition.get('name')
                if not vi_name:
                    continue
                
                # Comprobar si la parte codificada comienza con "NOMBRE_VI_"
                if current_encoded_part.startswith(vi_name + "_"):
                    # El descriptor es todo lo que sigue después de "NOMBRE_VI_"
                    descriptor_value = current_encoded_part[len(vi_name) + 1:]
                    reconstructed_sub_value_list.append(f"{vi_name}={descriptor_value}")
                    parsed_correctly = True
                    break # VI encontrada para esta parte
            
            if not parsed_correctly:
                # Si no se pudo parsear (ej. "SinSubValores" o formato inesperado)
                # Se podría añadir el original o un placeholder, o loguear.
                # Por ahora, si no se parsea, no se añade, lo que podría ser problemático.
                # Mejor añadir el original como fallback para depuración.
                if current_encoded_part: # Solo si no está vacío
                    logger.warning(f"No se pudo parsear la parte del sub-valor '{current_encoded_part}' "
                                   f"del archivo '{filename}' a formato VI=Descriptor. "
                                   f"VIs conocidas: {[v['name'] for v in self.study_vis]}")
                    reconstructed_sub_value_list.append(current_encoded_part) # Fallback
                    
        return calc_type, data_type, reconstructed_sub_value_list

    def _fetch_all_table_files_data(self):
        """Obtiene y parsea todos los archivos de tablas .xlsx del servicio."""
        self.all_tables_data = []
        tables_path = self.analysis_service.get_discrete_analysis_tables_path(self.study_id)
        if tables_path and tables_path.exists(): # Check if path exists
            for freq_dir in tables_path.iterdir(): # e.g., Cinematica, Cinetica
                if freq_dir.is_dir():
                    for file_path in freq_dir.iterdir(): # e.g., Maximo_Cinematica_VI1=DescA.xlsx
                        if file_path.is_file() and file_path.suffix == '.xlsx': # Solo .xlsx
                            try:
                                calc, freq, sub_values_list = self._parse_table_filename(file_path.name)
                                mtime = file_path.stat().st_mtime
                                self.all_tables_data.append({
                                    "path": file_path,
                                    "name": file_path.name,
                                    "type": freq, # Tipo de Dato (Frecuencia)
                                    "calc": calc,
                                    "sub_values_raw": sub_values_list, # Lista de "VI=Desc"
                                    "mtime": mtime
                                })
                            except Exception as e:
                                logger.error(f"Error parseando nombre de archivo de tabla {file_path.name}: {e}")
        
        # Actualizar opciones de los filtros de Tipo de Dato y Cálculo
        types = sorted(list(set(table_info["type"] for table_info in self.all_tables_data)))
        calcs = sorted(list(set(table_info["calc"] for table_info in self.all_tables_data)))

        self.type_combo['values'] = ["Todos"] + types
        self.calc_filter_combo['values'] = ["Todos"] + calcs # Corrected: self.calc_filter_combo
        # Format filter is removed

    def _populate_treeview(self, tables_to_display: list):
        """Popula el Treeview con la lista de datos de tablas proporcionada."""
        self.tables_tree.delete(*self.tables_tree.get_children())

        start_index = (self.current_page - 1) * self.tables_per_page
        end_index = start_index + self.tables_per_page
        paginated_tables_data = tables_to_display[start_index:end_index]

        if not paginated_tables_data:
            num_empty_cols = len(self.tables_tree["columns"])
            empty_values = tuple(["No hay tablas que coincidan con los filtros."] + [""] * (num_empty_cols -1))
            self.tables_tree.insert("", tk.END, values=empty_values, iid="NoMatch")
        else:
            for table_info in paginated_tables_data:
                filename = table_info["name"]
                # data_type = table_info["type"] # Not displayed directly in table anymore
                calc_type = table_info["calc"]
                
                # Formatear sub-valores
                sub_values_display_parts = []
                for sv_part in table_info["sub_values_raw"]: # sv_part is "VI=Desc"
                    try:
                        vi_name, desc_val = sv_part.split('=', 1)
                        alias = self.study_aliases.get(desc_val, desc_val)
                        sub_values_display_parts.append(f"{vi_name}: {alias}")
                    except ValueError:
                        sub_values_display_parts.append(sv_part) # Fallback
                sub_values_str_formatted = ", ".join(sub_values_display_parts)
                table_info["sub_values_display"] = sub_values_str_formatted # Store for sorting
                
                date_str = datetime.fromtimestamp(table_info["mtime"]).strftime('%Y-%m-%d %H:%M')
                
                # Updated values for new column order
                self.tables_tree.insert("", tk.END, iid=str(table_info['path']), # Explicitly set iid to path string
                                        values=(filename, calc_type, 
                                                sub_values_str_formatted, date_str))
        
        self.update_pagination_controls()

    def load_tables(self):
        """Alias para aplicar filtros, que ahora maneja la carga y población."""
        # Fetch all data first, then apply filters.
        # This is slightly different from previous where apply_filters re-fetched.
        # Now, _fetch_all_table_files_data is called once at init and after generation.
        self.apply_filters()


    def update_pagination_controls(self):
        """Actualiza el estado y texto de los controles de paginación."""
        # Limpiar controles existentes en self.bottom_fixed_pagination_frame
        for widget in self.bottom_fixed_pagination_frame.winfo_children():
            widget.destroy()

        if self.total_pages <= 1:
            return # No mostrar si solo hay una página

        page_info = (f"Página {self.current_page} de {self.total_pages} "
                     f"({self.total_tables} tablas)")
        
        # --- Left-aligned buttons ---
        first_btn = ttk.Button(self.bottom_fixed_pagination_frame, text="<<", command=lambda: self.go_to_page(1))
        first_btn.pack(side=tk.LEFT, padx=2)
        Tooltip(first_btn, text="Ir a la primera página de tablas.", short_text="Primera página.", enabled=self.settings.enable_hover_tooltips)
        if self.current_page == 1: first_btn.config(state=tk.DISABLED)

        prev_btn = ttk.Button(
            self.bottom_fixed_pagination_frame, text="< Anterior",
            command=lambda: self.go_to_page(self.current_page - 1),
            state=tk.DISABLED if self.current_page <= 1 else tk.NORMAL
        )
        prev_btn.pack(side=tk.LEFT, padx=5)
        Tooltip(prev_btn, text="Ir a la página anterior de tablas.", short_text="Página anterior.", enabled=self.settings.enable_hover_tooltips)

        # --- Right-aligned buttons (packed in reverse visual order) ---
        last_btn = ttk.Button(self.bottom_fixed_pagination_frame, text=">>", command=lambda: self.go_to_page(self.total_pages))
        last_btn.pack(side=tk.RIGHT, padx=2)
        Tooltip(last_btn, text="Ir a la última página de tablas.", short_text="Última página.", enabled=self.settings.enable_hover_tooltips)
        if self.current_page == self.total_pages: last_btn.config(state=tk.DISABLED)

        next_btn = ttk.Button(
            self.bottom_fixed_pagination_frame, text="Siguiente >",
            command=lambda: self.go_to_page(self.current_page + 1),
            state=tk.DISABLED if self.current_page >= self.total_pages else tk.NORMAL
        )
        next_btn.pack(side=tk.RIGHT, padx=5)
        Tooltip(next_btn, text="Ir a la página siguiente de tablas.", short_text="Página siguiente.", enabled=self.settings.enable_hover_tooltips)
        
        # --- Center-aligned label (fills remaining space) ---
        page_label = ttk.Label(self.bottom_fixed_pagination_frame, text=page_info)
        page_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)


    def go_to_page(self, page_number):
        """Navega a una página específica."""
        if 1 <= page_number <= self.total_pages:
            self.current_page = page_number
            self._populate_treeview(self.filtered_tables_data) # Repopulate with current filtered data
        else:
            logger.warning(f"Intento de ir a página inválida: {page_number}")

    # search_tables removed, combined into apply_filters

    def apply_filters(self, event=None):
        """Aplica los filtros seleccionados y recarga la tabla."""
        search_term = self.search_var.get().lower()
        selected_calc = self.calc_filter_var.get()
        # selected_format no longer exists
        
        # VI Filters
        vi_filter_mode = self.filter_vi_count_var.get()
        vi1_name_filter = self.filter_vi1_name_var.get()
        vi1_desc_display_filter = self.filter_vi1_desc_var.get()
        vi1_desc_original_filter = self._get_descriptor_original_value(vi1_desc_display_filter)
        
        vi2_name_filter = self.filter_vi2_name_var.get()
        vi2_desc_display_filter = self.filter_vi2_desc_var.get()
        vi2_desc_original_filter = self._get_descriptor_original_value(vi2_desc_display_filter)

        target_filter_vi_part1 = f"{vi1_name_filter}={vi1_desc_original_filter}" if vi1_name_filter and vi1_desc_original_filter else None
        target_filter_vi_part2 = f"{vi2_name_filter}={vi2_desc_original_filter}" if vi2_name_filter and vi2_desc_original_filter else None

        self.filtered_tables_data = []
        for table_info in self.all_tables_data: # Iterate over parsed data
            # Match search term (name, calc, sub_values_display)
            search_match = True
            if search_term:
                # Use sub_values_display for search as it's what user sees
                sv_display_for_search = table_info.get("sub_values_display", "") 
                search_match = (search_term in table_info["name"].lower() or
                                search_term in table_info["calc"].lower() or
                                search_term in sv_display_for_search.lower())
            if not search_match:
                continue

            # Match calculation filter
            calc_match = (selected_calc == "Todos" or table_info["calc"] == selected_calc)
            if not calc_match:
                continue
            
            # Match VI filters
            vi_match = True
            if vi_filter_mode != "No filtrar":
                table_sub_values_raw = table_info.get("sub_values_raw", []) # List of "VI=Desc"
                
                if target_filter_vi_part1:
                    if not any(target_filter_vi_part1 == sv_part for sv_part in table_sub_values_raw):
                        vi_match = False
                
                if vi_match and vi_filter_mode == "2 VIs" and target_filter_vi_part2:
                    if not any(target_filter_vi_part2 == sv_part for sv_part in table_sub_values_raw):
                        vi_match = False
            
            if vi_match: # If all filters pass
                self.filtered_tables_data.append(table_info)
        
        self.total_tables = len(self.filtered_tables_data)
        self.tables_per_page = self.settings.discrete_tables_per_page # Ensure it's up-to-date
        self.total_pages = math.ceil(self.total_tables / self.tables_per_page) if self.tables_per_page > 0 else 1
        self.total_pages = max(1, self.total_pages)
        self.current_page = 1 # Reset to first page after filtering
        
        self._populate_treeview(self.filtered_tables_data)
        
        # "Gestor de Análisis Discretos" button is always enabled.
        # Popups inside the manager will handle cases with no data.
        if hasattr(self, 'open_manager_button'):
            self.open_manager_button.config(state=tk.NORMAL)
            Tooltip(self.open_manager_button, text="Abrir el gestor para crear, ver y eliminar análisis discretos individuales (boxplots, tests estadísticos).", short_text="Gestor análisis.", enabled=self.settings.enable_hover_tooltips)


    def clear_filters(self):
        """Limpia los filtros y la búsqueda, y recarga la tabla."""
        self.search_var.set("")
        self.calc_filter_var.set("Todos")
        self.filter_type_var.set("Todos") # Reset Tipo de Dato filter
        # format_filter_var removed
        self._clear_vi_filters() # Clear VI filters as well
        # self.current_page = 1 # apply_filters will reset page
        # self.load_tables() # apply_filters is now the main method
        self.apply_filters()

    def _on_selection_change(self, event=None):
        """Actualiza el estado de los botones basado en la selección."""
        selected_items = self.tables_tree.selection()
        num_selected = len(selected_items)

        if self.view_table_button: # Check if button exists
            self.view_table_button.config(state=tk.NORMAL if num_selected == 1 else tk.DISABLED)
        
        if self.delete_selected_button: # Check if button exists
            self.delete_selected_button.config(state=tk.NORMAL if num_selected > 0 else tk.DISABLED)


    def sort_column(self, sort_key_internal, reverse): # Renamed col to sort_key_internal
        """Ordena el Treeview por la columna especificada."""
        # sort_key_internal is now the internal key like "name", "calc", "mtime", "sub_values_display"
        
        if not sort_key_internal:
            logger.warning(f"Clave de ordenación interna no válida: {sort_key_internal}")
            return

        # Ordenar self.filtered_tables_data
        if sort_key_internal == "mtime":
            self.filtered_tables_data.sort(key=lambda x: x.get(sort_key_internal, 0), reverse=reverse)
        # For sub_values_display, it's already a string, direct sort is fine
        else: # Ordenación alfabética para otras columnas (name, calc, sub_values_display)
            self.filtered_tables_data.sort(key=lambda x: str(x.get(sort_key_internal, "")).lower(), reverse=reverse)

        # Repopular el treeview con los datos ordenados (reseteando paginación)
        self.current_page = 1
        self._populate_treeview(self.filtered_tables_data)
        
        # Invertir dirección para la próxima vez
        # Need to map back from internal key to display column name for the heading command
        display_col_name = None
        cols_map_for_heading = { # Inverse of the map in create_widgets or direct
            "name": "Nombre Archivo", "calc": "Cálculo",
            "sub_values_display": "Sub-valores", "mtime": "Fecha Creación/Modif."
        }
        display_col_name = cols_map_for_heading.get(sort_key_internal)

        if display_col_name:
            self.tables_tree.heading(display_col_name, command=lambda: self.sort_column(sort_key_internal, not reverse))
        else:
            logger.warning(f"No se pudo encontrar el nombre de display para la clave interna de ordenación: {sort_key_internal}")


    def _load_study_vi_data(self):
        """Loads VI names and their descriptors for the current study."""
        try:
            details = self.analysis_service.study_service.get_study_details(self.study_id)
            self.study_vis = details.get('independent_variables', [])
            self.study_aliases = self.analysis_service.study_service.get_study_aliases(self.study_id)
        except Exception as e:
            logger.error(f"Error loading VI data for study {self.study_id} in DiscreteAnalysisView: {e}", exc_info=True)
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
        # Automatically apply filters when a VI descriptor is selected or cleared
        self.apply_filters()


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
            self.filter_vi1_frame.grid() # Use grid to show
            self.filter_vi2_frame.grid_remove()
        elif count_mode == "2 VIs":
            self.filter_vi1_frame.grid()
            self.filter_vi2_frame.grid()
        else: # "No filtrar"
            self.filter_vi1_frame.grid_remove()
            self.filter_vi2_frame.grid_remove()
        self.apply_filters() # Apply filters when VI count mode changes

    def _get_descriptor_original_value(self, display_name: str) -> str:
        if not display_name: return ""
        if " (" in display_name and display_name.endswith(")"):
            original_candidate = display_name.rsplit(" (", 1)[0]
            if self.study_aliases.get(original_candidate) == display_name.rsplit(" (", 1)[1][:-1]:
                return original_candidate
        return display_name

    def _clear_vi_filters(self):
        self.filter_vi_count_var.set("No filtrar")
        self._on_filter_vi_count_change() # This will hide frames and clear sub-vars
        # self.apply_filters() # _on_filter_vi_count_change already calls apply_filters

    def view_table(self):
        """Abre la tabla CSV seleccionada con la aplicación predeterminada."""
        selected_items = self.tables_tree.selection()
        if not selected_items or len(selected_items) > 1:
            messagebox.showwarning("Selección Múltiple", "Por favor, seleccione una única tabla para ver.", parent=self)
            return
        
        if not selected_items: # Should be caught by above, but defensive
            messagebox.showwarning("Sin Selección", "Seleccione una tabla para ver.", parent=self)
            return

        selected_item_iid = selected_items[0]

        if not selected_item_iid or selected_item_iid == "NoMatch":
            messagebox.showwarning("Sin Selección", "No hay una tabla válida seleccionada.",
                                   parent=self)
            return

        file_path = Path(selected_item_iid) # Use the iid which is the path string

        if not file_path.exists():
            messagebox.showerror("Error",
                                   f"El archivo ya no existe:\n{file_path}",
                                   parent=self)
            self._fetch_all_table_files_data() # Re-fetch all data
            self.apply_filters() # Then apply filters to refresh view
            return

        try:
            logger.info(f"Intentando abrir archivo: {file_path}")
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", file_path], check=True)
            else:  # linux variants
                subprocess.run(["xdg-open", file_path], check=True)
        except FileNotFoundError:
            # Este caso ya se verifica arriba, pero por si acaso
            messagebox.showerror("Error",
                                   f"No se pudo encontrar el archivo:\n{file_path}",
                                   parent=self)
        except OSError as e:
            logger.error("Error del sistema operativo al intentar abrir "
                         f"{file_path}: {e}", exc_info=True)
            messagebox.showerror(
                "Error al Abrir",
                "No se pudo abrir el archivo con la aplicación "
                f"predeterminada.\nError: {e}", parent=self)
        except subprocess.CalledProcessError as e:
            logger.error("Error al ejecutar comando para abrir "
                         f"{file_path}: {e}", exc_info=True)
            messagebox.showerror(
                "Error al Abrir",
                f"El comando para abrir el archivo falló.\nError: {e}",
                parent=self)
        except Exception as e:
            logger.error(f"Error inesperado al abrir {file_path}: {e}",
                         exc_info=True)
            messagebox.showerror(
                "Error Inesperado",
                "Ocurrió un error inesperado al intentar abrir el "
                f"archivo:\n{e}", parent=self)

    def _get_selected_table_paths(self) -> list[str]:
        """Retorna una lista de strings de rutas para las tablas seleccionadas."""
        selected_paths = []
        selected_item_iids = self.tables_tree.selection()
        for iid in selected_item_iids:
            if iid and iid != "NoMatch":
                selected_paths.append(iid) # iid es la ruta como string
        return selected_paths

    def _confirm_delete_selected_tables(self):
        """Muestra confirmación y elimina las tablas seleccionadas."""
        selected_paths_str = self._get_selected_table_paths()
        if not selected_paths_str:
            messagebox.showwarning("Sin Selección", "No hay tablas seleccionadas para eliminar.", parent=self)
            return

        num_selected = len(selected_paths_str)
        # Obtener nombres de archivo para el mensaje de confirmación
        # file_names_to_confirm = [Path(p_str).name for p_str in selected_paths_str] # No longer needed for message

        confirm_message = (f"¿Está seguro de que desea eliminar las {num_selected} tablas seleccionadas?\n"
                           "Esta acción es IRREVERSIBLE.")

        if messagebox.askyesno("Confirmar Eliminación Múltiple", confirm_message, icon='warning', parent=self):
            success_count, errors = self.analysis_service.delete_selected_discrete_summary_tables(selected_paths_str)

            if errors:
                error_details = "\n".join(errors[:3])
                if len(errors) > 3:
                    error_details += f"\n... y {len(errors) - 3} más."
                messagebox.showerror("Errores en Eliminación",
                                     f"Se eliminaron {success_count} tablas, pero ocurrieron errores con {len(errors)} tablas:\n{error_details}",
                                     parent=self)
            elif success_count > 0:
                messagebox.showinfo("Éxito", f"{success_count} tabla(s) eliminada(s) correctamente.", parent=self)
            else:
                messagebox.showinfo("Información", "No se eliminó ninguna tabla.", parent=self)
            
            self._fetch_all_table_files_data() # Re-fetch all data
            self.apply_filters() # Then apply filters to refresh view

    # delete_table (singular) is removed.

    def open_individual_analysis_manager(self):
        """Abre el diálogo para gestionar análisis individuales."""
        # The check for self.all_tables_data is removed.
        # IndividualAnalysisManagerDialog will handle cases with no data.

        # Import local para evitar dependencia circular si es necesario
        from kineviz.ui.dialogs.individual_analysis_manager_dialog \
            import IndividualAnalysisManagerDialog
        # Pasar self.analysis_service y self.study_id
        # The parent for IndividualAnalysisManagerDialog should be self (DiscreteAnalysisView)
        # and it will access main_window via self.parent.main_window
        _dialog = IndividualAnalysisManagerDialog(self, self.analysis_service, self.study_id)

    def _open_summary_tables_folder(self):
        """Abre la carpeta donde se guardan las tablas de resumen discreto."""
        try:
            tables_path = self.analysis_service.get_discrete_analysis_tables_path(self.study_id)
            if tables_path and tables_path.exists():
                self.main_window.open_folder(str(tables_path))
            elif tables_path:
                messagebox.showinfo("Información", f"La carpeta de tablas de resumen ({tables_path}) aún no ha sido creada.", parent=self)
            else:
                messagebox.showerror("Error", "No se pudo determinar la ruta de la carpeta de tablas de resumen.", parent=self)
        except Exception as e:
            logger.error(f"Error al intentar abrir carpeta de tablas de resumen para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir la carpeta de tablas de resumen:\n{e}", parent=self)

    def destroy(self):
        """Destruye el frame principal de esta vista."""
        super().destroy()
# Eliminado bloque redundante de update_pagination_controls y métodos siguientes
# ya que se corrigieron en el bloque anterior.
