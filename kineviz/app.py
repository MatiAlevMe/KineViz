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

def main():
    """Punto de entrada principal para la aplicación KineViz."""
    try:
        logger.info("Iniciando KineViz...")
        root = tk.Tk()
        # MainWindow ahora se encarga de la lógica principal de la app
        app = MainWindow(root)
        root.mainloop()
        logger.info("KineViz cerrado normalmente.")
    except Exception as e:
        logger.critical("Error crítico no capturado en la aplicación.", exc_info=True)
        # Opcionalmente, mostrar un mensaje de error al usuario antes de salir
        # messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado:\n{e}\n\nConsulte el archivo kineviz.log para más detalles.")
        sys.exit(1) # Salir con código de error

if __name__ == "__main__":
    # Asegurar que el script se ejecute correctamente si se llama directamente
    # Esto es útil para empaquetado o ejecución directa
    main()
