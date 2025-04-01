from tkinter import ttk, messagebox, Tk, Toplevel, Text, Scrollbar, filedialog
from .ui.main_window import MainWindow
from .database.operations import get_db_connection
import sqlite3
import os
import configparser
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

class KineVizApp:
    def __init__(self, root):
        self.root = root
        self.study_service = StudyService()
        self.analysis_service = AnalysisService()
        self.current_view = None
        
        self.configure_styles()
        self.show_landing_page()

    def configure_styles(self):
        # Configurar estilos de la aplicación
        style = ttk.Style()
        style.configure('TButton', font=('Helvetica', 10))
        style.configure('TLabel', font=('Helvetica', 12))

    def show_landing_page(self):
        # Mostrar página de inicio
        if self.current_view:
            self.current_view.destroy()
        
        self.current_view = LandingPage(self.root, self)
        self.current_view.pack(fill=tk.BOTH, expand=True)

    def show_study_view(self, study_id=None):
        # Mostrar vista de estudio
        if self.current_view:
            self.current_view.destroy()
        
        self.current_view = StudyView(self.root, self, study_id)
        self.current_view.pack(fill=tk.BOTH, expand=True)

    def open_analysis_dialog(self, study_id):
        # Abrir diálogo de análisis
        AnalysisDialog(self.root, self.analysis_service, study_id)
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
        self.current_pdf_page = 1  # Initialize current_pdf_page here

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
            self.pdfs_per_page = int(self.config['SETTINGS'].get('pdfs_per_page', 10))  # Load pdfs_per_page, default 10
        except Exception as e:
            # Handle errors (e.g., file not found, invalid values)
            messagebox.showerror("Error", f"Error loading configuration: {str(e)}")
            self.estudios_por_pagina = 10  # Default value
            self.files_per_page = 10  # Default value for files_per_page
            self.pdfs_per_page = 10  # Default value for pdfs_per_page

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

    def validar_pacientes_estudio(self, id_estudio):
        """Valida que el estudio tenga al menos dos pacientes diferentes"""
        # Obtener el nombre del estudio
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT nombre_estudio FROM estudios WHERE id_estudio = ?', (id_estudio,))
        nombre_estudio = cursor.fetchone()[0]
        conn.close()

        # Obtener la ruta del estudio
        estudio_path = os.path.join("estudios", nombre_estudio)
        
        # Obtener lista de pacientes únicos
        pacientes = set()
        if os.path.exists(estudio_path):
            for root, dirs, files in os.walk(estudio_path):
                for file in files:
                    if file.endswith('.txt'):
                        # El paciente es el nombre del directorio dos niveles arriba del archivo
                        paciente = os.path.basename(os.path.dirname(os.path.dirname(os.path.join(root, file))))
                        pacientes.add(paciente)
        
        return len(pacientes) >= 2

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

        # Validar que no haya valores duplicados entre tipos y periodos de prueba
        tipos_prueba = [x.strip() for x in self.var_tipos_prueba.get().split(',') if x.strip()]
        periodos_prueba = [x.strip() for x in self.var_periodos_prueba.get().split(',') if x.strip()]
        
        duplicates = set(tipos_prueba) & set(periodos_prueba)
        if duplicates:
            messagebox.showerror("Error", f"Los siguientes valores están duplicados en Tipos y Periodos de prueba: {', '.join(duplicates)}")
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
            ','.join(tipos_prueba),
            ','.join(periodos_prueba),
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

    def extract_test_info(self, filename, tipos_prueba, periodos_prueba):
        """
        Extract Tipo de Prueba and Periodo de Prueba from filename.
        Handles different formats and validates against study criteria.
        """
        # Remove extension and split
        name = os.path.splitext(filename)[0]
        parts = name.split()
        
        tipo_prueba = None
        periodo_prueba = None
        
        # Convert to sets for easier lookup
        tipos_set = set(tipos_prueba) if tipos_prueba else set()
        periodos_set = set(periodos_prueba) if periodos_prueba else set()
        
        if len(parts) >= 4:  # Format: "Pte01 POST CMJ 01"
            # Check if second part is in periodos and third in tipos
            if parts[1] in periodos_set and parts[2] in tipos_set:
                periodo_prueba = parts[1]
                tipo_prueba = parts[2]
            # Check if second part is in tipos and third in periodos
            elif parts[1] in tipos_set and parts[2] in periodos_set:
                tipo_prueba = parts[1]
                periodo_prueba = parts[2]
        elif len(parts) == 3:  # Format: "Pte01 CMJ 01" or "Pte01 POST 01"
            # Check if middle part is in tipos or periodos
            if parts[1] in tipos_set:
                tipo_prueba = parts[1]
            elif parts[1] in periodos_set:
                periodo_prueba = parts[1]
        
        return tipo_prueba, periodo_prueba

    def check_existing_files(self, estudio_path):
        """Check if there are any files in the study directory"""
        if not os.path.exists(estudio_path):
            return False
            
        for root, _, files in os.walk(estudio_path):
            for file in files:
                if file.endswith('.txt'):
                    return True
        return False

    def validate_filename_format(self, filename, tipos_prueba, periodos_prueba):
        """
        Validate filename format based on study criteria.
        Returns True if valid, False otherwise.
        """
        # Remove extension and split by spaces or underscores
        name = os.path.splitext(filename)[0]
        parts = name.replace('_', ' ').split()
        
        # Case 1: No tipos or periodos defined - expect only 2 parts (Pte01 01)
        if not tipos_prueba and not periodos_prueba:
            return len(parts) == 2
            
        # Case 2: Only tipos or only periodos defined - expect 3 parts (Pte01 CMJ 01)
        if bool(tipos_prueba) != bool(periodos_prueba):  # XOR - one is defined but not both
            if len(parts) != 3:
                return False
            middle_part = parts[1]
            if tipos_prueba:
                return middle_part in tipos_prueba
            else:
                return middle_part in periodos_prueba
                
        # Case 3: Both tipos and periodos defined - expect 4 parts (Pte01 CMJ PRE 01)
        if len(parts) != 4:
            return False
        return (parts[1] in tipos_prueba and parts[2] in periodos_prueba) or \
               (parts[1] in periodos_prueba and parts[2] in tipos_prueba)

    def get_invalid_files(self, estudio_path, tipos_prueba, periodos_prueba):
        """Get list of files that don't meet the criteria"""
        invalid_files = []
        if os.path.exists(estudio_path):
            for root, _, files in os.walk(estudio_path):
                for file in files:
                    if file.endswith('.txt'):
                        rel_path = os.path.relpath(os.path.join(root, file), estudio_path)
                        if not self.validate_filename_format(file, tipos_prueba, periodos_prueba):
                            invalid_files.append(rel_path)
        return invalid_files

    def guardar_edicion(self, id_estudio, nombre_estudio_original):
        # Validar campos obligatorios
        if not self.var_nombre.get():
            messagebox.showerror("Error", "El nombre del estudio es obligatorio")
            return

        # Validar si el nombre del estudio ya existe (excluyendo el nombre actual)
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM estudios WHERE nombre_estudio = ? AND id_estudio != ?', 
                      (self.var_nombre.get(), id_estudio))
        count = cursor.fetchone()[0]
        
        if count > 0:
            messagebox.showerror("Error", "Ya existe un estudio con ese nombre")
            conn.close()
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

        # Get current study criteria
        cursor.execute('SELECT tipos_prueba, periodos_prueba FROM estudios WHERE id_estudio = ?', (id_estudio,))
        current_tipos, current_periodos = cursor.fetchone()
        
        # Get new criteria
        new_tipos = [x.strip() for x in self.var_tipos_prueba.get().split(',') if x.strip()]
        new_periodos = [x.strip() for x in self.var_periodos_prueba.get().split(',') if x.strip()]

        # Check for duplicates between tipos and periodos
        duplicates = set(new_tipos) & set(new_periodos)
        if duplicates:
            messagebox.showerror("Error", 
                               f"Los siguientes valores están duplicados en Tipos y Periodos de prueba: {', '.join(duplicates)}")
            conn.close()
            return

        # Check if criteria changed and there are existing files
        estudio_path = os.path.join("estudios", nombre_estudio_original)
        has_files = self.check_existing_files(estudio_path)
        
        if has_files and (
            ','.join(new_tipos) != (current_tipos or '') or 
            ','.join(new_periodos) != (current_periodos or '')
        ):
            # Get list of invalid files
            invalid_files = self.get_invalid_files(estudio_path, new_tipos, new_periodos)
            
            if invalid_files:
                if messagebox.askyesno("Advertencia", 
                                     f"Los siguientes archivos no cumplen con los nuevos criterios:\n" +
                                     "\n".join(invalid_files) +
                                     "\n\n¿Desea eliminar estos archivos y continuar?"):
                    # Eliminar archivos inválidos
                    for file in invalid_files:
                        file_path = os.path.join(estudio_path, file)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            # Remove parent directories if empty
                            parent_dir = os.path.dirname(file_path)
                            while parent_dir != estudio_path:
                                try:
                                    os.rmdir(parent_dir)
                                    parent_dir = os.path.dirname(parent_dir)
                                except OSError:
                                    break
                else:
                    conn.close()
                    return

        # Actualizar en la base de datos
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
            ','.join(new_tipos),
            ','.join(new_periodos),
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
                os.makedirs(new_path)

        conn.commit()
        conn.close()
        
        messagebox.showinfo("Éxito", "Estudio actualizado correctamente")
        self.ventana_editar.destroy()
        self.mostrar_main_page()

    def validate_file_criteria(self, filename, id_estudio):
        """Validate if file meets the study criteria"""
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT tipos_prueba, periodos_prueba FROM estudios WHERE id_estudio = ?', (id_estudio,))
        tipos_prueba_str, periodos_prueba_str = cursor.fetchone()
        conn.close()

        tipos_prueba = [t.strip() for t in tipos_prueba_str.split(',')] if tipos_prueba_str else []
        periodos_prueba = [p.strip() for p in periodos_prueba_str.split(',')] if periodos_prueba_str else []

        # Remove extension and split
        name = os.path.splitext(filename)[0]
        parts = name.replace('_', ' ').split()

        # Validate based on study criteria
        if not tipos_prueba and not periodos_prueba:
            if len(parts) != 2:
                return False, f"El archivo debe tener formato 'PteXX NN' pero tiene {len(parts)} partes: {name}"
            return True, None

        if bool(tipos_prueba) != bool(periodos_prueba):  # One is defined but not both
            if len(parts) != 3:
                return False, f"El archivo debe tener formato 'PteXX VALOR NN' pero tiene {len(parts)} partes: {name}"
            middle_part = parts[1]
            if tipos_prueba and middle_part not in tipos_prueba:
                return False, f"El tipo de prueba '{middle_part}' no coincide con los criterios del estudio: {', '.join(tipos_prueba)}"
            if periodos_prueba and middle_part not in periodos_prueba:
                return False, f"El periodo de prueba '{middle_part}' no coincide con los criterios del estudio: {', '.join(periodos_prueba)}"
            return True, None

        # Both tipos and periodos defined
        if len(parts) != 4:
            return False, f"El archivo debe tener formato 'PteXX TIPO PERIODO NN' pero tiene {len(parts)} partes: {name}"
        
        # Check both possible orders (tipo-periodo and periodo-tipo)
        valid_order1 = parts[1] in tipos_prueba and parts[2] in periodos_prueba
        valid_order2 = parts[1] in periodos_prueba and parts[2] in tipos_prueba
        
        if not (valid_order1 or valid_order2):
            return False, f"Los valores '{parts[1]}' y '{parts[2]}' no coinciden con los tipos de prueba ({', '.join(tipos_prueba)}) y periodos de prueba ({', '.join(periodos_prueba)})"
        
        return True, None

    def agregar_archivos(self, estudio_path, nombre_estudio):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("Archivos de texto", "*.txt"), ("Archivos CSV", "*.csv")]
        )
        if archivo:
            # Get study ID
            conn = sqlite3.connect('kineviz.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id_estudio FROM estudios WHERE nombre_estudio = ?', (nombre_estudio,))
            id_estudio = cursor.fetchone()[0]
            conn.close()

            # Validate file
            is_valid, error_msg = self.validate_file_criteria(os.path.basename(archivo), id_estudio)
            
            if not is_valid:
                messagebox.showerror("Error de Validación", error_msg)
                return

            try:
                leer_archivo_csv_o_txt(archivo, nombre_estudio)
                messagebox.showinfo("Éxito", "Archivo agregado correctamente")
                # Actualizar vista de archivos
                self.cargar_archivos(estudio_path, nombre_estudio)
            except Exception as e:
                messagebox.showerror("Error", f"Error al agregar archivo: {str(e)}")

    def remove_from_analysis(self, category, item):
        """Elimina un elemento de la lista de análisis"""
        if item:
            analysis_listbox = getattr(self, f"{category.lower().replace(' ', '_').replace('ó', 'o')}_analysis_listbox")
            selection = analysis_listbox.curselection()
            if selection:
                analysis_listbox.delete(selection)

    def reset_filter(self, var, default_value):
        """Resetea un filtro a su valor por defecto"""
        var.set(default_value)

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
                    # Botón para abrir carpeta de PDFs
            
            ttk.Button(scroll_frame, text="Abrir Carpeta de Reportes",
                      command=lambda: self.abrir_carpeta(os.path.join(estudio_path, "reportes"))).pack(pady=10)

            # Botón para abrir ventana de análisis
            ttk.Button(scroll_frame, text="Análisis de Estudio",
                      command=lambda: self.mostrar_analisis_estudio(id_estudio)).pack(pady=10)

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
            filter_options = ["Todos", "Cinematica", "Cinetica", "Electromiografica", "OG"]
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

    def setup_parameter_selection(self, parent, title):
        """Configura un frame para selección de parámetros"""
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill=tk.X, pady=5)
        
        # Listbox para selección
        listbox = tk.Listbox(frame, height=4, selectmode=tk.SINGLE)
        listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        # Botón para agregar
        ttk.Button(
            frame, 
            text="Agregar",
            command=lambda: self.add_to_analysis(
                title,
                listbox.get(listbox.curselection()) if listbox.curselection() else None
            )
        ).pack(side=tk.LEFT, padx=5)
        
        return listbox

    def setup_analysis_list(self, parent, title):
        """Configura un frame para la lista de análisis"""
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill=tk.X, pady=5)
        
        # Listbox para elementos seleccionados
        listbox = tk.Listbox(frame, height=4)
        listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        # Botón para eliminar
        ttk.Button(
            frame, 
            text="Eliminar",
            command=lambda: self.remove_from_analysis(
                title,
                listbox.get(listbox.curselection()) if listbox.curselection() else None
            )
        ).pack(side=tk.LEFT, padx=5)
        
        return listbox

    def actualizar_listas_parametros(self, id_estudio):
        """Actualiza las listas de parámetros basado en la frecuencia seleccionada"""
        # Obtener el nombre del estudio y criterios
        conn = sqlite3.connect('kineviz.db')
        cursor = conn.cursor()
        cursor.execute('SELECT nombre_estudio, tipos_prueba, periodos_prueba FROM estudios WHERE id_estudio = ?', (id_estudio,))
        nombre_estudio, tipos_prueba, periodos_prueba = cursor.fetchone()
        conn.close()

        # Ruta del estudio
        estudio_path = os.path.join("estudios", nombre_estudio)
        frecuencia = self.freq_var.get()

        # Limpiar listboxes
        for categoria in ["pacientes", "frecuencia_medicion", "tipo_prueba", "periodo_prueba"]:
            listbox = getattr(self, f"{categoria}_listbox")
            listbox.delete(0, tk.END)

        # Obtener y mostrar datos
        pacientes = set()
        frecuencias = set()
        tipos_prueba_set = set()
        periodos_prueba_set = set()

        if os.path.exists(estudio_path):
            for root, _, files in os.walk(estudio_path):
                for file in files:
                    if file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        
                        # Solo procesar archivos que coincidan con la frecuencia seleccionada
                        if frecuencia == "Todos" or frecuencia in file_path:
                            # Extraer información del path y nombre de archivo
                            rel_path = os.path.relpath(file_path, estudio_path)
                            parts = rel_path.split(os.sep)
                            
                            if len(parts) >= 2:
                                pacientes.add(parts[0])  # Primer nivel es el paciente
                                
                                # Determinar frecuencia del archivo
                                if "Cinematica" in file_path:
                                    frecuencias.add("Cinematica")
                                elif "Cinetica" in file_path:
                                    frecuencias.add("Cinetica")
                                elif "Electromiografica" in file_path:
                                    frecuencias.add("Electromiografica")
                                
                                # Extraer y validar tipo y periodo de prueba
                                tipo_prueba, periodo_prueba = self.extract_test_info(file, 
                                                                                   tipos_prueba.split(',') if tipos_prueba else [], 
                                                                                   periodos_prueba.split(',') if periodos_prueba else [])
                                
                                if tipo_prueba:
                                    tipos_prueba_set.add(tipo_prueba)
                                if periodo_prueba:
                                    periodos_prueba_set.add(periodo_prueba)

        # Actualizar listboxes
        for paciente in sorted(pacientes):
            self.pacientes_listbox.insert(tk.END, paciente)
        
        for freq in sorted(frecuencias):
            self.frecuencia_medicion_listbox.insert(tk.END, freq)
        
        for tipo in sorted(tipos_prueba_set):
            self.tipo_prueba_listbox.insert(tk.END, tipo)
        
        for periodo in sorted(periodos_prueba_set):
            self.periodo_prueba_listbox.insert(tk.END, periodo)

    def generar_grafico_barras(self, pacientes, calculo):
        """Genera un gráfico de barras con la media del cálculo para cada paciente."""
        if not pacientes or not calculo:
            messagebox.showerror("Error", "Debe seleccionar al menos dos pacientes y un cálculo.")
            return

        # Obtener nombre del estudio
        current_window = self.root.focus_get().winfo_toplevel()
        study_name = current_window.title().replace('Análisis de Estudio - ', '')
        estudio_path = os.path.join("estudios", study_name)

        medias = []
        for paciente in pacientes:
            valores_totales = []
            # Recorrer todas las carpetas de frecuencia
            for frecuencia in ["Cinematica", "Cinetica", "Electromiografica"]:
                # Recorrer todos los tipos de prueba
                for tipo in self.tipo_prueba_analysis_listbox.get(0, tk.END):
                    # Recorrer todos los periodos de prueba
                    for periodo in self.periodo_prueba_analysis_listbox.get(0, tk.END):
                        valores = self.procesar_datos(estudio_path, paciente, frecuencia, tipo, periodo)
                        if valores:
                            valores_totales.extend(valores)
            
            media = self.calcular_estadisticas(valores_totales, calculo) if valores_totales else 0
            medias.append(media)

        # Crear el gráfico de barras
        plt.figure(figsize=(8, 6))
        plt.bar(pacientes, medias)
        plt.title(f"Media de {calculo} por Paciente")
        plt.xlabel("Pacientes")
        plt.ylabel(f"Media de {calculo}")
        plt.show()

    def mostrar_analisis_estudio(self, id_estudio):
        """Muestra la ventana de análisis de estudio"""
        # Validar que haya al menos dos pacientes antes de abrir la ventana
        if not self.validar_pacientes_estudio(id_estudio):
            messagebox.showwarning("Advertencia", 
                                 "El estudio debe tener al menos dos pacientes diferentes para realizar el análisis.")
            return

        # Crear la ventana de análisis
        analisis_window = Toplevel(self.root)
        analisis_window.title('Análisis de Estudio')
        analisis_window.geometry('1000x800')

        # Frame principal con scroll
        main_frame = ttk.Frame(analisis_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Filtro de Frecuencia
        freq_frame = ttk.LabelFrame(main_frame, text="Frecuencia")
        freq_frame.pack(fill=tk.X, pady=(0, 10))
        freq_options = ["Todos", "Cinematica", "Cinetica", "Electromiografica"]
        self.freq_var = tk.StringVar(value=freq_options[0])

        # Frame para selección de parámetros y lista de análisis
        params_frame = ttk.Frame(main_frame)
        params_frame.pack(fill=tk.BOTH, expand=True)

        # Frame izquierdo - Selección de parámetros
        left_frame = ttk.LabelFrame(params_frame, text="Selección de Parámetros")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Pacientes
        pacientes_frame = ttk.LabelFrame(left_frame, text="Pacientes")
        pacientes_frame.pack(fill=tk.X, pady=5)
        self.pacientes_listbox = tk.Listbox(pacientes_frame, height=4, selectmode=tk.SINGLE)
        self.pacientes_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(pacientes_frame, text="Agregar", 
                  command=lambda: self.add_to_analysis("Pacientes", 
                  self.pacientes_listbox.get(self.pacientes_listbox.curselection()) if self.pacientes_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(pacientes_frame, text="Agregar Todo", 
                  command=lambda: self.add_all_to_analysis("Pacientes", self.pacientes_listbox)).pack(side=tk.LEFT, padx=5)

        # Frecuencia de Medición
        freq_med_frame = ttk.LabelFrame(left_frame, text="Frecuencia de Medición")
        freq_med_frame.pack(fill=tk.X, pady=5)
        self.frecuencia_medicion_listbox = tk.Listbox(freq_med_frame, height=4, selectmode=tk.SINGLE)
        self.frecuencia_medicion_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(freq_med_frame, text="Agregar", 
                  command=lambda: self.add_to_analysis("Frecuencia de Medición",
                  self.frecuencia_medicion_listbox.get(self.frecuencia_medicion_listbox.curselection()) if self.frecuencia_medicion_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(freq_med_frame, text="Agregar Todo", 
                  command=lambda: self.add_all_to_analysis("Frecuencia de Medición", self.frecuencia_medicion_listbox)).pack(side=tk.LEFT, padx=5)

        # Tipo de Prueba
        tipo_prueba_frame = ttk.LabelFrame(left_frame, text="Tipo de Prueba")
        tipo_prueba_frame.pack(fill=tk.X, pady=5)
        self.tipo_prueba_listbox = tk.Listbox(tipo_prueba_frame, height=4, selectmode=tk.SINGLE)
        self.tipo_prueba_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(tipo_prueba_frame, text="Agregar", 
                  command=lambda: self.add_to_analysis("Tipo de Prueba",
                  self.tipo_prueba_listbox.get(self.tipo_prueba_listbox.curselection()) if self.tipo_prueba_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(tipo_prueba_frame, text="Agregar Todo", 
                  command=lambda: self.add_all_to_analysis("Tipo de Prueba", self.tipo_prueba_listbox)).pack(side=tk.LEFT, padx=5)

        # Periodo de Prueba
        periodo_prueba_frame = ttk.LabelFrame(left_frame, text="Periodo de Prueba")
        periodo_prueba_frame.pack(fill=tk.X, pady=5)
        self.periodo_prueba_listbox = tk.Listbox(periodo_prueba_frame, height=4, selectmode=tk.SINGLE)
        self.periodo_prueba_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(periodo_prueba_frame, text="Agregar", 
                  command=lambda: self.add_to_analysis("Periodo de Prueba",
                  self.periodo_prueba_listbox.get(self.periodo_prueba_listbox.curselection()) if self.periodo_prueba_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(periodo_prueba_frame, text="Agregar Todo", 
                  command=lambda: self.add_all_to_analysis("Periodo de Prueba", self.periodo_prueba_listbox)).pack(side=tk.LEFT, padx=5)

        # Cálculos
        calculo_frame = ttk.LabelFrame(left_frame, text="Cálculos")
        calculo_frame.pack(fill=tk.X, pady=5)
        self.calculo_listbox = tk.Listbox(calculo_frame, height=4, selectmode=tk.SINGLE)
        self.calculo_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Add default calculation options
        for calc in ["Maximo", "Minimo", "Rango"]:
            self.calculo_listbox.insert(tk.END, calc)
        ttk.Button(calculo_frame, text="Agregar", 
                  command=lambda: self.add_to_analysis("Cálculos",
                  self.calculo_listbox.get(self.calculo_listbox.curselection()) if self.calculo_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(calculo_frame, text="Agregar Todo", 
                  command=lambda: self.add_all_to_analysis("Cálculos", self.calculo_listbox)).pack(side=tk.LEFT, padx=5)

        # Frame derecho - Lista de análisis
        right_frame = ttk.LabelFrame(params_frame, text="Lista de Análisis")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Pacientes Analysis
        pacientes_analysis_frame = ttk.LabelFrame(right_frame, text="Pacientes")
        pacientes_analysis_frame.pack(fill=tk.X, pady=5)
        self.pacientes_analysis_listbox = tk.Listbox(pacientes_analysis_frame, height=4)
        self.pacientes_analysis_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(pacientes_analysis_frame, text="Eliminar", 
                  command=lambda: self.remove_from_analysis("Pacientes",
                  self.pacientes_analysis_listbox.get(self.pacientes_analysis_listbox.curselection()) if self.pacientes_analysis_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(pacientes_analysis_frame, text="Eliminar Todo", 
                  command=lambda: self.remove_all_from_analysis("Pacientes")).pack(side=tk.LEFT, padx=5)

        # Frecuencia de Medición Analysis
        freq_med_analysis_frame = ttk.LabelFrame(right_frame, text="Frecuencia de Medición")
        freq_med_analysis_frame.pack(fill=tk.X, pady=5)
        self.frecuencia_medicion_analysis_listbox = tk.Listbox(freq_med_analysis_frame, height=4)
        self.frecuencia_medicion_analysis_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(freq_med_analysis_frame, text="Eliminar", 
                  command=lambda: self.remove_from_analysis("Frecuencia de Medición",
                  self.frecuencia_medicion_analysis_listbox.get(self.frecuencia_medicion_analysis_listbox.curselection()) if self.frecuencia_medicion_analysis_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(freq_med_analysis_frame, text="Eliminar Todo", 
                  command=lambda: self.remove_all_from_analysis("Frecuencia de Medición")).pack(side=tk.LEFT, padx=5)

        # Tipo de Prueba Analysis
        tipo_prueba_analysis_frame = ttk.LabelFrame(right_frame, text="Tipo de Prueba")
        tipo_prueba_analysis_frame.pack(fill=tk.X, pady=5)
        self.tipo_prueba_analysis_listbox = tk.Listbox(tipo_prueba_analysis_frame, height=4)
        self.tipo_prueba_analysis_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(tipo_prueba_analysis_frame, text="Eliminar", 
                  command=lambda: self.remove_from_analysis("Tipo de Prueba",
                  self.tipo_prueba_analysis_listbox.get(self.tipo_prueba_analysis_listbox.curselection()) if self.tipo_prueba_analysis_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(tipo_prueba_analysis_frame, text="Eliminar Todo", 
                  command=lambda: self.remove_all_from_analysis("Tipo de Prueba")).pack(side=tk.LEFT, padx=5)

        # Periodo de Prueba Analysis
        periodo_prueba_analysis_frame = ttk.LabelFrame(right_frame, text="Periodo de Prueba")
        periodo_prueba_analysis_frame.pack(fill=tk.X, pady=5)
        self.periodo_prueba_analysis_listbox = tk.Listbox(periodo_prueba_analysis_frame, height=4)
        self.periodo_prueba_analysis_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(periodo_prueba_analysis_frame, text="Eliminar", 
                  command=lambda: self.remove_from_analysis("Periodo de Prueba",
                  self.periodo_prueba_analysis_listbox.get(self.periodo_prueba_analysis_listbox.curselection()) if self.periodo_prueba_analysis_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(periodo_prueba_analysis_frame, text="Eliminar Todo", 
                  command=lambda: self.remove_all_from_analysis("Periodo de Prueba")).pack(side=tk.LEFT, padx=5)

        # Cálculos Analysis
        calculo_analysis_frame = ttk.LabelFrame(right_frame, text="Cálculos")
        calculo_analysis_frame.pack(fill=tk.X, pady=5)
        self.calculo_analysis_listbox = tk.Listbox(calculo_analysis_frame, height=4)
        self.calculo_analysis_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(calculo_analysis_frame, text="Eliminar", 
                  command=lambda: self.remove_from_analysis("Cálculos",
                  self.calculo_analysis_listbox.get(self.calculo_analysis_listbox.curselection()) if self.calculo_analysis_listbox.curselection() else None
                  )).pack(side=tk.LEFT, padx=5)
        ttk.Button(calculo_analysis_frame, text="Eliminar Todo", 
                  command=lambda: self.remove_all_from_analysis("Cálculos")).pack(side=tk.LEFT, padx=5)

        # Frame para botones de acción
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        # Botones de acción
        ttk.Button(action_frame, text="Crear Reporte PDF", 
                  command=lambda: self.crear_reporte_pdf(id_estudio)).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Ver PDF", 
                  command=self.ver_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Eliminar PDF", 
                  command=self.eliminar_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Nuevo Análisis", 
                  command=self.nuevo_analisis).pack(side=tk.LEFT, padx=5)

        # Frame para búsqueda y paginación
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=10)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Buscar", 
                  command=self.buscar_pdf).pack(side=tk.LEFT)

        # Paginación
        self.pagination_frame = ttk.Frame(main_frame)
        self.pagination_frame.pack(fill=tk.X)
        self.update_pdf_pagination()

         # Now define the on_freq_change function and call actualizar_listas_parametros
        def on_freq_change(*args):
            self.actualizar_listas_parametros(id_estudio)

        self.freq_var.trace_add("write", on_freq_change)
        freq_menu = ttk.OptionMenu(freq_frame, self.freq_var, freq_options[0], *freq_options)
        freq_menu.pack(side=tk.LEFT, pady=5)

        # Botón para resetear frecuencia
        ttk.Button(freq_frame, text="Resetear", 
                  command=lambda: self.reset_filter(self.freq_var, freq_options[0])).pack(side=tk.LEFT, padx=5)

        # Cargar datos iniciales
        self.actualizar_listas_parametros(id_estudio)

    def add_to_analysis(self, category, item):
        """Agrega un elemento a la lista de análisis"""
        if item:
            # Map category names to attribute names
            category_map = {
                "Frecuencia de Medición": "frecuencia_medicion",
                "Tipo de Prueba": "tipo_prueba",
                "Periodo de Prueba": "periodo_prueba",
                "Pacientes": "pacientes",
                "Cálculos": "calculo"
            }
            
            attr_name = f"{category_map.get(category, category.lower())}_analysis_listbox"
            analysis_listbox = getattr(self, attr_name)
            
            if item not in analysis_listbox.get(0, tk.END):
                analysis_listbox.insert(tk.END, item)

    def add_all_to_analysis(self, category, source_listbox):
        """Agrega todos los elementos de un listbox a la lista de análisis"""
        items = source_listbox.get(0, tk.END)
        for item in items:
            self.add_to_analysis(category, item)

    def remove_from_analysis(self, category, item):
        """Elimina un elemento de la lista de análisis"""
        if item:
            # Map category names to attribute names
            category_map = {
                "Frecuencia de Medición": "frecuencia_medicion",
                "Tipo de Prueba": "tipo_prueba",
                "Periodo de Prueba": "periodo_prueba",
                "Pacientes": "pacientes",
                "Cálculos": "calculo"
            }
            
            attr_name = f"{category_map.get(category, category.lower())}_analysis_listbox"
            analysis_listbox = getattr(self, attr_name)
            
            selection = analysis_listbox.curselection()
            if selection:
                analysis_listbox.delete(selection)

    def remove_all_from_analysis(self, category):
        """Elimina todos los elementos de una lista de análisis"""
        # Map category names to attribute names
        category_map = {
            "Frecuencia de Medición": "frecuencia_medicion",
            "Tipo de Prueba": "tipo_prueba",
            "Periodo de Prueba": "periodo_prueba",
            "Pacientes": "pacientes",
            "Cálculos": "calculo"
        }
        
        attr_name = f"{category_map.get(category, category.lower())}_analysis_listbox"
        analysis_listbox = getattr(self, attr_name)
        analysis_listbox.delete(0, tk.END)

    def remove_selected_calculation(self):
        """Elimina el cálculo seleccionado de la lista"""
        selection = self.calc_listbox.curselection()
        if selection:
            self.calc_listbox.delete(selection)

    def procesar_datos(self, estudio_path, paciente, frecuencia, tipo, periodo):
        """Procesa los datos de un archivo específico"""
        # Construir la ruta del archivo
        archivo_path = os.path.join(estudio_path, paciente, frecuencia)
        
        if not os.path.exists(archivo_path):
            print(f"- Directorio no encontrado: {archivo_path}")
            return None
            
        print(f"- Buscando en: {archivo_path}")
        
        # Get all files in directory
        try:
            archivos = os.listdir(archivo_path)
            # Filter files that match our pattern
            archivos_validos = [
                f for f in archivos 
                if f.startswith(f"{paciente} {tipo} {periodo}") and 
                "_" in f and 
                f.split("_")[1] == f"{frecuencia}.txt"
            ]
            
            print(f"- Archivos encontrados: {archivos_validos}")
            
            # Process each matching file
            for nombre in archivos_validos:
                path = os.path.join(archivo_path, nombre)
                print(f"- Procesando: {path}")
                try:
                    valores = []
                    with open(path, 'r') as f:
                        # Skip first 4 lines (headers)
                        for _ in range(4):
                            next(f)
                        
                        # Read values until we find MAXIMO, MINIMO or RANGO
                        for line in f:
                            if any(x in line for x in ["MAXIMO", "MINIMO", "RANGO"]):
                                break
                            try:
                                # Values are separated by semicolons
                                partes = line.strip().split(';')
                                if len(partes) > 2:  # Make sure we have values
                                    # Take third value onwards (first two are indices)
                                    for valor in partes[2:]:
                                        if valor.strip():  # If not empty
                                            valores.append(float(valor))
                            except ValueError:
                                continue
                    
                    if valores:  # If we found valid values
                        return valores
                except Exception as e:
                    print(f"- Error procesando {path}: {str(e)}")
                    continue
            
            print("- No se encontraron datos válidos")
        except Exception as e:
            print(f"- Error listando archivos: {str(e)}")
        
        return None

    def generar_nombre_pdf(self, reporte_id, calculos, frecuencias):
        """Genera el nombre del PDF según el formato especificado"""
        # Fecha actual en formato YYYYMMDD
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Formatear cálculos (ej: "max-min-rango")
        calc_map = {"Maximo": "max", "Minimo": "min", "Rango": "rango"}
        calc_str = "-".join(calc_map[c] for c in calculos)
        
        # Formatear frecuencias
        freq_str = "-".join(frecuencias)
        
        return f"reporte-{reporte_id}_{date_str}_{calc_str}_{freq_str}.pdf"

    def obtener_siguiente_reporte_id(self, reportes_dir):
        """Obtiene el siguiente ID de reporte disponible"""
        if not os.path.exists(reportes_dir):
            return 1
            
        max_id = 0
        for filename in os.listdir(reportes_dir):
            if filename.startswith("reporte-") and filename.endswith(".pdf"):
                try:
                    reporte_id = int(filename.split("_")[0].split("-")[1])
                    max_id = max(max_id, reporte_id)
                except:
                    continue
        return max_id + 1

    def crear_reporte_pdf(self, id_estudio):
            """Crea un reporte PDF con los análisis seleccionados"""
            # Verificar que haya al menos dos pacientes seleccionados
            pacientes = list(self.pacientes_analysis_listbox.get(0, tk.END))
            if len(pacientes) < 2:
                messagebox.showerror("Error", "Debe seleccionar al menos dos pacientes")
                return
                
            if not self.frecuencia_medicion_analysis_listbox.get(0, tk.END):
                messagebox.showerror("Error", "Debe seleccionar al menos una frecuencia de medición")
                return
                
            if not self.tipo_prueba_analysis_listbox.get(0, tk.END):
                messagebox.showerror("Error", "Debe seleccionar al menos un tipo de prueba")
                return
                
            if not self.periodo_prueba_analysis_listbox.get(0, tk.END):
                messagebox.showerror("Error", "Debe seleccionar al menos un periodo de prueba")
                return
                
            if not self.calculo_analysis_listbox.get(0, tk.END):
                messagebox.showerror("Error", "Debe seleccionar al menos un cálculo")
                return

            # Obtener datos seleccionados
            frecuencias = list(self.frecuencia_medicion_analysis_listbox.get(0, tk.END))
            tipos = list(self.tipo_prueba_analysis_listbox.get(0, tk.END))
            periodos = list(self.periodo_prueba_analysis_listbox.get(0, tk.END))
            calculos = list(self.calculo_analysis_listbox.get(0, tk.END))

            # Obtener nombre del estudio
            conn = sqlite3.connect('kineviz.db')
            cursor = conn.cursor()
            cursor.execute('SELECT nombre_estudio FROM estudios WHERE id_estudio = ?', (id_estudio,))
            nombre_estudio = cursor.fetchone()[0]
            conn.close()

            # Crear directorio para PDFs si no existe
            pdf_dir = os.path.join("estudios", nombre_estudio, "reportes")
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)

            # Crear directorio temporal para gráficos si no existe
            temp_dir = os.path.join("estudios", nombre_estudio, "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Obtener siguiente ID de reporte y generar nombre del PDF
            reporte_id = self.obtener_siguiente_reporte_id(pdf_dir)
            pdf_name = self.generar_nombre_pdf(reporte_id, calculos, frecuencias)
            pdf_path = os.path.join(pdf_dir, pdf_name)

            try:
                # Crear PDF
                doc = SimpleDocTemplate(pdf_path, pagesize=letter)
                elements = []
                
                # Estilos
                styles = getSampleStyleSheet()
                title_style = styles['Title']
                heading_style = styles['Heading1']
                heading2_style = styles['Heading2']
                normal_style = styles['Normal']
                
                # Título
                elements.append(Paragraph(f"Reporte de Análisis - {nombre_estudio}", title_style))
                elements.append(Spacer(1, 12))
                
                # Fecha
                elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
                elements.append(Spacer(1, 12))
                
                # Parámetros seleccionados
                elements.append(Paragraph("Parámetros Seleccionados:", heading_style))
                elements.append(Paragraph(f"Pacientes: {', '.join(pacientes)}", normal_style))
                elements.append(Paragraph(f"Frecuencias: {', '.join(frecuencias)}", normal_style))
                elements.append(Paragraph(f"Tipos de Prueba: {', '.join(tipos)}", normal_style))
                elements.append(Paragraph(f"Periodos de Prueba: {', '.join(periodos)}", normal_style))
                elements.append(Paragraph(f"Cálculos: {', '.join(calculos)}", normal_style))
                elements.append(Spacer(1, 12))
                
                # Ruta del estudio
                estudio_path = os.path.join("estudios", nombre_estudio)
                
                # Procesar datos y generar gráficos para cada frecuencia
                for frecuencia in frecuencias:
                    elements.append(Paragraph(f"Análisis para {frecuencia}:", heading_style))
                    elements.append(Spacer(1, 12))
                    
                    # Para cada tipo y periodo
                    for tipo in tipos:
                        for periodo in periodos:
                            elements.append(Paragraph(f"{tipo} - {periodo}", heading2_style))
                            elements.append(Spacer(1, 6))
                            
                            # Recopilar datos para el gráfico
                            datos_pacientes = {}
                            for paciente in pacientes:
                                valores = self.procesar_datos(estudio_path, paciente, frecuencia, tipo, periodo)
                                if valores:
                                    datos_pacientes[paciente] = valores
                            
                            if datos_pacientes:
                                # Crear gráfico de caja (boxplot)
                                plt.figure(figsize=(8, 6))
                                plt.boxplot([datos_pacientes[p] for p in datos_pacientes.keys()],
                                        tick_labels=list(datos_pacientes.keys()))
                                plt.title(f"Boxplot: {tipo} - {periodo}")
                                plt.ylabel("Valores")
                                plt.xticks(rotation=45)
                                
                                # Guardar gráfico temporalmente
                                temp_plot = os.path.join(temp_dir, f"temp_plot_{frecuencia}_{tipo}_{periodo}.png")
                                plt.savefig(temp_plot, bbox_inches='tight', dpi=300)
                                plt.close()
                                
                                # Agregar gráfico al PDF
                                elements.append(Image(temp_plot, width=400, height=300))
                                elements.append(Spacer(1, 12))
                                
                                # Agregar resultados estadísticos y generar gráficos de barras
                                for calculo in calculos:
                                    elements.append(Paragraph(f"Resultados para {calculo}:", normal_style))
                                    
                                    # Calcular valores para el gráfico de barras
                                    medias = []
                                    nombres_pacientes = []
                                    for paciente in datos_pacientes:
                                        valor = self.calcular_estadisticas(datos_pacientes[paciente], calculo)
                                        if valor is not None:
                                            medias.append(valor)
                                            nombres_pacientes.append(paciente)
                                    
                                    if medias:
                                        # Crear gráfico de barras
                                        plt.figure(figsize=(8, 6))
                                        plt.bar(nombres_pacientes, medias)
                                        plt.title(f"Gráfico de Barras - {calculo}\n{tipo} - {periodo}")
                                        plt.xlabel("Pacientes")
                                        plt.ylabel(f"{calculo}")
                                        plt.xticks(rotation=45)
                                        
                                        # Guardar gráfico temporalmente
                                        temp_bar = os.path.join(temp_dir, f"temp_bar_{frecuencia}_{tipo}_{periodo}_{calculo}.png")
                                        plt.savefig(temp_bar, bbox_inches='tight', dpi=300)
                                        plt.close()
                                        
                                        # Agregar gráfico al PDF
                                        elements.append(Image(temp_bar, width=400, height=300))
                                        elements.append(Spacer(1, 12))
                                        
                                        # Agregar resultados numéricos
                                        resultados = []
                                        for paciente, valor in zip(nombres_pacientes, medias):
                                            resultados.append(f"{paciente}: {valor:.2f}")
                                        
                                        if resultados:
                                            elements.append(Paragraph("<br/>".join(resultados), normal_style))
                                        elements.append(Spacer(1, 6))
                            else:
                                elements.append(Paragraph("No hay datos disponibles para esta combinación", normal_style))
                            
                            elements.append(Spacer(1, 12))
                
                # Generar PDF
                doc.build(elements)
                
                # Limpiar archivos temporales
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, file))
                    os.rmdir(temp_dir)
                    
                messagebox.showinfo("Éxito", "Reporte PDF generado correctamente")
                
                # Abrir el PDF
                if messagebox.askyesno("Ver PDF", "¿Desea abrir el PDF generado?"):
                    self.abrir_archivo(pdf_path)
                    
            except Exception as e:
                # Asegurar limpieza de archivos temporales incluso si hay error
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        try:
                            os.remove(os.path.join(temp_dir, file))
                        except:
                            pass
                    try:
                        os.rmdir(temp_dir)
                    except:
                        pass
                messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")

    def ver_pdf(self):
        """Abre el PDF seleccionado"""
        # Obtener el estudio actual
        current_window = self.root.focus_get().winfo_toplevel()
        study_name = current_window.title().replace('Análisis de Estudio - ', '')
        
        # Directorio de reportes
        reportes_dir = os.path.join("estudios", study_name, "reportes")
        if not os.path.exists(reportes_dir):
            messagebox.showerror("Error", "No hay reportes disponibles")
            return
            
        # Listar PDFs disponibles
        pdfs = [f for f in os.listdir(reportes_dir) if f.endswith('.pdf')]
        if not pdfs:
            messagebox.showerror("Error", "No hay reportes disponibles")
            return
            
        # Crear ventana de selección
        select_window = Toplevel(self.root)
        select_window.title('Seleccionar PDF')
        select_window.geometry('800x600')
        
        # Frame principal
        main_frame = ttk.Frame(select_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Frame de búsqueda
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Frame para la tabla
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear tabla
        columns = ('ID', 'Fecha', 'Cálculos', 'Frecuencias', 'Ver')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Configurar columnas
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar tabla y scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def cargar_pdfs(search_term=''):
            # Limpiar tabla
            for item in tree.get_children():
                tree.delete(item)
                
            # Cargar PDFs
            for pdf in pdfs:
                if search_term.lower() in pdf.lower():
                    try:
                        # Extraer información del nombre del archivo
                        parts = pdf.replace('.pdf', '').split('_')
                        reporte_id = parts[0].split('-')[1]
                        fecha = parts[1]
                        calculos = parts[2].replace('-', ', ')
                        frecuencias = parts[3].replace('-', ', ')
                        
                        tree.insert('', tk.END, values=(
                            reporte_id,
                            f"{fecha[:4]}/{fecha[4:6]}/{fecha[6:]}",
                            calculos,
                            frecuencias,
                            'Ver'
                        ), tags=(pdf,))
                    except:
                        continue
        
        def on_search(*args):
            cargar_pdfs(search_var.get())
            
        search_var.trace_add('write', on_search)
        
        def on_tree_click(event):
            region = tree.identify("region", event.x, event.y)
            if region == "cell":
                column = tree.identify_column(event.x)
                if column == "#5":  # Ver
                    item = tree.selection()[0]
                    pdf_name = tree.item(item, "tags")[0]
                    pdf_path = os.path.join(reportes_dir, pdf_name)
                    self.abrir_archivo(pdf_path)
                    select_window.destroy()
        
        tree.bind('<ButtonRelease-1>', on_tree_click)
        
        # Cargar PDFs inicialmente
        cargar_pdfs()
        
        # Frame de paginación
        pagination_frame = ttk.Frame(main_frame)
        pagination_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Obtener configuración de paginación
        items_per_page = int(self.config['SETTINGS']['files_per_page'])
        total_pages = (len(pdfs) // items_per_page) + (1 if len(pdfs) % items_per_page else 0)
        current_page = tk.IntVar(value=1)
        
        def update_pagination():
            # Limpiar botones existentes
            for widget in pagination_frame.winfo_children():
                widget.destroy()
                
            if total_pages > 1:
                ttk.Button(pagination_frame, text="<<", 
                          command=lambda: current_page.set(1)).pack(side=tk.LEFT)
                ttk.Button(pagination_frame, text="<", 
                          command=lambda: current_page.set(max(1, current_page.get() - 1))).pack(side=tk.LEFT)
                
                for page in range(1, total_pages + 1):
                    ttk.Button(pagination_frame, text=str(page),
                             command=lambda p=page: current_page.set(p)).pack(side=tk.LEFT)
                             
                ttk.Button(pagination_frame, text=">",
                          command=lambda: current_page.set(min(total_pages, current_page.get() + 1))).pack(side=tk.LEFT)
                ttk.Button(pagination_frame, text=">>",
                          command=lambda: current_page.set(total_pages)).pack(side=tk.LEFT)
        
        def on_page_change(*args):
            start_idx = (current_page.get() - 1) * items_per_page
            end_idx = start_idx + items_per_page
            cargar_pdfs(search_var.get())
            
        current_page.trace_add('write', on_page_change)
        
        # Actualizar paginación inicial
        update_pagination()

    def calcular_estadisticas(self, valores, calculo):
        """Calcula estadísticas específicas para un conjunto de valores"""
        if not valores:
            return None
            
        if calculo == "Maximo":
            return max(valores)
        elif calculo == "Minimo":
            return min(valores)
        elif calculo == "Rango":
            return max(valores) - min(valores)
        return None

    def generar_pdf(self, pdf_path, nombre_estudio, pacientes, frecuencias, tipos, periodos, calculos):
        """Genera el PDF con los análisis seleccionados"""
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading1']
        heading2_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Título
        elements.append(Paragraph(f"Reporte de Análisis - {nombre_estudio}", title_style))
        elements.append(Spacer(1, 12))
        
        # Fecha
        elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 12))
        
        # Parámetros seleccionados
        elements.append(Paragraph("Parámetros Seleccionados:", heading_style))
        elements.append(Paragraph(f"Pacientes: {', '.join(pacientes)}", normal_style))
        elements.append(Paragraph(f"Frecuencias: {', '.join(frecuencias)}", normal_style))
        elements.append(Paragraph(f"Tipos de Prueba: {', '.join(tipos)}", normal_style))
        elements.append(Paragraph(f"Periodos de Prueba: {', '.join(periodos)}", normal_style))
        elements.append(Paragraph(f"Cálculos: {', '.join(calculos)}", normal_style))
        elements.append(Spacer(1, 12))
        
        # Ruta del estudio
        estudio_path = os.path.join("estudios", nombre_estudio)
        
        # Procesar datos y generar gráficos para cada frecuencia
        for frecuencia in frecuencias:
            elements.append(Paragraph(f"Análisis para {frecuencia}:", heading_style))
            elements.append(Spacer(1, 12))
            
            # Para cada tipo y periodo
            for tipo in tipos:
                for periodo in periodos:
                    elements.append(Paragraph(f"{tipo} - {periodo}", heading2_style))
                    elements.append(Spacer(1, 6))
                    
                    # Recopilar datos para el gráfico
                    datos_pacientes = {}
                    for paciente in pacientes:
                        valores = self.procesar_datos(estudio_path, paciente, frecuencia, tipo, periodo)
                        if valores:
                            datos_pacientes[paciente] = valores
                    
                    if datos_pacientes:
                        # Crear gráfico de caja (boxplot)
                        plt.figure(figsize=(8, 6))
                        plt.boxplot([datos_pacientes[p] for p in datos_pacientes.keys()],
                                  labels=list(datos_pacientes.keys()))
                        plt.title(f"{tipo} - {periodo}")
                        plt.ylabel("Valores")
                        plt.xticks(rotation=45)
                        
                        # Guardar gráfico temporalmente
                        temp_plot = f"temp_plot_{frecuencia}_{tipo}_{periodo}.png"
                        plt.savefig(temp_plot, bbox_inches='tight')
                        plt.close()
                        
                        # Agregar gráfico al PDF
                        elements.append(Image(temp_plot, width=400, height=300))
                        elements.append(Spacer(1, 12))
                        
                        # Eliminar archivo temporal
                        os.remove(temp_plot)
                        
                        # Agregar resultados estadísticos
                        for calculo in calculos:
                            elements.append(Paragraph(f"Resultados para {calculo}:", normal_style))
                            
                            # Tabla de resultados
                            resultados = []
                            for paciente in datos_pacientes:
                                valor = self.calcular_estadisticas(datos_pacientes[paciente], calculo)
                                if valor is not None:
                                    resultados.append(f"{paciente}: {valor:.2f}")
                            
                            if resultados:
                                elements.append(Paragraph("<br/>".join(resultados), normal_style))
                            elements.append(Spacer(1, 6))
                    else:
                        elements.append(Paragraph("No hay datos disponibles para esta combinación", normal_style))
                    
                    elements.append(Spacer(1, 12))
        
        # Generar PDF
        doc.build(elements)

    def eliminar_pdf(self):
        """Elimina el PDF seleccionado"""
        # Obtener el estudio actual
        current_window = self.root.focus_get().winfo_toplevel()
        study_name = current_window.title().replace('Análisis de Estudio - ', '')
        
        # Directorio de reportes
        reportes_dir = os.path.join("estudios", study_name, "reportes")
        if not os.path.exists(reportes_dir):
            messagebox.showerror("Error", "No hay reportes disponibles")
            return
            
        # Listar PDFs disponibles
        pdfs = [f for f in os.listdir(reportes_dir) if f.endswith('.pdf')]
        if not pdfs:
            messagebox.showerror("Error", "No hay reportes disponibles")
            return
            
        # Crear ventana de selección
        select_window = Toplevel(self.root)
        select_window.title('Eliminar PDF')
        select_window.geometry('400x300')
        
        # Lista de PDFs
        listbox = tk.Listbox(select_window)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ordenar PDFs por fecha (más reciente primero)
        pdfs.sort(reverse=True)
        
        for pdf in pdfs:
            listbox.insert(tk.END, pdf)
            
        def eliminar_pdf_seleccionado():
            selection = listbox.curselection()
            if selection:
                pdf_name = listbox.get(selection[0])
                if messagebox.askyesno("Confirmar", f"¿Está seguro de que desea eliminar {pdf_name}?"):
                    pdf_path = os.path.join(reportes_dir, pdf_name)
                    try:
                        os.remove(pdf_path)
                        listbox.delete(selection)
                        messagebox.showinfo("Éxito", "PDF eliminado correctamente")
                        if not listbox.get(0, tk.END):  # Si no quedan PDFs
                            select_window.destroy()
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al eliminar PDF: {str(e)}")
                
        ttk.Button(select_window, text="Eliminar", command=eliminar_pdf_seleccionado).pack(pady=10)

    def buscar_pdf(self):
        """Busca PDFs basado en el término de búsqueda"""
        # Obtener el estudio actual
        current_window = self.root.focus_get().winfo_toplevel()
        study_name = current_window.title().replace('Análisis de Estudio - ', '')
        
        # Directorio de reportes
        reportes_dir = os.path.join("estudios", study_name, "reportes")
        if not os.path.exists(reportes_dir):
            messagebox.showerror("Error", "No hay reportes disponibles")
            return
            
        # Obtener término de búsqueda
        search_term = self.search_var.get().lower()
        
        # Listar PDFs disponibles
        all_pdfs = [f for f in os.listdir(reportes_dir) if f.endswith('.pdf')]
        if not all_pdfs:
            messagebox.showerror("Error", "No hay reportes disponibles")
            return
            
        # Filtrar PDFs según término de búsqueda
        filtered_pdfs = [pdf for pdf in all_pdfs if search_term in pdf.lower()]
        
        # Crear ventana de resultados
        results_window = Toplevel(self.root)
        results_window.title('Resultados de Búsqueda')
        results_window.geometry('400x300')
        
        # Lista de PDFs
        listbox = tk.Listbox(results_window)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ordenar PDFs por fecha (más reciente primero)
        filtered_pdfs.sort(reverse=True)
        
        for pdf in filtered_pdfs:
            listbox.insert(tk.END, pdf)
            
        if not filtered_pdfs:
            ttk.Label(results_window, text="No se encontraron resultados").pack(pady=10)
            
        def abrir_pdf_seleccionado():
            selection = listbox.curselection()
            if selection:
                pdf_name = listbox.get(selection[0])
                pdf_path = os.path.join(reportes_dir, pdf_name)
                self.abrir_archivo(pdf_path)
                results_window.destroy()
                
        ttk.Button(results_window, text="Abrir", command=abrir_pdf_seleccionado).pack(pady=10)

    def update_pdf_pagination(self):
        """Actualiza la paginación de PDFs"""
        # Obtener el estudio actual
        current_window = self.root.focus_get().winfo_toplevel()
        study_name = current_window.title().replace('Análisis de Estudio - ', '')
        
        # Directorio de reportes
        reportes_dir = os.path.join("estudios", study_name, "reportes")
        if not os.path.exists(reportes_dir):
            return
            
        # Listar PDFs disponibles
        pdfs = [f for f in os.listdir(reportes_dir) if f.endswith('.pdf')]
        if not pdfs:
            return
            
        # Limpiar botones existentes
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()
            
        # Calcular número total de páginas
        items_per_page = 10
        total_pages = (len(pdfs) // items_per_page) + (1 if len(pdfs) % items_per_page else 0)
        
        if total_pages > 1:
            # Botones de navegación
            ttk.Button(self.pagination_frame, text="<<", 
                      command=lambda: self.go_to_pdf_page(1)).pack(side=tk.LEFT)
                      
            ttk.Button(self.pagination_frame, text="<", 
                      command=lambda: self.go_to_pdf_page(max(1, self.current_pdf_page - 1))).pack(side=tk.LEFT)
                      
            # Botones de página
            for page in range(1, total_pages + 1):
                ttk.Button(self.pagination_frame, text=str(page),
                          command=lambda p=page: self.go_to_pdf_page(p)).pack(side=tk.LEFT)
                          
            ttk.Button(self.pagination_frame, text=">",
                      command=lambda: self.go_to_pdf_page(min(total_pages, self.current_pdf_page + 1))).pack(side=tk.LEFT)
                      
            ttk.Button(self.pagination_frame, text=">>",
                      command=lambda: self.go_to_pdf_page(total_pages)).pack(side=tk.LEFT)

    def go_to_pdf_page(self, page):
        """Navega a una página específica de PDFs"""
        self.current_pdf_page = page
        self.update_pdf_pagination()

    def nuevo_analisis(self):
        """Limpia todas las selecciones para un nuevo análisis"""
        # Limpiar listas de análisis
        self.pacientes_analysis_listbox.delete(0, tk.END)
        self.frecuencia_medicion_analysis_listbox.delete(0, tk.END)
        self.tipo_prueba_analysis_listbox.delete(0, tk.END)
        self.periodo_prueba_analysis_listbox.delete(0, tk.END)
        self.calculo_analysis_listbox.delete(0, tk.END)
        
        # Resetear filtros
        self.freq_var.set("Todos")

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
                    elif "Cinematica" in root:
                        tipo = "New"
                        frecuencia = "Cinematica"
                    elif "Cinetica" in root:
                        tipo = "New"
                        frecuencia = "Cinetica"
                    elif "Electromiografica" in root:
                        tipo = "New"
                        frecuencia = "Electromiografica"

                    archivos.append((paciente, rel_path, tipo, frecuencia))

        # Aplicar filtros
        search_query = self.search_file_entry.get().lower()
        filter_type = self.filter_type_var.get()

        filtered_archivos = []
        for paciente, archivo, tipo, frecuencia in archivos:
            if (search_query in archivo.lower() or search_query in paciente.lower()) and \
               (filter_type == "Todos" or 
                (filter_type == "Cinematica" and "Cinematica" in archivo) or
                (filter_type == "Cinetica" and "Cinetica" in archivo) or
                (filter_type == "Electromiografica" and "Electromiografica" in archivo) or
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
                    elif "Cinematica" in root:
                        tipo = "New"
                        frecuencia = "Cinematica"
                    elif "Cinetica" in root:
                        tipo = "New"
                        frecuencia = "Cinetica"
                    elif "Electromiografica" in root:
                        tipo = "New"
                        frecuencia = "Electromiografica"

                    archivos.append((paciente, rel_path, tipo, frecuencia))

        # Apply filters
        search_query = self.search_file_entry.get().lower()
        filter_type = self.filter_type_var.get()

        filtered_archivos = []
        for paciente, archivo, tipo, frecuencia in archivos:
            if (search_query in archivo.lower() or search_query in paciente.lower()) and \
               (filter_type == "Todos" or 
                (filter_type == "Cinematica" and "Cinematica" in archivo) or
                (filter_type == "Cinetica" and "Cinetica" in archivo) or
                (filter_type == "Electromiografica" and "Electromiografica" in archivo) or
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
