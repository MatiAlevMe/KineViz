KineViz - Instrucciones de Ejecución
Introducción

KineViz es una herramienta desarrollada para el análisis y visualización de datos biomecánicos. Este documento proporciona los pasos necesarios para configurar y ejecutar la aplicación en sistemas Windows 10 y Mac OS. El programa está escrito principalmente en Python y utiliza varias bibliotecas de código abierto para procesar y visualizar los datos.
Requisitos

Antes de ejecutar el programa, necesitarás:

    Python 3.x (preferentemente Python 3.8 o superior)
    Librerías necesarias para Python (detalladas a continuación)
    Git (opcional, si vas a clonar desde un repositorio)

Librerías Necesarias

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

Estructura del Proyecto

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

Instrucciones para Windows 10
Paso 1: Instalar Python

    Descarga Python para Windows desde el sitio oficial de Python.

    Ejecuta el instalador y asegúrate de seleccionar la opción Add Python to PATH durante la instalación.

    Verifica la instalación abriendo Símbolo del Sistema y escribiendo:

    bash

    python --version

Paso 2: Descargar el Programa

    Descarga el archivo ZIP con el programa KineViz, o clona el repositorio GitHub (si está disponible):

    bash

git clone https://github.com/MatiAlevMe/KineViz.git

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

python main.py

Esto abrirá la interfaz gráfica de usuario (GUI), donde podrás cargar archivos de datos biomecánicos y realizar análisis.
Instrucciones para Mac OS
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

git clone https://github.com/MatiAlevMe/KineViz.git

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

python3 main.py

Esto lanzará la interfaz gráfica de usuario (GUI), permitiéndote procesar y analizar los archivos de datos.
Solución de Problemas

    Faltan Librerías: Si encuentras problemas con librerías faltantes, asegúrate de que todas las bibliotecas requeridas estén instaladas utilizando la versión correcta de Python.

    Problemas de Permisos (Mac): Si encuentras problemas de permisos al ejecutar el programa, intenta usar sudo:

    bash

    sudo python3 main.py

    Problemas con la Ruta de Python: En Windows, si Python no es reconocido, asegúrate de haber agregado Python al PATH del sistema durante la instalación.

Licencia

Este proyecto está bajo la Licencia de uso personal de Matías Alevropulos.

Para más información o consultas, contacta con el desarrollador en matias.alevropulos.e@mail.pucv.cl
