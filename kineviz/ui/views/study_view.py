import tkinter as tk # Importar tk para fill/expand
from tkinter import ttk, messagebox # Importar messagebox
import logging # Importar logging
import webbrowser # Para abrir archivo de ayuda                                                                                     
from pathlib import Path # Para construir ruta de ayuda  
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
        self.frame = ttk.Frame(parent) # This is the outermost frame for StudyView
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Setup for scrollable area ---
        canvas_container = ttk.Frame(self.frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        
        self.scrollable_frame = ttk.Frame(self.canvas) # Content goes here

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        # Removed problematic canvas.bind("<Configure>") that forced inner frame width

        self.canvas.interior_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        # --- End scrollable area setup ---

        self.create_ui_content(self.scrollable_frame) # Pass scrollable_frame as parent for content

    def create_ui_content(self, parent_frame): # Renamed from create_ui, parent_frame is self.scrollable_frame
        # --- Header Row 1 ---
        header_frame_row1 = ttk.Frame(parent_frame) # Changed parent
        header_frame_row1.pack(fill=tk.X, pady=(0, 5))

        back_command = self.main_window.show_main_view
        ttk.Button(header_frame_row1, text="<< Volver a Estudios",
                   command=back_command).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(header_frame_row1, text="Agregar Archivo(s)",                                                                                      
                   command=self.add_files_dialog, style="Celeste.TButton").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(header_frame_row1, text="Análisis Discreto",
                   command=lambda: self.main_window.show_discrete_analysis_view(self.study_id), style="Green.TButton").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(header_frame_row1, text="Análisis Continuo",
                   command=lambda: self.main_window.show_continuous_analysis_manager_dialog(self.study_id), style="Green.TButton").pack(side=tk.LEFT, padx=(0, 10))

        # Botón Ayuda General (a la derecha de la primera fila de header)
        style = ttk.Style() 
        style.configure("HelpView.TButton", foreground="white", background="green") 
        help_button_general = ttk.Button(header_frame_row1, text="?", width=3, style="HelpView.TButton", command=self.show_study_view_help)
        help_button_general.pack(side=tk.RIGHT, padx=(10, 0))

        # --- Header Row 2 ---
        header_frame_row2 = ttk.Frame(parent_frame) # Changed parent
        header_frame_row2.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(header_frame_row2, text="Abrir Carpeta de Estudio", # Renamed
                   command=self.open_study_folder).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(header_frame_row2, text="Gestionar Alias de Sub-valores", # Renamed
                   command=self.manage_descriptor_aliases).pack(side=tk.LEFT, padx=(0, 10))


        # --- Detalles del estudio ---
        study_details = self.main_window.study_service.get_study_details(self.study_id)
        details_frame = ttk.LabelFrame(parent_frame, text="Detalles del Estudio") # Changed parent
        details_frame.pack(fill='x', padx=10, pady=10) # Keep pady for spacing from header_frame_row2

        # Corregido: Mostrar solo una vez el nombre
        ttk.Label(details_frame, text=f"Nombre del Estudio: {study_details.get('name', 'N/A')}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Cantidad de Participantes: {study_details.get('num_subjects', 'N/A')}").pack(anchor='w', padx=5, pady=2)
        ttk.Label(details_frame, text=f"Cantidad de Intento(s) de Prueba: {study_details.get('attempts_count', 'N/A')}").pack(anchor='w', padx=5, pady=2)

        # --- Mostrar Variables Independientes y Botón Info ---
        vi_frame = ttk.Frame(details_frame)
        vi_frame.pack(anchor='w', padx=5, pady=2, fill='x')

        # Extraer nombres de VIs
        independent_variables = study_details.get('independent_variables', [])
        vi_names = [iv.get('name', 'N/A') for iv in independent_variables]
        vi_display_text = "Variable(s) Independientes (VIs): " + (", ".join(vi_names) if vi_names else "Ninguna")
        ttk.Label(vi_frame, text=vi_display_text).pack(side=tk.LEFT, anchor='w')

        # Botón Info (si hay VIs)
        if vi_names:
            info_button = ttk.Button(vi_frame, text="ℹ️", width=3, command=self.show_vi_descriptor_info)
            info_button.pack(side=tk.LEFT, padx=(5, 0))
        # --- Fin VIs ---

        # Mostrar Alias asignados a sub-valores definidos
        self.alias_label = ttk.Label(details_frame, text="Alias Asignados: Cargando...", wraplength=500) # Usar wraplength
        self.alias_label.pack(anchor='w', padx=5, pady=2)
        # No llamar aquí, se llama después de obtener detalles
        # self.update_alias_display()

        # --- File browser ---
        # Pasar la instancia de file_service y files_per_page desde main_window
        files_per_page = self.main_window.files_per_page # Obtener de main_window
        self.file_browser = FileBrowser(self.frame, self.file_service, self.study_id, files_per_page)
        # --- Botón Eliminar Todos los Archivos (y seleccionados) ---
        # Empaquetar este frame al final (side=tk.BOTTOM) para que no sea empujado por FileBrowser
        delete_all_files_button_frame = ttk.Frame(parent_frame) # Changed parent
        delete_all_files_button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        delete_all_files_button = ttk.Button(
            delete_all_files_button_frame, # Parent is this new frame
            text="Eliminar Todos los Archivos del Estudio",
            command=self._confirm_delete_all_files,
            style="Danger.TButton"
        )
        delete_all_files_button.pack(side=tk.LEFT, padx=(0,5))

        # Botón Eliminar Archivo(s) Seleccionado(s)
        self.delete_selected_files_button = ttk.Button(
            delete_all_files_button_frame, # Parent is this new frame
            text="Eliminar Archivo(s) Seleccionado(s)",
            command=self._confirm_delete_selected_files_from_browser,
            style="Danger.TButton",
            state=tk.DISABLED
        )
        self.delete_selected_files_button.pack(side=tk.LEFT, padx=(0, 5))

        # FileBrowser se empaqueta después de los detalles y ANTES del frame de botones de eliminación
        # para que los botones de eliminación queden fijos en la parte inferior.
        files_per_page = self.main_window.files_per_page
        self.file_browser = FileBrowser(parent_frame, self.file_service, self.study_id, files_per_page) # Changed parent
        self.file_browser.pack(fill=tk.BOTH, expand=True, pady=(10, 0)) # FileBrowser toma el espacio restante
        self.file_browser.bind("<<FileBrowserSelectionChanged>>", self._on_file_browser_selection_changed)

        # Llamar a update_alias_display después de que todo esté creado
        self.update_alias_display()

    def _on_file_browser_selection_changed(self, event=None):
        """Actualiza el estado del botón 'Eliminar Archivo(s) Seleccionado(s)'."""
        if self.file_browser and self.file_browser.get_selected_file_paths():
            self.delete_selected_files_button.config(state=tk.NORMAL)
        else:
            self.delete_selected_files_button.config(state=tk.DISABLED)

    def _confirm_delete_selected_files_from_browser(self):
        """Muestra confirmación y elimina los archivos seleccionados en FileBrowser."""
        if not self.file_browser:
            return

        selected_file_paths = self.file_browser.get_selected_file_paths()
        if not selected_file_paths:
            messagebox.showwarning("Sin Selección", "No hay archivos seleccionados para eliminar.", parent=self.frame)
            return

        if messagebox.askyesno("Confirmar Eliminación",
                               f"¿Está seguro de que desea eliminar los {len(selected_file_paths)} archivo(s) seleccionados?\n"
                               "Esta acción es IRREVERSIBLE.",
                               icon='warning', parent=self.frame):
            try:
                self.file_service.delete_selected_files(self.study_id, selected_file_paths)
                messagebox.showinfo("Éxito", f"{len(selected_file_paths)} archivo(s) eliminado(s) correctamente.", parent=self.frame)
                self.refresh_file_list() # Recargar la lista de archivos
            except Exception as e:
                logger.error(f"Error al eliminar archivos seleccionados del estudio {self.study_id}: {e}", exc_info=True)
                messagebox.showerror("Error al Eliminar", f"No se pudieron eliminar los archivos seleccionados:\n{e}", parent=self.frame)
                self.refresh_file_list() # Recargar también en caso de error parcial

    def _confirm_delete_all_files(self):
        """Muestra confirmación y luego elimina todos los archivos del estudio."""
        study_details = self.main_window.study_service.get_study_details(self.study_id)
        study_name = study_details.get('name', f"ID {self.study_id}")
        if messagebox.askyesno("Confirmar Eliminación de Archivos",
                               f"¿Está SEGURO de que desea eliminar TODOS los archivos (originales y procesados) "
                               f"del estudio '{study_name}'?\n\n"
                               "Esta acción es IRREVERSIBLE.",
                               icon='warning', parent=self.frame):
            try:
                self.file_service.delete_all_files_in_study(self.study_id)
                messagebox.showinfo("Eliminación Completada",
                                    "Todos los archivos del estudio han sido eliminados.",
                                    parent=self.frame)
                self.refresh_file_list() # Actualizar el FileBrowser
            except Exception as e:
                logger.error(f"Error al eliminar todos los archivos del estudio {self.study_id}: {e}", exc_info=True)
                messagebox.showerror("Error al Eliminar Archivos",
                                     f"Ocurrió un error al eliminar los archivos:\n{e}",
                                     parent=self.frame)

    def update_alias_display(self):
        """Obtiene y muestra los alias asignados a los sub-valores definidos."""
        logger.debug(f"Actualizando display de alias para estudio {self.study_id}")
        try:
            # Obtener detalles del estudio (incluye VIs y alias)
            study_details = self.main_window.study_service.get_study_details(self.study_id)
            independent_variables = study_details.get('independent_variables', [])
            study_aliases = study_details.get('aliases', {}) # Alias específicos del estudio
            logger.debug(f"Aliases cargados para estudio {self.study_id}: {study_aliases}")

            # Extraer todos los sub-valores definidos
            defined_descriptors = set()
            for iv in independent_variables:
                if isinstance(iv, dict) and 'descriptors' in iv and isinstance(iv['descriptors'], list):
                    for desc in iv['descriptors']:
                        if isinstance(desc, str) and desc.strip():
                            defined_descriptors.add(desc.strip())

            if not defined_descriptors:
                self.alias_label.config(text="Alias Asignados: No hay sub-valores definidos en este estudio.")
                logger.debug("Display de alias actualizado: Sin sub-valores definidos.")
                return

            # Construir string de alias para sub-valores definidos
            alias_parts = []
            # Ordenar para consistencia
            for desc in sorted(list(defined_descriptors)):
                alias = study_aliases.get(desc) # Obtener alias específico del estudio
                if alias:
                    alias_parts.append(f"{desc} ({alias})")
                else:
                    alias_parts.append(desc) # Mostrar sub-valor original si no hay alias

            alias_display_text = "Alias Asignados: " + ", ".join(alias_parts)
            self.alias_label.config(text=alias_display_text)
            logger.debug(f"Display de alias actualizado a: '{alias_display_text}'")

        except Exception as e:
            logger.error(f"Error actualizando display de alias para estudio {self.study_id}: {e}", exc_info=True)
            self.alias_label.config(text="Alias Asignados: Error al cargar.")


    def manage_descriptor_aliases(self):
        """Abre el diálogo para gestionar los alias de los sub-valores."""
        # Pasar StudyService y study_id
        dialog = DescriptorAliasDialog(
            self.frame, # Padre
            self.main_window.study_service, # Pasar StudyService
            self.study_id
        )
        # Esperar a que el diálogo se cierre y luego actualizar la etiqueta de alias
        self.parent.wait_window(dialog) # Espera a que el Toplevel se cierre
        self.update_alias_display() # Actualizar la información mostrada

    def show_vi_descriptor_info(self):
        """Muestra un popup con los sub-valores y alias de cada VI."""
        try:
            study_details = self.main_window.study_service.get_study_details(self.study_id)
            independent_variables = study_details.get('independent_variables', [])
            study_aliases = study_details.get('aliases', {})

            if not independent_variables:
                messagebox.showinfo("Información VIs", "No hay Variable(s) Independientes (VIs) definidas para este estudio.", parent=self.frame)
                return

            info_text = "Variable(s) Independientes (VIs) y sus Sub-valores (Alias):\n\n"
            for iv in independent_variables:
                vi_name = iv.get('name', 'VI Sin Nombre')
                descriptors = iv.get('descriptors', [])
                allows_combination = iv.get('allows_combination', False)
                is_mandatory = iv.get('is_mandatory', False)

                info_text += f"▶ {vi_name}:\n"
                if descriptors:
                    for desc in sorted(descriptors):
                        alias = study_aliases.get(desc)
                        display = f"{desc} ({alias})" if alias else desc
                        info_text += f"    - {display}\n"
                else:
                    info_text += "    (Sin sub-valores definidos)\n"
                
                # Añadir manejo de sub-valores
                if allows_combination:
                    if is_mandatory:
                        info_text += "    Manejo Sub-valores: Múltiple y Obligatorio\n"
                    else:
                        info_text += "    Manejo Sub-valores: Múltiple y No Obligatorio\n"
                else:
                    info_text += "    Manejo Sub-valores: No Múltiple\n"
                info_text += "\n" # Espacio entre VIs

            messagebox.showinfo("Detalle Variable(s) Independientes (VIs)", info_text.strip(), parent=self.frame)

        except Exception as e:
            logger.error(f"Error mostrando información de VIs para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo mostrar la información de las VIs:\n{e}", parent=self.frame)


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

    def show_study_view_help(self):
        """Muestra el archivo de ayuda para la vista de estudio."""
        try:
            # Construir ruta relativa al archivo actual
            help_file_path = Path(__file__).parent.parent.parent / "docs" / "help" / "study_view_help.txt"
            if help_file_path.exists():
                # Usar webbrowser para abrir el archivo (más portable)
                webbrowser.open(help_file_path.as_uri()) # as_uri() para formato file:///
            else:
                messagebox.showerror("Error", f"No se encontró el archivo de ayuda:\n{help_file_path}", parent=self.frame)
        except Exception as e:
            logger.error(f"Error al abrir archivo de ayuda de StudyView: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir el archivo de ayuda:\n{e}", parent=self.frame)
