import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, simpledialog
from pathlib import Path
import datetime # For formatting timestamp
import logging # For logging
import time # For sleep in dummy test

# Import backup_manager functions directly for type hinting and direct calls
from kineviz.core import backup_manager 
from kineviz.config.settings import AppSettings # For AppSettings type hint
from kineviz.ui.widgets.tooltip import Tooltip

# Setup logger for this module if not configured globally for UI
logger = logging.getLogger(__name__)


class BackupRestoreDialog(Toplevel):
    """Diálogo para gestionar copias de seguridad y restauraciones."""

    def __init__(self, parent, app_settings: AppSettings):
        super().__init__(parent)
        self.parent_window = parent # Store parent for simpledialog if needed
        self.app_settings = app_settings # Store AppSettings instance

        self.title("Gestión de Copias de Seguridad")
        self.geometry("800x500") # Initial size
        self.minsize(600, 400)

        self.backup_list = [] # To store data from backup_manager.list_backups()

        self.create_widgets()
        self.load_backups()

        self.transient(parent)
        self.grab_set()
        # self.protocol("WM_DELETE_WINDOW", self.destroy) # Default behavior is fine

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Treeview para listar backups ---
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("type", "timestamp", "alias", "filename")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("type", text="Tipo")
        self.tree.heading("timestamp", text="Fecha de Creación")
        self.tree.heading("alias", text="Alias (Manual)")
        self.tree.heading("filename", text="Nombre Archivo") # Hidden column for internal use

        self.tree.column("type", width=100, anchor=tk.W)
        self.tree.column("timestamp", width=180, anchor=tk.W)
        self.tree.column("alias", width=200, anchor=tk.W)
        self.tree.column("filename", width=0, stretch=tk.NO) # Hide filename column

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_backup_selected)


        # --- Frame para botones de acción ---
        action_buttons_frame = ttk.Frame(main_frame)
        action_buttons_frame.pack(fill=tk.X, pady=(5,0))

        self.btn_create_manual = ttk.Button(action_buttons_frame, text="Crear Copia Manual", command=self.create_manual_backup_action)
        self.btn_create_manual.pack(side=tk.LEFT, padx=5)
        Tooltip(self.btn_create_manual, "Crea una nueva copia de seguridad manual del estado actual del sistema.", enabled=self.app_settings.enable_hover_tooltips)

        self.btn_restore = ttk.Button(action_buttons_frame, text="Restaurar Seleccionada", command=self.restore_selected_action, state=tk.DISABLED)
        self.btn_restore.pack(side=tk.LEFT, padx=5)
        Tooltip(self.btn_restore, "Restaura el sistema al estado de la copia de seguridad seleccionada. ¡Esta acción es irreversible!", enabled=self.app_settings.enable_hover_tooltips)
        
        self.btn_assign_alias = ttk.Button(action_buttons_frame, text="Asignar/Editar Alias", command=self.assign_alias_action, state=tk.DISABLED)
        self.btn_assign_alias.pack(side=tk.LEFT, padx=5)
        Tooltip(self.btn_assign_alias, "Asigna o edita un alias descriptivo a una copia de seguridad manual seleccionada.", enabled=self.app_settings.enable_hover_tooltips)

        self.btn_delete_manual = ttk.Button(action_buttons_frame, text="Eliminar Manual", command=self.delete_manual_action, state=tk.DISABLED, style="Danger.TButton")
        self.btn_delete_manual.pack(side=tk.LEFT, padx=5)
        Tooltip(self.btn_delete_manual, "Elimina permanentemente la copia de seguridad manual seleccionada.", enabled=self.app_settings.enable_hover_tooltips)

        # --- Botón de Cancelar/Cerrar ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10,0))
        
        btn_refresh = ttk.Button(bottom_frame, text="Refrescar Lista", command=self.load_backups)
        btn_refresh.pack(side=tk.LEFT, padx=5)
        Tooltip(btn_refresh, "Vuelve a cargar la lista de copias de seguridad disponibles.", enabled=self.app_settings.enable_hover_tooltips)

        btn_cancel = ttk.Button(bottom_frame, text="Cerrar", command=self.destroy)
        btn_cancel.pack(side=tk.RIGHT, padx=5)


    def load_backups(self):
        """Carga la lista de backups y los muestra en el Treeview."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        self.backup_list = backup_manager.list_backups()
        
        for backup_item in self.backup_list:
            backup_type_display = "Automática" if backup_item['type'] == backup_manager.AUTOMATIC_BACKUPS_SUBDIR else "Manual"
            timestamp_display = backup_item['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            alias_display = backup_item['alias'] if backup_item['alias'] else ""
            
            # Store full path or unique identifier if needed for actions
            self.tree.insert("", tk.END, values=(
                backup_type_display, 
                timestamp_display, 
                alias_display,
                backup_item['filename'] # Store filename for identification
            ))
        self.on_backup_selected(None) # Update button states

    def on_backup_selected(self, event):
        """Actualiza el estado de los botones cuando se selecciona un backup."""
        selected_item_id = self.tree.focus() # Obtiene el ID del item seleccionado
        if not selected_item_id:
            self.btn_restore.config(state=tk.DISABLED)
            self.btn_assign_alias.config(state=tk.DISABLED)
            self.btn_delete_manual.config(state=tk.DISABLED)
            return

        selected_values = self.tree.item(selected_item_id, "values")
        backup_type_display = selected_values[0]
        # backup_filename = selected_values[3] # Filename is at index 3

        is_manual = (backup_type_display == "Manual")
        
        self.btn_restore.config(state=tk.NORMAL) # Restore can be done for any type
        self.btn_assign_alias.config(state=tk.NORMAL if is_manual else tk.DISABLED)
        self.btn_delete_manual.config(state=tk.NORMAL if is_manual else tk.DISABLED, style="Danger.TButton" if is_manual else "TButton")


    def create_manual_backup_action(self):
        """Acción para crear una copia de seguridad manual."""
        alias = simpledialog.askstring("Alias para Copia Manual", 
                                       "Ingrese un alias opcional para esta copia de seguridad manual:",
                                       parent=self)
        if alias is not None: # User didn't cancel, alias can be empty string
            try:
                logger.info(f"Attempting to create manual backup with alias: '{alias if alias else 'No Alias'}'")
                backup_path = backup_manager.create_backup(backup_manager.MANUAL_BACKUPS_SUBDIR)
                if backup_path:
                    if alias.strip(): # Only add alias if it's not empty
                        backup_manager.add_manual_backup_alias(backup_path.name, alias.strip())
                    messagebox.showinfo("Éxito", f"Copia de seguridad manual '{backup_path.name}' creada exitosamente.", parent=self)
                    self.load_backups()
                else:
                    messagebox.showerror("Error", "No se pudo crear la copia de seguridad manual.", parent=self)
            except Exception as e:
                logger.error(f"Error creando copia manual: {e}", exc_info=True)
                messagebox.showerror("Error", f"Ocurrió un error al crear la copia manual:\n{e}", parent=self)

    def restore_selected_action(self):
        """Acción para restaurar una copia de seguridad seleccionada."""
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una copia de seguridad para restaurar.", parent=self)
            return

        selected_values = self.tree.item(selected_item_id, "values")
        backup_filename = selected_values[3] # Filename is at index 3
        backup_type_display = selected_values[0]
        backup_type_internal = backup_manager.AUTOMATIC_BACKUPS_SUBDIR if backup_type_display == "Automática" else backup_manager.MANUAL_BACKUPS_SUBDIR
        
        full_backup_path = backup_manager.get_project_root() / backup_manager.BACKUPS_DIR_NAME / backup_type_internal / backup_filename

        if not messagebox.askokcancel("Confirmar Restauración", 
                                     f"¿Está seguro de que desea restaurar el sistema desde la copia '{backup_filename}'?\n\n"
                                     "ESTA ACCIÓN ES IRREVERSIBLE y reemplazará todos los datos actuales del estudio, "
                                     "la base de datos y la configuración.",
                                     icon='warning', parent=self):
            return

        try:
            # Placeholder for actual restoration logic
            # success = backup_manager.restore_backup(full_backup_path)
            logger.info(f"Placeholder: Restaurar desde {full_backup_path}")
            messagebox.showinfo("Restauración (Simulada)", "Funcionalidad de restauración aún no implementada.\n"
                                f"Se intentaría restaurar desde: {backup_filename}", parent=self)
            # if success:
            #     messagebox.showinfo("Éxito", "Sistema restaurado exitosamente.\nSe recomienda reiniciar la aplicación.", parent=self)
            #     # Potentially trigger app restart or navigate to landing page
            # else:
            #     messagebox.showerror("Error", "No se pudo restaurar la copia de seguridad.", parent=self)
        except Exception as e:
            logger.error(f"Error restaurando copia de seguridad {backup_filename}: {e}", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error al restaurar la copia de seguridad:\n{e}", parent=self)


    def assign_alias_action(self):
        """Acción para asignar o editar un alias a una copia manual."""
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una copia de seguridad manual.", parent=self)
            return

        selected_values = self.tree.item(selected_item_id, "values")
        backup_type_display = selected_values[0]
        current_alias = selected_values[2]
        backup_filename = selected_values[3]

        if backup_type_display != "Manual":
            messagebox.showwarning("Tipo Inválido", "Solo se pueden asignar alias a copias de seguridad manuales.", parent=self)
            return

        new_alias = simpledialog.askstring("Asignar/Editar Alias", 
                                           f"Ingrese un nuevo alias para '{backup_filename}':\n(Deje vacío para quitar el alias actual)",
                                           initialvalue=current_alias,
                                           parent=self)

        if new_alias is not None: # User didn't cancel
            try:
                if new_alias.strip():
                    backup_manager.add_manual_backup_alias(backup_filename, new_alias.strip())
                    messagebox.showinfo("Éxito", f"Alias actualizado para '{backup_filename}'.", parent=self)
                else: # Empty string means remove alias
                    backup_manager.remove_manual_backup_alias(backup_filename)
                    messagebox.showinfo("Éxito", f"Alias eliminado para '{backup_filename}'.", parent=self)
                self.load_backups()
            except Exception as e:
                logger.error(f"Error asignando alias a {backup_filename}: {e}", exc_info=True)
                messagebox.showerror("Error", f"Ocurrió un error al asignar el alias:\n{e}", parent=self)


    def delete_manual_action(self):
        """Acción para eliminar una copia de seguridad manual seleccionada."""
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione una copia de seguridad manual para eliminar.", parent=self)
            return

        selected_values = self.tree.item(selected_item_id, "values")
        backup_type_display = selected_values[0]
        backup_filename = selected_values[3]

        if backup_type_display != "Manual":
            messagebox.showwarning("Tipo Inválido", "Solo se pueden eliminar copias de seguridad manuales desde aquí.", parent=self)
            return

        if not messagebox.askokcancel("Confirmar Eliminación", 
                                     f"¿Está seguro de que desea eliminar permanentemente la copia de seguridad manual '{backup_filename}'?",
                                     icon='warning', parent=self):
            return
        
        try:
            success = backup_manager.delete_manual_backup(backup_filename)
            if success:
                messagebox.showinfo("Éxito", f"Copia de seguridad manual '{backup_filename}' eliminada.", parent=self)
                self.load_backups()
            else:
                messagebox.showerror("Error", f"No se pudo eliminar la copia de seguridad manual '{backup_filename}'.", parent=self)
        except Exception as e:
            logger.error(f"Error eliminando copia manual {backup_filename}: {e}", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error al eliminar la copia manual:\n{e}", parent=self)


if __name__ == '__main__':
    # This is a basic test, assumes backup_manager and AppSettings are available
    # and that some dummy backup files might exist or be created by backup_manager tests.
    
    # Setup dummy logger for testing
    logging.basicConfig(level=logging.DEBUG)
    # logger is already defined at module level

    # Create dummy AppSettings
    class DummyAppSettings:
        def __init__(self):
            self.enable_hover_tooltips = True
            # Add other settings if BackupRestoreDialog directly uses them

    root = tk.Tk()
    root.title("Test Root")
    
    # Create dummy backup files for testing list_backups
    # You would need to adapt this to your backup_manager's structure
    dummy_backup_dir = backup_manager.get_project_root() / backup_manager.BACKUPS_DIR_NAME
    (dummy_backup_dir / backup_manager.AUTOMATIC_BACKUPS_SUBDIR).mkdir(parents=True, exist_ok=True)
    (dummy_backup_dir / backup_manager.MANUAL_BACKUPS_SUBDIR).mkdir(parents=True, exist_ok=True)
    
    now = datetime.datetime.now()
    (dummy_backup_dir / backup_manager.AUTOMATIC_BACKUPS_SUBDIR / f"backup_{now.strftime('%Y%m%d_%H%M%S')}.zip").write_text("auto content")
    time.sleep(1) # Ensure distinct timestamp for manual backup
    now_manual = datetime.datetime.now()
    manual_fn = f"backup_{now_manual.strftime('%Y%m%d_%H%M%S')}.zip"
    (dummy_backup_dir / backup_manager.MANUAL_BACKUPS_SUBDIR / manual_fn).write_text("manual content")
    
    # Dummy alias file
    aliases = {manual_fn: "Test Manual Alias"}
    backup_manager._save_manual_backup_aliases(aliases)


    app_settings_instance = DummyAppSettings()
    
    def open_dialog():
        dialog = BackupRestoreDialog(root, app_settings_instance)
        root.wait_window(dialog)

    ttk.Button(root, text="Open Backup/Restore Dialog", command=open_dialog).pack(padx=20, pady=20)
    
    root.mainloop()

    # Clean up dummy files (optional)
    # import shutil # Already imported if needed for cleanup
    # shutil.rmtree(dummy_backup_dir, ignore_errors=True)
    logger.info("Test finished. Manual cleanup of 'backups' directory might be needed.")