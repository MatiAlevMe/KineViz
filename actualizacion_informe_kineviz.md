# ============================================================
# ACTUALIZACIONES SUGERIDAS PARA EL INFORME "Proyecto.pdf"
# ============================================================
# Nota: Este archivo contiene únicamente las secciones modificadas o añadidas.
# Reemplaza o complementa las secciones correspondientes en tu informe original.

# --- SECCIÓN 2: Introducción y Contexto (pp. 8-9) ---

## 2.2 Problemáticas Detectadas (Actualización Sugerida)

1.  **Dificultad en la interpretación de datos biomecánicos:** ... (Mantener texto original) ... específica. *Se añade la complejidad de interpretar estudios con múltiples factores o condiciones experimentales (ej. diferentes tipos de intervenciones, momentos de medición, grupos de sujetos), que ahora KineViz modela mediante Variables Independientes (VIs).*
2.  **Falta de integración entre diferentes fuentes de datos:** ... (Mantener texto original) ... (p.ej., datos de fuerza, movimiento y actividad muscular). *Además, la gestión manual de la correspondencia entre archivos y las condiciones experimentales específicas de cada sujeto se vuelve propensa a errores.*
3.  **Soluciones costosas y de difícil acceso:** ... (Mantener texto original) ... especializadas.
4.  **Tiempo de análisis:** ... (Mantener texto original) ... tiempo real. *Este tiempo se incrementa exponencialmente al intentar realizar comparaciones entre múltiples grupos o condiciones.*
5.  **No existe una herramienta que cubra la necesidad específica:** El software KineViz está diseñado para una necesidad particular del cliente, integrando datos biomecánicos (cinemáticos, cinéticos y electromiográficos) de manera automatizada y personalizada. *Ofrece una flexibilidad en la definición de la estructura del estudio (mediante VIs) y un flujo de análisis estadístico discreto integrado que no se encuentra comúnmente en otras plataformas disponibles de forma accesible.*

## 2.4 Limitaciones de las Soluciones Actuales (Actualización Sugerida)

1.  **Costo elevado:** ... (Mantener texto original) ... independientes.
2.  **Falta de interoperabilidad:** ... (Mantener texto original) ... biomecánicos. *Muchas herramientas carecen de la flexibilidad para definir estructuras de estudio personalizadas (como las VIs de KineViz) y adaptar los análisis a dichas estructuras.*
3.  **Curva de aprendizaje pronunciada:** ... (Mantener texto original) ... técnica avanzada. *La configuración de análisis comparativos entre grupos específicos definidos por el usuario suele requerir pasos manuales en software estadístico externo.*

## 2.5 Mejoras Propuestas por KineViz (Actualización Sugerida)

KineViz tiene como objetivo superar las limitaciones de las soluciones actuales mediante la creación de una plataforma accesible y fácil de usar, que permita integrar y visualizar datos cinemáticos, cinéticos y electromiográficos de manera intuitiva y eficiente. La principal innovación de KineViz radica en:

*   **Gestión de Estudios basada en Variables Independientes (VIs):** Permite definir estructuras de estudio jerárquicas y personalizadas con descriptores asociados, adaptándose a diseños experimentales complejos. Incluye la gestión de **Alias** para mejorar la legibilidad.
*   **Automatización del Procesamiento:** Incluye la **detección automática de frecuencia** (Cinemática, Cinética, EMG) y la generación de archivos procesados estructurados con cálculos básicos (ej. columna de tiempo).
*   **Análisis Estadístico Discreto Integrado:**
    *   Generación automática de **tablas resumen** con estadísticas descriptivas (máximo, mínimo, rango, etc.) agrupadas por combinaciones únicas de descriptores de VIs y frecuencia.
    *   Un **flujo de análisis individual configurable** que permite al usuario seleccionar grupos (basados en VIs/Alias), una variable de interés (columna), y supuestos estadísticos.
    *   Ejecución automática de las **pruebas estadísticas** adecuadas (t-test, ANOVA, Wilcoxon, Kruskal-Wallis).
    *   Generación de **gráficos comparativos (boxplot + swarmplot)** estáticos (PNG) e interactivos (HTML) con resultados estadísticos (p-valor) y etiquetas/leyendas claras.
*   **Gestión y Visualización Centralizada:** Ofrece una interfaz para listar, filtrar, visualizar y gestionar estudios, archivos procesados y análisis individuales guardados.

Este sistema automatizado permite realizar análisis individuales o grupales de estudios biomecánicos completos, generando gráficas, informes y resultados en cuestión de segundos. Esta optimización del proceso no solo ahorra tiempo considerable a los profesionales de la salud y entrenadores, sino que también mejora la precisión y consistencia de los análisis, ya que el software gestiona grandes volúmenes de datos de forma coherente y estandarizada, adaptándose a la estructura específica de cada estudio definida por el usuario.

# --- SECCIÓN 3: Objetivos Generales y Específicos (p. 12) ---

## 3.1 Objetivo General: (Mantener similar o refinar ligeramente)

Automatizar y optimizar el proceso de análisis biomecánico mediante el desarrollo de una herramienta digital capaz de integrar y visualizar datos cinemáticos, cinéticos y electromiográficos, *basada en una estructura de estudio flexible definida por Variables Independientes*, mejorando la eficiencia de los profesionales de la salud en la evaluación de estudios individuales o grupales.

## 3.2 Objetivos Específicos: (Reemplazar lista existente)

1.  **Desarrollar un sistema de análisis** que integre diferentes tipos de datos biomecánicos (cinemáticos, cinéticos y electromiográficos), implementando la **detección automática de frecuencia** y generando **archivos procesados** estructurados.
2.  **Implementar una interfaz gráfica intuitiva** que permita a los usuarios **gestionar estudios basados en Variables Independientes (VIs) y Descriptores**, incluyendo la definición y uso de **Alias**, y visualizar los resultados de análisis **discretos** (tablas resumen, gráficos comparativos).
3.  **Optimizar los procesos de cálculo y generación de gráficos** mediante la creación de **tablas de resumen de análisis discreto** y la implementación de un flujo de **análisis individual configurable** que ejecute pruebas estadísticas (t-test, ANOVA, etc.) y genere gráficos comparativos (boxplot + swarmplot) estáticos (PNG) e interactivos (HTML).
4.  **Facilitar la comparación *dentro* de un estudio** permitiendo la selección de **grupos basados en combinaciones de descriptores de VIs** para realizar análisis individuales comparativos.
5.  **Validar el sistema** a través de pruebas funcionales, de integración y de usuario (con profesionales/estudiantes del área) para asegurar que cumple con los requisitos de precisión, usabilidad y utilidad clínica, enfocándose en la correcta implementación de la lógica de **VIs, agrupación, análisis estadístico discreto y generación de resultados**.
6.  **Establecer la base para futuros análisis continuos**, definiendo e implementando los requerimientos iniciales de procesamiento (ej. normalización temporal) y visualización (ej. gráficos de líneas promedio).

# --- SECCIÓN 4.3: Descripción de la Funcionalidad ---
# --- Subsección 4.3.1 Requerimientos Funcionales (pp. 18-21) ---
# --- Subsección 4.3.2 Requerimientos No Funcionales (pp. 21-22) ---

*(Añadir al inicio de estas secciones o en una nota introductoria)*

**Nota:** Los siguientes requerimientos funcionales (RF) y no funcionales (RNF) describen el estado actual y planificado del sistema KineViz, reemplazando versiones anteriores (como las documentadas en `Cambios.pdf`). Se agrupan por categorías para mayor claridad: Gestión de Estudios (GE), Gestión de Archivos (GA), Análisis de Datos Discreto (AD), Análisis de Datos Continuo (AC), Configuración y Utilidades (CU), Usabilidad (US), Rendimiento (RE), Fiabilidad (FI), Mantenibilidad (MA), Portabilidad (PO).

*(Añadir los siguientes RNF a la lista existente en 4.3.2)*

*   **RNF-FI-005 (Precisión Estadística):** El sistema debe utilizar librerías estadísticas validadas (ej. SciPy) y aplicar los cálculos correctamente según la configuración del análisis (tipo de test, supuestos seleccionados).
*   **RNF-US-007 (Interpretabilidad Resultados):** Los resultados de los análisis (p-valores, gráficos, tablas) deben presentarse de forma clara y organizada, utilizando elementos como tooltips, alias y leyendas legibles para facilitar su interpretación por parte de usuarios con conocimientos básicos de estadística.

*(Añadir la siguiente lista de requerimientos funcionales actuales, basados en Proyecto.pdf pp. 18-21)*

**Requerimientos Funcionales - Gestión de Estudios (RF-GE)**

*   **RF-GE-001: Creación de Estudio:** El sistema permitirá al usuario crear un nuevo estudio especificando su nombre, número de sujetos, cantidad de intentos de prueba y definiendo la estructura jerárquica de Variables Independientes (VIs) y sus Descriptores asociados.
*   **RF-GE-002: Creación de Alias de Estudio:** El sistema permitirá al usuario definir Alias para los Descriptores de un estudio específico. Estos alias se almacenarán asociados al estudio y se utilizarán para mejorar la legibilidad en análisis y reportes.
*   **RF-GE-003: Listado Paginado y Búsqueda de Estudios:** El sistema permitirá listar los estudios existentes de forma paginada y ofrecerá una opción de búsqueda.
*   **RF-GE-004: Visualización de Estudio:** El sistema permitirá ver los detalles completos de un estudio seleccionado, incluyendo metadatos, la estructura de VIs/Descriptores (con alias) y un resumen o acceso a los archivos asociados.
*   **RF-GE-005: Edición de Estudio:** El sistema permitirá modificar los metadatos de un estudio existente (nombre de estudio, nombre del paciente, número de intentos de prueba) y sus alias. La estructura de VIs/Descriptores tendrá edición restringida (solo renombrar VIs) tras la creación inicial.
*   **RF-GE-006: Eliminación de Estudio:** El sistema permitirá eliminar un estudio seleccionado, incluyendo sus metadatos, archivos procesados y resultados de análisis asociados, previa confirmación del usuario.

**Requerimientos Funcionales - Gestión de Archivos (RF-GA)**

*   **RF-GA-001: Adición de Archivo(s):** El sistema permitirá al usuario seleccionar y añadir uno o más archivos de datos (tanto .txt como .csv pero en el formato especificado por el cliente) a un estudio existente.
*   **RF-GA-002: Validación de Nombre(s) de Archivo(s):** Al añadir archivos, el sistema validará que sus nombres sigan el formato “PteXX [DescriptorVI1]...[DescriptorVIn] NN", comprobando la existencia y orden de los descriptores contra la estructura de VIs del estudio (permitiendo "Nulo" siempre y cuando exista al menos un descriptor definido).
*   **RF-GA-003: Procesamiento y Clasificación de Archivo(s):** En el procesado, de manera general, se realizará lo siguiente: (1) Detectar automáticamente la frecuencia de datos (Cinemática, Cinética, EMG) por contenido. (2) Extraer datos relevantes en un nuevo formato (ie. Columna de tiempo y cálculos de las columnas). (3) Guardar los datos procesados en archivos estructurados (ej. CSV) en subcarpetas por frecuencia.
*   **RF-GA-004: Creación de Columna Tiempo:** Durante el procesado, se generarán archivos resultantes con una columna nueva llamada "tiempo” en todos los archivos de estudio al calcular el tiempo basado en la fórmula (1/Hz) para cada sección de datos en el archivo.
*   **RF-GA-005: Creación de Filas de Cálculos:** Durante el procesado, se generarán archivos resultantes con nuevas filas con cálculos específicos (max, min, rango) para todas las columnas excepto "frames”, “subframe” y “tiempo”.
*   **RF-GA-006: Listado Paginado, Búsqueda y Filtrado de Archivos:** El sistema permitirá listar los archivos asociados a un estudio, con opciones de filtrado por tipo/frecuencia, búsqueda y paginación.
*   **RF-GA-007: Gestión de Archivos:** El sistema permitirá eliminar archivos específicos de un estudio, como también visualizar cada archivo del estudio tanto procesado como los archivos originales subidos por el usuario.

**Requerimientos Funcionales - Análisis de Datos Discreto (RF-AD)**

*   **RF-AD-001: Generación de Tablas:** El sistema permitirá generar tablas resumen (CSV/TSV/XLSX) con estadísticas descriptivas (máximo, mínimo, promedio, etc.) para cada columna numérica, agrupadas por combinación única de Descriptores de VIs y por frecuencia, almacenandose en ".../Análisis Discreto/Tablas".
*   **RF-AD-002: Gestión de Tablas:** El sistema proporcionará una vista (donde se puede observar nombre de archivo, tipo de cálculo, sus descriptores y VIs, entre otras) para listar en un formato paginado, buscar, filtrar por cálculo u formato (.csv, .tsv, .xlsx, etc), eliminar, y visualizar (abrir) las tablas resumen generadas en RF-AD-001.
*   **RF-AD-003: Configuración de Análisis Individual:** El sistema ofrecerá un diálogo para configurar un análisis comparativo, permitiendo seleccionar: frecuencia, cálculo base (de tablas resumen), dos o más grupos (presentados con VIs/Alias), una columna común (variable dependiente), y supuestos estadísticos (paramétrico/no paramétrico, pareado/no pareado).
*   **RF-AD-004: Ejecución de Análisis Individual:** Tras la configuración (RF-AD-003), el sistema ejecutará la prueba estadística adecuada (t-test, ANOVA, Wilcoxon, etc.), generará gráficos comparativos (boxplot+swarmplot) estáticos (PNG) e interactivos (HTML) con etiquetas legibles (VIs/Alias) y significancia, y guardará los resultados (config.json, PNG, HTML) en Análisis Discreto/Individual/[NOMBRE_ANALISIS]
*   **RF-AD-005: Gestión de Análisis Individuales:** El sistema proporcionará un diálogo para listar análisis individuales guardados, mostrar detalles relevantes (grupos, columna analizada, p-valor, entre otras), visualizar gráficos (PNG/HTML), eliminar análisis y abrir su carpeta de resultados.
*   **RF-AD-006: Generación de Reporte General PDF:** El sistema permitirá generar un reporte PDF consolidado para un estudio. El usuario seleccionará una columna de interés, y el sistema realizará análisis comparativos para combinaciones relevantes de grupos para esa columna, incluyendo gráficos y resultados en el PDF.

**Requerimientos Funcionales - Configuración y Utilidades (RF-CU)**

*   **RF-CU-001: Configuración de Ajustes de Aplicación:** El sistema permitirá al usuario configurar ajustes generales (ej. elementos por página) a través de un diálogo específico.
*   **RF-CU-002: Persistencia de Configuraciones:** Las configuraciones de la aplicación se guardarán en un archivo (config.ini) y se cargarán al inicio.
*   **RF-CU-003: Registro de Eventos (Logging):** El sistema registrará eventos importantes y errores en archivos de log para diagnóstico y monitoreo.
*   **RF-CU-004: Guardado de Estudios Localmente:** El sistema debe permitir guardar los estudios y sus archivos de manera local en una carpeta del programa, permitiendo que estos se carguen fluidamente sin necesidad de recargar los estudios previamente guardados.
*   **RF-CU-005: Página de Bienvenida:** El sistema mostrará una ventana de bienvenida al iniciar el programa por primera vez, esta ventana contará con distintas opciones relevantes (ej. Crear primer estudio, una pequeña guía de acceso rápido para crear el primer estudio y el manual de estudio).
*   **RF-CU-006: Acceso a Carpetas Locales del Sistema:** El sistema mostrará un botón para abrir distintas carpetas relevantes para el usuario (ej. La carpeta de los distintos estudios, la carpeta de los distintos análisis)

*(Añadir la siguiente NUEVA subsección de requerimientos funcionales para Análisis Continuo)*

**Requerimientos Funcionales - Análisis Continuo (RF-AC)**

*   **RF-AC-001: Selección de Datos para Análisis Continuo:** El sistema debe permitir al usuario seleccionar uno o más sujetos (o grupos definidos por VIs/Descriptores), una frecuencia de medición específica, y una o más columnas de datos (variables) de los archivos procesados para realizar un análisis de series temporales.
*   **RF-AC-002: Procesamiento de Series Temporales:** El sistema debe ofrecer opciones para procesar las series temporales seleccionadas, incluyendo (al menos) la **normalización temporal** (ej. interpolación al 100% del ciclo/tiempo) para permitir la comparación y el promediado entre diferentes pruebas o sujetos.
*   **RF-AC-003: Cálculo de Curvas Promedio y Variabilidad:** Para un conjunto de series temporales normalizadas (correspondientes a un grupo seleccionado), el sistema debe ser capaz de calcular la curva promedio y una medida de variabilidad (ej. desviación estándar o intervalo de confianza) punto a punto a lo largo del ciclo normalizado.
*   **RF-AC-004: Generación de Gráficos de Series Temporales:** El sistema debe permitir generar gráficos de líneas que visualicen:
    *   Series temporales individuales seleccionadas.
    *   La curva promedio de un grupo.
    *   La curva promedio junto con una banda sombreada representando la variabilidad (DE/IC) del grupo.
*   **RF-AC-005: Configuración y Personalización de Gráficos Continuos:** El usuario debe poder configurar aspectos básicos de los gráficos de series temporales generados, como títulos, etiquetas de ejes y potencialmente la selección de colores o estilos de línea.
*   **RF-AC-006: Exportación de Resultados de Análisis Continuo:** El sistema debe permitir exportar los datos procesados (ej. series normalizadas, curvas promedio y de variabilidad en formato CSV/TSV) y los gráficos generados (ej. como archivo de imagen PNG o como archivo HTML interactivo si se usan librerías como Plotly).

# --- SECCIÓN 4.4: Análisis de Riesgos (pp. 31-32) ---

*(Actualización y adición a los riesgos listados en Proyecto.pdf pp. 31-32)*

**Nota:** Los siguientes riesgos (RSG-VI, RSG-AD, RSG-STAT, RSG-PLOT) complementan y actualizan el análisis de riesgos inicial (RSG-01 a RSG-09) presentado en el informe `Proyecto.pdf`, reflejando la evolución del proyecto hacia el uso de Variables Independientes y análisis estadístico más complejo.

*   **RSG-VI-01: Complejidad en Validación y Gestión de VIs**
    *   **Impacto:** Medio
    *   **Probabilidad:** Media
    *   **Descripción:** La lógica para validar nombres de archivo contra la estructura jerárquica de VIs (considerando orden, descriptores permitidos, manejo de "Nulo") y la gestión de VIs/Alias en la UI y análisis puede volverse compleja, aumentando la posibilidad de errores o casos borde no manejados.
    *   **Plan de Mitigación:** Implementar pruebas unitarias exhaustivas para el validador de nombres y la lógica de VIs. Documentar claramente el formato esperado de nombres de archivo. Diseñar la UI de gestión de VIs de forma robusta y clara.

*   **RSG-AD-01: Rendimiento del Análisis Discreto con Alto Volumen**
    *   **Impacto:** Medio
    *   **Probabilidad:** Baja/Media
    *   **Descripción:** Con un número muy elevado de archivos procesados y/o una gran cantidad de combinaciones únicas de descriptores de VIs, la generación inicial de las tablas resumen de análisis discreto o la ejecución de análisis individuales (que leen estas tablas) podría volverse lenta.
    *   **Plan de Mitigación:** Optimizar la lectura y escritura de archivos CSV/TSV. Realizar pruebas de estrés con volúmenes de datos realistas o elevados. Considerar estrategias de carga parcial o indexación si el rendimiento se vuelve un problema crítico.

*   **RSG-STAT-01: Aplicación Incorrecta de Supuestos Estadísticos**
    *   **Impacto:** Alto (Resultados inválidos)
    *   **Probabilidad:** Media
    *   **Descripción:** Existe el riesgo de que el usuario seleccione incorrectamente si sus datos cumplen los supuestos para tests paramétricos vs. no paramétricos, o si las comparaciones son pareadas vs. no pareadas, llevando a conclusiones estadísticas erróneas.
    *   **Plan de Mitigación:** Diseñar el diálogo de configuración de análisis individual de forma muy clara, con tooltips o ayudas contextuales explicando brevemente cada supuesto. Incluir advertencias en la documentación sobre la importancia de verificar los supuestos. (Opcional avanzado: implementar tests de normalidad básicos como Shapiro-Wilk y mostrarlos como información, sin forzar la elección del test).

*   **RSG-PLOT-01: Complejidad y Legibilidad de Gráficos Avanzados**
    *   **Impacto:** Medio
    *   **Probabilidad:** Media
    *   **Descripción:** La generación de gráficos comparativos (boxplot+swarmplot, futuros gráficos continuos) que incluyen leyendas dinámicas basadas en VIs/Alias, múltiples grupos y anotaciones de significancia estadística (especialmente en gráficos interactivos como Plotly) puede volverse compleja de implementar y mantener, con riesgo de problemas de legibilidad o errores visuales.
    *   **Plan de Mitigación:** Desarrollar el código de generación de gráficos de forma modular. Realizar pruebas visuales exhaustivas con diferentes combinaciones de datos y grupos. Limitar la complejidad de las anotaciones automáticas si es necesario, priorizando la claridad.

# --- SECCIÓN 7: Estado de Avance del Proyecto (pp. 41-44) ---

*(Reemplazar COMPLETAMENTE la sección 7 existente con el siguiente texto)*

**7. Estado de Avance del Proyecto (Actualizado a 24 de Abril de 2025)**

**7.1 Resumen General**

Desde el inicio formal del proyecto en agosto de 2024 y la documentación inicial (reflejada en la versión de Octubre 2024 del informe), KineViz ha transitado desde una fase conceptual y de prototipado inicial hacia una aplicación funcional con una arquitectura significativamente refactorizada y capacidades de análisis concretas. El desarrollo se ha guiado por un enfoque iterativo, priorizando la construcción de una base sólida y modular. Los avances más notables se centran en la adopción de un modelo de datos basado en **Variables Independientes (VIs)** y la implementación robusta del flujo de **Análisis Estadístico Discreto**. El proyecto se encuentra actualmente en la fase final (Proyecto de Título), enfocándose en completar las funcionalidades comprometidas y preparar la entrega final.

**7.2 Avances Clave y Evolución**

La evolución del proyecto se puede entender mejor comparando el estado actual con la visión y requerimientos iniciales (documentados en `Cambios.pdf`) y el progreso registrado en el `ROADMAP.md`:

*   **Refactorización Inicial (Aprox. 2 semanas post-inicio Agosto 2024):** Se realizó una refactorización temprana para establecer una estructura de código más modular y mantenible (UI, Core, Database, etc.), sentando las bases para el desarrollo posterior.

*   **Implementación de Variables Independientes (VI):** (Corresponde a Fase 3 del Roadmap - Mayormente Completada)
    *   *Evolución:* Se abandonó el modelo simple basado en `tipos de prueba` y `periodos de prueba` (ver `Cambios.pdf` RF-002, RF-012). Se diseñó e implementó una estructura de datos y lógica de negocio para soportar **Variables Independientes jerárquicas y sus Descriptores** asociados a cada estudio (Base de Datos, `StudyService`, `StudyRepository`). Esto permite modelar diseños experimentales complejos.
    *   *Funcionalidad:* La UI (`StudyDialog`, `StudyView`) fue adaptada para permitir la creación, edición (restringida) y visualización de esta estructura de VIs. Se implementó la gestión de **Alias** por descriptor a nivel de estudio (`DescriptorAliasDialog`, `StudyService`) para mejorar la legibilidad de los resultados.
    *   *Validación:* Se desarrolló un nuevo validador (`validate_filename_for_study_criteria` en `validators.py`) que comprueba rigurosamente los nombres de archivo (`PteXX [DescVI1]...[DescVIn] NN`) contra la estructura de VIs definida en el estudio, incluyendo el manejo de descriptores "Nulo" y el orden correcto (`RF-GA-002` actual).

*   **Procesamiento de Archivos Mejorado:** (Corresponde a Fase 1 del Roadmap - Completada)
    *   *Detección Automática de Frecuencia:* Se implementó la lógica (`file_handlers.leer_seccion`) para identificar automáticamente la frecuencia (Cinemática, Cinética, EMG) basada en el contenido/metadatos del archivo durante el procesamiento (`RF-GA-003` actual). Los archivos procesados se guardan en subcarpetas por frecuencia.
    *   *Generación de Archivos Procesados:* Se estandarizó la salida de archivos procesados (ej. formato CSV/TSV) incluyendo una columna de tiempo calculada (`RF-GA-004`) y filas con cálculos básicos (`RF-GA-005`).

*   **Implementación del Análisis Estadístico Discreto:** (Corresponde a Fase 2 del Roadmap - Mayormente Completada)
    *   *Evolución:* Se pasó de conceptos generales de "Análisis Individual/Grupal" (`Cambios.pdf` RF-007, RF-008) a un flujo específico y potente.
    *   *Generación de Tablas Resumen:* El sistema genera automáticamente tablas (CSV/TSV/XLSX) con estadísticas descriptivas (máximo, mínimo, rango, etc.) para cada columna numérica, agrupadas por cada combinación única de descriptores de VIs y por frecuencia (`RF-AD-001`, `AnalysisService.generate_discrete_summary_tables`). Estas tablas son la base para los análisis comparativos.
    *   *Identificación de Grupos y Columnas:* Se implementó la lógica para identificar los grupos únicos basados en combinaciones de VIs/Descriptores (`AnalysisService._identify_study_groups`) y encontrar las columnas de datos comunes entre los grupos seleccionados para un análisis (`AnalysisService.get_common_columns_for_groups`).
    *   *Flujo de Análisis Individual Configurable:*
        *   Se creó un diálogo (`ConfigureIndividualAnalysisDialog`) donde el usuario selecciona frecuencia, cálculo base (de las tablas resumen), dos o más grupos (presentados con VIs/Alias para claridad), la columna común a analizar (variable dependiente), y los supuestos estadísticos (paramétrico/no paramétrico, pareado/no pareado) (`RF-AD-003`).
        *   El sistema ejecuta la prueba estadística apropiada (t-test, ANOVA, Wilcoxon, Kruskal-Wallis vía `scipy.stats`) según los supuestos (`RF-AD-004`, `AnalysisService.perform_individual_analysis`). Se consideró la adición de tests post-hoc, pero se ha generalizado a "Mejoras Análisis Estadístico" por ahora.
        *   Se generan gráficos comparativos (boxplot + swarmplot usando `seaborn`/`matplotlib` y `plotly`) estáticos (PNG) e interactivos (HTML), mostrando resultados clave (p-valor) y con etiquetas/leyendas legibles que incorporan VIs/Alias (`RF-AD-004`, `charting.py`).
    *   *Gestión de Análisis Guardados:* Se implementó un diálogo (`IndividualAnalysisManagerDialog`) para listar los análisis individuales guardados, mostrar sus detalles (grupos, p-valor), visualizar los gráficos (PNG/HTML), eliminar análisis y abrir su carpeta contenedora (`RF-AD-005`, `AnalysisService.list_individual_analyses`, `delete_individual_analysis`).
    *   *Vista de Tablas Discretas:* Se creó una vista (`DiscreteAnalysisView`) para gestionar las tablas resumen generadas (`RF-AD-002`).

*   **Interfaz de Usuario y Experiencia:** La UI ha sido desarrollada usando Tkinter y ttk, con vistas y diálogos específicos para cada funcionalidad principal. Se ha implementado paginación y búsqueda en las listas principales (estudios, archivos) y se han añadido elementos de ayuda contextual (botones `(?)` que abren archivos `.txt` de ayuda).

**7.3 Comparativa de Requerimientos (Antiguos vs. Actuales)**

La transición de los requerimientos genéricos listados en `Cambios.pdf` a los requerimientos específicos actuales (RF-GE, RF-GA, RF-AD, RF-CU en `Proyecto.pdf` pp. 18-21) refleja la maduración del proyecto:

*   La **lectura y carga** (`RF-001`, `RF-005` viejos) se detallan ahora en `RF-GA-001` (adición) y `RF-GA-003` (procesamiento y clasificación).
*   La **gestión de estudios** (`RF-002`, `RF-003`, `RF-004` viejos) se redefine completamente con VIs y Alias en `RF-GE-001` a `RF-GE-006`.
*   La **validación** (`RF-006` viejo) se enfoca ahora en la validación estructural de nombres de archivo (`RF-GA-002`).
*   El **análisis** (`RF-007` a `RF-013`, `RF-015` viejos) se concreta en el detallado flujo de **Análisis Discreto** (`RF-AD-001` a `RF-AD-005`). El reporte general (`RF-AD-006`) y el análisis continuo (`RF-AC-*`) son los siguientes pasos. La normalización (`RF-011` viejo) es un pendiente clave, probablemente para el análisis continuo.
*   La **exportación** (`RF-016`, `RF-017` viejo) se materializa en la exportación de tablas (`RF-AD-001`), resultados de análisis individuales (JSON, PNG, HTML) (`RF-AD-004`) y el futuro reporte PDF (`RF-AD-006`) y resultados continuos (`RF-AC-006`).
*   Los aspectos de **UI y configuración** (`RF-018` a `RF-025` viejos) están cubiertos por los requerimientos `RF-CU-*` y `RNF-US-*` actuales.

**7.4 Prioridades y Próximos Pasos (Fase Final: Marzo - Junio 2025)**

La prioridad para esta fase final es completar el MVP (Minimum Viable Product) comprometido, enfocándose en:

1.  **Finalizar Análisis Discreto:** Implementar el Reporte General PDF (`RF-AD-006`) y realizar mejoras estadísticas si el tiempo lo permite (considerando la generalización de tests post-hoc). Realizar correcciones menores (`ROADMAP F2.10`).
2.  **Pruebas y Validación VIs:** Ejecutar pruebas exhaustivas de la lógica de VIs y Alias (`ROADMAP F3.9`).
3.  **Implementar Análisis Continuo (MVP):** Desarrollar la funcionalidad básica descrita en `RF-AC-001` a `RF-AC-006`, priorizando la normalización temporal, cálculo de promedio/DE y visualización gráfica.
4.  **Pruebas de Usuario y Finales:** Realizar pruebas de usabilidad con estudiantes/profesionales de kinesiología y pruebas de integración finales.
5.  **Documentación y Entrega:** Completar la documentación de usuario y técnica, y preparar el paquete final para la entrega del 20 de junio.

Las reuniones semanales con los profesores guía servirán para monitorear el avance, resolver dudas y ajustar prioridades según sea necesario.
# --- FIN DE LAS ACTUALIZACIONES SUGERIDAS ---
