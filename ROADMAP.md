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

## Fase 5: Mejoras Incrementales - Descriptores y Detección de Frecuencia (Completada)

*   [x] **Modificación de Identificador de Frecuencias**: Cambiar la detección de tipo de frecuencia (Cinemática, Cinética, Electromiográfica) basada en metadatos del archivo ("Model Outputs", "Force Plate"). (Tarea 1)
*   [x] **Implementación de Descriptores**: Reemplazar el sistema de "Tipos de Prueba" y "Periodos de Prueba" por un sistema flexible de "Descriptores" definidos por el usuario al crear/editar estudios. (Tarea 2 - UI y DB)
*   [x] **Modificación de Etiquetas Post-Carga**: Permitir al usuario asignar alias o nombres descriptivos a los descriptores detectados en los archivos, para visualización en análisis y reportes. (Tarea 3)
*   [x] **Integración Completa**: Asegurar que los cambios en la detección de frecuencia y el sistema de descriptores se integren correctamente en la carga de archivos, validación, análisis, reportes y UI. (Tarea 4)

## Fase 6: Análisis Estadístico Discreto y Reportes Avanzados (Pendiente)

### **Visión General**
Esta funcionalidad está pensada para automatizar el análisis estadístico de datos discretos (por ejemplo, valores máximos, mínimos y rangos) obtenidos de estudios, en donde cada estudio puede contener múltiples archivos por paciente y por intento. Principalmente, se enfoca en datos cinemáticos, generando tanto tablas como gráficos para comparar estadísticamente distintos descriptores según las etiquetas asignadas.

### Flujo del Proceso
1.  **Extracción y Normalización de Datos**
    *   Se genera una tabla para cada cálculo (máximo, mínimo, rango) basada en los datos originales del estudio.
    *   Cada tabla contendrá:
        *   El tipo de cálculo realizado (por ejemplo, máximo).
        *   Filas que representan a cada paciente (con sus intentos).
        *   Columnas que corresponden a las variables repetidas presentes en cada archivo (p.ej.: posiciones X, Y, Z agrupadas por articulación y unidad de medida).

2. **Interacción y Configuración del Análisis:**
    *   **Paso 1: Definir el Diseño del Estudio**
        *   Preguntar al usuario si los datos son **pareados** o **independientes**.
        *   Preguntar si los datos se pueden asumir normalmente distribuidos o si se requiere la aplicación de una prueba automática para verificar la normalidad.
    *   **Paso 2: Seleccionar el Método Estadístico**
        *   **Si se comparan dos descriptores:**
            *   Utilizar t-test pareado o t-test para muestras independientes, según corresponda.
        *   **Si se comparan tres o más descriptores:**
            *   Utilizar ANOVA (o su equivalente no paramétrico en caso de datos no normales).
    *   **Paso 3: Configuración Adicional**
        *   Elegir las variables y etiquetas que se utilizarán para generar las tablas y gráficos.
        *   Guardar la configuración para análisis individual y generar reportes generales en PDF con las combinaciones de gráficos y tablas pertinentes.

### Gráficos y Tablas
1.  **Generación de Gráficos y Reportes:**
    *   Se generan gráficos que reflejen el análisis de las variables desginadas
    *   Se incorpora la opción de utilizar dos o mas descriptores del estudio según lo definido por el usuario.
    *   Los reportes generales se crean automáticamente en formato PDF, agrupados por tipo de cálculo. Es decir habrían 3 archivos si hay 3 calculos Maximo, Minimo, Rango, cada archivo muestra como ese calculo interactua con los descriptores en un gráfico de boxplot para cada combinación de descriptores y el calculo fijo. Lo que quiere decir que se traducirian en varios gráficos en un archivo de una manera rapida y sencilla.

2.  **Generación de Archivos y Acceso**
    *   Al hacer clic en el botón “Análisis Continuo” (para la parte de tablas discretas) se generan múltiples archivos automáticamente:
        *   Cada archivo corresponde a un cálculo (por ejemplo, “Máximo – Cinemática – Estudio: Testing” y "Minimo - Cinemática - Estudio: Testing").
        *   Las tablas generadas se alojan en una estructura de carpetas accesible mediante un botón en la nueva ventana de análisis. Algo asi como Estudios/[NOMBRE_DEL_ESTUDIO]/Analisis Discreto/Individual/[CALCULO]/[FRECUENCIA]/[ARCHIVOS]

3.  **Análisis Individual y Reporte General**
    *   **Análisis Individual:**
        *   Se abre una ventana donde el usuario define parámetros tales como:
            *   El cálculo a utilizar.
            *   Un calculo de referencia (fijo) para comparar con otros descriptores (que pueden ser n descriptores extras según permita el estudio) en un boxplot, estos descriptores seran también los puntos del gráfico, el calculo será el eje vertical y los distintos descriptores estarán en el eje horizontal.
            *   La variable (columna) a graficar.
        *   Se guarda la configuración y se despliega una lista de análisis previos, con opciones de búsqueda, filtrado y visualización (incluyendo un botón para abrir la carpeta de gráficos y tablas).

    *   **Reporte General:**
        *   Se genera un PDF automático que incluye todos los posibles gráficos generados para cada cálculo, utilizando todas las variables y combinaciones de descriptores disponibles en el estudio.
        *   La nomenclatura de los archivos y carpetas sigue una estructura jerárquica basada en el cálculo y el descriptor fijo.

### Consideraciones Técnicas
- **Herramientas:** Pandas, Matplotlib/Seaborn, SciPy.
- **Enfoque Inicial:** Datos cinemáticos.
- **Exclusiones:** Columnas "Frame", "Sub Frame", "Tiempo".
- **Normalización:** No necesaria para análisis discreto.

### Ejemplo de archivo de tabla resultante en "TABLA RESUMEN CINEMÁTICA CMJ MAX.csv"
### Ejemplo de gráfico resultante en "H Salto.png"

## Fase 7: Refinamientos y Finalización (Antigua Fase 4)

*   [x] Implementar `ConfigDialog` (`kineviz/ui/dialogs/config_dialog.py`) y `AppSettings` (`kineviz/config/settings.py`).
*   [x] Mejorar manejo de errores y logging (`kineviz/utils/logger.py`). (Integrado en la mayoría de módulos)
*   [ ] Añadir pruebas unitarias e de integración (`tests/`). (Inicio: validadores, StudyRepository, FileService, AnalysisService) - **Necesita más cobertura, especialmente tras refactor VI.**
*   [ ] Completar documentación (`docs/`).
*   [x] Limpiar código remanente de `interfaz.py` y `lectura.py`.
*   [ ] Revisión final de estilos y UX.

## Fase 8: Refactorización a Variables Independientes (En Progreso)

*   **1. Modificar Modelo de Estudio:**
    *   [x] Reemplazar columna `descriptores` por `independent_variables` (JSON TEXT) en DB (conceptual).
    *   [x] Actualizar `StudyRepository` y `StudyService` para manejar la nueva estructura JSON `[{"name": "VI_Nombre", "descriptors": ["Desc1", "Desc2"]}]`.
*   **2. Refactorizar UI Creación/Edición Estudio (`StudyDialog`):**
    *   [x] Reemplazar entrada de descriptores por flujo: Num VIs -> (Nombre VI -> Num Descriptores -> [Nombres Descriptores]) x Num VIs.
    *   [x] Implementar restricciones de edición (solo nombre VI editable inicialmente).
    *   [x] Añadir tooltip/info sobre uso de "Nulo".
*   **3. Refactorizar Validación (`validators.py`):**
    *   [x] Reescribir `validate_filename_for_study_criteria` para nuevo formato (`PteXX VI1 VI2... VIn IntentoNN`), orden estricto, valores permitidos (incl. "Nulo"), y regla de al menos un descriptor no-Nulo.
    *   [x] Eliminar `validate_study_data` (lógica movida a `StudyDialog`).
*   **4. Actualizar Vista Estudio (`StudyView`):**
    *   [x] Mostrar nombres de VIs.
    *   [x] Añadir botón/tooltip para mostrar descriptores por VI.
*   **5. Integrar con Servicios:**
    *   [ ] Actualizar `FileService.add_files_to_study` (usa nuevo validador). **(Pendiente - requiere `FileService`)**
    *   [x] Actualizar `AnalysisService._identify_study_groups` (crear claves combinadas: "DescVI1_DescVI2_...").
    *   [x] Asegurar que `generate_discrete_summary_tables` y `perform_individual_analysis` usen las nuevas claves de grupo.
*   **6. Pruebas:** (Pendiente) Añadir pruebas de integración para la nueva validación y flujo.

---

## Diccionario de Tareas (Fase 5+)

**Fase 5: Mejoras Incrementales - Descriptores y Detección de Frecuencia**

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

**Fase 6: Análisis Estadístico Discreto y Reportes Avanzados**

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
