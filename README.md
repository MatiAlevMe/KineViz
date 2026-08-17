# KineViz: Análisis, Optimización y Visualización de Datos para Estudios Kinesiológicos

https://github.com/user-attachments/assets/1228d6c1-51da-4ada-bea8-cbeb08e7a742

**Introducción**

**KineViz** es una aplicación de escritorio diseñada para la gestión integral y el análisis avanzado de datos provenientes de estudios kinesiológicos. Es una herramienta robusta para investigadores, profesionales de la kinesiología, fisioterapeutas y estudiantes que necesiten manejar eficientemente datos de movimiento humano y biomecánica.

Desarrollada específicamente para responder a las necesidades de la **Escuela de Kinesiología de la Pontificia Universidad Católica de Valparaíso**, KineViz aborda la complejidad de manejar múltiples herramientas y formatos de archivo, proveyendo un sistema unificado para pasar de la recolección de datos crudos a la obtención de resultados analíticos y visualizaciones significativas.

La aplicación permite el post-procesamiento eficiente de datos de cinemática, cinética y electromiografía, facilitando análisis estadísticos, tanto discretos (comparación de medias, boxplots) como continuos (Análisis Estadístico Paramétrico no Multivariado - SPM). Además, mejora la visualización de resultados generando gráficos informativos y personalizables, y asegura la integridad de los datos mediante mecanismos de validación y copias de seguridad.

Este documento detalla los pasos necesarios para configurar y ejecutar KineViz en sistemas **Windows 10** y **macOS**. La herramienta está programada principalmente en **Python** y hace uso de diversas bibliotecas de código abierto para el procesamiento, análisis y visualización de datos biomecánicos.

---

## Programa EXE de Windows

En la sección **[Releases](https://github.com/MatiAlevMe/KineViz-public/releases)** del repositorio ([v2.0](https://github.com/MatiAlevMe/KineViz-public/releases/tag/v2.0)), encontrarás una versión empaquetada para Windows (`.exe` dentro de un archivo `.zip`) que permite ejecutar KineViz directamente sin necesidad de instalar dependencias adicionales. Esto facilita una rápida puesta en marcha en sistemas **Windows 10**.

---

## Características Principales

KineViz ofrece un conjunto integral de funcionalidades para la gestión y análisis de estudios kinesiológicos:

* **Gestión Centralizada de Estudios**: Un único lugar para crear, organizar y almacenar estudios, gestionando metadatos como el nombre, cantidad de participantes e intentos, y Variables Independientes (VIs).
* **Procesamiento Automatizado de Datos**: Facilita la lectura, validación y estandarización de archivos de datos crudos (`.txt`, `.csv`), copiándolos y procesándolos internamente para diferentes tipos de datos (Cinemática, Cinética, EMG).
* **Análisis Estadístico Avanzado**:
    * **Análisis Discreto**: Permite la comparación de valores puntuales o estadísticos resumidos (máximo, mínimo, promedio) entre diferentes grupos o condiciones, generando tablas de resumen y boxplots.
    * **Análisis Continuo (SPM)**: Para comparar series temporales completas (curvas) entre grupos, identificando diferencias significativas a lo largo del tiempo utilizando Statistical Parametric Mapping.
* **Visualización de Resultados**: Genera gráficos estáticos (PNG) e interactivos (HTML) para los análisis discretos y continuos, incluyendo curvas SPM y clusters significativos.
* **Gestión de Archivos Flexible**: Permite añadir, ver y eliminar archivos de datos dentro de un estudio, con validaciones robustas de formato y estructura.
* **Configuración y Personalización**: Ofrece amplias opciones de configuración, incluyendo temas, tooltips, y gestión de copias de seguridad automáticas y manuales.
* **Funcionalidad "Deshacer Eliminación"**: Permite revertir la última operación de eliminación soportada (estudios, archivos, análisis) para mayor seguridad.
* **Uso del Valor "Nulo" y Alias**: Soporte para la palabra clave "Nulo" en nombres de archivo para VIs no aplicables, y la capacidad de asignar alias descriptivos a los sub-valores para mejorar la legibilidad en las visualizaciones.

---

## Flujos de Trabajo Principales

1.  **Creación de un Nuevo Estudio**: Define el nombre, cantidad de participantes e intentos, y las Variables Independientes (VIs) con sus sub-valores. Es crucial el orden de las VIs, ya que dicta la secuencia en los nombres de los archivos.
2.  **Adición de Archivos a un Estudio**: Los archivos (`.txt` o `.csv`) deben seguir un formato de nombre específico (`ID_Participante [SubValor_VI1] ... NN.ext`) para su correcta validación y procesamiento.
3.  **Realización de un Análisis Discreto**: Accede al gestor de análisis, configura los parámetros de comparación (tipo de dato, cálculo, VIs, supuestos estadísticos) y ejecuta para obtener resultados y gráficos.
4.  **Realización de un Análisis Continuo (SPM)**: Configura el análisis SPM seleccionando la variable de serie temporal, los grupos a comparar y las opciones de visualización para obtener la curva SPM y los clusters significativos.

---

## Recursos Adicionales

* **Manual de Usuario Completo**: Para una guía detallada de todas las funcionalidades, consulta el **[Manual de Usuario](manual_usuario.txt)** (`manual_usuario.txt`) incluido en el repositorio.
* **Ayuda Contextual**: La aplicación incluye botones con `?` y notas emergentes (tooltips) al posicionar el cursor sobre las opciones para una ayuda rápida.
* **Video DEMO**: Un video introductorio **[DEMO](DEMO.mp4)** (`DEMO.mp4`) está disponible para mostrar los flujos de trabajo clave.

---

**Programación y Compatibilidad:**

KineViz está programado principalmente en **Python** y hace uso de diversas bibliotecas de código abierto para el procesamiento, análisis y visualización de datos biomecánicos. Compatible con sistemas **Windows 10** (Versión pública, empaquetada) y **macOS** (Versión privada, desarrollo).
