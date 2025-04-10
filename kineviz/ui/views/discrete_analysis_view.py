import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from kineviz.core.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class DiscreteAnalysisView(ttk.Frame):
    """Vista para gestionar y visualizar el análisis discreto (Fase 6)."""

    def __init__(self, parent, main_window, analysis_service: AnalysisService, study_id: int):
        super().__init__(parent)
        self.parent = parent
        self.main_window = main_window
        self.analysis_service = analysis_service
        self.study_id = study_id
        self.tables_tree = None # Placeholder for the Treeview

        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10) # Empaquetar el frame principal

        self.create_widgets()
        self.load_tables() # Carga inicial de tablas

    def create_widgets(self):
        """Crea los widgets para la vista de análisis discreto."""

        # --- Cabecera ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Botón Volver a la vista del estudio
        ttk.Button(header_frame, text="<< Volver al Estudio",
                   command=lambda: self.main_window.show_study_view(self.study_id)).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(header_frame, text=f"Análisis Discreto - Estudio {self.study_id}", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 20))

        # --- Acciones ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(action_frame, text="Generar/Actualizar Tablas Resumen (Cinemática)",
                   command=self.generate_tables).pack(side=tk.LEFT, padx=5)

        # Botón para abrir carpeta (se implementará después)
        # ttk.Button(action_frame, text="Abrir Carpeta de Tablas",
        #            command=self.open_tables_folder).pack(side=tk.LEFT, padx=5)

        # --- Placeholder para la lista de tablas ---
        # --- Lista de Tablas Generadas ---
        list_frame = ttk.LabelFrame(self, text="Tablas Generadas")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        list_frame.columnconfigure(0, weight=1) # Hacer que el Treeview se expanda horizontalmente
        list_frame.rowconfigure(0, weight=1)    # Hacer que el Treeview se expanda verticalmente

        # Crear Treeview
        self.tables_tree = ttk.Treeview(
            list_frame,
            columns=("Tipo", "Fecha Modificación", "Tamaño"),
            show="headings" # No mostrar la columna fantasma #0
        )
        self.tables_tree.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Definir cabeceras
        self.tables_tree.heading("Tipo", text="Tipo Cálculo")
        self.tables_tree.heading("Fecha Modificación", text="Fecha Modificación")
        self.tables_tree.heading("Tamaño", text="Tamaño")

        # Definir ancho de columnas (ajustar según necesidad)
        self.tables_tree.column("Tipo", width=150, anchor=tk.W)
        self.tables_tree.column("Fecha Modificación", width=150, anchor=tk.CENTER)
        self.tables_tree.column("Tamaño", width=100, anchor=tk.E)

        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tables_tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        self.tables_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tables_tree.xview)
        hsb.grid(row=1, column=0, sticky='ew')
        self.tables_tree.configure(xscrollcommand=hsb.set)

        # --- Botones de Acción para Tablas ---
        table_action_frame = ttk.Frame(list_frame)
        table_action_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(5, 0))

        ttk.Button(table_action_frame, text="Refrescar Lista", command=self.load_tables).pack(side=tk.LEFT, padx=5)
        ttk.Button(table_action_frame, text="Ver Tabla", command=self.view_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(table_action_frame, text="Eliminar Tabla", command=self.delete_table).pack(side=tk.LEFT, padx=5)

    def generate_tables(self):
        """Llama al servicio para generar las tablas resumen CSV."""
        logger.info(f"Solicitando generación de tablas discretas para estudio {self.study_id}")
        try:
            # Mostrar un mensaje de "procesando" podría ser útil aquí
            results = self.analysis_service.generate_discrete_summary_tables(self.study_id)

            success_count = len(results.get('success', []))
            error_count = len(results.get('errors', []))

            message = f"Generación de tablas completada.\n\n"
            message += f"Tablas generadas/actualizadas: {success_count}\n"
            if error_count > 0:
                message += f"Errores encontrados: {error_count}\n\n"
                message += "Errores detallados:\n"
                message += "\n".join([f"- {err}" for err in results['errors'][:5]]) # Mostrar hasta 5 errores
                if error_count > 5:
                    message += f"\n... y {error_count - 5} más (ver logs)."
                messagebox.showwarning("Resultado Generación", message, parent=self)
            else:
                messagebox.showinfo("Resultado Generación", message, parent=self)

            # Refrescar la lista de tablas
            self.load_tables()

        except Exception as e:
            logger.critical(f"Error crítico al llamar a generate_discrete_summary_tables: {e}", exc_info=True)
            messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado al generar las tablas:\n{e}", parent=self)

    def _format_size(self, size_bytes):
        """Formatea el tamaño en bytes a KB, MB, etc."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes / (1024**2):.1f} MB"
        else:
            return f"{size_bytes / (1024**3):.1f} GB"

    def load_tables(self):
        """Carga la lista de tablas CSV generadas en el Treeview."""
        if not self.tables_tree:
            logger.warning("El Treeview de tablas aún no está inicializado.")
            return

        # Limpiar Treeview
        for item in self.tables_tree.get_children():
            self.tables_tree.delete(item)

        try:
            tables_path = self.analysis_service.get_discrete_analysis_tables_path(self.study_id)
            if not tables_path or not tables_path.exists() or not tables_path.is_dir():
                logger.info(f"Directorio de tablas discretas no encontrado o no es un directorio para estudio {self.study_id}: {tables_path}")
                # Opcional: Mostrar mensaje en la UI
                # self.tables_tree.insert("", tk.END, text="Directorio no encontrado", values=("", "", ""))
                return

            found_files = False
            # Iterar sobre subdirectorios (frecuencias) y luego archivos CSV
            for freq_dir in tables_path.iterdir():
                if freq_dir.is_dir():
                    for file_path in freq_dir.glob("*.csv"):
                        if file_path.is_file():
                            try:
                                stats = file_path.stat()
                                mod_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                                size = self._format_size(stats.st_size)
                                # Extraer tipo de cálculo del nombre (ej: Maximo_Cinematica_Desc1.csv -> Maximo)
                                parts = file_path.name.split('_')
                                calc_type = parts[0] if parts else "Desconocido"

                                # Insertar en Treeview, guardando la ruta completa en 'text' (no visible)
                                self.tables_tree.insert(
                                    "", tk.END,
                                    text=str(file_path), # Guardar ruta completa aquí
                                    values=(calc_type, mod_time, size),
                                    tags=(str(file_path),) # Usar ruta como tag para identificación
                                )
                                found_files = True
                            except Exception as e_file:
                                logger.error(f"Error procesando archivo de tabla {file_path}: {e_file}", exc_info=True)

            if not found_files:
                 logger.info(f"No se encontraron archivos CSV en {tables_path} o sus subdirectorios.")
                 # Opcional: Mostrar mensaje
                 # self.tables_tree.insert("", tk.END, text="No hay tablas generadas", values=("", "", ""))

        except Exception as e:
            logger.error(f"Error cargando lista de tablas discretas para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo cargar la lista de tablas:\n{e}", parent=self)

    def view_table(self):
        """Abre la tabla CSV seleccionada con la aplicación predeterminada."""
        selected_item = self.tables_tree.focus() # Obtiene el IID del item seleccionado
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una tabla para ver.", parent=self)
            return

        # Recuperar la ruta completa guardada en el tag o text (usamos text ahora)
        file_path_str = self.tables_tree.item(selected_item, "text")
        file_path = Path(file_path_str)

        if not file_path.exists():
            messagebox.showerror("Error", f"El archivo seleccionado ya no existe:\n{file_path}", parent=self)
            self.load_tables() # Refrescar lista
            return

        try:
            logger.info(f"Intentando abrir archivo: {file_path}")
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin": # macOS
                subprocess.run(["open", file_path], check=True)
            else: # linux variants
                subprocess.run(["xdg-open", file_path], check=True)
        except FileNotFoundError:
             messagebox.showerror("Error", f"No se pudo encontrar el archivo:\n{file_path}", parent=self)
        except OSError as e:
            logger.error(f"Error del sistema operativo al intentar abrir {file_path}: {e}", exc_info=True)
            messagebox.showerror("Error al Abrir", f"No se pudo abrir el archivo con la aplicación predeterminada.\nError: {e}", parent=self)
        except subprocess.CalledProcessError as e:
             logger.error(f"Error al ejecutar comando para abrir {file_path}: {e}", exc_info=True)
             messagebox.showerror("Error al Abrir", f"El comando para abrir el archivo falló.\nError: {e}", parent=self)
        except Exception as e:
            logger.error(f"Error inesperado al abrir {file_path}: {e}", exc_info=True)
            messagebox.showerror("Error Inesperado", f"Ocurrió un error inesperado al intentar abrir el archivo:\n{e}", parent=self)

    def delete_table(self):
        """Elimina la tabla CSV seleccionada."""
        selected_item = self.tables_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una tabla para eliminar.", parent=self)
            return

        file_path_str = self.tables_tree.item(selected_item, "text")
        file_path = Path(file_path_str)
        file_name = file_path.name

        if not messagebox.askyesno("Confirmar Eliminación",
                                   f"¿Está seguro de que desea eliminar permanentemente la tabla '{file_name}'?",
                                   parent=self):
            return

        try:
            self.analysis_service.delete_discrete_summary_table(str(file_path))
            messagebox.showinfo("Eliminación Exitosa", f"La tabla '{file_name}' ha sido eliminada.", parent=self)
            self.load_tables() # Refrescar la lista
        except FileNotFoundError:
            messagebox.showerror("Error", f"El archivo seleccionado ya no existe:\n{file_path}", parent=self)
            self.load_tables() # Refrescar de todas formas
        except (OSError, ValueError) as e:
            logger.error(f"Error al eliminar la tabla {file_path}: {e}", exc_info=True)
            messagebox.showerror("Error al Eliminar", f"No se pudo eliminar la tabla '{file_name}'.\nError: {e}", parent=self)
        except Exception as e:
            logger.error(f"Error inesperado al eliminar {file_path}: {e}", exc_info=True)
            messagebox.showerror("Error Inesperado", f"Ocurrió un error inesperado al eliminar la tabla:\n{e}", parent=self)

    def destroy(self):
        """Destruye el frame principal de esta vista."""
        super().destroy()
