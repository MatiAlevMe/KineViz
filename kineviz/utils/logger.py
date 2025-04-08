import logging
import logging.handlers
from pathlib import Path
import sys

LOG_FILENAME = "kineviz.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

def setup_logging(log_dir_name='logs', log_level=logging.INFO):
    """
    Configura el sistema de logging para la aplicación.

    Crea un directorio de logs si no existe y configura handlers para
    escribir en un archivo rotatorio y opcionalmente en la consola.

    :param log_dir_name: Nombre del directorio donde se guardarán los logs.
    :param log_level: Nivel mínimo de logging (ej. logging.INFO, logging.DEBUG).
    """
    try:
        # Determinar la ruta raíz del proyecto (asumiendo que logger.py está en kineviz/utils)
        project_root = Path(__file__).resolve().parent.parent.parent
        log_dir = project_root / log_dir_name
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / LOG_FILENAME

        # Formato del log
        log_format = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
        formatter = logging.Formatter(log_format)

        # Configuración raíz del logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        # Limpiar handlers existentes para evitar duplicados si se llama varias veces
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Handler para archivo rotatorio
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Handler para consola (opcional, útil para debugging)
        # Podríamos condicionarlo basado en un flag de debug o el nivel
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        # Mostrar solo INFO y superior en consola por defecto
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)

        logging.info(f"Logging configurado. Nivel: {logging.getLevelName(log_level)}. Archivo: {log_file_path}")

    except Exception as e:
        # Fallback a logging básico si la configuración falla
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"Error configurando el logging: {e}", exc_info=True)

# Ejemplo de uso (opcional)
if __name__ == '__main__':
    setup_logging(log_level=logging.DEBUG)
    logging.debug("Mensaje de debug")
    logging.info("Mensaje informativo")
    logging.warning("Mensaje de advertencia")
    logging.error("Mensaje de error")
    try:
        1 / 0
    except ZeroDivisionError:
        logging.exception("Ocurrió una excepción")
