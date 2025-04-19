import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, Canvas, Scrollbar, Frame
import webbrowser # Para abrir archivo de ayuda
from pathlib import Path # Para construir ruta de ayuda
# Importar NUEVO validador de datos y validador de nombres de archivo
from kineviz.ui.utils.validators import validate_study_iv_data, validate_filename_for_study_criteria
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
        self.is_editing = bool(study_to_edit) # Flag para modo edición

        # Estructura para almacenar VIs y sus descriptores en la UI
        # Lista de diccionarios: [{'name_var': StringVar, 'descriptor_vars': [StringVar], 'frame': Frame, 'desc_frames': [Frame]}]
        self.independent_variables_ui = []

        self.title("Editar Estudio" if self.is_editing else "Nuevo Estudio")
        # Aumentar altura para VIs/descriptores
        self.geometry("600x550")
        self.resizable(True, True) # Permitir redimensionar

        # Variables para campos fijos
        self.var_nombre = tk.StringVar()
        self.var_num_sujetos = tk.StringVar()
        self.var_cantidad_intentos = tk.StringVar()

        # Cargar datos si estamos editando (ahora carga VIs)
        if self.is_editing:
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

            # Cargar estructura de VIs y descriptores
            # get_study_details ya devuelve la estructura Python parseada
            self.initial_independent_variables = study_details.get('independent_variables', [])

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

        # --- Sección de Variables Independientes Dinámicas ---
        iv_frame = ttk.LabelFrame(main_frame, text="Variables Independientes (VIs)")
        iv_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=10)
        iv_frame.columnconfigure(0, weight=1) # Permitir que el contenido se expanda
        main_frame.rowconfigure(row_idx, weight=1) # Permitir que esta sección se expanda verticalmente
        self.iv_container = iv_frame # Guardar referencia
        row_idx += 1

        # --- Canvas y Scrollbar para VIs ---
        iv_canvas = Canvas(self.iv_container, borderwidth=0, highlightthickness=0)
        iv_scrollbar = ttk.Scrollbar(self.iv_container, orient="vertical", command=iv_canvas.yview)
        # Frame interior que contendrá las VIs
        self.iv_scrollable_frame = ttk.Frame(iv_canvas)

        self.iv_scrollable_frame.bind(
            "<Configure>",
            lambda e: iv_canvas.configure(scrollregion=iv_canvas.bbox("all"))
        )
        iv_canvas.create_window((0, 0), window=self.iv_scrollable_frame, anchor="nw")
        iv_canvas.configure(yscrollcommand=iv_scrollbar.set)

        iv_canvas.pack(side="left", fill="both", expand=True)
        iv_scrollbar.pack(side="right", fill="y")
        # --- Fin Canvas y Scrollbar ---

        # Botón para añadir VI (dentro del frame principal, debajo del contenedor scrollable)
        add_iv_button_frame = ttk.Frame(main_frame)
        add_iv_button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=15, pady=(5,0))
        self.add_iv_button = ttk.Button(add_iv_button_frame, text="+ Añadir Variable Independiente", command=self.add_independent_variable_ui)
        self.add_iv_button.pack()
        # Deshabilitar si estamos editando
        if self.is_editing:
            self.add_iv_button.config(state=tk.DISABLED)
        row_idx += 1

        # Cargar VIs iniciales (si estamos editando)
        initial_ivs_to_load = self.initial_independent_variables if self.is_editing else []
        if not initial_ivs_to_load and not self.is_editing:
             # Añadir una VI vacía por defecto al crear nuevo estudio
             self.add_independent_variable_ui()
        else:
             for iv_data in initial_ivs_to_load:
                 self.add_independent_variable_ui(
                     name_value=iv_data.get('name', ''),
                     descriptors_values=iv_data.get('descriptors', [])
                 )

        # --- Frame para botones (Guardar, Cancelar, Ayuda) ---
        button_frame = ttk.Frame(main_frame)
        # Usar row_idx actual, que está después del botón "+ Añadir VI"
        button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="se", pady=20, padx=5)
        # No configurar rowconfigure aquí, dejar que los botones estén al final

        # Botón de Ayuda (?)
        # Usar un estilo para el color o configurar directamente
        style = ttk.Style()
        style.configure("Help.TButton", foreground="white", background="blue") # Ejemplo de estilo
        help_button = ttk.Button(button_frame, text="?", width=3, style="Help.TButton", command=self.show_iv_help)
        help_button.pack(side=tk.LEFT, padx=(0, 10)) # A la izquierda de Cancelar

        ttk.Button(button_frame, text="Guardar", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)


    def add_independent_variable_ui(self, name_value="", descriptors_values=None):
        """Añade una nueva sección para una Variable Independiente."""
        if descriptors_values is None:
            descriptors_values = []

        # Frame principal para esta VI (dentro del scrollable_frame)
        vi_frame = ttk.Frame(self.iv_scrollable_frame, padding="5", relief="groove", borderwidth=1)
        vi_frame.pack(fill=tk.X, pady=5, padx=5)

        # --- Fila para Nombre VI y botones ---
        vi_header_frame = ttk.Frame(vi_frame)
        vi_header_frame.pack(fill=tk.X)

        vi_name_var = tk.StringVar(value=name_value)
        vi_name_entry = ttk.Entry(vi_header_frame, textvariable=vi_name_var, width=30)
        vi_name_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        # Permitir editar nombre VI en modo edición
        # vi_name_entry.config(state='readonly' if self.is_editing else 'normal')

        # Botón para añadir descriptor a ESTA VI
        add_desc_button = ttk.Button(vi_header_frame, text="+", width=3,
                                     command=lambda v=vi_name_var: self.add_descriptor_ui(v))
        add_desc_button.pack(side=tk.LEFT, padx=(0, 5))
        if self.is_editing:
            add_desc_button.config(state=tk.DISABLED)

        # Botón para eliminar ESTA VI
        remove_vi_button = ttk.Button(vi_header_frame, text="🗑️", width=3,
                                      command=lambda f=vi_frame, v=vi_name_var: self.remove_independent_variable_ui(f, v))
        remove_vi_button.pack(side=tk.LEFT, padx=(0, 5))
        if self.is_editing:
            remove_vi_button.config(state=tk.DISABLED)

        # --- Contenedor para descriptores de esta VI ---
        descriptors_container = ttk.Frame(vi_frame, padding="5 0 0 20") # Indentación izquierda
        descriptors_container.pack(fill=tk.X)

        # Guardar referencias
        vi_ui_data = {
            'name_var': vi_name_var,
            'descriptor_vars': [],
            'frame': vi_frame,
            'descriptors_container': descriptors_container,
            'desc_frames': []
        }
        self.independent_variables_ui.append(vi_ui_data)

        # Añadir descriptores iniciales para esta VI
        if not descriptors_values and not self.is_editing:
            # Añadir 2 descriptores vacíos por defecto al crear nueva VI
            self.add_descriptor_ui(vi_name_var)
            self.add_descriptor_ui(vi_name_var)
        else:
            for desc_value in descriptors_values:
                self.add_descriptor_ui(vi_name_var, value=desc_value)

    def remove_independent_variable_ui(self, frame_to_remove, vi_name_var_to_remove):
        """Elimina la sección de una Variable Independiente."""
        if self.is_editing: return # No permitir eliminar en modo edición

        found_index = -1
        for i, vi_data in enumerate(self.independent_variables_ui):
            if vi_data['name_var'] == vi_name_var_to_remove:
                found_index = i
                break

        if found_index != -1:
            self.independent_variables_ui.pop(found_index)
            frame_to_remove.destroy()
        else:
            logger.warning("Intento de eliminar una VI que no está en la lista UI.")

    def add_descriptor_ui(self, vi_name_var, value=""):
        """Añade una fila para un descriptor dentro de una VI específica."""
        if self.is_editing: return # No permitir añadir en modo edición

        # Encontrar la VI correspondiente en la UI
        target_vi_data = None
        for vi_data in self.independent_variables_ui:
            if vi_data['name_var'] == vi_name_var:
                target_vi_data = vi_data
                break

        if not target_vi_data:
            logger.error(f"No se encontró la VI UI para añadir descriptor (Nombre Var: {vi_name_var.get()})")
            return

        container = target_vi_data['descriptors_container']
        desc_frame = ttk.Frame(container)
        desc_frame.pack(fill=tk.X, pady=1)

        desc_var = tk.StringVar(value=value)
        desc_entry = ttk.Entry(desc_frame, textvariable=desc_var)
        desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        if self.is_editing:
            desc_entry.config(state='readonly')

        # Botón para eliminar este descriptor
        remove_desc_button = ttk.Button(desc_frame, text="🗑️", width=3,
                                        command=lambda f=desc_frame, v=desc_var, vi_v=vi_name_var: self.remove_descriptor_ui(f, v, vi_v))
        remove_desc_button.pack(side=tk.LEFT, padx=(0, 5))
        if self.is_editing:
            remove_desc_button.config(state=tk.DISABLED)

        target_vi_data['descriptor_vars'].append(desc_var)
        target_vi_data['desc_frames'].append(desc_frame)

    def remove_descriptor_ui(self, frame_to_remove, desc_var_to_remove, vi_name_var):
        """Elimina una fila de descriptor de una VI específica."""
        if self.is_editing: return # No permitir eliminar en modo edición

        # Encontrar la VI
        target_vi_data = None
        for vi_data in self.independent_variables_ui:
            if vi_data['name_var'] == vi_name_var:
                target_vi_data = vi_data
                break

        if not target_vi_data:
            logger.error(f"No se encontró la VI UI para eliminar descriptor (Nombre Var VI: {vi_name_var.get()})")
            return

        # Encontrar el descriptor dentro de la VI
        try:
            index = target_vi_data['descriptor_vars'].index(desc_var_to_remove)
            target_vi_data['descriptor_vars'].pop(index)
            target_vi_data['desc_frames'].pop(index)
            frame_to_remove.destroy()
        except ValueError:
            logger.warning("Intento de eliminar un descriptor que no está en la lista de la VI.")

    def show_iv_help(self):
        """Muestra el archivo de ayuda para VIs."""
        try:
            # Construir ruta relativa al archivo actual
            help_file_path = Path(__file__).parent.parent.parent / "docs" / "help" / "study_dialog_iv_help.txt"
            if help_file_path.exists():
                # Usar webbrowser para abrir el archivo (más portable)
                webbrowser.open(help_file_path.as_uri()) # as_uri() para formato file:///
            else:
                messagebox.showerror("Error", f"No se encontró el archivo de ayuda:\n{help_file_path}", parent=self)
        except Exception as e:
            logger.error(f"Error al abrir archivo de ayuda: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir el archivo de ayuda:\n{e}", parent=self)


    def save(self):
        # Recolectar datos de VIs y descriptores de la UI
        collected_ivs = []
        for vi_ui_data in self.independent_variables_ui:
            vi_name = vi_ui_data['name_var'].get().strip()
            descriptors = [desc_var.get().strip() for desc_var in vi_ui_data['descriptor_vars']]
            # Filtrar descriptores vacíos
            valid_descriptors = [d for d in descriptors if d]
            # Solo añadir VI si tiene nombre y descriptores válidos
            if vi_name and valid_descriptors:
                collected_ivs.append({'name': vi_name, 'descriptors': valid_descriptors})

        study_data = {
            'name': self.var_nombre.get().strip(),
            'num_subjects': self.var_num_sujetos.get().strip(),
            'attempts_count': self.var_cantidad_intentos.get().strip(),
            'independent_variables': collected_ivs, # Pasar estructura recolectada
            # Aliases se manejan por separado, no se envían desde aquí
        }

        # Validar datos usando el nuevo validador
        is_valid, error_message = validate_study_iv_data(study_data)
        if not is_valid:
            messagebox.showerror("Datos Inválidos", error_message, parent=self)
            return

        # --- Lógica de manejo de cambio de criterios (REVISAR EN TAREA 4) ---
        # La validación de archivos existentes al cambiar VIs/descriptores es compleja
        # y se abordará en un paso posterior. Por ahora, asumimos que se puede guardar.
        proceed_with_save = True
        if self.is_editing:
            # Aquí iría la lógica para comparar `collected_ivs` con `self.initial_independent_variables`
            # y llamar a una función similar a `_handle_criteria_change` si hay diferencias
            # estructurales (que no deberían ocurrir si los botones están deshabilitados).
            # Solo el cambio de nombre de VI es permitido y no requiere revalidar archivos.
            logger.debug("Modo edición: Omitiendo validación de archivos existentes por cambio de estructura (deshabilitado).")
            pass

        if not proceed_with_save:
             logger.warning(f"Guardado de estudio {self.study_to_edit.get('id', 'N/A')} abortado.")
             return

        # Preparar datos finales para el servicio (ya están en el formato correcto)
        final_study_data = study_data.copy()
        # Si estamos editando, necesitamos obtener los alias existentes para no perderlos
        if self.is_editing:
            try:
                existing_details = self.study_service.get_study_details(self.study_to_edit['id'])
                final_study_data['aliases'] = existing_details.get('aliases', {})
            except Exception as e:
                 logger.error(f"Error obteniendo alias existentes para estudio {self.study_to_edit['id']} al guardar: {e}")
                 messagebox.showerror("Error", "No se pudieron obtener los alias existentes. Cambios no guardados.", parent=self)
                 return
        else:
             # Para nuevos estudios, inicializar alias como vacío
             final_study_data['aliases'] = {}


        try:
            if self.is_editing:
                # Actualizar estudio existente
                self.study_service.update_study(
                    self.study_to_edit['id'], final_study_data
                )
                messagebox.showinfo(
                    "Éxito", "Estudio actualizado correctamente", parent=self
                )
            else:
                # Crear nuevo estudio
                self.study_service.create_study(final_study_data)
                messagebox.showinfo(
                    "Éxito", "Estudio creado correctamente", parent=self
                )

            # Llamar al callback si existe
            if self.on_save_callback:
                self.on_save_callback()

            self.destroy()  # Cerrar el diálogo
        except ValueError as ve:  # Capturar errores específicos de validación (ej. nombre duplicado)
            logger.warning(f"Error de validación al guardar estudio: {ve}")
            messagebox.showerror("Error de Validación", str(ve), parent=self)
        except Exception as e:  # Capturar errores generales
            study_id_log = self.study_to_edit['id'] if self.is_editing else "nuevo"
            logger.error(
                f"Error inesperado al guardar estudio {study_id_log}: {e}", exc_info=True
            )
            messagebox.showerror(
                "Error al Guardar", f"Ocurrió un error inesperado:\n{str(e)}", parent=self
            )
