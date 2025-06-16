import datetime
import logging
import pathlib
import shutil
import zipfile
from typing import Optional

# Configure logger for this module
logger = logging.getLogger(__name__)

# Constants for backup configuration
BACKUPS_DIR_NAME = "backups"
AUTOMATIC_BACKUPS_SUBDIR = "automatic"
MANUAL_BACKUPS_SUBDIR = "manuales"

DB_FILENAME = "kineviz.db"
CONFIG_FILENAME = "config.ini"
STUDIES_DIR_NAME = "estudios"

SUPPORTED_BACKUP_TYPES = [AUTOMATIC_BACKUPS_SUBDIR, MANUAL_BACKUPS_SUBDIR]


def get_project_root() -> pathlib.Path:
    """
    Determines the project root directory.
    Assumes this file is located in kineviz/core/backup_manager.py
    The project root is three levels up from this file's directory.
    """
    return pathlib.Path(__file__).resolve().parent.parent.parent


def _ensure_dir_exists(dir_path: pathlib.Path) -> bool:
    """
    Ensures that the specified directory exists. Creates it if it doesn't.
    Returns True if the directory exists or was created, False otherwise.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        logger.error(f"Error creating directory {dir_path}: {e}")
        return False


def create_backup(backup_type: str) -> Optional[pathlib.Path]:
    """
    Creates a full system backup.

    The backup includes:
    - The database file (kineviz.db)
    - The configuration file (config.ini)
    - The entire studies directory (estudios/)

    Backups are stored as timestamped ZIP files in subdirectories
    (automatic/ or manuales/) within the 'backups' directory at the project root.

    Args:
        backup_type: Type of backup. Must be one of SUPPORTED_BACKUP_TYPES.
                     Determines the subdirectory for storing the backup.

    Returns:
        The Path object to the created backup ZIP file, or None if an error occurred.
    """
    if backup_type not in SUPPORTED_BACKUP_TYPES:
        logger.error(f"Invalid backup_type: '{backup_type}'. Must be one of {SUPPORTED_BACKUP_TYPES}.")
        return None

    project_root = get_project_root()
    backup_destination_base_dir = project_root / BACKUPS_DIR_NAME
    backup_destination_subdir = backup_destination_base_dir / backup_type

    if not _ensure_dir_exists(backup_destination_subdir):
        return None

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"backup_{timestamp}.zip"
    zip_filepath = backup_destination_subdir / zip_filename

    db_file_path = project_root / DB_FILENAME
    config_file_path = project_root / CONFIG_FILENAME
    studies_dir_path = project_root / STUDIES_DIR_NAME

    items_to_backup = []
    if db_file_path.exists() and db_file_path.is_file():
        items_to_backup.append((db_file_path, DB_FILENAME))
    else:
        logger.warning(f"Database file {db_file_path} not found. It will not be included in the backup.")

    if config_file_path.exists() and config_file_path.is_file():
        items_to_backup.append((config_file_path, CONFIG_FILENAME))
    else:
        logger.warning(f"Config file {config_file_path} not found. It will not be included in the backup.")

    if not items_to_backup and not (studies_dir_path.exists() and studies_dir_path.is_dir()):
        logger.error("No items found to backup (database, config, or studies directory). Backup aborted.")
        return None

    try:
        logger.info(f"Creating backup: {zip_filepath}")
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item_path, arcname in items_to_backup:
                logger.debug(f"Adding file to backup: {item_path} as {arcname}")
                zf.write(item_path, arcname=arcname)

            if studies_dir_path.exists() and studies_dir_path.is_dir():
                logger.debug(f"Adding directory to backup: {studies_dir_path}")
                for file_path in studies_dir_path.rglob('*'):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(project_root)
                        logger.debug(f"Adding file from studies dir: {file_path} as {relative_path}")
                        zf.write(file_path, arcname=relative_path)
            elif studies_dir_path.exists(): # It exists but is not a directory
                 logger.warning(f"Studies path {studies_dir_path} exists but is not a directory. It will not be included in the backup.")
            else: # It does not exist
                logger.warning(f"Studies directory {studies_dir_path} not found. It will not be included in the backup.")


        logger.info(f"Backup created successfully: {zip_filepath}")
        return zip_filepath
    except Exception as e:
        logger.error(f"Failed to create backup {zip_filepath}: {e}")
        if zip_filepath.exists():
            try:
                zip_filepath.unlink() # Attempt to clean up partially created zip
            except OSError as ose:
                logger.error(f"Failed to delete partial backup file {zip_filepath}: {ose}")
        return None

if __name__ == '__main__':
    # Example usage (for testing purposes)
    # Ensure logger is configured to see output
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create dummy files and directories for testing
    root = get_project_root()
    (root / DB_FILENAME).write_text("dummy db content")
    (root / CONFIG_FILENAME).write_text("[SETTINGS]\ndummy_setting=1")
    
    dummy_studies_dir = root / STUDIES_DIR_NAME
    dummy_studies_dir.mkdir(exist_ok=True)
    (dummy_studies_dir / "study1").mkdir(exist_ok=True)
    (dummy_studies_dir / "study1" / "data.txt").write_text("study1 data")
    (dummy_studies_dir / "study2").mkdir(exist_ok=True)
    (dummy_studies_dir / "study2" / "report.pdf").write_text("study2 report")
    (dummy_studies_dir / "empty_study").mkdir(exist_ok=True)


    logger.info(f"Project root determined as: {root}")
    
    # Test automatic backup
    logger.info("Attempting to create an automatic backup...")
    auto_backup_path = create_backup(AUTOMATIC_BACKUPS_SUBDIR)
    if auto_backup_path:
        logger.info(f"Automatic backup created at: {auto_backup_path}")
    else:
        logger.error("Automatic backup creation failed.")

    # Test manual backup
    logger.info("Attempting to create a manual backup...")
    manual_backup_path = create_backup(MANUAL_BACKUPS_SUBDIR)
    if manual_backup_path:
        logger.info(f"Manual backup created at: {manual_backup_path}")
    else:
        logger.error("Manual backup creation failed.")

    # Test invalid backup type
    logger.info("Attempting to create a backup with invalid type...")
    invalid_backup_path = create_backup("invalid_type")
    if not invalid_backup_path:
        logger.info("Backup creation with invalid type correctly failed.")

    # Clean up dummy files and directories
    # (root / DB_FILENAME).unlink(missing_ok=True)
    # (root / CONFIG_FILENAME).unlink(missing_ok=True)
    # if dummy_studies_dir.exists():
    #     shutil.rmtree(dummy_studies_dir)
    # logger.info("Cleaned up dummy files and directories.")
    # logger.info(f"Please manually clean up the '{BACKUPS_DIR_NAME}' directory created under {root} if needed.")
    # logger.info("To fully test, run this script, check the 'backups' directory, then uncomment cleanup lines and run again.")
