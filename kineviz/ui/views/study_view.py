import tkinter as tk # Importar tk para fill/expand
from tkinter import ttk, messagebox # Importar messagebox
import logging # Importar logging
# Ya no se necesita PaginatedTable aquí
from kineviz.ui.widgets.file_browser import FileBrowser
# Importar FileService para type hinting
from kineviz.core.services.file_service import FileService
# Importar diálogos necesarios
from kineviz.ui.dialogs.file_dialog import FileDialog
# DescriptorAliasDialog ya no se usa con la nueva estructura VI
# from kineviz.ui.dialogs.descriptor_alias_dialog import DescriptorAliasDialog
from kineviz.ui.widgets.tooltip import ToolTip # Para mostrar descriptores
import json # Para parsear estructura VI

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
        # Botón Gestionar Alias Descriptores (Eliminado - ya no aplica directamente)
        # ttk.Button(header_frame, text="Gestionar Alias Descriptores",
        #            command=self.manage_descriptor_aliases).pack(side=tk.LEFT, padx=(0, 10))

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
        ttk.Label(details_frame, text=f"Intentos: {study_details.get('attempts_count', 'N/A')}").pack(anchor='w', padx=5, pady=2)

        # Mostrar Variables Independientes y Descriptores
        vi_frame = ttk.Frame(details_frame)
        vi_frame.pack(anchor='w', padx=5, pady=2)
        ttk.Label(vi_frame, text="Variables Independientes: ").pack(side=tk.LEFT)
        self.vi_label = ttk.Label(vi_frame, text="Cargando...")
        self.vi_label.pack(side=tk.LEFT)
        self.info_vi_button = ttk.Label(vi_frame, text="ℹ️", cursor="question_arrow", foreground="blue")
        self.info_vi_button.pack(side=tk.LEFT, padx=5)
        self.info_vi_tooltip = ToolTip(self.info_vi_button, "") # Tooltip se llenará después

        self.load_and_display_vi_structure(study_details)

        # --- File browser ---
        # Pasar la instancia de file_service y files_per_page desde main_window
        files_per_page = self.main_window.files_per_page # Obtener de main_window
        self.file_browser = FileBrowser(self.frame, self.file_service, self.study_id, files_per_page)
        self.file_browser.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        def load_and_display_vi_structure(self, study_details):
            """Carga la estructura VI y actualiza la UI."""
            vi_structure = study_details.get('independent_variables_struct', [])
            if not vi_structure:
                self.vi_label.config(text="No definidas")
                self.info_vi_button.pack_forget() # Ocultar botón info si no hay VIs
                return

            vi_names = [vi.get('name', f'VI {i+1}') for i, vi in enumerate(vi_structure)]
            self.vi_label.config(text=", ".join(vi_names))

            # Crear texto para el tooltip
            tooltip_text = ""
            for i, vi in enumerate(vi_structure):
                name = vi.get('name', f'VI {i+1}')
                descriptors = vi.get('descriptors', [])
                tooltip_text += f"{name}:\n  " + ", ".join(descriptors) + "\n\n"

            self.info_vi_tooltip.text = tooltip_text.strip()
            self.info_vi_button.pack(side=tk.LEFT, padx=5) # Asegurar que esté visible

        # Eliminar manage_descriptor_aliases y update_alias_display

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
