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
└── examples/             # Ejemplos de uso

## Diccionario de Tareas

**Fase 1: Mejoras Incrementales - Descriptores y Detección de Frecuencia**

*   **1. Implementar detección automática de tipo de frecuencias basada en metadatos del archivo. (Completado - 91ffd0a)**
    *   **Detalle**: Modificada la lógica en `kineviz.core.data_processing.file_handlers.leer_seccion` y `kineviz.core.services.file_service._process_and_copy_file` para identificar Cinemática ("Model Outputs") y Cinética ("Force Plate").
    *   **1.1 Implementación de identificador de archivo para Cinemática**: (Hecho).
    *   **1.2 Implementación de identificador de archivo para Cinética**: (Hecho).
    *   **1.3 Implementación de identificador de archivo para Electromiográfica**: (Pendiente) de confirmación del formato/identificador.

*   **2. Implementación para crear/editar estudio con descriptores extra. (Completado)**
    *   **Detalle**: Modificado `kineviz.ui.dialogs.study_dialog.py` para reemplazar los campos de entrada de "Tipos de Prueba" y "Periodos de Prueba" por una sección dinámica que permita añadir/eliminar campos de texto para "Descriptores".
    *   **2.1 Soportar múltiples etiquetas de descriptores**: (Hecho) UI modificada para añadir/eliminar campos. Tabla `estudios` modificada para usar columna `descriptores` (TEXT, separado por comas). Repositorio y Servicio actualizados.
    *   **2.2 Validación de descriptores**: (Hecho) Añadida validación en `kineviz.ui.utils.validators.validate_study_data` para evitar descriptores vacíos o duplicados exactos.

*   **3. Implementación para modificar nombres de etiquetas de descriptores post-carga.** (Completado)
    *   **Detalle**: Añadir una nueva funcionalidad (posiblemente en `kineviz.ui.views.study_view.py` o un nuevo diálogo) que permita al usuario ver los descriptores *detectados* en los nombres de archivo de un estudio y asignarles un "alias" o "nombre descriptivo" (ej: "CMJ" -> "Salto Contra Movimiento"). Este alias se usaría para mostrar en gráficos y reportes. El almacenamiento de estos alias podría ser en `config.ini` o en la base de datos. *Nota: Inicialmente, esta modificación es solo visual.*
    *   **3.1 Añadir gestión de alias en `AppSettings`**: (Hecho) Métodos para leer/escribir sección `[DESCRIPTOR_ALIASES]` en `config.ini`.
    *   **3.2 Crear `DescriptorAliasDialog`**: (Hecho) Diálogo para ver descriptores detectados y asignar/guardar alias usando `AppSettings`.
    *   **3.3 Añadir botón en `StudyView` para abrir el diálogo**: (Hecho).
    *   **3.4 Mostrar alias en `StudyView`**: (Hecho).

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

**Fase 2: Análisis Estadístico Discreto y Reportes Avanzados**

*   **1. Generación de Matrices:** (En Progreso) Crear tablas por tipo de cálculo y descriptor (ej: "máximo_cinemática_obesidad").
    *   **1.1 Servicio `generate_discrete_summary_tables`**: (Hecho) Lógica para agrupar archivos, leer stats, crear DataFrames y guardar CSVs (inicialmente para Cinemática).
    *   **1.2 Botón en `StudyView`**: (Hecho) Añadido botón "Análisis Discreto".
    *   **1.3 Vista `DiscreteAnalysisView`**: (Hecho) Creada vista básica con botón para generar tablas.
    *   **1.4 Listar/Mostrar Tablas Generadas**: (En Progreso)
        *   (Hecho) Implementado Treeview básico y lógica para mostrar/ver/eliminar archivos CSV.
        *   (Hecho) Añadidas columnas: Nombre Archivo, Tipo Cálculo, Descriptores, Fecha Modificación, Tamaño.
        *   (Hecho) Añadida barra de búsqueda (por nombre, cálculo, descriptores).
        *   (Hecho) Añadido filtro por Tipo de Cálculo.
        *   (Hecho) Añadida paginación configurable (`discrete_tables_per_page` en `config.ini`).
 *   **2. Identificación de Grupos y Columnas Comunes:** (Hecho)
     *   (Hecho) `AnalysisService._identify_study_groups`: Identifica grupos únicos por descriptores.
     *   (Hecho) `AnalysisService.get_discrete_analysis_groups`: Expone grupos a la UI.
     *   (Hecho) `AnalysisService.get_common_columns_for_groups`: Encuentra columnas comunes en tablas CSV.
 *   **3. Diálogo de Configuración de Análisis Individual:** (Hecho)
     *   (Hecho) Creado `ConfigureIndividualAnalysisDialog` con UI para seleccionar Frecuencia, Cálculo, Grupos (dinámico), Columna (dinámico), y supuestos (paramétrico/pareado).
     *   (Hecho) Lógica básica para cargar grupos y columnas disponibles.
 *   **4. Diálogo de Gestión de Análisis Individual:** (Hecho)
     *   (Hecho) Creado `IndividualAnalysisManagerDialog` con UI básica (lista placeholder, botones).
     *   (Hecho) Añadido botón "Análisis Individual" en `DiscreteAnalysisView` para abrir el gestor.
 *   **5. Generación de Gráfico Boxplot Comparativo:** (Hecho)
     *   (Hecho) Añadida función `create_comparison_boxplot` en `charting.py`.
     *   (Hecho) `AnalysisService.perform_individual_analysis`: Implementada lógica básica para leer datos de tablas CSV, preparar datos por grupo y llamar a `create_comparison_boxplot`. Guarda gráfico y config.json.
 *   **6. Implementación de Tests Estadísticos y Mejoras Gráficas:** (En Progreso)
     *   (Hecho) Añadida lógica en `perform_individual_analysis` para ejecutar tests principales (t-test/ANOVA/Wilcoxon/Kruskal/Friedman) usando `scipy.stats`.
     *   (Hecho) Modificado `create_comparison_boxplot` para usar `seaborn` y `swarmplot`.
     *   (Hecho) Añadida leyenda de grupos al boxplot.
     *   (Hecho) Reintroducido `statannot` para mostrar significancia (NS, *, **) en comparaciones de 2 grupos en gráfico estático (PNG). P-valor general mostrado como texto para >2 grupos.
     *   (Pendiente) Considerar tests post-hoc y anotaciones pairwise para >2 grupos si es necesario (en gráfico estático).
 *   **7. Generación de Gráfico Interactivo (Plotly):** (En Progreso)
     *   (Hecho) Añadida dependencia `plotly`.
     *   (Hecho) Creada función `create_interactive_comparison_boxplot` en `charting.py` para generar HTML con Plotly (sin anotaciones de significancia).
     *   (Hecho) Modificado `perform_individual_analysis` para generar y guardar `boxplot_interactive.html`.
     *   (Pendiente) Implementar lógica personalizada para añadir anotaciones de significancia en Plotly (complejo, Fase B).
 *   **8. Gestión de Análisis Guardados:** (En Progreso)
     *   (Hecho) Implementado `AnalysisService.list_individual_analyses` y `delete_individual_analysis`.
     *   (Hecho) Conectada UI de `IndividualAnalysisManagerDialog` (cargar, ver gráfico PNG, eliminar, abrir carpeta).
     *   (Hecho) Añadido botón "Ver Gráfico Interactivo" en `IndividualAnalysisManagerDialog` para abrir HTML en navegador.
     *   (Hecho) Modificada tabla en `IndividualAnalysisManagerDialog`: reemplazada columna "Grupo X" por "Grupos Comparados". Corregido bug de encabezados.
     *   (Hecho) Añadida columna "Valores Clave" para mostrar resultado del test (p-valor). Guardado p-valor en `config.json`.
 *   **9. Reporte General:** (Pendiente) Implementar generación automática de PDF con todas las combinaciones.
     *   **Nota**: Necesitará preguntar/configurar los supuestos (paramétrico/pareado) para aplicar las comparaciones correctas.
 *   **10. Corrección de Errores:** (En Progreso)
     *   (Hecho) Corregido error de reconocimiento de columnas (prefijo `PteXX:`) modificando la generación de tablas resumen y la lectura de cabeceras.
 *   **11. Integración y Pruebas:** (Pendiente) Integrar la funcionalidad en la plataforma y realizar pruebas de integración.

## Fase 3: Refactorización a Variables Independientes (Completada - Parcialmente)
*   **1. Modificar Modelo de Estudio:** (Completado)
    *   **1.1 DB Conceptual**: (Hecho) Reemplazada columna `descriptores` por `independent_variables` (JSON TEXT).
    *   **1.2 Repositorio (`StudyRepository`)**: (Hecho) Actualizados métodos `create_study`, `get_study_by_id`, `update_study` para usar
`independent_variables`. Añadida migración simple.
    *   **1.3 Servicio (`StudyService`)**: (Hecho) Actualizados métodos `create_study`, `get_study_details`, `update_study` para manejar la conversión entre estructura Python y JSON string.
*   **2. Refactorizar UI Creación/Edición Estudio (`StudyDialog`):** (Completado)
    *   **2.1 Flujo UI**: (Hecho) Reemplazada sección de descriptores por UI dinámica para definir VIs y sus descriptores.
    *   **2.2 Restricciones Edición**: (Hecho) Número de VIs y descriptores no editables al modificar estudio; nombre de VI sí editable.
    *   **2.3 Tooltip "Nulo"**: (Hecho) Añadido icono de información y tooltip explicando el uso de "Nulo".
    *   **2.4 Validación Interna**: (Hecho) Movida y adaptada la validación de datos del estudio al método `save` del diálogo.
*   **3. Refactorizar Validación (`validators.py`):** (Completado)
    *   **3.1 Validador Nombres Archivo**: (Hecho) Reescribir `validate_filename_for_study_criteria` para validar formato `PteXX VI1...VIn NN`, orden, valores permitidos (incl. "Nulo"), y regla de al menos un descriptor no-Nulo. Devuelve tupla `(bool, list[str|None])`.
    *   **3.2 Eliminar Validador Estudio**: (Hecho) Eliminada función `validate_study_data`.
*   **4. Actualizar Vista Estudio (`StudyView`):** (Completado)
    *   **4.1 Mostrar Nombres VI**: (Hecho) Añadido label para mostrar nombres de VIs definidos.
    *   **4.2 Mostrar Descriptores (Tooltip)**: (Hecho) Añadido botón `ℹ️` con tooltip que muestra los descriptores asociados a cada VI.
*   **5. Integrar con Servicios:** (En Progreso)
    *   **5.1 `FileService.add_files_to_study`**: (Pendiente) Actualizar para usar el nuevo `validate_filename_for_study_criteria` y la
estructura VI obtenida de `StudyService`. **(Requiere `FileService`)**
    *   **5.2 `AnalysisService._identify_study_groups`**: (Hecho) Modificado para usar el nuevo validador y crear claves de grupo combinadas (ej:"CMJ_Normal", "SaltoAlto_Nulo").
    *   **5.3 `AnalysisService.generate_discrete_summary_tables`**: (Hecho) Modificado para usar las nuevas claves de grupo combinadas al agrupar archivos y nombrar las tablas generadas. 
    *   **5.4 `AnalysisService.perform_individual_analysis`**: (Hecho) Modificado para recibir y usar las claves de grupo combinadas al leer las tablas CSV internas.
    *   **5.5 `AnalysisService.get_discrete_analysis_groups`**: (Hecho) Modificado para devolver las claves combinadas únicas.
    *   **5.6 `AnalysisService.get_common_columns_for_groups`**: (Hecho) Adaptado para recibir claves combinadas (lógica interna sin cambios).
    *   **5.7 `AnalysisService.generate_report`**: (Hecho) Adaptado para usar alias (si se reintroducen) o claves combinadas en títulos leyendas.
*   **6. Adaptar UI de Análisis:** (Completado)
    *   **6.1 `ConfigureIndividualAnalysisDialog`**: (Hecho) Modificado para mostrar y seleccionar las claves de grupo combinadas.
    *   **6.2 `IndividualAnalysisManagerDialog`**: (Hecho) Modificado para mostrar las claves de grupo combinadas en la columna "Grupos  Comparados".     
*   **7. Pruebas:** (Pendiente) Añadir/actualizar pruebas unitarias y de integración para la nueva lógica de validación, creación/edición de estudios y agrupación en análisis.

---

## Known Issues / Bugs

*   **Edición de Estudio - Cambio de Criterios**: Al editar un estudio y cambiar los `Tipos de Prueba` o `Periodos de Prueba`, no se validan ni eliminan automáticamente los archivos existentes que ya no cumplen con los nuevos criterios. (Ver Fase 2 - Editar Estudio).
*   **Análisis y Reportes**: La lógica de análisis, generación de PDF y gestión básica de reportes (listar, ver, eliminar) está implementada.
*   **Configuración**: Implementada la gestión básica de configuración (`AppSettings`, `ConfigDialog`) para paginación. El botón de reseteo global está conectado.
*   **Limpieza de Directorios**: La limpieza de directorios vacíos (paciente, frecuencia) después de eliminar el último archivo dentro de ellos funciona, pero podría mejorarse para manejar casos borde o errores de permisos de forma más robusta.
*   **Validación de Pacientes para Análisis**: La validación ahora se basa en los parámetros únicos extraídos de archivos procesados válidos. Si un estudio tiene archivos pero no cumplen los criterios o solo tiene archivos OG, no permitirá el análisis.
*   **Lectura de Datos Procesados**: La función `_read_processed_file_data` en `AnalysisService` asume un formato específico (';' como separador, 4 líneas de header, 3 de stats). Podría ser más robusta o configurable.
*   **Logging**: El logging está implementado en la mayoría de los módulos. Se podrían añadir más mensajes de `DEBUG` o refinar los niveles existentes.
*   **Análisis Discreto - formato CSV**:
    *   Primera línea de comas vacías en el archivo de ejemplo.
    *   Nombres de las primeras dos filas de cabecera ("Atributo", "Columna" vs. vacía, "PteXX:Articulacion").
    *   La primera columna (índice) se escribe sin nombre explícito en la fila de datos (comportamiento actual después de 1.5).

---
*Este archivo se actualizará y se marcaran con una X las tareas que se vayan realizando a medida que avance el desarrollo.*
