import datetime
import logging
import pathlib
import shutil
import time # Added for cooldown
import zipfile
import json # Added for alias management
from typing import Optional

# Configure logger for this module
logger = logging.getLogger(__name__)

from kineviz.utils.paths import get_application_base_dir # Import the new utility

# AppSettings will be imported locally where needed
_last_automatic_backup_end_time: Optional[datetime.datetime] = None
_last_pre_restore_backup_end_time: Optional[datetime.datetime] = None # For "respaldo" backups

# Constants for backup configuration
BACKUPS_DIR_NAME = "backups"
AUTOMATIC_BACKUPS_SUBDIR = "automatic"
MANUAL_BACKUPS_SUBDIR = "manual"
PRE_RESTORE_BACKUP_SUBDIR = "respaldo" # For backups made before a restore operation
BACKUP_ALIASES_FILENAME = "backup_aliases.json" # General alias file

DB_FILENAME = "kineviz.db"
CONFIG_FILENAME = "config.ini"
STUDIES_DIR_NAME = "estudios"

SUPPORTED_BACKUP_TYPES = [AUTOMATIC_BACKUPS_SUBDIR, MANUAL_BACKUPS_SUBDIR, PRE_RESTORE_BACKUP_SUBDIR]


def get_project_root() -> pathlib.Path:
    """
    Determines the project root directory.
    Assumes this file is located in kineviz/core/backup_manager.py
    The project root is three levels up from this file's directory.
    """
    # This function remains the same, get_project_root() is removed.
    # The caller will now pass paths derived from get_application_base_dir().


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


def create_backup(backup_type: str, _is_test_mode: bool = False) -> Optional[pathlib.Path]:
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
    from kineviz.config.settings import AppSettings # Import AppSettings locally
    global _last_automatic_backup_end_time, _last_pre_restore_backup_end_time # Needed for backup logic

    settings = AppSettings() # Load settings at the beginning

    if backup_type not in SUPPORTED_BACKUP_TYPES:
        logger.error(f"Invalid backup_type: '{backup_type}'. Must be one of {SUPPORTED_BACKUP_TYPES}.")
        return None

    app_base_dir = get_application_base_dir() # Use new utility
    backup_destination_base_dir = app_base_dir / BACKUPS_DIR_NAME # Path relative to app base
    backup_destination_subdir = backup_destination_base_dir / backup_type

    if not _ensure_dir_exists(backup_destination_subdir):
        return None

    # Manage rolling backups, cooldown, and locking for automatic backups
    if backup_type == AUTOMATIC_BACKUPS_SUBDIR and not _is_test_mode:
        if not settings.enable_automatic_backups:
            logger.info("Automatic backups are disabled in settings. Skipping automatic backup creation.")
            return None
        try:
            # settings = AppSettings() # Already loaded
            max_auto_backups = settings.max_automatic_backups
            cooldown_seconds = settings.automatic_backup_cooldown_seconds
            
            lock_file_path = backup_destination_subdir / ".backup_in_progress.lock"

            # 1. Check for lock file (another backup in progress)
            if lock_file_path.exists():
                logger.info(f"Automatic backup skipped: another backup operation is currently in progress (lock file found: {lock_file_path}).")
                return None

            # 2. Check cooldown period
            if _last_automatic_backup_end_time:
                seconds_since_last_backup = (datetime.datetime.now() - _last_automatic_backup_end_time).total_seconds()
                if seconds_since_last_backup < cooldown_seconds:
                    logger.info(f"Automatic backup skipped: cooldown period active. {int(seconds_since_last_backup)}s since last backup (cooldown: {cooldown_seconds}s).")
                    return None
            
            # 3. Create lock file and proceed with backup logic
            try:
                lock_file_path.touch() # Create the lock file

                # Rolling backup logic (existing)
                existing_backups = sorted(
                    [f for f in backup_destination_subdir.glob("backup_*.zip") if f.is_file()],
                key=lambda f: f.name
            )
            
                # This logic needs to be inside the try block
                num_existing = len(existing_backups)
                if num_existing >= max_auto_backups and max_auto_backups > 0: # Use max_auto_backups
                    num_to_delete = num_existing - max_auto_backups + 1
                    for i in range(num_to_delete):
                        old_backup = existing_backups[i]
                        logger.info(f"Max automatic backups ({max_auto_backups}) reached. Deleting oldest: {old_backup.name}")
                        old_backup.unlink()
                elif max_auto_backups == 0: # If max_auto_backups is 0, delete all existing automatic backups
                    logger.info("max_automatic_backups is 0. Deleting all existing automatic backups.")
                    for old_backup in existing_backups:
                        old_backup.unlink()
                # End of original rolling backup logic block
            
            except Exception as e: # Catch errors from rolling backup logic or lock file creation
                logger.error(f"Error during pre-backup management (rolling/locking) for automatic backup: {e}", exc_info=True)
                if lock_file_path.exists(): # Clean up lock file if created
                    lock_file_path.unlink()
                return None # Do not proceed if pre-backup management fails
            # If we proceed beyond this point, the lock file exists.
            # The main backup creation will be wrapped in try/finally to remove the lock.

        except Exception as e: # This outer except is for AppSettings or initial checks
            logger.error(f"Error during initial setup for automatic backup: {e}", exc_info=True)
            # Decide if we should proceed with backup creation or not. For now, we'll proceed.
            # However, if lock file logic is above, this might be redundant or need restructuring.
            # For now, assuming this is for settings load error, and we might still attempt backup without cooldown/rolling.
            # Corrected: The logic above now returns None on error, so this block might not be hit often with that intent.
            # This 'except' is for the AppSettings loading or initial cooldown_seconds/lock_file_path setup.
            # If these fail, we might not be able to enforce lock/cooldown, so log and continue cautiously or abort.
            # Given the structure, if AppSettings fails, cooldown_seconds might not be set.
            # Let's assume if settings fail, we skip the backup to be safe.
            logger.error(f"Critical error setting up automatic backup parameters (AppSettings or paths): {e}. Aborting backup.", exc_info=True)
            return None

    elif backup_type == PRE_RESTORE_BACKUP_SUBDIR and not _is_test_mode:
        # Logic for "respaldo" (pre-restore) backups
        if not settings.get_bool_setting('enable_pre_restore_backups', True): # Default True
            logger.info("Pre-restore backups ('respaldo') are disabled in settings. Skipping creation.")
            return None
        try:
            max_pre_restore_backups = settings.get_int_setting('max_pre_restore_backups', 10) # Default 10
            cooldown_seconds = settings.get_int_setting('pre_restore_backup_cooldown_seconds', 60) # Default 60
            
            lock_file_path = backup_destination_subdir / ".pre_restore_backup.lock"

            if lock_file_path.exists():
                logger.info(f"Pre-restore backup skipped: another pre-restore backup operation is currently in progress (lock file found: {lock_file_path}).")
                return None

            if _last_pre_restore_backup_end_time:
                seconds_since_last_backup = (datetime.datetime.now() - _last_pre_restore_backup_end_time).total_seconds()
                if seconds_since_last_backup < cooldown_seconds:
                    logger.info(f"Pre-restore backup skipped: cooldown period active. {int(seconds_since_last_backup)}s since last backup (cooldown: {cooldown_seconds}s).")
                    return None
            
            try:
                lock_file_path.touch()
                existing_backups = sorted(
                    [f for f in backup_destination_subdir.glob("backup_*.zip") if f.is_file()],
                    key=lambda f: f.name
                )
                num_existing = len(existing_backups)
                if max_pre_restore_backups > 0 and num_existing >= max_pre_restore_backups:
                    num_to_delete = num_existing - max_pre_restore_backups + 1
                    for i in range(num_to_delete):
                        old_backup = existing_backups[i]
                        logger.info(f"Max pre-restore backups ({max_pre_restore_backups}) reached. Deleting oldest: {old_backup.name}")
                        remove_backup_alias(PRE_RESTORE_BACKUP_SUBDIR, old_backup.name) # Remove alias if exists
                        old_backup.unlink()
                elif max_pre_restore_backups == 0: # Effectively disables creation if set to 0 after some exist
                    logger.info("max_pre_restore_backups is 0. Deleting all existing pre-restore backups.")
                    for old_backup in existing_backups:
                        remove_backup_alias(PRE_RESTORE_BACKUP_SUBDIR, old_backup.name) # Remove alias if exists
                        old_backup.unlink()
            except Exception as e:
                logger.error(f"Error during pre-backup management for pre-restore backup: {e}", exc_info=True)
                if lock_file_path.exists():
                    lock_file_path.unlink()
                return None
        except Exception as e:
            logger.error(f"Critical error setting up pre-restore backup parameters: {e}. Aborting backup.", exc_info=True)
            return None
            
    elif backup_type == MANUAL_BACKUPS_SUBDIR:
        if not settings.enable_manual_backups: # Check if manual backups are enabled
            logger.info("Manual backups are disabled in settings. Skipping manual backup creation.")
            # UI should ideally prevent calling this, but double check here.
            return None
        try:
            # settings = AppSettings() # Already loaded
            max_manual_bkups = settings.max_manual_backups
            
            existing_manual_backups = sorted(
                [f for f in backup_destination_subdir.glob("backup_*.zip") if f.is_file()],
                key=lambda f: f.name # Sort by name (timestamp)
            )
            num_existing_manual = len(existing_manual_backups)

            if max_manual_bkups > 0 and num_existing_manual >= max_manual_bkups:
                logger.warning(f"Cannot create new manual backup. Limit of {max_manual_bkups} reached. User must delete an existing manual backup.")
                # This message should ideally be shown to the user via the UI.
                # For now, the function will return None, and the UI should handle this.
                # We can raise a specific exception here if the UI is prepared to catch it.
                # For simplicity, returning None and relying on UI to check is okay for now.
                # The UI (BackupRestoreDialog) will need to inform the user.
                return None # Signal to UI that backup was not created due to limit.
            elif max_manual_bkups == 0: # If limit is 0, effectively "disabled" but also means "delete all existing if any are found"
                                        # The original code deleted all if max_manual_bkups == 0.
                                        # New behavior: if max_manual_bkups is 0, no manual backups can be created.
                logger.info("Manual backups are disabled (max_manual_backups is 0). Cannot create new manual backup.")
                return None # Signal to UI

            # Original logic for deleting all if max_manual_bkups == 0 (when creating a new one)
            # This part is now changed. If max_manual_bkups is 0, creation is disallowed above.
            # If max_manual_bkups was > 0 but then set to 0, existing backups are not touched by *this* function.
            # Deletion of all when max_manual_backups is set to 0 should be handled by ConfigDialog/AppSettings setter if desired.
            # For now, this function only respects the limit for *new* creations.

            # Old code for deleting all if max_manual_bkups == 0:
            # elif max_manual_bkups == 0: # Delete all if max is 0
            #     logger.info("max_manual_backups is 0. Deleting all existing manual backups.")
            #     aliases = _load_manual_backup_aliases()
            # ... (rest of deletion logic) ...
            # This behavior is removed from here.

        except Exception as e:
            logger.error(f"Error during pre-check for manual backup creation: {e}", exc_info=True)
            return None # Do not proceed if pre-check fails
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"backup_{timestamp}.zip"
    zip_filepath = backup_destination_subdir / zip_filename

    # app_base_dir is already defined if control reaches here from the previous change.
    # If not, it should be fetched: app_base_dir = get_application_base_dir()
    # Assuming app_base_dir is in scope from the earlier modification in this function.
    app_base_dir = get_application_base_dir() # Ensure it's available

    db_file_path = app_base_dir / DB_FILENAME
    config_file_path = app_base_dir / CONFIG_FILENAME
    studies_dir_path = app_base_dir / STUDIES_DIR_NAME

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

    # Determine lock_file_path again for the finally block, specific to automatic backups
    # This is a bit redundant but ensures the finally block has the correct path if it's an automatic backup.
    # A better way would be to pass lock_file_path if it was created.
    # For now, re-evaluate:
    current_lock_file_for_finally = None
    if backup_type == AUTOMATIC_BACKUPS_SUBDIR and not _is_test_mode:
        current_lock_file_for_finally = backup_destination_subdir / ".backup_in_progress.lock"
    elif backup_type == PRE_RESTORE_BACKUP_SUBDIR and not _is_test_mode:
        current_lock_file_for_finally = backup_destination_subdir / ".pre_restore_backup.lock"

    try:
        logger.info(f"Creating backup: {zip_filepath} (Type: {backup_type}, Test Mode: {_is_test_mode})")
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item_path, arcname in items_to_backup:
                logger.debug(f"Adding file to backup: {item_path} as {arcname}")
                zf.write(item_path, arcname=arcname)

            if studies_dir_path.exists() and studies_dir_path.is_dir():
                logger.debug(f"Selectively adding files from studies directory: {studies_dir_path}")
                
                for study_name_dir in studies_dir_path.iterdir():
                    if not study_name_dir.is_dir():
                        continue # Skip files directly under studies_dir_path, looking for study folders
                    
                    # Add the study directory itself to the archive
                    # This ensures empty study folders are backed up.
                    # app_base_dir should be in scope
                    study_relative_path = study_name_dir.relative_to(app_base_dir)
                    zf.write(study_name_dir, arcname=study_relative_path) # Add the directory entry
                    logger.debug(f"Adding study directory to backup: {study_name_dir} as {study_relative_path}")

                    # Path: estudios/[NOMBRE_ESTUDIO]
                    
                    # 1. Participant data files (Originals and Processed)
                    for participant_dir in study_name_dir.iterdir():
                        if not participant_dir.is_dir():
                            # If there are files directly under study_name_dir, they are not per current structure.
                            # We only back up recognized structure.
                            continue # Skip files, looking for participant folders (e.g., [ID_PARTICIPANTE])

                        # Path: estudios/[NOMBRE_ESTUDIO]/[ID_PARTICIPANTE]
                        
                        # Original files: .../[ID_PARTICIPANTE]/OG/*.txt or *.csv
                        og_dir = participant_dir / "OG"
                        if og_dir.is_dir():
                            for ext in ["*.txt", "*.csv"]:
                                for file_path in og_dir.glob(ext):
                                    if file_path.is_file():
                                        relative_path = file_path.relative_to(app_base_dir) # Use app_base_dir
                                        logger.debug(f"Adding original data file: {file_path} as {relative_path}")
                                        zf.write(file_path, arcname=relative_path)
                        
                        # Processed files: .../[ID_PARTICIPANTE]/[TIPO_DATO]/*.txt
                        for data_type_dir in participant_dir.iterdir():
                            if data_type_dir.is_dir() and data_type_dir.name != "OG":
                                # Path: estudios/[NOMBRE_ESTUDIO]/[ID_PARTICIPANTE]/[TIPO_DATO]
                                for file_path in data_type_dir.glob("*.txt"):
                                    if file_path.is_file():
                                        relative_path = file_path.relative_to(app_base_dir) # Use app_base_dir
                                        logger.debug(f"Adding processed data file: {file_path} as {relative_path}")
                                        zf.write(file_path, arcname=relative_path)

                    # 2. Resultados de Análisis Discreto
                    discrete_analysis_dir = study_name_dir / "Analisis Discreto"
                    if discrete_analysis_dir.is_dir():
                        # Tablas: .../Analisis Discreto/Tablas/[TIPO_DATO]/*.xlsx or *.csv
                        tables_dir = discrete_analysis_dir / "Tablas"
                        if tables_dir.is_dir():
                            for data_type_sub_dir in tables_dir.iterdir(): # [TIPO_DATO]
                                if data_type_sub_dir.is_dir():
                                    for ext in ["*.xlsx", "*.csv"]:
                                        for file_path in data_type_sub_dir.glob(ext):
                                            if file_path.is_file():
                                                relative_path = file_path.relative_to(app_base_dir) # Use app_base_dir
                                                logger.debug(f"Adding discrete analysis table: {file_path} as {relative_path}")
                                                zf.write(file_path, arcname=relative_path)
                        # Graficos/Config: .../Analisis Discreto/Graficos/[COLUMNA_ANALIZADA]/[NOMBRE_ANALISIS]/ (contenido relevante)
                        graphics_dir = discrete_analysis_dir / "Graficos"
                        if graphics_dir.is_dir():
                            for column_analyzed_dir in graphics_dir.iterdir(): # [COLUMNA_ANALIZADA]
                                if column_analyzed_dir.is_dir():
                                    for analysis_name_dir in column_analyzed_dir.iterdir(): # [NOMBRE_ANALISIS]
                                        if analysis_name_dir.is_dir():
                                            for file_path in analysis_name_dir.rglob('*'):
                                                if file_path.is_file():
                                                    relative_path = file_path.relative_to(app_base_dir) # Use app_base_dir
                                                    logger.debug(f"Adding discrete analysis graphic/config: {file_path} as {relative_path}")
                                                    zf.write(file_path, arcname=relative_path)
                                                    
                    # 3. Resultados de Análisis Continuo
                    #    .../Analisis Continuo/[COLUMNA_ANALIZADA]/[NOMBRE_ANALISIS]/ (contenido relevante)
                    continuous_analysis_dir = study_name_dir / "Analisis Continuo"
                    if continuous_analysis_dir.is_dir():
                        for column_analyzed_dir in continuous_analysis_dir.iterdir(): # [COLUMNA_ANALIZADA]
                            if column_analyzed_dir.is_dir():
                                for analysis_name_dir in column_analyzed_dir.iterdir(): # [NOMBRE_ANALISIS]
                                    if analysis_name_dir.is_dir():
                                        for file_path in analysis_name_dir.rglob('*'):
                                            if file_path.is_file():
                                                relative_path = file_path.relative_to(app_base_dir) # Use app_base_dir
                                                logger.debug(f"Adding continuous analysis file: {file_path} as {relative_path}")
                                                zf.write(file_path, arcname=relative_path)
            elif studies_dir_path.exists(): # It exists but is not a directory
                 logger.warning(f"Studies path {studies_dir_path} exists but is not a directory. It will not be included in the backup.")
            else: # It does not exist
                logger.warning(f"Studies directory {studies_dir_path} not found. It will not be included in the backup.")


        logger.info(f"Backup created successfully: {zip_filepath}")
        if backup_type == AUTOMATIC_BACKUPS_SUBDIR and not _is_test_mode:
            _last_automatic_backup_end_time = datetime.datetime.now()
            logger.debug(f"Updated _last_automatic_backup_end_time to {_last_automatic_backup_end_time}")
        elif backup_type == PRE_RESTORE_BACKUP_SUBDIR and not _is_test_mode:
            _last_pre_restore_backup_end_time = datetime.datetime.now()
            logger.debug(f"Updated _last_pre_restore_backup_end_time to {_last_pre_restore_backup_end_time}")
        return zip_filepath
    except Exception as e:
        logger.error(f"Failed to create backup {zip_filepath} (Type: {backup_type}, Test Mode: {_is_test_mode}): {e}", exc_info=True)
        if zip_filepath.exists():
            try:
                zip_filepath.unlink() # Attempt to clean up partially created zip
            except OSError as ose:
                logger.error(f"Failed to delete partial backup file {zip_filepath}: {ose}")
        return None
    finally:
        if current_lock_file_for_finally and current_lock_file_for_finally.exists():
            try:
                current_lock_file_for_finally.unlink()
                logger.debug(f"Lock file {current_lock_file_for_finally} removed.")
            except OSError as ose:
                logger.error(f"Failed to remove lock file {current_lock_file_for_finally}: {ose}")

# --- Alias Management for Backups ---

def _get_backup_aliases_path() -> pathlib.Path:
    """Returns the path to the backup aliases JSON file."""
    # Aliases file stored directly in the main backups directory
    app_base_dir = get_application_base_dir()
    return app_base_dir / BACKUPS_DIR_NAME / BACKUP_ALIASES_FILENAME

def _load_backup_aliases() -> dict:
    """Loads backup aliases from the JSON file."""
    aliases_path = _get_backup_aliases_path()
    if aliases_path.exists():
        try:
            with open(aliases_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading backup aliases from {aliases_path}: {e}", exc_info=True)
    return {}

def _save_backup_aliases(aliases_data: dict):
    """Saves backup aliases to the JSON file."""
    aliases_path = _get_backup_aliases_path()
    try:
        aliases_path.parent.mkdir(parents=True, exist_ok=True) # Ensure main backups dir exists
        with open(aliases_path, 'w', encoding='utf-8') as f:
            json.dump(aliases_data, f, indent=4)
        logger.info(f"Backup aliases saved to {aliases_path}")
    except OSError as e:
        logger.error(f"Error saving backup aliases to {aliases_path}: {e}", exc_info=True)

def add_backup_alias(backup_type_subdir: str, backup_filename: str, alias: str) -> bool:
    """Adds or updates an alias for a backup file (manual or automatic)."""
    if not backup_filename.startswith("backup_") or not backup_filename.endswith(".zip"):
        logger.error(f"Invalid backup filename format for alias: {backup_filename}")
        return False
    if not alias.strip():
        logger.error("Alias cannot be empty or just whitespace.")
        return False
    
    # Key in JSON will be "automatic/backup_file.zip" or "manual/backup_file.zip"
    alias_key = f"{backup_type_subdir}/{backup_filename}"
        
    aliases = _load_backup_aliases()
    aliases[alias_key] = alias.strip()
    _save_backup_aliases(aliases)
    logger.info(f"Alias for '{alias_key}' set to '{alias.strip()}'.")
    return True

def remove_backup_alias(backup_type_subdir: str, backup_filename: str) -> bool:
    """Removes an alias for a backup file."""
    alias_key = f"{backup_type_subdir}/{backup_filename}"
    aliases = _load_backup_aliases()
    if alias_key in aliases:
        del aliases[alias_key]
        _save_backup_aliases(aliases)
        logger.info(f"Alias for '{alias_key}' removed.")
        return True
    logger.warning(f"No alias found for '{alias_key}' to remove.")
    return False

def delete_manual_backup(backup_filename: str) -> bool:
    """Deletes a specific manual backup file and its alias."""
    app_base_dir = get_application_base_dir()
    backup_file_path = app_base_dir / BACKUPS_DIR_NAME / MANUAL_BACKUPS_SUBDIR / backup_filename
    if not backup_file_path.exists() or not backup_file_path.is_file():
        logger.error(f"Manual backup file not found: {backup_file_path}")
        return False
    try:
        backup_file_path.unlink()
        logger.info(f"Manual backup file deleted: {backup_file_path}")
        remove_backup_alias(MANUAL_BACKUPS_SUBDIR, backup_filename) # Attempt to remove alias
        return True
    except OSError as e:
        logger.error(f"Error deleting manual backup file {backup_file_path}: {e}", exc_info=True)
        return False

def cleanup_bak_files() -> tuple[int, int]:
    """
    Deletes all .bak files and directories from the project root.
    These are typically created during restore operations.
    Returns: (deleted_count, error_count)
    """
    app_base_dir = get_application_base_dir()
    deleted_count = 0
    error_count = 0
    logger.info(f"Iniciando limpieza de archivos/carpetas .bak en: {app_base_dir}")

    for item in app_base_dir.glob("*.bak"):
        try:
            if item.is_file():
                item.unlink()
                logger.info(f"Archivo .bak eliminado: {item}")
                deleted_count += 1
            elif item.is_dir():
                shutil.rmtree(item)
                logger.info(f"Carpeta .bak eliminada: {item}")
                deleted_count += 1
        except OSError as e:
            logger.error(f"Error eliminando {item}: {e}")
            error_count += 1
    
    logger.info(f"Limpieza de .bak completada. Eliminados: {deleted_count}, Errores: {error_count}")
    return deleted_count, error_count

# --- Listing Backups ---

def list_backups() -> list[dict]:
    """
    Lists all available backups, both automatic and manual.
    Returns a list of dictionaries, each representing a backup.
    """
    all_backups = []
    app_base_dir = get_application_base_dir()
    backup_base_dir = app_base_dir / BACKUPS_DIR_NAME

    # Load all aliases (manual and automatic)
    all_backup_aliases = _load_backup_aliases()

    for backup_type_subdir_name in SUPPORTED_BACKUP_TYPES:
        backup_type_path = backup_base_dir / backup_type_subdir_name
        if backup_type_path.exists() and backup_type_path.is_dir():
            for item in backup_type_path.glob("backup_*.zip"):
                if item.is_file():
                    try:
                        # Extract timestamp from filename backup_YYYYMMDD_HHMMSS.zip
                        # Corrected timestamp parsing:
                        # item.stem is "backup_YYYYMMDD_HHMMSS"
                        # remove "backup_" prefix
                        ts_str_from_stem = item.stem.replace("backup_", "", 1)
                        timestamp_dt = datetime.datetime.strptime(ts_str_from_stem, "%Y%m%d_%H%M%S")
                        
                        # Construct the key used in backup_aliases.json
                        alias_key = f"{backup_type_subdir_name}/{item.name}"
                        alias = all_backup_aliases.get(alias_key)

                        all_backups.append({
                            "type": backup_type_subdir_name,
                            "path": item,
                            "filename": item.name,
                            "timestamp": timestamp_dt,
                            "alias": alias
                        })
                    except (IndexError, ValueError) as e:
                        logger.warning(f"Could not parse timestamp from backup filename '{item.name}': {e}")
                        # Add with a None timestamp or skip? For now, skip.
                        continue
    
    # Sort by timestamp, most recent first
    all_backups.sort(key=lambda b: b["timestamp"], reverse=True)
    return all_backups


def restore_backup(backup_zip_path: pathlib.Path) -> bool:
    """
    Restores the system state from a given backup ZIP file.
    This involves replacing kineviz.db, config.ini, and the estudios/ directory.
    """
    app_base_dir = get_application_base_dir()
    if not backup_zip_path.exists() or not backup_zip_path.is_file():
        logger.error(f"Backup file not found: {backup_zip_path}")
        return False

    temp_extract_dir = app_base_dir / f"temp_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}" # Temp dir in app base
    
    live_db_path = app_base_dir / DB_FILENAME
    live_config_path = app_base_dir / CONFIG_FILENAME
    live_studies_dir = app_base_dir / STUDIES_DIR_NAME

    # Paths for backed-up (renamed) live items
    bak_db_path = app_base_dir / f"{DB_FILENAME}.{timestamp_str()}.bak"
    bak_config_path = app_base_dir / f"{CONFIG_FILENAME}.{timestamp_str()}.bak"
    bak_studies_dir = app_base_dir / f"{STUDIES_DIR_NAME}.{timestamp_str()}.bak"

    try:
        logger.info(f"Starting restoration from backup: {backup_zip_path}")
        _ensure_dir_exists(temp_extract_dir)

        # 1. Extract backup to temporary directory
        logger.info(f"Extracting backup to {temp_extract_dir}...")
        with zipfile.ZipFile(backup_zip_path, 'r') as zf:
            zf.extractall(temp_extract_dir)
        logger.info("Backup extracted successfully.")

        extracted_db_path = temp_extract_dir / DB_FILENAME
        extracted_config_path = temp_extract_dir / CONFIG_FILENAME
        extracted_studies_dir = temp_extract_dir / STUDIES_DIR_NAME

        # 2. Rename current live items (if they exist)
        logger.info("Renaming current live items...")
        if live_db_path.exists():
            live_db_path.rename(bak_db_path)
            logger.info(f"Renamed live DB to {bak_db_path}")
        if live_config_path.exists():
            live_config_path.rename(bak_config_path)
            logger.info(f"Renamed live config to {bak_config_path}")
        if live_studies_dir.exists() and live_studies_dir.is_dir():
            shutil.move(str(live_studies_dir), str(bak_studies_dir)) # shutil.move can rename dirs
            logger.info(f"Moved live studies dir to {bak_studies_dir}")

        # 3. Move extracted items to live locations
        logger.info("Moving extracted items to live locations...")
        if extracted_db_path.exists():
            shutil.move(str(extracted_db_path), str(live_db_path))
            logger.info(f"Restored DB from {extracted_db_path}")
        else:
            logger.warning(f"No database file found in backup archive at {extracted_db_path}. DB not restored.")

        if extracted_config_path.exists():
            shutil.move(str(extracted_config_path), str(live_config_path))
            logger.info(f"Restored config from {extracted_config_path}")
        else:
            logger.warning(f"No config file found in backup archive at {extracted_config_path}. Config not restored.")

        if extracted_studies_dir.exists() and extracted_studies_dir.is_dir():
            shutil.move(str(extracted_studies_dir), str(live_studies_dir))
            logger.info(f"Restored studies directory from {extracted_studies_dir}")
        elif extracted_studies_dir.exists(): # It's a file, not a dir - problematic
            logger.error(f"Extracted studies path {extracted_studies_dir} is a file, not a directory. Studies not restored.")
        else:
            logger.warning(f"No studies directory found in backup archive at {extracted_studies_dir}. Studies not restored.")
            # Ensure studies directory exists even if not in backup (e.g., for a fresh restore)
            _ensure_dir_exists(live_studies_dir)

        # If restoration reached this point, it's considered successful. Clean up .bak files.
        logger.info("Restoration successful. Cleaning up .bak files...")
        if bak_db_path.exists(): bak_db_path.unlink(missing_ok=True)
        if bak_config_path.exists(): bak_config_path.unlink(missing_ok=True)
        if bak_studies_dir.exists(): shutil.rmtree(bak_studies_dir, ignore_errors=True)
        logger.info(".bak files cleaned up.")

        logger.info("Restoration process completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Error during backup restoration: {e}", exc_info=True)
        # Attempt to rollback renames if something went wrong
        logger.info("Attempting to rollback renames due to restoration error...")
        try:
            if bak_db_path.exists() and not live_db_path.exists(): # If live was deleted/moved and bak exists
                bak_db_path.rename(live_db_path)
                logger.info(f"Rolled back DB: {bak_db_path} -> {live_db_path}")
            if bak_config_path.exists() and not live_config_path.exists():
                bak_config_path.rename(live_config_path)
                logger.info(f"Rolled back config: {bak_config_path} -> {live_config_path}")
            if bak_studies_dir.exists() and not live_studies_dir.exists():
                shutil.move(str(bak_studies_dir), str(live_studies_dir))
                logger.info(f"Rolled back studies dir: {bak_studies_dir} -> {live_studies_dir}")
        except Exception as rollback_e:
            logger.error(f"Error during rollback of renames: {rollback_e}", exc_info=True)
        return False
    finally:
        # 4. Clean up temporary extraction directory
        if temp_extract_dir.exists():
            try:
                shutil.rmtree(temp_extract_dir)
                logger.info(f"Cleaned up temporary extraction directory: {temp_extract_dir}")
            except OSError as e:
                logger.error(f"Error cleaning up temp directory {temp_extract_dir}: {e}")

def timestamp_str() -> str:
    """Generates a simple timestamp string for backup file suffixes."""
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

if __name__ == '__main__':
    # DB_FILENAME and CONFIG_FILENAME are module-level globals.
    # The 'global' keyword is not needed here and was causing a SyntaxError.
    # Assignments within this block will directly modify the module-level variables.

    import sys # For sys.path modification
    # shutil is already imported at the top if needed for cleanup

    # Example usage (for testing purposes)
    # Ensure logger is configured to see output
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Adjust sys.path to allow finding the 'kineviz' package for AppSettings
    # The new `get_application_base_dir` handles dev vs bundled path.
    app_base_dir_for_test = get_application_base_dir()
    if str(app_base_dir_for_test) not in sys.path: # For dev, this adds project root
        sys.path.insert(0, str(app_base_dir_for_test))

    from kineviz.config.settings import AppSettings # Import AppSettings locally for the test block
    
    # --- Test specific constants ---
    TEST_DB_FILENAME = "dummy_test_kineviz.db"
    TEST_CONFIG_FILENAME = "dummy_test_config.ini"
    # We will still use the real STUDIES_DIR_NAME for testing the studies backup part,
    # but the DB and Config will be dummies.
    
    # Create dummy files and directories for testing
    # app_base_dir_for_test is already defined above
    (app_base_dir_for_test / TEST_DB_FILENAME).write_text("dummy db content for testing")
    
    # Create a more complete dummy config.ini for testing
    default_settings_for_test = AppSettings.DEFAULT_SETTINGS['SETTINGS']
    config_content_for_test = "[SETTINGS]\n"
    for key, value in default_settings_for_test.items():
        config_content_for_test += f"{key} = {value}\n"
    # Override specific values for test if needed, e.g., max_automatic_backups for the test logic
    config_content_for_test += "dummy_test_specific_setting = True\n" # Example if needed
    (app_base_dir_for_test / TEST_CONFIG_FILENAME).write_text(config_content_for_test)
        
    # Temporarily override global constants for the scope of this test
    # The 'global DB_FILENAME, CONFIG_FILENAME' declaration was moved to the top 
    # of the 'if __name__ == "__main__":' block.
    original_db_filename, original_config_filename = DB_FILENAME, CONFIG_FILENAME
    DB_FILENAME, CONFIG_FILENAME = TEST_DB_FILENAME, TEST_CONFIG_FILENAME
    
    dummy_studies_dir = app_base_dir_for_test / STUDIES_DIR_NAME # This will be the actual studies dir name
    dummy_studies_dir.mkdir(exist_ok=True)
    (dummy_studies_dir / "study1").mkdir(exist_ok=True)
    (dummy_studies_dir / "study1" / "data.txt").write_text("study1 data")
    (dummy_studies_dir / "study2").mkdir(exist_ok=True)
    (dummy_studies_dir / "study2" / "report.pdf").write_text("study2 report")
    (dummy_studies_dir / "empty_study").mkdir(exist_ok=True)


    logger.info(f"Application base directory for test: {app_base_dir_for_test}")
    
    # Test automatic backup
    logger.info("Attempting to create an automatic backup...")
    # Create a few automatic backups to test rolling
    app_settings = AppSettings()
    max_auto = app_settings.max_automatic_backups
    logger.info(f"Max automatic backups configured: {max_auto}")

    if max_auto > 0:
        for i in range(max_auto + 2): # Create more than max to test deletion
            logger.info(f"Creating automatic backup {i+1} (test mode)...")
            # Pass _is_test_mode=True to bypass cooldown/lock for testing rolling logic
            auto_backup_path = create_backup(AUTOMATIC_BACKUPS_SUBDIR, _is_test_mode=True) 
            if auto_backup_path:
                logger.info(f"Automatic backup {i+1} created at: {auto_backup_path.name}")
                # Introduce a small delay to ensure distinct timestamps if runs too fast
                if i < max_auto + 1: # Not for the last one
                    # import time # time is already imported at the top of the module
                    time.sleep(0.1) # Shorter sleep for faster tests, still ensuring timestamp difference
            else:
                logger.error(f"Automatic backup {i+1} (test mode) creation failed.")
    else:
        logger.info("Skipping automatic backup creation test as max_automatic_backups is 0 or less.")
        # Test if existing backups are deleted if max_auto is 0
        # Create one first then try to create another
        logger.info("Creating one auto backup then testing deletion with max_auto = 0")
        # Temporarily create a backup file to test deletion when max_auto is 0
        temp_backup_dir = app_base_dir_for_test / BACKUPS_DIR_NAME / AUTOMATIC_BACKUPS_SUBDIR
        _ensure_dir_exists(temp_backup_dir)
        (temp_backup_dir / "backup_20000101_000000.zip").write_text("temp")
        
        # Pass _is_test_mode=True to bypass cooldown/lock for testing rolling logic
        auto_backup_path = create_backup(AUTOMATIC_BACKUPS_SUBDIR, _is_test_mode=True) 
        if not (temp_backup_dir / "backup_20000101_000000.zip").exists():
            logger.info("Temp auto backup was correctly deleted when max_auto is 0 (test mode).")
        else:
            logger.warning("Temp auto backup was NOT deleted when max_auto is 0 (test mode).")


    # Test manual backup
    logger.info("Attempting to create a manual backup...")
    manual_backup_path = create_backup(MANUAL_BACKUPS_SUBDIR) # Manual backups don't have cooldown/lock
    if manual_backup_path:
        logger.info(f"Manual backup created at: {manual_backup_path}")
    else:
        logger.error("Manual backup creation failed.")

    # Test invalid backup type
    logger.info("Attempting to create a backup with invalid type...")
    invalid_backup_path = create_backup("invalid_type")
    if not invalid_backup_path:
        logger.info("Backup creation with invalid type correctly failed.")

    # --- Clean up dummy files and directories used for testing ---
    logger.info("Cleaning up test-specific dummy files...")
    (app_base_dir_for_test / TEST_DB_FILENAME).unlink(missing_ok=True)
    (app_base_dir_for_test / TEST_CONFIG_FILENAME).unlink(missing_ok=True)
    
    # Restore original global constants
    DB_FILENAME, CONFIG_FILENAME = original_db_filename, original_config_filename
    
    # Note: dummy_studies_dir and its contents are NOT automatically cleaned up here
    # to allow inspection of its structure if needed after a test run.
    # The backup files created in kineviz/backups/ are also not cleaned up automatically.
    logger.info(f"Test cleanup complete. Dummy DB ({TEST_DB_FILENAME}) and Config ({TEST_CONFIG_FILENAME}) removed.")
    logger.info(f"Please manually clean up the '{BACKUPS_DIR_NAME}' directory and '{STUDIES_DIR_NAME}' if it was created/modified by this test script.")
