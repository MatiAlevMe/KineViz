"""
Este módulo contiene la interfaz de usuario para la aplicación KineViz.
Incluye funciones para cargar y visualizar datos de estudios en formato CSV o TXT.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from lectura_archivos.lectura import leer_archivo_csv_o_txt

def crear_estudio():
    """
    Crea un estudio basado en los archivos cargados y opciones seleccionadas.
    """
    nombre_estudio = entrada_nombre.get()
    if not nombre_estudio:
        messagebox.showerror("Error", "El nombre del estudio no puede estar vacío")
        return
    
    archivo_seleccionado = filedialog.askopenfilename(title="Seleccionar archivo CSV o TXT", 
                                                      filetypes=[("Archivos CSV", "*.csv"), ("Archivos TXT", "*.txt")])
    if archivo_seleccionado:
        # Leer y procesar el archivo
        df = leer_archivo_csv_o_txt(archivo_seleccionado)
        messagebox.showinfo("Éxito", f"Archivo {archivo_seleccionado} cargado correctamente")
        # Aquí podrías guardar el estudio en tu carpeta local
    else:
        messagebox.showerror("Error", "No se seleccionó ningún archivo")
        
def abrir_interfaz():
    ventana = tk.Tk()
    ventana.title('Creación de Estudios Kinesiológicos')
    
    # Nombre del estudio
    tk.Label(ventana, text="Nombre del estudio:").pack()
    global entrada_nombre
    entrada_nombre = tk.Entry(ventana)
    entrada_nombre.pack()
    
    # Botón para crear estudio
    btn_crear_estudio = tk.Button(ventana, text='Crear Estudio', command=crear_estudio)
    btn_crear_estudio.pack()
    
    ventana.mainloop()

# Ejecutar la interfaz
if __name__ == "__main__":
    abrir_interfaz()
