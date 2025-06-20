Notas y Respuestas para la Refinación del Informe KineViz

## Sobre Tablas para Archivos o Pruebas (Sección Modelo de Datos)

**Pregunta:** ¿Estas seguro que no se tienen tablas para los archivos o las pruebas también? Puedes desarrollar estos dos puntos en un documento txt aparte.

**Respuesta:**

Sí, estoy seguro de que en la implementación actual de KineViz, tal como se describe en el código fuente proporcionado (específicamente en `StudyRepository`, `FileService` y `AnalysisService`), no existen tablas SQL dedicadas exclusivamente para "Archivos" individuales o "Pruebas" (tests/trials) como entidades separadas con sus propios IDs y atributos en la base de datos.

La estrategia adoptada por KineViz es la siguiente:

1.  **Gestión de Archivos:**
    *   La información sobre los archivos de datos (tanto originales como procesados) no se almacena en una tabla de base de datos "Archivos". En su lugar, `FileService` gestiona los archivos basándose en:
        *   **Estructura de Carpetas:** Los archivos se organizan jerárquicamente en el sistema de archivos bajo el directorio de cada estudio y, dentro de este, por participante y tipo de dato (ej: `estudios/[NOMBRE_ESTUDIO]/[ID_PARTICIPANTE]/OG/` y `estudios/[NOMBRE_ESTUDIO]/[ID_PARTICIPANTE]/[TIPO_DATO]/`).
        *   **Convenciones de Nomenclatura:** Los nombres de los archivos deben seguir un formato estricto (`ID_Participante [SubValor_VI1] ... NN.ext`) que codifica la información del participante, las condiciones experimentales (sub-valores de las VIs) y el número de intento. `FileService` y `validators.py` se encargan de parsear y validar estos nombres.
    *   Cuando la aplicación necesita listar o acceder a archivos, `FileService.get_study_files()` escanea dinámicamente la estructura de directorios del estudio correspondiente.
    *   Esta aproximación evita la redundancia de almacenar metadatos de archivos en la base de datos que ya están implícitos en su ruta y nombre, y simplifica la sincronización entre la base de datos y el sistema de archivos.

2.  **Gestión de Pruebas (Trials/Condiciones Experimentales):**
    *   El concepto de "Prueba" o condición experimental específica bajo la cual se toma una medición se define a través de la combinación de Variables Independientes (VIs) y sus sub-valores, tal como se configura en la tabla `estudios` (campo `independent_variables`).
    *   No hay una tabla "Pruebas" separada. La información que definiría una prueba (ej: tipo de salto, condición pre/post) está codificada en los nombres de los archivos de datos a través de los sub-valores de las VIs.
    *   `AnalysisService` (ej: en `_identify_study_groups`) agrupa los archivos y los datos para el análisis basándose en estas combinaciones de sub-valores extraídas de los nombres de archivo.

3.  **Resultados de Análisis:**
    *   De manera similar, los resultados de los análisis (tanto discretos como continuos) no se almacenan como filas en una tabla "ResultadosDeAnalisis" en la base de datos.
    *   Se guardan como archivos en el sistema de carpetas del estudio (ej: `Analisis Discreto/Tablas/`, `Analisis Discreto/Graficos/[VARIABLE]/[NOMBRE_ANALISIS]/`, `Analisis Continuo/[VARIABLE]/[NOMBRE_ANALISIS]/`).
    *   Las configuraciones de los análisis y los metadatos clave (como p-valores) se almacenan en archivos JSON junto a los gráficos o tablas generadas.

**Ventajas de este enfoque:**
*   **Simplicidad de la Base de Datos:** Mantiene el esquema de la base de datos SQLite relativamente simple, centrado en la tabla `estudios`.
*   **Flexibilidad:** Permite una gran flexibilidad en la definición de VIs y la estructura de los estudios sin requerir migraciones complejas de la base de datos.
*   **Gestión Directa de Archivos:** Facilita el manejo de grandes cantidades de archivos de datos, ya que el sistema de archivos es inherentemente bueno para esto.

**Consideraciones:**
*   La consistencia entre la información en los nombres de archivo/estructura de carpetas y la definición de VIs en la base de datos es crucial. Los validadores juegan un papel importante aquí.
*   Consultas complejas que involucren metadatos de archivos o condiciones de prueba específicas deben ser implementadas en la lógica de la aplicación (escaneando y filtrando archivos) en lugar de mediante consultas SQL directas a tablas dedicadas.

En resumen, el diseño actual prioriza un esquema de base de datos más ligero y delega la gestión detallada de archivos y condiciones experimentales a la lógica de la aplicación y a una estructura organizada en el sistema de archivos.

## Sobre el Diagrama de Modelo Relacional Conceptual (Figura 3.5)

**Pregunta:** En cuanto a la figura 4.5, puedes explicar en mayor detalle a que te refieres a mostrar conceptualmente? Tengo que construir un diagrama modelo relacional para decir como interactuó con as tablas, como puedo representarlos en este modelo conceptualmente? No creo que tenga mucho sentido representar un diagrama de modelo relacional de manera conceptual.

**Respuesta:**

Entiendo tu punto sobre la naturaleza de un "diagrama de modelo relacional". Tradicionalmente, estos diagramas (como los diagramas Entidad-Relación) representan tablas SQL y las relaciones entre ellas mediante claves foráneas. Mi sugerencia de "mostrar conceptualmente" busca adaptar esta idea a la realidad de KineViz, donde mucha información estructural no reside en tablas SQL separadas, sino dentro de campos JSON en la tabla `estudios` o en la estructura del sistema de archivos.

El objetivo **no es abandonar** la idea de un diagrama que muestre la estructura de la base de datos, sino **extenderlo** para ilustrar cómo las entidades conceptuales (como VIs, Alias, Archivos) se relacionan con la única tabla SQL principal (`estudios`), aunque no sean tablas SQL por sí mismas.

Aquí te explico cómo puedes construir un diagrama que sea fiel al modelo relacional de la base de datos (la tabla `estudios`) y al mismo tiempo represente estas relaciones "conceptuales":

1.  **Entidad Principal (Tabla SQL):**
    *   Dibuja un rectángulo representando la tabla `estudios`.
    *   Dentro de este, lista sus columnas principales: `id_estudio (PK)`, `nombre_estudio`, `num_participantes` (actualizado de `num_sujetos`), `cantidad_intentos_prueba`, `independent_variables (TEXT/JSON)`, `aliases (TEXT/JSON)`, `is_pinned`, `comentario`.

2.  **Representación de Campos JSON (Conceptual):**
    *   **Para `independent_variables`:**
        *   Puedes dibujar una línea desde la columna `independent_variables` hacia un recuadro o una nota explicativa que ilustre la *estructura* del JSON que contiene. Por ejemplo, este recuadro podría mostrar:
            ```json
            [
              {
                "name": "VI_Nombre_1",
                "descriptors": ["SubValorA", "SubValorB"],
                "allows_combination": true,
                "is_mandatory": false
              }, ...
            ]
            ```
        *   Esto no implica que `independent_variables` sea una tabla separada con una relación de clave foránea, sino que visualiza el *contenido estructurado* de ese campo de texto.
    *   **Para `aliases`:**
        *   Similarmente, una línea desde la columna `aliases` a un recuadro que muestre la estructura del JSON:
            ```json
            {
              "SubValorOriginal1": "AliasDescriptivo1",
              "SubValorOriginal2": "AliasDescriptivo2"
            }
            ```
        *   Podrías incluso dibujar una línea punteada o una anotación que indique que las claves de este JSON (`SubValorOriginal1`) se corresponden con los valores en la lista `descriptors` dentro del JSON de `independent_variables`.

3.  **Representación de la Relación con el Sistema de Archivos (Conceptual):**
    *   Puedes añadir una entidad conceptual llamada "Sistema de Archivos del Estudio" o "Directorio del Estudio".
    *   Dibuja una relación (quizás una línea discontinua o con una etiqueta descriptiva como "Organizado en") desde la columna `nombre_estudio` (o desde la entidad `estudios` en general) hacia esta entidad conceptual "Sistema de Archivos".
    *   Dentro o junto a esta entidad "Sistema de Archivos", puedes anotar la estructura de carpetas clave:
        *   `estudios/[nombre_estudio]/`
        *   `.../[ID_PARTICIPANTE]/OG/`
        *   `.../[ID_PARTICIPANTE]/[TIPO_DATO]/`
        *   `.../Analisis Discreto/`
        *   `.../Analisis Continuo/`
    *   También puedes añadir una nota indicando que los **Nombres de Archivo** (ej: `P01_CMJ_PRE_01.txt`) se validan contra la estructura definida en `independent_variables`.

**¿Por qué "conceptual" y por qué tiene sentido?**

*   **Fidelidad al Diseño Actual:** Refleja con precisión que no estás usando múltiples tablas SQL interrelacionadas para VIs, archivos, etc., sino que has optado por un diseño que utiliza JSON y el sistema de archivos para estas estructuras. Un diagrama E-R tradicional con muchas tablas sería engañoso.
*   **Claridad para el Lector:** Ayuda al lector del informe a entender cómo se almacena y organiza la información completa del estudio, no solo la parte que está estrictamente normalizada en SQL. Muestra dónde reside la "inteligencia" estructural.
*   **Interacción con las Tablas:** Aunque las VIs no sean una tabla, la aplicación *interactúa* con el contenido de la columna `independent_variables` (parseando el JSON) como si fuera una estructura de datos relacional en memoria. El diagrama ayuda a visualizar esto.

**En resumen para el diagrama:**
*   **Sí, es un diagrama de modelo relacional** porque su entidad central es la tabla SQL `estudios` con sus atributos.
*   Se vuelve "conceptual" en la forma en que representa las **relaciones** de esta tabla con datos estructurados que *no* están en otras tablas SQL, sino en campos JSON o en el sistema de archivos.
*   Utiliza anotaciones, recuadros explicativos para el contenido JSON, y representaciones de la estructura de carpetas para mostrar estas relaciones no tradicionales.

Espero que esta explicación aclare la intención. El objetivo es un diagrama informativo y preciso para el diseño *real* de KineViz.