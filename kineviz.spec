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

# Opcional: Añadir un icono (descomentar y ajustar la ruta si tienes uno)
icon_file = str(project_root / 'assets' / 'kineviz_icon_windows.ico') # Para Windows (.ico)
icon_file = str(project_root / 'assets' / 'kineviz_icon_mac.icns') # Para macOS (.icns)


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
    target_arch=None, # None para arquitectura nativa
    codesign_identity=None,
    entitlements_file=None,
    # icon=icon_file # Descomentar si se define un icono arriba
)

#Específico para Windos
#coll = COLLECT(
#    exe,
#    a.binaries,
#    a.zipfiles,
#    a.datas,
#    strip=False,
#    upx=True,
#    upx_exclude=[],
#    name=app_name
#)

Específico para macOS: Crear un .app bundle
app = BUNDLE(
    coll,
    name=f'{app_name}.app',
    icon=icon_file, # Usar el .icns definido arriba
    bundle_identifier=None # Opcional: ej. 'com.tuorganizacion.kineviz'
)

# Nota: Para macOS, descomenta la sección 'app = BUNDLE(...)' y comenta/elimina 'coll = COLLECT(...)'
#       Asegúrate de que 'icon_file' apunte a un archivo .icns válido.
# Nota: Para Windows, usa la sección 'coll = COLLECT(...)' y asegúrate de que 'icon_file' (si se usa) apunte a un .ico.
