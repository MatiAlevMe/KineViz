# KineViz Refactoring Roadmap

Este roadmap describe el proceso de refactorización de la aplicación KineViz, moviendo la lógica original de los archivos `interfaz.py` y `lectura.py` a una estructura modular basada en servicios, repositorios y componentes de UI reutilizables dentro del paquete `kineviz`. El objetivo es mejorar la mantenibilidad, escalabilidad y organización del código.

Este ROADMAP debe ser actualizado en cada iteración hasta completar la refactorización y se debe dar la opción de ejecutar el programa con "python -m kineviz.app" para ir capturando errores.

## Estrctura de carpetas de refactorización

├── __init__.py
├── app.py           # Punto de entrada principal
│
├── core/                 # Lógica de negocio y dominio
│   ├── __init__.py
│   ├── exceptions.py  
│   ├── data_processing/  # Procesamiento de datos
│   │   ├── processors.py  # (formatos, cálculos)
│   │   ├── file_handlers.py  # Manejo específico de archivos
│   │   └── directory_manager.py  # Gestión de estructura de directorios
│   │
│   ├── models/           # Modelos de datos y DTOs
│   │   ├── study.py
│   │   ├── measurement.py
│   │   └── report.py
│   │
│   └── services/         # Lógica de negocio
│       ├── study_service.py
│       ├── file_service.py
│       └── analysis_service.py
│
├── ui/                   # Capa de presentación
│   ├── __init__.py
│   ├── main_window.py    # Ventana principal
│   │
│   ├── views/            # Vistas complejas
│   │   ├── landing_page.py
│   │   ├── study_view.py
│   │   └── analysis_view.py
│   │
│   ├── dialogs/          # Diálogos modales
│   │   ├── analysis_dialog.py
│   │   ├── study_dialog.py
│   │   ├── file_dialog.py
│   │   └── report_dialog.py
│   │
│   ├── widgets/          # Componentes reutilizables
│   │   ├── pagination.py
│   │   ├── paginated_table.py
│   │   ├── file_tree.py
│   │   ├── file_browser.py
│   │   └── charting.py
│   │
│   └── utils/            # Helpers de UI
│       ├── validators.py
│       ├── file_ops.py
│       └── style.py      # Temas y estilos
│
├── database/             # Persistencia de datos
│   ├── __init__.py
│   ├── operations.py     # CRUD básico
│   ├── repositories.py   # Patrón repositorio
│   └── models.py         # Modelos de DB
│
├── config/               # Configuración
│   ├── __init__.py
│   ├── settings.py
│   └── environment.py    # Gestión de entornos
│
├── utils/                # Utilidades generales
│   ├── __init__.py
│   ├── logger.py
│   └── security.py       # Encriptación, etc.
│
├── tests/                # Pruebas automatizadas
│   ├── unit/
│   └── integration/
│
├── docs/                 # Documentación
└── examples/             # Ejemplos de uso

## Fase 1: Integración Inicial y Estructura Base (Completada - d2caeef)

*   [x] Crear estructura básica del proyecto (`kineviz` package).
*   [x] Mover lógica de `lectura.py` a `kineviz.core.data_processing` y `kineviz.core.services`.
*   [x] Crear punto de entrada `kineviz/app.py`.
*   [x] Refactorizar `kineviz/ui/main_window.py` para manejar la ventana principal, configuración inicial y navegación básica.
*   [x] Integrar `LandingPage` (`kineviz/ui/views/landing_page.py`).
*   [x] Integrar diálogo de creación/edición de estudios (`kineviz/ui/dialogs/study_dialog.py`) con validación básica.
*   [x] Adaptar `StudyService` y `StudyRepository` para soportar operaciones básicas y conteo.
*   [x] Corregir errores iniciales de importación y validación.

## Fase 2: Vista Principal y Gestión de Estudios

*   [x] Implementar `MainView` (`kineviz/ui/views/main_view.py`) para mostrar la lista de estudios.
    *   [x] Tabla de estudios (`ttk.Treeview`).
    *   [x] Funcionalidad de búsqueda.
    *   [x] Paginación de estudios.
    *   [x] Botones de acción (Ver, Editar, Eliminar) en la tabla.
    *   [x] Botones de cabecera (Manual, Config, Ayuda, Abrir Carpeta).
*   [x] Implementar la funcionalidad completa de **Editar Estudio** en `StudyDialog` y `StudyService`/`StudyRepository`.
    *   [x] Cargar datos existentes en el diálogo.
    *   [x] Validar datos modificados.
    *   [x] Actualizar datos en la base de datos (`StudyService.update_study`).
    *   [x] Renombrar carpeta del estudio si el nombre cambia (`StudyRepository.rename_study_folder`).
    *   [x] Manejar la validación/eliminación de archivos existentes si los criterios (tipos/periodos) cambian.
*   [x] Implementar la funcionalidad de **Eliminar Estudio** en `MainView` y `StudyService`/`StudyRepository`.
*   [x] Implementar la funcionalidad de **Ver Estudio** (`StudyView`).
    *   [x] Mostrar detalles básicos del estudio.
    *   [x] Integrar `FileBrowser` para mostrar archivos del estudio.
    *   [x] Implementar carga real de archivos en `FileBrowser` desde `FileService`.
    *   [x] Funcionalidad "Ver Archivo".
    *   [x] Funcionalidad "Eliminar Archivo".

## Fase 3: Gestión de Archivos y Análisis

*   [x] Implementar `FileBrowser` (`kineviz/ui/widgets/file_browser.py`) completamente.
    *   [x] Cargar y mostrar archivos del estudio desde `FileService`. (Hecho en Fase 2)
    *   [x] Paginación de archivos.
    *   [x] Búsqueda/filtrado de archivos.
    *   [x] Funcionalidad "Ver Archivo". (Hecho en Fase 2)
    *   [x] Funcionalidad "Eliminar Archivo". (Hecho en Fase 2)
*   [x] Implementar `FileService` para manejar la lógica de archivos (obtener, eliminar, filtrar, paginar, agregar). (Hecho en Fase 2 y 3)
*   [x] Implementar diálogo para **Agregar Archivos** a un estudio, incluyendo validación de formato de nombre.
*   [X] Implementar `AnalysisDialog` (`kineviz/ui/dialogs/analysis_dialog.py`).
    *   [x] Selección de parámetros (pacientes, frecuencias, tipos, periodos, cálculos).
    *   [X] Generación de reportes PDF.
    *   [X] Visualización/eliminación de reportes generados.
*   [x] Implementar `AnalysisService` para la lógica de análisis y generación de reportes. (Implementación inicial de PDF y cálculos)
*   [x] Implementar `Charting` (`kineviz/ui/widgets/charting.py`) para visualizaciones. (Boxplot, Barchart básicos)
*   [x] Implementar visualización/eliminación de reportes generados en `AnalysisDialog`.

## Fase 4: Refinamientos y Finalización

*   [x] Implementar `ConfigDialog` (`kineviz/ui/dialogs/config_dialog.py`) y `AppSettings` (`kineviz/config/settings.py`).
*   [ ] Mejorar manejo de errores y logging (`kineviz/utils/logger.py`).
*   [ ] Añadir pruebas unitarias e de integración (`tests/`).
*   [ ] Completar documentación (`docs/`).
*   [x] Limpiar código remanente de `interfaz.py` y `lectura.py`.
*   [ ] Revisión final de estilos y UX.

---

## Known Issues / Bugs

*   **Edición de Estudio - Cambio de Criterios**: Al editar un estudio y cambiar los `Tipos de Prueba` o `Periodos de Prueba`, no se validan ni eliminan automáticamente los archivos existentes que ya no cumplen con los nuevos criterios. (Ver Fase 2 - Editar Estudio).
*   **Análisis y Reportes**: La lógica de análisis, generación de PDF y gestión básica de reportes (listar, ver, eliminar) está implementada.
*   **Configuración**: Implementada la gestión básica de configuración (`AppSettings`, `ConfigDialog`) para paginación. El botón de reseteo global está conectado.
*   **Limpieza de Directorios**: La limpieza de directorios vacíos (paciente, frecuencia) después de eliminar el último archivo dentro de ellos funciona, pero podría mejorarse para manejar casos borde o errores de permisos de forma más robusta.
*   **Validación de Pacientes para Análisis**: La validación ahora se basa en los parámetros únicos extraídos de archivos procesados válidos. Si un estudio tiene archivos pero no cumplen los criterios o solo tiene archivos OG, no permitirá el análisis.
*   **Lectura de Datos Procesados**: La función `_read_processed_file_data` en `AnalysisService` asume un formato específico (';' como separador, 4 líneas de header, 3 de stats). Podría ser más robusta o configurable.

---
*Este archivo se actualizará a medida que avance el desarrollo.*
