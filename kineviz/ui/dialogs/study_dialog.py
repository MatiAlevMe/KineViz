import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, Canvas, Scrollbar, Frame
# Importar validador de datos y nuevo validador de nombres de archivo
from kineviz.ui.utils.validators import validate_study_data, validate_filename_for_study_criteria
import logging # Importar logging
# Importar FileService para obtener archivos y Path para manejar rutas
# Nota: FileService se importa aquí para consistencia, aunque también se usa en __init__
from kineviz.core.services.file_service import FileService
from pathlib import Path

logger = logging.getLogger(__name__) # Logger para este módulo

class StudyDialog(Toplevel):
    # Añadir study_to_edit y on_save_callback
    def __init__(self, parent, study_service, study_to_edit=None, on_save_callback=None):
        super().__init__(parent)
        self.study_service = study_service
        self.file_service = FileService(study_service) # Necesitamos FileService para buscar archivos
        self.study_to_edit = study_to_edit
        self.on_save_callback = on_save_callback

        # Lista para almacenar las entradas de descriptores (StringVar)
        self.descriptor_vars = []
        # Lista para almacenar los frames de cada fila de descriptor
        self.descriptor_frames = []

        self.title("Editar Estudio" if study_to_edit else "Nuevo Estudio")
        # Aumentar altura para descriptores
        self.geometry("600x550")
        self.resizable(True, True) # Permitir redimensionar

        # Variables para campos fijos
        self.var_nombre = tk.StringVar()
        self.var_num_sujetos = tk.StringVar()
        self.var_cantidad_intentos = tk.StringVar()

        # Si estamos editando, cargar datos existentes (incluyendo descriptores)
        if self.study_to_edit:
            self._load_study_data()

        self.create_form()

        # Centrar diálogo en la ventana padre
        self.transient(parent)
        self.grab_set()
        # Calcular posición para centrar (opcional pero mejora UX)
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = 600
        dialog_height = 450
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')


    def _load_study_data(self):
        """Carga los datos del estudio existente en las variables del formulario."""
        try:
            # Obtener detalles del estudio usando el servicio
            study_details = self.study_service.get_study_details(self.study_to_edit['id']) # Asumiendo que study_to_edit tiene 'id'
            self.var_nombre.set(study_details.get('name', ''))
            self.var_num_sujetos.set(str(study_details.get('num_subjects', '')))
            self.var_cantidad_intentos.set(str(study_details.get('attempts_count', '')))

            # Cargar descriptores
            descriptors_str = study_details.get('descriptores', '') or ''
            self.initial_descriptors = [d.strip() for d in descriptors_str.split(',') if d.strip()]

        except Exception as e:
            logger.error(f"No se pudieron cargar los datos del estudio {self.study_to_edit.get('id', 'N/A')} para edición: {e}", exc_info=True)
            messagebox.showerror("Error al Cargar", f"No se pudieron cargar los datos del estudio:\n{e}", parent=self)
            self.destroy() # Cerrar diálogo si no se pueden cargar datos


    def create_form(self):
        # Usar un Frame normal, el scroll no parece necesario para esta cantidad de campos
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configurar grid layout para mejor alineación
        main_frame.columnconfigure(1, weight=1) # Columna de Entries expandible

        row_idx = 0

        # --- Campos Fijos ---
        ttk.Label(main_frame, text="Nombre del estudio:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_nombre).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Número de Sujetos:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_num_sujetos).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Cantidad de Intentos por Prueba:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_cantidad_intentos).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        # --- Sección de Descriptores Dinámicos ---
        descriptors_label_frame = ttk.LabelFrame(main_frame, text="Descriptores")
        descriptors_label_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        descriptors_label_frame.columnconfigure(1, weight=1) # Permitir que Entry se expanda
        self.descriptors_container = descriptors_label_frame # Guardar referencia
        row_idx += 1

        # Botón inicial para añadir el primer descriptor (o más)
        add_button_frame = ttk.Frame(main_frame)
        add_button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=15)
        ttk.Button(add_button_frame, text="+ Añadir Descriptor", command=self.add_descriptor_entry).pack()
        row_idx += 1

        # Cargar descriptores iniciales (si estamos editando o si queremos uno por defecto)
        initial_descriptors_to_load = self.initial_descriptors if self.study_to_edit else []
        if not initial_descriptors_to_load:
             # Opcional: añadir un campo vacío por defecto al crear nuevo
             # self.add_descriptor_entry()
             pass
        else:
             for desc_value in initial_descriptors_to_load:
                 self.add_descriptor_entry(value=desc_value)


        # --- Frame para botones (Guardar, Cancelar) ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="se", pady=20, padx=5)
        main_frame.rowconfigure(row_idx, weight=1) # Empujar botones hacia abajo

        ttk.Button(button_frame, text="Guardar", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def add_descriptor_entry(self, value=""):
        """Añade una nueva fila para un descriptor."""
        frame = ttk.Frame(self.descriptors_container)
        frame.pack(fill=tk.X, pady=2) # Usar pack dentro del LabelFrame

        descriptor_var = tk.StringVar(value=value)
        label_text = f"Descriptor {len(self.descriptor_vars) + 1}:"
        ttk.Label(frame, text=label_text).pack(side=tk.LEFT, padx=5)
        entry = ttk.Entry(frame, textvariable=descriptor_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Botón para eliminar esta fila específica
        remove_button = ttk.Button(frame, text="🗑️", width=3,
                                   command=lambda f=frame, v=descriptor_var: self.remove_descriptor_entry(f, v))
        remove_button.pack(side=tk.LEFT, padx=5)

        self.descriptor_vars.append(descriptor_var)
        self.descriptor_frames.append(frame)

    def remove_descriptor_entry(self, frame_to_remove, var_to_remove):
        """Elimina una fila de descriptor."""
        try:
            index = self.descriptor_vars.index(var_to_remove)
            self.descriptor_vars.pop(index)
            frame = self.descriptor_frames.pop(index)
            frame.destroy()

            # Re-numerar las etiquetas restantes
            for i, frm in enumerate(self.descriptor_frames):
                # Asumiendo que el Label es el primer widget hijo del frame
                label_widget = frm.winfo_children()[0]
                if isinstance(label_widget, ttk.Label):
                    label_widget.config(text=f"Descriptor {i + 1}:")

        except ValueError:
            logger.warning("Intento de eliminar un descriptor que ya no existe en la lista.")

    def _handle_criteria_change(self, study_id: int, new_types: list[str], new_periods: list[str]) -> bool:
        """
        Verifica si los archivos existentes cumplen con los nuevos criterios y pide confirmación para eliminar los inválidos.

        :param study_id: ID del estudio que se está editando.
        :param new_types: Nueva lista de tipos de prueba.
        :param new_descriptors: Nueva lista de descriptores.
        :return: True si se puede proceder con el guardado, False si el usuario canceló la eliminación.
        """
        # --- ESTA LÓGICA NECESITA REVISIÓN COMPLETA EN TAREA 4 ---
        # Por ahora, la comentamos o devolvemos True para permitir guardar cambios
        # sin validar/eliminar archivos basados en los nuevos descriptores.
        logger.warning(f"Validación de cambio de criterios para descriptores aún no implementada. Omitiendo validación de archivos existentes.")
        return True
        # El código comentado desde aquí hasta el final de la función original _handle_criteria_change se elimina.

    def save(self):
        # Recolectar descriptores de las entradas
        current_descriptors = [var.get().strip() for var in self.descriptor_vars]

        study_data = {
            'name': self.var_nombre.get().strip(),
        'num_subjects': self.var_num_sujetos.get().strip(),
        'descriptores': current_descriptors, # Pasar la lista para validación
        'attempts_count': self.var_cantidad_intentos.get().strip()
    }

    # Validar datos básicos del formulario (incluyendo descriptores)
    is_valid, error_message = validate_study_data(study_data)
    if not is_valid:
        messagebox.showerror("Datos Inválidos", error_message, parent=self)
        return

    # --- Lógica de manejo de cambio de criterios (DESHABILITADA TEMPORALMENTE) ---
    proceed_with_save = True
    if self.study_to_edit:
        # Comparar descriptores nuevos con los originales
        # new_descriptors_set = set(d for d in current_descriptors if d) # Ignorar vacíos para comparación
        # original_descriptors_set = set(self.initial_descriptors)
        # if new_descriptors_set != original_descriptors_set:
        #     logger.info("Descriptores han cambiado.")
        #     # Llamar a la función que maneja la validación/eliminación de archivos (Tarea 4)
        #     proceed_with_save = self._handle_criteria_change(
        #         self.study_to_edit['id'],
        #         list(new_descriptors_set) # Pasar lista limpia
        #     )
        # else:
        #     logger.debug(f"Descriptores no han cambiado para estudio {self.study_to_edit['id']}.")
        pass # Omitir validación de archivos por ahora

    # --- Proceder con el guardado si todo está bien ---
    if not proceed_with_save:
        logger.warning(f"Guardado de estudio {self.study_to_edit.get('id', 'N/A')} abortado debido a cancelación de eliminación de archivos.")
        return # No guardar si el usuario canceló la eliminación

    # Preparar datos finales para el servicio (unir descriptores)
    final_study_data = study_data.copy()
    # Filtrar descriptores vacíos antes de unir
    valid_descriptors = [d for d in current_descriptors if d]
    final_study_data['descriptores'] = ','.join(valid_descriptors)

    try:
        if self.study_to_edit:
            # Actualizar estudio existente
            self.study_service.update_study(self.study_to_edit['id'], final_study_data)
            messagebox.showinfo("Éxito", "Estudio actualizado correctamente", parent=self)
        else:
            # Crear nuevo estudio
            self.study_service.create_study(final_study_data)
            messagebox.showinfo("Éxito", "Estudio creado correctamente", parent=self)

        # Llamar al callback si existe
            if self.on_save_callback:
                self.on_save_callback()

            self.destroy() # Cerrar el diálogo

        except ValueError as ve: # Capturar errores específicos de validación (ej. nombre duplicado si se implementa)
            logger.warning(f"Error de validación al guardar estudio: {ve}")
            messagebox.showerror("Error de Validación", str(ve), parent=self)
        except Exception as e: # Capturar errores generales del servicio o DB
            study_id_log = self.study_to_edit['id'] if self.study_to_edit else "nuevo"
            logger.error(f"Error inesperado al guardar estudio {study_id_log}: {e}", exc_info=True)
            # import traceback # Ya no es necesario
            # traceback.print_exc() # Reemplazado por logger
            messagebox.showerror("Error al Guardar", f"Ocurrió un error inesperado:\n{str(e)}", parent=self)
