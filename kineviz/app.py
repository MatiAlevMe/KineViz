import tkinter as tk
import logging # Importar logging
import os
import sys
from pathlib import Path

# Añadir el directorio raíz del proyecto al sys.path para asegurar importaciones relativas
# Asumiendo que app.py está en kineviz/
from kineviz.ui.main_window import MainWindow
from kineviz.utils.logger import setup_logging as setup_logging_system # Renamed to avoid conflict
from kineviz.config.settings import AppSettings # Import AppSettings to get log_level
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configurar logging ANTES de cualquier otra cosa
# Load settings minimally to get log level for initial setup
# This means config.ini must exist or be creatable by AppSettings constructor
# A more advanced approach might involve a pre-config step or default log level before full settings load.
try:
    # Initialize settings just to get the log level
    # This will also ensure config.ini is created with defaults if it doesn't exist
    temp_settings = AppSettings()
    initial_log_level = temp_settings.log_level # Default is now WARNING
except Exception as e:
    # Fallback if AppSettings fails critically before logging is set up
    print(f"Error initializing AppSettings for logging: {e}. Defaulting log level to WARNING.", file=sys.stderr)
    initial_log_level = "WARNING" # Fallback to WARNING

setup_logging_system(log_level_name=initial_log_level)
logger = logging.getLogger(__name__) # Obtener logger para este módulo

def main_loop():
    """Ejecuta una instancia de la aplicación KineViz."""
    logger.info("Iniciando KineViz...")
    # AppSettings will be instantiated again inside MainWindow, which is fine.
    # The key is that logging is set up *before* MainWindow tries to use it.
    root = tk.Tk()
    app = MainWindow(root) # MainWindow se encarga de la lógica principal
    root.mainloop()

    # Verificar si se solicitó un reinicio
    if hasattr(app, 'restart_pending') and app.restart_pending:
        logger.info("Reinicio de KineViz solicitado.")
        try:
            if root.winfo_exists():
                root.destroy() # Destruir la ventana raíz actual
        except tk.TclError:
            logger.warning("Error al destruir la ventana raíz durante el reinicio, puede que ya no exista.")
        return True # Señal para reiniciar
    
    logger.info("KineViz cerrado normalmente.")
    return False # Señal para salir

if __name__ == "__main__":
    # Bucle para permitir el reinicio de la aplicación
    while main_loop():
        logger.info("Reiniciando la aplicación...")
    
    logger.info("Saliendo de KineViz.")
    sys.exit(0) # Salir limpiamente
