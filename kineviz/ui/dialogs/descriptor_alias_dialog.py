import tkinter as tk
from tkinter import ttk, Toplevel, messagebox
import logging
from kineviz.config.settings import AppSettings
from kineviz.core.services.file_service import FileService

logger = logging.getLogger(__name__)

class DescriptorAliasDialog(Toplevel):
    """Diálogo para gestionar alias de descriptores detectados en un estudio."""

    def __init__(self, parent, app_settings: AppSettings, file_service: FileService, study_id: int):
        super().__init__(parent)
        self.app_settings = app_settings
        self.file_service = file_service
        self.study_id = study_id

        self.title(f"Gestionar Alias de Descriptores (Estudio {study_id})")
        self.geometry("500x400")
        self.resizable(True, True)

        # Diccionario para almacenar las variables de entrada de alias
        self.alias_vars = {}
        # Almacenar descriptores detectados
        self.detected_descriptors = set()

        # --- Frame principal con scroll ---
        container_frame = ttk.Frame(self)
        container_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(container_frame)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # --- Fin frame principal con scroll ---

        # Crear widgets dentro del frame desplazable
        self.create_widgets(self.scrollable_frame)
        self.load_descriptors_and_aliases()

        # Centrar diálogo
        self.transient(parent)
        self.grab_set()

    def create_widgets(self, parent_frame):
        """Crea los widgets dentro del frame especificado."""
        main_frame = ttk.Frame(parent_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instrucciones
        ttk.Label(main_frame, text="Asigne un alias descriptivo a cada descriptor detectado en los archivos del estudio.", wraplength=450).pack(pady=(0, 10))

        # Frame para la tabla de alias (usaremos grid aquí)
        self.alias_grid_frame = ttk.Frame(main_frame)
        self.alias_grid_frame.pack(fill=tk.BOTH, expand=True)
        self.alias_grid_frame.columnconfigure(1, weight=1) # Columna de alias expandible

        # Cabeceras (opcional)
        ttk.Label(self.alias_grid_frame, text="Descriptor Detectado", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.alias_grid_frame, text="Alias Asignado", font=('Helvetica', 10, 'bold')).grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Los descriptores se añadirán dinámicamente en load_descriptors_and_aliases

        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        ttk.Button(button_frame, text="Guardar Alias", command=self.save_aliases).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def load_descriptors_and_aliases(self):
        """Carga los descriptores detectados y los alias existentes."""
        try:
            # Obtener descriptores únicos detectados en los archivos del estudio
            params = self.file_service.get_unique_study_parameters(self.study_id)
            self.detected_descriptors = params.get('descriptors', set())
            logger.info(f"Descriptores detectados para estudio {self.study_id}: {self.detected_descriptors}")

            # Obtener alias existentes desde la configuración
            existing_aliases = self.app_settings.get_all_aliases()

            # Limpiar entradas anteriores si se recarga
            for widget in self.alias_grid_frame.winfo_children():
                # No eliminar las cabeceras
                if widget.grid_info()['row'] > 0:
                    widget.destroy()
            self.alias_vars.clear()

            # Crear fila para cada descriptor detectado
            row_idx = 1 # Empezar después de las cabeceras
            if not self.detected_descriptors:
                 ttk.Label(self.alias_grid_frame, text="No se detectaron descriptores en los archivos válidos de este estudio.").grid(row=row_idx, column=0, columnspan=2, pady=10)
            else:
                for descriptor in sorted(list(self.detected_descriptors)):
                    # Etiqueta del descriptor
                    ttk.Label(self.alias_grid_frame, text=descriptor).grid(row=row_idx, column=0, padx=5, pady=2, sticky='w')

                    # Entrada para el alias
                    alias_var = tk.StringVar()
                    alias_var.set(existing_aliases.get(descriptor, "")) # Cargar alias existente o vacío
                    alias_entry = ttk.Entry(self.alias_grid_frame, textvariable=alias_var)
                    alias_entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky='ew')

                    self.alias_vars[descriptor] = alias_var
                    row_idx += 1

        except Exception as e:
            logger.error(f"Error cargando descriptores o alias para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los descriptores o alias:\n{e}", parent=self)

    def save_aliases(self):
        """Guarda los alias modificados en la configuración."""
        try:
            changed = False
            for descriptor, alias_var in self.alias_vars.items():
                new_alias = alias_var.get().strip()
                current_alias = self.app_settings.get_descriptor_alias(descriptor) or ""
                if new_alias != current_alias:
                    self.app_settings.set_descriptor_alias(descriptor, new_alias)
                    changed = True

            if changed:
                self.app_settings.save_settings()
                messagebox.showinfo("Éxito", "Alias guardados correctamente.", parent=self)
            else:
                messagebox.showinfo("Información", "No se detectaron cambios en los alias.", parent=self)

            self.destroy() # Cerrar diálogo después de guardar
        except Exception as e:
            logger.error(f"Error guardando alias: {e}", exc_info=True)
            messagebox.showerror("Error al Guardar", f"Ocurrió un error al guardar los alias:\n{e}", parent=self)
