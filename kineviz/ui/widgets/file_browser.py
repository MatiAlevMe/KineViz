import tkinter as tk
from tkinter import ttk, messagebox
import os # Necesario para os.startfile
import sys # Necesario para sys.platform
import subprocess # Necesario para open/xdg-open
from pathlib import Path # Para manejar rutas de archivo
import logging # Importar logging
# Importar FileService para type hinting
from kineviz.core.services.file_service import FileService
from kineviz.config.settings import AppSettings # Import AppSettings
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # Import font utilities
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip


logger = logging.getLogger(__name__) # Logger para este módulo

class FileBrowser(ttk.Frame):
    def __init__(self, parent, file_service: FileService, study_id: int, files_per_page: int = 10, settings: AppSettings = None, pagination_parent=None):
        super().__init__(parent)
        self.file_service = file_service
        self.study_id = study_id
        self.files_per_page = files_per_page
        self.settings = settings # Store AppSettings instance
        self.pagination_parent = pagination_parent # Store the custom parent for pagination

        # Estado de paginación y filtros
        self.current_page = 1
        self.total_files = 0
        self.total_pages = 1
        self.search_var = tk.StringVar()
        self.filter_type_var = tk.StringVar(value="Todos")
        self.filter_freq_var = tk.StringVar(value="Todos")

        self.create_widgets()
        self.load_files() # Carga inicial
        self.update_font_scaling()

    def create_widgets(self):
        # --- Frame para Filtros y Búsqueda ---
        # Asegurar estilos en la ventana principal
        self.configure(style='TFrame')

        # Frame para Filtros
        filter_frame = ttk.Frame(self, style='TFrame')
        filter_frame.pack(fill=tk.X, pady=(0, 5))

        # Búsqueda
        ttk.Label(filter_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        scaled_font_tuple = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale if self.settings else 1.0)
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, font=scaled_font_tuple) # Added font
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", lambda event: self.apply_filters())

        # Filtro Tipo
        ttk.Label(filter_frame, text="Tipo:").pack(side=tk.LEFT, padx=(10, 5))
        type_options = ["Todos", "Processed", "Original"]
        self.type_menu = ttk.Combobox(filter_frame, textvariable=self.filter_type_var, values=type_options, state="readonly", style='TCombobox')
        self.type_menu.set(type_options[0])  # Establecer el valor por defecto
        self.type_menu.pack(side=tk.LEFT, padx=5)

        # Filtro Tipo de Dato
        ttk.Label(filter_frame, text="Tipo de Dato:").pack(side=tk.LEFT, padx=(10, 5))
        freq_options = ["Todos", "Cinematica", "Cinetica", "Electromiografica", "N/A"]
        self.freq_menu = ttk.Combobox(filter_frame, textvariable=self.filter_freq_var, values=freq_options, state="readonly", style="TCombobox")
        self.freq_menu.set(freq_options[0])  # Establecer el valor por defecto
        self.freq_menu.pack(side=tk.LEFT, padx=5)
        
        # Botones de Filtro
        apply_button = ttk.Button(filter_frame, text="Aplicar", command=self.apply_filters, style="Celeste.TButton")
        apply_button.pack(side=tk.LEFT, padx=5)
        Tooltip(apply_button, text="Aplicar los filtros de búsqueda, tipo y tipo de dato.", short_text="Aplicar filtros.", enabled=self.settings.enable_hover_tooltips if self.settings else False)

        clear_button = ttk.Button(filter_frame, text="Limpiar", command=self.clear_filters)
        clear_button.pack(side=tk.LEFT, padx=(0,5))
        Tooltip(clear_button, text="Limpiar todos los filtros y mostrar todos los archivos.", short_text="Limpiar filtros.", enabled=self.settings.enable_hover_tooltips if self.settings else False)

        refresh_button = ttk.Button(filter_frame, text="Refrescar", command=self.load_files)
        refresh_button.pack(side=tk.LEFT, padx=5)
        Tooltip(refresh_button, text="Recargar la lista de archivos del estudio.", short_text="Recargar lista.", enabled=self.settings.enable_hover_tooltips if self.settings else False)

        # --- Tabla de Archivos ---
        # Crear tabla de archivos directamente en self (FileBrowser frame)
        # y establecer su altura según files_per_page.
        columns = ('Participante', 'Nombre', 'Tipo', 'Tipo de Dato') # Removed Ver, Eliminar
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode="extended", height=self.files_per_page)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='w') # Default anchor to 'w'

        # Pack the tree directly. It will fill horizontally but not expand vertically beyond its requested height.
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0,5), padx=5) # Changed to fill=tk.BOTH, expand=True

        # Configurar eventos
        self.tree.bind('<ButtonRelease-1>', self.on_tree_click)
        self.tree.bind('<<TreeviewSelect>>', self._on_fb_selection_change)

        # --- Frame para Paginación ---
        # If a custom parent is provided for pagination, use it. Otherwise, pack locally.
        if self.pagination_parent:
            # If pagination is internal, pack it after the tree.
            # Pack the pagination frame into its custom parent
            # when provided. Otherwise, it will be packed below.
            self.pagination_frame = ttk.Frame(self.pagination_parent)
            self.pagination_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0), padx=5)
        else:
            self.pagination_frame = ttk.Frame(self)
            self.pagination_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0), padx=5)

        # Apply styles to comboboxes
        # self.type_menu.bind("<Enter>", lambda event: self.type_menu.configure(style='Hover.TCombobox'))
        # self.type_menu.bind("<Leave>", lambda event: self.type_menu.configure(style='TCombobox'))

        # self.freq_menu.bind("<Enter>", lambda event: self.freq_menu.configure(style='Hover.TCombobox'))
        # self.freq_menu.bind("<Leave>", lambda event: self.freq_menu.configure(style='TCombobox'))

    def load_files(self):
        """Carga los archivos filtrados y paginados usando FileService."""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Obtener parámetros de filtro/búsqueda
        search_query = self.search_var.get() or None
        file_type_filter = self.filter_type_var.get()
        frequency_filter = self.filter_freq_var.get()

        try:
            # Obtener archivos paginados y filtrados
            files_on_page, self.total_files = self.file_service.get_study_files(
                study_id=self.study_id,
                page=self.current_page,
                per_page=self.files_per_page,
                search_term=search_query,
                file_type=file_type_filter if file_type_filter != "Todos" else None,
                frequency=frequency_filter if frequency_filter != "Todos" else None
            )

            # Calcular total de páginas
            self.total_pages = (self.total_files // self.files_per_page) + \
                               (1 if self.total_files % self.files_per_page else 0)
            self.total_pages = max(1, self.total_pages) # Asegurar al menos 1 página

            # Llenar tabla
            for file_info in files_on_page:
                # Indent this line
                self.tree.insert('', 'end', values=(
                    str(file_info.get('patient', 'N/A')),
                    str(file_info.get('name', 'N/A')),
                    str(file_info.get('type', 'N/A')),
                    str(file_info.get('frequency', 'N/A')),
                ), tags=(str(file_info.get('path', '')),)) # Guardar la ruta como string en tags

            self.update_pagination_controls()

        except Exception as e:
            logger.error(f"Error al cargar archivos para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error al Cargar Archivos", f"No se pudieron cargar los archivos del estudio:\n{e}", parent=self)
            self.total_files = 0
            self.total_pages = 1
            self.update_pagination_controls() # Actualizar controles incluso en error
            # import traceback # Ya no es necesario
            # traceback.print_exc() # Reemplazado por logger

    def apply_filters(self):
        """Aplica los filtros y búsqueda, reseteando a la página 1."""
        self.current_page = 1
        self.load_files()

    def clear_filters(self):
        """Limpia los filtros y búsqueda, y recarga los archivos."""
        self.search_var.set("")
        self.filter_type_var.set("Todos")
        self.filter_freq_var.set("Todos")
        self.current_page = 1
        self.load_files()

    def update_pagination_controls(self):
        """Actualiza los botones y etiqueta de paginación."""
        # Limpiar controles existentes
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()

        if self.total_pages <= 1:
            return # No mostrar si solo hay una página

        # --- Left-aligned buttons ---
        # Botón Primera Página
        first_btn = ttk.Button(self.pagination_frame, text="<<", command=lambda: self.go_to_page(1))
        first_btn.pack(side=tk.LEFT, padx=2)
        Tooltip(first_btn, text="Ir a la primera página.", short_text="Primera página.", enabled=self.settings.enable_hover_tooltips if self.settings else False)
        if self.current_page == 1:
            first_btn.config(state=tk.DISABLED)

        # Botón Anterior
        prev_btn = ttk.Button(self.pagination_frame, text="<", command=lambda: self.go_to_page(self.current_page - 1))
        prev_btn.pack(side=tk.LEFT, padx=2)
        Tooltip(prev_btn, text="Ir a la página anterior.", short_text="Página anterior.", enabled=self.settings.enable_hover_tooltips if self.settings else False)
        if self.current_page == 1:
            prev_btn.config(state=tk.DISABLED)

        # --- Right-aligned buttons (packed in reverse visual order) ---
        # Botón Última Página
        last_btn = ttk.Button(self.pagination_frame, text=">>", command=lambda: self.go_to_page(self.total_pages))
        last_btn.pack(side=tk.RIGHT, padx=2)
        Tooltip(last_btn, text="Ir a la última página.", short_text="Última página.", enabled=self.settings.enable_hover_tooltips if self.settings else False)
        if self.current_page == self.total_pages:
            last_btn.config(state=tk.DISABLED)

        # Botón Siguiente
        next_btn = ttk.Button(self.pagination_frame, text=">", command=lambda: self.go_to_page(self.current_page + 1))
        next_btn.pack(side=tk.RIGHT, padx=2)
        Tooltip(next_btn, text="Ir a la página siguiente.", short_text="Página siguiente.", enabled=self.settings.enable_hover_tooltips if self.settings else False)
        if self.current_page == self.total_pages:
            next_btn.config(state=tk.DISABLED)

        # --- Center-aligned label (fills remaining space) ---
        # Etiqueta de Página Actual
        page_label = ttk.Label(self.pagination_frame, text=f"Página {self.current_page} de {self.total_pages} ({self.total_files} archivos)")
        page_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)


    def go_to_page(self, page_number):
        """Navega a una página específica."""
        if 1 <= page_number <= self.total_pages:
            self.current_page = page_number
            self.load_files()
        else:
            logger.warning(f"Intento de ir a página inválida {page_number} (Total: {self.total_pages})")

    def _on_fb_selection_change(self, event=None):
        """Emite un evento cuando la selección en el FileBrowser cambia."""
        self.event_generate("<<FileBrowserSelectionChanged>>")

    def get_selected_file_paths(self) -> list[Path]:
        """Retorna una lista de objetos Path para los archivos seleccionados."""
        selected_paths = []
        selected_items = self.tree.selection()
        for item_id in selected_items:
            item_tags = self.tree.item(item_id, "tags")
            if item_tags and item_tags[0]:
                try:
                    # El tag es la ruta como string, convertir a Path
                    selected_paths.append(Path(item_tags[0]))
                except Exception as e:
                    logger.error(f"Error convirtiendo tag a Path: {item_tags[0]}, error: {e}")
        return selected_paths

    def on_tree_click(self, event):
        """Maneja los clics en la tabla de archivos."""
        # Si hay múltiples selecciones, no procesar clics de celda individuales
        if len(self.tree.selection()) > 1:
            return

        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column_id = self.tree.identify_column(event.x) # ej: '#5'
        row_id = self.tree.identify_row(event.y) # ej: 'I001'

        if not row_id: # Clic fuera de las filas
            return

        # Obtener la ruta del archivo desde los tags
        item_tags = self.tree.item(row_id, "tags")
        if not item_tags or not item_tags[0]:
            messagebox.showwarning("Advertencia", "No se pudo obtener la ruta del archivo seleccionado.", parent=self)
            return
        file_path_str = item_tags[0]
        file_path = Path(file_path_str) # Convertir a Path

        # Column click actions are removed as they are handled by buttons in StudyView
        # This method might still be useful for double-click to view, if desired later.
        # For now, it does nothing if columns are clicked.
        pass

    def view_file(self, file_path: Path):
        """Abre el archivo seleccionado con la aplicación predeterminada."""
        if not file_path.exists():
             messagebox.showerror("Error", f"El archivo no existe:\n{file_path}", parent=self)
             return
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin': # macOS
                subprocess.run(['open', file_path], check=True)
            else: # Linux, etc.
                subprocess.run(['xdg-open', file_path], check=True)
        except FileNotFoundError:
             messagebox.showerror("Error", f"No se pudo encontrar la aplicación para abrir el archivo:\n{file_path}", parent=self)
        except subprocess.CalledProcessError as e:
             messagebox.showerror("Error", f"El comando para abrir el archivo falló:\n{e}", parent=self)
        except Exception as e:
            logger.error(f"Error al intentar abrir archivo {file_path}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir el archivo '{file_path.name}':\n{str(e)}", parent=self)

    def delete_file(self, file_path: Path, item_id):
        """Solicita confirmación y elimina un archivo usando FileService."""
        if not file_path.exists():
             messagebox.showerror("Error", f"El archivo ya no existe:\n{file_path}", parent=self)
             self.load_files() # Recargar lista completa si el archivo no existe
             return

        file_name = file_path.name
        if messagebox.askyesno("Confirmar Eliminación",
                               f"¿Está seguro de que desea eliminar el archivo:\n'{file_name}'?\n\nEsta acción es permanente.",
                               icon='warning', parent=self):
            try:
                # Usar el file_service para eliminar, pasando el study_id
                self.file_service.delete_file(file_path, self.study_id)
                messagebox.showinfo("Éxito", f"Archivo '{file_name}' eliminado correctamente.", parent=self)
                # Eliminar solo el item de la tabla en lugar de recargar todo
                # self.tree.delete(item_id) # Esto puede desincronizar la paginación
                # Mejor recargar la página actual para reflejar el cambio y la paginación correcta
                self.load_files()
            except FileNotFoundError:
                 messagebox.showerror("Error", f"El archivo no se encontró al intentar eliminarlo:\n{file_path}", parent=self)
                 self.load_files() # Recargar lista completa
            except Exception as e:
                logger.error(f"Error al eliminar archivo {file_path} para estudio {self.study_id}: {e}", exc_info=True)
                messagebox.showerror("Error al Eliminar", f"No se pudo eliminar el archivo:\n{e}", parent=self)
                # import traceback # Ya no es necesario
                # traceback.print_exc() # Reemplazado por logger
    def update_font_scaling(self):
        if self.settings:
            scaled_font_tuple = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)
            style = ttk.Style()

            # Update the font of the Treeview
            style.configure('Treeview.Heading', font=scaled_font_tuple)
            style.configure('Treeview', font=scaled_font_tuple)

            # Update the font of the TCombobox style
            style.configure('TCombobox', font=scaled_font_tuple)

            # Update the instances of Combobox
            self.type_menu.configure(font=scaled_font_tuple)
            self.freq_menu.configure(font=scaled_font_tuple)

            # Update the font of the dropdown list (Listbox)
            font_string = f"{scaled_font_tuple[0]} {scaled_font_tuple[1]} {scaled_font_tuple[2]}"

            # Use self.master to refer to the root window
            self.type_menu.master.option_add("*TCombobox*Listbox.font", font_string)
            self.freq_menu.master.option_add("*TCombobox*Listbox.font", font_string)
