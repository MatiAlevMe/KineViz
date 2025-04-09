# KineViz Development Roadmap

Este roadmap describe el proceso de desarrollo de la aplicación KineViz. Inicialmente se enfocó en la refactorización de la lógica original a una estructura modular. A partir de la Fase 5, el enfoque cambia a mejoras incrementales y la adición de nuevas funcionalidades, mejoras a las funcionalidades actuales u bug-fixes.

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

## Fase 5: Mejoras Incrementales - Descriptores y Detección de Frecuencia

*   [x] **Modificación de Identificador de Frecuencias**: Cambiar la detección de tipo de frecuencia (Cinemática, Cinética, Electromiográfica) basada en metadatos del archivo ("Model Outputs", "Force Plate"). (Tarea 1)
*   [X] **Implementación de Descriptores**: Reemplazar el sistema de "Tipos de Prueba" y "Periodos de Prueba" por un sistema flexible de "Descriptores" definidos por el usuario al crear/editar estudios. (Tarea 2 - UI y DB)
*   [ ] **Modificación de Etiquetas Post-Carga**: Permitir al usuario asignar alias o nombres descriptivos a los descriptores detectados en los archivos, para visualización en análisis y reportes. (Tarea 3)
*   [ ] **Integración Completa**: Asegurar que los cambios en la detección de frecuencia y el sistema de descriptores se integren correctamente en la carga de archivos, validación, análisis, reportes y UI. (Tarea 4)

## Fase 6: Análisis Discreto - Individual y General - Tablas y Gráficos (WIP)

## Fase 7: Refinamientos y Finalización (Antigua Fase 4)

*   [x] Implementar `ConfigDialog` (`kineviz/ui/dialogs/config_dialog.py`) y `AppSettings` (`kineviz/config/settings.py`).
*   [x] Mejorar manejo de errores y logging (`kineviz/utils/logger.py`). (Integrado en la mayoría de módulos)
*   [ ] Añadir pruebas unitarias e de integración (`tests/`). (Inicio: validadores, StudyRepository, FileService, AnalysisService)
*   [ ] Completar documentación (`docs/`).
*   [x] Limpiar código remanente de `interfaz.py` y `lectura.py`.
*   [ ] Revisión final de estilos y UX.

---

## Diccionario de Tareas (Fase 5+)

**Fase 5: Mejoras Incrementales - Descriptores y Detección de Frecuencia**

*   **1. Implementar detección automática de tipo de frecuencias basada en metadatos del archivo. (Completado - 91ffd0a)**
    *   **Detalle**: Modificada la lógica en `kineviz.core.data_processing.file_handlers.leer_seccion` y `kineviz.core.services.file_service._process_and_copy_file` para identificar Cinemática ("Model Outputs") y Cinética ("Force Plate").
    *   **1.1 Implementación de identificador de archivo para Cinemática**: Hecho.
    *   **1.2 Implementación de identificador de archivo para Cinética**: Hecho.
    *   **1.3 Implementación de identificador de archivo para Electromiográfica**: Pendiente de confirmación del formato/identificador.

*   **2. Implementación para crear/editar estudio con descriptores extra. (Completado)**
    *   **Detalle**: Modificado `kineviz.ui.dialogs.study_dialog.py` para reemplazar los campos de entrada de "Tipos de Prueba" y "Periodos de Prueba" por una sección dinámica que permita añadir/eliminar campos de texto para "Descriptores".
    *   **2.1 Soportar múltiples etiquetas de descriptores**: (Hecho) UI modificada para añadir/eliminar campos. Tabla `estudios` modificada para usar columna `descriptores` (TEXT, separado por comas). Repositorio y Servicio actualizados.
    *   **2.2 Validación de descriptores**: (Hecho) Añadida validación en `kineviz.ui.utils.validators.validate_study_data` para evitar descriptores vacíos o duplicados exactos.

*   **3. Implementación para modificar nombres de etiquetas de descriptores post-carga.** (Parcialmente Completado)
    *   **Detalle**: Añadir una nueva funcionalidad (posiblemente en `kineviz.ui.views.study_view.py` o un nuevo diálogo) que permita al usuario ver los descriptores *detectados* en los nombres de archivo de un estudio y asignarles un "alias" o "nombre descriptivo" (ej: "CMJ" -> "Salto Contra Movimiento"). Este alias se usaría para mostrar en gráficos y reportes. El almacenamiento de estos alias podría ser en `config.ini` o en la base de datos. *Nota: Inicialmente, esta modificación es solo visual.*
    *   **3.1 Añadir gestión de alias en `AppSettings`**: (Hecho) Métodos para leer/escribir sección `[DESCRIPTOR_ALIASES]` en `config.ini`.
    *   **3.2 Crear `DescriptorAliasDialog`**: (Hecho) Diálogo para ver descriptores detectados y asignar/guardar alias usando `AppSettings`.
    *   **3.3 Añadir botón en `StudyView` para abrir el diálogo**: (Hecho)

*   **4. Integrar con el resto del código. (Completado - Alias)**
    *   **Detalle**: Revisar y actualizar todos los módulos que dependían de `test_types` y `test_periods` (Hecho). **Adicionalmente**, integrar el uso de los alias de descriptores en:
        *   `kineviz.core.services.analysis_service`: (Hecho) Usar alias en `generate_report` para títulos, leyendas, etc.
        *   `kineviz.ui.dialogs.analysis_dialog.py`: (Hecho) Mostrar alias en el selector de descriptores. Asegurarse de pasar el descriptor original al servicio.
        *   `kineviz.ui.utils.validators.validate_filename_for_study_criteria`: (Hecho) Actualizada para validar contra `descriptors`.
        *   `kineviz.core.services.file_service.add_files_to_study`: (Hecho) Actualizado para usar el validador con `descriptors`.
        *   `kineviz.core.services.file_service.get_unique_study_parameters`: (Hecho) Actualizado para extraer `descriptors` de nombres de archivo válidos.
        *   `kineviz.core.services.analysis_service`: (Hecho) `get_analysis_parameters`, `_get_data_for_parameters`, `generate_report` actualizados para usar `descriptors`.
        *   `kineviz.ui.dialogs.analysis_dialog.py`: (Hecho) Actualizado para mostrar y usar selector de `descriptors`.
        *   Actualizar pruebas unitarias afectadas. (Hecho)

---

## Known Issues / Bugs

*   **Edición de Estudio - Cambio de Criterios**: Al editar un estudio y cambiar los `Tipos de Prueba` o `Periodos de Prueba`, no se validan ni eliminan automáticamente los archivos existentes que ya no cumplen con los nuevos criterios. (Ver Fase 2 - Editar Estudio).
*   **Análisis y Reportes**: La lógica de análisis, generación de PDF y gestión básica de reportes (listar, ver, eliminar) está implementada.
*   **Configuración**: Implementada la gestión básica de configuración (`AppSettings`, `ConfigDialog`) para paginación. El botón de reseteo global está conectado.
*   **Limpieza de Directorios**: La limpieza de directorios vacíos (paciente, frecuencia) después de eliminar el último archivo dentro de ellos funciona, pero podría mejorarse para manejar casos borde o errores de permisos de forma más robusta.
*   **Validación de Pacientes para Análisis**: La validación ahora se basa en los parámetros únicos extraídos de archivos procesados válidos. Si un estudio tiene archivos pero no cumplen los criterios o solo tiene archivos OG, no permitirá el análisis.
*   **Lectura de Datos Procesados**: La función `_read_processed_file_data` en `AnalysisService` asume un formato específico (';' como separador, 4 líneas de header, 3 de stats). Podría ser más robusta o configurable.
*   **Logging**: El logging está implementado en la mayoría de los módulos. Se podrían añadir más mensajes de `DEBUG` o refinar los niveles existentes.

---
*Este archivo se actualizará y se marcaran con una X las tareas que se vayan realizando a medida que avance el desarrollo.*
