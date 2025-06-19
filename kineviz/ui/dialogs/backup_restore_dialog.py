import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, simpledialog
from pathlib import Path
import datetime # For formatting timestamp
import logging # For logging
import time # For sleep in dummy test

# Import backup_manager functions directly for type hinting and direct calls
from kineviz.core import backup_manager
from kineviz.config.settings import AppSettings # For AppSettings type hint
from kineviz.ui.widgets.tooltip import Tooltip
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # For direct font scaling
from kineviz.utils.paths import get_application_base_dir # Import for base directory

# Setup logger for this module if not configured globally for UI
logger = logging.getLogger(__name__)


class BackupRestoreDialog(Toplevel):
    """Diálogo para gestionar copias de seguridad y restauraciones."""

    def __init__(self, parent, app_settings: AppSettings, main_window_instance=None):
        super().__init__(parent)
        self.parent_window = parent # Store parent for simpledialog if needed
        self.app_settings = app_settings # Store AppSettings instance
        self.main_window_instance = main_window_instance # Store MainWindow instance for restart
        self.restart_required_after_restore = False # New flag

        self.title("Gestión de Copias de Seguridad")
        # Responsive sizing
        base_min_width = 600 
        base_min_height = 400 
        base_geom_width = 800
        base_geom_height = 500
        current_font_scale = self.app_settings.font_scale

        dynamic_min_width = int(base_min_width * (1 + (current_font_scale - 1) * 0.30))
        dynamic_min_height = int(base_min_height * (1 + (current_font_scale - 1) * 0.50))
        self.minsize(max(base_min_width, dynamic_min_width), max(base_min_height, dynamic_min_height))

        initial_geom_width = int(base_geom_width * (1 + (current_font_scale - 1) * 0.25))
        initial_geom_height = int(base_geom_height * (1 + (current_font_scale - 1) * 0.45))
        self.geometry(f"{max(base_geom_width, initial_geom_width)}x{max(base_geom_height, initial_geom_height)}")


        self.all_loaded_backups = [] # To store the full list from backup_manager
        self.current_display_list = [] # To store the currently displayed (filtered/sorted) list
        self.paginated_list = [] # To store the list for the current page
    
        # Filter and sort variables
        self.filter_type_var = tk.StringVar(value="Todos") # Default to "Todos"
        self.search_alias_var = tk.StringVar()
        self.sort_key_var = tk.StringVar(value="Fecha de Creación")
        self.sort_order_asc_var = tk.BooleanVar(value=False) # False for Descending initially

        # Pagination variables
        self.current_page_backups = tk.IntVar(value=1)
        self.total_pages_backups = tk.IntVar(value=1)
        self.backups_per_page = self.app_settings.backups_per_page # Get from settings

        # Calculate scaled font once for direct application
        self.scaled_font_tuple = get_scaled_font(DEFAULT_FONT_SIZE, self.app_settings.font_scale)

        self.create_widgets()
        self.load_backups() # Initial load

        # Set initial geometry after widgets are created and data loaded (for reqheight)
        self.update_idletasks() # Ensure Tkinter has processed widget sizes
        # Use the previously calculated initial_geom_width
        # Set height based on requested height of the content
        calculated_initial_width = int(base_geom_width * (1 + (current_font_scale - 1) * 0.25))
        # Ensure the width is at least the min_width
        final_initial_width = max(dynamic_min_width, calculated_initial_width)
        self.geometry(f"{final_initial_width}x{self.winfo_reqheight()}")


        self.transient(parent)
        self.grab_set()
        # self.protocol("WM_DELETE_WINDOW", self.destroy) # Default behavior is fine

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1) # Allow the main content column to expand
        # Configure main_frame rows to allow treeview to expand and button rows to take fixed space
        main_frame.rowconfigure(1, weight=1) # Treeview frame (ALLOW TO EXPAND VERTICALLY)
        main_frame.rowconfigure(2, weight=0) # Pagination controls frame
        main_frame.rowconfigure(3, weight=0) # Actions row 2
        main_frame.rowconfigure(4, weight=0) # Actions row 3


        # --- Filter and Sort Controls Frame ---
        filter_sort_frame = ttk.LabelFrame(main_frame, text="Filtrar y Ordenar", padding="10")
        filter_sort_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10)) # Use grid
        filter_sort_frame.columnconfigure(1, weight=1) 
        filter_sort_frame.columnconfigure(3, weight=1)
        filter_sort_frame.columnconfigure(4, weight=0) # For Clear button
        filter_sort_frame.columnconfigure(5, weight=0) # For Apply button
        
        # Type Filter
        ttk.Label(filter_sort_frame, text="Tipo:").grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")
        type_combo = ttk.Combobox(filter_sort_frame, textvariable=self.filter_type_var,
                                  values=["Todos", "Manual", "Automática", "Respaldo"], state="readonly", font=self.scaled_font_tuple) # Added font
        type_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        type_combo.bind("<<ComboboxSelected>>", self._apply_filters_and_sort)

        # Alias Search
        ttk.Label(filter_sort_frame, text="Buscar Alias/Nombre:").grid(row=0, column=2, padx=(10,5), pady=5, sticky="w")
        search_entry = ttk.Entry(filter_sort_frame, textvariable=self.search_alias_var, font=self.scaled_font_tuple) # Added font
        search_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        search_entry.bind("<Return>", self._apply_filters_and_sort)
        # Search Button (optional, can rely on Enter or type filter change)
        # search_button = ttk.Button(filter_sort_frame, text="Buscar", command=self._apply_filters_and_sort)
        # search_button.grid(row=0, column=4, padx=5, pady=5)

        # Sort Key
        ttk.Label(filter_sort_frame, text="Ordenar por:").grid(row=1, column=0, padx=(0,5), pady=5, sticky="w")
        sort_key_combo = ttk.Combobox(filter_sort_frame, textvariable=self.sort_key_var, 
                                      values=["Fecha de Creación", "Tipo", "Alias"], state="readonly", font=self.scaled_font_tuple) # Added font
        sort_key_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        sort_key_combo.bind("<<ComboboxSelected>>", self._apply_filters_and_sort)

        # Sort Order Button
        self.sort_order_button = ttk.Button(filter_sort_frame, text="Orden: ↓", command=self._toggle_sort_order) # Removed width
        self.sort_order_button.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        Tooltip(self.sort_order_button, text="Cambiar orden (Ascendente/Descendente).", enabled=self.app_settings.enable_hover_tooltips)
        
        # Clear Filters Button
        clear_filters_btn = ttk.Button(filter_sort_frame, text="Limpiar", command=self._reset_filters)
        clear_filters_btn.grid(row=1, column=3, padx=(5,5), pady=5, sticky="e")
        Tooltip(clear_filters_btn, text="Restablecer filtros y orden a los valores por defecto.", enabled=self.app_settings.enable_hover_tooltips)

        # Apply Filters Button (explicitly)
        apply_filters_btn = ttk.Button(filter_sort_frame, text="Aplicar", command=self._apply_filters_and_sort, style="Celeste.TButton")
        apply_filters_btn.grid(row=1, column=4, padx=(0,5), pady=5, sticky="e") # Adjusted column

        # --- Treeview para listar backups ---
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10)) # Use grid, sticky nsew
        tree_frame.rowconfigure(0, weight=1)    # Allow treeview to expand within tree_frame
        tree_frame.columnconfigure(0, weight=1) # Allow treeview to expand within tree_frame


        columns = ("type", "timestamp", "alias", "filename") # Filename is hidden but used for actions
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse", height=self.backups_per_page) # Set initial height
        
        self.tree.heading("type", text="Tipo")
        self.tree.heading("timestamp", text="Fecha de Creación")
        self.tree.heading("alias", text="Alias (Manual)")
        self.tree.heading("filename", text="Nombre Archivo") # Hidden column for internal use

        self.tree.column("type", width=100, anchor=tk.W)
        self.tree.column("timestamp", width=180, anchor=tk.W)
        self.tree.column("alias", width=200, anchor=tk.W)
        self.tree.column("filename", width=0, stretch=tk.NO) # Hide filename column

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns") # Use grid
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew") # Use grid
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew") # Use grid
        self.tree.bind("<<TreeviewSelect>>", self.on_backup_selected)

        # --- Pagination Controls Frame (Row 1 of bottom buttons) ---
        pagination_controls_frame = ttk.Frame(main_frame)
        pagination_controls_frame.grid(row=2, column=0, sticky="ew", pady=(5,0))
        pagination_controls_frame.columnconfigure(0, weight=1) # Previous button
        pagination_controls_frame.columnconfigure(1, weight=0) # Prev button
        pagination_controls_frame.columnconfigure(2, weight=0) # Page label
        pagination_controls_frame.columnconfigure(3, weight=0) # Next button
        pagination_controls_frame.columnconfigure(4, weight=1) # Last button (pushes to right)


        self.btn_first_page_backups = ttk.Button(pagination_controls_frame, text="<<", command=lambda: self.go_to_backup_page("first"), style="Nav.TButton")
        self.btn_first_page_backups.grid(row=0, column=0, sticky="w", padx=(5,0))
        self.btn_prev_page_backups = ttk.Button(pagination_controls_frame, text="<", command=lambda: self.go_to_backup_page("prev"), style="Nav.TButton")
        self.btn_prev_page_backups.grid(row=0, column=1, sticky="w", padx=(0,5))
        
        self.lbl_page_backups = ttk.Label(pagination_controls_frame, text="Página: 1 / 1")
        self.lbl_page_backups.grid(row=0, column=2, padx=5)
        
        self.btn_next_page_backups = ttk.Button(pagination_controls_frame, text=">", command=lambda: self.go_to_backup_page("next"), style="Nav.TButton")
        self.btn_next_page_backups.grid(row=0, column=3, sticky="e", padx=(5,0))
        self.btn_last_page_backups = ttk.Button(pagination_controls_frame, text=">>", command=lambda: self.go_to_backup_page("last"), style="Nav.TButton")
        self.btn_last_page_backups.grid(row=0, column=4, sticky="e", padx=(0,5))
        
        self.pagination_controls_frame = pagination_controls_frame # Store ref for visibility toggle

        # --- Action Buttons Row 2 ---
        actions_row2_frame = ttk.Frame(main_frame)
        actions_row2_frame.grid(row=3, column=0, sticky="ew", pady=(5,0))
        actions_row2_frame.columnconfigure(0, weight=0) # Create Manual
        actions_row2_frame.columnconfigure(1, weight=0) # Restore Selected
        actions_row2_frame.columnconfigure(2, weight=1) # Expanding space
        actions_row2_frame.columnconfigure(3, weight=0) # Assign Alias
        
        self.btn_create_manual = ttk.Button(actions_row2_frame, text="Crear Copia Manual", command=self.create_manual_backup_action, style="Green.TButton")
        self.btn_create_manual.grid(row=0, column=0, padx=5, sticky="w")
        Tooltip(self.btn_create_manual, "Crea una nueva copia de seguridad manual del estado actual del sistema.", enabled=self.app_settings.enable_hover_tooltips)

        self.btn_restore = ttk.Button(actions_row2_frame, text="Restaurar Seleccionada", command=self.restore_selected_action, state=tk.DISABLED, style="Green.TButton")
        self.btn_restore.grid(row=0, column=1, padx=5, sticky="w")
        Tooltip(self.btn_restore, "Restaura el sistema al estado de la copia de seguridad seleccionada. ¡Esta acción es irreversible!", enabled=self.app_settings.enable_hover_tooltips)
        
        self.btn_assign_alias = ttk.Button(actions_row2_frame, text="Asignar/Editar Alias", command=self.assign_alias_action, state=tk.DISABLED, style="Celeste.TButton")
        self.btn_assign_alias.grid(row=0, column=3, padx=5, sticky="e") # Rightmost in this row
        Tooltip(self.btn_assign_alias, "Asigna o edita un alias descriptivo a la copia de seguridad seleccionada (manual o automática).", enabled=self.app_settings.enable_hover_tooltips)

        # --- Action Buttons Row 3 ---
        actions_row3_frame = ttk.Frame(main_frame)
        actions_row3_frame.grid(row=4, column=0, sticky="ew", pady=(5,0))
        actions_row3_frame.columnconfigure(1, weight=1) # To push refresh and close to the right

        self.btn_delete_manual = ttk.Button(actions_row3_frame, text="Eliminar Manual", command=self._delete_manual_backup_action, state=tk.DISABLED, style="Danger.TButton")
        self.btn_delete_manual.grid(row=0, column=0, padx=5, sticky="w")
        Tooltip(self.btn_delete_manual, "Elimina permanentemente la copia de seguridad manual seleccionada.", enabled=self.app_settings.enable_hover_tooltips)
        
        # Right side of row 3
        btn_refresh = ttk.Button(actions_row3_frame, text="Refrescar Lista", command=self.load_backups)
        btn_refresh.grid(row=0, column=2, padx=5, sticky="e")
        Tooltip(btn_refresh, "Vuelve a cargar la lista de copias de seguridad disponibles.", enabled=self.app_settings.enable_hover_tooltips)

        btn_cancel = ttk.Button(actions_row3_frame, text="Cerrar", command=self.destroy)
        btn_cancel.grid(row=0, column=3, padx=5, sticky="e")

    def load_backups(self):
        """Carga la lista completa de backups desde el gestor."""
        self.all_loaded_backups = backup_manager.list_backups()
        # Initially, sort by timestamp descending (default from list_backups)
        self.sort_key_var.set("Fecha de Creación")
        self.sort_order_asc_var.set(False) # Descending
        self._update_sort_button_text()
        self._apply_filters_and_sort()

    def _apply_filters_and_sort(self, event=None):
        """Filtra y ordena la lista de backups y actualiza el Treeview."""
        filter_type = self.filter_type_var.get()
        search_term = self.search_alias_var.get().lower()
        sort_key = self.sort_key_var.get()
        sort_asc = self.sort_order_asc_var.get()

        # 1. Filter
        filtered_list = self.all_loaded_backups
        if filter_type != "Todos":
            internal_type_map = {
                "Manual": backup_manager.MANUAL_BACKUPS_SUBDIR,
                "Automática": backup_manager.AUTOMATIC_BACKUPS_SUBDIR,
                "Respaldo": backup_manager.PRE_RESTORE_BACKUP_SUBDIR
            }
            internal_type = internal_type_map.get(filter_type)
            if internal_type:
                filtered_list = [b for b in filtered_list if b['type'] == internal_type]

        if search_term:
            filtered_list = [
                b for b in filtered_list 
                if search_term in b['filename'].lower() or 
                   (b['alias'] and search_term in b['alias'].lower())
            ]
        
        # 2. Sort
        if sort_key == "Fecha de Creación":
            filtered_list.sort(key=lambda b: b['timestamp'], reverse=not sort_asc)
        elif sort_key == "Tipo":
            filtered_list.sort(key=lambda b: b['type'], reverse=not sort_asc)
        elif sort_key == "Alias":
            # Sort by alias, putting None/empty aliases last or first based on order
            filtered_list.sort(key=lambda b: (b['alias'] is None, b['alias'] if b['alias'] else ''), reverse=not sort_asc)
        
        self.current_display_list = filtered_list
        self.current_page_backups.set(1) # Reset to first page
        self._populate_treeview()
        self._update_backup_pagination_controls()

    def _reset_filters(self, event=None):
        """Resets filter and sort options to their default values and reloads."""
        self.filter_type_var.set("Todos")
        self.search_alias_var.set("")
        self.sort_key_var.set("Fecha de Creación")
        self.sort_order_asc_var.set(False) # Descending
        self._update_sort_button_text()
        self._apply_filters_and_sort()

    def _toggle_sort_order(self):
        """Cambia el orden de clasificación y reaplica."""
        self.sort_order_asc_var.set(not self.sort_order_asc_var.get())
        self._update_sort_button_text()
        self._apply_filters_and_sort()

    def _update_sort_button_text(self):
        """Actualiza el texto del botón de orden."""
        self.sort_order_button.config(text="Orden: ↑" if self.sort_order_asc_var.get() else "Orden: ↓")

    def _populate_treeview(self):
        """Populates the treeview with the current page of self.current_display_list."""
        for i in self.tree.get_children():
            self.tree.delete(i)

        start_index = (self.current_page_backups.get() - 1) * self.backups_per_page
        end_index = start_index + self.backups_per_page
        self.paginated_list = self.current_display_list[start_index:end_index]
        
        for backup_item in self.paginated_list:
            if backup_item['type'] == backup_manager.AUTOMATIC_BACKUPS_SUBDIR:
                backup_type_display = "Automática"
            elif backup_item['type'] == backup_manager.MANUAL_BACKUPS_SUBDIR:
                backup_type_display = "Manual"
            elif backup_item['type'] == backup_manager.PRE_RESTORE_BACKUP_SUBDIR:
                backup_type_display = "Respaldo"
            else:
                backup_type_display = "Desconocido" # Fallback

            # Ensure timestamp is a datetime object before formatting
            timestamp_obj = backup_item['timestamp']
            if isinstance(timestamp_obj, datetime.datetime):
                 timestamp_display = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
            else: # Fallback if timestamp is not as expected (e.g. None or already string)
                 timestamp_display = str(timestamp_obj) if timestamp_obj else "N/A"
            
            alias_display = backup_item['alias'] if backup_item['alias'] else ""
            
            self.tree.insert("", tk.END, values=(
                backup_type_display, 
                timestamp_display, 
                alias_display,
                backup_item['filename'] 
            ))
        
        # Dynamic Treeview height
        # Show rows for a full page, or fewer if less than a page of items. Min 1 row.
        # If paginated_list is empty, display_count will be 0, so max(1,0) is 1.
        # If paginated_list has items, it will be len(self.paginated_list).
        # The initial height is set by self.backups_per_page.
        # We no longer dynamically shrink the treeview height here.
        # display_count = len(self.paginated_list)
        # self.tree.config(height=max(1, display_count)) # Removed to keep height fixed by backups_per_page

        self.on_backup_selected(None) # Update button states

    def _update_backup_pagination_controls(self):
        """Updates the pagination controls' state and label."""
        num_items = len(self.current_display_list)
        self.total_pages_backups.set(max(1, (num_items + self.backups_per_page - 1) // self.backups_per_page))
        
        current_pg = self.current_page_backups.get()
        total_pg = self.total_pages_backups.get()

        self.lbl_page_backups.config(text=f"Página: {current_pg} / {total_pg}")
        logger.debug(f"Updating pagination: Current Page: {current_pg}, Total Pages: {total_pg}, Items: {num_items}, Per Page: {self.backups_per_page}")

        if total_pg <= 1:
            logger.debug("Hiding pagination controls.")
            # Hide the entire pagination frame if only one page or no items
            if hasattr(self, 'pagination_controls_frame'): # Check if frame exists
                 self.pagination_controls_frame.grid_remove()
        else:
            logger.debug("Showing pagination controls.")
            if hasattr(self, 'pagination_controls_frame'):
                 self.pagination_controls_frame.grid() # Ensure it's visible
            self.btn_first_page_backups.config(state=tk.NORMAL if current_pg > 1 else tk.DISABLED)
            self.btn_prev_page_backups.config(state=tk.NORMAL if current_pg > 1 else tk.DISABLED)
            self.btn_next_page_backups.config(state=tk.NORMAL if current_pg < total_pg else tk.DISABLED)
            self.btn_last_page_backups.config(state=tk.NORMAL if current_pg < total_pg else tk.DISABLED)
            
    def go_to_backup_page(self, direction):
        """Navigates to the first, previous, next, or last page of backups."""
        current_pg = self.current_page_backups.get()
        total_pg = self.total_pages_backups.get()
        new_page = current_pg

        if direction == "first":
            new_page = 1
        elif direction == "prev" and current_pg > 1:
            new_page = current_pg - 1
        elif direction == "next" and current_pg < total_pg:
            new_page = current_pg + 1
        elif direction == "last":
            new_page = total_pg
        
        if new_page == current_pg and direction not in ["first", "last"]: # Avoid re-render if no change unless forcing first/last
            if not ( (direction == "first" and current_pg == 1) or (direction == "last" and current_pg == total_pg) ):
                 return # No change needed

        self.current_page_backups.set(new_page)
        self._populate_treeview()
        self._update_backup_pagination_controls()


    def on_backup_selected(self, event=None):
        """Actualiza el estado de los botones cuando se selecciona un backup."""
        selected_item_id = self.tree.focus() # Obtiene el ID del item seleccionado
        if not selected_item_id:
            self.btn_restore.config(state=tk.DISABLED) # Revert to default style when disabled
            self.btn_assign_alias.config(state=tk.DISABLED)
            self.btn_delete_manual.config(state=tk.DISABLED) # Revert to default style
            return

        selected_values = self.tree.item(selected_item_id, "values")
        backup_type_display = selected_values[0]
        # backup_filename = selected_values[3] # Filename is at index 3

        is_manual = (backup_type_display == "Manual")
        # "Eliminar Manual" is enabled only if a manual backup is selected.
        self.btn_restore.config(state=tk.NORMAL, style="Green.TButton")
        self.btn_assign_alias.config(state=tk.NORMAL) 
        self.btn_delete_manual.config(state=tk.NORMAL if is_manual else tk.DISABLED, style="Danger.TButton")


    def create_manual_backup_action(self):
        """Acción para crear una copia de seguridad manual."""
        alias = simpledialog.askstring("Alias para Copia Manual", 
                                       "Ingrese un alias opcional para esta copia de seguridad manual:",
                                       parent=self)
        
        if alias is None: # User cancelled alias input
            return

        # Proceed with creation if alias was not None (even if empty string)
        if not self.app_settings.enable_manual_backups:
            messagebox.showwarning("Deshabilitado", 
                                   "La creación de copias de seguridad manuales está desactivada en la configuración.", 
                                       parent=self)
            return
        # Proceed with creation if alias was not None (even if empty string)
        # The try block was incorrectly indented under the return statement above.
        try:
            logger.info(f"Attempting to create manual backup with alias: '{alias if alias else 'No Alias'}'")
            backup_path = backup_manager.create_backup(backup_manager.MANUAL_BACKUPS_SUBDIR)
            if backup_path: # Backup was created successfully
                if alias.strip(): # Only add alias if it's not empty
                    backup_manager.add_backup_alias(backup_manager.MANUAL_BACKUPS_SUBDIR, backup_path.name, alias.strip())
                messagebox.showinfo("Éxito", f"Copia de seguridad manual '{backup_path.name}' creada exitosamente.", parent=self)
                self.load_backups()
            else: # Backup creation failed or was prevented
                # Check if it was due to limit
                # settings = AppSettings() # AppSettings is available as self.app_settings
                max_manual_bkups = self.app_settings.max_manual_backups
                
                # Re-fetch existing backups count to be sure about the reason
                existing_manual_backups = [
                    b for b in backup_manager.list_backups() 
                    if b['type'] == backup_manager.MANUAL_BACKUPS_SUBDIR
                ]
                num_existing_manual = len(existing_manual_backups)

                if max_manual_bkups > 0 and num_existing_manual >= max_manual_bkups:
                    messagebox.showwarning("Límite Alcanzado", 
                                           f"No se puede crear la copia de seguridad manual.\n"
                                           f"Se ha alcanzado el límite de {max_manual_bkups} copias manuales.\n\n"
                                           "Por favor, elimine una copia existente para continuar.", 
                                           parent=self)
                elif max_manual_bkups == 0:
                     messagebox.showwarning("Deshabilitado",
                                           "La creación de copias de seguridad manuales está deshabilitada (límite configurado a 0).\n\n"
                                           "Puede cambiar esta configuración en Archivo > Configuración > Copias de Seguridad.",
                                           parent=self)
                else:
                    # Generic error if not due to limit (e.g., disk error)
                    messagebox.showerror("Error", "No se pudo crear la copia de seguridad manual.\nConsulte los logs para más detalles.", parent=self)
        except Exception as e:
            logger.error(f"Error creando copia manual: {e}", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error al crear la copia manual:\n{e}", parent=self)

    def restore_selected_action(self):
        """Acción para restaurar una copia de seguridad seleccionada."""
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una copia de seguridad para restaurar.", parent=self)
            return

        selected_values = self.tree.item(selected_item_id, "values")
        backup_filename = selected_values[3] # Filename is at index 3
        backup_type_display = selected_values[0]

        if backup_type_display == "Automática":
            backup_type_internal = backup_manager.AUTOMATIC_BACKUPS_SUBDIR
        elif backup_type_display == "Manual":
            backup_type_internal = backup_manager.MANUAL_BACKUPS_SUBDIR
        elif backup_type_display == "Respaldo":
            backup_type_internal = backup_manager.PRE_RESTORE_BACKUP_SUBDIR
        else:
            messagebox.showerror("Error Desconocido", f"Tipo de backup desconocido: {backup_type_display}", parent=self)
            return
        
        if backup_type_internal == backup_manager.MANUAL_BACKUPS_SUBDIR and \
           not self.app_settings.enable_manual_backups:
            messagebox.showwarning("Deshabilitado", 
                                   "La restauración de copias de seguridad manuales está desactivada en la configuración.", 
                                   parent=self)
            return
        if backup_type_internal == backup_manager.AUTOMATIC_BACKUPS_SUBDIR and \
           not self.app_settings.enable_automatic_backups:
            messagebox.showwarning("Deshabilitado", 
                                   "La restauración de copias de seguridad automáticas está desactivada en la configuración.", 
                                   parent=self)
            return

        app_base_dir = get_application_base_dir()
        full_backup_path = app_base_dir / backup_manager.BACKUPS_DIR_NAME / backup_type_internal / backup_filename

        if not messagebox.askokcancel("Confirmar Restauración", 
                                     f"¿Está seguro de que desea restaurar el sistema desde la copia '{backup_filename}'?\n\n"
                                     "ESTA ACCIÓN ES IRREVERSIBLE y reemplazará todos los datos actuales del estudio, "
                                     "la base de datos y la configuración.",
                                     icon='warning', parent=self):
            return

        # Second, more emphatic confirmation for restore
        confirm_restore2 = messagebox.askokcancel("Restaurar Copia de Seguridad - ¡CONFIRMACIÓN FINAL!",
                                     f"ADVERTENCIA: Está a punto de reemplazar TODOS los datos actuales con la copia '{backup_filename}'.\n\n"
                                     "Esta acción NO SE PUEDE DESHACER.\n\n"
                                     "¿Está ABSOLUTAMENTE SEGURO de que desea proceder con la restauración?",
                                     icon='error', parent=self) # Removed default=messagebox.NO
        if not confirm_restore2:
            return

        # Create a "respaldo" backup before restoring, if enabled in settings
        # Assuming new AppSettings: enable_pre_restore_backups, max_pre_restore_backups, pre_restore_backup_cooldown_seconds
        if self.app_settings.get_bool_setting('enable_pre_restore_backups', True): # Default to True if not set
            logger.info("Creando copia de seguridad tipo 'Respaldo' antes de la restauración...")
            pre_restore_backup_path = backup_manager.create_backup(backup_manager.PRE_RESTORE_BACKUP_SUBDIR)
            if pre_restore_backup_path:
                messagebox.showinfo("Copia de Respaldo Pre-Restauración", # Changed title and type description
                                    f"Se ha creado una copia de respaldo ('{pre_restore_backup_path.name}') antes de proceder con la restauración.",
                                    parent=self)
                self.load_backups() # Refresh list to show new backup
            else:
                if not messagebox.askyesno("Error Pre-Restauración",
                                                 "No se pudo crear la copia de seguridad automática antes de la restauración.\n"
                                                 "¿Desea continuar con la restauración SIN esta copia de seguridad adicional?",
                                                 icon='error', parent=self):
                    return # User chose not to proceed

        try:
            logger.info(f"Attempting to restore from {full_backup_path}")
            success = backup_manager.restore_backup(full_backup_path)
            
            if success:
                messagebox.showinfo("Restauración Exitosa", 
                                    "El sistema ha sido restaurado exitosamente desde la copia de seguridad.\n\n"
                                    "La aplicación AHORA SE CERRARÁ.\n"
                                    "Por favor, vuelva a iniciar KineViz manualmente.",
                                    parent=self)
                
                self.restart_required_after_restore = True # Signal that a restart is needed
                self.destroy() # Close this dialog
                # The calling dialog (ConfigDialog) or MainWindow will handle the restart logic
                # by checking self.restart_required_after_restore.
            else:
                messagebox.showerror("Error de Restauración", 
                                     "No se pudo restaurar el sistema desde la copia de seguridad.\n"
                                     "Consulte los logs para más detalles.", 
                                     parent=self)
        except Exception as e:
            logger.error(f"Error durante el proceso de restauración de {backup_filename}: {e}", exc_info=True)
            messagebox.showerror("Error Crítico de Restauración", 
                                 f"Ocurrió un error crítico durante la restauración:\n{e}\n\n"
                                 "El estado de la aplicación puede ser inconsistente. Se recomienda revisar los logs.", 
                                 parent=self)


    def assign_alias_action(self):
        """Acción para asignar o editar un alias a una copia manual."""
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una copia de seguridad manual.", parent=self)
            return

        selected_values = self.tree.item(selected_item_id, "values")
        backup_type_display = selected_values[0]
        current_alias = selected_values[2] # Alias is at index 2
        backup_filename = selected_values[3] # Filename is at index 3
        
        # Determine internal backup type string (e.g., "automatic" or "manual")
        if backup_type_display == "Automática":
            backup_type_internal = backup_manager.AUTOMATIC_BACKUPS_SUBDIR
        elif backup_type_display == "Manual":
            backup_type_internal = backup_manager.MANUAL_BACKUPS_SUBDIR
        elif backup_type_display == "Respaldo":
            backup_type_internal = backup_manager.PRE_RESTORE_BACKUP_SUBDIR
        else:
            logger.error(f"Unknown backup_type_display for alias assignment: {backup_type_display}")
            messagebox.showerror("Error", f"Tipo de copia de seguridad desconocido: {backup_type_display}", parent=self)
            return

        new_alias = simpledialog.askstring("Asignar/Editar Alias", 
                                           f"Ingrese un nuevo alias para la copia '{backup_filename}' ({backup_type_display}):\n(Deje vacío para quitar el alias actual)",
                                           initialvalue=current_alias,
                                           parent=self)

        if new_alias is not None: # User didn't cancel
            try:
                if new_alias.strip():
                    backup_manager.add_backup_alias(backup_type_internal, backup_filename, new_alias.strip())
                    messagebox.showinfo("Éxito", f"Alias actualizado para '{backup_filename}'.", parent=self)
                else: # Empty string means remove alias
                    backup_manager.remove_backup_alias(backup_type_internal, backup_filename)
                    messagebox.showinfo("Éxito", f"Alias eliminado para '{backup_filename}'.", parent=self)
                self.load_backups()
            except Exception as e:
                logger.error(f"Error asignando alias a {backup_type_internal}/{backup_filename}: {e}", exc_info=True)
                messagebox.showerror("Error", f"Ocurrió un error al asignar el alias:\n{e}", parent=self)


    def _delete_manual_backup_action(self): # Renamed from _delete_selected_backup_action
        """Acción para eliminar una copia de seguridad manual seleccionada."""
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una copia de seguridad manual para eliminar.", parent=self)
            return

        selected_values = self.tree.item(selected_item_id, "values")
        backup_type_display = selected_values[0]
        backup_filename = selected_values[3]

        if backup_type_display != "Manual": # Only allow deleting manual backups
            messagebox.showwarning("Tipo Inválido", "Solo se pueden eliminar copias de seguridad manuales desde esta opción.", parent=self)
            return

        # First confirmation
        confirm1 = messagebox.askokcancel("Confirmar Eliminación - Paso 1 de 2",
                                     f"¿Está seguro de que desea eliminar la copia de seguridad manual '{backup_filename}'?\n\n"
                                     "Esta acción no se puede deshacer.",
                                     icon='warning', parent=self)
        if not confirm1:
            return

        # Second confirmation
        confirm2 = messagebox.askokcancel("Confirmar Eliminación - Paso 2 de 2",
                                     f"¡ADVERTENCIA FINAL!\n\n"
                                     f"La copia de seguridad manual '{backup_filename}' será eliminada permanentemente.\n"
                                     "¿Está ABSOLUTAMENTE SEGURO de que desea proceder?",
                                     icon='error', parent=self)
        if not confirm2:
            return
        
        try:
            success = backup_manager.delete_manual_backup(backup_filename) # Call existing method
            if success:
                messagebox.showinfo("Éxito", f"Copia de seguridad manual '{backup_filename}' eliminada.", parent=self)
                self.load_backups()
            else:
                messagebox.showerror("Error", f"No se pudo eliminar la copia de seguridad manual '{backup_filename}'.", parent=self)
        except Exception as e:
            logger.error(f"Error eliminando copia manual {backup_filename}: {e}", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error al eliminar la copia manual:\n{e}", parent=self)


if __name__ == '__main__':
    # This is a basic test, assumes backup_manager and AppSettings are available
    # and that some dummy backup files might exist or be created by backup_manager tests.
    
    # Setup dummy logger for testing
    logging.basicConfig(level=logging.DEBUG)
    # logger is already defined at module level

    # Create dummy AppSettings
    class DummyAppSettings:
        def __init__(self):
            self.enable_hover_tooltips = True
            # Add other settings if BackupRestoreDialog directly uses them

    root = tk.Tk()
    root.title("Test Root")
    
    # Create dummy backup files for testing list_backups
    # You would need to adapt this to your backup_manager's structure
    dummy_backup_dir = backup_manager.get_project_root() / backup_manager.BACKUPS_DIR_NAME
    (dummy_backup_dir / backup_manager.AUTOMATIC_BACKUPS_SUBDIR).mkdir(parents=True, exist_ok=True)
    (dummy_backup_dir / backup_manager.MANUAL_BACKUPS_SUBDIR).mkdir(parents=True, exist_ok=True)
    
    now = datetime.datetime.now()
    (dummy_backup_dir / backup_manager.AUTOMATIC_BACKUPS_SUBDIR / f"backup_{now.strftime('%Y%m%d_%H%M%S')}.zip").write_text("auto content")
    time.sleep(1) # Ensure distinct timestamp for manual backup
    now_manual = datetime.datetime.now()
    manual_fn = f"backup_{now_manual.strftime('%Y%m%d_%H%M%S')}.zip"
    (dummy_backup_dir / backup_manager.MANUAL_BACKUPS_SUBDIR / manual_fn).write_text("manual content")
    
    # Dummy alias file
    aliases = {manual_fn: "Test Manual Alias"}
    backup_manager._save_manual_backup_aliases(aliases)


    app_settings_instance = DummyAppSettings()
    
    def open_dialog():
        dialog = BackupRestoreDialog(root, app_settings_instance)
        root.wait_window(dialog)

    ttk.Button(root, text="Open Backup/Restore Dialog", command=open_dialog).pack(padx=20, pady=20)
    
    root.mainloop()

    # Clean up dummy files (optional)
    # import shutil # Already imported if needed for cleanup
    # shutil.rmtree(dummy_backup_dir, ignore_errors=True)
    logger.info("Test finished. Manual cleanup of 'backups' directory might be needed.")
