import tkinter as tk
import logging # Importar logging
import os
import sys
from pathlib import Path

# Añadir el directorio raíz del proyecto al sys.path para asegurar importaciones relativas
# Asumiendo que app.py está en kineviz/
from kineviz.ui.main_window import MainWindow
from kineviz.utils.logger import setup_logging # Importar setup_logging
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configurar logging ANTES de cualquier otra cosa
setup_logging(log_level=logging.DEBUG) # Usar nivel por defecto (INFO)/ Para usar DEBUGG: setup_logging(log_level=logging.DEBUG)
logger = logging.getLogger(__name__) # Obtener logger para este módulo

def main_loop():
    """Ejecuta una instancia de la aplicación KineViz."""
    logger.info("Iniciando KineViz...")
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
