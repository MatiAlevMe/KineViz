# Roadmap del Desarrollo de KineViz

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

## [Hecho] Fase 1: Mejoras Incrementales - Detección de Frecuencia
1. [Hecho] Implementar detección automática de tipo de frecuencias basada en metadatos del archivo.
Detalle: Modificar la lógica en `kineviz.core.data_processing.file_handlers.leer_seccion` y `kineviz.core.services.file_service._process_and_copy_file` para identificar Cinemática ("Model Outputs"), Cinética ("Force Plate") y Electromiográfica.
1.1 [Hecho] Implementación de identificador de archivo para Cinemática.
1.2 [Hecho] Implementación de identificador de archivo para Cinética. 
1.3 [Hecho] Implementación de identificador de archivo para Electromiográfica de confirmación del formato/identificador.

## [Hecho] Fase 2: Análisis Estadístico Discreto y Reportes
1. [Hecho] Generación de Matrices: Crear tablas por tipo de cálculo y combinación de descriptores (ej: "máximo_cinemática_CMJ_Normal").
1.1 [Hecho] Servicio `generate_discrete_summary_tables`: Lógica para agrupar archivos por combinación de descriptores, leer stats, crear DataFrames y guardar CSVs/TSVs/SCSVs/XLSX.
1.2 [Hecho] Botón en `StudyView`: Añadir botón "Análisis Discreto".
1.3 [Hecho] Vista `DiscreteAnalysisView`: Crear vista para listar/mostrar/eliminar tablas generadas, con filtros y paginación.
2. Identificación de Grupos y Columnas Comunes.
2.1 [Hecho] `AnalysisService._identify_study_groups`: Identifica grupos únicos por combinación de descriptores.
2.2 [Hecho] `AnalysisService.get_discrete_analysis_groups`: Expone grupos combinados a la UI.
2.3 [Hecho] `AnalysisService.get_common_columns_for_groups`: Encuentra columnas comunes en tablas CSV internas para grupos combinados.
3. [Hecho] Diálogo de Configuración de Análisis Individual.
3.1 [Hecho] Crear `ConfigureIndividualAnalysisDialog`: UI para seleccionar Frecuencia, Cálculo, Grupos combinados (dinámico), Columna (dinámico), y supuestos (paramétrico/pareado).
3.2 [Hecho] Integración con VIs: Grupos combinados ahora usan formato "VI: Alias" y se seleccionan correctamente.
4. [Hecho] Diálogo de Gestión de Análisis Individual.
4.1 [Hecho] Crear `IndividualAnalysisManagerDialog`: UI para listar, ver (gráfico estático/interactivo), eliminar análisis guardados y abrir carpeta.
4.2 [Hecho] Botón en `DiscreteAnalysisView`: Añadir botón para abrir el gestor.
5. [Hecho] Generación de Gráfico Boxplot Comparativo.
5.1 [Hecho] Función `create_comparison_boxplot`: En `charting.py` usando seaborn/matplotlib.
5.2 [Hecho] `AnalysisService.perform_individual_analysis`: Lógica para leer datos de tablas CSV internas, preparar datos por grupo combinado y llamar a `create_comparison_boxplot`. Guarda gráfico PNG y config.json.
6. [Hecho] Implementación de Tests Estadísticos y Mejoras Gráficas.
6.1 [Hecho] Lógica en `perform_individual_analysis`: Ejecutar tests (t-test/ANOVA/Wilcoxon/Kruskal/Friedman) usando `scipy.stats`.
6.2 [Hecho] Mejorar `create_comparison_boxplot`: Usar `swarmplot`, añadir leyenda, mostrar significancia (statannot para 2 grupos, p-valor general para >2).
6.3 [Hecho] Integrar LEYENDAS con VIs: Leyenda muestra nombres completos ("Grupo X - VI: Alias").
6.4 [Hecho] Integrar EL EJE HORIZONTAL con VIs: Eje X muestra etiquetas genéricas ("Grupo 1", "Grupo 2").
6.5 [Hecho] Tests post-hoc: Considerar y añadir si es necesario.
7. [Hecho] Generación de Gráfico Interactivo (Plotly).
7.1 [Hecho] Añadir dependencia `plotly`.
7.2 [Hecho] Crear `create_interactive_comparison_boxplot`: En `charting.py` para generar HTML.
7.3 [Hecho] Modificar `perform_individual_analysis`: Generar y guardar HTML.
8. [Hecho] Gestión de Análisis Guardados.
8.1 [Hecho] `AnalysisService.list_individual_analyses` / `delete_individual_analysis`.
8.2 [Hecho] Conectar UI `IndividualAnalysisManagerDialog`: Cargar, ver PNG, ver HTML, eliminar, abrir carpeta. Mostrar grupos combinados y p-valor.
9. [Hecho] Implementar agregación de datos para análisis de efectos principales en `perform_individual_analysis`: Cuando se selecciona el modo "1VI" en la configuración de análisis individual, se agregan datos de las tablas de resumen combinadas correspondientes para permitir comparaciones de efectos principales (ej. "todos los jóvenes" vs "todos los mayores").
10. [Hecho] Adaptar `get_common_columns_for_groups` para efectos principales: Asegurar que la selección de columnas comunes funcione correctamente cuando se comparan efectos principales en modo "1VI".

## [Hecho] Fase 3: Refactorización a Variables Independientes (VI) y Mejoras UI/Validación
1. [Hecho] Modificar Modelo de Estudio.
1.1 [Hecho] DB Conceptual: Reemplazada columna `descriptores` por `independent_variables` (JSON TEXT) y añadida `aliases` (JSON TEXT) en tabla `estudios`.
1.2 [Hecho] Repositorio (`StudyRepository`): Actualizados `_create_tables` (migración), `create_study`, `get_study_by_id`, `update_study` para manejar `independent_variables` y `aliases`.
1.3 [Hecho] Servicio (`StudyService`): Actualizados métodos para manejar conversión Python <-> JSON para `independent_variables` y `aliases`. Añadidos `get_study_aliases`, `update_study_aliases`.
2. [Hecho] Refactorizar UI Creación/Edición Estudio (`StudyDialog`).
2.1 [Hecho] Flujo UI: Implementada UI jerárquica para definir VIs y sus Descriptores (con botones '+', '🗑️').
2.2 [Hecho] Restricciones Edición: Deshabilitados añadir/eliminar VIs/Descriptores; permitido renombrar VIs.
2.3 [Hecho] Botón Ayuda VI: Añadido botón `(?)` coloreado que abre `kineviz/docs/help/study_dialog_iv_help.txt`.
3. [Hecho] Refactorizar Validación (`validators.py`).
3.1 [Hecho] Validador Datos Estudio: Creado `validate_study_iv_data` (incluye regla anti-"Nulo").
3.2 [Hecho] Validador Nombres Archivo: Reescrito `validate_filename_for_study_criteria` para formato `[ID_Participante] [VAL_VI1]...[VAL_VIn] NN`, donde `ID_Participante` es una combinación de letras seguidas de números (ej: `P01`, `Sujeto007`). Valida orden de VIs, valores permitidos (incl. "Nulo"), y regla de al menos un descriptor no-Nulo. Devuelve `(bool, subject_id, list[str|None], attempt_num)`.
3.3 [Hecho] Eliminar Validador Antiguo: Eliminado `validate_study_data`.
4. [Hecho] Integrar Validación.
4.1 [Hecho] `StudyDialog`: Usa `validate_study_iv_data` en `save` (corregido bug edición).
4.2 [Hecho] `FileService.add_files_to_study`: Usa nuevo `validate_filename_for_study_criteria`.
5. [Hecho] Actualizar `FileService`.
5.1 [Hecho] `add_files_to_study`: Obtiene estructura VI de `StudyService` para validación.
5.2 [Hecho] `get_unique_study_parameters`: Adaptado para extraer parámetros basados en la nueva estructura y nombres de archivo. Devuelve descriptores únicos encontrados por *posición* de VI.
6. [Hecho] Actualizar Vista Estudio (`StudyView`).
6.1 [Hecho] Mostrar VIs: Añadido label para mostrar nombres de VIs.
6.2 [Hecho] Mostrar Descriptores (Tooltip/Popup): Añadido botón `ℹ️` que muestra Descriptores por VI (con alias) en popup.
6.3 [Hecho] Botón Ayuda General: Añadido botón `(?)` que abre `kineviz/docs/help/study_view_help.txt`.
7. [Hecho] Refactorizar Gestión de Alias.
7.1 [Hecho] Mover a DB: Implementado carga/guardado de alias por estudio en `StudyRepository` y `StudyService`.
7.2 [Hecho] Adaptar `DescriptorAliasDialog`: Carga/guarda alias vía `StudyService`.
7.3 [Hecho] Limpiar `AppSettings`: Eliminados métodos de alias globales.
8. [Hecho] Adaptar Servicios y UI de Análisis.
8.1 [Hecho] `AnalysisService._identify_study_groups`: Crea claves de grupo combinadas (ej: "VI1=DescA;VI2=DescB").
8.2 [Hecho] `AnalysisService` (Resto): Adaptados `get_discrete_analysis_groups`, `_get_data_for_parameters`, `perform_analysis`, `perform_individual_analysis`, `generate_report`, `generate_discrete_summary_tables`, `get_common_columns_for_groups` para usar claves combinadas y mostrar nombres de VI/alias.
8.3 [Hecho] `ConfigureIndividualAnalysisDialog`: Muestra/selecciona nombres de grupo legibles ("Grupo X - ..."), guarda claves originales.
8.4 [Hecho] `IndividualAnalysisManagerDialog`: Muestra nombres de grupo legibles ("Grupo X - ...").
9. [Hecho] Pruebas: Añadir/actualizar pruebas unitarias y de integración para validadores, servicios, UI refactorizada y lógica de agrupación/análisis.
10. [Hecho] Crear Archivos de Ayuda.
10.1 [Hecho] `docs/help/study_dialog_iv_help.txt`.
10.2 [Hecho] `docs/help/study_view_help.txt`.
11. [Hecho] Validación Número Sujetos/Intentos.
11.1 [Hecho] `FileService.add_files_to_study`: Validar que no se exceda `num_subjects` ni `attempts_count` al añadir archivos, considerando estado actual + lote nuevo.
11.2 [Hecho] `StudyDialog.save` (Edición): Validar que no se pueda reducir `num_subjects` por debajo de los sujetos existentes, ni `attempts_count` por debajo del máximo intento existente.
11.3 [Hecho] Actualizar Documentación Ayuda: Reflejar nuevas validaciones en `study_dialog_iv_help.txt` y `study_view_help.txt`.
12. [Hecho] Eliminar Funcionalidad "Analizar Estudio" Antigua.
12.1 [Hecho] `StudyView`: Eliminar botón "Analizar Estudio".
12.2 [Hecho] `AnalysisDialog` y `MainWindow.show_analysis_dialog`: Eliminados/Comentados ya que la funcionalidad fue reemplazada.
13. [Hecho] Refinamientos UI y Texto en Diálogo/Vista Estudio.
13.1 [Hecho] `StudyDialog`: Mejorar layout de checkboxes "¿Multiple?" y "¿Obligatorio?" (visibilidad condicional). Actualizar etiquetas ("Cantidad de Participantes", "Cantidad de Intento(s) de Prueba", "Nombre del Estudio", "Variable(s) Independientes (VIs)").
13.2 [Hecho] `StudyView`: Actualizar etiquetas ("Nombre del Estudio", "Cantidad de Participantes", "Cantidad de Intento(s) de Prueba", "Variable(s) Independientes (VIs)"). Mejorar popup de info de VIs para mostrar manejo de descriptores.
13.3 [Hecho] Actualizar Manuales de Ayuda: Reflejar cambios de etiquetas y comportamiento en `manual_usuario.txt`, `study_dialog_iv_help.txt`, `study_view_help.txt`.
14. [Hecho] Implementar Validación Avanzada de Archivos según Reglas de VI.
14.1 [Hecho] `validators.py`: Creada función `validate_files_for_vi_rules` para verificar:
Regla de Descriptor Fijo (si VI no permite combinación).
Regla de Descriptores Obligatorios (si VI permite combinación y es obligatoria).
14.2 [Hecho] `FileService`:
Creado helper `_get_all_study_files_descriptors` para obtener estado de descriptores de archivos existentes.
Integrada `validate_files_for_vi_rules` en `add_files_to_study`.
Si validación falla, se loguean errores específicos y se devuelve un error genérico a la UI.
14.3 [Hecho] Notificación UI: `FileDialog` mostrará el error genérico si la validación de reglas de VI falla.
15. [Hecho] Ajuste UI en Diálogo de Estudio.
15.1 [Hecho] `StudyDialog` UI: Ajustado el espaciado vertical de los checkboxes "¿Multiple?" y "¿Obligatorio?" para que estén más cerca de los descriptores. (Refinado para igualar espaciado inter-descriptor).

## [EnProgreso] Fase 4: Análisis Continuo (SPM)
1. [Pendiente] Diseño y Prototipado de UI para Análisis Continuo.
1.1 [Hecho] Botón en `StudyView`: Añadir botón "Análisis Continuo" en la vista de estudio, junto al de "Análisis Discreto".
1.2 [Hecho] Crear `ContinuousAnalysisConfigDialog` (o similar): Creado diálogo base para configurar el análisis continuo.
Selección de Tipo de datos (ej: Cinemática, Cinética). Solo permite Cinemática inicialmente.
Selección de Variable/Columna de Agrupación: Permitir al usuario seleccionar la variable específica a analizar (ej: "LAnkleAngles_X", "KneeMoment_Y"). Esto implica identificar y listar las columnas de datos relevantes de los archivos procesados, excluyendo "Frame", "Sub Frame" y "Tiempo".
Selector de Descriptores: Permitir al usuario seleccionar dos o más grupos de descriptores (basados en las VIs del estudio) para comparar.
Opciones de Visualización y Anotación: Permitir al usuario configurar cómo se visualizan las curvas promedio (EEM, DE, IC) y si se muestran anotaciones de clusters SPM y delimitaciones de tiempo.
1.3 [En Progreso] Crear `ContinuousAnalysisView` (anteriormente `ContinuousAnalysisResultsView`): Vista en la UI para:
    - [Hecho] Listar los análisis continuos generados (nombre, columna, grupos, fecha).
    - [Hecho] Proveer opciones para cada análisis: ver gráfico SPM (PNG), ver configuración (JSON), abrir carpeta de resultados, eliminar análisis.
    - [Hecho] Botón para lanzar `ContinuousAnalysisConfigDialog` para crear nuevos análisis.
    - [Pendiente] Mostrar filtros y opciones de ordenación para la lista de análisis.
2. [Hecho] Implementación de Normalización de Datos Temporales.
2.1 [Hecho] Lógica de Normalización Temporal: Implementar una función (posiblemente en `processors.py` o un nuevo módulo) para normalizar la duración de las secuencias de datos a 101 puntos (0-100%).
Esto se aplicará a la variable seleccionada para cada archivo/sujeto/intento.
Investigar y aplicar métodos de interpolación adecuados (ej: splines, interpolación lineal).
2.2 [Hecho] Procesamiento de Archivos para Normalización: En `AnalysisService`, crear lógica para:
Identificar los archivos relevantes del estudio según los tipos de datos y sub-valores seleccionados.
Leer la columna de datos de la variable de interés de cada archivo.
Aplicar la normalización temporal.
2.3 [Hecho] Estructura de Datos Normalizados: `AnalysisService._get_normalized_data_for_groups` devuelve un diccionario de listas de arrays NumPy (101 puntos), adecuado para SPM.
3. [Hecho] Lógica de Análisis Estadístico Continuo (usando `spm1d`).
3.1 [Hecho] Integración de la Librería `spm1d`.
3.2 [Hecho] `AnalysisService.perform_continuous_analysis`: Método expandido para:
Orquestar la preparación de datos (llamando a `_get_normalized_data_for_groups`).
Recibir los datos normalizados y agrupados.
Preparar los datos en el formato requerido por `spm1d`.
Ejecutar tests básicos de `spm1d` (`ttest2`, `anova1`), realizar inferencia estadística y loguear resultados.
3.3 [Hecho] Almacenamiento de Resultados SPM: Guardar los resultados del análisis (curva SPM, umbral crítico, grados de libertad, clusters significativos con p-valores) en formato JSON.
4. [Hecho] Generación de Gráficos y Tablas para Análisis Continuo.
4.1 [Hecho] `charting.py` - Nuevas Funciones para Gráficos SPM:
    - [Hecho] Función `create_spm_results_plot` para generar gráfico estático (PNG) con:
        - Panel superior: Curvas promedio por grupo (con opciones de visualización EEM, DE, IC) vs. tiempo normalizado.
        - Panel inferior: Curva del estadístico SPM, umbral crítico y resaltado de clusters significativos (con opciones de anotación).
        - Opciones para delimitar el rango de tiempo mostrado en el gráfico y añadir etiquetas personalizadas.
    - [Pendiente] Generar gráficos interactivos (HTML con Plotly, si es factible).
4.2 [Pendiente] Nomenclatura de Creación de Carpeta de Guardado de Archivos:
Guardar los archivos del analisis en una subcarpeta específica dentro de la carpeta del estudio (ej: `[NOMBRE_ESTUDIO]/Analisis Continuo/[NOMBRE_COMPLETO_MUSCULO_MAS_SU_DIMENSION_PERO_SIN _LA_UNIDAD_DE_MEDIDA] (ie. "Estudio de Adultos Mayores/Analisis Continuo/LAnkleMoment X")`).
5. [Pendiente] Gestión de Análisis Continuos Guardados en `AnalysisService`.
5.1 [Pendiente] Nuevos Métodos en `AnalysisService`:
`list_continuous_analyses(study_id)`: Lista los análisis continuos guardados.
`delete_continuous_analysis(study_id, analysis_name_or_id)`: Elimina un análisis continuo.
`get_continuous_analysis_details(study_id, analysis_name_or_id)`: Obtiene detalles/archivos de un análisis.
5.2 [Pendiente] Integración con UI: Conectar estos métodos a `ContinuousAnalysisResultsView` para la gestión de los análisis.

## [Pendiente] Fase 5: Funcionalidades Adicionales
1. [Pendiente] Copias de Seguridad Automaticas en la Ventana de Estudios.
1.1 [Pendiente] Implementar copias de seguridad automáticas cada vez que se agreguen archivos a un estudio.
1.2 [Pendiente] Implementar opción de volver a versión anterior del estudio.
2. [Pendiente] Ayuda en la Interfaz: Añadir Tooltips Adicionales.
2.1 [Pendiente] Añadir tooltips que explique el formato de cada ventana relevante:
Editar estudio, crear estudio, agregar archivos, crear analisis discreto, crear analisis continuo.
3. [Pendiente] Optimización del Sistema.
3.1 [Pendiente] Decidir si mantener todas las tablas del analisis discreto o solamente las tablas .xlsx para ahorrar espacio.
3.2 [Pendiente] Decidir formato final y filtrado de las ventanas de tablas de datos como:
Ventana de estudio, ventana de estudio especifico, ventana de tablas de analisis discreto, analisis discreto, analisis continuo

## [Pendiente] Fase 6: Cambios Opcionales.
1. [Pendiente] (Cambio Manual) Cambiar terminos de:
"paciente" a "participante", "Paciente" a "Participante"
"pacientes" a "participantes", "Pacientes" a "Participantes"
"sujeto de prueba" a "participante", "Sujetos de Prueba" a "Participantes"
2. [Pendiente] Implementar "Full Two-Way ANOVA"
Full Two-Way ANOVA: The current "2VIs" mode performs comparisons within a level of a fixed VI (simple main effects). A full two-way ANOVA (e.g., spm1d.stats.anova2 or spm1d.stats.anova2rm for repeated measures) would assess:
2.1 [Pendiente] Main effect of VI1 (e.g., "Edad")
2.2 [Pendiente] Main effect of VI2 (e.g., "Peso")
2.3 [Pendiente] Interaction effect (VI1 x VI2) This would require a different UI setup (selecting both VIs and all their relevant levels) and significant changes in AnalysisService to  structure data for spm1d.stats.anova2 and interpret its multi-faceted results.
2.4 [Pendiente] Post-hoc tests for ANOVA: If an ANOVA (either 1-way in 1VI mode or the simple main effect ANOVA in 2VI mode) is significant, post-hoc tests would be needed to determine which specific groups differ. spm1d offers functions for this (e.g., spm1d.stats.posthoc.ttest_paired, spm1d.stats.posthoc.anova1_ttest_paired).
2.5 [Pendiente] Visualizations for 2VI: Specific plots for interactions (if a 2-way ANOVA was implemented) or more complex comparative plots for the "slicing" approach might be beneficial.
3. [Pendiente] Funcionalidad Extra para Eliminar:
3.1 [Pendiente] Botón para eliminar todos los archivos dentro de un estudio.
3.2 [Pendiente] Botón para eliminar todas las pruebas para el analisis discreto y el analisis continuo.
3.3 [Pendiente] Botón "Eliminación Masiva" para seleccionar los archivos que se deseen eliminar. Tanto en la ventana de estudio como en la ventana de pruebas de analisis discreto y pruebas analisis continuo.
4. [Pendiente] Agregar las Siguiente Reglas a la Eliminación de Archivos Individuales o Eliminación Masiva:
"Si no hay archivos en el estudio elimina todos los archivos y carpetas dentro del estudio"
"Si no hay archivos para un participante en particular, elimina la carpeta con el nombre del participante"
5. [Pendiente] Agregar Botón para Refrescar Archivos en Todas las Tablas:
Este botón mostrara los nuevos archivos en caso de por ejemplo el usuario modifique los archivos locales.
6. [Pendiente] Manejo de Floats al Procesar Archivos en un Estudio:
Que exista la posibilidad de manejar situaciones donde los archivos de entrada esten en float como "Pte03 CMJ 03.txt: could not convert string to float: '5,47567'" en cuyo caso se debería poder convertir al valor convencional de "5.47567".
7. [Pendiente] Opción para Destacar Estudios (Hasta 5) en la Ventana Principal
Cosa de que esos estudios se mantengan sobre todos los demas estudios.
Con un botón de chincheta y se mantengan fijos sobre los demas estudios.
8. [Pendiente] Opción para Comentar Estudios en la Ventana del Estudio Especifico (Maximo 150 caracteres)
Para que el usuario tenga la opción de escribir algún detalle que estime conveniente sobre el estudio especifico.
9. [Pendiente] Opciones de Accesibilidad en la Configuración del Software:
Como aumentar el tamaño de las letras, y cambiar el tema de blanco a oscuro.
10. [Pendiente] Mejoras en la UI

## [Pendiente] Fase 7: Pruebas, Documentación y Despliegue
1. [Pendiente] Análisis Discreto
1.1 [Pendiente] Corrección de Errores: Revisar y corregir errores conocidos (ej: formato cabeceras CSV, error generación tablas discretas, inconsistencia nombres archivo análisis individual).
1.2 [Pendiente] Integración y Pruebas: Integrar y probar toda la funcionalidad de análisis discreto, incluyendo análisis de efectos principales.
2. [Pendiente] Análisis Continuo 
2.1 [Pendiente] Pruebas Unitarias: Para la lógica de normalización, interacción con `spm1d`, y generación de gráficos/tablas.
2.2 [Pendiente] Pruebas de Integración: Probar el flujo completo desde la configuración en la UI hasta la visualización y gestión de los resultados del análisis continuo.
3. [Pendiente] Documentación.
3.1 [Pendiente] Refactorizar los manuales de usuario de la siguiente manera:
3.1.1 [Pendiente] Unir todos los manuales en el manual principal con distintas secciones, esto es primero una descripción general del software, los objetivos, algunos flujos de trabajo u casos de uso del software que se podrían realizar, y una sección para cada parte importante como crear nuevo estudio, editar, agregar archivos, todo lo referente a la ventana principal, a la ventana de estudios, a la ventana de analisis continuo, a la ventana de analisis discreto y los distintos archivos resultantes, los formatos, etc. 
3.1.2 [Pendiente] Agregar referencias dentro del mismo manual que diga "Vaya a la sección X" o similares para referirse a que sección ir del manual para alguna información importante relevante.
3.2 [Pendiente] Eliminar todos los botones que hagan referencia a manuales antiguos que no sean el manual principal.
3.3 [Pendiente] (Cambio Manual) Modificar Tabla de Modelo de Datos:
Modificar terminología de Frecuencia a Tipo de Dato y Pruebas (POST/PRE)
3.4 [Pendiente] (Cambio Manual) Modificar el Abstract:
Sugiero mejorar el abstract del proyecto para sea más claro en lo que hace Kineviz y en que tipos de análisis se enfoca
3.5 [Pendiente] (Cambio Manual) Revisión Final de ortografía del informe con V. D.
También agregar imagenes finales del software funcionando
3.6 [Pendiente] (Cambio Manual) Revisión Final de ortografía de la presentación con V. D.
Agregar el DEMO y optimizar los tiempos + añadir los ultimos cambios
3.7 [Pendiente] (Cambio Manual) Limpiar archivos como kineviz.spec, kineviz/docs/recurso, logs de la repo final
1. [Pendiente] (Cambio Manual) Creación de Demo en Video del Uso del Software con V. D.
2. [Pendiente] Empaquetado y Distribución con Paquetes Distribuibles.
5.1 [Pendiente] Configurar PyInstaller: Creado y refinando `kineviz.spec` para definir el proceso de build (corrigiendo errores de hidden imports, backends, etc.).
5.2 [Pendiente] Generar Build Windows: Ejecutar PyInstaller en Windows para crear el paquete.
5.3 [Pendiente] Generar Build macOS: Ejecutando PyInstaller en macOS para crear el paquete (`.app` bundle).
5.4 [Pendiente] Pruebas de Paquetes: Probar los paquetes generados en máquinas limpias de Windows 10/11 y macOS 11+.

# Arquitectura de KineViz

## 1. Introducción
KineViz es una aplicación de escritorio diseñada para la gestión, procesamiento y análisis de datos kinesiológicos. Su objetivo principal es facilitar a los investigadores y profesionales la organización de estudios, el manejo de archivos de datos crudos y procesados, y la realización de análisis estadísticos tanto discretos como continuos (SPM).

## 2. Estructura del Proyecto
La aplicación sigue una estructura modular para separar responsabilidades:
`kineviz/`: Directorio raíz del código fuente.
`app.py`: Punto de entrada de la aplicación (inicia `MainWindow`).
`core/`: Contiene la lógica de negocio central y el dominio de la aplicación.
`ui/`: Responsable de la interfaz de usuario y la interacción con el usuario.
`database/`: Maneja la persistencia de datos, principalmente la base de datos SQLite.
`config/`: Gestiona la configuración de la aplicación.
`utils/`: Utilidades generales como el sistema de logging.
`docs/`: Documentación del proyecto, incluyendo este archivo y el roadmap.

## 3. Módulos Principales y Responsabilidades

3.1 `kineviz.core` - Lógica de Negocio y Dominio
`core.services`: Orquesta las operaciones y la lógica de negocio.
`StudyService`: Gestiona las operaciones CRUD (Crear, Leer, Actualizar, Eliminar) para los estudios. Maneja los metadatos del estudio, la definición de Variables Independientes (VIs), y los alias de los descriptores.
`FileService`: Administra las operaciones de archivos dentro de los estudios, incluyendo la adición, eliminación, listado y procesamiento de archivos crudos. También extrae parámetros únicos (como frecuencias y descriptores) de los archivos procesados.
`AnalysisService`: Contiene la lógica para todos los tipos de análisis (discreto, individual, continuo). Esto incluye la agregación de datos, cálculos estadísticos (utilizando `scipy.stats` para discreto y `spm1d` para continuo), generación de reportes en PDF (con `reportlab`) y gráficos (con `matplotlib`, `seaborn`, `plotly`). Implementa métodos como `get_available_frequencies_for_study` y `get_data_columns_for_frequency` para poblar selectores en diálogos de configuración de análisis. Para el análisis continuo, incluye `_get_normalized_data_for_groups` para preparar los datos y `perform_continuous_analysis` para orquestar el análisis SPM.
`core.data_processing`: Módulos encargados del procesamiento y manejo de datos.
`file_handlers`: Responsable de leer e interpretar archivos de datos crudos (ej. `.txt`), extraer metadatos, identificar el tipo de frecuencia (Cinemática, Cinética, EMG) y realizar el procesamiento inicial para generar archivos estandarizados (incluyendo la adición de una columna "Tiempo").
`processors`: Contiene funciones de utilidad para la transformación de datos, cálculos estadísticos básicos (máximo, mínimo, rango) sobre DataFrames de pandas, formateo de valores, y normalización temporal de datos (ej. `normalize_temporal_data`).
`directory_manager`: Gestiona la creación y la estructura de los directorios para los estudios y los pacientes dentro del sistema de archivos.
`core.exceptions`: Define clases de excepciones personalizadas para un manejo de errores más específico dentro de la aplicación (ej. `FileNotFoundError`, `InvalidFileFormatError`).

3.2 `kineviz.ui` - Capa de Interfaz de Usuario (Tkinter)
`ui.main_window.py` (`MainWindow`): Es la ventana principal de la aplicación. Orquesta la navegación entre las diferentes vistas y diálogos. Mantiene instancias de los servicios principales (`StudyService`, `FileService`, `AnalysisService`) y `AppSettings`.
`ui.views`: Vistas principales que ocupan la mayor parte de la ventana.
`LandingPage`: Vista inicial que se muestra cuando no existen estudios en la aplicación.
`MainView`: Muestra la lista paginada de estudios existentes, permitiendo buscar y acceder a ellos.
`StudyView`: Presenta una vista detallada de un estudio específico. Incluye un navegador de archivos (`FileBrowser`), opciones para agregar archivos, gestionar alias, y acceder a los módulos de análisis.
`DiscreteAnalysisView`: Interfaz para gestionar y visualizar los resultados de los análisis discretos (tablas resumen generadas).
*(Futuro: `ContinuousAnalysisView` para mostrar resultados de análisis SPM)*.
`ui.dialogs`: Ventanas modales que se utilizan para tareas específicas y entrada de datos.
`StudyDialog`: Para crear nuevos estudios o editar los metadatos de estudios existentes, incluyendo la definición de Variables Independientes (VIs) y sus descriptores.
`FileDialog`: Permite al usuario seleccionar y agregar archivos de datos a un estudio específico.
`DescriptorAliasDialog`: Facilita la gestión (creación, edición, eliminación) de alias para los descriptores de las VIs de un estudio.
`ConfigureIndividualAnalysisDialog`: Diálogo para configurar los parámetros de un análisis discreto individual (selección de frecuencia, cálculo, columna, grupos a comparar, y supuestos estadísticos).
`IndividualAnalysisManagerDialog`: Permite listar, visualizar (gráficos estáticos e interactivos), eliminar y abrir la carpeta de resultados de los análisis individuales guardados.
`ContinuousAnalysisConfigDialog`: Diálogo para configurar los parámetros de un análisis continuo (SPM). Incluye selección de frecuencia de datos, la variable/columna específica a analizar, y la selección de grupos de descriptores (para modos 1VI y 2VIs [efectos simples]).
`ConfigDialog`: Permite al usuario modificar configuraciones globales de la aplicación (ej. elementos por página) que se guardan en `config.ini`.
`AnalysisDialog`: (Obsoleto/Comentado) Diálogo anterior para análisis, reemplazado por funcionalidades más específicas.
`ui.widgets`: Componentes de UI reutilizables.
`FileBrowser`: Widget para listar, filtrar y gestionar archivos dentro de un estudio, con paginación.
`charting`: Módulo para generar gráficos estáticos (con `matplotlib`/`seaborn`) e interactivos (con `plotly`), como boxplots y gráficos de barras.
`ui.utils`: Utilidades específicas de la interfaz de usuario.
`validators`: Contiene funciones para validar entradas del usuario, nombres de archivo según criterios de VIs (formato `ID_Participante [VI_Subvalor1] ... Intento`, donde `ID_Participante` es texto+número), y la consistencia de los datos del estudio.

3.3 `kineviz.database` - Persistencia de Datos
`database.repositories.StudyRepository`: Implementa el patrón Repositorio para abstraer las interacciones con la base de datos SQLite (`kineviz.db`). Es responsable de la creación de tablas y las operaciones CRUD para los datos de los estudios (metadatos, VIs, alias).

3.4 `kineviz.config` - Configuración de la Aplicación
`config.settings.AppSettings`: Gestiona la carga y el guardado de las configuraciones de la aplicación desde y hacia el archivo `config.ini`. Proporciona una interfaz para acceder a estos ajustes.
`config.ini`: Archivo de texto plano que almacena configuraciones persistentes como el número de elementos por página.

3.5 `kineviz.utils` - Utilidades Generales
`utils.logger.setup_logging`: Configura el sistema de logging para la aplicación, definiendo el nivel de log y el formato de los mensajes, guardando los logs en archivos.

## 4. Flujos de Datos Clave (Ejemplos)

1. Creación de un Nuevo Estudio:
1.1. `MainWindow` invoca `show_create_study_dialog()`.
1.2. Se abre `StudyDialog`. El usuario ingresa los metadatos del estudio y define las Variables Independientes (VIs) y sus descriptores.
1.3. Al guardar, `StudyDialog` llama a `StudyService.create_study()` con los datos ingresados.
1.4. `StudyService` valida los datos (usando `validators.validate_study_iv_data`), y luego interactúa con `StudyRepository.create_study()`.
1.5. `StudyRepository` escribe la información del nuevo estudio en la base de datos SQLite.
1.6. `DirectoryManager.crear_estructura_estudio()` (llamado desde `StudyService` o `StudyRepository`) crea la carpeta física para el estudio en el sistema de archivos.
1.7. `MainWindow` refresca la `MainView` para mostrar el nuevo estudio.

2. Adición de Archivos a un Estudio:
2.1. Desde `StudyView`, el usuario hace clic en "Agregar Archivos", lo que abre `FileDialog`.
2.2. El usuario selecciona uno o más archivos de datos.
2.3. `FileDialog` llama a `FileService.add_files_to_study()` con los archivos seleccionados y el ID del estudio.
2.4. `FileService`:

2.4.1 Obtiene las VIs del estudio desde `StudyService`.
2.4.2. Valida los nombres de los archivos contra las VIs y sus descriptores (usando `validators.validate_filename_for_study_criteria`, que espera un formato como `IDParticipante [SubValorVI1] ... Intento.ext`, donde `IDParticipante` es texto seguido de números, ej: `P01`).
2.4.3. Valida contra el número de sujetos e intentos definidos en el estudio.
2.4.4. Valida contra las reglas de combinación y obligatoriedad de las VIs (usando `validators.validate_files_for_vi_rules`).
2.4.5. Si las validaciones son exitosas, copia los archivos originales a la estructura de carpetas del estudio (`estudios/<nombre_estudio>/<nombre_paciente>/origen/`).
2.4.6. Procesa cada archivo (usando `file_handlers.leer_seccion`) para extraer datos, identificar la frecuencia, y generar un archivo procesado estandarizado en la carpeta correspondiente (ej. `estudios/<nombre_estudio>/<nombre_paciente>/<frecuencia>/`).

2.5. `StudyView` refresca el `FileBrowser` para mostrar los nuevos archivos.

3. Realización de un Análisis Discreto Individual:
3.1. Desde `DiscreteAnalysisView`, el usuario accede a `IndividualAnalysisManagerDialog` y luego a `ConfigureIndividualAnalysisDialog`.
3.2. El usuario configura los parámetros del análisis: nombre, frecuencia, cálculo (Maximo, Minimo, Rango), columna de datos (variable), grupos a comparar (basados en VIs), y supuestos estadísticos (paramétrico, pareado).
3.3. El diálogo llama a `AnalysisService.perform_individual_analysis()` con la configuración.
3.4. `AnalysisService`:

3.4.1. Lee los datos relevantes de las tablas de resumen CSV previamente generadas (ubicadas en `estudios/<nombre_estudio>/Analisis Discreto/Tablas/<frecuencia>/`).
3.4.2. Agrupa los datos según los grupos seleccionados. Si es un análisis de efecto principal (modo "1VI"), agrega datos de múltiples tablas combinadas.
3.4.3. Realiza la prueba estadística seleccionada (ej. t-test, ANOVA, Wilcoxon, Kruskal-Wallis) usando `scipy.stats`.
3.4.4. Genera un gráfico boxplot comparativo (estático PNG con `matplotlib`/`seaborn` y opcionalmente interactivo HTML con `plotly`) usando `charting.create_comparison_boxplot` y `charting.create_interactive_comparison_boxplot`.
3.4.5. Guarda la configuración del análisis y los resultados estadísticos (p-valor) en un archivo `config.json` y el gráfico en la carpeta del análisis (`estudios/<nombre_estudio>/Analisis Discreto/Individual/<nombre_analisis>/`).

3.5. Los resultados pueden ser visualizados y gestionados a través de `IndividualAnalysisManagerDialog`.

4. Configuración de un Análisis Continuo:
4.1. Desde `StudyView`, el usuario hace clic en "Análisis Continuo".
4.2. `MainWindow` llama a `show_continuous_analysis_config_dialog()`.
4.3. Se abre `ContinuousAnalysisConfigDialog`.
4.4. El diálogo llama a `AnalysisService.get_available_frequencies_for_study()` para poblar el combobox de frecuencias.
4.5. Al seleccionar una frecuencia, el diálogo llama a `AnalysisService.get_data_columns_for_frequency()` para poblar el combobox de variables.
4.6. El usuario selecciona una frecuencia, una variable, el modo de agrupación (1VI o 2VIs) y los grupos específicos a comparar.
4.7. Al "Aceptar", el diálogo pasa la configuración a `AnalysisService`, que intenta realizar el análisis SPM (t-test o ANOVA de un factor) y guarda los resultados y la configuración.

## 5. Patrones de Diseño y Convenciones Importantes
Capa de Servicios (Service Layer): Centraliza la lógica de negocio y la orquestación de operaciones, desacoplando la UI de la lógica de datos directa.
Patrón Repositorio (Repository Pattern): Utilizado en `StudyRepository` para desacoplar los servicios de los detalles específicos de acceso a la base de datos SQLite.
Separación de Responsabilidades (similar a MVC/MVP):
`ui` (Vistas y Diálogos): Responsables de la presentación y captura de la entrada del usuario (Vista y parte del Controlador/Presentador).
`core.services`: Contienen la lógica de la aplicación y actúan como intermediarios (parte del Controlador/Presentador y Modelo de negocio).
`database.repositories`: Manejan la persistencia de datos (parte del Modelo de datos).
Tkinter para la UI: Uso de la biblioteca estándar de Python para la interfaz gráfica de usuario.
Logging Centralizado: Uso consistente del módulo `logging` de Python, configurado en `utils.logger`, para registrar eventos y errores de la aplicación.
Manejo de Excepciones Personalizadas: Uso de excepciones definidas en `core.exceptions` para un control de errores más granular.
Configuración Externa: Uso de `config.ini` para ajustes de la aplicación que pueden ser modificados sin cambiar el código.

## 6. Estructuras de Datos Clave / DTOs (Data Transfer Objects)
Objeto/Diccionario de Estudio: Estructura utilizada por `StudyService` y `StudyRepository` para representar un estudio. Incluye: `id`, `name`, `num_subjects`, `attempts_count`, `independent_variables` (JSON/lista de dicts), `aliases` (JSON/dict).
Estructura de Variable Independiente (VI): Una lista de diccionarios, donde cada diccionario representa una VI:
    `{'name': str, 'descriptors': list[str], 'allows_combination': bool, 'is_mandatory': bool}`.
Diccionarios de Información de Archivo: Utilizados por `FileService` y `FileBrowser` para representar archivos. Incluyen: `path` (Path), `name` (str), `type` (str: "Raw", "Processed"), `frequency` (str), `patient` (str), `descriptors` (list[str|None]).
Diccionarios de Configuración de Análisis: Utilizados para pasar parámetros a `AnalysisService` y para guardar las configuraciones de análisis individuales. Ejemplos:
    Análisis Discreto Individual: `{'name': str, 'frequency': str, 'calculation': str, 'column': str (formato 'Atributo/Columna/Unidad'), 'groups': list[str (claves de grupo)], 'parametric': bool, 'paired': bool, 'grouping_mode': str, 'primary_vi_name': str|None, 'fixed_vi_name': str|None, 'fixed_descriptor_display': str|None}`.
Claves de Grupo para Análisis: String combinado que representa una condición experimental única, basado en las VIs y sus descriptores. Formato: `"VI1_Nombre=DescriptorValor;VI2_Nombre=DescriptorValor"`. Ejemplo: `"TipoSalto=CMJ;Condicion=PRE"`.

## 7. Notas sobre el Descriptor "Nulo"
Concepto: "Nulo" es un valor de descriptor especial que indica la ausencia de un descriptor específico para una Variable Independiente (VI) en un archivo particular. Esto es útil cuando una VI no aplica a todas las mediciones o cuando se quiere analizar un efecto principal ignorando otras VIs.
En Nombres de Archivo: Si una VI no es obligatoria y no se especifica un descriptor para ella en un archivo, se puede usar explícitamente la palabra `Nulo` en el nombre del archivo para esa posición de VI (ej: `P01 CMJ Nulo 1.txt`). El validador `validate_filename_for_study_criteria` maneja esto.
En Lógica de Agrupación: Al identificar grupos para análisis (`_identify_study_groups`), "Nulo" se trata como cualquier otro descriptor, permitiendo agrupar archivos que comparten la "ausencia" de ciertos descriptores. La clave de grupo reflejará esto, ej: `"VI1=CMJ;VI2=Nulo"`.
Validación: Existe una regla que impide nombrar explícitamente un descriptor como "Nulo" (ignorando mayúsculas/minúsculas) durante la definición de VIs en `StudyDialog` para evitar ambigüedades. "Nulo" es un estado que se representa con `None` internamente o la palabra "Nulo" en el nombre de archivo.
Regla "Al Menos Un Descriptor No-Nulo": Para que un nombre de archivo sea válido, debe contener al menos un descriptor que no sea "Nulo" (implícito o explícito) si hay VIs definidas. Esto asegura que el archivo se asocie con alguna condición experimental.

## 8. Consideraciones Adicionales
Internacionalización (i18n): Actualmente la UI está predominantemente en español. No hay un sistema formal de i18n.
Pruebas Automatizadas: El proyecto tiene una estructura para pruebas (`tests/unit`, `tests/integration`), pero la cobertura y mantenimiento de estas es un proceso continuo.
Dependencias Clave: `pandas` para manipulación de datos, `numpy` para operaciones numéricas, `scipy` para estadísticas, `matplotlib` y `seaborn` para gráficos estáticos, `plotly` para gráficos interactivos, `reportlab` para PDFs, `openpyxl` para exportación a Excel.
