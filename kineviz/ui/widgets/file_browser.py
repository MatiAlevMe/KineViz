import tkinter as tk # Importar tkinter
from tkinter import ttk, messagebox
import os

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
        
        # Cargar archivos iniciales
        self.load_files()
    
    def load_files(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener archivos del estudio
        files = self.file_service.get_study_files(self.study_id)
        
        for file_info in files:
            self.tree.insert('', 'end', values=(
                file_info['patient'],
                file_info['name'],
                file_info['type'],
                file_info['frequency'],
                'Ver',
                'Eliminar'
            ), tags=(file_info['path'],))
    
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            row = self.tree.identify_row(event.y)
            
            if column == "#5":  # Ver
                self.view_file(row)
            elif column == "#6":  # Eliminar
                self.delete_file(row)
    
    def view_file(self, row):
        file_path = self.tree.item(row, "tags")[0]
        try:
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")
    
    def delete_file(self, row):
        file_path = self.tree.item(row, "tags")[0]
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este archivo?"):
            try:
                os.remove(file_path)
                self.load_files()
                messagebox.showinfo("Éxito", "Archivo eliminado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el archivo: {str(e)}")
