import tkinter as tk # Asegurar importación base
from tkinter import ttk, messagebox, Toplevel, Text, Scrollbar
import os
import sys
import subprocess
import shutil
import configparser
import logging # Importar logging
from pathlib import Path

# Vistas y Diálogos UI
from kineviz.ui.views.landing_page import LandingPage
from kineviz.ui.views.study_view import StudyView
from kineviz.ui.views.main_view import MainView
from kineviz.ui.dialogs.study_dialog import StudyDialog
# from kineviz.ui.dialogs.analysis_dialog import AnalysisDialog
from kineviz.ui.dialogs.config_dialog import ConfigDialog
# ContinuousAnalysisConfigDialog is now opened by ContinuousAnalysisManagerDialog
# from kineviz.ui.dialogs.continuous_analysis_config_dialog import ContinuousAnalysisConfigDialog 
from kineviz.ui.dialogs.continuous_analysis_manager_dialog import ContinuousAnalysisManagerDialog # Import new manager dialog
from kineviz.ui.dialogs.comment_dialog import CommentDialog # Importar CommentDialog
from kineviz.ui.views.discrete_analysis_view import DiscreteAnalysisView
# ContinuousAnalysisView will be removed
# from kineviz.ui.views.continuous_analysis_view import ContinuousAnalysisView 
# Servicios Core
from kineviz.core.services.study_service import StudyService
from kineviz.core.services.file_service import FileService
from kineviz.core.services.analysis_service import AnalysisService
from kineviz.config.settings import AppSettings # get_resource_path will no longer be used for DB path
from kineviz.core.undo_manager import UndoManager, DB_FILENAME # Import UndoManager and DB_FILENAME
from kineviz.ui.utils import style as app_style # Import the style utility
from kineviz.utils.paths import get_application_base_dir # Import for base directory

logger = logging.getLogger(__name__) # Logger para este módulo

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title('KineViz')
        self.root.geometry('1000x600')

        # --- Carga de Configuración usando AppSettings ---
        self.settings = AppSettings() # Instanciar AppSettings
        # Acceder a las configuraciones a través de las propiedades de AppSettings
        self.estudios_por_pagina = self.settings.studies_per_page
        self.files_per_page = self.settings.files_per_page
        self.analysis_items_per_page = self.settings.analysis_items_per_page # Renamed
        self.font_scale = self.settings.font_scale
        self.app_theme = self.settings.theme
        # Ya no necesitamos el objeto self.config ni el bloque try/except aquí

        # --- Instanciación de Servicios ---
        # Determine db_path for UndoManager.
        # DB_FILENAME is imported from kineviz.core.undo_manager
        app_base_dir = get_application_base_dir()
        db_path_for_undo = app_base_dir / DB_FILENAME
        self.undo_manager = UndoManager(settings=self.settings, study_repository_db_path=str(db_path_for_undo))

        self.study_service = StudyService(settings=self.settings, undo_manager=self.undo_manager)
        self.file_service = FileService(self.study_service, settings=self.settings) # Pass settings
        # Pasar settings y undo_manager a AnalysisService
        self.analysis_service = AnalysisService(
            study_service=self.study_service,
            file_service=self.file_service,
            settings=self.settings,
            undo_manager=self.undo_manager
        )
        
        # Clear undo cache if timed out on application startup
        self.undo_manager.clear_undo_cache_if_timed_out()

        self.current_view = None
        self.style = ttk.Style()
        self.restart_pending = False # Flag para controlar el reinicio de la aplicación
        # self.configure_styles() # Will be called by apply_application_styles
        self.apply_application_styles() # Apply theme and font scale on init

        # --- Configuración Inicial de DB (Adaptado de setup_database) ---
        # Esto ahora debería ser manejado por el StudyRepository en su __init__
        # self.setup_database() # Ya no es necesario llamar explícitamente aquí

        # --- Crear Menú ---
        self._create_menubar()

        # --- Setup Window Close Protocol ---
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # --- Decidir Vista Inicial (Adaptado de __init__) ---
        if self.study_service.has_studies(): # Necesita método has_studies en StudyService
             self.show_main_view() # Mostrar vista principal si hay estudios
        else:
             self.show_landing_page() # Mostrar landing page si no hay estudios

    def _create_menubar(self):
        """Crea la barra de menú principal de la aplicación."""
        menubar = tk.Menu(self.root)

        # --- Menú Archivo ---
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Configuración...", command=self.show_config_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._on_close) # Use _on_close for consistent shutdown
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # --- Menú Editar ---
        self.edit_menu = tk.Menu(menubar, tearoff=0) # Store as self.edit_menu
        # The "Deshacer" command will be managed by update_undo_menu_state
        menubar.add_cascade(label="Editar", menu=self.edit_menu)
        
        # --- Menú Ayuda ---
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Manual de Usuario", command=self.open_user_manual)
        help_menu.add_command(label="Acerca de...", command=self._show_about_dialog)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.root.config(menu=menubar)

    def _show_about_dialog(self):
        """Muestra un diálogo simple 'Acerca de...'."""
        messagebox.showinfo(
            "Acerca de KineViz",
            "KineViz - Aplicación para Gestión y Análisis Kinesiológico\n\n"
            "Versión: 2.0\n" # Puedes actualizar esto según sea necesario
            "Creado por: Matías Alevropulos",
            parent=self.root
        )

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

        self.style.configure('TButton', padding=6, font=('Helvetica', 10), relief="raised", borderwidth=1) # Added borderwidth for clarity
        self.style.map('TButton',
                       foreground=[('pressed', 'red'), ('active', 'blue')],
                       background=[('pressed', '!disabled', 'lightgrey'), ('active', 'white')]) # Ajustar colores
        self.style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'))
        self.style.configure('Header.TLabel', font=('Helvetica', 24, 'bold')) # Estilo para header
        self.style.configure('TLabel', font=('Helvetica', 12))
        self.style.configure('TLabelframe.Label', font=('Helvetica', 12, 'bold')) # Estilo para títulos de LabelFrame
        self.style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold')) # Estilo para cabeceras de Treeview
        self.style.configure("Help.TButton", foreground="white", background="blue") # Estilo para botones de ayuda
        self.style.configure("Danger.TButton", foreground="white", background="red") # Asegurar que Danger exista
        self.style.configure("Green.TButton", foreground="white", background="green")
        self.style.configure("Celeste.TButton", foreground="black", background="#AFEEEE") # Light pale turquoise
        # Añadir más configuraciones de estilo según sea necesario

        # The core styling is now handled by app_style.apply_theme_and_font
        # This method can be kept for very specific MainWindow-only tweaks if needed,
        # or eventually removed if all styling is centralized in style.py.
        # For now, ensure it's called correctly by apply_application_styles.
        pass


    def apply_application_styles(self):
        """Aplica el tema y la escala de fuente a toda la aplicación."""
        logger.info(f"Applying theme: {self.app_theme}, font scale: {self.font_scale}")
        app_style.apply_theme_and_font(self.root, self.style, self.app_theme, self.font_scale)
        # Call the original configure_styles if it contains additional specific styles
        # not covered by the global theme application.
        # self.configure_styles() # Or integrate its contents into apply_theme_and_font

        # For Tkinter non-ttk widgets, one might need to apply settings directly,
        # e.g. self.root.configure(bg=app_style.THEMES[self.app_theme]['bg'])
        # However, KineViz primarily uses ttk.

        # Force UI update if necessary, though usually Tkinter handles this.
        # self.root.update_idletasks()


    def clear_window(self):
        """Limpia la ventana principal antes de mostrar una nueva vista."""
        if self.root is None:
            logger.info("MainWindow.clear_window: Root window is None. Skipping clear.")
            return
        # Destruir vista actual si existe y tiene método destroy
        if self.current_view and hasattr(self.current_view, 'destroy'):
            try:
                self.current_view.destroy()
            except tk.TclError:
                # Ignorar error si el widget ya fue destruido (puede pasar en refrescos rápidos)
                pass
        # La línea "for widget in self.root.winfo_children(): widget.destroy()"
        # fue eliminada porque destruía el menú y otros elementos persistentes.
        # Se asume que self.current_view.destroy() limpia adecuadamente su propio frame.
        self.current_view = None

    def show_landing_page(self):
        """Muestra la página de bienvenida/inicio."""
        self.clear_window()
        # LandingPage necesita ser adaptada para recibir MainWindow y usar sus métodos
        self.current_view = LandingPage(self.root, self)
        # El pack/grid debe hacerse dentro de LandingPage
        self.update_undo_menu_state() # Update undo state when view changes

    def show_main_view(self):
        """Muestra la vista principal con la lista de estudios."""
        self.clear_window()
        # Instanciar y mostrar la MainView real
        self.current_view = MainView(self.root, self)
        # El empaquetado/grid se maneja dentro de MainView.__init__
        self.update_undo_menu_state() # Update undo state when view changes


    def show_study_view(self, study_id: int):
        """Muestra la vista detallada de un estudio específico."""
        self.clear_window()
        # Pasar la instancia de file_service a StudyView
        self.current_view = StudyView(self.root, self, study_id, self.file_service)
        # El pack/grid se maneja dentro de StudyView
        self.update_undo_menu_state() # Update undo state when view changes

    def show_backup_restore_dialog_from_landing(self):
        """Muestra el diálogo de gestión de copias de seguridad, invocado desde la landing page."""
        # Similar a show_config_dialog, pero para BackupRestoreDialog
        # BackupRestoreDialog needs AppSettings
        from kineviz.ui.dialogs.backup_restore_dialog import BackupRestoreDialog # Local import
        dialog = BackupRestoreDialog(self.root, app_settings=self.settings)
        self.root.wait_window(dialog) # Make it modal

        if hasattr(dialog, 'restart_required_after_restore') and dialog.restart_required_after_restore:
            logger.info("BackupRestoreDialog (from landing) indicated a restart is required. Triggering app restart.")
            self.trigger_app_restart()

    def play_demo_video(self):
        """Intenta reproducir el archivo DEMO.mp4 ubicado en kineviz/assets/."""
        from kineviz.config.settings import get_resource_path # Local import
        
        demo_video_relative_path = Path("kineviz") / "assets" / "DEMO.mp4"
        video_path = get_resource_path(demo_video_relative_path)

        if not video_path.exists() or not video_path.is_file():
            logger.error(f"Archivo DEMO.mp4 no encontrado en la ruta esperada: {video_path}")
            messagebox.showerror("Error", f"El archivo DEMO.mp4 no se encontró en:\n{video_path}", parent=self.root)
            return

        try:
            logger.info(f"Intentando reproducir video DEMO: {video_path}")
            if sys.platform == 'win32':
                os.startfile(video_path)
            elif sys.platform == 'darwin': # macOS
                subprocess.run(['open', str(video_path)], check=True)
            else: # Linux, etc.
                subprocess.run(['xdg-open', str(video_path)], check=True)
        except FileNotFoundError:
             messagebox.showerror("Error", f"No se pudo encontrar el archivo del video DEMO:\n'{video_path}'", parent=self.root)
             logger.error(f"Archivo del video DEMO no encontrado al intentar abrir: {video_path}", exc_info=True)
        except PermissionError:
             messagebox.showerror("Error", f"No tiene permisos para acceder al archivo del video DEMO:\n'{video_path}'", parent=self.root)
             logger.error(f"Permiso denegado al abrir el video DEMO: {video_path}", exc_info=True)
        except subprocess.CalledProcessError as e:
             logger.error(f"Comando para abrir el video DEMO {video_path} falló: {e}", exc_info=True)
             messagebox.showerror("Error", f"El comando para abrir el video DEMO falló:\n{e}", parent=self.root)
        except Exception as e:
            logger.error(f"Error inesperado al abrir el video DEMO {video_path}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir el video DEMO '{video_path}':\n{str(e)}", parent=self.root)

    def show_discrete_analysis_view(self, study_id: int):
        """Muestra la vista para el análisis discreto (Fase 6)."""
        self.clear_window()
        # Pasar main_window, analysis_service, study_id y settings
        self.current_view = DiscreteAnalysisView(self.root, self, self.analysis_service, study_id, settings=self.settings)
        # El pack/grid se maneja dentro de DiscreteAnalysisView
        self.update_undo_menu_state() # Update undo state when view changes

    def show_continuous_analysis_manager_dialog(self, study_id: int):
        """Muestra el diálogo para gestionar análisis continuos."""
        # No limpia la ventana principal, es un diálogo Toplevel
        ContinuousAnalysisManagerDialog(self.root, self.analysis_service, study_id, main_window_instance=self)
        # El diálogo se gestiona a sí mismo.

    def show_create_study_dialog(self, study_to_edit=None):
        """
        Muestra el diálogo para crear o editar un estudio.
        Llama a refresh_main_view cuando se guarda exitosamente.
        """
        # StudyDialog necesita ser adaptada para manejar la edición
        # y aceptar un callback
        # Pasar el callback como argumento nombrado
        StudyDialog(self.root, self.study_service, self.settings, study_to_edit=study_to_edit, on_save_callback=self.refresh_main_view)

    def show_comment_dialog(self, study_id: int, study_name: str):
        """Muestra el diálogo para añadir/editar un comentario de estudio."""
        try:
            current_comment = self.study_service.get_study_comment(study_id)
            CommentDialog(self.root, self.settings, study_id, study_name, current_comment, self.study_service, on_save_callback=self.refresh_main_view)
        except Exception as e:
            logger.error(f"Error al preparar diálogo de comentario para estudio {study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir el diálogo de comentarios:\n{e}", parent=self.root)


    def show_analysis_dialog(self, study_id: int):
        """Muestra el diálogo para realizar análisis en un estudio."""
        # Instanciar y mostrar el AnalysisDialog real
        # Pasarle el servicio de análisis, el ID del estudio y los settings
        # AnalysisDialog(self.root, self.analysis_service, study_id, self.settings) # Comentado si ya no se usa
        # En su lugar, o adicionalmente, podríamos tener diálogos más específicos.
        # Por ahora, este método puede quedar como estaba o ser eliminado si AnalysisDialog ya no se usa.
        messagebox.showinfo("Información", "La funcionalidad 'Analizar Estudio' (antigua) ha sido reemplazada por 'Análisis Discreto' y 'Análisis Continuo'.")


    def show_config_dialog(self):
        """Muestra el diálogo de configuración."""
        # Pasar la instancia de AppSettings y el método de reseteo como callback
        dialog = ConfigDialog(self.root, self.settings, reset_callback=self.reset_to_defaults)
        # El diálogo se encargará de guardar los settings si el usuario presiona "Guardar"
        # Esperar a que el diálogo se cierre antes de continuar
        self.root.wait_window(dialog)
        # Recargar settings en MainWindow después de cerrar el diálogo (por si cambiaron)
        self.reload_settings()

    def reload_settings(self):
        """Recarga las configuraciones desde AppSettings."""
        if self.root is None:
            logger.info("MainWindow.reload_settings: Root window is None (likely app closing/restarting). Skipping reload.")
            return
        # No es necesario recargar el archivo, AppSettings lo maneja.
        # Solo actualizar las variables de MainWindow si es necesario.
        self.estudios_por_pagina = self.settings.studies_per_page
        self.files_per_page = self.settings.files_per_page
        self.analysis_items_per_page = self.settings.analysis_items_per_page # Renamed
        self.font_scale = self.settings.font_scale
        self.app_theme = self.settings.theme
        
        # Only apply styles if not in the middle of a restart sequence and root is valid
        if not self.restart_pending and self.root:
            self.apply_application_styles() # Re-apply styles
        elif self.root is None:
            logger.info("MainWindow.reload_settings: Root is None, skipping style application.")
        else: # restart_pending is true
            logger.info("MainWindow.reload_settings: Reinicio pendiente, omitiendo re-aplicación de estilos.")
        
        # Podríamos necesitar refrescar la vista actual si la paginación cambió
        # o si el cambio de tema/fuente requiere recrear widgets.
        # For now, a full refresh of the current view might be the simplest
        # way to ensure changes are visible, though it's a bit heavy.
        if self.root: # Only refresh if root is still valid
            self.refresh_current_view_after_settings_change()
        else:
            logger.info("MainWindow.reload_settings: Root is None, skipping view refresh after settings change.")


    def refresh_current_view_after_settings_change(self):
        """Refreshes the current view to apply style changes."""
        if self.root is None:
            logger.info("MainWindow.refresh_current_view_after_settings_change: Root window is None. Skipping view refresh.")
            return

        if self.current_view:
            if isinstance(self.current_view, MainView):
                self.show_main_view()
            elif isinstance(self.current_view, StudyView):
                # StudyView needs study_id. Assume it's stored if we need to refresh it.
                # This might require self.current_study_id to be tracked.
                if hasattr(self.current_view, 'study_id'):
                    self.show_study_view(self.current_view.study_id)
                else:
                    logger.warning("Cannot refresh StudyView: study_id not found on current_view.")
                    self.show_main_view() # Fallback
            elif isinstance(self.current_view, DiscreteAnalysisView):
                if hasattr(self.current_view, 'study_id'):
                    self.show_discrete_analysis_view(self.current_view.study_id)
                else:
                    logger.warning("Cannot refresh DiscreteAnalysisView: study_id not found on current_view.")
                    self.show_main_view() # Fallback
            elif isinstance(self.current_view, LandingPage):
                self.show_landing_page()
            else:
                # For other views, or if a generic refresh is preferred:
                logger.info(f"Refreshing view of type: {type(self.current_view)}. Defaulting to main view if no specific refresh path.")
                self.show_main_view() # Fallback, or implement more specific refreshes
        self.update_undo_menu_state() # Update undo state after view refresh


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
        self.update_undo_menu_state() # Update undo state after main view refresh


    # --- Métodos de Ayuda y Utilidades (Adaptados de KineVizApp) ---

    def show_welcome_message(self):
        """Muestra el mensaje de bienvenida inicial con las opciones disponibles."""
        messagebox.showinfo(
            "Bienvenido a KineViz",
            "KineViz - Sistema de gestión y análisis de estudios kinesiológicos\n\n"
            "Creado por: Matías Alevropulos\n\n"
            "Opciones de inicio:\n"
            "1. Ver DEMO interactivo\n"
            "2. Consultar manual de usuario\n"
            "3. Crear nuevo estudio\n"
            "4. Restaurar desde una copia de seguridad\n"
            "📌 Busque los iconos '?' para ayuda contextual\n\n"
            "¡Gracias por elegir KineViz!"
        )

    def open_user_manual(self):
        """Abre el manual de usuario con la aplicación predeterminada del sistema."""
        # Asume que manual_usuario.txt está en .../KineViz/kineviz/docs/help
        project_root_dir = Path(__file__).resolve().parent.parent.parent
        manual_path = project_root_dir / 'kineviz' / 'docs' / 'help' / 'manual_usuario.txt'

        if not manual_path.exists():
            messagebox.showerror("Error", f"Manual de usuario no encontrado en:\n'{manual_path}'", parent=self.root)
            logger.error(f"Manual de usuario no encontrado: {manual_path}")
            return

        try:
            logger.info(f"Intentando abrir manual de usuario: {manual_path}")
            if sys.platform == 'win32':
                os.startfile(manual_path)
            elif sys.platform == 'darwin': # macOS
                subprocess.run(['open', str(manual_path)], check=True) # Ensure manual_path is string for subprocess
            else: # Linux, etc.
                subprocess.run(['xdg-open', str(manual_path)], check=True) # Ensure manual_path is string for subprocess
        except FileNotFoundError: # Should be caught by the initial check, but good for safety
             messagebox.showerror("Error", f"No se pudo encontrar el archivo del manual:\n'{manual_path}'", parent=self.root)
             logger.error(f"Archivo del manual no encontrado al intentar abrir: {manual_path}", exc_info=True)
        except PermissionError:
             messagebox.showerror("Error", f"No tiene permisos para acceder al archivo del manual:\n'{manual_path}'", parent=self.root)
             logger.error(f"Permiso denegado al abrir el manual: {manual_path}", exc_info=True)
        except subprocess.CalledProcessError as e:
             logger.error(f"Comando para abrir el manual {manual_path} falló: {e}", exc_info=True)
             messagebox.showerror("Error", f"El comando para abrir el manual falló:\n{e}", parent=self.root)
        except Exception as e:
            logger.error(f"Error inesperado al abrir el manual {manual_path}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir el manual '{manual_path}':\n{str(e)}", parent=self.root)


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
                logger.info(f"Carpeta creada: {folder_path}")

            logger.info(f"Intentando abrir carpeta: {folder_path}")

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
             logger.error(f"Comando para abrir carpeta {folder_path} falló: {e}", exc_info=True)
             messagebox.showerror("Error", f"El comando para abrir la carpeta falló:\n{e}")
        except Exception as e:
            logger.error(f"Error inesperado al abrir carpeta {folder_path}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo abrir la carpeta '{folder_path}':\n{str(e)}")

    def reset_to_defaults(self):
        """Restablece la aplicación a su estado inicial."""
        if messagebox.askyesno("Confirmar Restablecimiento", "¿Está seguro de que desea restablecer los valores por defecto?\n\nEsta acción eliminará permanentemente:\n- Todos los estudios y sus archivos asociados.\n- Todos los reportes generados.\n- La base de datos completa.\n- Todas las configuraciones personalizadas.\n\nEsta acción no se puede deshacer.", icon='warning'):
            try:
                app_base_dir = get_application_base_dir()
                # DB_FILENAME is imported from kineviz.core.undo_manager
                db_path = app_base_dir / DB_FILENAME
                studies_base_dir = app_base_dir / "estudios" # STUDIES_DIR_NAME from backup_manager

                logger.warning(f"Iniciando restablecimiento a valores por defecto. Eliminando DB: {db_path}, Directorio Estudios: {studies_base_dir}")

                if db_path.exists():
                    try:
                        db_path.unlink()
                        logger.info(f"Base de datos eliminada: {db_path}")
                    except OSError as e:
                        logger.error(f"Error al eliminar base de datos {db_path}: {e}", exc_info=True)
                        # Continuar de todos modos si es posible
                else:
                    logger.info("Base de datos no encontrada, omitiendo eliminación.")

                if studies_base_dir.exists() and studies_base_dir.is_dir():
                    try:
                        shutil.rmtree(studies_base_dir)
                        logger.info(f"Directorio de estudios eliminado: {studies_base_dir}")
                    except OSError as e:
                        logger.error(f"Error al eliminar directorio de estudios {studies_base_dir}: {e}", exc_info=True)
                        # Continuar de todos modos si es posible
                else:
                    logger.info("Directorio de estudios no encontrado, omitiendo eliminación.")

                # Recrear la base de datos y la carpeta de estudios
                logger.info("Recreando estructura inicial...")
                # Asegurarse de que el directorio para la DB exista si es necesario
                db_path.parent.mkdir(parents=True, exist_ok=True)
                self.study_service.repo._create_tables() # Llama al método privado para recrear tablas
                studies_base_dir.mkdir(exist_ok=True)

                # Reset config.ini to default values
                logger.info("Restableciendo config.ini a valores por defecto...")
                self.settings.reset_to_defaults() # This saves defaults to config.ini
                self.reload_settings() # Reload settings in MainWindow and re-apply styles

                messagebox.showinfo("Éxito", "Valores por defecto restablecidos correctamente.\nLa configuración de la aplicación también ha sido restaurada.")
                self.show_landing_page() # Volver a la landing page
                self.update_undo_menu_state() # Update undo state after factory reset
            except Exception as e:
                logger.critical(f"Error crítico durante el restablecimiento a valores por defecto: {e}", exc_info=True)
                # import traceback # Ya no es necesario
                # traceback.print_exc() # Reemplazado por logger
                messagebox.showerror("Error", f"Error durante el restablecimiento:\n{str(e)}")
                self.update_undo_menu_state() # Update undo state even on error

    def update_undo_menu_state(self):
        """Updates the state and presence of the 'Undo' menu item."""
        if not hasattr(self, 'edit_menu'):
            return

        undo_label = "Deshacer"

        if self.settings.enable_undo_delete:
            # Ensure "Undo" command exists
            try:
                # Check if item exists by trying to get its index.
                # If this fails, it means the item is not in the menu.
                self.edit_menu.index(undo_label)
            except tk.TclError:
                # Item does not exist, add it at the top (index 0)
                self.edit_menu.insert_command(0, label=undo_label, command=self._perform_undo_operation)
            
            # Now configure its state
            if self.study_service.can_undo_last_operation():
                self.edit_menu.entryconfig(undo_label, state=tk.NORMAL)
            else:
                self.edit_menu.entryconfig(undo_label, state=tk.DISABLED)
        else:
            # Undo is disabled in settings, remove the menu item if it exists
            try:
                self.edit_menu.index(undo_label) # Check if it exists
                self.edit_menu.delete(undo_label) # If yes, delete it
            except tk.TclError:
                # Item does not exist, nothing to do
                pass

    def _perform_undo_operation(self):
        """Performs the undo operation and refreshes the view."""
        if not self.settings.enable_undo_delete:
            messagebox.showwarning("Deshacer Deshabilitado", 
                                   "La función 'Deshacer Eliminación' está deshabilitada en la configuración.", 
                                   parent=self.root)
            return

        if self.study_service.can_undo_last_operation():
            try:
                success = self.study_service.undo_last_operation()
                if success:
                    messagebox.showinfo("Deshacer", "La última operación de eliminación ha sido deshecha.", parent=self.root)
                    # Refresh the current view to reflect the undone changes
                    self.refresh_current_view_after_settings_change() # Re-use existing refresh logic
                else:
                    messagebox.showerror("Error al Deshacer", "No se pudo completar la operación de deshacer.", parent=self.root)
            except Exception as e:
                logger.error(f"Error al intentar deshacer la operación: {e}", exc_info=True)
                messagebox.showerror("Error Crítico al Deshacer", f"Ocurrió un error inesperado al intentar deshacer:\n{e}", parent=self.root)
            finally:
                self.update_undo_menu_state() # Update menu state after attempting undo
        else:
            messagebox.showinfo("Deshacer", "No hay ninguna operación para deshacer.", parent=self.root)
            self.update_undo_menu_state() # Ensure menu state is correct

    def trigger_app_restart(self):
        """Prepara la aplicación para un reinicio. Sets self.root to None after destruction."""
        logger.info("MainWindow: Solicitud de reinicio de la aplicación recibida.")
        self.restart_pending = True
        try:
            if self.root:
                try:
                    self.root.quit()
                except tk.TclError as e:
                    logger.warning(f"MainWindow: Error al hacer self.root.quit() durante el reinicio (puede ser normal si no hay mainloop activo o root ya no es válido): {e}")

                try:
                    if self.root.winfo_exists():
                        self.root.destroy()
                    else:
                        logger.info("MainWindow: La ventana raíz ya no existe, no se necesita destruir para el reinicio.")
                except tk.TclError as e: # Catch error if winfo_exists fails or destroy fails
                    logger.warning(f"MainWindow: Error al destruir la ventana raíz durante el reinicio (puede que ya no exista): {e}")
                finally:
                    self.root = None # Crucial: mark as gone
            else:
                logger.info("MainWindow: La ventana raíz (self.root) es None. No se requiere acción de Tkinter para el reinicio.")
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Excepción inesperada en trigger_app_restart: {e}", exc_info=True)
            if self.root: # Try to set to None even on error
                self.root = None

    def _on_close(self):
        """Handles the application closing sequence. Sets self.root to None after destruction."""
        logger.info("Cerrando la aplicación...")
        # Perform any pre-close cleanup if necessary
        # For example, ensuring threads are joined, files are saved, etc.
        # Currently, no specific pre-close actions identified beyond Tkinter cleanup.
        try:
            if self.root:
                try:
                    self.root.quit()
                except tk.TclError as e:
                    logger.warning(f"MainWindow: Error al hacer self.root.quit() durante el cierre (puede ser normal si no hay mainloop activo o root ya no es válido): {e}")
                
                try:
                    # Check if window still exists before destroying
                    if self.root.winfo_exists():
                        self.root.destroy()
                    else:
                        logger.info("MainWindow: La ventana raíz ya no existe, no se necesita destruir.")
                except tk.TclError as e: # Catch error if winfo_exists fails or destroy fails
                    logger.warning(f"MainWindow: Error al destruir la ventana raíz durante el cierre (puede que ya no exista): {e}")
                finally:
                    self.root = None # Crucial: mark as gone
            else:
                logger.info("MainWindow: La ventana raíz (self.root) es None. No se requiere acción de cierre de Tkinter.")
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Error inesperado durante _on_close: {e}", exc_info=True)
            # Ensure self.root is set to None even if an unexpected error occurs during cleanup
            if hasattr(self, 'root'): # Check if self has 'root' attr before trying to set it
                self.root = None
        # The main application loop (in app.py) should handle sys.exit() based on self.restart_pending.
