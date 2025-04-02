import tkinter as tk
from tkinter import ttk, messagebox
import os # Necesario para os.startfile
import sys # Necesario para sys.platform
import subprocess # Necesario para open/xdg-open
from pathlib import Path # Para manejar rutas de archivo
# Importar FileService para type hinting
from kineviz.core.services.file_service import FileService

class FileBrowser(ttk.Frame):
    def __init__(self, parent, file_service, study_id):
        super().__init__(parent)
        self.file_service = file_service
        self.study_id = study_id
        self.create_widgets()
    
    def create_widgets(self):
        # Crear tabla de archivos
        columns = ('Paciente', 'Nombre', 'Tipo', 'Frecuencia', 'Ver', 'Eliminar')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100) # Ajustar ancho si es necesario

        # Usar tk.BOTH en lugar de ttk.BOTH
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Configurar eventos
        self.tree.bind('<ButtonRelease-1>', self.on_tree_click)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Empaquetar usando grid para controlar scrollbar
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')


        # Cargar archivos iniciales
        self.load_files()

    def load_files(self):
        """Carga los archivos usando FileService y los muestra en la tabla."""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener archivos del estudio usando el file_service inyectado
        try:
            files = self.file_service.get_study_files(self.study_id)
        except Exception as e:
            messagebox.showerror("Error al Cargar Archivos", f"No se pudieron cargar los archivos del estudio:\n{e}", parent=self)
            files = [] # Dejar la tabla vacía si hay error

        for file_info in files:
            # Asegurarse de que los valores sean strings para el Treeview
            # Usar .get con default por si alguna clave falta (aunque no debería)
            self.tree.insert('', 'end', values=(
                str(file_info.get('patient', 'N/A')),
                str(file_info.get('name', 'N/A')),
                str(file_info.get('type', 'N/A')),
                str(file_info.get('frequency', 'N/A')),
                'Ver',      # Texto para botón Ver
                'Eliminar'  # Texto para botón Eliminar
            ), tags=(str(file_info.get('path', '')),)) # Guardar la ruta como string en tags

    def on_tree_click(self, event):
        """Maneja los clics en la tabla de archivos."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column_id = self.tree.identify_column(event.x) # ej: '#5'
        row_id = self.tree.identify_row(event.y) # ej: 'I001'

        if not row_id: # Clic fuera de las filas
            return

        # Obtener la ruta del archivo desde los tags
        item_tags = self.tree.item(row_id, "tags")
        if not item_tags or not item_tags[0]:
            messagebox.showwarning("Advertencia", "No se pudo obtener la ruta del archivo seleccionado.", parent=self)
            return
        file_path_str = item_tags[0]
        file_path = Path(file_path_str) # Convertir a Path

        # Determinar la acción basada en la columna clickeada
        # Los índices de columna empiezan en 1 ('#1', '#2', ...)
        column_index = int(column_id.replace('#', '')) - 1 # Índice basado en 0

        if column_index == 4:  # Columna "Ver" (índice 4)
            self.view_file(file_path)
        elif column_index == 5:  # Columna "Eliminar" (índice 5)
            self.delete_file(file_path)

    def view_file(self, file_path: Path):
        """Abre el archivo seleccionado con la aplicación predeterminada."""
        if not file_path.exists():
             messagebox.showerror("Error", f"El archivo no existe:\n{file_path}", parent=self)
             return
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin': # macOS
                subprocess.run(['open', file_path], check=True)
            else: # Linux, etc.
                subprocess.run(['xdg-open', file_path], check=True)
        except FileNotFoundError:
             messagebox.showerror("Error", f"No se pudo encontrar la aplicación para abrir el archivo:\n{file_path}", parent=self)
        except subprocess.CalledProcessError as e:
             messagebox.showerror("Error", f"El comando para abrir el archivo falló:\n{e}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo '{file_path.name}':\n{str(e)}", parent=self)

    def delete_file(self, file_path: Path):
        """Solicita confirmación y elimina un archivo usando FileService."""
        if not file_path.exists():
             messagebox.showerror("Error", f"El archivo ya no existe:\n{file_path}", parent=self)
             self.load_files() # Recargar por si acaso
             return

        file_name = file_path.name
        if messagebox.askyesno("Confirmar Eliminación",
                               f"¿Está seguro de que desea eliminar el archivo:\n'{file_name}'?\n\nEsta acción es permanente.",
                               icon='warning', parent=self):
            try:
                # Usar el file_service para eliminar
                self.file_service.delete_file(file_path)
                messagebox.showinfo("Éxito", f"Archivo '{file_name}' eliminado correctamente.", parent=self)
                self.load_files() # Recargar la lista de archivos
            except FileNotFoundError:
                 messagebox.showerror("Error", f"El archivo no se encontró al intentar eliminarlo:\n{file_path}", parent=self)
                 self.load_files() # Recargar lista
            except Exception as e:
                messagebox.showerror("Error al Eliminar", f"No se pudo eliminar el archivo:\n{e}", parent=self)
                import traceback
                traceback.print_exc() # Para debugging en consola
