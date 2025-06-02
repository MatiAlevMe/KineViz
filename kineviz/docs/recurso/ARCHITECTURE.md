# Arquitectura de KineViz

## 1. Introducción
KineViz es una aplicación de escritorio diseñada para la gestión, procesamiento y análisis de datos kinesiológicos. Su objetivo principal es facilitar a los investigadores y profesionales la organización de estudios, el manejo de archivos de datos crudos y procesados, y la realización de análisis estadísticos tanto discretos como continuos (SPM).

## 2. Estructura del Proyecto
La aplicación sigue una estructura modular para separar responsabilidades:
*   `kineviz/`: Directorio raíz del código fuente.
    *   `app.py`: Punto de entrada de la aplicación (inicia `MainWindow`).
    *   `core/`: Contiene la lógica de negocio central y el dominio de la aplicación.
    *   `ui/`: Responsable de la interfaz de usuario y la interacción con el usuario.
    *   `database/`: Maneja la persistencia de datos, principalmente la base de datos SQLite.
    *   `config/`: Gestiona la configuración de la aplicación.
    *   `utils/`: Utilidades generales como el sistema de logging.
    *   `docs/`: Documentación del proyecto, incluyendo este archivo y el roadmap.

## 3. Módulos Principales y Responsabilidades

### 3.1. `kineviz.core` - Lógica de Negocio y Dominio
*   **`core.services`**: Orquesta las operaciones y la lógica de negocio.
    *   `StudyService`: Gestiona las operaciones CRUD (Crear, Leer, Actualizar, Eliminar) para los estudios. Maneja los metadatos del estudio, la definición de Variables Independientes (VIs), y los alias de los descriptores.
    *   `FileService`: Administra las operaciones de archivos dentro de los estudios, incluyendo la adición, eliminación, listado y procesamiento de archivos crudos. También extrae parámetros únicos (como frecuencias y descriptores) de los archivos procesados.
    *   `AnalysisService`: Contiene la lógica para todos los tipos de análisis (discreto, individual, continuo). Esto incluye la agregación de datos, cálculos estadísticos (utilizando `scipy.stats` y `spm1d`), generación de reportes en PDF (con `reportlab`) y gráficos (con `matplotlib`, `seaborn`, `plotly`).
*   **`core.data_processing`**: Módulos encargados del procesamiento y manejo de datos.
    *   `file_handlers`: Responsable de leer e interpretar archivos de datos crudos (ej. `.txt`), extraer metadatos, identificar el tipo de frecuencia (Cinemática, Cinética, EMG) y realizar el procesamiento inicial para generar archivos estandarizados.
    *   `processors`: Contiene funciones de utilidad para la transformación de datos, cálculos estadísticos básicos (máximo, mínimo, rango) sobre DataFrames de pandas, y formateo de valores.
    *   `directory_manager`: Gestiona la creación y la estructura de los directorios para los estudios y los pacientes dentro del sistema de archivos.
*   **`core.exceptions`**: Define clases de excepciones personalizadas para un manejo de errores más específico dentro de la aplicación (ej. `FileNotFoundError`, `InvalidFileFormatError`).

### 3.2. `kineviz.ui` - Capa de Interfaz de Usuario (Tkinter)
*   **`ui.main_window.py` (`MainWindow`)**: Es la ventana principal de la aplicación. Orquesta la navegación entre las diferentes vistas y diálogos. Mantiene instancias de los servicios principales (`StudyService`, `FileService`, `AnalysisService`) y `AppSettings`.
*   **`ui.views`**: Vistas principales que ocupan la mayor parte de la ventana.
    *   `LandingPage`: Vista inicial que se muestra cuando no existen estudios en la aplicación.
    *   `MainView`: Muestra la lista paginada de estudios existentes, permitiendo buscar y acceder a ellos.
    *   `StudyView`: Presenta una vista detallada de un estudio específico. Incluye un navegador de archivos (`FileBrowser`), opciones para agregar archivos, gestionar alias, y acceder a los módulos de análisis.
    *   `DiscreteAnalysisView`: Interfaz para gestionar y visualizar los resultados de los análisis discretos (tablas resumen generadas).
    *   *(Futuro: `ContinuousAnalysisView` para mostrar resultados de análisis SPM)*.
*   **`ui.dialogs`**: Ventanas modales que se utilizan para tareas específicas y entrada de datos.
    *   `StudyDialog`: Para crear nuevos estudios o editar los metadatos de estudios existentes, incluyendo la definición de Variables Independientes (VIs) y sus descriptores.
    *   `FileDialog`: Permite al usuario seleccionar y agregar archivos de datos a un estudio específico.
    *   `DescriptorAliasDialog`: Facilita la gestión (creación, edición, eliminación) de alias para los descriptores de las VIs de un estudio.
    *   `ConfigureIndividualAnalysisDialog`: Diálogo para configurar los parámetros de un análisis discreto individual (selección de frecuencia, cálculo, columna, grupos a comparar, y supuestos estadísticos).
    *   `IndividualAnalysisManagerDialog`: Permite listar, visualizar (gráficos estáticos e interactivos), eliminar y abrir la carpeta de resultados de los análisis individuales guardados.
    *   `ContinuousAnalysisConfigDialog`: Diálogo para configurar los parámetros de un análisis continuo (SPM), como la frecuencia de datos, la variable a analizar y los grupos de descriptores a comparar.
    *   `ConfigDialog`: Permite al usuario modificar configuraciones globales de la aplicación (ej. elementos por página) que se guardan en `config.ini`.
    *   `AnalysisDialog`: (Obsoleto/Comentado) Diálogo anterior para análisis, reemplazado por funcionalidades más específicas.
*   **`ui.widgets`**: Componentes de UI reutilizables.
    *   `FileBrowser`: Widget para listar, filtrar y gestionar archivos dentro de un estudio, con paginación.
    *   `charting`: Módulo para generar gráficos estáticos (con `matplotlib`/`seaborn`) e interactivos (con `plotly`), como boxplots y gráficos de barras.
*   **`ui.utils`**: Utilidades específicas de la interfaz de usuario.
    *   `validators`: Contiene funciones para validar entradas del usuario, nombres de archivo según criterios de VIs, y la consistencia de los datos del estudio.

### 3.3. `kineviz.database` - Persistencia de Datos
*   **`database.repositories.StudyRepository`**: Implementa el patrón Repositorio para abstraer las interacciones con la base de datos SQLite (`kineviz.db`). Es responsable de la creación de tablas y las operaciones CRUD para los datos de los estudios (metadatos, VIs, alias).

### 3.4. `kineviz.config` - Configuración de la Aplicación
*   **`config.settings.AppSettings`**: Gestiona la carga y el guardado de las configuraciones de la aplicación desde y hacia el archivo `config.ini`. Proporciona una interfaz para acceder a estos ajustes.
*   **`config.ini`**: Archivo de texto plano que almacena configuraciones persistentes como el número de elementos por página.

### 3.5. `kineviz.utils` - Utilidades Generales
*   **`utils.logger.setup_logging`**: Configura el sistema de logging para la aplicación, definiendo el nivel de log y el formato de los mensajes, guardando los logs en archivos.

## 4. Flujos de Datos Clave (Ejemplos)

*   **Creación de un Nuevo Estudio:**
    1.  `MainWindow` invoca `show_create_study_dialog()`.
    2.  Se abre `StudyDialog`. El usuario ingresa los metadatos del estudio y define las Variables Independientes (VIs) y sus descriptores.
    3.  Al guardar, `StudyDialog` llama a `StudyService.create_study()` con los datos ingresados.
    4.  `StudyService` valida los datos (usando `validators.validate_study_iv_data`), y luego interactúa con `StudyRepository.create_study()`.
    5.  `StudyRepository` escribe la información del nuevo estudio en la base de datos SQLite.
    6.  `DirectoryManager.crear_estructura_estudio()` (llamado desde `StudyService` o `StudyRepository`) crea la carpeta física para el estudio en el sistema de archivos.
    7.  `MainWindow` refresca la `MainView` para mostrar el nuevo estudio.

*   **Adición de Archivos a un Estudio:**
    1.  Desde `StudyView`, el usuario hace clic en "Agregar Archivos", lo que abre `FileDialog`.
    2.  El usuario selecciona uno o más archivos de datos.
    3.  `FileDialog` llama a `FileService.add_files_to_study()` con los archivos seleccionados y el ID del estudio.
    4.  `FileService`:
        a.  Obtiene las VIs del estudio desde `StudyService`.
        b.  Valida los nombres de los archivos contra las VIs y sus descriptores (usando `validators.validate_filename_for_study_criteria`).
        c.  Valida contra el número de sujetos e intentos definidos en el estudio.
        d.  Valida contra las reglas de combinación y obligatoriedad de las VIs (usando `validators.validate_files_for_vi_rules`).
        e.  Si las validaciones son exitosas, copia los archivos originales a la estructura de carpetas del estudio (`estudios/<nombre_estudio>/<nombre_paciente>/origen/`).
        f.  Procesa cada archivo (usando `file_handlers.leer_seccion`) para extraer datos, identificar la frecuencia, y generar un archivo procesado estandarizado en la carpeta correspondiente (ej. `estudios/<nombre_estudio>/<nombre_paciente>/<frecuencia>/`).
    5.  `StudyView` refresca el `FileBrowser` para mostrar los nuevos archivos.

*   **Realización de un Análisis Discreto Individual:**
    1.  Desde `DiscreteAnalysisView`, el usuario accede a `IndividualAnalysisManagerDialog` y luego a `ConfigureIndividualAnalysisDialog`.
    2.  El usuario configura los parámetros del análisis: nombre, frecuencia, cálculo (Maximo, Minimo, Rango), columna de datos (variable), grupos a comparar (basados en VIs), y supuestos estadísticos (paramétrico, pareado).
    3.  El diálogo llama a `AnalysisService.perform_individual_analysis()` con la configuración.
    4.  `AnalysisService`:
        a.  Lee los datos relevantes de las tablas de resumen CSV previamente generadas (ubicadas en `estudios/<nombre_estudio>/Analisis Discreto/Tablas/<frecuencia>/`).
        b.  Agrupa los datos según los grupos seleccionados. Si es un análisis de efecto principal (modo "1VI"), agrega datos de múltiples tablas combinadas.
        c.  Realiza la prueba estadística seleccionada (ej. t-test, ANOVA, Wilcoxon, Kruskal-Wallis) usando `scipy.stats`.
        d.  Genera un gráfico boxplot comparativo (estático PNG con `matplotlib`/`seaborn` y opcionalmente interactivo HTML con `plotly`) usando `charting.create_comparison_boxplot` y `charting.create_interactive_comparison_boxplot`.
        e.  Guarda la configuración del análisis y los resultados estadísticos (p-valor) en un archivo `config.json` y el gráfico en la carpeta del análisis (`estudios/<nombre_estudio>/Analisis Discreto/Individual/<nombre_analisis>/`).
    5.  Los resultados pueden ser visualizados y gestionados a través de `IndividualAnalysisManagerDialog`.

*   **Configuración de un Análisis Continuo:**
    1.  Desde `StudyView`, el usuario hace clic en "Análisis Continuo".
    2.  `MainWindow` llama a `show_continuous_analysis_config_dialog()`.
    3.  Se abre `ContinuousAnalysisConfigDialog`.
    4.  El diálogo llama a `AnalysisService.get_available_frequencies_for_study()` para poblar el combobox de frecuencias.
    5.  El usuario selecciona una frecuencia (y futuramente, otras opciones como variable y grupos).
    6.  Al "Aceptar", el diálogo almacena la selección y se cierra. (La lógica de ejecución del análisis SPM es futura).

## 5. Patrones de Diseño y Convenciones Importantes
*   **Capa de Servicios (Service Layer)**: Centraliza la lógica de negocio y la orquestación de operaciones, desacoplando la UI de la lógica de datos directa.
*   **Patrón Repositorio (Repository Pattern)**: Utilizado en `StudyRepository` para desacoplar los servicios de los detalles específicos de acceso a la base de datos SQLite.
*   **Separación de Responsabilidades (similar a MVC/MVP)**:
    *   `ui` (Vistas y Diálogos): Responsables de la presentación y captura de la entrada del usuario (Vista y parte del Controlador/Presentador).
    *   `core.services`: Contienen la lógica de la aplicación y actúan como intermediarios (parte del Controlador/Presentador y Modelo de negocio).
    *   `database.repositories`: Manejan la persistencia de datos (parte del Modelo de datos).
*   **Tkinter para la UI**: Uso de la biblioteca estándar de Python para la interfaz gráfica de usuario.
*   **Logging Centralizado**: Uso consistente del módulo `logging` de Python, configurado en `utils.logger`, para registrar eventos y errores de la aplicación.
*   **Manejo de Excepciones Personalizadas**: Uso de excepciones definidas en `core.exceptions` para un control de errores más granular.
*   **Configuración Externa**: Uso de `config.ini` para ajustes de la aplicación que pueden ser modificados sin cambiar el código.

## 6. Estructuras de Datos Clave / DTOs (Data Transfer Objects)
*   **Objeto/Diccionario de Estudio**: Estructura utilizada por `StudyService` y `StudyRepository` para representar un estudio. Incluye: `id`, `name`, `num_subjects`, `attempts_count`, `independent_variables` (JSON/lista de dicts), `aliases` (JSON/dict).
*   **Estructura de Variable Independiente (VI)**: Una lista de diccionarios, donde cada diccionario representa una VI:
    `{'name': str, 'descriptors': list[str], 'allows_combination': bool, 'is_mandatory': bool}`.
*   **Diccionarios de Información de Archivo**: Utilizados por `FileService` y `FileBrowser` para representar archivos. Incluyen: `path` (Path), `name` (str), `type` (str: "Raw", "Processed"), `frequency` (str), `patient` (str), `descriptors` (list[str|None]).
*   **Diccionarios de Configuración de Análisis**: Utilizados para pasar parámetros a `AnalysisService` y para guardar las configuraciones de análisis individuales. Ejemplos:
    *   Análisis Discreto Individual: `{'name': str, 'frequency': str, 'calculation': str, 'column': str (formato 'Atributo/Columna/Unidad'), 'groups': list[str (claves de grupo)], 'parametric': bool, 'paired': bool, 'grouping_mode': str, 'primary_vi_name': str|None, 'fixed_vi_name': str|None, 'fixed_descriptor_display': str|None}`.
*   **Claves de Grupo para Análisis**: String combinado que representa una condición experimental única, basado en las VIs y sus descriptores. Formato: `"VI1_Nombre=DescriptorValor;VI2_Nombre=DescriptorValor"`. Ejemplo: `"TipoSalto=CMJ;Condicion=PRE"`.

## 7. Notas sobre el Descriptor "Nulo"
*   **Concepto**: "Nulo" es un valor de descriptor especial que indica la ausencia de un descriptor específico para una Variable Independiente (VI) en un archivo particular. Esto es útil cuando una VI no aplica a todas las mediciones o cuando se quiere analizar un efecto principal ignorando otras VIs.
*   **En Nombres de Archivo**: Si una VI no es obligatoria y no se especifica un descriptor para ella en un archivo, se asume "Nulo" para esa VI al parsear el nombre del archivo. El validador `validate_filename_for_study_criteria` maneja esto.
*   **En Lógica de Agrupación**: Al identificar grupos para análisis (`_identify_study_groups`), "Nulo" se trata como cualquier otro descriptor, permitiendo agrupar archivos que comparten la "ausencia" de ciertos descriptores. La clave de grupo reflejará esto, ej: `"VI1=CMJ;VI2=Nulo"`.
*   **Validación**: Existe una regla que impide nombrar explícitamente un descriptor como "Nulo" durante la definición de VIs en `StudyDialog` para evitar ambigüedades. "Nulo" es un estado implícito.
*   **Regla "Al Menos Un Descriptor No-Nulo"**: Para que un nombre de archivo sea válido, debe contener al menos un descriptor que no sea "Nulo" (implícito o explícito) si hay VIs definidas. Esto asegura que el archivo se asocie con alguna condición experimental.

## 8. Consideraciones Adicionales
*   **Internacionalización (i18n)**: Actualmente la UI está predominantemente en español. No hay un sistema formal de i18n.
*   **Pruebas Automatizadas**: El proyecto tiene una estructura para pruebas (`tests/unit`, `tests/integration`), pero la cobertura y mantenimiento de estas es un proceso continuo.
*   **Dependencias Clave**: `pandas` para manipulación de datos, `numpy` para operaciones numéricas, `scipy` para estadísticas, `matplotlib` y `seaborn` para gráficos estáticos, `plotly` para gráficos interactivos, `reportlab` para PDFs, `openpyxl` para exportación a Excel.