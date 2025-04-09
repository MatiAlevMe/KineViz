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
Esta funcionalidad está pensada para automatizar el análisis estadístico de datos discretos (por ejemplo, valores máximos, mínimos y rangos) obtenidos de estudios, en donde cada estudio puede contener múltiples archivos por paciente y por intento. Principalmente, se enfoca en datos cinemáticos, generando tanto tablas como gráficos (barras y boxplots) para comparar estadísticamente distintos descriptores según las etiquetas asignadas.

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
    *   Se generan gráficos que reflejen el análisis continuo de las variables desginadas
    *   Se incorpora la opción de comparar dos o mas descriptores del estudio según lo definido por el usuario.
    *   Los reportes generales se crean automáticamente en formato PDF, agrupados por tipo de cálculo. Es decir habrían 3 archivos si hay 3 calculos Maximo, Minimo, Rango, cada archivo muestra como ese calculo interactua en cada paciente con su intento por cada una de las articulación y su posición x, y o z del estudio, cada articulación y la posición x, y o z son distintas gráficas, y en cada gráfica se muestran distintas lineas para cada descriptor y como por ejemplo la persona obesa tiene un maximo mayor entonces puede que su angulo de inclinación para una articulación sea mayor que el de un normopeso, lo que quiere decir que en el gráfico se veria representado por una diferencia en el angulo de la linea formada por cada descriptor.

2.  **Generación de Archivos y Acceso**
    *   Al hacer clic en el botón “Análisis Continuo” (para la parte de tablas discretas) se generan múltiples archivos automáticamente:
        *   Cada archivo corresponde a un cálculo (por ejemplo, “Máximo – Cinemática – Estudio: Testing” y "Minimo - Cinemática - Estudio: Testing").
        *   Las tablas generadas se alojan en una estructura de carpetas accesible mediante un botón en la nueva ventana de análisis. Algo asi como Estudios/[NOMBRE_DEL_ESTUDIO]/Analisis Discreto/Individual/[CALCULO]/[FRECUENCIA]/[ARCHIVOS]

3.  **Análisis Individual y Reporte General**
    *   **Análisis Individual:**
        *   Se abre una ventana donde el usuario define parámetros tales como:
            *   El cálculo a utilizar.
            *   Un calculo de referencia (fijo) para comparar con otros descriptores (que pueden ser n descriptores extras según permita el estudio) en un boxplot, estos descriptores seran las lineas del gráfico, y las columnas serán uno de los ejes, el otro sera el calculo.
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

*   **1. Generación de Matrices:** (Pendiente) Crear tablas por tipo de cálculo y descriptor (ej: "máximo_cinemática_obesidad").
*   **2. Selector de Variables y Etiquetas:** (Pendiente) Permitir que el usuario elija las variables a utilizar en el análisis.
*   **3. Interacción sobre Datos Pareados:** (Pendiente) Preguntar si los datos son pareados o independientes.
*   **4. Chequeo de Distribución:** (Pendiente) Permitir al usuario indicar si confía en que sus datos son normales o si se debe realizar una prueba automática (ej: Shapiro-Wilk).
*   **5. Selección del Test Estadístico:** (Pendiente)
    *   **5.1 Implementar t-test** (pareado o independiente) para comparación de dos descriptores.
    *   **5.2 Implementar ANOVA** (o test no paramétrico) para tres o más descriptores.
*   **6. Generación de Gráficos:** (Pendiente) Implementar gráficos de barra y boxplot.
*   **7. Exportación y Reporte:** (Pendiente) Exportar tablas en CSV/Excel/txt y generar reportes en PDF.
*   **8. Análisis Individual:** (Pendiente)
    *   **8.1 Crear ventana/diálogo** para configuración de análisis individual (cálculo, descriptor fijo, descriptores variables, variable a graficar).
    *   **8.2 Implementar guardado/carga** de configuraciones de análisis individual.
    *   **8.3 Crear lista** de análisis guardados con búsqueda/filtrado.
    *   **8.4 Añadir botón** para abrir carpetas de tablas/gráficos de análisis individuales.
*   **9. Reporte General:** (Pendiente) Implementar generación automática de PDF con todas las combinaciones.
*   **10. Integración y Pruebas:** (Pendiente) Integrar la funcionalidad en la plataforma y realizar pruebas de integración.

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
