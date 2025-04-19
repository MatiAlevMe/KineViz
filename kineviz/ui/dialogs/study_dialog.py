import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, Canvas, Scrollbar, Frame
# Importar validador de datos y nuevo validador de nombres de archivo
from tkinter import simpledialog # Para pedir número de VIs/Descriptores
from kineviz.ui.utils.validators import validate_study_data # Se adaptará
# validate_filename_for_study_criteria no se usa directamente aquí
import logging
# FileService no se necesita directamente aquí ahora
# from kineviz.core.services.file_service import FileService
from pathlib import Path
import json # Para cargar/guardar estructura VI
from kineviz.ui.widgets.tooltip import ToolTip # Para info "Nulo"

logger = logging.getLogger(__name__) # Logger para este módulo

class StudyDialog(Toplevel):
    # Añadir study_to_edit y on_save_callback
    def __init__(self, parent, study_service, study_to_edit=None, on_save_callback=None):
        super().__init__(parent)
        self.study_service = study_service
        self.file_service = FileService(study_service) # Necesitamos FileService para buscar archivos
        self.study_to_edit = study_to_edit
        self.on_save_callback = on_save_callback

        # Estructura para almacenar VIs y Descriptores (widgets y datos)
        # self.vi_structure = [
        #     {'name_var': StringVar, 'desc_vars': [StringVar], 'frame': Frame, 'desc_container': Frame}, ...
        # ]
        self.vi_widgets = []
        self.initial_vi_structure = [] # Para cargar al editar

        self.title("Editar Estudio" if study_to_edit else "Nuevo Estudio")
        self.geometry("700x600") # Ajustar tamaño
        self.resizable(True, True)

        # Variables para campos fijos
        self.var_nombre = tk.StringVar()
        self.var_num_sujetos = tk.StringVar()
        self.var_cantidad_intentos = tk.StringVar()
        self.var_num_vis = tk.IntVar(value=0) # Para número de VIs

        # Si estamos editando, cargar datos existentes (incluyendo estructura VI)
        if self.study_to_edit:
            self._load_study_data() # Carga self.initial_vi_structure

        self.create_form() # Crea la UI basada en los datos cargados o iniciales

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

            # Cargar estructura VI desde JSON parseado por el servicio
            self.initial_vi_structure = study_details.get('independent_variables_struct', [])
            self.var_num_vis.set(len(self.initial_vi_structure))

        except Exception as e:
            logger.error(f"No se pudieron cargar los datos del estudio {self.study_to_edit.get('id', 'N/A')} para edición: {e}", exc_info=True)
            messagebox.showerror("Error al Cargar", f"No se pudieron cargar los datos del estudio:\n{e}", parent=self)
            self.destroy() # Cerrar diálogo si no se pueden cargar datos


    def create_form(self):
        # Usar un Frame normal, el scroll no parece necesario para esta cantidad de campos
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configurar grid layout para mejor alineación
        # Frame principal con scrollbar vertical
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="20")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Contenido dentro del scrollable_frame ---
        scrollable_frame.columnconfigure(1, weight=1) # Columna de Entries expandible
        row_idx = 0

        # --- Campos Fijos ---
        ttk.Label(scrollable_frame, text="Nombre del estudio:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(scrollable_frame, textvariable=self.var_nombre).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(scrollable_frame, text="Número de Sujetos:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(scrollable_frame, textvariable=self.var_num_sujetos).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(scrollable_frame, text="Cantidad de Intentos por Prueba:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(scrollable_frame, textvariable=self.var_cantidad_intentos).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        # --- Sección de Variables Independientes (VIs) ---
        vi_header_frame = ttk.Frame(scrollable_frame)
        vi_header_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=5, pady=(10, 0))
        row_idx += 1

        ttk.Label(vi_header_frame, text="Variables Independientes (VIs):").pack(side=tk.LEFT, anchor='w')
        # Botón Info "Nulo"
        info_icon = ttk.Label(vi_header_frame, text="ℹ️", cursor="question_arrow")
        info_icon.pack(side=tk.LEFT, padx=5)
        ToolTip(info_icon, "Los nombres de archivo deben incluir un valor para cada VI definida.\n"
                         "Si un archivo no aplica a una VI específica, use la palabra 'Nulo' (exactamente así) en esa posición.\n"
                         "Ej: Pte01 CMJ Nulo 01\n"
                         "Al menos una VI debe tener un valor distinto de 'Nulo'.")

        # Frame contenedor para las VIs
        self.vi_container_frame = ttk.Frame(scrollable_frame)
        self.vi_container_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        scrollable_frame.rowconfigure(row_idx, weight=1) # Permitir que esta área se expanda verticalmente
        row_idx += 1

        # Botón para definir/cambiar número de VIs (solo al crear)
        self.define_vis_button = ttk.Button(scrollable_frame, text="Definir Número de VIs", command=self.define_number_of_vis)
        self.define_vis_button.grid(row=row_idx, column=0, columnspan=2, pady=5)
        if self.study_to_edit:
            self.define_vis_button.config(state=tk.DISABLED)
        row_idx += 1

        # Cargar VIs iniciales (si estamos editando o si ya se definieron)
        self._populate_vi_entries()

        # --- Frame para botones (Guardar, Cancelar) ---
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="e", pady=20, padx=5)
        # No configurar rowconfigure aquí para que los botones queden abajo

        ttk.Button(button_frame, text="Guardar", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def define_number_of_vis(self):
        """Pide al usuario el número de VIs y actualiza la UI."""
        if self.study_to_edit: return # No permitir cambiar al editar

        num = simpledialog.askinteger("Número de Variables",
                                      "¿Cuántas variables independientes tendrá el estudio?",
                                      parent=self, minvalue=1, initialvalue=self.var_num_vis.get() or 1)
        if num is not None and num > 0:
            if num != self.var_num_vis.get():
                self.var_num_vis.set(num)
                # Limpiar estructura existente y repoblar
                self.initial_vi_structure = [{'name': '', 'descriptors': []} for _ in range(num)]
                self._clear_vi_entries()
                self._populate_vi_entries()

    def _clear_vi_entries(self):
        """Elimina todos los widgets de VIs existentes."""
        for widget_info in self.vi_widgets:
            widget_info['frame'].destroy()
        self.vi_widgets = []

    def _populate_vi_entries(self):
        """Crea los widgets para las VIs basadas en initial_vi_structure."""
        self._clear_vi_entries() # Limpiar primero
        for i, vi_data in enumerate(self.initial_vi_structure):
            self._add_vi_section(index=i, initial_data=vi_data)

    def _add_vi_section(self, index: int, initial_data: dict = None):
        """Añade una sección completa para una VI."""
        if initial_data is None:
            initial_data = {'name': '', 'descriptors': []}

        vi_frame = ttk.LabelFrame(self.vi_container_frame, text=f"Variable Independiente {index + 1}")
        vi_frame.pack(fill=tk.X, expand=True, pady=5, padx=5)
        vi_frame.columnconfigure(1, weight=1)

        # Nombre de la VI
        ttk.Label(vi_frame, text="Nombre VI:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        name_var = tk.StringVar(value=initial_data.get('name', ''))
        name_entry = ttk.Entry(vi_frame, textvariable=name_var)
        name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        # Nombre es editable siempre

        # Contenedor para descriptores de esta VI
        desc_container = ttk.Frame(vi_frame)
        desc_container.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0))
        desc_container.columnconfigure(1, weight=1)

        # Botón para definir número de descriptores (solo al crear)
        num_desc_button = ttk.Button(
            vi_frame, text="Definir Descriptores",
            command=lambda idx=index: self._define_num_descriptors(idx)
        )
        num_desc_button.grid(row=2, column=0, columnspan=2, pady=5)
        if self.study_to_edit:
            num_desc_button.config(state=tk.DISABLED)

        # Guardar widgets y variables
        widget_info = {
            'frame': vi_frame,
            'name_var': name_var,
            'desc_vars': [],
            'desc_container': desc_container,
            'num_desc_button': num_desc_button
        }
        self.vi_widgets.append(widget_info)

        # Añadir entradas para descriptores existentes (solo al cargar/editar)
        for desc_value in initial_data.get('descriptors', []):
            self._add_descriptor_entry_to_vi(index, value=desc_value)

    def _define_num_descriptors(self, vi_index: int):
        """Pide el número de descriptores para una VI y actualiza su sección."""
        if self.study_to_edit: return

        widget_info = self.vi_widgets[vi_index]
        current_num = len(widget_info['desc_vars'])

        num = simpledialog.askinteger(f"Número de Descriptores (VI {vi_index + 1})",
                                      f"¿Cuántos descriptores tendrá la variable '{widget_info['name_var'].get() or f'VI {vi_index + 1}'}'?",
                                      parent=self, minvalue=1, initialvalue=current_num or 1)

        if num is not None and num > 0:
            # Limpiar descriptores existentes para esta VI
            for child in widget_info['desc_container'].winfo_children():
                child.destroy()
            widget_info['desc_vars'] = []

            # Añadir nuevas entradas
            for _ in range(num):
                self._add_descriptor_entry_to_vi(vi_index)

    def _add_descriptor_entry_to_vi(self, vi_index: int, value=""):
        """Añade una entrada de descriptor a una VI específica."""
        widget_info = self.vi_widgets[vi_index]
        desc_container = widget_info['desc_container']
        desc_index = len(widget_info['desc_vars'])

        frame = ttk.Frame(desc_container)
        frame.pack(fill=tk.X, pady=1)

        desc_var = tk.StringVar(value=value)
        label_text = f"  Descriptor {desc_index + 1}:" # Indentar un poco
        ttk.Label(frame, text=label_text).pack(side=tk.LEFT, padx=5)
        entry = ttk.Entry(frame, textvariable=desc_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Descriptores no son editables ni eliminables al editar estudio
        if self.study_to_edit:
            entry.config(state='readonly')
        # No añadir botón de eliminar por ahora, se gestiona por número

        widget_info['desc_vars'].append(desc_var)

    # Eliminar _handle_criteria_change ya que la lógica de validación de archivos
    # se hará en el nuevo validador basado en la estructura VI guardada.

    def save(self):
        # Recolectar datos de la estructura VI
        vi_structure_to_save = []
        validation_errors = []
        num_vis = self.var_num_vis.get()

        if num_vis <= 0 and not self.study_to_edit: # Solo requerir VIs al crear
             validation_errors.append("Defina al menos una Variable Independiente.")
        elif num_vis != len(self.vi_widgets):
             # Esto indica un error interno si la UI no se actualizó
             validation_errors.append("Error interno: Inconsistencia en número de VIs.")
        else:
            for i, widget_info in enumerate(self.vi_widgets):
                vi_name = widget_info['name_var'].get().strip()
                if not vi_name:
                    validation_errors.append(f"El nombre de la Variable Independiente {i+1} es obligatorio.")

                descriptors = [var.get().strip() for var in widget_info['desc_vars']]
                cleaned_descriptors = [d for d in descriptors if d] # Ignorar vacíos

                if not cleaned_descriptors:
                     validation_errors.append(f"La Variable Independiente '{vi_name or f'VI {i+1}'}' debe tener al menos un descriptor definido.")
                elif len(cleaned_descriptors) != len(set(cleaned_descriptors)):
                     # Encontrar duplicados
                     counts = {}
                     duplicates = set()
                     for d in cleaned_descriptors:
                         counts[d] = counts.get(d, 0) + 1
                         if counts[d] > 1: duplicates.add(d)
                     validation_errors.append(f"Descriptores duplicados en VI '{vi_name or f'VI {i+1}'}': {', '.join(duplicates)}")
                # Validar que no se use "Nulo" como descriptor
                elif "Nulo" in cleaned_descriptors:
                     validation_errors.append(f"El nombre 'Nulo' está reservado y no puede usarse como descriptor (en VI '{vi_name or f'VI {i+1}'}').")


                vi_structure_to_save.append({
                    'name': vi_name,
                    'descriptors': cleaned_descriptors # Guardar solo los no vacíos
                })

        # Recolectar datos fijos
        study_data_fixed = {
            'name': self.var_nombre.get().strip(),
            'num_subjects': self.var_num_sujetos.get().strip(),
            'attempts_count': self.var_cantidad_intentos.get().strip()
        }

        # Validar datos fijos (usando una parte adaptada de validate_study_data)
        is_fixed_valid, fixed_error = self._validate_fixed_study_data(study_data_fixed)
        if not is_fixed_valid:
            validation_errors.append(fixed_error)

        # Mostrar todos los errores de validación juntos
        if validation_errors:
            messagebox.showerror("Datos Inválidos", "\n".join(validation_errors), parent=self)
            return

        # --- Proceder con el guardado ---
        final_study_data = study_data_fixed.copy()
        # Añadir la estructura VI para que el servicio la convierta a JSON
        final_study_data['independent_variables_struct'] = vi_structure_to_save

        try:
            if self.study_to_edit:
                self.study_service.update_study(self.study_to_edit['id'], final_study_data)
                messagebox.showinfo("Éxito", "Estudio actualizado correctamente", parent=self)
            else:
                # Crear nuevo estudio
                self.study_service.create_study(final_study_data)
                messagebox.showinfo("Éxito", "Estudio creado correctamente", parent=self)

            # Llamar al callback si existe
            if self.on_save_callback:
                self.on_save_callback()

            self.destroy()  # Cerrar el diálogo
        except ValueError as ve:  # Capturar errores específicos de validación
            logger.warning(f"Error de validación al guardar estudio: {ve}")
            messagebox.showerror("Error de Validación", str(ve), parent=self)
        except Exception as e:  # Capturar errores generales
            study_id_log = (
                self.study_to_edit['id' if self.study_to_edit else "nuevo"]
            )
            logger.error(
                f"Error inesperado al guardar estudio {study_id_log}: {e}", exc_info=True)
            messagebox.showerror("Error al Guardar", f"Ocurrió un error inesperado:\n{str(e)}", parent=self)

    def _validate_fixed_study_data(self, data):
        """Valida solo los campos fijos del estudio (nombre, sujetos, intentos)."""
        name = data.get('name', '').strip()
        if not name: return False, "El nombre del estudio es obligatorio."
        if len(name) < 3: return False, "El nombre del estudio debe tener al menos 3 caracteres."

        num_subjects_str = data.get('num_subjects', '')
        if not num_subjects_str: return False, "El número de sujetos es obligatorio."
        try:
            if int(num_subjects_str) <= 0: return False, "El número de sujetos debe ser un entero positivo."
        except ValueError: return False, "El número de sujetos debe ser un número entero."

        attempts_count_str = data.get('attempts_count', '')
        if not attempts_count_str: return False, "La cantidad de intentos es obligatoria."
        try:
            if int(attempts_count_str) <= 0: return False, "La cantidad de intentos debe ser un entero positivo."
        except ValueError: return False, "La cantidad de intentos debe ser un número entero."

        return True, None
