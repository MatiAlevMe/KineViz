import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Text, Scrollbar
from lectura import leer_archivo_csv_o_txt
import os
import sqlite3

ventana = tk.Tk()

# Función para abrir el manual de usuario
def abrir_manual_usuario():
    manual_window = Toplevel()
    manual_window.title('Manual de Usuario')
    
    # Cargar el contenido del manual de usuario
    with open('manual_usuario.txt', 'r', encoding='utf-8') as file:
        manual_content = file.read()
    
    # Crear un widget de texto para mostrar el manual
    text_widget = Text(manual_window, wrap='word', height=20, width=80)
    text_widget.insert('1.0', manual_content)
    text_widget.config(state='disabled')  # Hacer el texto no editable
    text_widget.pack(side='left', fill='both', expand=True)
    
    # Crear una barra de desplazamiento
    scrollbar = Scrollbar(manual_window, command=text_widget.yview)
    scrollbar.pack(side='right', fill='y')
    text_widget.config(yscrollcommand=scrollbar.set)

# Función para crear estudio
def crear_estudio():
    nombre_estudio = entrada_nombre.get()
    if not nombre_estudio:
        messagebox.showerror("Error", "El nombre del estudio no puede estar vacío")
        return
    
    num_sujetos = entrada_num_sujetos.get()
    if not num_sujetos.isdigit() or int(num_sujetos) <= 0:
        messagebox.showerror("Error", "El número de sujetos debe ser un número positivo")
        return
    
    formato_sujetos = entrada_formato_sujetos.get()
    if not formato_sujetos:
        messagebox.showerror("Error", "El formato de los sujetos no puede estar vacío")
        return
    
    tiene_tipo_prueba = var_tipo_prueba.get()
    tipos_prueba = []
    if tiene_tipo_prueba:
        cantidad_tipos_prueba = entrada_cantidad_tipos_prueba.get()
        if not cantidad_tipos_prueba.isdigit() or int(cantidad_tipos_prueba) <= 0:
            messagebox.showerror("Error", "La cantidad de tipos de prueba debe ser un número positivo")
            return
        
        for i in range(int(cantidad_tipos_prueba)):
            tipo_prueba = entrada_tipo_prueba[i].get()
            if not tipo_prueba:
                messagebox.showerror("Error", f"El nombre del tipo de prueba {i+1} no puede estar vacío")
                return
            tipos_prueba.append(tipo_prueba)
    
    tiene_periodo_prueba = var_periodo_prueba.get()
    periodos_prueba = []
    if tiene_periodo_prueba:
        cantidad_periodos_prueba = entrada_cantidad_periodos_prueba.get()
        if not cantidad_periodos_prueba.isdigit() or int(cantidad_periodos_prueba) <= 0:
            messagebox.showerror("Error", "La cantidad de períodos de prueba debe ser un número positivo")
            return
        
        for i in range(int(cantidad_periodos_prueba)):
            periodo_prueba = entrada_periodo_prueba[i].get()
            if not periodo_prueba:
                messagebox.showerror("Error", f"El nombre del período de prueba {i+1} no puede estar vacío")
                return
            periodos_prueba.append(periodo_prueba)
    
    cantidad_intentos_prueba = entrada_cantidad_intentos_prueba.get()
    if not cantidad_intentos_prueba.isdigit() or int(cantidad_intentos_prueba) <= 0:
        messagebox.showerror("Error", "La cantidad de intentos de prueba debe ser un número positivo")
        return
    
    formato_intentos_prueba = entrada_formato_intentos_prueba.get()
    if not formato_intentos_prueba:
        messagebox.showerror("Error", "El formato de los intentos de prueba no puede estar vacío")
        return
    
    # Guardar la información en la base de datos
    conn = sqlite3.connect('kineviz.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudios (
            id_estudio INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_estudio TEXT NOT NULL,
            num_sujetos INTEGER NOT NULL,
            formato_sujetos TEXT NOT NULL,
            tiene_tipo_prueba BOOLEAN NOT NULL,
            tipos_prueba TEXT,
            tiene_periodo_prueba BOOLEAN NOT NULL,
            periodos_prueba TEXT,
            cantidad_intentos_prueba INTEGER NOT NULL,
            formato_intentos_prueba TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT INTO estudios (nombre_estudio, num_sujetos, formato_sujetos, tiene_tipo_prueba, tipos_prueba, tiene_periodo_prueba, periodos_prueba, cantidad_intentos_prueba, formato_intentos_prueba)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nombre_estudio, int(num_sujetos), formato_sujetos, tiene_tipo_prueba, ','.join(tipos_prueba) if tiene_tipo_prueba else None, tiene_periodo_prueba, ','.join(periodos_prueba) if tiene_periodo_prueba else None, int(cantidad_intentos_prueba), formato_intentos_prueba))
    conn.commit()
    
    # Obtener el id_estudio del estudio recién creado
    cursor.execute('SELECT id_estudio FROM estudios WHERE nombre_estudio = ?', (nombre_estudio,))
    id_estudio = cursor.fetchone()[0]
    conn.close()
    
    messagebox.showinfo("Éxito", f"Estudio '{nombre_estudio}' creado correctamente")
    ver_estudio(id_estudio)

# Función para abrir la página principal de gestión de estudios
def abrir_main_page():
    ventana.destroy()
    main_window = tk.Tk()
    main_window.title('Gestión de Estudios Kinesiológicos')
    
    # Crear una tabla para listar estudios
    frame = tk.Frame(main_window)
    frame.pack(pady=20)
    
    # Encabezados de la tabla
    tk.Label(frame, text="Nombre del Estudio").grid(row=0, column=0, padx=10, pady=5)
    tk.Label(frame, text="Acciones").grid(row=0, column=1, padx=10, pady=5)
    
    # Conectar a la base de datos y listar estudios
    conn = sqlite3.connect('kineviz.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id_estudio, nombre_estudio FROM estudios')
    estudios = cursor.fetchall()
    conn.close()
    
    for index, estudio in enumerate(estudios):
        id_estudio, nombre_estudio = estudio
        tk.Label(frame, text=nombre_estudio).grid(row=index+1, column=0, padx=10, pady=5)
        
        # Botones para cada estudio
        btn_ver = tk.Button(frame, text='Ver', command=lambda id_estudio=id_estudio: ver_estudio(id_estudio))
        btn_ver.grid(row=index+1, column=1, padx=10, pady=5, sticky='w')
        
        btn_editar = tk.Button(frame, text='Editar', command=lambda id_estudio=id_estudio: editar_estudio(id_estudio))
        btn_editar.grid(row=index+1, column=1, padx=10, pady=5, sticky='e')
        
        btn_eliminar = tk.Button(frame, text='Eliminar', command=lambda id_estudio=id_estudio: eliminar_estudio(id_estudio))
        btn_eliminar.grid(row=index+1, column=1, padx=10, pady=5, sticky='s')
    
    main_window.mainloop()

# Función para ver un estudio
def ver_estudio(id_estudio):
    ver_window = Toplevel()
    ver_window.title('Ver Estudio')
    
    # Conectar a la base de datos y obtener información del estudio
    conn = sqlite3.connect('kineviz.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM estudios WHERE id_estudio = ?', (id_estudio,))
    estudio = cursor.fetchone()
    conn.close()
    
    if estudio:
        _, nombre_estudio, _, _, _, tipos_prueba, _, _, _, formato_intentos_prueba = estudio
        tk.Label(ver_window, text=f"Nombre del Estudio: {nombre_estudio}").pack()
        tk.Label(ver_window, text=f"Formato de Intentos de Prueba: {formato_intentos_prueba}").pack()
        
        if tipos_prueba:
            tk.Label(ver_window, text=f"Tipos de Prueba: {tipos_prueba}").pack()
        
        # Listar archivos del estudio
        estudio_path = os.path.join("estudios", nombre_estudio)
        if os.path.exists(estudio_path):
            archivos = os.listdir(estudio_path)
            if archivos:
                for archivo in archivos:
                    tk.Label(ver_window, text=archivo).pack()
                    
                    # Botones para cada archivo
                    btn_eliminar_archivo = tk.Button(ver_window, text='Eliminar', command=lambda archivo=archivo: eliminar_archivo(estudio_path, archivo))
                    btn_eliminar_archivo.pack(side='left', padx=5)
                    
                    btn_agregar_archivo = tk.Button(ver_window, text='Agregar Archivos', command=lambda: agregar_archivos(estudio_path))
                    btn_agregar_archivo.pack(side='right', padx=5)
            else:
                tk.Label(ver_window, text="No hay archivos que mostrar").pack()
        else:
            tk.Label(ver_window, text="No hay archivos que mostrar").pack()

# Función para editar un estudio
def editar_estudio(id_estudio):
    editar_window = Toplevel()
    editar_window.title('Editar Estudio')
    
    # Conectar a la base de datos y obtener información del estudio
    conn = sqlite3.connect('kineviz.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM estudios WHERE id_estudio = ?', (id_estudio,))
    estudio = cursor.fetchone()
    conn.close()
    
    if estudio:
        _, nombre_estudio, num_sujetos, formato_sujetos, tiene_tipo_prueba, tipos_prueba, tiene_periodo_prueba, periodos_prueba, cantidad_intentos_prueba, formato_intentos_prueba = estudio
        
        tk.Label(editar_window, text="Nombre del Estudio:").pack()
        entrada_nombre_editar = tk.Entry(editar_window)
        entrada_nombre_editar.insert(0, nombre_estudio)
        entrada_nombre_editar.pack()
        
        tk.Label(editar_window, text="Número de Sujetos de Prueba:").pack()
        entrada_num_sujetos_editar = tk.Entry(editar_window)
        entrada_num_sujetos_editar.insert(0, str(num_sujetos))
        entrada_num_sujetos_editar.pack()
        
        tk.Label(editar_window, text="Formato de los Sujetos de Prueba:").pack()
        entrada_formato_sujetos_editar = tk.Entry(editar_window)
        entrada_formato_sujetos_editar.insert(0, formato_sujetos)
        entrada_formato_sujetos_editar.pack()
        
        var_tipo_prueba_editar = tk.BooleanVar(value=tiene_tipo_prueba)
        chk_tipo_prueba_editar = tk.Checkbutton(editar_window, text="Tiene Tipo de Prueba", variable=var_tipo_prueba_editar)
        chk_tipo_prueba_editar.pack()
        
        if tiene_tipo_prueba:
            tk.Label(editar_window, text="Cantidad de Tipos de Prueba:").pack()
            entrada_cantidad_tipos_prueba_editar = tk.Entry(editar_window)
            entrada_cantidad_tipos_prueba_editar.insert(0, str(len(tipos_prueba.split(','))))
            entrada_cantidad_tipos_prueba_editar.pack()
            
            for i, tipo_prueba in enumerate(tipos_prueba.split(',')):
                tk.Label(editar_window, text=f"Nombre de Tipo de Prueba {i+1}:").pack()
                entrada_tipo_prueba_editar = tk.Entry(editar_window)
                entrada_tipo_prueba_editar.insert(0, tipo_prueba)
                entrada_tipo_prueba_editar.pack()
        
        var_periodo_prueba_editar = tk.BooleanVar(value=tiene_periodo_prueba)
        chk_periodo_prueba_editar = tk.Checkbutton(editar_window, text="Tiene Periodo de Prueba", variable=var_periodo_prueba_editar)
        chk_periodo_prueba_editar.pack()
        
        if tiene_periodo_prueba:
            tk.Label(editar_window, text="Cantidad de Periodos de Prueba:").pack()
            entrada_cantidad_periodos_prueba_editar = tk.Entry(editar_window)
            entrada_cantidad_periodos_prueba_editar.insert(0, str(len(periodos_prueba.split(','))))
            entrada_cantidad_periodos_prueba_editar.pack()
            
            for i, periodo_prueba in enumerate(periodos_prueba.split(',')):
                tk.Label(editar_window, text=f"Nombre de Periodo de Prueba {i+1}:").pack()
                entrada_periodo_prueba_editar = tk.Entry(editar_window)
                entrada_periodo_prueba_editar.insert(0, periodo_prueba)
                entrada_periodo_prueba_editar.pack()
        
        tk.Label(editar_window, text="Cantidad de Intentos de Prueba:").pack()
        entrada_cantidad_intentos_prueba_editar = tk.Entry(editar_window)
        entrada_cantidad_intentos_prueba_editar.insert(0, str(cantidad_intentos_prueba))
        entrada_cantidad_intentos_prueba_editar.pack()
        
        tk.Label(editar_window, text="Formato de los Intentos de Prueba:").pack()
        entrada_formato_intentos_prueba_editar = tk.Entry(editar_window)
        entrada_formato_intentos_prueba_editar.insert(0, formato_intentos_prueba)
        entrada_formato_intentos_prueba_editar.pack()
        
        # Botón para guardar los cambios
        btn_guardar_editar = tk.Button(editar_window, text='Guardar', command=lambda: guardar_edicion(id_estudio, entrada_nombre_editar, entrada_num_sujetos_editar, entrada_formato_sujetos_editar, var_tipo_prueba_editar, entrada_cantidad_tipos_prueba_editar, entrada_tipo_prueba_editar, var_periodo_prueba_editar, entrada_cantidad_periodos_prueba_editar, entrada_periodo_prueba_editar, entrada_cantidad_intentos_prueba_editar, entrada_formato_intentos_prueba_editar))
        btn_guardar_editar.pack()

# Función para guardar la edición de un estudio
def guardar_edicion(id_estudio, entrada_nombre, entrada_num_sujetos, entrada_formato_sujetos, var_tipo_prueba, entrada_cantidad_tipos_prueba, entrada_tipo_prueba, var_periodo_prueba, entrada_cantidad_periodos_prueba, entrada_periodo_prueba, entrada_cantidad_intentos_prueba, entrada_formato_intentos_prueba):
    nombre_estudio = entrada_nombre.get()
    if not nombre_estudio:
        messagebox.showerror("Error", "El nombre del estudio no puede estar vacío")
        return
    
    num_sujetos = entrada_num_sujetos.get()
    if not num_sujetos.isdigit() or int(num_sujetos) <= 0:
        messagebox.showerror("Error", "El número de sujetos debe ser un número positivo")
        return
    
    formato_sujetos = entrada_formato_sujetos.get()
    if not formato_sujetos:
        messagebox.showerror("Error", "El formato de los sujetos no puede estar vacío")
        return
    
    tiene_tipo_prueba = var_tipo_prueba.get()
    tipos_prueba = []
    if tiene_tipo_prueba:
        cantidad_tipos_prueba = entrada_cantidad_tipos_prueba.get()
        if not cantidad_tipos_prueba.isdigit() or int(cantidad_tipos_prueba) <= 0:
            messagebox.showerror("Error", "La cantidad de tipos de prueba debe ser un número positivo")
            return
        
        for i in range(int(cantidad_tipos_prueba)):
            tipo_prueba = entrada_tipo_prueba[i].get()
            if not tipo_prueba:
                messagebox.showerror("Error", f"El nombre del tipo de prueba {i+1} no puede estar vacío")
                return
            tipos_prueba.append(tipo_prueba)
    
    tiene_periodo_prueba = var_periodo_prueba.get()
    periodos_prueba = []
    if tiene_periodo_prueba:
        cantidad_periodos_prueba = entrada_cantidad_periodos_prueba.get()
        if not cantidad_periodos_prueba.isdigit() or int(cantidad_periodos_prueba) <= 0:
            messagebox.showerror("Error", "La cantidad de períodos de prueba debe ser un número positivo")
            return
        
        for i in range(int(cantidad_periodos_prueba)):
            periodo_prueba = entrada_periodo_prueba[i].get()
            if not periodo_prueba:
                messagebox.showerror("Error", f"El nombre del período de prueba {i+1} no puede estar vacío")
                return
            periodos_prueba.append(periodo_prueba)
    
    cantidad_intentos_prueba = entrada_cantidad_intentos_prueba.get()
    if not cantidad_intentos_prueba.isdigit() or int(cantidad_intentos_prueba) <= 0:
        messagebox.showerror("Error", "La cantidad de intentos de prueba debe ser un número positivo")
        return
    
    formato_intentos_prueba = entrada_formato_intentos_prueba.get()
    if not formato_intentos_prueba:
        messagebox.showerror("Error", "El formato de los intentos de prueba no puede estar vacío")
        return
    
    # Actualizar la información en la base de datos
    conn = sqlite3.connect('kineviz.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE estudios
        SET nombre_estudio = ?, num_sujetos = ?, formato_sujetos = ?, tiene_tipo_prueba = ?, tipos_prueba = ?, tiene_periodo_prueba = ?, periodos_prueba = ?, cantidad_intentos_prueba = ?, formato_intentos_prueba = ?
        WHERE id_estudio = ?
    ''', (nombre_estudio, int(num_sujetos), formato_sujetos, tiene_tipo_prueba, ','.join(tipos_prueba) if tiene_tipo_prueba else None, tiene_periodo_prueba, ','.join(periodos_prueba) if tiene_periodo_prueba else None, int(cantidad_intentos_prueba), formato_intentos_prueba, id_estudio))
    conn.commit()
    conn.close()
    
    messagebox.showinfo("Éxito", f"Estudio '{nombre_estudio}' actualizado correctamente")
    abrir_main_page()

# Función para eliminar un estudio
def eliminar_estudio(id_estudio):
    confirmacion = messagebox.askyesno("Confirmación", "¿Está seguro de que desea eliminar este estudio?")
    if confirmacion:
        # Conectar a la base de datos y eliminar el estudio
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT nombre_estudio FROM estudios WHERE id_estudio = ?', (id_estudio,))
        estudio = cursor.fetchone()
        if estudio:
            nombre_estudio = estudio[0]
            estudio_path = os.path.join("estudios", nombre_estudio)
            if os.path.exists(estudio_path):
                for archivo in os.listdir(estudio_path):
                    os.remove(os.path.join(estudio_path, archivo))
                os.rmdir(estudio_path)
            cursor.execute('DELETE FROM estudios WHERE id_estudio = ?', (id_estudio,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", f"Estudio '{nombre_estudio}' eliminado correctamente")
            abrir_main_page()

# Función para agregar archivos a un estudio
def agregar_archivos(estudio_path):
    archivo_seleccionado = filedialog.askopenfilename(title="Seleccionar archivo CSV o TXT", 
                                                      filetypes=[("Archivos CSV", "*.csv"), ("Archivos TXT", "*.txt")])
    if archivo_seleccionado:
        # Leer y procesar el archivo con el nombre del estudio
        nombre_estudio = os.path.basename(estudio_path)
        leer_archivo_csv_o_txt(archivo_seleccionado, nombre_estudio)
        messagebox.showinfo("Éxito", f"Archivo {archivo_seleccionado} cargado correctamente")
        ver_estudio(estudio_path)

# Función para eliminar un archivo de un estudio
def eliminar_archivo(estudio_path, archivo):
    confirmacion = messagebox.askyesno("Confirmación", "¿Está seguro de que desea eliminar este archivo?")
    if confirmacion:
        os.remove(os.path.join(estudio_path, archivo))
        messagebox.showinfo("Éxito", f"Archivo '{archivo}' eliminado correctamente")
        ver_estudio(estudio_path)

# Función para abrir la landing page
def abrir_landing_page():
    ventana.title('KineViz')
    
    # Nombre del proyecto
    tk.Label(ventana, text="KineViz", font=('Helvetica', 24, 'bold')).pack(pady=20)
    
    # Botón para la introducción rápida
    btn_empieza_aqui = tk.Button(ventana, text='Empieza Aquí', command=lambda: messagebox.showinfo("Introducción", "Bienvenido a KineViz. Esta es una aplicación para la gestión y análisis de estudios kinesiológicos."))
    btn_empieza_aqui.pack(pady=5)
    
    # Botón para el manual de usuario
    btn_manual_usuario = tk.Button(ventana, text='Manual de Usuario', command=abrir_manual_usuario)
    btn_manual_usuario.pack(pady=5)
    
    # Botón para crear estudio
    btn_crear_estudio = tk.Button(ventana, text='Crea Tu Primer Estudio', command=crear_estudio_form)
    btn_crear_estudio.pack(pady=5)
    
    ventana.mainloop()

# Función para abrir el formulario de creación de estudio
def crear_estudio_form():
    crear_estudio_window = Toplevel(ventana)
    crear_estudio_window.title('Crear Estudio')
    
    # Nombre del estudio
    tk.Label(crear_estudio_window, text="Nombre del estudio:").pack()
    global entrada_nombre
    entrada_nombre = tk.Entry(crear_estudio_window)
    entrada_nombre.pack()
    
    # Número de sujetos de prueba
    tk.Label(crear_estudio_window, text="Número de Sujetos de Prueba:").pack()
    global entrada_num_sujetos
    entrada_num_sujetos = tk.Entry(crear_estudio_window)
    entrada_num_sujetos.pack()
    
    # Formato de los sujetos de prueba
    tk.Label(crear_estudio_window, text="Formato de los Sujetos de Prueba:").pack()
    global entrada_formato_sujetos
    entrada_formato_sujetos = tk.Entry(crear_estudio_window)
    entrada_formato_sujetos.pack()
    
    # ¿Tiene Tipo de Prueba?
    global var_tipo_prueba
    var_tipo_prueba = tk.BooleanVar()
    chk_tipo_prueba = tk.Checkbutton(crear_estudio_window, text="Tiene Tipo de Prueba", variable=var_tipo_prueba, command=mostrar_campos_tipo_prueba)
    chk_tipo_prueba.pack()
    
    # Campos para Tipo de Prueba
    global entrada_cantidad_tipos_prueba, entrada_tipo_prueba
    entrada_cantidad_tipos_prueba = tk.Entry(crear_estudio_window)
    entrada_tipo_prueba = []
    
    # ¿Tiene Periodo de Prueba?
    global var_periodo_prueba
    var_periodo_prueba = tk.BooleanVar()
    chk_periodo_prueba = tk.Checkbutton(crear_estudio_window, text="Tiene Periodo de Prueba", variable=var_periodo_prueba, command=mostrar_campos_periodo_prueba)
    chk_periodo_prueba.pack()
    
    # Campos para Periodo de Prueba
    global entrada_cantidad_periodos_prueba, entrada_periodo_prueba
    entrada_cantidad_periodos_prueba = tk.Entry(crear_estudio_window)
    entrada_periodo_prueba = []
    
    # Cantidad de Intentos de Prueba
    tk.Label(crear_estudio_window, text="Cantidad de Intentos de Prueba:").pack()
    global entrada_cantidad_intentos_prueba
    entrada_cantidad_intentos_prueba = tk.Entry(crear_estudio_window)
    entrada_cantidad_intentos_prueba.pack()
    
    # Formato de los Intentos de Prueba
    tk.Label(crear_estudio_window, text="Formato de los Intentos de Prueba:").pack()
    global entrada_formato_intentos_prueba
    entrada_formato_intentos_prueba = tk.Entry(crear_estudio_window)
    entrada_formato_intentos_prueba.pack()
    
    # Botón para guardar el estudio
    btn_guardar = tk.Button(crear_estudio_window, text='Guardar', command=crear_estudio)
    btn_guardar.pack(pady=20)
    
    crear_estudio_window.mainloop()

# Función para mostrar campos de Tipo de Prueba
def mostrar_campos_tipo_prueba():
    if var_tipo_prueba.get():
        tk.Label(crear_estudio_window, text="Cantidad de Tipos de Prueba:").pack()
        entrada_cantidad_tipos_prueba.pack()
        cantidad_tipos_prueba = entrada_cantidad_tipos_prueba.get()
        if cantidad_tipos_prueba.isdigit() and int(cantidad_tipos_prueba) > 0:
            for i in range(int(cantidad_tipos_prueba)):
                tk.Label(crear_estudio_window, text=f"Nombre de Tipo de Prueba {i+1}:").pack()
                entrada_tipo_prueba.append(tk.Entry(crear_estudio_window))
                entrada_tipo_prueba[i].pack()
    else:
        entrada_cantidad_tipos_prueba.pack_forget()
        for entry in entrada_tipo_prueba:
            entry.pack_forget()
        entrada_tipo_prueba = []

# Función para mostrar campos de Periodo de Prueba
def mostrar_campos_periodo_prueba():
    if var_periodo_prueba.get():
        tk.Label(crear_estudio_window, text="Cantidad de Periodos de Prueba:").pack()
        entrada_cantidad_periodos_prueba.pack()
        cantidad_periodos_prueba = entrada_cantidad_periodos_prueba.get()
        if cantidad_periodos_prueba.isdigit() and int(cantidad_periodos_prueba) > 0:
            for i in range(int(cantidad_periodos_prueba)):
                tk.Label(crear_estudio_window, text=f"Nombre de Periodo de Prueba {i+1}:").pack()
                entrada_periodo_prueba.append(tk.Entry(crear_estudio_window))
                entrada_periodo_prueba[i].pack()
    else:
        entrada_cantidad_periodos_prueba.pack_forget()
        for entry in entrada_periodo_prueba:
            entry.pack_forget()
        entrada_periodo_prueba = []

# Función para verificar si existen estudios y abrir la landing page o la página principal
def verificar_estudios_y_abrir():
    if os.path.exists('kineviz.db'):
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM estudios')
        count = cursor.fetchone()[0]
        conn.close()
        if count > 0:
            abrir_main_page()
        else:
            abrir_landing_page()
    else:
        abrir_landing_page()

if __name__ == "__main__":
    verificar_estudios_y_abrir()
