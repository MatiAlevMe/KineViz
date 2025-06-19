import datetime
import logging
import pathlib
import shutil
import json
from typing import Optional, List, Dict, Any

from kineviz.config.settings import AppSettings
from kineviz.utils.paths import get_application_base_dir # Import the new utility

# This should be consistent with StudyRepository and BackupManager
DB_FILENAME = "kineviz.db"

logger = logging.getLogger(__name__)

UNDO_CACHE_SUBDIR = ".undo_cache"  # Inside backups directory as per roadmap
UNDO_INFO_FILENAME = "undo_info.json"


class UndoManager:
    def __init__(self, settings: AppSettings, study_repository_db_path: str):
        self.settings = settings
        self.app_base_dir = get_application_base_dir() # Use the new utility
        self.db_path_live = pathlib.Path(study_repository_db_path) # This path is correctly passed by MainWindow
        self.undo_cache_dir = self.app_base_dir / "backups" / UNDO_CACHE_SUBDIR # Use app_base_dir
        self._ensure_dir_exists(self.undo_cache_dir)

        self.cached_items_info: List[Dict[str, Any]] = []
        self.db_backup_in_cache_path: Optional[pathlib.Path] = None

    # _get_project_root method is removed

    def _ensure_dir_exists(self, dir_path: pathlib.Path) -> bool:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except OSError as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            return False

    def is_undo_enabled(self) -> bool:
        return self.settings.enable_undo_delete

    def clear_undo_cache(self, called_from_prepare: bool = False):
        """Clears the undo cache directory and resets internal state."""
        if not called_from_prepare:
            logger.info("Clearing undo cache.")
        if self.undo_cache_dir.exists():
            try:
                for item in self.undo_cache_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            except OSError as e:
                logger.error(f"Error clearing undo cache directory {self.undo_cache_dir}: {e}", exc_info=True)

        self.cached_items_info = []
        self.db_backup_in_cache_path = None
        # Explicitly remove the info file when clearing the cache
        info_file = self.undo_cache_dir / UNDO_INFO_FILENAME
        if info_file.exists():
            try:
                info_file.unlink()
            except OSError as e:
                logger.error(f"Error deleting undo info file {info_file}: {e}", exc_info=True)


    def prepare_undo_cache(self) -> bool:
        """
        Prepares the cache for a new undo operation.
        Clears previous cache and backs up the current database.
        Returns True if preparation was successful, False otherwise.
        """
        if not self.is_undo_enabled():
            return False

        logger.info("Preparing undo cache for new operation.")
        self.clear_undo_cache(called_from_prepare=True)

        if not self.db_path_live.exists():
            logger.error(f"Live database file not found at {self.db_path_live}. Cannot prepare undo cache.")
            return False

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.db_backup_in_cache_path = self.undo_cache_dir / f"{DB_FILENAME}.undo.{timestamp}.bak"

        try:
            shutil.copy2(self.db_path_live, self.db_backup_in_cache_path)
            logger.info(f"Database backed up for undo to: {self.db_backup_in_cache_path}")
            self._save_undo_info()
            return True
        except OSError as e:
            logger.error(f"Failed to backup database for undo: {e}", exc_info=True)
            self.db_backup_in_cache_path = None
            return False

    def cache_item_for_undo(self, original_path_str: str, item_type: str) -> bool:
        """
        Caches a file or directory for a potential undo operation.
        Assumes prepare_undo_cache has been called.
        """
        if not self.is_undo_enabled() or self.db_backup_in_cache_path is None:
            logger.warning(f"Undo not enabled or DB backup missing. Skipping caching of {original_path_str}.")
            return False

        original_path = pathlib.Path(original_path_str)
        if not original_path.exists():
            logger.error(f"Item to cache does not exist: {original_path}")
            return False

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
            cached_item_name = f"{original_path.name}.undo.{timestamp}"
            if not original_path.is_dir() and original_path.suffix:
                cached_item_name = f"{original_path.stem}.undo.{timestamp}{original_path.suffix}"
            
            cached_path = self.undo_cache_dir / cached_item_name

            if original_path.is_file():
                shutil.copy2(original_path, cached_path)
            elif original_path.is_dir():
                shutil.copytree(original_path, cached_path, dirs_exist_ok=False)
            
            logger.info(f"Item cached for undo: {original_path} -> {cached_path}")
            
            self.cached_items_info.append({
                "original_path": str(original_path),
                "cached_path": str(cached_path),
                "item_type": item_type,
                "is_dir": original_path.is_dir()
            })
            self._save_undo_info()
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache item {original_path} for undo: {e}", exc_info=True)
            return False

    def can_undo(self) -> bool:
        """Checks if there is a valid undo operation available by loading persisted info."""
        if not self.is_undo_enabled():
            return False
        
        loaded_info = self._load_undo_info()
        if not loaded_info:
            return False
        
        db_backup_path_from_info = loaded_info.get("db_backup_in_cache_path")
        # items_from_info = loaded_info.get("cached_items_info", []) # Not strictly needed for can_undo check

        if db_backup_path_from_info and pathlib.Path(db_backup_path_from_info).exists():
            return True 
        return False

    def perform_undo(self) -> bool:
        """Restores the system state from the undo cache."""
        if not self.can_undo():
            logger.warning("Undo operation cannot be performed or is not available.")
            return False

        logger.info("Performing undo operation.")
        
        loaded_info = self._load_undo_info()
        if not loaded_info:
            logger.error("Failed to load undo information. Cannot perform undo.")
            return False

        db_backup_to_restore_str = loaded_info.get("db_backup_in_cache_path")
        items_to_restore = loaded_info.get("cached_items_info", [])

        if not db_backup_to_restore_str:
            logger.error("Database backup path not found in undo info. Cannot perform undo.")
            return False
        
        db_backup_to_restore = pathlib.Path(db_backup_to_restore_str)
        if not db_backup_to_restore.exists():
            logger.error(f"Database backup file for undo not found at {db_backup_to_restore}. Cannot perform undo.")
            return False

        try:
            self.db_path_live.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db_backup_to_restore, self.db_path_live)
            logger.info(f"Database restored from undo cache: {db_backup_to_restore} -> {self.db_path_live}")
        except OSError as e:
            logger.error(f"Failed to restore database from undo cache: {e}", exc_info=True)
            return False

        all_items_restored = True
        for item_info in reversed(items_to_restore):
            original_path = pathlib.Path(item_info["original_path"])
            cached_path = pathlib.Path(item_info["cached_path"])
            is_dir = item_info["is_dir"]

            if not cached_path.exists():
                logger.error(f"Cached item not found: {cached_path}. Cannot restore {original_path}.")
                all_items_restored = False
                continue

            try:
                original_path.parent.mkdir(parents=True, exist_ok=True)
                if original_path.exists():
                    logger.warning(f"Original path {original_path} already exists. Skipping restore of this item.")
                    all_items_restored = False
                    continue

                if is_dir:
                    shutil.move(str(cached_path), str(original_path))
                else:
                    shutil.move(str(cached_path), str(original_path))
                logger.info(f"Item restored from undo cache: {cached_path} -> {original_path}")
            except Exception as e:
                logger.error(f"Failed to restore item {original_path} from {cached_path}: {e}", exc_info=True)
                all_items_restored = False
        
        if all_items_restored:
            logger.info("Undo operation completed successfully.")
            self.clear_undo_cache()
            return True
        else:
            logger.error("Undo operation completed with errors. Some items may not have been restored.")
            return False

    def _save_undo_info(self):
        """Saves the current undo state to a JSON file."""
        if not self.undo_cache_dir.exists(): # Should exist if prepare_undo_cache was called
            self._ensure_dir_exists(self.undo_cache_dir)

        info_path = self.undo_cache_dir / UNDO_INFO_FILENAME
        data_to_save = {
            "db_backup_in_cache_path": str(self.db_backup_in_cache_path) if self.db_backup_in_cache_path else None,
            "cached_items_info": self.cached_items_info,
            "prepared_timestamp": datetime.datetime.now().isoformat() # Add timestamp
        }
        try:
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
        except OSError as e:
            logger.error(f"Failed to save undo info to {info_path}: {e}", exc_info=True)

    def _load_undo_info(self) -> Optional[Dict[str, Any]]:
        """Loads undo state from the JSON file."""
        info_path = self.undo_cache_dir / UNDO_INFO_FILENAME
        if not info_path.exists():
            return None
        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load undo info from {info_path}: {e}", exc_info=True)
            return None

    def get_undo_cache_dir_path(self) -> pathlib.Path:
        """Returns the path to the undo cache directory."""
        return self.undo_cache_dir

    def clear_undo_cache_if_timed_out(self):
        """Clears the undo cache if it has timed out based on settings."""
        if not self.is_undo_enabled():
            return

        timeout_seconds = self.settings.undo_cache_timeout_seconds
        if timeout_seconds <= 0: # 0 or negative means no timeout
            return

        loaded_info = self._load_undo_info()
        if not loaded_info:
            return # No info, so effectively no active cache to timeout

        prepared_timestamp_str = loaded_info.get("prepared_timestamp")
        if not prepared_timestamp_str:
            logger.warning("Undo info found but missing 'prepared_timestamp'. Cannot check for timeout.")
            return

        try:
            prepared_time = datetime.datetime.fromisoformat(prepared_timestamp_str)
            elapsed_time = datetime.datetime.now() - prepared_time
            if elapsed_time.total_seconds() > timeout_seconds:
                logger.info(f"Undo cache timed out after {elapsed_time.total_seconds():.0f}s (limit: {timeout_seconds}s). Clearing cache.")
                self.clear_undo_cache()
            else:
                logger.debug(f"Undo cache not timed out. Elapsed: {elapsed_time.total_seconds():.0f}s, Limit: {timeout_seconds}s.")
        except ValueError:
            logger.error(f"Invalid 'prepared_timestamp' format in undo info: {prepared_timestamp_str}. Cannot check for timeout.", exc_info=True)
