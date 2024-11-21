"""
KineViz: Sistema de Gestión de Estudios Kinesiológicos

Este sistema permite gestionar estudios kinesiológicos, incluyendo:
- Creación de nuevos estudios
- Visualización de estudios existentes
- Edición de estudios
- Eliminación de estudios
- Gestión de sujetos y pruebas
"""
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Text, Scrollbar, ttk
from lectura import leer_archivo_csv_o_txt
import os
import sqlite3
import shutil
import configparser

class KineVizApp:
    def __init__(self, root):
        self.root = root
        self.root.title('KineViz')

        # Load settings from config file
        self.load_config()
        
        # Variables para campos dinámicos
        self.tipo_prueba_widgets = []
        self.periodo_prueba_widgets = []
        self.current_page = 1 # Initialize current_page here
        self.current_file_page = 1  # Initialize current_file_page here

        # Configurar la base de datos
        self.setup_database()
        
        # Verificar si hay estudios existentes
        if self.hay_estudios():
            self.mostrar_main_page()
        else:
            self.mostrar_landing_page()

    def load_config(self):
        self.config = configparser.ConfigParser()
        try:
            self.config.read('config.ini')
            self.estudios_por_pagina = int(self.config['SETTINGS']['estudios_por_pagina'])
            self.files_per_page = int(self.config['SETTINGS']['files_per_page'])  # Load files_per_page
        except Exception as e:
            # Handle errors (e.g., file not found, invalid values)
            messagebox.showerror("Error", f"Error loading configuration: {str(e)}")
            self.estudios_por_pagina = 10 # Default value
            self.files_per_page = 10  # Default value for files_per_page

    def setup_database(self):
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS estudios (
                id_estudio INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_estudio TEXT NOT NULL,
                num_sujetos INTEGER NOT NULL,
                tipos_prueba TEXT,
                periodos_prueba TEXT,
                cantidad_intentos_prueba INTEGER NOT NULL
            )               
        ''')
        conn.commit()
        conn.close()

    def hay_estudios(self):
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM estudios')
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def restablecer_valores_por_defecto(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea restablecer los valores por defecto?\nEsta acción eliminará todos los estudios y la base de datos."):
            try:
                os.remove("kineviz.db")
                shutil.rmtree("estudios", ignore_errors=True)  # Eliminar la carpeta "estudios"
                self.setup_database()
                messagebox.showinfo("Éxito", "Valores por defecto restablecidos correctamente")
                self.mostrar_landing_page()  # Mostrar la landing page después de reiniciar
            except Exception as e:
                messagebox.showerror("Error", f"Error al restablecer valores: {str(e)}")

    def mostrar_bienvenida(self):
        messagebox.showinfo("Introducción", 
                          "Bienvenido a KineViz. Esta es una aplicación para la gestión y análisis de estudios kinesiológicos.")

    def abrir_manual_usuario(self):
        manual_window = Toplevel(self.root)
        manual_window.title('Manual de Usuario')
        manual_window.geometry('800x600')
        
        try:
            with open('manual_usuario.txt', 'r', encoding='utf-8') as file:
                manual_content = file.read()
        except FileNotFoundError:
            manual_content = "Manual de usuario no encontrado."
        
        text_widget = Text(manual_window, wrap='word')
        text_widget.insert('1.0', manual_content)
        text_widget.config(state='disabled')
        
        scrollbar = Scrollbar(manual_window, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        text_widget.pack(side='left', fill='both', expand=True)

    def mostrar_landing_page(self):
        self.limpiar_ventana()
        
        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = ttk.Label(main_frame, text="KineViz", font=('Helvetica', 24, 'bold'))
        titulo.pack(pady=20)
        
        # Frame para botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        # Botones con estilo consistente
        ttk.Button(button_frame, text='Empieza Aquí', 
                  command=self.mostrar_bienvenida).pack(pady=5)
        
        ttk.Button(button_frame, text='Manual de Usuario', 
                  command=self.abrir_manual_usuario).pack(pady=5)
        
        ttk.Button(button_frame, text='Crear Nuevo Estudio', 
                  command=self.mostrar_crear_estudio).pack(pady=5)

    def mostrar_main_page(self):
        self.limpiar_ventana()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título y botones de la landing page
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="KineViz", font=('Helvetica', 24, 'bold')).pack(side=tk.LEFT)
        
        # Botones de la landing page en el header
        ttk.Button(header_frame, text='Manual', command=self.abrir_manual_usuario).pack(side=tk.RIGHT, padx=5)
        ttk.Button(header_frame, text='Configuración', command=self.mostrar_configuracion).pack(side=tk.RIGHT, padx=5)
        ttk.Button(header_frame, text='Ayuda', command=self.mostrar_bienvenida).pack(side=tk.RIGHT, padx=5)
        ttk.Button(header_frame, text='Abrir Carpeta de Estudios', 
                  command=lambda: self.abrir_carpeta("estudios")).pack(side=tk.RIGHT, padx=5)

        # Frame de búsqueda
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(search_frame, text="Buscar estudio:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Buscar", command=self.buscar_estudio).pack(side=tk.LEFT)
        
        # Frame para la tabla de estudios
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear tabla
        columns = ('Nombre', 'Ver', 'Editar', 'Eliminar')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Configurar columnas
        self.tree.heading('Nombre', text='Nombre del Estudio')
        self.tree.heading('Ver', text='Ver')
        self.tree.heading('Editar', text='Editar')
        self.tree.heading('Eliminar', text='Eliminar')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar tabla y scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar estudios y verificar existencia de carpetas
        self.verificar_estudios_existentes()
        self.cargar_estudios()

        # Frame de paginación
        self.pagination_frame = ttk.Frame(main_frame)
        self.pagination_frame.pack(pady=(10, 0))
        self.update_pagination()
        
        # Botón para crear nuevo estudio
        ttk.Button(main_frame, text='Crear Nuevo Estudio', 
                  command=self.mostrar_crear_estudio).pack(pady=20)

        ttk.Button(main_frame, text='Refrescar', 
                  command=self.cargar_estudios).pack(pady=20)

    def abrir_carpeta(self, path):
        """Abre una carpeta en el explorador de archivos del sistema"""
        if not os.path.exists(path):
            os.makedirs(path)
        if sys.platform == 'win32':
            os.startfile(path)
        else:
            subprocess.call(['open', path])

    def verificar_estudios_existentes(self):
        """Verifica si las carpetas de los estudios existen y elimina los que no tienen carpeta"""
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id_estudio, nombre_estudio FROM estudios')
        estudios = cursor.fetchall()
        
        for id_estudio, nombre_estudio in estudios:
            ruta_estudio = os.path.join("estudios", nombre_estudio)
            if not os.path.exists(ruta_estudio):
                cursor.execute('DELETE FROM estudios WHERE id_estudio = ?', (id_estudio,))
        
        conn.commit()
        conn.close()
        
    def mostrar_configuracion(self):
        config_window = Toplevel(self.root)
        config_window.title('Configuración')

        reset_button = ttk.Button(config_window, text="Restablecer Valores por Defecto", command=self.restablecer_valores_por_defecto)
        reset_button.pack(pady=20)

    def buscar_estudio(self):
        query = self.search_entry.get()
        # Limpiar la tabla
        for i in self.tree.get_children():
            self.tree.delete(i)
        # Realizar la búsqueda en la base de datos y mostrar los resultados
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id_estudio, nombre_estudio FROM estudios WHERE nombre_estudio LIKE ?", ('%' + query + '%',))
        estudios = cursor.fetchall()
        conn.close()
        # Insertar los resultados en la tabla
        for estudio in estudios:
            id_estudio, nombre = estudio
            self.tree.insert("", "end", values=(nombre, 'Ver', 'Editar', 'Eliminar'), tags=(str(id_estudio),))
        self.update_pagination()

    def cargar_estudios(self):
        # Verificar estudios existentes antes de cargar
        self.verificar_estudios_existentes()
        
        # Limpiar tabla existente
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Cargar estudios desde la base de datos
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id_estudio, nombre_estudio FROM estudios LIMIT ? OFFSET ?", (self.estudios_por_pagina, (self.current_page - 1) * self.estudios_por_pagina))
        estudios = cursor.fetchall()
        conn.close()
        
        for estudio in estudios:
            id_estudio, nombre = estudio
            # Insertar fila con botones
            item = self.tree.insert('', tk.END, values=(
                nombre, 
                'Ver', 
                'Editar', 
                'Eliminar'
            ), tags=(str(id_estudio),))
        
        # Configurar eventos de los botones
        self.tree.bind('<ButtonRelease-1>', self.on_tree_click)

    def on_tree_click(self, event):
        # Obtener la fila y columna clickeada
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            row = self.tree.identify_row(event.y)
            
            # Obtener el ID del estudio
            id_estudio = self.tree.item(row, "tags")[0]
            
            # Determinar la acción basada en la columna
            if column == "#2":  # Ver
                self.ver_estudio(int(id_estudio))
            elif column == "#3":  # Editar
                self.editar_estudio(int(id_estudio))
            elif column == "#4":  # Eliminar
                self.eliminar_estudio(int(id_estudio))

    def mostrar_crear_estudio(self):
        self.ventana_crear = Toplevel(self.root)
        self.ventana_crear.title('Crear Estudio')
        self.ventana_crear.geometry('600x800')
        
        # Frame principal con scroll
        canvas = tk.Canvas(self.ventana_crear)
        scrollbar = ttk.Scrollbar(self.ventana_crear, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Variables para campos
        self.var_nombre = tk.StringVar()
        self.var_num_sujetos = tk.StringVar()
        self.var_tipos_prueba = tk.StringVar()
        self.var_periodos_prueba = tk.StringVar()
        self.var_cantidad_intentos = tk.StringVar()
        
        # Campos del formulario
        ttk.Label(scroll_frame, text="Nombre del estudio:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_nombre).pack(pady=5)
        
        ttk.Label(scroll_frame, text="Número de Sujetos:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_num_sujetos).pack(pady=5)
        
        ttk.Label(scroll_frame, text="Tipos de Prueba:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_tipos_prueba).pack(pady=5)
        
        ttk.Label(scroll_frame, text="Periodos de Prueba:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_periodos_prueba).pack(pady=5)

        ttk.Label(scroll_frame, text="Cantidad de Intentos:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_cantidad_intentos).pack(pady=5)
        
        ttk.Button(scroll_frame, text="Guardar", 
                  command=self.guardar_estudio).pack(pady=20)
        
        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def guardar_estudio(self):
        # Validar campos obligatorios
        if not self.var_nombre.get():
            messagebox.showerror("Error", "El nombre del estudio es obligatorio")
            return

        # Validar si el nombre del estudio ya existe
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM estudios WHERE nombre_estudio = ?', (self.var_nombre.get(),))
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            messagebox.showerror("Error", "Ya existe un estudio con ese nombre")
            return
            
        try:
            num_sujetos = int(self.var_num_sujetos.get())
            if num_sujetos <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "El número de sujetos debe ser un número positivo")
            return

        try:
            cantidad_intentos = int(self.var_cantidad_intentos.get())
            if cantidad_intentos <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "La cantidad de intentos debe ser un número positivo")
            return
        
        # Guardar en la base de datos
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO estudios (
                nombre_estudio, num_sujetos, 
                tipos_prueba, periodos_prueba,
                cantidad_intentos_prueba
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            self.var_nombre.get(),
            num_sujetos,
            ','.join([x.strip() for x in self.var_tipos_prueba.get().split(',') if x.strip()]) if self.var_tipos_prueba.get() else None, 
            ','.join([x.strip() for x in self.var_periodos_prueba.get().split(',') if x.strip()]) if self.var_periodos_prueba.get() else None,
            cantidad_intentos,
        ))
        
        # Crear carpeta para el estudio
        estudio_path = os.path.join("estudios", self.var_nombre.get())
        
        if not os.path.exists(estudio_path):
            os.makedirs(estudio_path)

        conn.commit()
        conn.close()
        
        messagebox.showinfo("Éxito", "Estudio creado correctamente")
        self.ventana_crear.destroy()
        self.mostrar_main_page()

    def ver_estudio(self, id_estudio):
        ver_window = Toplevel(self.root)
        ver_window.title('Ver Estudio')
        ver_window.geometry('800x600')
        
        # Frame principal con scroll
        canvas = tk.Canvas(ver_window)
        scrollbar = ttk.Scrollbar(ver_window, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Obtener información del estudio
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM estudios WHERE id_estudio = ?', (id_estudio,))
        estudio = cursor.fetchone()
        conn.close()
        
        if estudio:
            _, nombre_estudio, num_sujetos, tipos_prueba, periodos_prueba, cantidad_intentos = estudio
            
            # Mostrar información del estudio
            ttk.Label(scroll_frame, text=f"Nombre: {nombre_estudio}", 
                     font=('Helvetica', 12, 'bold')).pack(pady=10)
            ttk.Label(scroll_frame, text=f"Número de sujetos: {num_sujetos}").pack(pady=5)

            if tipos_prueba:
                ttk.Label(scroll_frame, text=f"Tipos de prueba: {tipos_prueba}").pack(pady=5)

            if periodos_prueba:
                ttk.Label(scroll_frame, text=f"Periodos de prueba: {periodos_prueba}").pack(pady=5)
            
            ttk.Label(scroll_frame, text=f"Cantidad de intentos: {cantidad_intentos}").pack(pady=5)

            estudio_path = os.path.join("estudios", nombre_estudio)
            
            # Botón para agregar archivos
            ttk.Button(scroll_frame, text="Agregar Archivos", 
                      command=lambda: self.agregar_archivos(estudio_path, nombre_estudio)).pack(pady=10)
                                    
            ttk.Button(scroll_frame, text="Abrir Carpeta del Estudio", 
                      command=lambda: self.abrir_carpeta_estudio(estudio_path)).pack(pady=10)

            # Frame para archivos
            self.archivos_frame = ttk.LabelFrame(scroll_frame, text="Archivos Resultantes")
            self.archivos_frame.pack(pady=10, fill="x", padx=5)

            # Frame para filtros y botones
            filter_frame = ttk.Frame(self.archivos_frame)
            filter_frame.pack(fill=tk.X, pady=(0, 10))

            ttk.Label(filter_frame, text="Buscar archivo:").pack(side=tk.LEFT)
            self.search_file_entry = ttk.Entry(filter_frame)
            self.search_file_entry.pack(side=tk.LEFT, padx=5)

            ttk.Label(filter_frame, text="Filtrar por tipo:").pack(side=tk.LEFT)
            self.filter_type_var = tk.StringVar(value="Todos")
            filter_options = ["Todos", "Cinemática", "Cinética", "Electromiográfica", "OG"]
            filter_menu = ttk.OptionMenu(filter_frame, self.filter_type_var, *filter_options)
            filter_menu.pack(side=tk.LEFT, padx=5)

            ttk.Button(filter_frame, text="Aplicar", 
                      command=lambda: self.cargar_archivos(estudio_path, nombre_estudio)).pack(side=tk.LEFT)
            
            ttk.Button(filter_frame, text="Refrescar", 
                      command=lambda: self.cargar_archivos(estudio_path, nombre_estudio)).pack(side=tk.LEFT, padx=5)

            # Crear tabla de archivos
            self.crear_tabla_archivos(self.archivos_frame, ('Paciente', 'Nombre', 'Tipo', 'Frecuencia', 'Ver', 'Eliminar'))

            # Create file pagination frame BEFORE using it
            self.file_pagination_frame = ttk.Frame(self.archivos_frame)
            self.file_pagination_frame.pack(pady=(10, 0))

            # Now load files and update pagination
            self.cargar_archivos(estudio_path, nombre_estudio)
        
        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def crear_tabla_archivos(self, parent_frame, columns):
        self.archivos_tree = ttk.Treeview(parent_frame, columns=columns, show='headings')
        for col in columns:
            self.archivos_tree.heading(col, text=col)
            self.archivos_tree.column(col, width=75)
        self.archivos_tree.pack(pady=5)
        self.archivos_tree.bind('<ButtonRelease-1>', self.on_file_tree_click)

    def cargar_archivos(self, estudio_path, nombre_estudio):
        # Limpiar tabla existente
        for item in self.archivos_tree.get_children():
            self.archivos_tree.delete(item)

        # Obtener la lista de archivos
        archivos = []
        for root, _, files in os.walk(estudio_path):
            for file in files:
                if file.endswith(".txt"):
                    rel_path = os.path.relpath(os.path.join(root, file), estudio_path)
                    tipo = ""
                    frecuencia = ""
                    paciente = os.path.basename(os.path.dirname(os.path.dirname(os.path.join(root, file))))

                    # Determinar tipo y frecuencia basado en la ruta del archivo
                    if "OG" in root:
                        tipo = "OG"
                    elif "Cinemática" in root:
                        tipo = "New"
                        frecuencia = "Cinemática"
                    elif "Cinética" in root:
                        tipo = "New"
                        frecuencia = "Cinética"
                    elif "Electromiográfica" in root:
                        tipo = "New"
                        frecuencia = "Electromiográfica"

                    archivos.append((paciente, rel_path, tipo, frecuencia))

        # Aplicar filtros
        search_query = self.search_file_entry.get().lower()
        filter_type = self.filter_type_var.get()

        filtered_archivos = []
        for paciente, archivo, tipo, frecuencia in archivos:
            if (search_query in archivo.lower() or search_query in paciente.lower()) and \
               (filter_type == "Todos" or 
                (filter_type == "Cinemática" and "Cinemática" in archivo) or
                (filter_type == "Cinética" and "Cinética" in archivo) or
                (filter_type == "Electromiográfica" and "Electromiográfica" in archivo) or
                (filter_type == "OG" and tipo == "OG")):
                filtered_archivos.append((paciente, archivo, tipo, frecuencia))

        # Reset filter_type_var to "Todos" after filtering
        self.filter_type_var.set("Todos")  

        # Paginación
        start_idx = (self.current_file_page - 1) * self.files_per_page
        end_idx = min(start_idx + self.files_per_page, len(filtered_archivos))
        paginated_archivos = filtered_archivos[start_idx:end_idx]

        # Insertar filas en la tabla
        for paciente, archivo, tipo, frecuencia in paginated_archivos:
            self.archivos_tree.insert("", tk.END, values=(
                paciente,
                os.path.basename(archivo),
                tipo,
                frecuencia,
                'Ver',
                'Eliminar'
            ), tags=(archivo,))

        # Update pagination without resetting filter
        self.update_file_pagination(estudio_path, nombre_estudio)

    def update_file_pagination(self, estudio_path, nombre_estudio):
        """Update pagination for files table"""
        # Clear existing pagination buttons
        for widget in self.file_pagination_frame.winfo_children():
            widget.destroy()

        # Get all files and apply filters to get accurate count
        archivos = []
        for root, _, files in os.walk(estudio_path):
            for file in files:
                if file.endswith(".txt"):
                    rel_path = os.path.relpath(os.path.join(root, file), estudio_path)
                    tipo = ""
                    frecuencia = ""
                    paciente = os.path.basename(os.path.dirname(os.path.dirname(os.path.join(root, file))))

                    # Determinar tipo y frecuencia basado en la ruta del archivo
                    if "OG" in root:
                        tipo = "OG"
                    elif "Cinemática" in root:
                        tipo = "New"
                        frecuencia = "Cinemática"
                    elif "Cinética" in root:
                        tipo = "New"
                        frecuencia = "Cinética"
                    elif "Electromiográfica" in root:
                        tipo = "New"
                        frecuencia = "Electromiográfica"

                    archivos.append((paciente, rel_path, tipo, frecuencia))

        # Apply filters
        search_query = self.search_file_entry.get().lower()
        filter_type = self.filter_type_var.get()

        filtered_archivos = []
        for paciente, archivo, tipo, frecuencia in archivos:
            if (search_query in archivo.lower() or search_query in paciente.lower()) and \
               (filter_type == "Todos" or 
                (filter_type == "Cinemática" and "Cinemática" in archivo) or
                (filter_type == "Cinética" and "Cinética" in archivo) or
                (filter_type == "Electromiográfica" and "Electromiográfica" in archivo) or
                (filter_type == "OG" and tipo == "OG")):
                filtered_archivos.append((paciente, archivo, tipo, frecuencia))

        # Calculate total pages based on filtered files
        total_pages = (len(filtered_archivos) // self.files_per_page) + (1 if len(filtered_archivos) % self.files_per_page else 0)
        total_pages = max(1, total_pages)  # Ensure at least 1 page

        if total_pages > 1:
            # First page button
            ttk.Button(
                self.file_pagination_frame, 
                text="<<", 
                command=lambda e=estudio_path, n=nombre_estudio: self.go_to_first_file_page(e, n)
            ).pack(side=tk.LEFT)
            
            # Previous page button
            ttk.Button(
                self.file_pagination_frame, 
                text="<", 
                command=lambda e=estudio_path, n=nombre_estudio: self.go_to_previous_file_page(e, n)
            ).pack(side=tk.LEFT)

            # Page number buttons
            for page in range(1, total_pages + 1):
                ttk.Button(
                    self.file_pagination_frame, 
                    text=str(page),
                    command=lambda p=page, e=estudio_path, n=nombre_estudio: self.go_to_file_page(p, e, n)
                ).pack(side=tk.LEFT)

            # Next page button
            ttk.Button(
                self.file_pagination_frame, 
                text=">", 
                command=lambda e=estudio_path, n=nombre_estudio, t=total_pages: self.go_to_next_file_page(e, n, t)
            ).pack(side=tk.LEFT)
            
            # Last page button
            ttk.Button(
                self.file_pagination_frame, 
                text=">>", 
                command=lambda e=estudio_path, n=nombre_estudio, t=total_pages: self.go_to_last_file_page(e, n, t)
            ).pack(side=tk.LEFT)

    def go_to_first_file_page(self, estudio_path, nombre_estudio):
        self.current_file_page = 1
        self.cargar_archivos(estudio_path, nombre_estudio)

    def go_to_previous_file_page(self, estudio_path, nombre_estudio):
        if self.current_file_page > 1:
            self.current_file_page -= 1
            self.cargar_archivos(estudio_path, nombre_estudio)

    def go_to_next_file_page(self, estudio_path, nombre_estudio, total_pages):
        if self.current_file_page < total_pages:
            self.current_file_page += 1
            self.cargar_archivos(estudio_path, nombre_estudio)

    def go_to_last_file_page(self, estudio_path, nombre_estudio, total_pages):
        self.current_file_page = total_pages
        self.cargar_archivos(estudio_path, nombre_estudio)

    def go_to_file_page(self, page, estudio_path, nombre_estudio):
        self.current_file_page = page
        self.cargar_archivos(estudio_path, nombre_estudio)

    def on_file_tree_click(self, event):
        region = self.archivos_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.archivos_tree.identify_column(event.x)
            row = self.archivos_tree.identify_row(event.y)
            if not row:
                return
                
            values = self.archivos_tree.item(row)['values']
            if not values:
                return
                
            archivo = self.archivos_tree.item(row, "tags")[0]
            if not archivo:
                return

            # Get the study name from the current window title
            current_window = event.widget.winfo_toplevel()
            study_name = None
            
            # Get all studies from database
            conn = sqlite3.connect('kineviz.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nombre_estudio FROM estudios')
            studies = cursor.fetchall()
            conn.close()
            
            # Find which study this file belongs to
            for (nombre_estudio,) in studies:
                if os.path.exists(os.path.join("estudios", nombre_estudio, archivo)):
                    study_name = nombre_estudio
                    break
            
            if not study_name:
                messagebox.showerror("Error", "No se pudo encontrar el estudio asociado al archivo")
                return

            estudio_path = os.path.join("estudios", study_name)

            if column == "#5":  # Ver
                self.abrir_archivo(os.path.join(estudio_path, archivo))
            elif column == "#6":  # Eliminar
                self.eliminar_archivo(estudio_path, archivo)

    def abrir_archivo(self, archivo_path):
        if os.path.exists(archivo_path):
            if sys.platform == 'win32':
                os.startfile(archivo_path)
            else:
                subprocess.call(['open', archivo_path])
        else:
            messagebox.showerror("Error", "El archivo no existe")

    def eliminar_archivo(self, estudio_path, archivo):
        if messagebox.askyesno("Confirmar", f"¿Desea eliminar el archivo {archivo}?"):
            try:
                archivo_path = os.path.join(estudio_path, archivo)
                os.remove(archivo_path)
                messagebox.showinfo("Éxito", "Archivo eliminado correctamente")
                
                # Verificar si la carpeta del tipo de archivo está vacía
                tipo_path = os.path.dirname(archivo_path)
                if not os.listdir(tipo_path):
                    os.rmdir(tipo_path)
                
                # Verificar si la carpeta del paciente está vacía
                paciente_path = os.path.dirname(tipo_path)
                if not os.listdir(paciente_path):
                    os.rmdir(paciente_path)
                
                # Verificar si la carpeta del estudio está vacía
                if not os.listdir(estudio_path):
                    os.rmdir(estudio_path)
                    # Si la carpeta del estudio está vacía, eliminar el estudio de la base de datos
                    conn = sqlite3.connect('kineviz.db')
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM estudios WHERE nombre_estudio = ?', (os.path.basename(estudio_path),))
                    conn.commit()
                    conn.close()
                    self.mostrar_main_page()
                else:
                    # Actualizar vista de archivos
                    self.cargar_archivos(estudio_path, os.path.basename(estudio_path))
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar archivo: {str(e)}")

    def agregar_archivos(self, estudio_path, nombre_estudio):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("Archivos de texto", "*.txt"), ("Archivos CSV", "*.csv")]
        )
        if archivo:
            try:
                leer_archivo_csv_o_txt(archivo, nombre_estudio)
                messagebox.showinfo("Éxito", "Archivo agregado correctamente")
                # Actualizar vista de archivos
                self.cargar_archivos(estudio_path, nombre_estudio)
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar archivo: {str(e)}")

    def abrir_carpeta_estudio(self, estudio_path):
        if os.path.exists(estudio_path):
            if sys.platform == 'win32':
                os.startfile(estudio_path)
            else:
                subprocess.call(['open', estudio_path])
        else:
            messagebox.showerror("Error", "La carpeta del estudio no existe")

    def editar_estudio(self, id_estudio):
        # Similar a mostrar_crear_estudio pero con datos precargados
        self.ventana_editar = Toplevel(self.root)
        self.ventana_editar.title('Editar Estudio')
        self.ventana_editar.geometry('600x800')
        
        # Obtener datos del estudio
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM estudios WHERE id_estudio = ?', (id_estudio,))
        estudio = cursor.fetchone()
        conn.close()
        
        if not estudio:
            messagebox.showerror("Error", "Estudio no encontrado")
            return
        
        _, nombre_estudio, num_sujetos, tipos_prueba, periodos_prueba, cantidad_intentos = estudio

        # Frame principal con scroll
        canvas = tk.Canvas(self.ventana_editar)
        scrollbar = ttk.Scrollbar(self.ventana_editar, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Variables para campos
        self.var_nombre = tk.StringVar(value=nombre_estudio)
        self.var_num_sujetos = tk.StringVar(value=str(num_sujetos))
        self.var_tipos_prueba = tk.StringVar(value=tipos_prueba)
        self.var_periodos_prueba = tk.StringVar(value=periodos_prueba)
        self.var_cantidad_intentos = tk.StringVar(value=str(cantidad_intentos))
        
        # Campos del formulario
        ttk.Label(scroll_frame, text="Nombre del estudio:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_nombre).pack(pady=5)
        
        ttk.Label(scroll_frame, text="Número de Sujetos:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_num_sujetos).pack(pady=5)
        
        ttk.Label(scroll_frame, text="Tipos de Prueba:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_tipos_prueba).pack(pady=5)
        
        ttk.Label(scroll_frame, text="Periodos de Prueba:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_periodos_prueba).pack(pady=5)

        ttk.Label(scroll_frame, text="Cantidad de Intentos:").pack(pady=5)
        ttk.Entry(scroll_frame, textvariable=self.var_cantidad_intentos).pack(pady=5)
        
        ttk.Button(scroll_frame, text="Guardar", 
                  command=lambda: self.guardar_edicion(id_estudio, nombre_estudio)).pack(pady=20)
        
        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def guardar_edicion(self, id_estudio, nombre_estudio_original):
        # Validar campos obligatorios
        if not self.var_nombre.get():
            messagebox.showerror("Error", "El nombre del estudio es obligatorio")
            return

        # Validar si el nombre del estudio ya existe (excluyendo el nombre actual)
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM estudios WHERE nombre_estudio = ? AND id_estudio != ?', (self.var_nombre.get(), id_estudio))
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            messagebox.showerror("Error", "Ya existe un estudio con ese nombre")
            return
            
        try:
            num_sujetos = int(self.var_num_sujetos.get())
            if num_sujetos <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "El número de sujetos debe ser un número positivo")
            return
            
        try:
            cantidad_intentos = int(self.var_cantidad_intentos.get())
            if cantidad_intentos <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "La cantidad de intentos debe ser un número positivo")
            return
        
        # Actualizar en la base de datos
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE estudios 
            SET nombre_estudio = ?, 
                num_sujetos = ?, 
                tipos_prueba = ?,
                periodos_prueba = ?,
                cantidad_intentos_prueba = ?
            WHERE id_estudio = ?
        ''', (
            self.var_nombre.get(),
            num_sujetos,
            ','.join([x.strip() for x in self.var_tipos_prueba.get().split(',') if x.strip()]) if self.var_tipos_prueba.get() else None, 
            ','.join([x.strip() for x in self.var_periodos_prueba.get().split(',') if x.strip()]) if self.var_periodos_prueba.get() else None,
            cantidad_intentos,
            id_estudio
        ))

        # Renombrar carpeta si el nombre del estudio cambió
        if nombre_estudio_original != self.var_nombre.get():
            old_path = os.path.join("estudios", nombre_estudio_original)
            new_path = os.path.join("estudios", self.var_nombre.get())
            
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
            else:
                # Si la carpeta no existe, créala (en caso de que se haya creado el estudio sin carpeta)
                os.makedirs(new_path)

        conn.commit()
        conn.close()
        
        messagebox.showinfo("Éxito", "Estudio actualizado correctamente")
        self.ventana_editar.destroy()
        self.mostrar_main_page()

    def eliminar_estudio(self, id_estudio):
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea eliminar este estudio?"):
            try:
                # Obtener nombre del estudio antes de eliminarlo
                conn = sqlite3.connect('kineviz.db')
                cursor = conn.cursor()
                cursor.execute('SELECT nombre_estudio FROM estudios WHERE id_estudio = ?', (id_estudio,))
                nombre_estudio = cursor.fetchone() 
                
                if nombre_estudio is not None:
                    nombre_estudio = nombre_estudio[0]
                else:
                    raise Exception("Estudio no encontrado en la base de datos")

                # Eliminar archivos físicos
                estudio_path = os.path.join("estudios", nombre_estudio)
                if os.path.exists(estudio_path):
                    for root, dirs, files in os.walk(estudio_path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(estudio_path)
                
                # Eliminar registro de la base de datos
                cursor.execute('DELETE FROM estudios WHERE id_estudio = ?', (id_estudio,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Éxito", "Estudio eliminado correctamente")
                self.mostrar_main_page()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar estudio: {str(e)}")

    def update_pagination(self):
        # Clear existing pagination buttons
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM estudios")
        total_estudios = cursor.fetchone()[0]
        conn.close()

        self.total_pages = (total_estudios // self.estudios_por_pagina) + (1 if total_estudios % self.estudios_por_pagina else 0)
        self.current_page = 1

        if self.total_pages > 1:
            ttk.Button(self.pagination_frame, text="<<", command=self.go_to_first_page).pack(side=tk.LEFT)
            ttk.Button(self.pagination_frame, text="<", command=self.go_to_previous_page).pack(side=tk.LEFT)

            for page in range(1, self.total_pages + 1):
                ttk.Button(self.pagination_frame, text=str(page), command=lambda p=page: self.go_to_page(p)).pack(side=tk.LEFT)

            ttk.Button(self.pagination_frame, text=">", command=self.go_to_next_page).pack(side=tk.LEFT)
            ttk.Button(self.pagination_frame, text=">>", command=self.go_to_last_page).pack(side=tk.LEFT)

    def go_to_first_page(self):
        self.current_page = 1
        self.cargar_estudios()

    def go_to_previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.cargar_estudios()

    def go_to_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.cargar_estudios()

    def go_to_last_page(self):
        self.current_page = self.total_pages
        self.cargar_estudios()

    def go_to_page(self, page):
        self.current_page = page
        self.cargar_estudios()

def main():
    root = tk.Tk()
    root.title('KineViz')
    root.geometry('1000x600')
    app = KineVizApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
