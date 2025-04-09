import tkinter as tk # Importar tk para fill/expand
from tkinter import ttk, messagebox # Importar messagebox
import logging # Importar logging
# Ya no se necesita PaginatedTable aquí
from kineviz.ui.widgets.file_browser import FileBrowser
# Importar FileService para type hinting
from kineviz.core.services.file_service import FileService
# Importar diálogos necesarios
from kineviz.ui.dialogs.file_dialog import FileDialog
from kineviz.ui.dialogs.descriptor_alias_dialog import DescriptorAliasDialog

logger = logging.getLogger(__name__) # Logger para este módulo

class StudyView:
    # Añadir file_service y aceptar config
    def __init__(self, parent, main_window, study_id: int, file_service: FileService):
        self.parent = parent
        self.main_window = main_window # Guardar referencia a main_window para acceder a config
        self.study_id = study_id
        self.file_service = file_service
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_ui()

    def create_ui(self):
        # --- Header ---
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, pady=(0, 10)) # Añadir padding inferior

        # Botón Volver (podría ir a MainView si hay estudios, o LandingPage si no)
        # Simplificado: siempre a main_view por ahora, refresh se encargará si no hay estudios
        back_command = self.main_window.show_main_view
        # Opcional: decidir basado en si hay estudios (más complejo)
        # back_command = self.main_window.show_main_view if self.main_window.study_service.has_studies() else self.main_window.show_landing_page
        ttk.Button(header_frame, text="<< Volver a Estudios",
                   command=back_command).pack(side=tk.LEFT, padx=(0, 10))

        # Botón Analizar - Corregir comando
        ttk.Button(header_frame, text="Analizar Estudio",
                   command=lambda: self.main_window.show_analysis_dialog(self.study_id)).pack(side=tk.LEFT, padx=(0, 10))

        # Botón Agregar Archivos                                                                                                               
        ttk.Button(header_frame, text="Agregar Archivos",                                                                                      
                   command=self.add_files_dialog).pack(side=tk.LEFT, padx=(0, 10))

        # Botón Abrir Carpeta Estudio (Movido desde interfaz.py)
        ttk.Button(header_frame, text="Abrir Carpeta Estudio",
                   command=self.open_study_folder).pack(side=tk.LEFT, padx=(0, 10))

        # Botón Gestionar Alias
        ttk.Button(header_frame, text="Gestionar Alias Descriptores",
                   command=self.manage_descriptor_aliases).pack(side=tk.LEFT, padx=(0, 10))

        # Botón Análisis Discreto (Fase 6)
        ttk.Button(header_frame, text="Análisis Discreto",
                   command=lambda: self.main_window.show_discrete_analysis_view(self.study_id)).pack(side=tk.LEFT, padx=(0, 10))


        # --- Detalles del estudio ---
        study_details = self.main_window.study_service.get_study_details(self.study_id)
        details_frame = ttk.LabelFrame(self.frame, text="Detalles del Estudio")
        details_frame.pack(fill='x', padx=10, pady=10)

        # Corregido: Mostrar solo una vez el nombre
        ttk.Label(details_frame, text=f"Nombre: {study_details.get('name', 'N/A')}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Número de Sujetos: {study_details.get('num_subjects', 'N/A')}").pack(anchor='w', padx=5, pady=2)
        # Mostrar Descriptores definidos en el estudio
        defined_descriptors_str = study_details.get('descriptores', 'Ninguno') or 'Ninguno'
        ttk.Label(details_frame, text=f"Descriptores Definidos: {defined_descriptors_str}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Intentos: {study_details.get('attempts_count', 'N/A')}").pack(anchor='w', padx=5, pady=2)

        # Mostrar Alias asignados a descriptores detectados
        self.alias_label = ttk.Label(details_frame, text="Alias Asignados: Cargando...", wraplength=500) # Usar wraplength
        self.alias_label.pack(anchor='w', padx=5, pady=2)
        self.update_alias_display() # Llamar a método para cargar y mostrar alias

        # --- File browser ---
        # Pasar la instancia de file_service y files_per_page desde main_window
        files_per_page = self.main_window.files_per_page # Obtener de main_window
        self.file_browser = FileBrowser(self.frame, self.file_service, self.study_id, files_per_page)
        self.file_browser.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    def update_alias_display(self):
        """Obtiene y muestra los alias asignados a los descriptores detectados."""
        logger.debug(f"Actualizando display de alias para estudio {self.study_id}") # Log inicio
        try:
            # Obtener descriptores detectados
            params = self.file_service.get_unique_study_parameters(self.study_id)
            detected_descriptors = sorted(list(params.get('descriptors', set())))
            logger.debug(f"Descriptores detectados: {detected_descriptors}") # Log descriptores

            if not detected_descriptors:
                self.alias_label.config(text="Alias Asignados: No se detectaron descriptores en archivos válidos.")
                logger.debug("Display de alias actualizado: Sin descriptores detectados.") # Log sin descriptores
                return

            # Obtener alias de la configuración
            all_aliases = self.main_window.settings.get_all_aliases()
            logger.debug(f"Aliases obtenidos de settings: {all_aliases}") # Log aliases cargados

            # Construir string de alias
            alias_parts = []
            for desc in detected_descriptors:
                # Buscar alias usando la versión en minúsculas del descriptor
                alias = all_aliases.get(desc.lower())
                if alias:
                    # Mostrar el descriptor original y su alias
                    alias_parts.append(f"{desc} ({alias})")
                else:
                    alias_parts.append(desc) # Mostrar descriptor original si no hay alias

            alias_display_text = "Alias Asignados: " + ", ".join(alias_parts)
            self.alias_label.config(text=alias_display_text)
            logger.debug(f"Display de alias actualizado a: '{alias_display_text}'") # Log texto final

        except Exception as e:
            logger.error(f"Error actualizando display de alias para estudio {self.study_id}: {e}", exc_info=True)
            self.alias_label.config(text="Alias Asignados: Error al cargar.")


    def manage_descriptor_aliases(self):
        """Abre el diálogo para gestionar los alias de los descriptores."""
        # Necesitamos pasar AppSettings, FileService y study_id
        dialog = DescriptorAliasDialog( # Asignar a la variable 'dialog'
            self.frame, # Padre
            self.main_window.settings, # AppSettings desde MainWindow
            self.file_service,
            self.study_id
        )
        # Esperar a que el diálogo se cierre y luego actualizar la etiqueta de alias
        self.parent.wait_window(dialog) # Espera a que el Toplevel se cierre
        self.update_alias_display() # Actualizar la información mostrada

    def open_study_folder(self):
        """Abre la carpeta del estudio actual."""
        try:
            study_details = self.main_window.study_service.get_study_details(self.study_id)
            study_name = study_details['name']
            # Construir la ruta relativa a la carpeta 'estudios'
            folder_path_str = f"estudios/{study_name}"
            self.main_window.open_folder(folder_path_str)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener la ruta del estudio: {e}", parent=self.frame)

    def add_files_dialog(self):
        """Abre el diálogo para seleccionar y agregar archivos al estudio."""
        # Pasar el file_service y el study_id, junto con el callback para refrescar
        FileDialog(self.frame, self.main_window.file_service, self.study_id, self.refresh_file_list)

    def refresh_file_list(self):
        """Refresca la lista de archivos en el FileBrowser."""
        if self.file_browser:
            self.file_browser.load_files()

    def destroy(self):
        """Destruye el frame principal de esta vista."""
        # Asegurarse de que el frame exista antes de destruirlo
        if self.frame and self.frame.winfo_exists():
             self.frame.destroy()
        self.frame = None # Limpiar referencia
