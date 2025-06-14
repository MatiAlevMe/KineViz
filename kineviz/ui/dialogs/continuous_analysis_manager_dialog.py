import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Text
import logging
from pathlib import Path
import json
import os # For os.startfile on Windows
import sys # For platform check
import subprocess # For open/xdg-open
from datetime import datetime # For formatting dates

from kineviz.core.services.analysis_service import AnalysisService
from kineviz.ui.dialogs.continuous_analysis_config_dialog import ContinuousAnalysisConfigDialog

logger = logging.getLogger(__name__)

class ContinuousAnalysisManagerDialog(Toplevel):
    """
    Dialog for managing (listing, creating, viewing, deleting) continuous analyses.
    """
    def __init__(self, parent, analysis_service: AnalysisService, study_id: int):
        super().__init__(parent)
        self.parent = parent
        self.analysis_service = analysis_service
        self.study_id = study_id
        self.main_window = parent.master # Assuming parent is a widget within MainWindow's root

        self.title(f"Gestor de Análisis Continuos - Estudio {study_id}")
        # self.geometry("850x550") # Adjust as needed
        self.grab_set()
        self.transient(parent)

        self.create_widgets()
        self.load_analyses()

        # Center dialog
        self.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        position_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        position_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"+{position_x}+{position_y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", self._on_close)


    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Header and New Analysis Button ---
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0,10))
        ttk.Label(header_frame, text="Análisis Continuos Guardados:", font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        ttk.Button(header_frame, text="Nuevo Análisis Continuo...", command=self._open_new_analysis_dialog).pack(side=tk.RIGHT, padx=5)

        # --- Treeview for listing analyses ---
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))

        columns = ("name", "column", "groups", "date")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Nombre Análisis")
        self.tree.heading("column", text="Variable Analizada")
        self.tree.heading("groups", text="Grupos Comparados")
        self.tree.heading("date", text="Fecha Creación/Modif.")

        self.tree.column("name", width=200, anchor=tk.W)
        self.tree.column("column", width=250, anchor=tk.W)
        self.tree.column("groups", width=300, anchor=tk.W)
        self.tree.column("date", width=150, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_analysis_selected)
        self.tree.bind("<Double-1>", self._view_plot) # Double click to view plot

        # --- Action Buttons ---
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(5,0))

        self.view_plot_button = ttk.Button(action_frame, text="Ver Gráfico SPM", command=self._view_plot, state=tk.DISABLED)
        self.view_plot_button.pack(side=tk.LEFT, padx=5)

        self.view_config_button = ttk.Button(action_frame, text="Ver Configuración", command=self._view_config, state=tk.DISABLED)
        self.view_config_button.pack(side=tk.LEFT, padx=5)

        self.open_folder_button = ttk.Button(action_frame, text="Abrir Carpeta", command=self._open_folder, state=tk.DISABLED)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(action_frame, text="Eliminar Análisis", command=self._delete_analysis, state=tk.DISABLED)
        self.delete_button.pack(side=tk.RIGHT, padx=5) # Align to right

        # --- Close Button ---
        close_button_frame = ttk.Frame(main_frame) # Separate frame for close button
        close_button_frame.pack(fill=tk.X, pady=(10,0))
        ttk.Button(close_button_frame, text="Cerrar", command=self._on_close).pack(side=tk.RIGHT)


    def load_analyses(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            analyses = self.analysis_service.list_continuous_analyses(self.study_id)
            # analyses are already sorted by mtime in list_continuous_analyses

            for analysis_info in analyses:
                name = analysis_info.get('name', 'N/A')
                config = analysis_info.get('config', {})
                column = config.get('column', 'N/A')
                
                group_keys = config.get('groups', [])
                mode = config.get('grouping_mode')
                primary_vi = config.get('primary_vi_name')
                fixed_vi = config.get('fixed_vi_name')
                fixed_desc_display = config.get('fixed_descriptor_display')
                
                # Get aliases from study_service via main_window reference
                aliases = self.main_window.study_service.get_study_aliases(self.study_id)
                
                group_display_parts = []
                if mode == "1VI" and primary_vi and group_keys:
                    for desc_key_part in group_keys:
                        try:
                            _, desc_val = desc_key_part.split("=",1)
                            alias = aliases.get(desc_val, desc_val)
                            group_display_parts.append(f"{primary_vi}: {alias}")
                        except ValueError:
                             group_display_parts.append(desc_key_part)
                elif mode == "2VIs" and fixed_vi and fixed_desc_display and group_keys:
                    fixed_desc_original = fixed_desc_display.split(" (")[0]
                    fixed_pair_str_to_remove = f"{fixed_vi}={fixed_desc_original}"
                    for full_key_of_variable_part in group_keys:
                        variable_part_display_inner = []
                        for part in full_key_of_variable_part.split(';'):
                            if part != fixed_pair_str_to_remove:
                                try:
                                    vi_name_inner, desc_val_inner = part.split('=',1)
                                    alias_inner = aliases.get(desc_val_inner, desc_val_inner)
                                    variable_part_display_inner.append(f"{vi_name_inner}: {alias_inner}")
                                except ValueError:
                                    variable_part_display_inner.append(part)
                        group_display_parts.append(", ".join(variable_part_display_inner))
                else:
                    for key in group_keys:
                        parts = []
                        for item_part in key.split(';'):
                            try:
                                vi_name, desc_val = item_part.split('=', 1)
                                alias = aliases.get(desc_val, desc_val)
                                parts.append(f"{vi_name}: {alias}")
                            except ValueError:
                                parts.append(item_part)
                        group_display_parts.append(", ".join(parts))

                groups_str = " vs ".join(group_display_parts) if group_display_parts else "N/A"
                mtime = analysis_info.get('mtime')
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M') if mtime else "N/A"

                self.tree.insert("", tk.END, values=(name, column, groups_str, date_str), iid=name)
        except Exception as e:
            logger.error(f"Error cargando lista de análisis continuos para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los análisis continuos:\n{e}", parent=self)
        
        self._on_analysis_selected()


    def get_selected_analysis_info(self) -> dict | None:
        selected_items = self.tree.selection()
        if not selected_items:
            return None
        analysis_name = selected_items[0]
        analyses = self.analysis_service.list_continuous_analyses(self.study_id)
        for analysis_info in analyses:
            if analysis_info.get('name') == analysis_name:
                return analysis_info
        return None

    def _on_analysis_selected(self, event=None):
        selected_info = self.get_selected_analysis_info()
        can_act = selected_info is not None
        self.view_plot_button.config(state=tk.NORMAL if can_act and selected_info.get("plot_path") else tk.DISABLED)
        self.view_config_button.config(state=tk.NORMAL if can_act and selected_info.get("config_path") else tk.DISABLED)
        self.open_folder_button.config(state=tk.NORMAL if can_act and selected_info.get("path") else tk.DISABLED)
        self.delete_button.config(state=tk.NORMAL if can_act else tk.DISABLED)

    def _open_new_analysis_dialog(self):
        # This is where ContinuousAnalysisConfigDialog is launched
        dialog = ContinuousAnalysisConfigDialog(self, self.analysis_service, self.study_id) # self (this Toplevel) is the parent
        # self.wait_window(dialog) # Dialog is modal by grab_set() and transient()

        if dialog.result: # This will be checked after dialog closes
            logger.info(f"Configuración recibida del diálogo de análisis continuo: {dialog.result}")
            try:
                analysis_results = self.analysis_service.perform_continuous_analysis(self.study_id, dialog.result)
                logger.info(f"Resultado de perform_continuous_analysis: {analysis_results}")

                status = analysis_results.get("status", "error")
                message = analysis_results.get("message", "Error desconocido durante el análisis.")
                
                if "error" in status:
                    messagebox.showerror("Error de Análisis Continuo", message, parent=self)
                elif status == "partial_success":
                    messagebox.showwarning("Análisis Continuo Parcial", message, parent=self)
                else: # success
                    success_msg = f"Análisis continuo '{dialog.result.get('analysis_name')}' completado.\n{message}"
                    if analysis_results.get("output_dir"):
                        try:
                            study_base_path = self.analysis_service.file_service._get_study_path(self.study_id).parent.parent
                            relative_output_dir = Path(analysis_results.get('output_dir')).relative_to(study_base_path)
                            success_msg += f"\n\nResultados guardados en:\n.../{relative_output_dir}"
                        except Exception:
                             success_msg += f"\n\nResultados guardados en la carpeta del estudio:\n{analysis_results.get('output_dir')}"
                    messagebox.showinfo("Análisis Continuo Completado", success_msg, parent=self)
                
                self.load_analyses() # Recargar la lista
            except Exception as e:
                logger.critical(f"Excepción al llamar perform_continuous_analysis o procesar su resultado: {e}", exc_info=True)
                messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado al procesar el análisis continuo:\n{e}", parent=self)
        else:
            logger.info(f"Diálogo de configuración de análisis continuo cancelado para estudio {self.study_id}.")


    def _view_plot(self, event=None): # Add event=None for double-click binding
        selected_info = self.get_selected_analysis_info()
        if selected_info and selected_info.get("plot_path"):
            plot_path = Path(selected_info["plot_path"])
            if plot_path.exists():
                try:
                    if sys.platform == "win32": os.startfile(plot_path)
                    elif sys.platform == "darwin": subprocess.run(["open", plot_path], check=True)
                    else: subprocess.run(["xdg-open", plot_path], check=True)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir el gráfico:\n{e}", parent=self)
                    logger.error(f"Error abriendo gráfico {plot_path}: {e}", exc_info=True)
            else:
                messagebox.showwarning("Archivo no encontrado", "El archivo del gráfico SPM no existe.", parent=self)
        elif event: # If called by double-click but no plot
             pass # Do nothing if double-click on item without plot
        else: # Called by button
            messagebox.showinfo("Información", "No hay gráfico SPM para el análisis seleccionado o el análisis no está seleccionado.", parent=self)

    def _view_config(self):
        selected_info = self.get_selected_analysis_info()
        if selected_info and selected_info.get("config_path"):
            config_path = Path(selected_info["config_path"])
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    config_window = Toplevel(self)
                    config_window.title(f"Configuración: {selected_info.get('name')}")
                    config_window.geometry("600x400")
                    
                    text_area = Text(config_window, wrap=tk.WORD, font=("Courier New", 10))
                    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    text_area.insert(tk.END, json.dumps(config_data, indent=4, ensure_ascii=False))
                    text_area.config(state=tk.DISABLED)

                    scrollbar = ttk.Scrollbar(text_area, command=text_area.yview)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    text_area.config(yscrollcommand=scrollbar.set)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo leer o mostrar el archivo de configuración:\n{e}", parent=self)
                    logger.error(f"Error leyendo/mostrando config {config_path}: {e}", exc_info=True)
            else:
                messagebox.showwarning("Archivo no encontrado", "El archivo de configuración no existe.", parent=self)
        else:
            messagebox.showinfo("Información", "No hay archivo de configuración para el análisis seleccionado o el análisis no está seleccionado.", parent=self)

    def _open_folder(self):
        selected_info = self.get_selected_analysis_info()
        if selected_info and selected_info.get("path"):
            folder_path = Path(selected_info["path"])
            if folder_path.exists() and folder_path.is_dir():
                # Use main_window.open_folder if available, otherwise direct call
                if hasattr(self.main_window, 'open_folder') and callable(self.main_window.open_folder):
                    self.main_window.open_folder(str(folder_path))
                else: # Fallback if main_window.open_folder is not available
                    try:
                        if sys.platform == "win32": os.startfile(folder_path)
                        elif sys.platform == "darwin": subprocess.run(["open", folder_path], check=True)
                        else: subprocess.run(["xdg-open", folder_path], check=True)
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{e}", parent=self)
                        logger.error(f"Error abriendo carpeta {folder_path}: {e}", exc_info=True)
            else:
                messagebox.showwarning("Carpeta no encontrada", "La carpeta del análisis no existe.", parent=self)
        else:
            messagebox.showinfo("Información", "No hay carpeta para el análisis seleccionado o el análisis no está seleccionado.", parent=self)

    def _delete_analysis(self):
        selected_info = self.get_selected_analysis_info()
        if not selected_info:
            messagebox.showinfo("Información", "Seleccione un análisis para eliminar.", parent=self)
            return

        analysis_name = selected_info.get('name')
        if messagebox.askyesno("Confirmar Eliminación",
                               f"¿Está seguro de que desea eliminar el análisis continuo '{analysis_name}'?\n"
                               "Esta acción no se puede deshacer.",
                               parent=self, icon='warning'):
            try:
                self.analysis_service.delete_continuous_analysis(self.study_id, analysis_name)
                messagebox.showinfo("Éxito", f"Análisis '{analysis_name}' eliminado correctamente.", parent=self)
                self.load_analyses()
            except FileNotFoundError:
                messagebox.showerror("Error", f"No se encontró el análisis '{analysis_name}' para eliminar.", parent=self)
                self.load_analyses()
            except Exception as e:
                logger.error(f"Error eliminando análisis continuo '{analysis_name}': {e}", exc_info=True)
                messagebox.showerror("Error", f"No se pudo eliminar el análisis '{analysis_name}':\n{e}", parent=self)

    def _on_close(self, event=None):
        self.destroy()

# Dummy main for testing
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Dummy Main Window for Manager")
    # root.geometry("900x700")

    class DummyStudyService:
        def get_study_details(self, study_id): return {'aliases': {}}
        def get_study_aliases(self, study_id): return {'CMJ': 'Salto CMJ', 'PRE': 'Antes'}

    class DummyFileService:
        def _get_study_path(self, study_id): return Path(f"/tmp/study_{study_id}")

    class DummyAnalysisService:
        def __init__(self):
            self.study_service = DummyStudyService()
            self.file_service = DummyFileService()
            self.continuous_analyses_store = {}

        def list_continuous_analyses(self, study_id):
            logger.info(f"Dummy Manager: list_continuous_analyses para estudio {study_id}")
            base_path = self.file_service._get_study_path(study_id) / "Analisis Continuo"
            if study_id not in self.continuous_analyses_store:
                 self.continuous_analyses_store[study_id] = {}
                 for i in range(1, 3):
                    name = f"SPM_Managed_Test_{i}"
                    analysis_path = base_path / name; analysis_path.mkdir(parents=True, exist_ok=True)
                    config_data = {"analysis_name": name, "column": f"Var{i}", "groups": [f"G{i}A", f"G{i}B"], "grouping_mode": "1VI", "primary_vi_name": "Cond", "mtime": datetime.now().timestamp() - (i * 3600)}
                    with open(analysis_path / "config_continuous.json", 'w') as f: json.dump(config_data, f)
                    (analysis_path / "spm_plot.png").touch()
                    self.continuous_analyses_store[study_id][name] = {'name': name, 'path': analysis_path, 'config': config_data, 'mtime': config_data['mtime'], 'plot_path': analysis_path / "spm_plot.png", 'config_path': analysis_path / "config_continuous.json"}
            return list(self.continuous_analyses_store.get(study_id, {}).values())

        def delete_continuous_analysis(self, study_id, analysis_name):
            logger.info(f"Dummy Manager: delete_continuous_analysis ({study_id}, {analysis_name})")
            # Simplified deletion for dummy
            if study_id in self.continuous_analyses_store and analysis_name in self.continuous_analyses_store[study_id]:
                del self.continuous_analyses_store[study_id][analysis_name]
            else: raise FileNotFoundError("Not found in dummy store")
        
        def perform_continuous_analysis(self, study_id, config): # Needed by _open_new_analysis_dialog
            logger.info(f"Dummy Manager: perform_continuous_analysis for {study_id} with {config}")
            name = config.get("analysis_name")
            if not name: return {"status": "error", "message": "Dummy: Name required."}
            # Simulate saving
            if study_id not in self.continuous_analyses_store: self.continuous_analyses_store[study_id] = {}
            base_path = self.file_service._get_study_path(study_id) / "Analisis Continuo"
            analysis_path = base_path / name; analysis_path.mkdir(parents=True, exist_ok=True)
            config['mtime'] = datetime.now().timestamp()
            with open(analysis_path / "config_continuous.json", 'w') as f: json.dump(config, f)
            (analysis_path / "spm_plot.png").touch()
            self.continuous_analyses_store[study_id][name] = {'name': name, 'path': analysis_path, 'config': config, 'mtime': config['mtime'], 'plot_path': analysis_path / "spm_plot.png", 'config_path': analysis_path / "config_continuous.json"}
            return {"status": "success", "message": "Dummy analysis completed.", "output_dir": str(analysis_path)}

        # Methods for ContinuousAnalysisConfigDialog
        def get_available_frequencies_for_study(self, study_id): return ["Cinematica"]
        def get_data_columns_for_frequency(self, study_id, frequency): return ["LAnkleAngles/X/deg", "RKneeAngles/Y/deg"]
        def get_filtered_discrete_analysis_groups(self, study_id, frequency, mode, primary_vi_name=None, fixed_vi_name=None, fixed_descriptor_value=None):
            if mode == "1VI": return {f"{primary_vi_name}=A": f"{primary_vi_name}: A", f"{primary_vi_name}=B": f"{primary_vi_name}: B"}
            return {}

    class DummyMainWindowForManager: # To act as parent.master
        def __init__(self):
            self.study_service = DummyStudyService()
        def open_folder(self, path_str): logger.info(f"DummyMainWindowForManager: open_folder({path_str})")

    # Setup for the dialog
    dummy_main_window_ref = DummyMainWindowForManager()
    # The dialog's parent is root, its master (for main_window access) is dummy_main_window_ref
    # This is a bit of a hack for testing; in real app, parent is a widget in MainWindow.root
    # So, self.main_window = parent.master would correctly get MainWindow instance.
    # For this dummy, we pass root as parent, and the dialog will try self.parent.master
    # We need to ensure root.master is set.
    root.master = dummy_main_window_ref 

    dummy_analysis_service_ref = DummyAnalysisService()
    test_study_id_for_manager = 1
    
    # Button to open the manager dialog
    ttk.Button(root, text="Open Continuous Analysis Manager", 
               command=lambda: ContinuousAnalysisManagerDialog(root, dummy_analysis_service_ref, test_study_id_for_manager)
              ).pack(padx=20, pady=20)

    root.mainloop()
