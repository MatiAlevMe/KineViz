import tkinter as tk
from kineviz.ui.main_window import MainWindow
import os
import sys
from pathlib import Path

# Añadir el directorio raíz del proyecto al sys.path para asegurar importaciones relativas
# Asumiendo que app.py está en kineviz/
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    """Punto de entrada principal para la aplicación KineViz."""
    root = tk.Tk()
    # MainWindow ahora se encarga de la lógica principal de la app
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    # Asegurar que el script se ejecute correctamente si se llama directamente
    # Esto es útil para empaquetado o ejecución directa
    main()
