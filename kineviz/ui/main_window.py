import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Text, Scrollbar
import os
import sys
import subprocess
import shutil
import configparser
from pathlib import Path

# Asumiendo que estos módulos serán creados/adaptados
import tkinter as tk # Asegurar importación base
from tkinter import ttk, messagebox, Toplevel, Text, Scrollbar
import os
import sys
import subprocess
import shutil
import configparser
from pathlib import Path

# Vistas y Diálogos UI
from kineviz.ui.views.landing_page import LandingPage
from kineviz.ui.views.study_view import StudyView
from kineviz.ui.views.main_view import MainView
from kineviz.ui.dialogs.study_dialog import StudyDialog
from kineviz.ui.dialogs.analysis_dialog import AnalysisDialog # Importar el nuevo diálogo
# from kineviz.ui.dialogs.config_dialog import ConfigDialog # (Futuro)
# Servicios Core
from kineviz.core.services.study_service import StudyService
from kineviz.core.services.file_service import FileService # Importar FileService
from kineviz.core.services.analysis_service import AnalysisService # Importar AnalysisService
# from kineviz.config.settings import AppSettings # (Futuro)

# Ya no se necesitan importaciones temporales del repositorio
# from kineviz.database.repositories import StudyRepository # Usar StudyService en su lugar

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title('KineViz')
        self.root.geometry('1000x600') # Tamaño por defecto de interfaz.py

        # --- Carga de Configuración (Adaptado de load_config) ---
        # self.settings = AppSettings() # Idealmente usar una clase de configuración
        self.config = configparser.ConfigParser()
        self.estudios_por_pagina = 10 # Valor por defecto
        self.files_per_page = 10 # Valor por defecto
        self.pdfs_per_page = 10 # Valor por defecto
        try:
            # Asume que config.ini está en el directorio raíz del proyecto
            # Si app.py está en kineviz/, necesitamos ir un nivel arriba
            project_root_dir = Path(__file__).resolve().parent.parent.parent
            config_path = project_root_dir / 'config.ini'

            if config_path.exists():
                self.config.read(config_path)
                self.estudios_por_pagina = int(self.config.get('SETTINGS', 'estudios_por_pagina', fallback=10))
                self.files_per_page = int(self.config.get('SETTINGS', 'files_per_page', fallback=10))
                self.pdfs_per_page = int(self.config.get('SETTINGS', 'pdfs_per_page', fallback=10))
            else:
                # Crear config.ini si no existe (opcional, pero útil)
                print(f"Advertencia: No se encontró {config_path}. Creando archivo con valores por defecto.")
                self.config['SETTINGS'] = {
                    'estudios_por_pagina': '10',
                    'files_per_page': '10',
                    'pdfs_per_page': '10'
                }
                # Asegurarse de que el directorio config exista si es necesario
                # config_path.parent.mkdir(exist_ok=True) # Descomentar si config.ini va en /config
                with open(config_path, 'w') as configfile:
                    self.config.write(configfile)
        except Exception as e:
            messagebox.showerror("Error de Configuración", f"No se pudo cargar 'config.ini': {str(e)}\nUsando valores por defecto.")
            # Usar valores por defecto ya establecidos

        # --- Instanciación de Servicios ---
        self.study_service = StudyService() # Servicio para operaciones de estudios (DB, carpetas base)
        # Pasar study_service a FileService para que pueda obtener nombres/rutas de estudios
        self.file_service = FileService(self.study_service) # Servicio para operaciones de archivos dentro de estudios
        self.analysis_service = AnalysisService() # Servicio para lógica de análisis y reportes

        self.current_view = None
        self.style = ttk.Style()
        self.configure_styles()

        # --- Configuración Inicial de DB (Adaptado de setup_database) ---
        # Esto ahora debería ser manejado por el StudyRepository en su __init__
        # self.setup_database() # Ya no es necesario llamar explícitamente aquí

        # --- Decidir Vista Inicial (Adaptado de __init__) ---
        if self.study_service.has_studies(): # Necesita método has_studies en StudyService
             self.show_main_view() # Mostrar vista principal si hay estudios
        else:
             self.show_landing_page() # Mostrar landing page si no hay estudios

    def configure_styles(self):
        """Configura estilos globales para la aplicación."""
        # Intentar usar un tema moderno si está disponible
        available_themes = self.style.theme_names()
        if 'clam' in available_themes:
            self.style.theme_use('clam')
        elif 'alt' in available_themes:
            self.style.theme_use('alt')
        elif 'default' in available_themes:
            self.style.theme_use('default')

        self.style.configure('TButton', padding=6, font=('Helvetica', 10), relief="flat")
        self.style.map('TButton',
                       foreground=[('pressed', 'red'), ('active', 'blue')],
                       background=[('pressed', '!disabled', 'lightgrey'), ('active', 'white')]) # Ajustar colores
        self.style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'))
        self.style.configure('Header.TLabel', font=('Helvetica', 24, 'bold')) # Estilo para header
        self.style.configure('TLabel', font=('Helvetica', 12))
        self.style.configure('TLabelframe.Label', font=('Helvetica', 12, 'bold')) # Estilo para títulos de LabelFrame
        self.style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold')) # Estilo para cabeceras de Treeview
        # Añadir más configuraciones de estilo según sea necesario

    def clear_window(self):
        """Limpia la ventana principal antes de mostrar una nueva vista."""
        # Destruir vista actual si existe y tiene método destroy
        if self.current_view and hasattr(self.current_view, 'destroy'):
            try:
                self.current_view.destroy()
            except tk.TclError:
                # Ignorar error si el widget ya fue destruido (puede pasar en refrescos rápidos)
                pass
        # Limpiar widgets hijos directos de root
        for widget in self.root.winfo_children():
            widget.destroy()
        self.current_view = None

    def show_landing_page(self):
        """Muestra la página de bienvenida/inicio."""
        self.clear_window()
        # LandingPage necesita ser adaptada para recibir MainWindow y usar sus métodos
        self.current_view = LandingPage(self.root, self)
        # El pack/grid debe hacerse dentro de LandingPage

    def show_main_view(self):
        """Muestra la vista principal con la lista de estudios."""
        self.clear_window()
        # Instanciar y mostrar la MainView real
        self.current_view = MainView(self.root, self)
        # El empaquetado/grid se maneja dentro de MainView.__init__


    def show_study_view(self, study_id: int):
        """Muestra la vista detallada de un estudio específico."""
        self.clear_window()
        # Pasar la instancia de file_service a StudyView
        self.current_view = StudyView(self.root, self, study_id, self.file_service)
        # El pack/grid se maneja dentro de StudyView

    def show_create_study_dialog(self, study_to_edit=None):
        """
        Muestra el diálogo para crear o editar un estudio.
        Llama a refresh_main_view cuando se guarda exitosamente.
        """
        # StudyDialog necesita ser adaptada para manejar la edición
        # y aceptar un callback
        # Pasar el callback como argumento nombrado
        StudyDialog(self.root, self.study_service, study_to_edit=study_to_edit, on_save_callback=self.refresh_main_view)

    def show_analysis_dialog(self, study_id: int):
        """Muestra el diálogo para realizar análisis en un estudio."""
        # Instanciar y mostrar el AnalysisDialog real
        # Pasarle el servicio de análisis y el ID del estudio
        AnalysisDialog(self.root, self.analysis_service, study_id)
        # Ya no se necesita el messagebox de placeholder


    def show_config_dialog(self):
        """Muestra el diálogo de configuración."""
        # ConfigDialog necesita ser creada
        # ConfigDialog(self.root, self.settings, self.reset_to_defaults)
        messagebox.showinfo("Información", "Mostrar diálogo de configuración (Por implementar)")


    def refresh_main_view(self):
        """
        Refresca la vista principal (útil después de crear/editar/eliminar estudio).
        Decide qué vista mostrar basado en si hay estudios.
        """
        # Verificar si hay estudios ANTES de decidir qué vista mostrar
        has_studies_now = self.study_service.has_studies()

        # Si estamos en la vista principal o si ahora hay estudios donde antes no había,
        # o si ya no hay estudios donde antes sí había, refrescamos.
        # Esto evita refrescos innecesarios si se crea un estudio desde la landing page
        # y ya había otros estudios.

        # Necesitamos una forma de saber cuál es la vista actual.
        # Por ahora, simplemente decidimos basado en si hay estudios.
        if has_studies_now:
            self.show_main_view()
        else:
            self.show_landing_page()


    # --- Métodos de Ayuda y Utilidades (Adaptados de KineVizApp) ---

    def show_welcome_message(self):
        """Muestra el mensaje de bienvenida."""
        messagebox.showinfo("Introducción",
                          "Bienvenido a KineViz. Esta es una aplicación para la gestión y análisis de estudios kinesiológicos.")

    def open_user_manual(self):
        """Abre y muestra el manual de usuario."""
        manual_window = Toplevel(self.root)
        manual_window.title('Manual de Usuario')
        manual_window.geometry('800x600')
        # Asume que manual_usuario.txt está en el directorio raíz del proyecto
        project_root_dir = Path(__file__).resolve().parent.parent.parent
        manual_path = project_root_dir / 'manual_usuario.txt'

        try:
            if manual_path.exists():
                with open(manual_path, 'r', encoding='utf-8') as file:
                    manual_content = file.read()
            else:
                manual_content = f"Manual de usuario ('{manual_path.name}') no encontrado en '{project_root_dir}'."
        except Exception as e:
            manual_content = f"Error al leer el manual de usuario: {str(e)}"

        text_widget = Text(manual_window, wrap='word', relief='flat', bd=0, padx=10, pady=10)
        text_widget.insert('1.0', manual_content)
        text_widget.config(state='disabled') # Hacerlo no editable

        scrollbar = Scrollbar(manual_window, command=text_widget.yview, relief='flat', bd=0)
        text_widget.config(yscrollcommand=scrollbar.set)

        # Usar grid para mejor control del layout
        manual_window.grid_rowconfigure(0, weight=1)
        manual_window.grid_columnconfigure(0, weight=1)
        text_widget.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        # Centrar la ventana hija en la principal
        manual_window.transient(self.root)
        manual_window.grab_set()
        # No esperar aquí para no bloquear la ventana principal
        # self.root.wait_window(manual_window)


    def open_folder(self, folder_path_str):
        """Abre la carpeta especificada en el explorador de archivos."""
        # Asegurarse de que la ruta base sea relativa al directorio del proyecto
        project_root_dir = Path(__file__).resolve().parent.parent.parent
        # Usar Path para construir la ruta de forma segura
        folder_path = project_root_dir / Path(folder_path_str)
        try:
            if not folder_path.exists():
                # Preguntar al usuario si desea crear la carpeta? O simplemente crearla?
                # Por ahora, la creamos silenciosamente si no existe.
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"Carpeta creada: {folder_path}") # Log para debugging

            print(f"Intentando abrir: {folder_path}") # Log para debugging

            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin': # macOS
                # Usar subprocess.run para mejor manejo de errores
                subprocess.run(['open', folder_path], check=True)
            else: # Linux, etc.
                # Usar subprocess.run para mejor manejo de errores
                subprocess.run(['xdg-open', folder_path], check=True)
        except FileNotFoundError:
             messagebox.showerror("Error", f"No se pudo encontrar la carpeta:\n'{folder_path}'")
        except PermissionError:
             messagebox.showerror("Error", f"No tiene permisos para acceder a la carpeta:\n'{folder_path}'")
        except subprocess.CalledProcessError as e:
             messagebox.showerror("Error", f"El comando para abrir la carpeta falló:\n{e}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta '{folder_path}':\n{str(e)}")

    def reset_to_defaults(self):
        """Restablece la aplicación a su estado inicial."""
        if messagebox.askyesno("Confirmar Restablecimiento", "¿Está seguro de que desea restablecer los valores por defecto?\n\nEsta acción eliminará permanentemente:\n- Todos los estudios y sus archivos asociados.\n- Todos los reportes generados.\n- La base de datos completa.\n\nEsta acción no se puede deshacer.", icon='warning'):
            try:
                # Obtener rutas desde una fuente central si es posible (e.g., config o servicio)
                project_root_dir = Path(__file__).resolve().parent.parent.parent
                # Asegurarse de que db_path sea absoluto o relativo a project_root_dir
                db_path_str = self.study_service.repo.db_path
                db_path = Path(db_path_str)
                if not db_path.is_absolute():
                    db_path = project_root_dir / db_path_str

                studies_base_dir = project_root_dir / "estudios" # Asumiendo que está en la raíz

                print(f"Eliminando base de datos: {db_path}")
                if db_path.exists():
                    db_path.unlink()
                else:
                    print("Base de datos no encontrada, omitiendo eliminación.")

                print(f"Eliminando directorio de estudios: {studies_base_dir}")
                if studies_base_dir.exists() and studies_base_dir.is_dir():
                    shutil.rmtree(studies_base_dir)
                else:
                    print("Directorio de estudios no encontrado, omitiendo eliminación.")

                # Recrear la base de datos y la carpeta de estudios
                print("Recreando estructura inicial...")
                # Asegurarse de que el directorio para la DB exista si es necesario
                db_path.parent.mkdir(parents=True, exist_ok=True)
                self.study_service.repo._create_tables() # Llama al método privado para recrear tablas
                studies_base_dir.mkdir(exist_ok=True)

                messagebox.showinfo("Éxito", "Valores por defecto restablecidos correctamente.")
                self.show_landing_page() # Volver a la landing page
            except Exception as e:
                # Imprimir traceback para más detalles en la consola
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Error durante el restablecimiento:\n{str(e)}")
