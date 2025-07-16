# KineViz: Análisis, Optimización y Visualización de Datos para Estudios Kinesiológicos

**Introducción**

**KineViz** es una herramienta desarrollada para el análisis y visualización de datos biomecánicos, diseñada específicamente para responder a las necesidades de la **Escuela de Kinesiología de la Pontificia Universidad Católica de Valparaíso**.  

La aplicación permite el post-procesamiento eficiente de datos de cinemática, cinética y electromiografía, facilitando análisis y visualización tanto de datos continuos como discretos (t-test, ANOVA), optimizando la interpretación de resultados para contextos clínicos y deportivos.  

Este documento detalla los pasos necesarios para configurar y ejecutar KineViz en sistemas **Windows 10** y **macOS**. La herramienta está programada principalmente en **Python** y hace uso de diversas bibliotecas de código abierto para el procesamiento, análisis y visualización de datos biomecánicos.

**Releases**

En la sección **Releases** del repositorio encontrarás una versión empaquetada para Windows que permite ejecutar KineViz directamente sin necesidad de instalar dependencias.

## Instrucciones de Ejecución

Antes de ejecutar el programa, necesitarás:

**Requisitos**

    Python 3.x (preferentemente Python 3.8 o superior)
    Librerías necesarias para Python (detalladas a continuación)
    Git (opcional, si vas a clonar desde un repositorio)

### Librerías Necesarias

El programa depende de varias librerías de Python para su correcto funcionamiento. La lista completa y las versiones específicas se encuentran en el archivo `requirements.txt`.
Algunas de las librerías clave incluyen:

    numpy
    pandas
    matplotlib
    scipy
    seaborn
    plotly (para gráficos interactivos)
    tkinter (para la interfaz gráfica de usuario)

Se recomienda encarecidamente instalar todas las dependencias utilizando el archivo `requirements.txt` para asegurar la compatibilidad.

### Estructura del Proyecto

El proyecto KineViz está organizado en los siguientes módulos principales:

- `kineviz/ui/main_window.py`: Ventana principal y lógica central de la interfaz de usuario.
- `kineviz/ui/views/landing_page.py`: Página de inicio de la aplicación.
- `kineviz/core/services/study_service.py`: Lógica central para la gestión de estudios (creación, consulta, etc.).
- `kineviz/core/services/file_service.py`: Lógica central para el manejo de archivos asociados a los estudios.
- `kineviz/core/services/analysis_service.py`: Lógica central para las funcionalidades de análisis de datos.
- `kineviz/ui/views/`: Contiene las diferentes vistas de la aplicación (ej. listado de estudios, vista detallada de un estudio, vista de análisis discreto).
- `kineviz/ui/dialogs/`: Diálogos para interacciones específicas con el usuario (ej. configuración de la aplicación, configuración de análisis, gestión de copias de seguridad).
- `kineviz/ui/widgets/`: Componentes reutilizables de la interfaz de usuario (ej. navegador de archivos, visualización de gráficos, tooltips).
- `kineviz/config/settings.py`: Gestión de la carga y guardado de configuraciones de la aplicación desde `config.ini`.
- `kineviz/core/backup_manager.py`: Lógica para la creación y gestión de copias de seguridad.
- `kineviz/core/undo_manager.py`: Gestión de la funcionalidad de deshacer cambios en la aplicación.
- `kineviz/database/repositories.py`: Define la interacción con la base de datos para la persistencia de datos de estudios.
- `kineviz/utils/logger.py`: Configuración del sistema de logging para el registro de eventos y errores.

Puedes instalar todas las librerías necesarias ejecutando el siguiente comando:

bash

pip install -r requirements.txt

### Instrucciones para Windows 10
Paso 1: Instalar Python

    Descarga Python para Windows desde el sitio oficial de Python.

    Ejecuta el instalador y asegúrate de seleccionar la opción Add Python to PATH durante la instalación.

    Verifica la instalación abriendo Símbolo del Sistema y escribiendo:

    bash

    python --version

Paso 2: Descargar el Programa

    Descarga el archivo ZIP con el programa KineViz, o clona el repositorio GitHub (si está disponible):

    bash

git clone https://github.com/MatiAlevMe/KineViz-public.git

Navega a la carpeta donde guardaste el programa:

bash

    cd path/to/kineviz

Paso 3: Instalar Dependencias

Instala las librerías necesarias de Python:

bash

pip install -r requirements.txt

Paso 4: Ejecutar el Programa

En el Símbolo del Sistema, navega al directorio donde se encuentra el programa KineViz y ejecuta el script principal de Python:

bash

python -m kineviz.app

Esto abrirá la interfaz gráfica de usuario (GUI), donde podrás cargar archivos de datos biomecánicos y realizar análisis.

### Instrucciones para Mac OS
Paso 1: Instalar Python

    Mac OS suele venir con Python preinstalado, pero se recomienda instalar Python 3.x usando Homebrew:

    Abre Terminal y escribe:

    bash

brew install python

Confirma que Python 3.x está instalado:

bash

    python3 --version

Paso 2: Descargar el Programa

    Descarga el archivo ZIP con el programa KineViz, o clona el repositorio GitHub (si está disponible):

    bash

git clone https://github.com/MatiAlevMe/KineViz-public.git

Navega a la carpeta donde guardaste el programa:

bash

    cd path/to/kineviz

Paso 3: Instalar Dependencias

Instala las librerías necesarias de Python:

bash

pip3 install -r requirements.txt

Paso 4: Ejecutar el Programa

En Terminal, navega al directorio donde se encuentra el programa KineViz y ejecuta el script principal de Python:

bash

python3 -m kineviz.app

Esto lanzará la interfaz gráfica de usuario (GUI), permitiéndote procesar y analizar los archivos de datos.

### Solución de Problemas

    Faltan Librerías: Si encuentras problemas con librerías faltantes, asegúrate de que todas las bibliotecas requeridas estén instaladas utilizando la versión correcta de Python.

    Problemas de Permisos (Mac): Si encuentras problemas de permisos al ejecutar el programa, intenta usar sudo:

    bash

    sudo python3 -m kineviz.app

    Problemas con la Ruta de Python: En Windows, si Python no es reconocido, asegúrate de haber agregado Python al PATH del sistema durante la instalación.

## Empaquetado con PyInstaller

Para generar el ejecutable de KineViz usando el archivo de especificación `kineviz.spec`, sigue estos pasos:

**Compatibilidad con Windows**
1. Asegúrate de tener Python 3.12.6 instalado en tu sistema operativo.  
2. Durante la instalación de Python, marca la casilla **Add Python to PATH**.  
3. Clona o descarga el repositorio y descomprime el ZIP en una carpeta local.  
4. Abre la terminal (o PowerShell) en la raíz del proyecto.  
5. Ejecuta:
   ```bash
   pip install -r requirements.txt
   python -m PyInstaller kineviz.spec
6. Una vez completo, ve a la carpeta dist/ y ejecuta:
   ```bash
    dist/KineViz/KineViz.exe
7. Si encuentras problemas, limpia los directorios de compilación y vuelve a intentar:
    ```bash
    rm -rf dist build

**Compatibilidad con macOS**  
Aunque los pasos anteriores están centrados en Windows, el proceso en macOS es prácticamente el mismo con estas diferencias clave:  
1. Instala Python 3.12.6 usando Homebrew (`brew install python@3.12`) o el instalador oficial desde python.org, marcando **Add Python to PATH** si usas el paquete de python.org.  
2. En macOS la llamada al intérprete suele ser `python3` en lugar de `python`.  
3. Ajusta en `kineviz.spec` las rutas de icono y de datos a las convenciones de macOS (por ejemplo, empaqueta recursos en `Contents/Resources`).  
4. Empaqueta con:
     ```bash
     pip3 install -r requirements.txt
     python3 -m PyInstaller kineviz.spec
     ```
5. Al finalizar encontrarás el bundle en `dist/KineViz/KineViz.app`. Ábrelo con:
     ```bash
     open dist/KineViz/KineViz.app
     ```
6. Si surge algún error, limpia y repite:
     ```bash
     rm -rf dist build
     ```

## Licencia

Este proyecto está bajo la Licencia de uso personal de Matías Alevropulos.

Para más información o consultas, contacta con el desarrollador en alevropulos@gmail.com
