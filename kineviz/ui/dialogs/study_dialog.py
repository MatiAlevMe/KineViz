import tkinter as tk # Usar tk en lugar de solo ttk para StringVar, etc.
from tkinter import ttk, Toplevel, messagebox, Canvas, Scrollbar, Frame # Importar explícitamente
from kineviz.ui.utils.validators import validate_study_data # Asumiendo que este validador es adecuado

class StudyDialog(Toplevel):
    # Añadir study_to_edit y on_save_callback
    def __init__(self, parent, study_service, study_to_edit=None, on_save_callback=None):
        super().__init__(parent)
        self.study_service = study_service
        self.file_service = FileService(study_service) # Necesitamos FileService para buscar archivos
        self.study_to_edit = study_to_edit
        self.on_save_callback = on_save_callback

        # Almacenar criterios originales si estamos editando
        self.original_test_types = []
        self.original_test_periods = []

        self.title("Editar Estudio" if study_to_edit else "Nuevo Estudio")
        self.geometry("600x450") # Ajustar tamaño si es necesario, 800 es muy alto
        self.resizable(False, False) # Evitar redimensionar por ahora

        # Variables para campos (usar tk.StringVar)
        self.var_nombre = tk.StringVar()
        self.var_num_sujetos = tk.StringVar()
        self.var_tipos_prueba = tk.StringVar()
        self.var_periodos_prueba = tk.StringVar()
        self.var_cantidad_intentos = tk.StringVar()

        # Si estamos editando, cargar datos existentes
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
            original_types_str = study_details.get('test_types', '') or ''
            original_periods_str = study_details.get('test_periods', '') or ''
            self.var_tipos_prueba.set(original_types_str)
            self.var_periodos_prueba.set(original_periods_str)
            self.var_cantidad_intentos.set(str(study_details.get('attempts_count', '')))

            # Guardar criterios originales limpios para comparación posterior
            self.original_test_types = [t.strip() for t in original_types_str.split(',') if t.strip()]
            self.original_test_periods = [p.strip() for p in original_periods_str.split(',') if p.strip()]

        except Exception as e:
            messagebox.showerror("Error al Cargar", f"No se pudieron cargar los datos del estudio:\n{e}", parent=self)
            self.destroy() # Cerrar diálogo si no se pueden cargar datos


    def create_form(self):
        # Usar un Frame normal, el scroll no parece necesario para esta cantidad de campos
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configurar grid layout para mejor alineación
        main_frame.columnconfigure(1, weight=1) # Columna de Entries expandible

        row_idx = 0

        # Campos del formulario con grid
        ttk.Label(main_frame, text="Nombre del estudio:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_nombre).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Número de Sujetos:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_num_sujetos).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Tipos de Prueba (separados por coma):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_tipos_prueba).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Periodos de Prueba (separados por coma):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_periodos_prueba).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        ttk.Label(main_frame, text="Cantidad de Intentos por Prueba:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(main_frame, textvariable=self.var_cantidad_intentos).grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5)
        row_idx += 1

        # Frame para botones (Guardar, Cancelar)
        button_frame = ttk.Frame(main_frame)
        # Alinear botones a la derecha
        button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="e", pady=20, padx=5)

        ttk.Button(button_frame, text="Guardar", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def _handle_criteria_change(self, study_id: int, new_types: list[str], new_periods: list[str]) -> bool:
        """
        Verifica si los archivos existentes cumplen con los nuevos criterios y pide confirmación para eliminar los inválidos.

        :param study_id: ID del estudio que se está editando.
        :param new_types: Nueva lista de tipos de prueba.
        :param new_periods: Nueva lista de periodos de prueba.
        :return: True si se puede proceder con el guardado, False si el usuario canceló la eliminación.
        """
        print("DEBUG: Verificando cambio de criterios...")
        try:
            # Obtener todos los archivos procesados del estudio
            # Usamos get_study_files que ya filtra por carpetas de frecuencia
            all_files_info = self.file_service.get_study_files(study_id)
            processed_files = [f for f in all_files_info if f.get('type') == 'Processed']

            if not processed_files:
                print("DEBUG: No hay archivos procesados, no se necesita validación de criterios.")
                return True # No hay archivos que validar

            invalid_files = []
            for file_info in processed_files:
                filename = file_info.get('name')
                file_path = file_info.get('path')
                if filename and file_path:
                    if not validate_filename_for_study_criteria(filename, new_types, new_periods):
                        # Guardar la ruta relativa para mostrar al usuario (más legible)
                        try:
                            # Intentar obtener ruta relativa desde la carpeta del estudio
                            study_details = self.study_service.get_study_details(study_id)
                            study_base_path = self.file_service.studies_base_dir / study_details['name']
                            relative_path = file_path.relative_to(study_base_path)
                            invalid_files.append((relative_path, file_path)) # Guardar relativa y absoluta
                        except Exception:
                             invalid_files.append((Path(filename), file_path)) # Fallback al nombre de archivo

            if invalid_files:
                print(f"DEBUG: Archivos inválidos encontrados: {[str(f[0]) for f in invalid_files]}")
                # Mostrar mensaje al usuario
                message = "Los siguientes archivos ya no cumplen con los nuevos criterios de Tipos/Periodos de Prueba:\n\n"
                message += "\n".join([f"- {str(f[0])}" for f in invalid_files[:10]]) # Mostrar hasta 10 archivos
                if len(invalid_files) > 10:
                    message += f"\n... y {len(invalid_files) - 10} más."
                message += "\n\n¿Desea eliminar permanentemente estos archivos inválidos para continuar?"

                if messagebox.askyesno("Confirmar Eliminación de Archivos", message, icon='warning', parent=self):
                    print("DEBUG: Usuario confirmó eliminación.")
                    deleted_count = 0
                    errors = []
                    for _, absolute_path in invalid_files:
                        try:
                            self.file_service.delete_file(absolute_path)
                            deleted_count += 1
                        except Exception as e:
                            errors.append(f"- {absolute_path.name}: {e}")
                            print(f"Error eliminando archivo {absolute_path}: {e}")

                    if errors:
                        messagebox.showerror("Error al Eliminar Archivos",
                                             f"Se eliminaron {deleted_count} archivos, pero ocurrieron errores al eliminar otros:\n" + "\n".join(errors),
                                             parent=self)
                        # Decidir si continuar o no. Por ahora, continuamos si al menos algunos se borraron.
                        # Podríamos retornar False aquí si queremos ser más estrictos.
                    else:
                         messagebox.showinfo("Archivos Eliminados", f"Se eliminaron {deleted_count} archivos inválidos.", parent=self)
                    return True # Proceder con el guardado
                else:
                    print("DEBUG: Usuario canceló eliminación.")
                    return False # Usuario canceló, no guardar
            else:
                print("DEBUG: Todos los archivos existentes cumplen los nuevos criterios.")
                return True # No hay archivos inválidos

        except Exception as e:
            messagebox.showerror("Error al Validar Archivos", f"Ocurrió un error al verificar los archivos existentes:\n{e}", parent=self)
            import traceback
            traceback.print_exc()
            return False # No proceder si hubo un error en la validación

    def save(self):
        # Preparar datos del estudio, limpiando tipos y periodos
        # Dividir por comas, quitar espacios y filtrar vacíos
        cleaned_types = [t.strip() for t in self.var_tipos_prueba.get().split(',') if t.strip()]
        cleaned_periods = [p.strip() for p in self.var_periodos_prueba.get().split(',') if p.strip()]

        study_data = {
            'name': self.var_nombre.get().strip(), # También quitar espacios del nombre
            'num_subjects': self.var_num_sujetos.get().strip(),
            'test_types': ','.join(cleaned_types), # Unir los valores limpios
            'test_periods': ','.join(cleaned_periods), # Unir los valores limpios
            'attempts_count': self.var_cantidad_intentos.get().strip()
        }

        # Validar datos básicos del formulario
        is_valid, error_message = validate_study_data(study_data)
        if not is_valid:
            messagebox.showerror("Datos Inválidos", error_message, parent=self)
            return

        # --- Lógica de manejo de cambio de criterios ---
        proceed_with_save = True
        if self.study_to_edit:
            # Comparar criterios nuevos (limpios) con los originales (ya limpios)
            new_cleaned_types_set = set(cleaned_types)
            new_cleaned_periods_set = set(cleaned_periods)
            original_types_set = set(self.original_test_types)
            original_periods_set = set(self.original_test_periods)

            if new_cleaned_types_set != original_types_set or new_cleaned_periods_set != original_periods_set:
                print("DEBUG: Criterios (tipos/periodos) han cambiado.")
                # Llamar a la función que maneja la validación/eliminación de archivos
                proceed_with_save = self._handle_criteria_change(
                    self.study_to_edit['id'],
                    cleaned_types, # Pasar listas limpias
                    cleaned_periods
                )
            else:
                print("DEBUG: Criterios (tipos/periodos) no han cambiado.")

        # --- Proceder con el guardado si todo está bien ---
        if not proceed_with_save:
            print("DEBUG: Guardado abortado debido a cancelación de eliminación de archivos.")
            return # No guardar si el usuario canceló la eliminación

        try:
            if self.study_to_edit:
                # Actualizar estudio existente
                self.study_service.update_study(self.study_to_edit['id'], study_data)
                messagebox.showinfo("Éxito", "Estudio actualizado correctamente", parent=self)
            else:
                # Crear nuevo estudio (no necesita validación de archivos existentes)
                self.study_service.create_study(study_data)
                messagebox.showinfo("Éxito", "Estudio creado correctamente", parent=self)

            # Llamar al callback si existe
            if self.on_save_callback:
                self.on_save_callback()

            self.destroy() # Cerrar el diálogo

        except ValueError as ve: # Capturar errores específicos si es posible
             messagebox.showerror("Error de Validación", str(ve), parent=self)
        except Exception as e: # Capturar errores generales del servicio o DB
            # Imprimir traceback para debugging
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error al Guardar", f"Ocurrió un error inesperado:\n{str(e)}", parent=self)
