import logging
import logging.handlers
from pathlib import Path
import sys
import os # For os.getenv, os.startfile
import platform # For platform.system()
import shutil # For shutil.make_archive
from tkinter import filedialog, messagebox # For export_logs dialogs
import subprocess # For opening folders on macOS/Linux

LOG_FILENAME = "kineviz.log" # Reverted to original name
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3

# Cache for the log directory path
_log_dir_cache = None

def get_log_dir() -> Path:
    """
    Determines the persistent log directory.
    For packaged apps:
        - Windows: %APPDATA%/KineViz/logs
        - macOS: ~/Library/Logs/KineViz
        - Linux: ~/.config/KineViz/logs
    For development: project_root/logs
    Caches the result.
    """
    global _log_dir_cache
    if _log_dir_cache:
        return _log_dir_cache

    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Packaged app
            system = platform.system()
            if system == 'Windows':
                # %APPDATA% is the typical place for app-specific data
                log_dir_base = Path(os.getenv('APPDATA', Path.home() / 'AppData' / 'Roaming'))
                resolved_log_dir = log_dir_base / 'KineViz' / 'logs'
            elif system == 'Darwin': # macOS
                resolved_log_dir = Path.home() / 'Library' / 'Logs' / 'KineViz'
            else: # Linux and other Unix-like
                # Use XDG Base Directory Specification if possible, fallback to .config
                xdg_config_home = os.getenv('XDG_CONFIG_HOME')
                if xdg_config_home:
                    resolved_log_dir = Path(xdg_config_home) / 'KineViz' / 'logs'
                else:
                    resolved_log_dir = Path.home() / '.config' / 'KineViz' / 'logs'
        else:
            # Development mode
            # Assuming this file is in kineviz/utils/logger.py
            # Project root is two levels up
            project_root = Path(__file__).resolve().parent.parent.parent
            resolved_log_dir = project_root / 'logs' # Reverted to 'logs' for dev
        
        _log_dir_cache = resolved_log_dir
        return resolved_log_dir
    except Exception as e:
        # Fallback in case of unexpected error determining path
        # This should be very rare.
        print(f"CRITICAL: Error determining log directory: {e}. Logging may not work as expected.", file=sys.stderr)
        # Fallback to a clearly temporary/error location
        fallback_dir = Path.cwd() / 'kineviz_LOG_ERROR_fallback_logs'
        _log_dir_cache = fallback_dir
        return fallback_dir


def setup_logging(log_level_name: str = 'INFO'):
    """
    Configura el sistema de logging para la aplicación.
    Usa una ruta persistente para los logs.

    :param log_level_name: Nivel mínimo de logging como string (e.g., "INFO", "DEBUG").
    """
    try:
        log_dir = get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / LOG_FILENAME

        # Convert log_level_name string to logging level constant
        numeric_level = getattr(logging, log_level_name.upper(), logging.INFO)

        # Formato del log
        log_format = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
        formatter = logging.Formatter(log_format)

        # Configuración raíz del logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level) # Use numeric_level
        # Limpiar handlers existentes para evitar duplicados si se llama varias veces
        # Esto es importante si setup_logging can be called multiple times (e.g. after settings change)
        for handler in root_logger.handlers[:]:
            handler.close() # Close existing handlers before removing
            root_logger.removeHandler(handler)

        # Handler para archivo rotatorio
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Handler para consola (opcional, útil para debugging)
        # Muestra todos los niveles en consola si el logger raíz está en DEBUG, sino INFO y superior.
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        if numeric_level == logging.DEBUG:
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.INFO) # Or keep it same as root_logger.level
        root_logger.addHandler(console_handler)

        logging.info(f"Logging configurado. Nivel: {log_level_name.upper()}. Archivo: {log_file_path}")

    except Exception as e:
        # Fallback a logging básico si la configuración falla
        # Use print as logger itself might be failing
        print(f"CRITICAL: Error configurando el logging: {e}", file=sys.stderr)
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.error(f"Error configurando el logging detallado: {e}", exc_info=True)


def open_logs_folder():
    """Abre la carpeta de logs en el explorador de archivos del sistema."""
    log_dir = get_log_dir()
    if not log_dir.exists():
        messagebox.showerror("Error", f"La carpeta de logs no existe aún: {log_dir}\nIntente generar algunos logs primero.", parent=None)
        return

    try:
        logging.info(f"Intentando abrir carpeta de logs: {log_dir}")
        if platform.system() == "Windows":
            os.startfile(log_dir)
        elif platform.system() == "Darwin": # macOS
            subprocess.run(['open', str(log_dir)], check=True)
        else: # Linux, etc.
            subprocess.run(['xdg-open', str(log_dir)], check=True)
    except FileNotFoundError:
         messagebox.showerror("Error", f"No se pudo encontrar la carpeta de logs:\n'{log_dir}'", parent=None)
         logging.error(f"Carpeta de logs no encontrada al intentar abrir: {log_dir}", exc_info=True)
    except PermissionError:
         messagebox.showerror("Error", f"No tiene permisos para acceder a la carpeta de logs:\n'{log_dir}'", parent=None)
         logging.error(f"Permiso denegado al abrir la carpeta de logs: {log_dir}", exc_info=True)
    except subprocess.CalledProcessError as e:
         logging.error(f"Comando para abrir la carpeta de logs {log_dir} falló: {e}", exc_info=True)
         messagebox.showerror("Error", f"El comando para abrir la carpeta de logs falló:\n{e}", parent=None)
    except Exception as e:
        logging.error(f"Error inesperado al abrir la carpeta de logs {log_dir}: {e}", exc_info=True)
        messagebox.showerror("Error", f"No se pudo abrir la carpeta de logs '{log_dir}':\n{str(e)}", parent=None)


def export_logs(parent_widget=None):
    """
    Comprime la carpeta de logs en un archivo ZIP y pide al usuario dónde guardarlo.
    :param parent_widget: Widget padre para los diálogos modales.
    """
    log_dir = get_log_dir()
    if not log_dir.exists() or not any(log_dir.iterdir()): # Check if directory exists and is not empty
        messagebox.showinfo("Exportar Logs", "La carpeta de logs está vacía o no existe. No hay nada que exportar.", parent=parent_widget)
        return

    default_zip_name = f"kineviz_logs_{platform.node()}_{Path(LOG_FILENAME).stem}.zip"
    dest_path_str = filedialog.asksaveasfilename(
        parent=parent_widget,
        title="Guardar Logs Exportados Como...",
        defaultextension=".zip",
        initialfile=default_zip_name,
        filetypes=[("Archivo ZIP", "*.zip")]
    )

    if not dest_path_str: # User cancelled
        return

    dest_path = Path(dest_path_str)

    try:
        logging.info(f"Exportando logs desde {log_dir} a {dest_path}")
        # shutil.make_archive base_name is path without extension
        shutil.make_archive(str(dest_path.with_suffix('')), 'zip', root_dir=log_dir.parent, base_dir=log_dir.name)
        messagebox.showinfo("Éxito", f"Logs exportados correctamente a:\n{dest_path}", parent=parent_widget)
        logging.info(f"Logs exportados exitosamente a: {dest_path}")
    except Exception as e:
        logging.error(f"Error al exportar logs a {dest_path}: {e}", exc_info=True)
        messagebox.showerror("Error de Exportación", f"No se pudieron exportar los logs:\n{e}", parent=parent_widget)


# Ejemplo de uso (opcional)
if __name__ == '__main__':
    # Test setup_logging
    print(f"Log directory will be: {get_log_dir()}")
    setup_logging(log_level_name='DEBUG') # Test with string level
    
    logging.debug("Mensaje de debug desde logger.py")
    logging.info("Mensaje informativo desde logger.py")
    logging.warning("Mensaje de advertencia desde logger.py")
    logging.error("Mensaje de error desde logger.py")
    try:
        1 / 0
    except ZeroDivisionError:
        logging.exception("Ocurrió una excepción en logger.py")

    # Test open_logs_folder (manual trigger, comment out if not needed for automated tests)
    # open_logs_folder()

    # Test export_logs (manual trigger)
    # export_logs()
    print(f"Contenido de la carpeta de logs ({get_log_dir()}):")
    for item in get_log_dir().iterdir():
        print(f" - {item.name}")
