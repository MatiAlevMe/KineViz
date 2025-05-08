# -*- mode: python ; coding: utf-8 -*-
# kineviz.spec

import sys
import os # Necesario para os.path.join y os.path.exists
from pathlib import Path

# Determinar la raíz del proyecto usando SPECPATH (proporcionado por PyInstaller)
# SPECPATH es la ruta al directorio que contiene este archivo .spec
project_root = Path(SPECPATH)
app_name = 'KineViz'
entry_point = str(project_root / 'kineviz' / 'app.py')

# Archivos de datos a incluir (config.ini, docs, assets, etc.)
# La tupla es (ruta_origen, ruta_destino_en_bundle)
# '.' como destino significa la raíz del bundle.
datas_to_include = [
    ('config.ini', '.'), # Incluir config.ini en la raíz del bundle
    (str(project_root / 'kineviz' / 'docs' / 'help'), 'kineviz/docs/help'), # Archivos de ayuda específicos
    (str(project_root / 'kineviz' / 'assets'), 'kineviz/assets') # Incluir assets
]

# Opcional: Añadir un icono
# Asegúrate de que la ruta correcta esté activa para el SO en el que estás construyendo.
# icon_file_win = str(project_root / 'kineviz' / 'assets' / 'kineviz_icon_windows.ico') # Para Windows (.ico)
icon_file_mac = str(project_root / 'kineviz' / 'assets' / 'kineviz_icon_mac.icns') # Para macOS (.icns)
# icon_to_use = icon_file_win # Descomentar para build de Windows
icon_to_use = icon_file_mac # Activo para build de macOS

# --- Determinar dinámicamente la ruta de la librería Python ---
# Usar sys.base_prefix que apunta a la raíz de la instalación de Python base
python_version_short = f"{sys.version_info.major}.{sys.version_info.minor}"
python_lib_filename = f"libpython{python_version_short}.dylib"
# sys.base_prefix debería apuntar a /Users/arakito/.pyenv/versions/3.12.6/ en este caso
python_lib_base_dir = getattr(sys, "base_prefix", sys.prefix) # Fallback a sys.prefix si base_prefix no existe (Python < 3.3)
_python_lib_path_temp = os.path.join(python_lib_base_dir, 'lib', python_lib_filename)

# Verificar si existe, si no, lanzar error claro
if not os.path.exists(_python_lib_path_temp):
    # Podríamos intentar un fallback, pero es mejor fallar si no se encuentra
    # python_lib_path_fallback = '/Users/arakito/.pyenv/versions/3.12.6/lib/libpython3.12.dylib' # Ruta anterior
    # if os.path.exists(python_lib_path_fallback):
    #     print(f"Warning: Dynamic Python lib path not found: {_python_lib_path_temp}. Using fallback: {python_lib_path_fallback}")
    #     _python_lib_path_temp = python_lib_path_fallback
    # else:
    expected_location_dir = os.path.join(python_lib_base_dir, 'lib')
    raise FileNotFoundError(
        f"Python library '{python_lib_filename}' not found in expected location: {expected_location_dir}. "
        f"Checked path: {_python_lib_path_temp}. Please ensure Python was compiled with --enable-shared or check your pyenv setup."
    )

# Usar la ruta real para evitar problemas con enlaces simbólicos
python_lib_path = os.path.realpath(_python_lib_path_temp)
print(f"Using Python library (real path): {python_lib_path}")
# --- Fin determinación dinámica ---


a = Analysis(
    [entry_point],
    pathex=[str(project_root)], # Asegura que PyInstaller busque módulos desde la raíz
    # Añadir la librería compartida de Python dinámicamente determinada
    binaries=[(python_lib_path, 'Frameworks')],
    datas=datas_to_include,
    # Añadir importaciones ocultas comunes para data science y GUI
    hiddenimports=[
        'pandas', 'numpy', # Fundamentales para datos
        'seaborn', 'matplotlib', 'matplotlib.pyplot', 'PIL', 'PIL._imagingtk', 'PIL._tkinter_finder', # Para gráficos estáticos y Tkinter
        'plotly', # Para gráficos interactivos
        'scipy', 'scipy.stats', 'statannotations', # Para análisis estadístico (nombre corregido)
        'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.font', # GUI y fuentes
        'configparser', 'logging', 'pathlib', # Utilidades estándar
        'openpyxl', # Para leer/escribir Excel con pandas
        'reportlab', # Si se usa para generar PDFs
        'PyPDF2', # Si se usa para manipular PDFs
        'dateutil', # A menudo usado por pandas
        'pytz' # A menudo usado por pandas
    ],
    hookspath=[],
    # Configuración específica para hooks
    hooksconfig={
        'matplotlib': {
            'backends': ['TkAgg']  # Especificar el backend de Tkinter para Matplotlib
        }
    },
    # Los runtime hooks suelen ser automáticos, eliminamos la entrada explícita por ahora
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher_block_size=None,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher_block_size=None)

exe = EXE(
    pyz,
    a.scripts,
    [], # Esto es para entradas *adicionales* al toc no presentes en el objeto Analysis 'a'.
      # a.binaries, a.datas, a.zipfiles son implícitamente parte de lo que EXE procesa desde Analysis 'a'
      # si no se excluyen.
    exclude_binaries=False, # Asegura que los binarios de Analysis se incluyan en el TOC de EXE para BUNDLE
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # Comprime el ejecutable (puede requerir instalar UPX)
    console=False, # False para una aplicación GUI estándar en macOS.
                   # Esto podría influir en cómo BUNDLE trata al exe.
    disable_windowed_traceback=False,
    target_arch=None, # None para arquitectura nativa (arm64 en tu Mac)
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_to_use # Usa el icono definido arriba
)

# --- Sección para Windows ---
# Descomentar esta sección y comentar la sección BUNDLE al construir en Windows
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name=app_name
# )
# --- Fin Sección Windows ---

# --- Sección para macOS ---
# Descomentar esta sección y comentar la sección COLLECT al construir en macOS
# Específico para macOS: Crear un .app bundle
app = BUNDLE(
    exe, # Usar el ejecutable directamente
    name=f'{app_name}.app',
    icon=icon_to_use, # Usar el .icns definido arriba
    bundle_identifier=None, # Opcional: ej. 'com.tuorganizacion.kineviz'
    info_plist={ # Añadir entradas básicas al Info.plist si es necesario
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True'
    }
    # Los binarios, datas, y zipfiles de Analysis 'a' deben ser recogidos
    # a través del TOC del objeto 'exe' (ya que exclude_binaries=False en EXE).
    # BUNDLE debería entonces colocarlos correctamente según sus destinos especificados
    # en 'a.binaries' y 'a.datas'.
)
# --- Fin Sección macOS ---

# Nota: Para macOS, asegúrate de que la sección 'app = BUNDLE(...)' esté descomentada
#       y la sección 'coll = COLLECT(...)' esté comentada.
#       Verifica que 'icon_to_use' apunte a un archivo .icns válido.
# Nota: Para Windows, asegúrate de que la sección 'coll = COLLECT(...)' esté descomentada
#       y la sección 'app = BUNDLE(...)' esté comentada.
#       Verifica que 'icon_to_use' apunte a un archivo .ico válido.
