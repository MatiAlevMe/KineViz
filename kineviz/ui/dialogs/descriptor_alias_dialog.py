import tkinter as tk
from tkinter import ttk, Toplevel, messagebox
import logging

from kineviz.core.services.study_service import StudyService
# Ya no se necesita AppSettings
# from kineviz.config.settings import AppSettings
# Ya no se necesita FileService directamente aquí
# from kineviz.core.services.file_service import FileService

logger = logging.getLogger(__name__)

class DescriptorAliasDialog(Toplevel):
    """Diálogo para gestionar alias de sub-valores definidos en un estudio."""

    # Cambiar app_settings y file_service por study_service
    def __init__(self, parent, study_service: StudyService, study_id: int):
        super().__init__(parent)
        # self.app_settings = app_settings # Ya no se usa
        # self.file_service = file_service # Ya no se usa
        self.study_service = study_service # Usar StudyService
        self.study_id = study_id

        self.title(f"Gestionar Alias de Sub-valores (Estudio {study_id})")
        self.geometry("500x400")
        self.resizable(True, True)

        # Diccionario para almacenar las variables de entrada de alias
        self.alias_vars = {}
        # Almacenar sub-valores definidos en el estudio
        self.defined_descriptors = set()
        # Almacenar alias actuales del estudio
        self.current_aliases = {}

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
        ttk.Label(main_frame, text="Asigne un alias descriptivo a cada descriptor definido para este estudio.", wraplength=450).pack(pady=(0, 10))

        # Frame para la tabla de alias (usaremos grid aquí)
        self.alias_grid_frame = ttk.Frame(main_frame)
        self.alias_grid_frame.pack(fill=tk.BOTH, expand=True)
        self.alias_grid_frame.columnconfigure(1, weight=1) # Columna de alias expandible

        # Cabeceras
        ttk.Label(self.alias_grid_frame, text="Sub-valor Definido", font=('Helvetica', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.alias_grid_frame, text="Alias Asignado", font=('Helvetica', 10, 'bold')).grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Los sub-valores se añadirán dinámicamente en load_descriptors_and_aliases

        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        ttk.Button(button_frame, text="Guardar Alias", command=self.save_aliases).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

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
                    alias_entry = ttk.Entry(self.alias_grid_frame, textvariable=alias_var)
                    alias_entry.grid(row=row_idx, column=1, padx=5, pady=2, sticky='ew')

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
