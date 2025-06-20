import configparser
from pathlib import Path
import os
import sys # Necesario para sys._MEIPASS
import logging # Importar logging
from kineviz.utils.paths import get_application_base_dir # Import for application base directory

logger = logging.getLogger(__name__) # Logger para este módulo

def get_resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        # Asegurarse de que sea un objeto Path
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # No se está ejecutando en un paquete de PyInstaller (modo desarrollo)
        # Asume que settings.py está en kineviz/config/
        # Sube tres niveles para llegar a la raíz del proyecto
        base_path = Path(__file__).resolve().parent.parent.parent

    # Une la ruta base con la ruta relativa del recurso
    resource_path = base_path / relative_path
    logger.debug(f"Calculated resource path for '{relative_path}': {resource_path}")
    return resource_path

class AppSettings:
    """Gestiona la carga y guardado de configuraciones desde config.ini."""

    DEFAULT_SETTINGS = {
        'SETTINGS': {
            'estudios_por_pagina': '10',
            'files_per_page': '10',
            'analysis_items_per_page': '10',
            'discrete_tables_per_page': '10',
            'font_scale': '1.0',
            'theme': 'Claro', # Changed default
            'show_factory_reset_button': 'False',
            'enable_hover_tooltips': 'True', # Changed default
            'max_automatic_backups': '10', # Changed default
            'max_manual_backups': '10',     # Changed default
            'automatic_backup_cooldown_seconds': '60',
            'backups_per_page': '10',
            'enable_automatic_backups': 'True', # Changed default
            'enable_manual_backups': 'True',     # Changed default
            # 'show_advanced_backup_options': 'False', # Removed, will not be persisted
            # 'backup_before_restore' is replaced by enable_pre_restore_backups
            'enable_pre_restore_backups': 'True',    # New, for pre-restore backups
            'max_pre_restore_backups': '10',         # New, max pre-restore backups
            'pre_restore_backup_cooldown_seconds': '60', # New, cooldown for pre-restore
            'enable_undo_delete': 'False', # New, for undo delete functionality
            'undo_cache_timeout_seconds': '300', # New, 5 minutes timeout for undo cache
            'log_level': 'WARNING' # New, for logging level (DEBUG, INFO, WARNING, ERROR), default to WARNING
        }
        # DESCRIPTOR_ALIASES ya no se gestiona aquí
    }

# Define VALID_LOG_LEVELS at the module level for easier import
VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]

class AppSettings:
    """Gestiona la carga y guardado de configuraciones desde config.ini."""

    DEFAULT_SETTINGS = {
        'SETTINGS': {
            'estudios_por_pagina': '10',
            'files_per_page': '10',
            'analysis_items_per_page': '10',
            'discrete_tables_per_page': '10',
            'font_scale': '1.0',
            'theme': 'Claro', # Changed default
            'show_factory_reset_button': 'False',
            'enable_hover_tooltips': 'True', # Changed default
            'max_automatic_backups': '10', # Changed default
            'max_manual_backups': '10',     # Changed default
            'automatic_backup_cooldown_seconds': '60',
            'backups_per_page': '10',
            'enable_automatic_backups': 'True', # Changed default
            'enable_manual_backups': 'True',     # Changed default
            # 'show_advanced_backup_options': 'False', # Removed, will not be persisted
            # 'backup_before_restore' is replaced by enable_pre_restore_backups
            'enable_pre_restore_backups': 'True',    # New, for pre-restore backups
            'max_pre_restore_backups': '10',         # New, max pre-restore backups
            'pre_restore_backup_cooldown_seconds': '60', # New, cooldown for pre-restore
            'enable_undo_delete': 'False', # New, for undo delete functionality
            'undo_cache_timeout_seconds': '300', # New, 5 minutes timeout for undo cache
            'log_level': 'WARNING' # New, for logging level (DEBUG, INFO, WARNING, ERROR), default to WARNING
        }
        # DESCRIPTOR_ALIASES ya no se gestiona aquí
    }

    # VALID_LOG_LEVELS was moved to module level

    def __init__(self, config_filename='config.ini'):
        """
        Inicializa AppSettings.

        :param config_filename: Nombre del archivo de configuración (relativo a la raíz del proyecto/bundle).
        """
        # Use get_application_base_dir() for config.ini path
        app_base = get_application_base_dir()
        self.config_path = app_base / config_filename
        logger.info(f"Using configuration file path: {self.config_path}")

        # project_root is no longer needed here for config_path resolution.
        # If other parts of AppSettings rely on self.project_root, it should be reviewed.
        # For now, we assume its primary use was for config_path.
        # self.project_root = Path(__file__).resolve().parent.parent.parent # Example, if needed elsewhere

        self.config = configparser.ConfigParser()
        self.load_settings()

    def _validate_loaded_config(self) -> bool:
        """
        Validates the currently loaded self.config against DEFAULT_SETTINGS.
        Checks for missing keys, extra keys, and unparseable/out-of-range values.
        Returns True if valid, False otherwise.
        """
        if 'SETTINGS' not in self.config:
            logger.error("Config validation failed: [SETTINGS] section missing.")
            return False

        default_keys = set(self.DEFAULT_SETTINGS['SETTINGS'].keys())
        loaded_keys = set(self.config['SETTINGS'].keys())

        if loaded_keys != default_keys:
            missing_keys = default_keys - loaded_keys
            extra_keys = loaded_keys - default_keys
            if missing_keys:
                logger.error(f"Config validation failed: Missing keys in [SETTINGS]: {missing_keys}")
            if extra_keys:
                logger.error(f"Config validation failed: Extra keys in [SETTINGS]: {extra_keys}")
            return False

        # Validate each setting's value and type
        try:
            # Use properties for their built-in validation logic where possible
            # For settings that are just retrieved with get_int_setting, etc.,
            # we need to replicate or enhance the validation here if properties don't cover it.

            # Integer positive values (must be > 0)
            strictly_positive_int_settings = [
                'estudios_por_pagina', 'files_per_page',
                'analysis_items_per_page', 'discrete_tables_per_page',
                'backups_per_page', # Added backups_per_page here
                # max_automatic_backups and max_manual_backups are now also strictly positive if enabled
            ]
            for key in strictly_positive_int_settings:
                val = self.get_int_setting(key, -1)
                if val <= 0:
                    raw_val = self.config.get('SETTINGS', key, fallback=None)
                    logger.error(f"Config validation failed: '{key}' must be a positive integer (>0), got '{raw_val}'.")
                    return False

            # Max backups (must be > 0 if enabled, otherwise value doesn't strictly matter but should be valid int)
            if self.get_bool_setting('enable_automatic_backups', False):
                if self.get_int_setting('max_automatic_backups', -1) <= 0:
                    raw_val = self.config.get('SETTINGS', 'max_automatic_backups', fallback=None)
                    logger.error(f"Config validation failed: 'max_automatic_backups' must be a positive integer (>0) when enabled, got '{raw_val}'.")
                    return False
            else: # Check it's a valid integer even if not enabled
                 if self.get_int_setting('max_automatic_backups', -1) < 0 : # Allow 0 if we decide, but user asked for positive
                    raw_val = self.config.get('SETTINGS', 'max_automatic_backups', fallback=None)
                    logger.error(f"Config validation failed: 'max_automatic_backups' must be a non-negative integer, got '{raw_val}'.")
                    return False


            if self.get_bool_setting('enable_manual_backups', False):
                if self.get_int_setting('max_manual_backups', -1) <= 0:
                    raw_val = self.config.get('SETTINGS', 'max_manual_backups', fallback=None)
                    logger.error(f"Config validation failed: 'max_manual_backups' must be a positive integer (>0) when enabled, got '{raw_val}'.")
                    return False
            else: # Check it's a valid integer even if not enabled
                if self.get_int_setting('max_manual_backups', -1) < 0:
                    raw_val = self.config.get('SETTINGS', 'max_manual_backups', fallback=None)
                    logger.error(f"Config validation failed: 'max_manual_backups' must be a non-negative integer, got '{raw_val}'.")
                    return False


            # Cooldown (non-negative integer)
            if self.get_int_setting('automatic_backup_cooldown_seconds', -1) < 0:
                raw_val = self.config.get('SETTINGS', 'automatic_backup_cooldown_seconds', fallback=None)
                logger.error(f"Config validation failed: 'automatic_backup_cooldown_seconds' must be a non-negative integer, got '{raw_val}'.")
                return False

            # Pre-restore backups settings
            if self.get_bool_setting('enable_pre_restore_backups', False):
                if self.get_int_setting('max_pre_restore_backups', -1) <= 0:
                    raw_val = self.config.get('SETTINGS', 'max_pre_restore_backups', fallback=None)
                    logger.error(f"Config validation failed: 'max_pre_restore_backups' must be a positive integer (>0) when enabled, got '{raw_val}'.")
                    return False
            else: # Check it's a valid integer even if not enabled
                 if self.get_int_setting('max_pre_restore_backups', -1) < 1 : # Must be at least 1
                    raw_val = self.config.get('SETTINGS', 'max_pre_restore_backups', fallback=None)
                    logger.error(f"Config validation failed: 'max_pre_restore_backups' must be a positive integer (>=1), got '{raw_val}'.")
                    return False
            
            if self.get_int_setting('pre_restore_backup_cooldown_seconds', -1) < 0:
                raw_val = self.config.get('SETTINGS', 'pre_restore_backup_cooldown_seconds', fallback=None)
                logger.error(f"Config validation failed: 'pre_restore_backup_cooldown_seconds' must be a non-negative integer, got '{raw_val}'.")
                return False

            if self.get_int_setting('undo_cache_timeout_seconds', -1) < 0:
                raw_val = self.config.get('SETTINGS', 'undo_cache_timeout_seconds', fallback=None)
                logger.error(f"Config validation failed: 'undo_cache_timeout_seconds' must be a non-negative integer, got '{raw_val}'.")
                return False
            
            # Font scale (positive float)
            font_scale_val_str = self.get_setting('font_scale', '0.0')
            if float(font_scale_val_str) <= 0:
                logger.error(f"Config validation failed: 'font_scale' must be a positive float, got '{font_scale_val_str}'.")
                return False

            # Theme (specific strings)
            theme_val = self.get_setting('theme', '')
            if theme_val not in ['Claro', 'Oscuro']: # Changed valid themes
                logger.error(f"Config validation failed: 'theme' must be one of ['Claro', 'Oscuro'], got '{theme_val}'.")
                return False

            # Log level (specific strings)
            log_level_val = self.get_setting('log_level', '')
            if log_level_val.upper() not in VALID_LOG_LEVELS: # Use module-level VALID_LOG_LEVELS
                logger.error(f"Config validation failed: 'log_level' must be one of {VALID_LOG_LEVELS}, got '{log_level_val}'.")
                return False
            
            # Booleans (show_factory_reset_button, enable_hover_tooltips, enable_automatic_backups, enable_manual_backups)
            # get_bool_setting handles parse errors by returning fallback, so we check if the raw string is valid.
            boolean_settings = [
                'show_factory_reset_button', 'enable_hover_tooltips',
                'enable_automatic_backups', 'enable_manual_backups',
                # 'show_advanced_backup_options', # Removed
                'enable_pre_restore_backups', # Updated
                'enable_undo_delete' # New
            ]
            for key in boolean_settings:
                raw_val = self.config.get('SETTINGS', key, fallback=None)
                if raw_val is None or raw_val.lower() not in ('true', 'yes', '1', 'on', 'false', 'no', '0', 'off', ''): # Allow empty string as false for robustness
                    logger.error(f"Config validation failed: '{key}' has an invalid boolean value '{raw_val}'.")
                    return False

        except ValueError: # Catch float conversion errors for font_scale
            logger.error("Config validation failed: Error converting a numeric setting value.", exc_info=True)
            return False
        except Exception as e: # Catch any other unexpected error during validation
            logger.error(f"Unexpected error during config validation: {e}", exc_info=True)
            return False
            
        return True

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
        """Carga las configuraciones desde el archivo config.ini.
        Si el archivo no existe, está corrupto, o contiene valores inválidos/extras,
        se restablecerá a los valores por defecto.
        """
        self._ensure_config_exists() # Asegura que el archivo exista antes de leer
        
        needs_reset = False
        try:
            self.config.read(self.config_path, encoding='utf-8')
            if not self._validate_loaded_config():
                logger.warning(f"Validación de {self.config_path} fallida. Se restablecerá a valores por defecto.")
                needs_reset = True
        except configparser.Error as e:
            logger.error(f"Error parseando {self.config_path}: {e}. Se restablecerá a valores por defecto.", exc_info=True)
            needs_reset = True
        except Exception as e: # Catch other unexpected errors during read or initial validation
            logger.error(f"Error inesperado cargando configuraciones desde {self.config_path}: {e}. Se restablecerá a valores por defecto.", exc_info=True)
            needs_reset = True

        if needs_reset:
            self.reset_to_defaults() # This saves the defaults to disk
            # Re-read the now default config file
            try:
                self.config.read(self.config_path, encoding='utf-8')
                logger.info(f"Configuración recargada desde {self.config_path} después del reseteo.")
            except Exception as e_reread:
                # This should ideally not happen if reset_to_defaults works
                logger.critical(f"Error crítico: No se pudo recargar config.ini después de resetear: {e_reread}. La aplicación puede estar inestable.", exc_info=True)
                # Fallback to in-memory defaults if re-read fails catastrophically
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

    def get_bool_setting(self, key: str, fallback: bool) -> bool:
        """Obtiene un valor de configuración como booleano."""
        value_str = self.get_setting(key)
        if value_str is None:
            return fallback
        if value_str.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value_str.lower() in ('false', 'no', '0', 'off'):
            return False
        logger.warning(f"Valor booleano inválido para '{key}' en config.ini ('{value_str}'). Usando fallback: {fallback}")
        return fallback

    def set_setting(self, key: str, value: str):
        """Establece un valor de configuración en la sección [SETTINGS]."""
        # Asegurarse de que la sección exista antes de establecer
        if 'SETTINGS' not in self.config:
            self.config['SETTINGS'] = {}
        self.config['SETTINGS'][key] = str(value) # Guardar como string

    # --- Métodos para gestión de alias de sub-valores (ELIMINADOS) ---
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
    def analysis_items_per_page(self) -> int: # Renamed from pdfs_per_page
        return self.get_int_setting('analysis_items_per_page', 10) # Renamed key

    @analysis_items_per_page.setter
    def analysis_items_per_page(self, value: int): # Renamed from pdfs_per_page
        self.set_setting('analysis_items_per_page', str(value)) # Renamed key

    @property
    def discrete_tables_per_page(self) -> int:
        """Número de tablas de análisis discreto a mostrar por página."""
        return self.get_int_setting('discrete_tables_per_page', 10)

    @discrete_tables_per_page.setter
    def discrete_tables_per_page(self, value: int):
        self.set_setting('discrete_tables_per_page', str(value))

    @property
    def font_scale(self) -> float:
        """Factor de escala de la fuente."""
        try:
            return float(self.get_setting('font_scale', '1.0'))
        except ValueError:
            logger.warning(f"Valor inválido para 'font_scale' en config.ini. Usando fallback: 1.0")
            return 1.0

    @font_scale.setter
    def font_scale(self, value: float):
        self.set_setting('font_scale', str(value))

    @property
    def theme(self) -> str:
        """Tema de la aplicación (ej: 'Claro', 'Oscuro')."""
        return self.get_setting('theme', 'Claro') # Changed default

    @theme.setter
    def theme(self, value: str):
        self.set_setting('theme', value)

    @property
    def show_factory_reset_button(self) -> bool:
        """Controla la visibilidad del botón de reseteo de fábrica."""
        return self.get_bool_setting('show_factory_reset_button', False)

    @show_factory_reset_button.setter
    def show_factory_reset_button(self, value: bool):
        self.set_setting('show_factory_reset_button', str(value))

    @property
    def enable_hover_tooltips(self) -> bool:
        """Controla si los tooltips por hover están habilitados."""
        return self.get_bool_setting('enable_hover_tooltips', False)

    @enable_hover_tooltips.setter
    def enable_hover_tooltips(self, value: bool):
        self.set_setting('enable_hover_tooltips', str(value))

    @property
    def max_automatic_backups(self) -> int:
        """Maximum number of automatic backups to keep."""
        return self.get_int_setting('max_automatic_backups', 4)

    @max_automatic_backups.setter
    def max_automatic_backups(self, value: int):
        self.set_setting('max_automatic_backups', str(value))

    @property
    def max_manual_backups(self) -> int:
        """Maximum number of manual backups to keep."""
        return self.get_int_setting('max_manual_backups', 4)

    @max_manual_backups.setter
    def max_manual_backups(self, value: int):
        self.set_setting('max_manual_backups', str(value))

    @property
    def automatic_backup_cooldown_seconds(self) -> int:
        """Cooldown period in seconds for automatic backups. Must be non-negative."""
        value = self.get_int_setting('automatic_backup_cooldown_seconds', 60)
        if value < 0:
            logger.warning(f"Invalid negative value '{value}' for 'automatic_backup_cooldown_seconds'. Using default 60.")
            return 60
        return value

    @automatic_backup_cooldown_seconds.setter
    def automatic_backup_cooldown_seconds(self, value: int):
        if value < 0:
            logger.warning(f"Attempted to set invalid negative value '{value}' for 'automatic_backup_cooldown_seconds'. Setting to 0 instead.")
            self.set_setting('automatic_backup_cooldown_seconds', '0')
        else:
            self.set_setting('automatic_backup_cooldown_seconds', str(value))

    @property
    def backups_per_page(self) -> int:
        """Number of backups to display per page in the backup manager."""
        return self.get_int_setting('backups_per_page', 10)

    @backups_per_page.setter
    def backups_per_page(self, value: int):
        self.set_setting('backups_per_page', str(value))

    @property
    def enable_automatic_backups(self) -> bool:
        """Controls if automatic backups are enabled."""
        return self.get_bool_setting('enable_automatic_backups', False)

    @enable_automatic_backups.setter
    def enable_automatic_backups(self, value: bool):
        self.set_setting('enable_automatic_backups', str(value))

    @property
    def enable_manual_backups(self) -> bool:
        """Controls if manual backups are enabled."""
        return self.get_bool_setting('enable_manual_backups', False)

    @enable_manual_backups.setter
    def enable_manual_backups(self, value: bool):
        self.set_setting('enable_manual_backups', str(value))

    # Property show_advanced_backup_options removed as it's no longer persisted.
    # The checkbox in ConfigDialog will manage its state locally.

    # Property backup_before_restore is removed, replaced by enable_pre_restore_backups and its related settings

    # @property
    # def backup_before_restore(self) -> bool:
    #     return self.get_bool_setting('backup_before_restore', True)

    # @backup_before_restore.setter
    def backup_before_restore(self, value: bool):
        self.set_setting('backup_before_restore', str(value))

    # --- New properties for Pre-Restore Backups ---
    @property
    def enable_pre_restore_backups(self) -> bool:
        """Controls if pre-restore backups ('respaldo') are enabled."""
        return self.get_bool_setting('enable_pre_restore_backups', True)

    @enable_pre_restore_backups.setter
    def enable_pre_restore_backups(self, value: bool):
        self.set_setting('enable_pre_restore_backups', str(value))

    @property
    def max_pre_restore_backups(self) -> int:
        """Maximum number of pre-restore backups to keep. Must be >= 1."""
        value = self.get_int_setting('max_pre_restore_backups', 10)
        if value < 1:
            logger.warning(f"Invalid value '{value}' for 'max_pre_restore_backups' (must be >= 1). Using default 10.")
            return 10
        return value

    @max_pre_restore_backups.setter
    def max_pre_restore_backups(self, value: int):
        if value < 1:
            logger.warning(f"Attempted to set invalid value '{value}' for 'max_pre_restore_backups'. Setting to 1 instead.")
            self.set_setting('max_pre_restore_backups', '1')
        else:
            self.set_setting('max_pre_restore_backups', str(value))

    @property
    def pre_restore_backup_cooldown_seconds(self) -> int:
        """Cooldown period in seconds for pre-restore backups. Must be non-negative."""
        value = self.get_int_setting('pre_restore_backup_cooldown_seconds', 60)
        if value < 0:
            logger.warning(f"Invalid negative value '{value}' for 'pre_restore_backup_cooldown_seconds'. Using default 60.")
            return 60
        return value

    @pre_restore_backup_cooldown_seconds.setter
    def pre_restore_backup_cooldown_seconds(self, value: int):
        if value < 0:
            logger.warning(f"Attempted to set invalid negative value '{value}' for 'pre_restore_backup_cooldown_seconds'. Setting to 0 instead.")
            self.set_setting('pre_restore_backup_cooldown_seconds', '0')
        else:
            self.set_setting('pre_restore_backup_cooldown_seconds', str(value))

    @property
    def enable_undo_delete(self) -> bool:
        """Controls if the undo delete feature is enabled."""
        return self.get_bool_setting('enable_undo_delete', False)

    @enable_undo_delete.setter
    def enable_undo_delete(self, value: bool):
        self.set_setting('enable_undo_delete', str(value))

    @property
    def undo_cache_timeout_seconds(self) -> int:
        """Timeout in seconds for the undo cache. Non-negative. 0 means no timeout."""
        value = self.get_int_setting('undo_cache_timeout_seconds', 300)
        if value < 0:
            logger.warning(f"Invalid negative value '{value}' for 'undo_cache_timeout_seconds'. Using default 300.")
            return 300
        return value

    @undo_cache_timeout_seconds.setter
    def undo_cache_timeout_seconds(self, value: int):
        if value < 0:
            logger.warning(f"Attempted to set invalid negative value '{value}' for 'undo_cache_timeout_seconds'. Setting to 0 instead.")
            self.set_setting('undo_cache_timeout_seconds', '0')
        else:
            self.set_setting('undo_cache_timeout_seconds', str(value))

    @property
    def log_level(self) -> str:
        """Nivel de logging de la aplicación (DEBUG, INFO, WARNING, ERROR)."""
        value = self.get_setting('log_level', 'WARNING').upper() # Default to WARNING
        if value not in VALID_LOG_LEVELS: # Use module-level VALID_LOG_LEVELS
            logger.warning(f"Invalid log_level '{value}' in config. Defaulting to 'WARNING'.")
            return 'WARNING' # Default to WARNING
        return value

    @log_level.setter
    def log_level(self, value: str):
        if value.upper() in VALID_LOG_LEVELS: # Use module-level VALID_LOG_LEVELS
            self.set_setting('log_level', value.upper())
        else:
            logger.warning(f"Attempted to set invalid log_level '{value}'. Keeping previous or default.")
            # Optionally set to a default if you want to enforce correction on set
            # self.set_setting('log_level', 'WARNING')


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
