import configparser
from pathlib import Path
import os
import logging # Importar logging

logger = logging.getLogger(__name__) # Logger para este módulo

class AppSettings:
    """Gestiona la carga y guardado de configuraciones desde config.ini."""

    DEFAULT_SETTINGS = {
        'SETTINGS': {
            'estudios_por_pagina': '10',
            'files_per_page': '10',
            'pdfs_per_page': '10',
            'discrete_tables_per_page': '15' # Añadir valor por defecto
        }
        # DESCRIPTOR_ALIASES ya no se gestiona aquí
    }

    def __init__(self, config_filename='config.ini'):
        """
        Inicializa AppSettings.

        :param config_filename: Nombre del archivo de configuración.
        """
        # Determinar la ruta raíz del proyecto para construir rutas absolutas
        # Asumiendo que este archivo está en kineviz/config/
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.config_path = self.project_root / config_filename
        self.config = configparser.ConfigParser()
        self.load_settings()

    def _ensure_config_exists(self):
        """Crea el archivo config.ini con valores por defecto si no existe."""
        if not self.config_path.exists():
            logger.warning(f"No se encontró {self.config_path}. Creando archivo con valores por defecto.")
            try:
                # Crear configparser con valores por defecto
                default_config = configparser.ConfigParser()
                default_config.read_dict(self.DEFAULT_SETTINGS)
                # Asegurarse de que el directorio padre exista (si config.ini no está en la raíz)
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as configfile:
                    default_config.write(configfile)
                logger.info(f"Archivo de configuración creado en: {self.config_path}")
            except OSError as e:
                logger.critical(f"No se pudo crear el archivo de configuración en {self.config_path}: {e}", exc_info=True)
                # Podríamos lanzar una excepción aquí o continuar con valores en memoria

    def load_settings(self):
        """Carga las configuraciones desde el archivo config.ini."""
        self._ensure_config_exists() # Asegura que el archivo exista antes de leer
        try:
            self.config.read(self.config_path, encoding='utf-8')
            # Validar/asegurar sección [SETTINGS] si es necesario
            if 'SETTINGS' not in self.config:
                logger.warning("Sección [SETTINGS] no encontrada en config.ini. Usando valores por defecto.")
                self.config['SETTINGS'] = self.DEFAULT_SETTINGS['SETTINGS']
            # Ya no se necesita asegurar DESCRIPTOR_ALIASES aquí

        except configparser.Error as e:
            logger.error(f"Error leyendo {self.config_path}: {e}. Usando valores por defecto.", exc_info=True)
            # Resetear a valores por defecto en memoria si hay error de lectura
            self.config = configparser.ConfigParser()
            self.config.read_dict(self.DEFAULT_SETTINGS)
        except Exception as e:
            logger.error(f"Error inesperado cargando configuraciones: {e}. Usando valores por defecto.", exc_info=True)
            self.config = configparser.ConfigParser()
            self.config.read_dict(self.DEFAULT_SETTINGS)


    def save_settings(self):
        """Guarda las configuraciones actuales en el archivo config.ini."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            logger.info(f"Configuraciones guardadas en {self.config_path}")
        except OSError as e:
            logger.error(f"Error guardando configuraciones en {self.config_path}: {e}", exc_info=True)
            # Considerar mostrar un error al usuario
            raise # Relanzar para que la UI pueda manejarlo

    def get_setting(self, key: str, fallback=None) -> str | None:
        """Obtiene un valor de configuración de la sección [SETTINGS]."""
        # Asegurar que la sección exista
        if 'SETTINGS' not in self.config:
             return fallback
        return self.config.get('SETTINGS', key, fallback=fallback)

    def get_int_setting(self, key: str, fallback: int) -> int:
        """Obtiene un valor de configuración como entero."""
        value_str = self.get_setting(key)
        if value_str is None:
            return fallback
        try:
            return int(value_str)
        except (ValueError, TypeError):
            logger.warning(f"Valor inválido para '{key}' en config.ini ('{value_str}'). Usando fallback: {fallback}")
            return fallback

    def set_setting(self, key: str, value: str):
        """Establece un valor de configuración en la sección [SETTINGS]."""
        # Asegurarse de que la sección exista antes de establecer
        if 'SETTINGS' not in self.config:
            self.config['SETTINGS'] = {}
        self.config['SETTINGS'][key] = str(value) # Guardar como string

    # --- Métodos para gestión de alias de descriptores (ELIMINADOS) ---
    # Los alias ahora se gestionan por estudio a través de StudyService.

    # --- Métodos específicos para configuraciones conocidas ---

    @property
    def studies_per_page(self) -> int:
        return self.get_int_setting('estudios_por_pagina', 10)

    @studies_per_page.setter
    def studies_per_page(self, value: int):
        self.set_setting('estudios_por_pagina', str(value))

    @property
    def files_per_page(self) -> int:
        return self.get_int_setting('files_per_page', 10)

    @files_per_page.setter
    def files_per_page(self, value: int):
        self.set_setting('files_per_page', str(value))

    @property
    def pdfs_per_page(self) -> int:
        return self.get_int_setting('pdfs_per_page', 10)

    @pdfs_per_page.setter
    def pdfs_per_page(self, value: int):
        self.set_setting('pdfs_per_page', str(value))

    @property
    def discrete_tables_per_page(self) -> int:
        """Número de tablas de análisis discreto a mostrar por página."""
        return self.get_int_setting('discrete_tables_per_page', 15)

    @discrete_tables_per_page.setter
    def discrete_tables_per_page(self, value: int):
        self.set_setting('discrete_tables_per_page', str(value))

    def reset_to_defaults(self):
         """Restablece las configuraciones en memoria a los valores por defecto."""
         logger.info("Restableciendo configuraciones a valores por defecto...")
         # Crear un nuevo configparser y leer los defaults (sin alias)
         new_config = configparser.ConfigParser()
         new_config.read_dict(self.DEFAULT_SETTINGS)
         self.config = new_config # Reemplazar el config actual
         # Guardar inmediatamente los valores por defecto en el archivo
         self.save_settings()
         logger.info("Configuraciones restablecidas y guardadas.")
