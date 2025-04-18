import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import subprocess
import sys
import math  # Para ceil en paginación
from pathlib import Path
from datetime import datetime
from kineviz.core.services.analysis_service import AnalysisService
# Importar AppSettings para leer configuración
from kineviz.config.settings import AppSettings


logger = logging.getLogger(__name__)


class DiscreteAnalysisView(ttk.Frame):
    """Vista para gestionar y visualizar el análisis discreto (Fase 6)."""

    def __init__(self, parent, main_window,
                 analysis_service: AnalysisService, study_id: int):
        super().__init__(parent)
        self.parent = parent
        self.main_window = main_window
        self.analysis_service = analysis_service
        self.study_id = study_id
        self.settings = AppSettings()  # Cargar configuración
        self.tables_per_page = self.settings.discrete_tables_per_page

        # Estado de UI y datos
        self.tables_tree = None
        # Lista completa de dicts:
        # {'path': Path, 'name': str, 'calc': str, 'desc': str,
        #  'mtime': float, 'size': int}
        self.all_table_files = []
        self.current_page = 1
        self.total_tables = 0
        self.total_pages = 1

        # Variables de control para filtros y búsqueda
        self.search_var = tk.StringVar()
        self.calc_filter_var = tk.StringVar()

        # Empaquetar el frame principal
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_widgets()
        self.load_tables()  # Carga inicial de tablas

    def create_widgets(self):
        """Crea los widgets para la vista de análisis discreto."""

        # --- Cabecera ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Botón Volver
        ttk.Button(
            header_frame, text="<< Volver al Estudio",
            command=lambda: self.main_window.show_study_view(self.study_id)
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(
            header_frame, text=f"Análisis Discreto - Estudio {self.study_id}",
            style='Header.TLabel'
        ).pack(side=tk.LEFT, padx=(0, 20))

        # --- Acciones ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            action_frame, text="Generar/Actualizar Tablas Resumen",
            command=self.generate_tables
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame, text="Análisis Individual",
            command=self.open_individual_analysis_manager
        ).pack(side=tk.LEFT, padx=5)

        # TODO: Añadir botón "Reporte General" (Fase 6)

        # TODO: Añadir botón "Abrir Carpeta de Tablas"
        # ttk.Button(
        #     action_frame, text="Abrir Carpeta de Tablas Resumen",
        #     command=self.open_summary_tables_folder
        # ).pack(side=tk.LEFT, padx=5)

        # --- Filtros y Búsqueda ---
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, pady=(5, 5))

        ttk.Label(filter_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var,
                                 width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<Return>", self.search_tables)  # Buscar con Enter

        ttk.Button(filter_frame, text="Buscar",
                   command=self.search_tables).pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="Cálculo:").pack(side=tk.LEFT,
                                                     padx=(10, 5))
        self.calc_filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.calc_filter_var,
            values=["Todos", "Maximo", "Minimo", "Rango"],
            state="readonly", width=10
        )
        self.calc_filter_combo.set("Todos")
        self.calc_filter_combo.pack(side=tk.LEFT, padx=5)
        self.calc_filter_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        ttk.Button(filter_frame, text="Limpiar Filtros",
                   command=self.clear_filters).pack(side=tk.LEFT, padx=10)

        # --- Lista de Tablas Generadas (Treeview) ---
        list_frame = ttk.LabelFrame(self, text="Tablas Generadas")
        # Reducir padding inferior
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        list_frame.columnconfigure(0, weight=1)  # Treeview se expande
        list_frame.rowconfigure(0, weight=1)     # Treeview se expande

        # Crear Treeview con nuevas columnas
        self.tables_tree = ttk.Treeview(
            list_frame,
            columns=("Nombre Archivo", "Tipo Cálculo", "Descriptores",
                     "Fecha Modificación", "Tamaño"),
            show="headings"
        )
        # Reducir padding inferior
        self.tables_tree.grid(row=0, column=0, sticky='nsew', padx=5, pady=(5, 0))

        # Definir cabeceras y comando de ordenación
        cols = ("Nombre Archivo", "Tipo Cálculo", "Descriptores",
                "Fecha Modificación", "Tamaño")
        for col in cols:
            self.tables_tree.heading(
                col, text=col,
                command=lambda c=col: self.sort_column(c, False)
            )

        # Definir ancho de columnas
        self.tables_tree.column("Nombre Archivo", width=250, anchor=tk.W)
        self.tables_tree.column("Tipo Cálculo", width=100, anchor=tk.W)
        self.tables_tree.column("Descriptores", width=200, anchor=tk.W)
        self.tables_tree.column("Fecha Modificación", width=150,
                                anchor=tk.CENTER)
        self.tables_tree.column("Tamaño", width=100, anchor=tk.E)

        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.tables_tree.yview)
        vsb.grid(row=0, column=1, sticky='ns', pady=(5, 0))
        self.tables_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(list_frame, orient="horizontal",
                            command=self.tables_tree.xview)
        hsb.grid(row=1, column=0, sticky='ew', padx=5)
        self.tables_tree.configure(xscrollcommand=hsb.set)

        # --- Controles de Paginación ---
        pagination_frame = ttk.Frame(list_frame)
        # Añadir padding inferior
        pagination_frame.grid(row=2, column=0, columnspan=2, sticky='ew',
                              pady=(5, 5))

        self.prev_button = ttk.Button(
            pagination_frame, text="<< Anterior",
            command=lambda: self.go_to_page(self.current_page - 1),
            state=tk.DISABLED
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.page_label = ttk.Label(pagination_frame, text="Página 1 de 1")
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(
            pagination_frame, text="Siguiente >>",
            command=lambda: self.go_to_page(self.current_page + 1),
            state=tk.DISABLED
        )
        self.next_button.pack(side=tk.LEFT, padx=5)

        # --- Botones de Acción para Tablas ---
        table_action_frame = ttk.Frame(list_frame)
        # Mover abajo, añadir padding inferior
        table_action_frame.grid(row=3, column=0, columnspan=2, sticky='ew',
                                pady=(0, 5))

        # Quitar botón Refrescar
        # ttk.Button(table_action_frame, text="Refrescar Lista",
        #            command=self.load_tables).pack(side=tk.LEFT, padx=5)
        ttk.Button(table_action_frame, text="Ver Tabla",
                   command=self.view_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(table_action_frame, text="Eliminar Tabla",
                   command=self.delete_table).pack(side=tk.LEFT, padx=5)

    def generate_tables(self):
        """Llama al servicio para generar las tablas resumen CSV."""
        logger.info(f"Solicitando generación de tablas discretas para estudio "
                    f"{self.study_id}")
        try:
            # TODO: Mostrar un mensaje de "procesando"
            results = self.analysis_service.generate_discrete_summary_tables(
                self.study_id
            )

            success_count = len(results.get('success', []))
            error_count = len(results.get('errors', []))

            message = "Generación de tablas completada.\n\n"
            message += f"Tablas generadas/actualizadas: {success_count}\n"
            if error_count > 0:
                message += f"Errores encontrados: {error_count}\n\n"
                message += "Errores detallados:\n"
                # Mostrar hasta 5 errores
                message += "\n".join([f"- {err}" for err in
                                      results['errors'][:5]])
                if error_count > 5:
                    message += f"\n... y {error_count - 5} más (ver logs)."
                messagebox.showwarning("Resultado Generación", message,
                                       parent=self)
            else:
                messagebox.showinfo("Resultado Generación", message, parent=self)

            # Refrescar la lista de tablas después de mostrar el mensaje
            self.load_tables()

        except Exception as e:
            logger.critical("Error crítico al llamar a "
                            f"generate_discrete_summary_tables: {e}",
                            exc_info=True)
            messagebox.showerror(
                "Error Crítico",
                f"Ocurrió un error inesperado al generar las tablas:\n{e}",
                parent=self)

    def _format_size(self, size_bytes):
        """Formatea el tamaño en bytes a KB, MB, etc."""
        if not isinstance(size_bytes, (int, float)) or size_bytes < 0:
            return "N/A"
        if size_bytes == 0:
            return "0 B"
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes / (1024**2):.1f} MB"
        else:
            return f"{size_bytes / (1024**3):.1f} GB"

    def _parse_table_filename(self, filename: str) -> tuple[str, str, str]:
        """Extrae Cálculo, Frecuencia y Descriptores del nombre de archivo."""
        # Formato: CALCULO_FRECUENCIA_DESC1_DESC2...DESCn.csv
        parts = filename.removesuffix('.csv').split('_')
        if len(parts) < 2:
            return "Desconocido", "Desconocido", ""  # No se puede determinar

        calc_type = parts[0]
        # Asumimos que siempre está presente después del cálculo
        freq_type = parts[1]
        descriptors = parts[2:]  # El resto son descriptores

        # Unir descriptores con coma
        descriptor_str = ", ".join(descriptors) if descriptors \
                                                else "SinDescriptores"

        return calc_type, freq_type, descriptor_str

    def _fetch_all_table_files(self):
        """Obtiene la lista completa de archivos CSV de tablas y sus metadatos."""
        self.all_table_files = []
        try:
            tables_path = self.analysis_service.get_discrete_analysis_tables_path(
                self.study_id
            )
            if not tables_path or not tables_path.exists() \
               or not tables_path.is_dir():
                logger.info("Directorio de tablas discretas no encontrado "
                            f"para estudio {self.study_id}: {tables_path}")
                return

            for freq_dir in tables_path.iterdir():
                if freq_dir.is_dir():
                    for file_path in freq_dir.glob("*.csv"):
                        if file_path.is_file():
                            try:
                                stats = file_path.stat()
                                calc_type, _, descriptor_str = \
                                    self._parse_table_filename(file_path.name)
                                self.all_table_files.append({
                                    'path': file_path,
                                    'name': file_path.name,
                                    'calc': calc_type,
                                    'desc': descriptor_str,
                                    'mtime': stats.st_mtime,
                                    'size': stats.st_size
                                })
                            except Exception as e_file:
                                logger.error("Error procesando metadatos de "
                                             f"{file_path}: {e_file}",
                                             exc_info=True)

        except Exception as e:
            logger.error("Error buscando archivos de tablas discretas para "
                         f"estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error",
                                   f"No se pudo buscar la lista de tablas:\n{e}",
                                   parent=self)

    def load_tables(self):
        """Filtra, ordena y muestra la página actual de tablas."""
        if not self.tables_tree:
            logger.warning("El Treeview de tablas aún no está inicializado.")
            return

        # 1. Obtener lista completa si es necesario
        # Se llama al inicio y después de eliminar/generar
        self._fetch_all_table_files() # Siempre refrescar la lista completa

        # 2. Aplicar Filtros y Búsqueda
        search_term = self.search_var.get().lower()
        selected_calc = self.calc_filter_var.get()

        filtered_files = self.all_table_files

        # Filtrar por cálculo
        if selected_calc != "Todos":
            filtered_files = [f for f in filtered_files
                              if f['calc'] == selected_calc]

        # Filtrar por término de búsqueda (nombre, cálculo, descriptores)
        if search_term:
            filtered_files = [
                f for f in filtered_files if (
                    search_term in f['name'].lower() or
                    search_term in f['calc'].lower() or
                    search_term in f['desc'].lower()
                )
            ]

        # 3. Ordenar (Implementación básica)
        # Por defecto, ordenar por fecha de modificación descendente
        # TODO: Implementar ordenación por columna clickeada
        filtered_files.sort(key=lambda x: x['mtime'], reverse=True)

        # 4. Calcular Paginación
        self.total_tables = len(filtered_files)
        # Recargar por si cambió en config.ini
        self.tables_per_page = self.settings.discrete_tables_per_page
        if self.tables_per_page > 0:
            self.total_pages = math.ceil(self.total_tables /
                                         self.tables_per_page)
        else:
            self.total_pages = 1
        self.total_pages = max(1, self.total_pages)  # Asegurar al menos 1

        # Ajustar página actual si está fuera de rango
        self.current_page = max(1, min(self.current_page, self.total_pages))

        # 5. Obtener la porción para la página actual
        start_index = (self.current_page - 1) * self.tables_per_page
        end_index = start_index + self.tables_per_page
        page_files = filtered_files[start_index:end_index]

        # 6. Limpiar y Poblar Treeview
        for item in self.tables_tree.get_children():
            self.tables_tree.delete(item)

        if not page_files and self.total_tables > 0:
            # Si no hay archivos en esta página pero sí hay en total
            # (p.ej. página inválida), simplemente dejar vacío.
            pass
        elif not page_files and self.total_tables == 0:
            # Mostrar mensaje si no hay tablas en absoluto (después de filtrar)
            self.tables_tree.insert(
                "", tk.END, text="NoMatch",
                values=("No se encontraron tablas que coincidan.", "", "", "", ""))
        else:
            for file_info in page_files:
                mod_time_str = datetime.fromtimestamp(
                    file_info['mtime']
                ).strftime('%Y-%m-%d %H:%M:%S')
                size_str = self._format_size(file_info['size'])

                # Insertar en Treeview, usando la ruta como ID interno (text)
                self.tables_tree.insert(
                    "", tk.END,
                    text=str(file_info['path']),  # Guardar ruta completa aquí
                    values=(
                        file_info['name'],
                        file_info['calc'],
                        file_info['desc'],
                        mod_time_str,
                        size_str
                    )
                )

        # 7. Actualizar Controles de Paginación
        self.update_pagination_controls()

    def update_pagination_controls(self):
        """Actualiza el estado y texto de los controles de paginación."""
        if not hasattr(self, 'page_label'):
            return  # Si aún no se crearon los widgets

        page_info = (f"Página {self.current_page} de {self.total_pages} "
                     f"({self.total_tables} tablas)")
        self.page_label.config(text=page_info)

        self.prev_button.config(
            state=tk.DISABLED if self.current_page <= 1 else tk.NORMAL
        )
        self.next_button.config(
            state=tk.DISABLED if self.current_page >= self.total_pages
            else tk.NORMAL)

    def go_to_page(self, page_number):
        """Navega a una página específica."""
        if 1 <= page_number <= self.total_pages:
            self.current_page = page_number
            self.load_tables()
        else:
            logger.warning(f"Intento de ir a página inválida: {page_number}")

    def search_tables(self, event=None):  # Aceptar event para bind <Return>
        """Inicia la búsqueda y recarga la tabla."""
        self.current_page = 1  # Volver a la primera página al buscar
        self.load_tables()

    def apply_filters(self, event=None):  # Aceptar event para bind Combobox
        """Aplica los filtros seleccionados y recarga la tabla."""
        self.current_page = 1  # Volver a la primera página al filtrar
        self.load_tables()

    def clear_filters(self):
        """Limpia los filtros y la búsqueda, y recarga la tabla."""
        self.search_var.set("")
        self.calc_filter_var.set("Todos")
        self.current_page = 1
        # No es necesario _fetch_all_table_files aquí, load_tables lo hará
        self.load_tables()

    # TODO: Implementar sort_column si se desea ordenar al hacer clic
    def sort_column(self, col, reverse):
        """Ordena el Treeview por la columna especificada."""
        # Esta implementación requiere guardar los datos mostrados o re-ordenar
        # self.all_table_files y luego llamar a load_tables.
        # Por simplicidad, se omite por ahora.
        logger.info(f"Ordenar por {col}, reverso={reverse}. "
                    "(Funcionalidad no implementada)")
        pass

    def view_table(self):
        """Abre la tabla CSV seleccionada con la aplicación predeterminada."""
        selected_item = self.tables_tree.focus()  # Obtiene IID del item
        if not selected_item:
            messagebox.showwarning("Sin Selección",
                                   "Seleccione una tabla para ver.",
                                   parent=self)
            return

        # Recuperar la ruta completa guardada como 'text' en el item
        file_path_str = self.tables_tree.item(selected_item, "text")
        # Verificar si es el mensaje "No se encontraron..."
        if not file_path_str or file_path_str == "NoMatch":
            messagebox.showwarning("Sin Selección",
                                   "No hay una tabla válida seleccionada.",
                                   parent=self)
            return

        file_path = Path(file_path_str)

        if not file_path.exists():
            messagebox.showerror("Error",
                                   f"El archivo ya no existe:\n{file_path}",
                                   parent=self)
            self.load_tables()  # Refrescar lista
            return

        try:
            logger.info(f"Intentando abrir archivo: {file_path}")
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", file_path], check=True)
            else:  # linux variants
                subprocess.run(["xdg-open", file_path], check=True)
        except FileNotFoundError:
            # Este caso ya se verifica arriba, pero por si acaso
            messagebox.showerror("Error",
                                   f"No se pudo encontrar el archivo:\n{file_path}",
                                   parent=self)
        except OSError as e:
            logger.error("Error del sistema operativo al intentar abrir "
                         f"{file_path}: {e}", exc_info=True)
            messagebox.showerror(
                "Error al Abrir",
                "No se pudo abrir el archivo con la aplicación "
                f"predeterminada.\nError: {e}", parent=self)
        except subprocess.CalledProcessError as e:
            logger.error("Error al ejecutar comando para abrir "
                         f"{file_path}: {e}", exc_info=True)
            messagebox.showerror(
                "Error al Abrir",
                f"El comando para abrir el archivo falló.\nError: {e}",
                parent=self)
        except Exception as e:
            logger.error(f"Error inesperado al abrir {file_path}: {e}",
                         exc_info=True)
            messagebox.showerror(
                "Error Inesperado",
                "Ocurrió un error inesperado al intentar abrir el "
                f"archivo:\n{e}", parent=self)

    def delete_table(self):
        """Elimina la tabla CSV seleccionada."""
        selected_item = self.tables_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección",
                                   "Seleccione una tabla para eliminar.",
                                   parent=self)
            return

        file_path_str = self.tables_tree.item(selected_item, "text")
        if not file_path_str or file_path_str == "NoMatch":
            messagebox.showwarning("Sin Selección",
                                   "No hay una tabla válida seleccionada.",
                                   parent=self)
            return

        file_path = Path(file_path_str)
        file_name = file_path.name

        if not messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Está seguro de que desea eliminar permanentemente la tabla "
                f"'{file_name}'?", parent=self):
            return

        try:
            self.analysis_service.delete_discrete_summary_table(str(file_path))
            messagebox.showinfo("Eliminación Exitosa",
                                f"La tabla '{file_name}' ha sido eliminada.",
                                parent=self)
            # Eliminar de la lista en memoria y recargar la vista actual
            self.all_table_files = [f for f in self.all_table_files
                                    if f['path'] != file_path]
            # Recalculará paginación y mostrará página actual
            self.load_tables()
        except FileNotFoundError:
            messagebox.showerror("Error",
                                   f"El archivo ya no existe:\n{file_path}",
                                   parent=self)
            # Eliminar de la lista en memoria y recargar
            self.all_table_files = [f for f in self.all_table_files
                                    if f['path'] != file_path]
            self.load_tables()
        except (OSError, ValueError) as e:
            logger.error(f"Error al eliminar la tabla {file_path}: {e}",
                         exc_info=True)
            messagebox.showerror(
                "Error al Eliminar",
                f"No se pudo eliminar la tabla '{file_name}'.\nError: {e}",
                parent=self)
        except Exception as e:
            logger.error(f"Error inesperado al eliminar {file_path}: {e}",
                         exc_info=True)
            messagebox.showerror(
                "Error Inesperado",
                "Ocurrió un error inesperado al eliminar la tabla:\n{e}",
                parent=self)

    def open_individual_analysis_manager(self):
        """Abre el diálogo para gestionar análisis individuales."""
        # Import local para evitar dependencia circular si es necesario
        from kineviz.ui.dialogs.individual_analysis_manager_dialog \
            import IndividualAnalysisManagerDialog
        # Pasar self.analysis_service y self.study_id
        _dialog = IndividualAnalysisManagerDialog(self, self.analysis_service,
                                                  self.study_id)
        # _dialog.grab_set()  # Hacer modal si se desea
        # Se usa _dialog para evitar F841, aunque no se use después

    # TODO: Implementar open_summary_tables_folder
    # def open_summary_tables_folder(self): ...

    def destroy(self):
        """Destruye el frame principal de esta vista."""
        super().destroy()
# Eliminado bloque redundante de update_pagination_controls y métodos siguientes
# ya que se corrigieron en el bloque anterior.
