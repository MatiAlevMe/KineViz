# -*- mode: python ; coding: utf-8 -*-
# kineviz.spec

from pathlib import Path

# Determinar la raíz del proyecto relativo a este archivo .spec
project_root = Path(__file__).parent.resolve()
app_name = 'KineViz'
entry_point = str(project_root / 'kineviz' / 'app.py')

# Archivos de datos a incluir (ej. archivos de ayuda)
# La tupla es (ruta_origen, ruta_destino_en_bundle)
datas_to_include = [
    (str(project_root / 'docs/help'), 'docs/help')
]

# Opcional: Añadir un icono
# Asegúrate de que la ruta correcta esté activa para el SO en el que estás construyendo.
# icon_file_win = str(project_root / 'assets' / 'kineviz_icon_windows.ico') # Para Windows (.ico)
icon_file_mac = str(project_root / 'assets' / 'kineviz_icon_mac.icns') # Para macOS (.icns)
# icon_to_use = icon_file_win # Descomentar para build de Windows
icon_to_use = icon_file_mac # Activo para build de macOS


a = Analysis(
    [entry_point],
    pathex=[str(project_root)], # Asegura que PyInstaller busque módulos desde la raíz
    binaries=[],
    datas=datas_to_include,
    hiddenimports=[], # Añadir aquí si PyInstaller no detecta alguna librería
    hookspath=[],
    hooksconfig={},
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
    console=False, # False para aplicaciones GUI (no muestra consola)
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
    datas=a.datas, # Incluir los datos definidos en Analysis
    binaries=a.binaries, # Incluir binarios definidos en Analysis
    zipfiles=a.zipfiles # Incluir zipfiles definidos en Analysis
)
# --- Fin Sección macOS ---

# Nota: Para macOS, asegúrate de que la sección 'app = BUNDLE(...)' esté descomentada
#       y la sección 'coll = COLLECT(...)' esté comentada.
#       Verifica que 'icon_to_use' apunte a un archivo .icns válido.
# Nota: Para Windows, asegúrate de que la sección 'coll = COLLECT(...)' esté descomentada
#       y la sección 'app = BUNDLE(...)' esté comentada.
#       Verifica que 'icon_to_use' apunte a un archivo .ico válido.
