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

## Fase 1: Mejoras Incrementales - Detección de Frecuencia
1. Implementar detección automática de tipo de frecuencias basada en metadatos del archivo.
Detalle: Modificar la lógica en `kineviz.core.data_processing.file_handlers.leer_seccion` y `kineviz.core.services.file_service._process_and_copy_file` para identificar Cinemática ("Model Outputs"), Cinética ("Force Plate") y Electromiográfica.
1.1 Implementación de identificador de archivo para Cinemática.
1.2 Implementación de identificador de archivo para Cinética.
1.3 Implementación de identificador de archivo para Electromiográfica de confirmación del formato/identificador.

## Fase 2: Análisis Estadístico Discreto y Reportes
1. Generación de Matrices: Crear tablas por tipo de cálculo y combinación de descriptores (ej: "máximo_cinemática_CMJ_Normal").
1.1 Servicio `generate_discrete_summary_tables`: Lógica para agrupar archivos por combinación de descriptores, leer stats, crear DataFrames y guardar CSVs/TSVs/SCSVs/XLSX.
1.2 Botón en `StudyView`: Añadir botón "Análisis Discreto".
1.3 Vista `DiscreteAnalysisView`: Crear vista para listar/mostrar/eliminar tablas generadas, con filtros y paginación.
2. Identificación de Grupos y Columnas Comunes.
2.1 `AnalysisService._identify_study_groups`: Identifica grupos únicos por combinación de descriptores.
2.2 `AnalysisService.get_discrete_analysis_groups`: Expone grupos combinados a la UI.
2.3 `AnalysisService.get_common_columns_for_groups`: Encuentra columnas comunes en tablas CSV internas para grupos combinados.
3. Diálogo de Configuración de Análisis Individual.
3.1 Crear `ConfigureIndividualAnalysisDialog`: UI para seleccionar Frecuencia, Cálculo, Grupos combinados (dinámico), Columna (dinámico), y supuestos (paramétrico/pareado).
3.2 Integración con VIs: Grupos combinados ahora usan formato "VI: Alias" y se seleccionan correctamente.
4. Diálogo de Gestión de Análisis Individual.
4.1 Crear `IndividualAnalysisManagerDialog`: UI para listar, ver (gráfico estático/interactivo), eliminar análisis guardados y abrir carpeta.
4.2 Botón en `DiscreteAnalysisView`: Añadir botón para abrir el gestor.
5. Generación de Gráfico Boxplot Comparativo.
5.1 Función `create_comparison_boxplot`: En `charting.py` usando seaborn/matplotlib.
5.2 `AnalysisService.perform_individual_analysis`: Lógica para leer datos de tablas CSV internas, preparar datos por grupo combinado y llamar a `create_comparison_boxplot`. Guarda gráfico PNG y config.json.
6. Implementación de Tests Estadísticos y Mejoras Gráficas.
6.1 Lógica en `perform_individual_analysis`: Ejecutar tests (t-test/ANOVA/Wilcoxon/Kruskal/Friedman) usando `scipy.stats`.
6.2 Mejorar `create_comparison_boxplot`: Usar `swarmplot`, añadir leyenda, mostrar significancia (statannot para 2 grupos, p-valor general para >2).
6.3 Integrar LEYENDAS con VIs: Leyenda muestra nombres completos ("Grupo X - VI: Alias").
6.4 Integrar EL EJE HORIZONTAL con VIs: Eje X muestra etiquetas genéricas ("Grupo 1", "Grupo 2").
6.5 Tests post-hoc: Considerar y añadir si es necesario.
7. Generación de Gráfico Interactivo (Plotly).
7.1 Añadir dependencia `plotly`.
7.2 Crear `create_interactive_comparison_boxplot`: En `charting.py` para generar HTML.
7.3 Modificar `perform_individual_analysis`: Generar y guardar HTML.
8. Gestión de Análisis Guardados.
8.1 `AnalysisService.list_individual_analyses` / `delete_individual_analysis`.
8.2 Conectar UI `IndividualAnalysisManagerDialog`: Cargar, ver PNG, ver HTML, eliminar, abrir carpeta. Mostrar grupos combinados y p-valor.
10. Corrección de Errores: Revisar y corregir errores conocidos (ej: formato cabeceras CSV, error generación tablas discretas, inconsistencia nombres archivo análisis individual).
11. Implementar agregación de datos para análisis de efectos principales en `perform_individual_analysis`: Cuando se selecciona el modo "1VI" en la configuración de análisis individual, se agregan datos de las tablas de resumen combinadas correspondientes para permitir comparaciones de efectos principales (ej. "todos los jóvenes" vs "todos los mayores").
12. Adaptar `get_common_columns_for_groups` para efectos principales: Asegurar que la selección de columnas comunes funcione correctamente cuando se comparan efectos principales en modo "1VI".
13. Integración y Pruebas: Integrar y probar toda la funcionalidad de análisis discreto, incluyendo análisis de efectos principales.

## Fase 3: Refactorización a Variables Independientes (VI) y Mejoras UI/Validación
1. Modificar Modelo de Estudio.
1.1 DB Conceptual: Reemplazada columna `descriptores` por `independent_variables` (JSON TEXT) y añadida `aliases` (JSON TEXT) en tabla `estudios`.
1.2 Repositorio (`StudyRepository`): Actualizados `_create_tables` (migración), `create_study`, `get_study_by_id`, `update_study` para manejar `independent_variables` y `aliases`.
1.3 Servicio (`StudyService`): Actualizados métodos para manejar conversión Python <-> JSON para `independent_variables` y `aliases`. Añadidos `get_study_aliases`, `update_study_aliases`.
2. Refactorizar UI Creación/Edición Estudio (`StudyDialog`).
2.1 Flujo UI: Implementada UI jerárquica para definir VIs y sus Descriptores (con botones '+', '🗑️').
2.2 Restricciones Edición: Deshabilitados añadir/eliminar VIs/Descriptores; permitido renombrar VIs.
2.3 Botón Ayuda VI: Añadido botón `(?)` coloreado que abre `kineviz/docs/help/study_dialog_iv_help.txt`.
3. Refactorizar Validación (`validators.py`).
3.1 Validador Datos Estudio: Creado `validate_study_iv_data` (incluye regla anti-"Nulo").
3.2 Validador Nombres Archivo: Reescrito `validate_filename_for_study_criteria` para formato `PteXX [VAL_VI1]...[VAL_VIn] NN`, orden, valores permitidos (incl. "Nulo"), regla de al menos un descriptor no-Nulo. Devuelve `(bool, list[str|None])`.
3.3 Eliminar Validador Antiguo: Eliminado `validate_study_data`.
4. Integrar Validación.
4.1 `StudyDialog`: Usa `validate_study_iv_data` en `save` (corregido bug edición).
4.2 `FileService.add_files_to_study`: Usa nuevo `validate_filename_for_study_criteria`.
5. Actualizar `FileService`.
5.1 `add_files_to_study`: Obtiene estructura VI de `StudyService` para validación.
5.2 `get_unique_study_parameters`: Adaptado para extraer parámetros basados en la nueva estructura y nombres de archivo. Devuelve descriptores únicos encontrados por *posición* de VI.
6. Actualizar Vista Estudio (`StudyView`).
6.1 Mostrar VIs: Añadido label para mostrar nombres de VIs.
6.2 Mostrar Descriptores (Tooltip/Popup): Añadido botón `ℹ️` que muestra Descriptores por VI (con alias) en popup.
6.3 Botón Ayuda General: Añadido botón `(?)` que abre `kineviz/docs/help/study_view_help.txt`.
7. Refactorizar Gestión de Alias.
7.1 Mover a DB: Implementado carga/guardado de alias por estudio en `StudyRepository` y `StudyService`.
7.2 Adaptar `DescriptorAliasDialog`: Carga/guarda alias vía `StudyService`.
7.3 Limpiar `AppSettings`: Eliminados métodos de alias globales.
8. Adaptar Servicios y UI de Análisis.
8.1 `AnalysisService._identify_study_groups`: Crea claves de grupo combinadas (ej: "VI1=DescA;VI2=DescB").
8.2 `AnalysisService` (Resto): Adaptados `get_discrete_analysis_groups`, `_get_data_for_parameters`, `perform_analysis`, `perform_individual_analysis`, `generate_report`, `generate_discrete_summary_tables`, `get_common_columns_for_groups` para usar claves combinadas y mostrar nombres de VI/alias.
8.3 `ConfigureIndividualAnalysisDialog`: Muestra/selecciona nombres de grupo legibles ("Grupo X - ..."), guarda claves originales.
8.4 `IndividualAnalysisManagerDialog`: Muestra nombres de grupo legibles ("Grupo X - ...").
9. Pruebas: Añadir/actualizar pruebas unitarias y de integración para validadores, servicios, UI refactorizada y lógica de agrupación/análisis.
10. Crear Archivos de Ayuda.
10.1 `docs/help/study_dialog_iv_help.txt`.
10.2 `docs/help/study_view_help.txt`.
11. Validación Número Sujetos/Intentos.
11.1 `FileService.add_files_to_study`: Validar que no se exceda `num_subjects` ni `attempts_count` al añadir archivos, considerando estado actual + lote nuevo.
11.2 `StudyDialog.save` (Edición): Validar que no se pueda reducir `num_subjects` por debajo de los sujetos existentes, ni `attempts_count` por debajo del máximo intento existente.
11.3 Actualizar Documentación Ayuda: Reflejar nuevas validaciones en `study_dialog_iv_help.txt` y `study_view_help.txt`.
12. Eliminar Funcionalidad "Analizar Estudio" Antigua.
12.1 `StudyView`: Eliminar botón "Analizar Estudio".
12.2 `AnalysisDialog` y `MainWindow.show_analysis_dialog`: Eliminados/Comentados ya que la funcionalidad fue reemplazada.
13. Refinamientos UI y Texto en Diálogo/Vista Estudio.
13.1 `StudyDialog`: Mejorar layout de checkboxes "¿Multiple?" y "¿Obligatorio?" (visibilidad condicional). Actualizar etiquetas ("Cantidad de Participantes", "Cantidad de Intento(s) de Prueba", "Nombre del Estudio", "Variable(s) Independientes (VIs)").
13.2 `StudyView`: Actualizar etiquetas ("Nombre del Estudio", "Cantidad de Participantes", "Cantidad de Intento(s) de Prueba", "Variable(s) Independientes (VIs)"). Mejorar popup de info de VIs para mostrar manejo de descriptores.
13.3 Actualizar Manuales de Ayuda: Reflejar cambios de etiquetas y comportamiento en `manual_usuario.txt`, `study_dialog_iv_help.txt`, `study_view_help.txt`.
14. Implementar Validación Avanzada de Archivos según Reglas de VI.
14.1 `validators.py`: Creada función `validate_files_for_vi_rules` para verificar:
Regla de Descriptor Fijo (si VI no permite combinación).
Regla de Descriptores Obligatorios (si VI permite combinación y es obligatoria).
14.2 `FileService`:
Creado helper `_get_all_study_files_descriptors` para obtener estado de descriptores de archivos existentes.
Integrada `validate_files_for_vi_rules` en `add_files_to_study`.
Si validación falla, se loguean errores específicos y se devuelve un error genérico a la UI.
14.3 Notificación UI: `FileDialog` mostrará el error genérico si la validación de reglas de VI falla.
15. Ajuste UI en Diálogo de Estudio.
15.1 `StudyDialog` UI: Ajustado el espaciado vertical de los checkboxes "¿Multiple?" y "¿Obligatorio?" para que estén más cerca de los descriptores. (Refinado para igualar espaciado inter-descriptor).

## Fase 4: Empaquetado y Distribución
1. Crear Paquetes Distribuibles.
1.1 Configurar PyInstaller: Creado y refinando `kineviz.spec` para definir el proceso de build (corrigiendo errores de hidden imports, backends, etc.).
1.2 Generar Build Windows: Ejecutar PyInstaller en Windows para crear el paquete.
1.3 Generar Build macOS: Ejecutando PyInstaller en macOS para crear el paquete (`.app` bundle).
1.4 Pruebas de Paquetes: Probar los paquetes generados en máquinas limpias de Windows 10/11 y macOS 11+.
2. Refinar Requerimiento de Compatibilidad (RNF-PO-001).
Detalle: Especificar versiones mínimas soportadas: Windows 10 (64-bit) y posteriores, macOS 11 (Big Sur) y posteriores (solo Apple Silicon / ARM64). Actualizar documentación formal si es posible.

## Fase 5: Análisis Continuo (SPM)
1. Diseño y Prototipado de UI para Análisis Continuo.
1.1 Botón en `StudyView`: Añadir botón "Análisis Continuo" en la vista de estudio, junto al de "Análisis Discreto".
1.2 Crear `ContinuousAnalysisConfigDialog` (o similar): Creado diálogo base para configurar el análisis continuo.
Selección de Tipo de datos (ej: Cinemática, Cinética). Solo permite Cinemática inicialmente.
Selección de Variable/Columna de Agrupación: Permitir al usuario seleccionar la variable específica a analizar (ej: "LAnkleAngles_X", "KneeMoment_Y"). Esto implica identificar y listar las columnas de datos relevantes de los archivos procesados, excluyendo "Frame", "Sub Frame" y "Tiempo".
Selector de Descriptores: Permitir al usuario seleccionar dos o más grupos de descriptores (basados en las VIs del estudio) para comparar.
1.3 Crear `ContinuousAnalysisResultsView` (o similar): Vista o sección en la UI para:
Listar los análisis continuos generados (nombre, columna, vi, sub-valores).
Mostrar filtros y opciones de ordenación para la lista de análisis.
Proveer opciones para cada análisis: ver gráfico SPM, ver tabla de datos normalizados/resultados, abrir carpeta de resultados, eliminar análisis.
2. Implementación de Normalización de Datos Temporales.
2.1 Lógica de Normalización Temporal: Implementar una función (posiblemente en `processors.py` o un nuevo módulo) para normalizar la duración de las secuencias de datos a 101 puntos (0-100%).
Esto se aplicará a la variable seleccionada para cada archivo/sujeto/intento.
Investigar y aplicar métodos de interpolación adecuados (ej: splines, interpolación lineal).
2.2 Procesamiento de Archivos para Normalización: En `AnalysisService`, crear lógica para:
Identificar los archivos relevantes del estudio según los tipos de datos y sub-valores seleccionados.
Leer la columna de datos de la variable de interés de cada archivo.
Aplicar la normalización temporal.
2.3 Estructura de Datos Normalizados: `AnalysisService._get_normalized_data_for_groups` devuelve un diccionario de listas de arrays NumPy (101 puntos), adecuado para SPM.
3. Lógica de Análisis Estadístico Continuo (usando `spm1d`).
3.1 Integración de la Librería `spm1d`.
3.2 `AnalysisService.perform_continuous_analysis`: Método expandido para:
Orquestar la preparación de datos (llamando a `_get_normalized_data_for_groups`).
Recibir los datos normalizados y agrupados.
Preparar los datos en el formato requerido por `spm1d`.
Ejecutar tests básicos de `spm1d` (`ttest2`, `anova1`) y loguear resultados.
3.3 Almacenamiento de Resultados SPM: Guardar los resultados del análisis (ej: la curva SPM, clusters significativos, p-valores) en un formato accesible (ej: JSON, CSV).
4. Generación de Gráficos y Tablas para Análisis Continuo.
4.1 `charting.py` - Nuevas Funciones para Gráficos SPM:
Función para generar gráficos de curvas comparativas: una curva promedio por cada grupo de descriptores, mostrando la variable a lo largo del tiempo normalizado.
Visualizar opcionalmente la desviación estándar o intervalos de confianza alrededor de las curvas promedio.
Superponer la curva del estadístico SPM (ej: t-valor) y resaltar las regiones donde las diferencias son estadísticamente significativas (basado en los p-valores y la teoría de campos aleatorios de `spm1d`).
Generar gráficos estáticos (PNG) e interactivos (HTML con Plotly, si es factible).
4.2 Generación de Tablas de Resultados:
Tablas con los datos normalizados para la variable y los descriptores seleccionados.
Tablas resumiendo los resultados del análisis SPM (ej: p-valores, información de clusters significativos).
4.3 Nomenclatura y Gestión de Archivos:
Definir una nomenclatura clara para los archivos generados (gráficos, tablas, datos SPM), ej: `[Variable]_[DescriptoresComparados]_cont_analysis.[png|html|csv]`.
Guardar estos archivos en una subcarpeta específica dentro de la carpeta del estudio (ej: `AnalisisContinuo`).
5. Gestión de Análisis Continuos Guardados en `AnalysisService`.
5.1 Nuevos Métodos en `AnalysisService`:
`list_continuous_analyses(study_id)`: Lista los análisis continuos guardados.
`delete_continuous_analysis(study_id, analysis_name_or_id)`: Elimina un análisis continuo.
`get_continuous_analysis_details(study_id, analysis_name_or_id)`: Obtiene detalles/archivos de un análisis.
5.2 Integración con UI: Conectar estos métodos a `ContinuousAnalysisResultsView` para la gestión de los análisis.
6. Validación y Consideraciones Adicionales.
6.1 Exclusión de Columnas Irrelevantes: Asegurar que las columnas "Frame" y "Sub Frame" se excluyan del selector de variables y del análisis.
6.2 Validación de Entradas del Usuario: Validar las selecciones en `ContinuousAnalysisConfigDialog` (ej: al menos dos grupos de descriptores, variable válida).
7. Pruebas.
7.1 Pruebas Unitarias: Para la lógica de normalización, interacción con `spm1d`, y generación de gráficos/tablas.
7.2 Pruebas de Integración: Probar el flujo completo desde la configuración en la UI hasta la visualización y gestión de los resultados del análisis continuo.
8. Documentación.
8.1 Actualizar Manual de Usuario: Añadir una sección detallada sobre cómo realizar y interpretar el Análisis Continuo.
8.2 Ayuda en la Interfaz: Considerar añadir tooltips o botones de ayuda en las nuevas ventanas de diálogo/vistas.