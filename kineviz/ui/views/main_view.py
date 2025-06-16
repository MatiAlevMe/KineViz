import tkinter as tk
from tkinter import ttk, messagebox
import os # Necesario para verificar existencia de carpetas
import logging # Importar logging
from pathlib import Path # Importar Path
from kineviz.core.services.study_service import MAX_PINNED_STUDIES # Importar la constante

logger = logging.getLogger(__name__) # Logger para este módulo


class MainView:
    """Vista principal que muestra la lista de estudios."""
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window
        self.study_service = main_window.study_service
        # self.config = main_window.config # Ya no es necesario, se accede a través de main_window.settings o propiedades
        self.MAX_PINNED_STUDIES = MAX_PINNED_STUDIES # Usar la constante importada

        # Variables de estado
        self.current_page = 1
        self.search_term = tk.StringVar()
        self.total_pages = 1

        # Crear la interfaz de usuario
        self.frame = ttk.Frame(root, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.create_ui()
        self.load_studies() # Carga inicial

    def create_ui(self):
        """Crea los widgets de la interfaz de usuario."""
        # --- Cabecera ---
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="KineViz", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 20))

        # Botones de acción rápida (derecha)
        action_button_frame = ttk.Frame(header_frame)
        action_button_frame.pack(side=tk.RIGHT)

        ttk.Button(action_button_frame, text='Manual', command=self.main_window.open_user_manual, style="Green.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_button_frame, text='Configuración', command=self.main_window.show_config_dialog).pack(side=tk.RIGHT, padx=5) # Placeholder
        ttk.Button(action_button_frame, text='Ayuda', command=self.main_window.show_welcome_message).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_button_frame, text='Abrir Carpeta Estudios',
                  command=lambda: self.main_window.open_folder("estudios")).pack(side=tk.RIGHT, padx=5)


        # --- Búsqueda ---
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Buscar estudio:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_term)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind("<Return>", lambda event: self.search_studies()) # Buscar al presionar Enter
        ttk.Button(search_frame, text="Buscar", command=self.search_studies).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Limpiar", command=self.clear_search).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(search_frame, text="Refrescar", command=self.load_studies).pack(side=tk.LEFT)

        # --- Tabla de Estudios ---
        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('Pin', 'Nombre', 'Comentar', 'Ver', 'Editar', 'Eliminar') # Añadir 'Comentar'
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', style='Treeview', selectmode="extended")

        # Configurar cabeceras
        self.tree.heading('Pin', text='Pin', anchor='center')
        self.tree.heading('Nombre', text='Nombre del Estudio')
        self.tree.heading('Comentar', text='Comentar', anchor='center') # Cabecera para Comentar
        self.tree.heading('Ver', text='Ver', anchor='center')
        self.tree.heading('Editar', text='Editar', anchor='center')
        self.tree.heading('Eliminar', text='Eliminar', anchor='center')

        # Configurar ancho de columnas (ajustar según necesidad)
        self.tree.column('Pin', width=50, anchor='center', stretch=tk.NO)
        self.tree.column('Nombre', width=300, stretch=tk.YES) # Ajustar ancho de Nombre
        self.tree.column('Comentar', width=90, anchor='center', stretch=tk.NO) # Ancho para Comentar
        self.tree.column('Ver', width=80, anchor='center', stretch=tk.NO)
        self.tree.column('Editar', width=80, anchor='center', stretch=tk.NO)
        self.tree.column('Eliminar', width=80, anchor='center', stretch=tk.NO)

        # Scrollbar vertical
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)

        # Scrollbar horizontal
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew') # Grid the horizontal scrollbar

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Evento de clic en la tabla
        self.tree.bind('<ButtonRelease-1>', self.on_tree_click) # Para acciones de celda
        self.tree.bind('<<TreeviewSelect>>', self._on_selection_change) # Para estado de botón

        # --- Paginación ---
        # --- Botón Crear Nuevo Estudio y otros botones inferiores ---
        # Este frame se empaquetará al final (side=tk.BOTTOM)
        bottom_buttons_frame = ttk.Frame(self.frame)
        bottom_buttons_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.X)

        # Botón Eliminar Todos los Estudios (a la izquierda)
        delete_all_button = ttk.Button(bottom_buttons_frame, text='Eliminar Todos los Estudios',
                                       command=self._confirm_delete_all_studies, style="Danger.TButton")
        delete_all_button.pack(side=tk.LEFT, padx=(0, 5))

        # Botón Eliminar Seleccionado(s)
        self.delete_selected_button = ttk.Button(bottom_buttons_frame, text='Eliminar Seleccionado(s)',
                                                 command=self._confirm_delete_selected_studies, style="Danger.TButton", state=tk.DISABLED)
        self.delete_selected_button.pack(side=tk.LEFT, padx=(0, 10))


        # Configurar estilo para el botón de peligro (opcional, si no existe se usará TButton normal)
        # Esto ya se hace en MainWindow, pero lo dejamos por si acaso o para especificidad.
        try:
            self.main_window.style.configure("Danger.TButton", foreground="white", background="red")
        except tk.TclError: # Si el estilo ya existe o hay otro problema
            logger.warning("No se pudo configurar el estilo Danger.TButton. Usando estilo por defecto.")


        # Botón Crear Nuevo Estudio (a la derecha)
        create_study_button = ttk.Button(bottom_buttons_frame, text='Crear Nuevo Estudio',
                                         command=lambda: self.main_window.show_create_study_dialog(study_to_edit=None), style="Celeste.TButton")
        create_study_button.pack(side=tk.RIGHT)
        
        # --- Paginación (se empaqueta después de los botones inferiores para que quede arriba de ellos) ---
        self.pagination_frame = ttk.Frame(self.frame)
        self.pagination_frame.pack(side=tk.BOTTOM, pady=(5, 0), fill=tk.X) # side=tk.BOTTOM


    def _confirm_delete_selected_studies(self):
        """Muestra confirmación y luego elimina los estudios seleccionados."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "No hay estudios seleccionados para eliminar.", parent=self.root)
            return

        if messagebox.askyesno("Confirmar Eliminación",
                               f"¿Está seguro de que desea eliminar los {len(selected_items)} estudio(s) seleccionados?\n"
                               "Esta acción también eliminará sus carpetas y todos los archivos asociados.",
                               icon='warning', parent=self.root):
            study_ids_to_delete = []
            for item_id in selected_items:
                item_tags = self.tree.item(item_id, "tags")
                if item_tags:
                    study_ids_to_delete.append(int(item_tags[0]))
            
            if not study_ids_to_delete:
                messagebox.showerror("Error", "No se pudieron obtener los IDs de los estudios seleccionados.", parent=self.root)
                return

            try:
                # Asumiendo que study_service tendrá un método para eliminar múltiples estudios
                self.study_service.delete_studies_by_ids(study_ids_to_delete)
                messagebox.showinfo("Éxito", f"{len(study_ids_to_delete)} estudio(s) eliminado(s) correctamente.", parent=self.root)
                self.load_studies() # Recargar la lista
                if not self.study_service.has_studies():
                    self.main_window.show_landing_page()
            except Exception as e:
                logger.error(f"Error al eliminar estudios seleccionados: {e}", exc_info=True)
                messagebox.showerror("Error al Eliminar", f"No se pudieron eliminar los estudios seleccionados:\n{e}", parent=self.root)

    def _confirm_delete_all_studies(self):
        """
        Llama al método de MainWindow para confirmar y eliminar todos los estudios.
        """
        self.main_window.confirm_delete_all_studies()


    def load_studies(self):
        """Carga los estudios desde el servicio y los muestra en la tabla."""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Obtener estudios paginados y filtrados
            studies_per_page = self.main_window.estudios_por_pagina
            search_query = self.search_term.get() if self.search_term.get() else None

            studies = self.study_service.get_studies_paginated(
                page=self.current_page,
                per_page=studies_per_page,
                search_term=search_query
            )
            total_studies = self.study_service.get_total_studies_count(search_term=search_query)
            self.total_pages = (total_studies // studies_per_page) + (1 if total_studies % studies_per_page else 0)
            self.total_pages = max(1, self.total_pages) # Asegurar al menos 1 página

            # Llenar tabla
            for study in studies:
                # Verificar si la carpeta del estudio existe (opcional pero bueno para consistencia)
                study_folder_path = Path("estudios") / study['name']
                if not study_folder_path.exists():
                    logger.warning(f"Carpeta no encontrada para el estudio '{study['name']}' (ID: {study['id']}). El registro puede estar desincronizado.")
                    # Podríamos eliminar el estudio aquí o marcarlo visualmente
                    # self.study_service.delete_study(study['id']) # ¡Cuidado con esto!
                    # continue # Omitir estudio sin carpeta
                
                pin_char = "📌" if study.get('is_pinned') else ""

                self.tree.insert('', tk.END, values=(
                    pin_char,
                    study['name'],
                    'Comentar', # Texto para el botón Comentar
                    'Ver',      # Texto para el botón Ver
                    'Editar',   # Texto para el botón Editar
                    'Eliminar'  # Texto para el botón Eliminar
                ), tags=(str(study['id']), study['name'], str(study.get('is_pinned', 0)))) # Guardar ID, nombre y estado de pin

            self.update_pagination_controls()

        except Exception as e:
            logger.error(f"Error al cargar estudios: {e}", exc_info=True)
            messagebox.showerror("Error al Cargar Estudios", f"No se pudieron cargar los estudios:\n{e}", parent=self.root)
            # import traceback # Ya no es necesario
            # traceback.print_exc() # Reemplazado por logger

    def update_pagination_controls(self):
        """Actualiza los botones de paginación."""
        # Limpiar controles existentes
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()

        if self.total_pages <= 1:
            return # No mostrar controles si hay 1 página o menos

        # Botón Primera Página
        first_btn = ttk.Button(self.pagination_frame, text="<<", command=lambda: self.go_to_page(1))
        first_btn.pack(side=tk.LEFT, padx=2)
        if self.current_page == 1:
            first_btn.config(state=tk.DISABLED)

        # Botón Anterior
        prev_btn = ttk.Button(self.pagination_frame, text="<", command=lambda: self.go_to_page(self.current_page - 1))
        prev_btn.pack(side=tk.LEFT, padx=2)
        if self.current_page == 1:
            prev_btn.config(state=tk.DISABLED)

        # Etiqueta de Página Actual
        ttk.Label(self.pagination_frame, text=f"Página {self.current_page} de {self.total_pages}").pack(side=tk.LEFT, padx=5)

        # Botón Siguiente
        next_btn = ttk.Button(self.pagination_frame, text=">", command=lambda: self.go_to_page(self.current_page + 1))
        next_btn.pack(side=tk.LEFT, padx=2)
        if self.current_page == self.total_pages:
            next_btn.config(state=tk.DISABLED)

        # Botón Última Página
        last_btn = ttk.Button(self.pagination_frame, text=">>", command=lambda: self.go_to_page(self.total_pages))
        last_btn.pack(side=tk.LEFT, padx=2)
        if self.current_page == self.total_pages:
            last_btn.config(state=tk.DISABLED)

        # Botón de ayuda para la vista principal
        # El estilo "Help.TButton" ahora se define globalmente en MainWindow.
        main_view_help_button = ttk.Button(self.pagination_frame, text="?", width=3,
                                           style="Help.TButton", command=self._show_main_view_help)
        main_view_help_button.pack(side=tk.LEFT, padx=(10, 2))

    def _show_main_view_help(self):
        """Muestra un popup de ayuda para la Vista Principal."""
        help_title = "Ayuda: Ventana Principal de Estudios"
        help_message = (
            "Esta ventana muestra una lista de todos los estudios creados.\n\n"
            "Funcionalidades:\n"
            "- Buscar estudios por su nombre.\n"
            "- Añadir/editar un comentario para un estudio haciendo clic en 'Comentar'.\n"
            "- Ver detalles de un estudio haciendo clic en 'Ver'.\n"
            "- Editar un estudio haciendo clic en 'Editar'.\n"
            "- Eliminar un estudio haciendo clic en 'Eliminar'.\n"
            "- Destacar hasta 5 estudios usando el icono '📌' para que aparezcan siempre al inicio de la lista.\n"
            "- Navegar entre páginas de estudios si hay muchos.\n"
            "- Crear un nuevo estudio usando el botón 'Crear Nuevo Estudio'.\n"
            "- Eliminar TODOS los estudios existentes usando el botón 'Eliminar Todos los Estudios' (¡con precaución!).\n"
            "- Eliminar estudios SELECCIONADOS usando el botón 'Eliminar Seleccionado(s)' (¡con precaución!)."
        )
        messagebox.showinfo(help_title, help_message, parent=self.root)

    def go_to_page(self, page_number):
        """Navega a una página específica."""
        if 1 <= page_number <= self.total_pages:
            self.current_page = page_number
            self.load_studies()
        else:
            logger.warning(f"Intento de ir a página inválida {page_number} (Total: {self.total_pages})")

    def search_studies(self):
        """Filtra los estudios basados en el término de búsqueda."""
        self.current_page = 1 # Resetear a la primera página al buscar
        self.load_studies()
        self._on_selection_change() # Actualizar estado del botón

    def clear_search(self):
        """Limpia el campo de búsqueda y recarga todos los estudios."""
        self.search_term.set("")
        self.current_page = 1
        self.load_studies()
        self._on_selection_change() # Actualizar estado del botón

    def _on_selection_change(self, event=None):
        """Actualiza el estado del botón 'Eliminar Seleccionado(s)'."""
        if self.tree.selection():
            self.delete_selected_button.config(state=tk.NORMAL)
        else:
            self.delete_selected_button.config(state=tk.DISABLED)

    def on_tree_click(self, event):
        """Maneja los clics en la tabla de estudios."""
        # Si hay múltiples selecciones, no procesar clics de celda individuales
        # para evitar acciones conflictivas.
        if len(self.tree.selection()) > 1:
            return

        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column_id = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)

        if not row_id: # Clic fuera de las filas
            return

        item_tags = self.tree.item(row_id, "tags")
        if not item_tags:
            return # No hay tags (inesperado)

        study_id = int(item_tags[0])
        study_name = item_tags[1] # Nombre guardado en el segundo tag

        # Determinar la acción basada en la columna clickeada
        column_index = int(column_id.replace('#', '')) - 1 # Índice basado en 0

        if column_index == 0: # Columna "Pin"
            logger.debug(f"Acción 'Pin' para estudio ID {study_id}")
            self.toggle_pin_study(study_id)
        elif column_index == 1: # Columna "Nombre" - sin acción directa
            pass
        elif column_index == 2: # Columna "Comentar"
            logger.debug(f"Acción 'Comentar' para estudio ID {study_id}")
            self.main_window.show_comment_dialog(study_id, study_name)
        elif column_index == 3: # Columna "Ver"
            logger.debug(f"Acción 'Ver' para estudio ID {study_id}")
            self.main_window.show_study_view(study_id)
        elif column_index == 4: # Columna "Editar"
            logger.debug(f"Acción 'Editar' para estudio ID {study_id}")
            study_details = {'id': study_id, 'name': study_name}
            self.main_window.show_create_study_dialog(study_to_edit=study_details)
        elif column_index == 5: # Columna "Eliminar"
            logger.debug(f"Acción 'Eliminar' para estudio ID {study_id}")
            self.delete_study(study_id, study_name)

    def toggle_pin_study(self, study_id: int):
        """Alterna el estado de pin de un estudio."""
        try:
            success = self.study_service.toggle_study_pin_status(study_id)
            if success:
                logger.info(f"Estado de pin para estudio {study_id} cambiado.")
                self.load_studies() # Recargar para reflejar el cambio y el orden
            else:
                messagebox.showwarning("Límite Alcanzado",
                                       f"No se pudo destacar el estudio. Ya hay {self.MAX_PINNED_STUDIES} estudios destacados.",
                                       parent=self.root)
        except ValueError as ve: # Estudio no encontrado
            logger.error(f"Error al cambiar pin para estudio {study_id}: {ve}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo encontrar el estudio para cambiar su estado de pin:\n{ve}", parent=self.root)
        except RuntimeError as re: # Error general del servicio
            logger.error(f"Error de servicio al cambiar pin para estudio {study_id}: {re}", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error al cambiar el estado de pin del estudio:\n{re}", parent=self.root)
        except Exception as e:
            logger.error(f"Error inesperado al cambiar pin para estudio {study_id}: {e}", exc_info=True)
            messagebox.showerror("Error Inesperado", f"Ocurrió un error inesperado:\n{e}", parent=self.root)


    def delete_study(self, study_id, study_name):
        """Solicita confirmación y elimina un estudio."""
        if messagebox.askyesno("Confirmar Eliminación",
                               f"¿Está seguro de que desea eliminar el estudio '{study_name}'?\n"
                               "Esta acción también eliminará su carpeta y todos los archivos asociados.",
                               icon='warning', parent=self.root):
            try:
                self.study_service.delete_study(study_id)
                messagebox.showinfo("Éxito", f"Estudio '{study_name}' eliminado correctamente.", parent=self.root)
                self.load_studies() # Recargar la lista
                # Si después de eliminar no quedan estudios, ir a landing page
                if not self.study_service.has_studies():
                    self.main_window.show_landing_page()
            except Exception as e:
                logger.error(f"Error al eliminar estudio ID {study_id} ('{study_name}'): {e}", exc_info=True)
                messagebox.showerror("Error al Eliminar", f"No se pudo eliminar el estudio:\n{e}", parent=self.root)
                # import traceback # Ya no es necesario
                # traceback.print_exc() # Reemplazado por logger

    def destroy(self):
        """Destruye el frame principal de esta vista."""
        if self.frame:
            self.frame.destroy()
            self.frame = None
