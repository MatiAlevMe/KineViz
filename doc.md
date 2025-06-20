[EXISTING TEXT FOR SECTIONS 1 AND 2, IF ANY, OR START OF SECTION 3]

## 3. Solución Propuesta

[EXISTING TEXT FOR 3.1 Proceso de Diseño de la Solución, IF ANY. THE OCR SHOWS THIS SECTION EXISTS.]

### 3.2 Arquitectura de la Solución
La arquitectura de KineViz se ha diseñado siguiendo un enfoque modular para garantizar la escalabilidad, mantenibilidad y separación de responsabilidades. Esta arquitectura ha evolucionado para soportar las crecientes funcionalidades del sistema, centrándose en una clara distinción entre la interfaz de usuario, la lógica de negocio y la persistencia de datos.

#### 3.2.1 Arquitectura Física
KineViz está diseñado para ser utilizado en estaciones de trabajo locales (Windows, macOS). Los archivos de estudio, datos procesados y resultados de análisis se almacenan de manera segura en el sistema de archivos local del usuario. La información estructural de los estudios y las configuraciones de la aplicación se guardan en una base de datos SQLite (`kineviz.db`) y un archivo de configuración (`config.ini`), respectivamente, también locales. Este diseño permite a los usuarios acceder y analizar sus datos sin depender de una conexión a internet, asegurando la funcionalidad completa en entornos offline.

#### 3.2.2 Arquitectura Lógica
La arquitectura lógica de KineViz se organiza en varios módulos principales, cada uno con responsabilidades bien definidas, para promover la cohesión y reducir el acoplamiento entre componentes.

**Módulos Principales y Responsabilidades:**

*   **`kineviz.core` - Lógica de Negocio y Dominio:** Este es el corazón de la aplicación, conteniendo la lógica fundamental.
    *   **`core.services`**: Orquesta las operaciones y la lógica de negocio.
        *   `StudyService`: Gestiona la creación, lectura, actualización y eliminación (CRUD) de estudios. Maneja los metadatos del estudio, la definición de Variables Independientes (VIs), sus sub-valores y los alias asociados. Interactúa con `StudyRepository` para la persistencia.
        *   `FileService`: Administra todas las operaciones relacionadas con archivos dentro de los estudios. Esto incluye la adición de nuevos archivos (con validación de nombres y estructura), la eliminación, el listado paginado y filtrado, y el procesamiento de archivos crudos para generar datos estandarizados. También es responsable de extraer parámetros únicos del estudio (como tipos de dato y sub-valores existentes) a partir de los archivos procesados.
        *   `AnalysisService`: Contiene toda la lógica para los diferentes tipos de análisis que KineViz ofrece.
            *   Para **Análisis Discreto**: Genera tablas de resumen estadístico (máximo, mínimo, rango) en formato `.xlsx` (y `.csv` interno), agrupadas por tipo de dato y combinación de VIs. Identifica grupos únicos basados en VIs y sub-valores. Permite la configuración y ejecución de análisis estadísticos comparativos (t-tests, ANOVA, etc., usando `scipy.stats`), generando gráficos (boxplots, swarmplots) estáticos y opcionalmente interactivos. Gestiona los análisis individuales guardados.
            *   Para **Análisis Continuo (SPM)**: Prepara y normaliza datos de series temporales (a 101 puntos). Ejecuta análisis SPM (usando la librería `spm1d`) para comparar curvas entre grupos, realizando inferencia estadística. Genera gráficos SPM que muestran curvas promedio, bandas de variabilidad y clusters significativos. Gestiona los análisis continuos guardados.
    *   **`core.data_processing`**: Módulos encargados del procesamiento detallado y manejo de los datos.
        *   `file_handlers.py`: Responsable de la lectura e interpretación de los archivos de datos crudos (ej. `.txt`). Extrae metadatos, identifica el tipo de dato (Cinemática, Cinética, EMG) basado en el contenido, y realiza el procesamiento inicial para generar archivos estandarizados (incluyendo la adición de una columna "Tiempo").
        *   `processors.py`: Contiene funciones de utilidad para la transformación de datos (ej. formateo), cálculos estadísticos básicos (máximo, mínimo, rango) sobre DataFrames de pandas, y la normalización temporal de datos para el análisis SPM.
        *   `directory_manager.py`: Gestiona la creación y la estructura de los directorios para los estudios y los datos de los participantes dentro del sistema de archivos local.
    *   **`core.backup_manager.py`**: Módulo dedicado a la creación, gestión y restauración de copias de seguridad del sistema. Soporta copias automáticas (activadas por operaciones críticas, con rotación y cooldown), manuales (iniciadas por el usuario, con alias y gestión de límites) y de tipo "Respaldo" (creadas antes de operaciones destructivas como la restauración de fábrica). Los backups incluyen la base de datos (`kineviz.db`), el archivo de configuración (`config.ini`) y el contenido esencial del directorio de estudios (`estudios/`).
    *   **`core.undo_manager.py` (`UndoManager` class):** Gestiona la funcionalidad "Deshacer Eliminación". Antes de operaciones de eliminación soportadas (estudios, archivos, resultados de análisis), copia los elementos a eliminar y el estado de la base de datos a una caché temporal. Si el usuario activa "Deshacer", restaura estos elementos. La caché es temporal y sujeta a un timeout configurable.
    *   **`core.exceptions.py`**: Define clases de excepciones personalizadas para un manejo de errores más específico y claro dentro de la aplicación.

*   **`kineviz.ui` - Capa de Interfaz de Usuario (Tkinter):** Responsable de toda la presentación visual y la interacción con el usuario.
    *   `ui.main_window.py` (`MainWindow`): Es la ventana principal de la aplicación. Orquesta la navegación entre las diferentes vistas y diálogos. Mantiene instancias de los servicios principales, `AppSettings`, y el `UndoManager`. Gestiona el estado del menú "Editar -> Deshacer".
    *   `ui.views`: Vistas principales que ocupan la mayor parte de la ventana, como `LandingPage` (bienvenida), `MainView` (lista de estudios), `StudyView` (vista detallada de un estudio, incluyendo el `FileBrowser`), y `DiscreteAnalysisView` (gestión de tablas de resumen discreto).
    *   `ui.dialogs`: Ventanas modales para tareas específicas: `StudyDialog` (crear/editar estudios y VIs), `FileDialog` (agregar archivos), `DescriptorAliasDialog` (gestionar alias), `ConfigDialog` (configuración de la aplicación), diálogos para configurar y gestionar análisis discretos (`ConfigureIndividualAnalysisDialog`, `IndividualAnalysisManagerDialog`) y continuos (`ContinuousAnalysisConfigDialog`, `ContinuousAnalysisManagerDialog`), `BackupRestoreDialog` (gestión de copias de seguridad), y `CommentDialog` (comentarios de estudio).
    *   `ui.widgets`: Componentes de UI reutilizables como `FileBrowser` (navegador de archivos del estudio), `charting.py` (generación de gráficos con `matplotlib`/`seaborn` y `plotly`), y `tooltip.py` (tooltips personalizadas).
    *   `ui.utils`: Utilidades específicas de la interfaz, como `validators.py` (validación de entradas y nombres de archivo) y `style.py` (gestión de temas y escalado de fuentes).

*   **`kineviz.database` - Persistencia de Datos:**
    *   `database.repositories.StudyRepository`: Implementa el patrón Repositorio para abstraer las interacciones con la base de datos SQLite (`kineviz.db`). Es responsable de la creación de la tabla `estudios` y las operaciones CRUD para los metadatos de los estudios, incluyendo las VIs y alias (almacenados como JSON).

*   **`kineviz.config` - Configuración de la Aplicación:**
    *   `config.settings.AppSettings`: Gestiona la carga y el guardado de las configuraciones de la aplicación desde y hacia el archivo `config.ini`. Proporciona una interfaz centralizada para acceder a estos ajustes y maneja la validación y los valores por defecto.

*   **`kineviz.utils` - Utilidades Generales:**
    *   `utils.logger.py`: Configura el sistema de logging para toda la aplicación, permitiendo diferentes niveles de detalle y salida a archivos.
    *   `utils.paths.py`: Proporciona funciones para obtener de manera confiable rutas base de la aplicación, importante para el empaquetado con PyInstaller y el acceso a recursos.

**Flujos de Datos Clave:**
1.  **Creación de un Nuevo Estudio:** El usuario interactúa con `StudyDialog`. Los datos (nombre, número de participantes, VIs, etc.) son pasados a `StudyService`, que valida y luego instruye a `StudyRepository` para crear el registro en `kineviz.db`. `DirectoryManager` (a través de `StudyRepository` o `StudyService`) crea la carpeta física del estudio.
2.  **Adición de Archivos a un Estudio:** `FileDialog` permite la selección de archivos. `FileService` recibe estos archivos, valida sus nombres y estructura contra las VIs del estudio (definidas en `kineviz.db` y obtenidas vía `StudyService`). Si son válidos, los copia a la estructura de carpetas del estudio y los procesa (usando `file_handlers` y `processors`) para generar versiones estandarizadas.
3.  **Realización de un Análisis (Discreto o Continuo):** Los diálogos de configuración de análisis (`ConfigureIndividualAnalysisDialog`, `ContinuousAnalysisConfigDialog`) recogen los parámetros del usuario. `AnalysisService` utiliza estos parámetros para:
    *   Obtener los datos relevantes (accediendo a archivos procesados vía `FileService` y a metadatos de estudio/VIs vía `StudyService`).
    *   Realizar los cálculos estadísticos necesarios (ej. `scipy.stats` para análisis discretos, `spm1d` para análisis continuos).
    *   Generar visualizaciones (gráficos, boxplots) usando `charting.py`.
    *   Guardar la configuración del análisis y los resultados (ej. archivos JSON, imágenes PNG/HTML) en subcarpetas específicas dentro del directorio del estudio.

**Patrones de Diseño y Convenciones Importantes:**
*   **Capa de Servicios (Service Layer):** Centraliza la lógica de negocio, actuando como intermediario entre la UI y la capa de datos/procesamiento.
*   **Patrón Repositorio (Repository Pattern):** `StudyRepository` abstrae los detalles de la interacción con la base de datos SQLite.
*   **Separación de Responsabilidades:** Se mantiene una distinción clara entre la presentación (UI), la lógica de la aplicación (servicios) y la persistencia/manejo de datos.
*   **Logging Centralizado:** Uso del módulo `logging` de Python, configurado por `utils.logger.py`.
*   **Configuración Externa:** `config.ini` permite la personalización de la aplicación sin modificar el código.

**Estructuras de Datos Clave / DTOs (Data Transfer Objects):**
*   **Objeto/Diccionario de Estudio:** Representa un estudio con atributos como `id`, `name`, `num_participantes`, `attempts_count`, `independent_variables` (serializado como JSON), `aliases` (serializado como JSON), `is_pinned`, `comentario`.
*   **Estructura de Variable Independiente (VI):** Dentro del JSON de `independent_variables`, cada VI es un diccionario: `{'name': str, 'descriptors': list[str], 'allows_combination': bool, 'is_mandatory': bool}`.
*   **Diccionarios de Información de Archivo:** Usados por `FileService` y `FileBrowser`, incluyen `path`, `name`, `type` ("Original", "Processed"), `frequency` (tipo de dato), `patient` (ID del participante), `descriptors` (lista de sub-valores extraídos del nombre).
*   **Diccionarios de Configuración de Análisis:** Para pasar parámetros a `AnalysisService` y guardar configuraciones. Contienen detalles como nombre del análisis, tipo de dato, cálculo/columna a analizar, grupos seleccionados, supuestos estadísticos, etc.

**Manejo del Descriptor "Nulo":**
"Nulo" es una palabra clave utilizada en los nombres de archivo para indicar que una VI particular no aplica a esa medición específica. Esto permite flexibilidad en diseños experimentales donde no todas las VIs son pertinentes para cada archivo. El sistema valida el uso de "Nulo" según la configuración de cada VI (si permite o no la omisión de un sub-valor). Al definir VIs, no se puede nombrar un sub-valor como "Nulo" para evitar ambigüedades.

**Sistema de Respaldo, Restauración y Deshacer:**
Estas funcionalidades son cruciales para la integridad de los datos y la experiencia del usuario:
*   **Copias de Seguridad (`backup_manager.py`):**
    *   **Componentes:** Se respaldan `kineviz.db`, `config.ini`, y el contenido esencial del directorio `estudios/` (archivos originales, procesados, y resultados de análisis).
    *   **Tipos y Gestión:**
        *   *Automáticas:* Se activan antes de operaciones críticas (eliminaciones). Tienen rotación (límite `max_automatic_backups`) y un período de enfriamiento (`automatic_backup_cooldown_seconds`). Un archivo de bloqueo (`.backup_in_progress.lock`) previene ejecuciones concurrentes.
        *   *Manuales:* Iniciadas por el usuario, con alias opcionales y rotación (límite `max_manual_backups`).
        *   *De "Respaldo" (Pre-Restauración):* Creadas automáticamente antes de una restauración de fábrica, si está habilitado (`enable_pre_restore_backups`), con su propio límite y cooldown.
    *   **Almacenamiento:** En `kineviz/backups/automatic/`, `kineviz/backups/manual/`, y `kineviz/backups/respaldo/`.
*   **Restauración de Copias de Seguridad:** Permite al usuario revertir el sistema (base de datos, configuración, datos de estudios) a un estado guardado en un archivo ZIP de backup.
*   **Funcionalidad "Deshacer Eliminación" (`UndoManager`):**
    *   **Propósito:** Revertir la última operación de eliminación soportada (estudios, archivos, resultados de análisis).
    *   **Mecanismo:** Antes de eliminar, se copian los elementos y `kineviz.db` a una caché temporal (`kineviz/backups/.undo_cache/`). "Deshacer" restaura desde esta caché.
    *   **Transitoriedad:** La caché es temporal, se borra con nuevas operaciones, por timeout (`undo_cache_timeout_seconds`), o al cerrar la app. Su disponibilidad es configurable.

##### 3.2.2.1 Estructura de Carpetas del Proyecto
La organización del código fuente de KineViz sigue una estructura modular para facilitar el desarrollo, mantenimiento y la comprensión del sistema. A continuación, se describe la disposición principal de las carpetas y su propósito:

```
kineviz/
├── app.py           # Punto de entrada principal de la aplicación.
│
├── core/            # Contiene la lógica de negocio central y el dominio de la aplicación.
│   ├── __init__.py
│   ├── exceptions.py          # Define excepciones personalizadas.
│   ├── backup_manager.py      # Gestiona la creación y restauración de copias de seguridad.
│   ├── undo_manager.py        # Gestiona la funcionalidad de "deshacer eliminación".
│   ├── data_processing/       # Módulos para el procesamiento de datos crudos.
│   │   ├── processors.py      # Funciones para cálculos y transformaciones de datos.
│   │   ├── file_handlers.py   # Manejo específico de lectura e interpretación de archivos.
│   │   └── directory_manager.py # Gestión de la estructura de directorios de estudios.
│   └── services/              # Orquesta las operaciones y la lógica de negocio.
│       ├── study_service.py     # Lógica para la gestión de estudios (metadatos, VIs, alias).
│       ├── file_service.py      # Lógica para la gestión de archivos dentro de los estudios.
│       └── analysis_service.py  # Lógica para los análisis discretos y continuos.
│
├── ui/              # Responsable de la interfaz de usuario y la interacción.
│   ├── __init__.py
│   ├── main_window.py         # Ventana principal de la aplicación.
│   ├── views/                 # Vistas principales que ocupan la mayor parte de la ventana.
│   │   ├── landing_page.py
│   │   ├── study_view.py
│   │   ├── main_view.py
│   │   └── discrete_analysis_view.py
│   ├── dialogs/               # Diálogos modales para tareas específicas.
│   │   ├── study_dialog.py
│   │   ├── file_dialog.py
│   │   ├── descriptor_alias_dialog.py
│   │   ├── config_dialog.py
│   │   ├── configure_individual_analysis_dialog.py
│   │   ├── individual_analysis_manager_dialog.py
│   │   ├── continuous_analysis_config_dialog.py
│   │   ├── continuous_analysis_manager_dialog.py
│   │   ├── backup_restore_dialog.py
│   │   └── comment_dialog.py
│   ├── widgets/               # Componentes de UI reutilizables.
│   │   ├── file_browser.py
│   │   ├── charting.py
│   │   └── tooltip.py
│   └── utils/                 # Utilidades específicas de la UI.
│       ├── validators.py
│       └── style.py
│
├── database/        # Maneja la persistencia de datos.
│   ├── __init__.py
│   └── repositories.py        # Implementa el patrón Repositorio para abstraer acceso a DB.
│
├── config/          # Gestiona la configuración de la aplicación.
│   ├── __init__.py
│   └── settings.py            # Carga y guarda configuraciones desde/hacia config.ini.
│
├── utils/           # Utilidades generales compartidas en la aplicación.
│   ├── __init__.py
│   ├── logger.py              # Configuración del sistema de logging.
│   └── paths.py               # Funciones para obtener rutas base de la aplicación.
│
├── assets/          # Recursos estáticos como videos (DEMO.mp4) e imágenes.
│
├── backups/         # Directorio donde se almacenan las copias de seguridad.
│   ├── automatic/             # Subdirectorio para copias automáticas.
│   ├── manual/                # Subdirectorio para copias manuales.
│   ├── respaldo/              # Subdirectorio para copias de pre-restauración.
│   └── .undo_cache/           # Caché temporal para la función "Deshacer".
│
├── docs/            # Documentación del proyecto.
│   ├── help/
│   │   └── manual_usuario.txt # Manual de usuario principal.
│   └── recurso/
│       └── ROADMAP.md         # Documento de planificación y arquitectura detallada.
│
└── estudios/        # Directorio raíz donde se almacenan los datos de todos los estudios.
                     # (Creado por la aplicación en el directorio base, no parte del código fuente versionado directamente).
```
Esta estructura promueve la modularidad y facilita la localización de código relacionado con funcionalidades específicas.


### 3.2.3 Modelo de Datos
El modelo de datos de KineViz ha evolucionado para soportar una estructura de estudios flexible basada en Variables Independientes (VIs). La persistencia de datos se maneja principalmente a través de una base de datos SQLite, gestionada por `kineviz.database.repositories.StudyRepository`.

#### 3.2.3.1 Componentes Claves del Modelo de Datos Actual:

1.  **Estudio (`estudios` tabla en DB):**
    *   Representa una investigación o proyecto.
    *   **Atributos Principales:**
        *   `id_estudio` (INTEGER, PK): Identificador único del estudio.
        *   `nombre_estudio` (TEXT, UNIQUE): Nombre descriptivo del estudio.
        *   `num_participantes` (INTEGER): Cantidad máxima de participantes previstos.
        *   `cantidad_intentos_prueba` (INTEGER): Número máximo de intentos por condición.
        *   `independent_variables` (TEXT): Almacena una estructura JSON que define las Variables Independientes (VIs) del estudio y sus respectivos sub-valores. Cada VI tiene un nombre, una lista de sub-valores, y atributos como `allows_combination` y `is_mandatory`.
        *   `aliases` (TEXT): Almacena una estructura JSON que mapea sub-valores de las VIs a alias definidos por el usuario para ese estudio, mejorando la legibilidad.
        *   `is_pinned` (INTEGER): Indica si el estudio está fijado en la lista principal (0 = no fijado, 1 = fijado).
        *   `comentario` (TEXT): Un campo para notas o descripciones adicionales sobre el estudio.

2.  **Participante (Conceptual, no una tabla separada):**
    *   Representa a un individuo cuyos datos se recolectan. El término "Participante" reemplaza a "Sujeto".
    *   Los datos de los participantes se asocian al estudio a través de los nombres de archivo y la estructura de carpetas. El `ID_Participante` es parte del nombre de archivo.

3.  **Archivo (Conceptual, gestionado por `FileService` y estructura de carpetas):**
    *   Representa un archivo de datos crudo o procesado.
    *   **Nombre de Archivo:** Sigue un formato estricto: `ID_Participante [SubValor_VI1] [SubValor_VI2] ... [SubValor_VIn] NN.ext`. Por ejemplo: `P01 CMJ PRE 01.txt`. Este formato es crucial para la validación y agrupación automática.
    *   Los archivos se organizan en una estructura de carpetas: `estudios/[NOMBRE_ESTUDIO]/[ID_PARTICIPANTE]/OG/` para originales y `estudios/[NOMBRE_ESTUDIO]/[ID_PARTICIPANTE]/[TIPO_DATO]/` para procesados.

4.  **Tipo de Dato (Conceptual, no una tabla separada en DB):**
    *   Se refiere a la naturaleza de los datos medidos (ej: Cinemática, Cinética, EMG).
    *   Se determina automáticamente durante el procesamiento de archivos (basado en el contenido o metadatos del archivo, ver `file_handlers.leer_seccion`).
    *   Se utiliza para organizar archivos procesados en subcarpetas y para filtrar análisis.

5.  **Cálculos y Resultados de Análisis (Gestionados por `AnalysisService` y estructura de carpetas):**
    *   Los resultados de análisis discretos (tablas resumen, gráficos individuales) y continuos (configuraciones, resultados SPM, gráficos) se almacenan en subcarpetas específicas dentro de la carpeta de cada estudio (ej. `Analisis Discreto/Tablas/`, `Analisis Discreto/Graficos/[VARIABLE]/[NOMBRE_ANALISIS]/`, `Analisis Continuo/[VARIABLE]/[NOMBRE_ANALISIS]/`).
    *   Las configuraciones de análisis y metadatos clave (como p-valores) se guardan en archivos JSON junto a los gráficos.

### 3.2.4 Modelo Relacional

#### 3.2.4.1 Importancia:
Un modelo de datos bien definido es crítico para asegurar que:
*   Los datos sean almacenados de manera organizada y puedan ser consultados eficientemente.
*   Se pueda realizar un seguimiento histórico de todas las pruebas y participantes.
*   Los cálculos y visualizaciones se generen en tiempo real sin problemas de rendimiento.

Este modelo de datos en KineViz asegura que los resultados de los análisis, gráficos, y reportes sean precisos y se generen de manera eficiente, lo que facilita la experiencia del usuario en el manejo de grandes volúmenes de datos biomecánicos.

#### 3.2.4.2 Modelo Relacional de KineViz
El modelo relacional de la base de datos en KineViz es intencionalmente simple, centrándose en una tabla principal `estudios`. La complejidad asociada a la estructura de los estudios (Variables Independientes, sub-valores) y la gestión de archivos de datos se maneja a través de campos JSON dentro de la tabla `estudios` y mediante una estructura organizada en el sistema de archivos, respectivamente.

*   **Tabla Principal `estudios`:** Es la única tabla SQL persistente que define la estructura central de los estudios. Sus columnas clave son:
    *   `id_estudio` (INTEGER, Clave Primaria)
    *   `nombre_estudio` (TEXT, Único)
    *   `num_participantes` (INTEGER)
    *   `cantidad_intentos_prueba` (INTEGER)
    *   `independent_variables` (TEXT): Almacena una cadena JSON que describe la lista de VIs, cada una con sus sub-valores y propiedades (`allows_combination`, `is_mandatory`).
    *   `aliases` (TEXT): Almacena una cadena JSON con el mapeo de sub-valores a sus alias para el estudio.
    *   `is_pinned` (INTEGER)
    *   `comentario` (TEXT)

*   **Entidades Conceptuales (No son tablas SQL separadas):**
    *   **Variables Independientes (VIs) y Sub-valores:** Definidos dentro del campo JSON `independent_variables` de la tabla `estudios`. La lógica de la aplicación parsea este JSON para entender la estructura experimental.
    *   **Alias de Sub-valores:** Definidos dentro del campo JSON `aliases` de la tabla `estudios`.
    *   **Participantes:** Identificados por el `ID_Participante` en los nombres de archivo y las carpetas correspondientes en el sistema de archivos. No existe una tabla `Participantes`.
    *   **Archivos de Datos:** Gestionados por `FileService` y organizados en el sistema de archivos. Su relación con un estudio y un participante se infiere de su ruta y nombre.
    *   **Tipos de Dato (Frecuencias):** Determinados por `FileService` durante el procesamiento de archivos y utilizados para organizar los archivos procesados en subcarpetas. No es una tabla en la base de datos.
    *   **Resultados de Análisis:** Guardados como archivos (JSON para configuraciones, PNG/HTML para gráficos, XLSX para tablas) en subdirectorios específicos dentro de la carpeta del estudio.

**Figura 3.5 (anteriormente 4.5) Modelo Relacional - Diagrama:**
El diagrama para representar este modelo debe:
1.  Mostrar claramente la tabla `estudios` con todas sus columnas SQL.
2.  Indicar visualmente (por ejemplo, con flechas o notas explicativas conectadas a las columnas `independent_variables` y `aliases`) que estos campos contienen estructuras JSON. Se puede incluir un ejemplo de la estructura JSON en una nota adjunta a estas columnas en el diagrama.
3.  Representar la relación entre un registro de la tabla `estudios` (identificado por `nombre_estudio`) y el "Sistema de Archivos del Estudio". Esto se puede hacer dibujando una entidad conceptual para el sistema de archivos y mostrando cómo la estructura de carpetas (`estudios/[nombre_estudio]/[ID_Participante]/...`) se organiza y cómo los nombres de archivo se validan contra la definición en `independent_variables`.
Este enfoque híbrido para el diagrama refleja con precisión que, si bien la base de datos relacional es simple, la riqueza estructural del sistema se maneja a través de datos semi-estructurados (JSON) y la organización del sistema de archivos, todo orquestado por la lógica de la aplicación.

[EXISTING TEXT FOR 3.2.5 Lenguajes de Programación, IF ANY, OR 3.2.3 FROM OCR]

[EXISTING TEXT FOR 3.3 Descripción de la Funcionalidad, ETC., UNTIL PROJECT ADVANCES SECTION]

## 7. Estado de Avance del Proyecto - Parte 2
[EXISTING TEXT FOR 7.1 Avances Iniciales (Marzo 2025 - Inicios de Mayo 2025)]

### 7.X Justificación de Cambios en el Modelo de Datos y Arquitectura (Nueva Subsección)

La evolución de KineViz desde su concepción inicial hasta la versión actual ha implicado cambios significativos tanto en su modelo de datos como en su arquitectura de software. Estas modificaciones no fueron arbitrarias, sino que respondieron a la necesidad de crear un sistema más robusto, flexible, mantenible y alineado con los requerimientos específicos de la investigación kinesiológica.

**Justificación de Cambios en el Modelo de Datos:**

1.  **Adopción de Variables Independientes (VIs) y Sub-valores Flexibles:**
    *   **Necesidad:** La investigación kinesiológica abarca una gran diversidad de diseños experimentales. Un modelo de datos con campos fijos para factores de estudio (como se podría haber inferido de las columnas `tipos_prueba`, `periodos_prueba` eliminadas del `StudyRepository`) limitaría severamente la capacidad del usuario para definir sus propios factores y niveles.
    *   **Solución:** Se transitó hacia una estructura basada en "Variables Independientes" (VIs) y sus "sub-valores" (descriptores), almacenada como una cadena JSON en la columna `independent_variables` de la tabla `estudios`.
    *   **Beneficio:** Esta aproximación permite a los usuarios modelar prácticamente cualquier diseño experimental (ej: "Tipo de Salto", "Condición del Participante", "Grupo de Edad", "Lateralidad", etc.) con sus respectivos niveles, sin requerir modificaciones en el esquema de la base de datos. Otorga una flexibilidad crucial, permitiendo que la aplicación se adapte al estudio y no al revés. Esto impacta directamente en la capacidad del sistema para validar nombres de archivo y agrupar datos correctamente para los análisis.

2.  **Gestión de Alias por Estudio:**
    *   **Necesidad:** Los sub-valores utilizados en los nombres de archivo, por razones de brevedad o convención técnica (ej: "CMJ", "PRE"), pueden no ser inmediatamente intuitivos para la interpretación de resultados o para usuarios menos familiarizados con la nomenclatura específica.
    *   **Solución:** Se implementó un sistema de alias por estudio, donde cada sub-valor puede tener un nombre más descriptivo (ej: "Salto Contra Movimiento", "Antes del Tratamiento"). Estos alias se almacenan como JSON en la columna `aliases` de la tabla `estudios`.
    *   **Beneficio:** Mejora significativamente la legibilidad de los resultados en la interfaz de usuario, gráficos y reportes, sin alterar los nombres de archivo originales que son necesarios para el procesamiento automatizado.

3.  **Simplificación del Esquema SQL y Uso Estratégico del Sistema de Archivos:**
    *   **Necesidad:** Los datos biomecánicos pueden ser voluminosos (archivos de series temporales) y los resultados de análisis pueden incluir múltiples artefactos (configuraciones, múltiples gráficos, tablas de datos). Almacenar toda esta información directamente en una base de datos relacional podría llevar a una base de datos muy grande y potencialmente menos eficiente para ciertos tipos de acceso, además de complicar el esquema.
    *   **Solución:** La base de datos SQLite se centra en almacenar los metadatos estructurales de los estudios (tabla `estudios`). Los archivos de datos crudos, los archivos procesados, las tablas de resumen de análisis discretos, y los artefactos de análisis continuos (configuraciones JSON, gráficos PNG/HTML, resultados SPM en JSON) se gestionan en una estructura de carpetas organizada dentro del directorio de cada estudio en el sistema de archivos.
    *   **Beneficio:** Este enfoque reduce la complejidad del esquema SQL, facilita el manejo de archivos grandes y diversos, y permite que la lógica de la aplicación (`FileService`, `AnalysisService`) orqueste el acceso y la organización de estos archivos de manera eficiente. La integridad se mantiene mediante convenciones de nomenclatura y la lógica de los servicios.

**Justificación de Cambios en la Arquitectura del Software:**

1.  **Modularización y Capas de Servicio:**
    *   **Necesidad:** Para un software con la complejidad funcional de KineViz, una arquitectura monolítica o con alto acoplamiento entre la interfaz de usuario y la lógica de datos dificultaría el mantenimiento, la extensión y las pruebas.
    *   **Solución:** Se adoptó una arquitectura modular con una clara separación de responsabilidades en capas (`core`, `ui`, `database`, `config`, `utils`) y, crucialmente, la introducción de una capa de servicios (`StudyService`, `FileService`, `AnalysisService`).
    *   **Beneficio:** Esta estructura mejora la mantenibilidad, ya que los cambios en una capa tienen un impacto controlado en otras. Facilita la escalabilidad, permitiendo que los módulos evolucionen. Además, simplifica las pruebas unitarias y de integración al poder probar componentes de forma aislada o con dependencias controladas.

2.  **Introducción de `BackupManager` y `UndoManager`:**
    *   **Necesidad:** La pérdida de datos o errores accidentales son riesgos inherentes en cualquier aplicación que maneje información valiosa. Para un software de investigación, la integridad y disponibilidad de los datos son primordiales.
    *   **Solución:** Se desarrollaron módulos dedicados: `BackupManager` para un sistema comprensivo de copias de seguridad (automáticas, manuales, pre-restauración) y `UndoManager` para permitir la reversión de operaciones de eliminación recientes.
    *   **Beneficio:** Aumenta drásticamente la robustez del sistema y la confianza del usuario. Las copias de seguridad protegen contra pérdidas mayores, y la función de deshacer ofrece una red de seguridad para errores operativos comunes.

3.  **Gestión Centralizada de Configuración (`AppSettings`):**
    *   **Necesidad:** Múltiples aspectos del comportamiento de la aplicación (ej: paginación, temas, límites de backup, habilitación de funciones) necesitan ser configurables por el usuario y persistentes entre sesiones.
    *   **Solución:** La clase `AppSettings` centraliza la carga, validación (con reseteo a valores por defecto en caso de corrupción) y guardado de todas estas configuraciones en un archivo `config.ini`.
    *   **Beneficio:** Proporciona un único punto de verdad para la configuración, facilita su modificación a través del `ConfigDialog`, y asegura un comportamiento predecible y personalizable de la aplicación.

Estos cambios arquitectónicos y de modelo de datos han sido fundamentales para transformar KineViz en una herramienta más potente, flexible y confiable, capaz de adaptarse a las diversas necesidades de la investigación kinesiológica y de proporcionar una base sólida para futuras expansiones.