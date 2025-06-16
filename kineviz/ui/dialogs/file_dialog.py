import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, filedialog, Listbox, Scrollbar
from pathlib import Path
import os # Para os.path.basename
import logging # Importar logging
from typing import Tuple # Importar Tuple para type hints

# Importar FileService para type hinting y validación
from kineviz.core.services.file_service import FileService
from kineviz.ui.utils.validators import validate_filename_for_study_criteria
from kineviz.config.settings import AppSettings # Import AppSettings
from kineviz.ui.utils.style import get_font_object, DEFAULT_FONT_SIZE # Import font utilities
from kineviz.ui.widgets.tooltip import Tooltip # Import Tooltip

logger = logging.getLogger(__name__) # Logger para este módulo

class FileDialog(Toplevel):
    """Diálogo para seleccionar y agregar archivos a un estudio."""

    def __init__(self, parent, file_service: FileService, study_id: int, settings: AppSettings, on_close_callback=None):
        super().__init__(parent)
        self.file_service = file_service
        self.study_id = study_id
        self.settings = settings # Store AppSettings instance
        self.on_close_callback = on_close_callback
        self.selected_files = [] # Lista de rutas (Path objects)
        # Mapeo de display_name en listbox a Path object
        self.listbox_item_to_path = {}

        # Obtener estructura de VIs del estudio para validación previa
        self.study_details = None
        self.independent_variables = [] # Estructura de VIs
        try:
            self.study_details = self.file_service.study_service.get_study_details(self.study_id)
            # Obtener la estructura de VIs (ya es una lista de dicts)
            self.independent_variables = self.study_details.get('independent_variables', [])
            logger.debug(f"Estructura VIs cargada en FileDialog para estudio {self.study_id}: {self.independent_variables}")
        except Exception as e:
            logger.error(f"No se pudieron cargar los detalles/VIs del estudio {self.study_id} en FileDialog: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los detalles del estudio: {e}", parent=parent)
            self.destroy()
            return

        self.title(f"Agregar Archivos a Estudio: {self.study_details.get('name', study_id)}")
        self.geometry("600x450")
        self.resizable(True, True)

        self.create_widgets()

        # Centrar diálogo
        self.transient(parent)
        self.grab_set()
        
        # Centering logic (can be simplified or made a helper)
        self.update_idletasks() # Ensure dialog size is calculated
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f'+{x}+{y}')

        # Definir estilo para el botón de ayuda (si no está globalmente definido)
        # style = ttk.Style()
        # style.configure("Help.TButton", foreground="white", background="blue")


    def _show_input_help(self, title: str, message: str):
        """Muestra un popup de ayuda simple."""
        messagebox.showinfo(title, message, parent=self)

    def create_widgets(self):
        # --- Top Fixed Frame for Selection Button and Help ---
        top_fixed_frame = ttk.Frame(self, padding=(10, 10, 10, 0)) # Pad bottom 0
        top_fixed_frame.pack(side=tk.TOP, fill=tk.X)

        # Botón para seleccionar archivos
        select_button = ttk.Button(top_fixed_frame, text="Seleccionar Archivos (.txt, .csv)", command=self.select_files)
        select_button.pack(side=tk.LEFT, padx=(0, 5))

        # Botón de ayuda para formato de nombre de archivo
        filename_help_button = ttk.Button(top_fixed_frame, text="?", width=3, style="Help.TButton",
                                           command=lambda: self._show_input_help("Ayuda: Formato Nombre de Archivo",
                                                                                 self._get_naming_rules_help_text())) # Use helper for long text
        filename_help_button.pack(side=tk.LEFT)
        filename_help_long_text = self._get_naming_rules_help_text()
        filename_help_short_text = "Reglas para nombrar archivos de datos."
        Tooltip(filename_help_button, text=filename_help_long_text, short_text=filename_help_short_text, enabled=self.settings.enable_hover_tooltips)

        # --- Bottom Fixed Frame for Action Buttons (Packed before middle frame) ---
        bottom_fixed_frame = ttk.Frame(self, padding=(10, 5, 10, 10)) # Pad top 5
        bottom_fixed_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Row 1 for "Quitar Archivo(s) Seleccionado(s)"
        remove_button_frame = ttk.Frame(bottom_fixed_frame)
        remove_button_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5)) # Add some padding below this row

        remove_button = ttk.Button(remove_button_frame, text="Quitar Archivo(s) Seleccionado(s)", command=self.remove_selected)
        remove_button.pack(side=tk.RIGHT) # Align to the left

        # Row 2 for "Procesar Archivo(s) Seleccionado(s)" and "Cancelar"
        process_cancel_frame = ttk.Frame(bottom_fixed_frame)
        process_cancel_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Pack Cancelar primero para que quede a la derecha de Procesar
        ttk.Button(process_cancel_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)
        self.process_button = ttk.Button(process_cancel_frame, text="Procesar Archivo(s) Seleccionado(s)", command=self.process_files, state=tk.DISABLED)
        self.process_button.pack(side=tk.RIGHT, padx=5)

        # --- Middle Frame for Listbox and Scrollbars (Packed last to fill remaining space) ---
        middle_list_frame = ttk.Frame(self)
        middle_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5) # This will now fill space between top and bottom
        middle_list_frame.grid_rowconfigure(0, weight=1)
        middle_list_frame.grid_columnconfigure(0, weight=1)

        # Calculate scaled font for tk.Listbox
        scaled_font_tuple = get_font_object(DEFAULT_FONT_SIZE, self.settings.font_scale)

        v_scrollbar = ttk.Scrollbar(middle_list_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(middle_list_frame, orient=tk.HORIZONTAL)
        
        self.listbox = Listbox(middle_list_frame, 
                               yscrollcommand=v_scrollbar.set, 
                               xscrollcommand=h_scrollbar.set, 
                               selectmode=tk.EXTENDED, 
                               font=scaled_font_tuple,
                               height=10, # Default height in lines
                               width=70)  # Default width in characters
        
        v_scrollbar.config(command=self.listbox.yview)
        h_scrollbar.config(command=self.listbox.xview)

        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew") # Span across listbox width
        self.listbox.grid(row=0, column=0, sticky="nsew")
        
        # Set minsize after widgets are created
        self.update_idletasks()
        self.minsize(500, 350) # Adjust minsize as needed

    def _get_naming_rules_help_text(self) -> str:
        """Helper to generate the detailed help text for naming rules."""
        return (
            "Los nombres de archivo deben seguir el formato:\n"
            "[ID_Participante] [SubValor_VI1] [SubValor_VI2] ... [Intento].ext\n\n"
            "Ejemplo: P01 CMJ PRE 01.txt\n\n"
            "- ID_Participante: Identificador único del participante (letras seguidas de números, ej: P01, Sujeto007).\n"
            "- SubValores VIs: Deben coincidir con los sub-valores definidos para cada VI en el estudio, en el orden correcto. Usar 'Nulo' si una VI opcional no aplica.\n"
            "- Intento: Número de intento para esa combinación de VIs (ej: 01, 02, 03).\n"
            "- Extensión: .txt o .csv"
        )

    def select_files(self):
        """Abre el diálogo del sistema para seleccionar archivos."""
        filetypes = [("Archivos de texto", "*.txt"), ("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        # Usar askopenfilenames para selección múltiple
        filenames = filedialog.askopenfilenames(title="Seleccionar Archivos", filetypes=filetypes, parent=self)

        if filenames:
            new_files_added = False
            # Usar self.listbox_item_to_path para verificar duplicados
            current_display_names_in_list = set(self.listbox_item_to_path.keys())

            for filename in filenames:
                file_path = Path(filename)
                file_name_str = file_path.name # Nombre del archivo

                # Validar nombre usando la estructura de VIs
                # Desempaquetar los 4 valores, aunque solo usemos is_valid aquí
                is_valid, _, _, _ = validate_filename_for_study_criteria(
                    file_name_str, self.independent_variables # Pasar estructura VIs
                )

                # Crear nombre para mostrar en la lista
                display_name = f"{file_name_str}{'' if is_valid else ' (Nombre Inválido)'}"

                # Evitar duplicados en la lista visual
                if display_name not in current_display_names_in_list:
                    self.listbox.insert(tk.END, display_name)
                    self.listbox.itemconfig(tk.END, {'fg': 'black' if is_valid else 'red'})
                    # Guardar mapeo display_name -> Path
                    self.listbox_item_to_path[display_name] = file_path
                    new_files_added = True
                else:
                    logger.debug(f"Archivo '{file_name_str}' ya está en la lista (o tiene el mismo estado de validez).")


            if new_files_added:
                # Habilitar botón solo si hay al menos un archivo válido en la lista
                has_valid_files = any('(Nombre Inválido)' not in item for item in self.listbox_item_to_path.keys())
                self.process_button.config(state=tk.NORMAL if has_valid_files else tk.DISABLED)

    def remove_selected(self):
        """Quita los archivos seleccionados de la listbox y del mapeo."""
        selected_indices = self.listbox.curselection()
        items_to_remove = [self.listbox.get(i) for i in selected_indices]

        # Eliminar del mapeo
        for item_display_name in items_to_remove:
            if item_display_name in self.listbox_item_to_path:
                del self.listbox_item_to_path[item_display_name]

        # Eliminar de la listbox (iterar en reversa)
        for i in reversed(selected_indices):
            self.listbox.delete(i)

        # Actualizar estado del botón
        has_valid_files = any('(Nombre Inválido)' not in item for item in self.listbox_item_to_path.keys())
        self.process_button.config(state=tk.NORMAL if has_valid_files else tk.DISABLED)

    def _validate_files_for_processing(self) -> Tuple[bool, str]:
        """
        Valida los archivos seleccionados contra los límites de sujetos e intentos
        (granular por combinación sujeto+sub-valores) del estudio.
        Considera los archivos existentes + los seleccionados.

        :return: Tupla (bool: es_valido, str: mensaje_error si no es válido)
        """
        import copy # Para deepcopy
        from typing import Tuple # Añadir Tuple para type hint

        logger.info(f"Iniciando validación de límites para {len(self.listbox_item_to_path)} archivos en lista para estudio {self.study_id}")

        # 1. Obtener límites y VIs del estudio
        try:
            max_subjects_allowed = self.study_details.get('num_subjects')
            max_attempts_allowed = self.study_details.get('attempts_count')
            independent_variables = self.study_details.get('independent_variables', [])

            if max_subjects_allowed is None or max_attempts_allowed is None:
                 raise ValueError("Límites de sujetos o intentos no definidos en los detalles del estudio.")
            logger.debug(f"Límites: {max_subjects_allowed} sujetos, {max_attempts_allowed} intentos/combinación.")
        except Exception as e:
            msg = f"Error obteniendo límites/VIs del estudio: {e}"
            logger.error(msg, exc_info=True)
            return False, msg

        # 2. Obtener estado actual de archivos del estudio
        try:
            # Usar la nueva estructura devuelta por _get_study_file_details
            existing_attempts_by_combination, existing_unique_subjects = self.file_service._get_study_file_details(self.study_id)
            logger.debug(f"Estado actual: {len(existing_unique_subjects)} sujetos. Intentos/comb: {existing_attempts_by_combination}")
        except Exception as e:
            msg = f"Error obteniendo detalles de archivos existentes: {e}"
            logger.error(msg, exc_info=True)
            return False, msg

        # 3. Simular adición de archivos seleccionados (válidos)
        simulated_attempts_by_combination = copy.deepcopy(existing_attempts_by_combination)
        simulated_unique_subjects = copy.deepcopy(existing_unique_subjects)
        validation_errors = []

        # Iterar sobre los archivos en la lista (mapeo)
        for display_name, file_path in self.listbox_item_to_path.items():
            file_name = file_path.name

            # Solo considerar archivos marcados como válidos en la lista
            if '(Nombre Inválido)' in display_name:
                logger.debug(f"Omitiendo archivo con nombre inválido '{file_name}' de la validación de límites.")
                continue

            # Validar nombre y extraer info (debería ser válido si no tiene la marca)
            is_valid, subject_id, extracted_descriptors, attempt_num = validate_filename_for_study_criteria(
                file_name, independent_variables
            )

            # Doble chequeo por si acaso
            if not is_valid or not subject_id or attempt_num is None:
                logger.warning(f"Archivo '{file_name}' marcado como válido pero falló la re-validación. Omitiendo de límites.")
                continue

            # Añadir sujeto al conjunto simulado
            simulated_unique_subjects.add(subject_id)

            # Crear clave de combinación y añadir intento
            combination_key = (subject_id, tuple(extracted_descriptors))
            if combination_key not in simulated_attempts_by_combination:
                simulated_attempts_by_combination[combination_key] = set()
            simulated_attempts_by_combination[combination_key].add(attempt_num)

        # 4. Realizar validaciones con datos simulados
        # 4.1. Validar número total de sujetos
        if len(simulated_unique_subjects) > max_subjects_allowed:
            msg = (f"Límite de sujetos excedido ({max_subjects_allowed}). "
                   f"El estudio tiene {len(existing_unique_subjects)} y con los seleccionados serían {len(simulated_unique_subjects)}.")
            logger.warning(msg)
            validation_errors.append(msg)

        # 4.2. Validar número de intentos por combinación
        for combination_key, attempts_set in simulated_attempts_by_combination.items():
            if len(attempts_set) > max_attempts_allowed:
                subject, descriptors = combination_key
                # Formatear sub-valores para el mensaje
                desc_str = ", ".join(d if d is not None else "Nulo" for d in descriptors)
                msg = (f"Límite de intentos excedido ({max_attempts_allowed}) para:\n"
                       f"  Sujeto: {subject}\n"
                       f"  Sub-valores: [{desc_str}]\n"
                       f"Se encontraron {len(attempts_set)} intentos.")
                logger.warning(msg)
                validation_errors.append(msg)

        # 5. Devolver resultado
        if validation_errors:
            # Construir mensaje de error consolidado
            final_error_message = "Errores de validación:\n- " + "\n- ".join(validation_errors)
            # Añadir info sobre estado actual y lo que se intenta añadir
            final_error_message += f"\n\nActualmente: {len(existing_unique_subjects)} sujetos."
            max_existing_attempts = 0
            for attempts in existing_attempts_by_combination.values():
                 max_existing_attempts = max(max_existing_attempts, len(attempts))
            final_error_message += f" Máximo {max_existing_attempts} intentos por combinación."

            final_error_message += f"\nIntentando añadir archivos que resultarían en: {len(simulated_unique_subjects)} sujetos."
            max_simulated_attempts = 0
            for attempts in simulated_attempts_by_combination.values():
                 max_simulated_attempts = max(max_simulated_attempts, len(attempts))
            final_error_message += f" Máximo {max_simulated_attempts} intentos por combinación."

            return False, final_error_message
        else:
            logger.info("Validación de límites exitosa.")
            return True, ""


    def process_files(self):
        """Valida y luego llama al FileService para procesar los archivos seleccionados válidos."""
        # Obtener solo los archivos válidos del mapeo
        valid_files_to_process = []
        invalid_names_skipped = []
        for display_name, file_path in self.listbox_item_to_path.items():
            if '(Nombre Inválido)' not in display_name:
                valid_files_to_process.append(file_path)
            else:
                invalid_names_skipped.append(file_path.name)

        if not valid_files_to_process:
            # Esto no debería ocurrir si el botón de procesar está deshabilitado correctamente
            messagebox.showwarning("Sin Archivos Válidos", "No hay archivos con nombres válidos en la lista para procesar.", parent=self)
            return

        # Convertir Paths a strings para el servicio
        file_path_strings = [str(p) for p in valid_files_to_process]

        try:
            # Deshabilitar botones durante el procesamiento
            self.process_button.config(state=tk.DISABLED)
            self.grab_set() # Bloquear interacción con otras ventanas
            self.update_idletasks() # Forzar actualización UI

            # Llamar al servicio (FileService ya no valida límites)
            results = self.file_service.add_files_to_study(self.study_id, file_path_strings)

            # Mostrar resultados
            success_count = results.get('success', 0)
            errors = results.get('errors', [])
            skipped_count = len(invalid_names_skipped)

            message = f"Procesamiento completado.\n\n"
            message += f"Archivos agregados exitosamente: {success_count}\n"
            if skipped_count > 0:
                 message += f"Archivos omitidos por nombre inválido: {skipped_count}\n"
            if errors:
                message += f"\nErrores encontrados ({len(errors)}):\n"
                message += "\n".join([f"- {err}" for err in errors[:10]]) # Mostrar hasta 10 errores
                if len(errors) > 10:
                    message += f"\n... y {len(errors) - 10} más."

            if errors or skipped_count > 0:
                 messagebox.showwarning("Resultado Procesamiento", message, parent=self)
            else:
                 messagebox.showinfo("Resultado Procesamiento", message, parent=self)

            # Llamar al callback si hubo éxito y existe callback
            if success_count > 0 and self.on_close_callback:
                self.on_close_callback()

            self.destroy() # Cerrar diálogo después de mostrar mensaje

        except Exception as e:
            logger.critical(f"Error inesperado durante el procesamiento de archivos para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado durante el procesamiento:\n{e}", parent=self)
            # Habilitar botón de nuevo en caso de error crítico
            self.process_button.config(state=tk.NORMAL if self.selected_files else tk.DISABLED)
            self.grab_release()
            # import traceback # Ya no es necesario
            # traceback.print_exc() # Reemplazado por logger
        finally:
             # Asegurarse de liberar el grab si aún está activo
             try:
                 self.grab_release()
             except tk.TclError:
                 pass # Ignorar si ya no existe

    def destroy(self):
        """Sobrescribir destroy para asegurar que grab_release se llame."""
        try:
            self.grab_release()
        except tk.TclError:
            pass
        super().destroy()

# Para pruebas directas (si es necesario)
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw() # Ocultar ventana raíz

    # --- Clases y Servicios Dummy ---
    class DummyStudyService:
        def get_study_details(self, study_id):
            # Usar print aquí está bien para un dummy __main__
            print(f"DummyStudyService: get_study_details({study_id})")
            # Simular criterios para prueba
            return {
                'id': study_id,
                'name': f'Estudio_{study_id}',
                'num_subjects': 5,
                'test_types': 'CMJ,SJ', # Criterios de ejemplo
                'test_periods': 'PRE,POST', # Criterios de ejemplo
                'attempts_count': 3
            }
    class DummyFileService:
        def __init__(self, study_service):
            self.study_service = study_service

        def add_files_to_study(self, study_id, file_paths):
            # Usar print aquí está bien para un dummy __main__
            print(f"DummyFileService: add_files_to_study({study_id}, {file_paths})")
            # Simular procesamiento
            results = {'success': 0, 'errors': []}
            for i, fpath in enumerate(file_paths):
                if i % 2 == 0: # Simular éxito para pares
                    results['success'] += 1
                    print(f"  -> Procesando {os.path.basename(fpath)}... Éxito (simulado)")
                else: # Simular error para impares
                    results['errors'].append(f"{os.path.basename(fpath)}: Error simulado de procesamiento.")
                    print(f"  -> Procesando {os.path.basename(fpath)}... Error (simulado)")
            import time
            time.sleep(1) # Simular tiempo de procesamiento
            return results
    # --- Fin Clases Dummy ---

    dummy_study_service = DummyStudyService()
    dummy_file_service = DummyFileService(dummy_study_service)

    def my_callback():
        # Usar print aquí está bien para un dummy __main__
        print("Callback llamado después de agregar archivos!")

    dialog = FileDialog(root, dummy_file_service, 1, my_callback)
    root.wait_window(dialog)
    root.destroy()
