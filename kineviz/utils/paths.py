import sys
from pathlib import Path
import os

def get_application_base_dir() -> Path:
    """
    Determines the base directory for the application.
    For a PyInstaller bundle, this is the directory containing the executable.
    For development, this is the project root.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        return Path(sys.executable).parent
    else:
        # Running in a normal Python environment (development)
        # Assuming this file (paths.py) is in kineviz/utils/
        # Project root is .. (kineviz) / .. (project_root)
        return Path(__file__).resolve().parent.parent.parent
