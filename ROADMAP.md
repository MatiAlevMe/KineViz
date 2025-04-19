# KineViz Development Roadmap

Este roadmap describe el proceso de desarrollo de la aplicación KineViz. Inicialmente se enfocó en la refactorización de la lógica original a una estructura modular. Luego, el enfoque cambia a mejoras incrementales y la adición de nuevas funcionalidades, mejoras a las funcionalidades actuales u bug-fixes.

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
│   └── help/             # Documentación de ayuda del software
│       ├── study_view_help.txt            # Guía Rápida: Variables Independientes y Descriptores
│       └── study_dialog_iv_help.txt       # Guía Rápida: Vista del Estudio  
└── examples/             # Ejemplos de uso

## Diccionario de Tareas

**Fase 1: Mejoras Incrementales - Detección de Frecuencia (Hecho)**

* **1. Implementar detección automática de tipo de frecuencias basada en metadatos del archivo.** (Hecho)
    * **Detalle**: Modificar la lógica en `kineviz.core.data_processing.file_handlers.leer_seccion` y `kineviz.core.services.file_service._process_and_copy_file` para identificar Cinemática ("Model Outputs"), Cinética ("Force Plate") y Electromiográfica (Hecho).
    * **1.1 Implementación de identificador de archivo para Cinemática**: (Hecho).
    * **1.2 Implementación de identificador de archivo para Cinética**: (Hecho).
    * **1.3 Implementación de identificador de archivo para Electromiográfica**: (Hecho) de confirmación del formato/identificador.

**Fase 2: Análisis Estadístico Discreto y Reportes (En Progreso)**

* **1. Generación de Matrices:** (Hecho) Crear tablas por tipo de cálculo y combinación de descriptores (ej: "máximo_cinemática_CMJ_Normal").
    * **1.1 Servicio `generate_discrete_summary_tables`**: (Hecho) Lógica para agrupar archivos por combinación de descriptores, leer stats, crear DataFrames y guardar CSVs/TSVs/SCSVs/XLSX.
    * **1.2 Botón en `StudyView`**: (Hecho) Añadir botón "Análisis Discreto".
    * **1.3 Vista `DiscreteAnalysisView`**: (Hecho) Crear vista para listar/mostrar/eliminar tablas generadas, con filtros y paginación.
* **2. Identificación de Grupos y Columnas Comunes:** (Hecho)
    * **2.1 `AnalysisService._identify_study_groups`**: (Hecho) Identifica grupos únicos por combinación de descriptores.
    * **2.2 `AnalysisService.get_discrete_analysis_groups`**: (Hecho) Expone grupos combinados a la UI.
    * **2.3 `AnalysisService.get_common_columns_for_groups`**: (Hecho) Encuentra columnas comunes en tablas CSV internas para grupos combinados.
* **3. Diálogo de Configuración de Análisis Individual:** (Hecho)
    * **3.1 Crear `ConfigureIndividualAnalysisDialog`**: (Hecho) UI para seleccionar Frecuencia, Cálculo, Grupos combinados (dinámico), Columna (dinámico), y supuestos (paramétrico/pareado).
    * **3.2 Integración con VIs**: (Hecho) Grupos combinados ahora usan formato "VI: Alias" y se seleccionan correctamente.
* **4. Diálogo de Gestión de Análisis Individual:** (Hecho)
    * **4.1 Crear `IndividualAnalysisManagerDialog`**: (Hecho) UI para listar, ver (gráfico estático/interactivo), eliminar análisis guardados y abrir carpeta.
    * **4.2 Botón en `DiscreteAnalysisView`**: (Hecho) Añadir botón para abrir el gestor.
* **5. Generación de Gráfico Boxplot Comparativo:** (Hecho)
    * **5.1 Función `create_comparison_boxplot`**: (Hecho) En `charting.py` usando seaborn/matplotlib.
    * **5.2 `AnalysisService.perform_individual_analysis`**: (Hecho) Lógica para leer datos de tablas CSV internas, preparar datos por grupo combinado y llamar a `create_comparison_boxplot`. Guarda gráfico PNG y config.json.
* **6. Implementación de Tests Estadísticos y Mejoras Gráficas:** (Hecho)
    * **6.1 Lógica en `perform_individual_analysis`**: (Hecho) Ejecutar tests (t-test/ANOVA/Wilcoxon/Kruskal/Friedman) usando `scipy.stats`.
    * **6.2 Mejorar `create_comparison_boxplot`**: (Hecho) Usar `swarmplot`, añadir leyenda, mostrar significancia (statannot para 2 grupos, p-valor general para >2).
    * **6.3 Integrar LEYENDAS con VIs**: (Hecho) Leyenda muestra nombres completos ("Grupo X - VI: Alias").
    * **6.4 Integrar EL EJE HORIZONTAL con VIs**: (Hecho) Eje X muestra etiquetas genéricas ("Grupo 1", "Grupo 2").
    * **6.5 Tests post-hoc**: (Pendiente) Considerar y añadir si es necesario.
* **7. Generación de Gráfico Interactivo (Plotly):** (Hecho)
    * **7.1 Añadir dependencia `plotly`**: (Hecho).
    * **7.2 Crear `create_interactive_comparison_boxplot`**: (Hecho) En `charting.py` para generar HTML.
    * **7.3 Modificar `perform_individual_analysis`**: (Hecho) Generar y guardar HTML.
    * **7.4 Anotaciones en Plotly**: (Pendiente - Fase B) Implementar lógica personalizada si se requiere.
* **8. Gestión de Análisis Guardados:** (Hecho)
    * **8.1 `AnalysisService.list_individual_analyses` / `delete_individual_analysis`**: (Hecho).
    * **8.2 Conectar UI `IndividualAnalysisManagerDialog`**: (Hecho) Cargar, ver PNG, ver HTML, eliminar, abrir carpeta. Mostrar grupos combinados y p-valor.
* **9. Reporte General (PDF):** (Pendiente) Implementar generación automática de PDF con análisis para combinaciones relevantes.
* **10. Corrección de Errores:** (En Progreso) Revisar y corregir errores conocidos (ej: formato cabeceras CSV, error generación tablas discretas, inconsistencia nombres archivo análisis individual).
* **11. Integración y Pruebas:** (Pendiente) Integrar y probar toda la funcionalidad de análisis discreto.

**Fase 3: Refactorización a Variables Independientes (VI)** (En Progreso)

* **1. Modificar Modelo de Estudio:** (Hecho)
    * **1.1 DB Conceptual**: (Hecho) Reemplazada columna `descriptores` por `independent_variables` (JSON TEXT) y añadida `aliases` (JSON TEXT) en tabla `estudios`.
    * **1.2 Repositorio (`StudyRepository`)**: (Hecho) Actualizados `_create_tables` (migración), `create_study`, `get_study_by_id`, `update_study` para manejar `independent_variables` y `aliases`.
    * **1.3 Servicio (`StudyService`)**: (Hecho) Actualizados métodos para manejar conversión Python <-> JSON para `independent_variables` y `aliases`. Añadidos `get_study_aliases`, `update_study_aliases`.
* **2. Refactorizar UI Creación/Edición Estudio (`StudyDialog`):** (Hecho)
    * **2.1 Flujo UI**: (Hecho) Implementada UI jerárquica para definir VIs y sus Descriptores (con botones '+', '🗑️').
    * **2.2 Restricciones Edición**: (Hecho) Deshabilitados añadir/eliminar VIs/Descriptores; permitido renombrar VIs.
    * **2.3 Botón Ayuda VI**: (Hecho) Añadido botón `(?)` coloreado que abre `kineviz/docs/help/study_dialog_iv_help.txt`.
* **3. Refactorizar Validación (`validators.py`):** (Hecho)
    * **3.1 Validador Datos Estudio**: (Hecho) Creado `validate_study_iv_data` (incluye regla anti-"Nulo").
    * **3.2 Validador Nombres Archivo**: (Hecho) Reescrito `validate_filename_for_study_criteria` para formato `PteXX [VAL_VI1]...[VAL_VIn] NN`, orden, valores permitidos (incl. "Nulo"), regla de al menos un descriptor no-Nulo. Devuelve `(bool, list[str|None])`.
    * **3.3 Eliminar Validador Antiguo**: (Hecho) Eliminado `validate_study_data`.
* **4. Integrar Validación:** (Hecho)
    * **4.1 `StudyDialog`**: (Hecho) Usa `validate_study_iv_data` en `save` (corregido bug edición).
    * **4.2 `FileService.add_files_to_study`**: (Hecho) Usa nuevo `validate_filename_for_study_criteria`.
* **5. Actualizar `FileService`:** (Hecho)
    * **5.1 `add_files_to_study`**: (Hecho) Obtiene estructura VI de `StudyService` para validación.
    * **5.2 `get_unique_study_parameters`**: (Hecho) Adaptado para extraer parámetros basados en la nueva estructura y nombres de archivo. Devuelve descriptores únicos encontrados por *posición* de VI.
* **6. Actualizar Vista Estudio (`StudyView`):** (Hecho)
    * **6.1 Mostrar VIs**: (Hecho) Añadido label para mostrar nombres de VIs.
    * **6.2 Mostrar Descriptores (Tooltip/Popup)**: (Hecho) Añadido botón `ℹ️` que muestra Descriptores por VI (con alias) en popup.
    * **6.3 Botón Ayuda General**: (Hecho) Añadido botón `(?)` que abre `kineviz/docs/help/study_view_help.txt`.
* **7. Refactorizar Gestión de Alias:** (Hecho)
    * **7.1 Mover a DB**: (Hecho) Implementado carga/guardado de alias por estudio en `StudyRepository` y `StudyService`.
    * **7.2 Adaptar `DescriptorAliasDialog`**: (Hecho) Carga/guarda alias vía `StudyService`.
    * **7.3 Limpiar `AppSettings`**: (Hecho) Eliminados métodos de alias globales.
* **8. Adaptar Servicios y UI de Análisis:** (Hecho)
    * **8.1 `AnalysisService._identify_study_groups`**: (Hecho) Crea claves de grupo combinadas (ej: "VI1=DescA;VI2=DescB").
    * **8.2 `AnalysisService` (Resto)**: (Hecho) Adaptados `get_discrete_analysis_groups`, `_get_data_for_parameters`, `perform_analysis`, `perform_individual_analysis`, `generate_report`, `generate_discrete_summary_tables`, `get_common_columns_for_groups` para usar claves combinadas y mostrar nombres de VI/alias.
    * **8.3 `ConfigureIndividualAnalysisDialog`**: (Hecho) Muestra/selecciona nombres de grupo legibles ("Grupo X - ..."), guarda claves originales.
    * **8.4 `IndividualAnalysisManagerDialog`**: (Hecho) Muestra nombres de grupo legibles ("Grupo X - ...").
* **9. Pruebas:** (Pendiente) Añadir/actualizar pruebas unitarias y de integración para validadores, servicios, UI refactorizada y lógica de agrupación/análisis.
* **10. Crear Archivos de Ayuda:** (Hecho)
    * **10.1 `docs/help/study_dialog_iv_help.txt`**: (Hecho)
    * **10.2 `docs/help/study_view_help.txt`**: (Hecho)

---

## Known Issues / Bugs

* **Edición de Estudio - Cambio de Criterios**: (Revisar en Fase 3) La validación de archivos existentes al cambiar criterios necesita ser reimplementada para la estructura de VI.
* **Análisis y Reportes**: (Revisar en Fase 2 y 3) La lógica de análisis y reportes necesita adaptarse a la estructura de VI y claves de grupo combinadas.
* **Configuración**: La gestión de alias debe moverse de `AppSettings` a la base de datos (Fase 3).
* **Limpieza de Directorios**: Funcionalidad básica existe, podría mejorarse.
* **Lectura de Datos Procesados**: Formato asumido en `_read_processed_file_data` podría ser más robusto.
* **Logging**: Implementado, pero puede refinarse.
* **Análisis Discreto - formato CSV/Cabeceras**: (Revisar en Fase 2) Corregir formato de cabeceras en tablas generadas.

---
*Este archivo se actualizará y se marcaran las tareas que se vayan realizando a medida que avance el desarrollo.*
