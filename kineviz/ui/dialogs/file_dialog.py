import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, filedialog, Listbox, Scrollbar
from pathlib import Path
import os # Para os.path.basename
import logging # Importar logging

# Importar FileService para type hinting y validación
from kineviz.core.services.file_service import FileService
from kineviz.ui.utils.validators import validate_filename_for_study_criteria

logger = logging.getLogger(__name__) # Logger para este módulo

class FileDialog(Toplevel):
    """Diálogo para seleccionar y agregar archivos a un estudio."""

    def __init__(self, parent, file_service: FileService, study_id: int, on_close_callback=None):
        super().__init__(parent)
        self.file_service = file_service
        self.study_id = study_id
        self.on_close_callback = on_close_callback
        self.selected_files = [] # Lista de rutas (Path objects)

        # Obtener criterios del estudio para validación previa (opcional pero mejora UX)
        self.study_details = None
        self.valid_types = []
        self.valid_periods = []
        try:
            self.study_details = self.file_service.study_service.get_study_details(self.study_id)
            types_str = self.study_details.get('test_types', '') or ''
            periods_str = self.study_details.get('test_periods', '') or ''
            self.valid_types = [t.strip() for t in types_str.split(',') if t.strip()]
            self.valid_periods = [p.strip() for p in periods_str.split(',') if p.strip()]
        except Exception as e:
            logger.error(f"No se pudieron cargar los detalles del estudio {self.study_id} en FileDialog: {e}", exc_info=True)
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
        # Código para centrar (similar a StudyDialog)
        # ...

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Botón para seleccionar archivos
        select_button = ttk.Button(main_frame, text="Seleccionar Archivos (.txt, .csv)", command=self.select_files)
        select_button.pack(pady=10)

        # Listbox para mostrar archivos seleccionados
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = Scrollbar(list_frame, orient=tk.VERTICAL)
        self.listbox = Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED) # Permitir selección múltiple
        scrollbar.config(command=self.listbox.yview)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Botón para quitar archivos seleccionados de la lista (opcional)
        remove_button = ttk.Button(main_frame, text="Quitar Seleccionados", command=self.remove_selected)
        remove_button.pack(pady=5)

        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        self.process_button = ttk.Button(button_frame, text="Procesar Archivos Seleccionados", command=self.process_files, state=tk.DISABLED)
        self.process_button.pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def select_files(self):
        """Abre el diálogo del sistema para seleccionar archivos."""
        filetypes = [("Archivos de texto", "*.txt"), ("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        # Usar askopenfilenames para selección múltiple
        filenames = filedialog.askopenfilenames(title="Seleccionar Archivos", filetypes=filetypes, parent=self)

        if filenames:
            new_files_added = False
            current_paths_in_list = {self.listbox.get(i) for i in range(self.listbox.size())}

            for filename in filenames:
                file_path = Path(filename)
                # Evitar duplicados en la lista
                if str(file_path) not in current_paths_in_list:
                    # Validar nombre antes de añadir a la lista (feedback temprano)
                    is_valid = validate_filename_for_study_criteria(
                        file_path.name, self.valid_types, self.valid_periods
                    )
                    # Añadir a la lista visual y a la lista interna
                    # Marcar visualmente si es inválido
                    display_name = f"{file_path.name}{'' if is_valid else ' (Nombre Inválido)'}"
                    self.listbox.insert(tk.END, display_name)
                    self.listbox.itemconfig(tk.END, {'fg': 'black' if is_valid else 'red'})
                    self.selected_files.append(file_path) # Guardar Path object
                    new_files_added = True

            if new_files_added:
                self.process_button.config(state=tk.NORMAL) # Habilitar botón si hay archivos

    def remove_selected(self):
        """Quita los archivos seleccionados de la listbox y de self.selected_files."""
        selected_indices = self.listbox.curselection()
        # Iterar en reversa para evitar problemas con índices cambiantes
        for i in reversed(selected_indices):
            # Encontrar el Path correspondiente en self.selected_files
            # Esto es un poco ineficiente si la lista es muy grande.
            # Podríamos almacenar el Path en el tag del item o usar un diccionario.
            display_name_with_status = self.listbox.get(i)
            # Extraer nombre base para buscar
            base_name = display_name_with_status.split(' (')[0]
            path_to_remove = None
            for p in self.selected_files:
                if p.name == base_name:
                    path_to_remove = p
                    break
            if path_to_remove:
                self.selected_files.remove(path_to_remove)

            self.listbox.delete(i)

        if not self.selected_files:
            self.process_button.config(state=tk.DISABLED)

    def process_files(self):
        """Llama al FileService para procesar los archivos seleccionados."""
        if not self.selected_files:
            messagebox.showwarning("Sin Archivos", "No hay archivos seleccionados para procesar.", parent=self)
            return

        # Filtrar solo los archivos cuyo nombre fue validado previamente
        # (Podríamos revalidar aquí por si acaso, pero confiamos en la validación inicial)
        valid_files_to_process = []
        invalid_names_skipped = []
        for i in range(self.listbox.size()):
             display_name = self.listbox.get(i)
             # Asumimos que el Path correspondiente está en self.selected_files[i]
             # ¡CUIDADO! Esto falla si se eliminan items. Necesitamos una mejor forma de mapear.
             # Mejor reconstruir la lista de Paths válidos desde la listbox
             if '(Nombre Inválido)' not in display_name:
                 # Buscar el Path correspondiente
                 base_name = display_name.split(' (')[0]
                 found_path = None
                 for p in self.selected_files:
                     if p.name == base_name:
                         found_path = p
                         break
                 if found_path:
                     valid_files_to_process.append(found_path)
             else:
                 invalid_names_skipped.append(display_name.split(' (')[0])


        if not valid_files_to_process:
             messagebox.showwarning("Sin Archivos Válidos", "No hay archivos con nombres válidos seleccionados para procesar.", parent=self)
             return

        # Convertir Paths a strings para el servicio (o asegurarse que el servicio acepte Paths)
        file_path_strings = [str(p) for p in valid_files_to_process]

        try:
            # Deshabilitar botones durante el procesamiento
            self.process_button.config(state=tk.DISABLED)
            self.grab_set() # Bloquear interacción con otras ventanas
            self.update_idletasks() # Forzar actualización UI

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
