# -*- mode: python ; coding: utf-8 -*-
# kineviz.spec

import sys
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


a = Analysis(
    [entry_point],
    pathex=[str(project_root)], # Asegura que PyInstaller busque módulos desde la raíz
    # Añadir explícitamente la librería compartida de Python para macOS con pyenv
    # El primer elemento es la ruta origen, el segundo es el directorio destino DENTRO del bundle
    # Para macOS .app, las librerías van en 'Frameworks'
    binaries=[('/Users/arakito/.pyenv/versions/3.12.6/lib/libpython3.12.dylib', 'Frameworks')],
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
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # Comprime el ejecutable (puede requerir instalar UPX)
    console=True, # True para depuración (muestra consola al ejecutar .app)
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
    },
    datas=a.datas # Incluir los datos definidos en Analysis (irán a Contents/Resources)
    # binaries y zipfiles son manejados por 'exe'
)
# --- Fin Sección macOS ---

# Nota: Para macOS, asegúrate de que la sección 'app = BUNDLE(...)' esté descomentada
#       y la sección 'coll = COLLECT(...)' esté comentada.
#       Verifica que 'icon_to_use' apunte a un archivo .icns válido.
# Nota: Para Windows, asegúrate de que la sección 'coll = COLLECT(...)' esté descomentada
#       y la sección 'app = BUNDLE(...)' esté comentada.
#       Verifica que 'icon_to_use' apunte a un archivo .ico válido.
