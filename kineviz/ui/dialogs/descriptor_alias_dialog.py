import tkinter as tk
from tkinter import ttk, Toplevel, messagebox
import logging

from kineviz.core.services.study_service import StudyService
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip
from kineviz.config.settings import AppSettings # Import AppSettings
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE # Import font utilities

logger = logging.getLogger(__name__)

class DescriptorAliasDialog(Toplevel):
    """Diálogo para gestionar alias de sub-valores definidos en un estudio."""

    # Cambiar app_settings y file_service por study_service
    def __init__(self, parent, study_service: StudyService, study_id: int, settings: AppSettings):
        super().__init__(parent)
        # self.app_settings = app_settings # Ya no se usa
        # self.file_service = file_service # Ya no se usa
        self.study_service = study_service # Usar StudyService
        self.study_id = study_id
        self.settings = settings # Store AppSettings instance

        self.title(f"Gestionar Alias de Sub-valores (Estudio {study_id})")
        self.geometry("500x400")
        self.resizable(True, True)

        # Diccionario para almacenar las variables de entrada de alias
        self.alias_vars = {}
        # Almacenar sub-valores definidos en el estudio
        self.defined_descriptors = set()
        # Almacenar alias actuales del estudio
        self.current_aliases = {}

        # --- Bottom Fixed Frame for Action Buttons (Packed first for bottom placement) ---
        self.bottom_action_buttons_frame = ttk.Frame(self, padding=(10, 10, 10, 10))
        self.bottom_action_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Middle Scrollable Area (Canvas Container) ---
        self.canvas_container = ttk.Frame(self) # Takes remaining space
        self.canvas_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(10,0)) # Add padding

        self.canvas = tk.Canvas(self.canvas_container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(self.canvas_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(self.canvas_container, orient="horizontal", command=self.canvas.xview)
        
        self.scrollable_frame = ttk.Frame(self.canvas) # Content goes here

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")) if hasattr(self, 'canvas') and self.canvas.winfo_exists() else None
        )
        
        self.canvas_interior_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.canvas.bind("<Configure>", self._dynamic_canvas_item_width_configure)

        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        # --- End Scrollable Area Setup ---

        self.create_widgets() # No longer takes parent_frame
        self.load_descriptors_and_aliases()

        # Centrar diálogo
        self.transient(parent)
        self.grab_set()

        # Definir estilo para el botón de ayuda
        style = ttk.Style()
        style.configure("Help.TButton", foreground="white", background="blue") # This might be better in main_window style config

    def _dynamic_canvas_item_width_configure(self, event):
        """
        Adjusts the width of the scrollable_frame (canvas window item)
        to be the maximum of its natural content width and the canvas's current width.
        """
        canvas_width = event.width
        if hasattr(self, 'scrollable_frame') and self.scrollable_frame.winfo_exists():
            self.scrollable_frame.update_idletasks() # Ensure natural width is calculated
            content_natural_width = self.scrollable_frame.winfo_reqwidth()
        else:
            content_natural_width = canvas_width # Fallback
            
        effective_width = max(content_natural_width, canvas_width)
        
        if hasattr(self, 'canvas_interior_id') and self.canvas_interior_id and \
           hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.itemconfig(self.canvas_interior_id, width=effective_width)

    def _show_input_help(self, title: str, message: str):
        """Muestra un popup de ayuda simple."""
        messagebox.showinfo(title, message, parent=self)

    def create_widgets(self):
        """Crea los widgets del diálogo."""
        # Content for self.scrollable_frame
        # Instrucciones
        ttk.Label(self.scrollable_frame, text="Asigne un alias descriptivo a cada sub-valor definido para este estudio.", wraplength=450).pack(pady=(0, 10), padx=10)

        # Frame para la tabla de alias (usaremos grid aquí)
        self.alias_grid_frame = ttk.Frame(self.scrollable_frame)
        self.alias_grid_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self.alias_grid_frame.columnconfigure(1, weight=1) # Columna de alias expandible

        # Cabeceras con fuente escalada
        header_font = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale, weight="bold")
        ttk.Label(self.alias_grid_frame, text="Sub-valor Definido", font=header_font).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.alias_grid_frame, text="Alias Asignado", font=header_font).grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Los sub-valores se añadirán dinámicamente en load_descriptors_and_aliases

        # Botones de acción en self.bottom_action_buttons_frame
        cancel_button = ttk.Button(self.bottom_action_buttons_frame, text="Cancelar", command=self.destroy)
        cancel_button.pack(side=tk.RIGHT)
        Tooltip(cancel_button, text="Cerrar este diálogo sin guardar cambios.", short_text="Cancelar.", enabled=self.settings.enable_hover_tooltips)
        
        save_button = ttk.Button(self.bottom_action_buttons_frame, text="Guardar Alias", command=self.save_aliases)
        save_button.pack(side=tk.RIGHT, padx=(0,5)) # Add padding between buttons
        Tooltip(save_button, text="Guardar los alias asignados y cerrar el diálogo.", short_text="Guardar.", enabled=self.settings.enable_hover_tooltips)


        # Set minsize after widgets are created
        self.update_idletasks() # Process pending operations
        self.scrollable_frame.update_idletasks()
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.update_idletasks()
        self.minsize(400, 300) # Set a reasonable fixed minimum size

    def load_descriptors_and_aliases(self):
        """Carga los sub-valores definidos en el estudio y sus alias actuales."""
        try:
            # Obtener detalles del estudio para VIs y alias
            study_details = self.study_service.get_study_details(self.study_id)
            independent_variables = study_details.get('independent_variables', [])
            self.current_aliases = study_details.get('aliases', {}) # Guardar alias actuales

            # Extraer todos los sub-valores definidos de la estructura de VIs
            self.defined_descriptors = set()
            for iv in independent_variables:
                # Asumiendo que cada VI es un dict con 'name' y 'descriptors' (lista)
                if isinstance(iv, dict) and 'descriptors' in iv and isinstance(iv['descriptors'], list):
                    for desc in iv['descriptors']:
                        if isinstance(desc, str) and desc.strip(): # Asegurar que sea string no vacío
                            self.defined_descriptors.add(desc.strip())

            logger.info(f"Sub-valores definidos para estudio {self.study_id}: {self.defined_descriptors}")
            logger.debug(f"Aliases actuales para estudio {self.study_id}: {self.current_aliases}")

            # Limpiar entradas anteriores si se recarga
            for widget in self.alias_grid_frame.winfo_children():
                # No eliminar las cabeceras
                if widget.grid_info()['row'] > 0:
                    widget.destroy()
            self.alias_vars.clear()

            # Crear fila para cada descriptor definido
            row_idx = 1 # Empezar después de las cabeceras
            if not self.defined_descriptors:
                 ttk.Label(self.alias_grid_frame, text="No hay sub-valores definidos para este estudio.").grid(row=row_idx, column=0, columnspan=2, pady=10)
            else:
                # Ordenar sub-valores para consistencia
                for descriptor in sorted(list(self.defined_descriptors)):
                    # Etiqueta del descriptor
                    ttk.Label(self.alias_grid_frame, text=descriptor).grid(row=row_idx, column=0, padx=5, pady=2, sticky='w')

                    # Entrada para el alias
                    alias_var = tk.StringVar()
                    # Cargar alias actual del estudio
                    alias_var.set(self.current_aliases.get(descriptor, ""))
                    
                    alias_entry_frame = ttk.Frame(self.alias_grid_frame)
                    alias_entry_frame.grid(row=row_idx, column=1, padx=5, pady=2, sticky='ew')
                    alias_entry_frame.columnconfigure(0, weight=1) # Entry se expande

                    alias_entry = ttk.Entry(alias_entry_frame, textvariable=alias_var)
                    alias_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

                    alias_long_text_template = ("Asigne un alias descriptivo opcional para el sub-valor '{descriptor}'.\n"
                                                "Este alias se usará en gráficos y reportes para mayor claridad.\n"
                                                "Si se deja vacío, se usará el nombre original del sub-valor.\n"
                                                "Ej: Para 'CTRL', el alias podría ser 'Control'.")
                    alias_short_text_template = "Alias opcional para '{descriptor}' (usado en gráficos/reportes)."
                    
                    current_long_text = alias_long_text_template.format(descriptor=descriptor)
                    current_short_text = alias_short_text_template.format(descriptor=descriptor)

                    alias_help_button = ttk.Button(alias_entry_frame, text="?", width=3, style="Help.TButton",
                                                   command=lambda lt=current_long_text, d=descriptor: self._show_input_help(f"Ayuda: Alias para '{d}'", lt))
                    alias_help_button.pack(side=tk.LEFT, padx=(2,0))
                    Tooltip(alias_help_button, text=current_long_text, short_text=current_short_text, enabled=self.settings.enable_hover_tooltips)
                    
                    self.alias_vars[descriptor] = alias_var
                    row_idx += 1

        except Exception as e:
            logger.error(f"Error cargando sub-valores o alias para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los sub-valores o alias:\n{e}", parent=self)

    def save_aliases(self):
        """Guarda los alias modificados para el estudio actual usando StudyService."""
        new_aliases_dict = {}
        changed = False
        for descriptor, alias_var in self.alias_vars.items():
            new_alias = alias_var.get().strip()
            # Guardar solo si el alias no está vacío
            if new_alias:
                new_aliases_dict[descriptor] = new_alias
            # Comparar con los alias originales cargados
            if new_alias != (self.current_aliases.get(descriptor) or ""):
                changed = True

        if not changed:
            messagebox.showinfo("Información", "No se detectaron cambios en los alias.", parent=self)
            self.destroy()
            return

        try:
            # Llamar al servicio para actualizar los alias del estudio
            self.study_service.update_study_aliases(self.study_id, new_aliases_dict)
            messagebox.showinfo("Éxito", "Alias guardados correctamente para este estudio.", parent=self)
            self.destroy() # Cerrar diálogo después de guardar
        except ValueError as ve:
            logger.error(f"Error de validación al guardar alias para estudio {self.study_id}: {ve}", exc_info=True)
            messagebox.showerror("Error de Validación", f"No se pudieron guardar los alias:\n{ve}", parent=self)
        except Exception as e:
            logger.error(f"Error inesperado guardando alias para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error al Guardar", f"Ocurrió un error inesperado al guardar los alias:\n{e}", parent=self)
