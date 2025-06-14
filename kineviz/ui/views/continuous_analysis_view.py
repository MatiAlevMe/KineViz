import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
from datetime import datetime # Import datetime
import webbrowser # For opening files/folders
import subprocess # For opening files/folders
import sys # For platform check
import json # For reading config files

from kineviz.core.services.analysis_service import AnalysisService
from kineviz.ui.dialogs.continuous_analysis_config_dialog import ContinuousAnalysisConfigDialog

logger = logging.getLogger(__name__)

class ContinuousAnalysisView(ttk.Frame):
    """
    View for managing and visualizing continuous analyses (SPM).
    """
    def __init__(self, parent, main_window, analysis_service: AnalysisService, study_id: int):
        super().__init__(parent)
        self.parent = parent
        self.main_window = main_window
        self.analysis_service = analysis_service
        self.study_id = study_id

        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.create_widgets()
        self.load_analyses()

    def create_widgets(self):
        # --- Header ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(header_frame, text="<< Volver al Estudio",
                   command=lambda: self.main_window.show_study_view(self.study_id)
                  ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(header_frame, text="Nuevo Análisis Continuo",
                   command=self._open_config_dialog).pack(side=tk.LEFT, padx=(0, 10))

        # --- Treeview para listar análisis ---
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

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

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_analysis_selected)

        # --- Botones de Acción ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, pady=(5, 0))

        self.view_plot_button = ttk.Button(action_frame, text="Ver Gráfico SPM", command=self._view_plot, state=tk.DISABLED)
        self.view_plot_button.pack(side=tk.LEFT, padx=5)

        self.view_config_button = ttk.Button(action_frame, text="Ver Configuración", command=self._view_config, state=tk.DISABLED)
        self.view_config_button.pack(side=tk.LEFT, padx=5)

        self.open_folder_button = ttk.Button(action_frame, text="Abrir Carpeta", command=self._open_folder, state=tk.DISABLED)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(action_frame, text="Eliminar Análisis", command=self._delete_analysis, state=tk.DISABLED)
        self.delete_button.pack(side=tk.RIGHT, padx=5)


    def load_analyses(self):
        """Carga y muestra la lista de análisis continuos guardados."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            analyses = self.analysis_service.list_continuous_analyses(self.study_id)
            analyses.sort(key=lambda x: x.get('mtime', 0), reverse=True) # Ordenar por fecha

            for analysis_info in analyses:
                name = analysis_info.get('name', 'N/A')
                config = analysis_info.get('config', {})
                column = config.get('column', 'N/A')
                
                # Formatear grupos para visualización
                group_keys = config.get('groups', [])
                mode = config.get('grouping_mode')
                primary_vi = config.get('primary_vi_name')
                fixed_vi = config.get('fixed_vi_name')
                fixed_desc_display = config.get('fixed_descriptor_display')
                aliases = self.main_window.study_service.get_study_aliases(self.study_id)
                
                group_display_parts = []
                if mode == "1VI" and primary_vi and group_keys:
                    # group_keys son los descriptores de la VI primaria
                    for desc_key_part in group_keys: # desc_key_part es "VI=Desc"
                        try:
                            _, desc_val = desc_key_part.split("=",1)
                            alias = aliases.get(desc_val, desc_val)
                            group_display_parts.append(f"{primary_vi}: {alias}")
                        except ValueError:
                             group_display_parts.append(desc_key_part) # Fallback
                elif mode == "2VIs" and fixed_vi and fixed_desc_display and group_keys:
                    # group_keys son las claves de la VI variable
                    fixed_desc_original = fixed_desc_display.split(" (")[0]
                    fixed_pair_str_to_remove = f"{fixed_vi}={fixed_desc_original}"
                    for full_key_of_variable_part in group_keys: # full_key_of_variable_part es "VI_var=Desc_var;VI_fixed=Desc_fixed"
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
                else: # Modo combinado o fallback
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
        
        self._on_analysis_selected() # Para actualizar estado de botones

    def _get_selected_analysis_info(self) -> dict | None:
        """Obtiene la información del análisis seleccionado en el Treeview."""
        selected_items = self.tree.selection()
        if not selected_items:
            return None
        
        analysis_name = selected_items[0] # iid es el nombre del análisis
        # Buscar en la lista de análisis cargados (podríamos almacenar esto en load_analyses)
        # Por ahora, volvemos a listar para obtener la info completa
        analyses = self.analysis_service.list_continuous_analyses(self.study_id)
        for analysis_info in analyses:
            if analysis_info.get('name') == analysis_name:
                return analysis_info
        return None

    def _on_analysis_selected(self, event=None):
        """Actualiza el estado de los botones de acción cuando se selecciona un análisis."""
        selected_info = self._get_selected_analysis_info()
        can_act = selected_info is not None

        self.view_plot_button.config(state=tk.NORMAL if can_act and selected_info.get("plot_path") else tk.DISABLED)
        self.view_config_button.config(state=tk.NORMAL if can_act and selected_info.get("config_path") else tk.DISABLED)
        self.open_folder_button.config(state=tk.NORMAL if can_act and selected_info.get("path") else tk.DISABLED)
        self.delete_button.config(state=tk.NORMAL if can_act else tk.DISABLED)

    def _open_config_dialog(self):
        """Abre el diálogo para configurar un nuevo análisis continuo."""
        dialog = ContinuousAnalysisConfigDialog(self.main_window.root, self.analysis_service, self.study_id)
        self.main_window.root.wait_window(dialog)

        if dialog.result:
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
                        # Tratar de obtener ruta relativa al directorio de estudios para un path más corto
                        try:
                            study_base_path = self.analysis_service.file_service._get_study_path(self.study_id).parent.parent
                            relative_output_dir = Path(analysis_results.get('output_dir')).relative_to(study_base_path)
                            success_msg += f"\n\nResultados guardados en:\n.../{relative_output_dir}"
                        except Exception: # Fallback a ruta absoluta
                             success_msg += f"\n\nResultados guardados en la carpeta del estudio:\n{analysis_results.get('output_dir')}"
                    messagebox.showinfo("Análisis Continuo Completado", success_msg, parent=self)
                
                self.load_analyses() # Recargar la lista
            except Exception as e:
                logger.critical(f"Excepción al llamar perform_continuous_analysis o procesar su resultado: {e}", exc_info=True)
                messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado al procesar el análisis continuo:\n{e}", parent=self)
        else:
            logger.info(f"Diálogo de configuración de análisis continuo cancelado para estudio {self.study_id}.")


    def _view_plot(self):
        selected_info = self._get_selected_analysis_info()
        if selected_info and selected_info.get("plot_path"):
            plot_path = Path(selected_info["plot_path"])
            if plot_path.exists():
                try:
                    if sys.platform == "win32":
                        os.startfile(plot_path)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", plot_path], check=True)
                    else:
                        subprocess.run(["xdg-open", plot_path], check=True)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo abrir el gráfico:\n{e}", parent=self)
                    logger.error(f"Error abriendo gráfico {plot_path}: {e}", exc_info=True)
            else:
                messagebox.showwarning("Archivo no encontrado", "El archivo del gráfico SPM no existe.", parent=self)
        else:
            messagebox.showinfo("Información", "No hay gráfico SPM para el análisis seleccionado o el análisis no está seleccionado.", parent=self)

    def _view_config(self):
        selected_info = self._get_selected_analysis_info()
        if selected_info and selected_info.get("config_path"):
            config_path = Path(selected_info["config_path"])
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # Mostrar en un Toplevel con Text widget
                    config_window = tk.Toplevel(self)
                    config_window.title(f"Configuración: {selected_info.get('name')}")
                    config_window.geometry("600x400")
                    
                    text_area = tk.Text(config_window, wrap=tk.WORD, font=("Courier New", 10))
                    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    text_area.insert(tk.END, json.dumps(config_data, indent=4, ensure_ascii=False))
                    text_area.config(state=tk.DISABLED)

                    # Scrollbar
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
        selected_info = self._get_selected_analysis_info()
        if selected_info and selected_info.get("path"):
            folder_path = Path(selected_info["path"])
            if folder_path.exists() and folder_path.is_dir():
                self.main_window.open_folder(str(folder_path)) # Reutilizar método de MainWindow
            else:
                messagebox.showwarning("Carpeta no encontrada", "La carpeta del análisis no existe.", parent=self)
        else:
            messagebox.showinfo("Información", "No hay carpeta para el análisis seleccionado o el análisis no está seleccionado.", parent=self)


    def _delete_analysis(self):
        selected_info = self._get_selected_analysis_info()
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
                self.load_analyses() # Recargar la lista
            except FileNotFoundError:
                messagebox.showerror("Error", f"No se encontró el análisis '{analysis_name}' para eliminar.", parent=self)
                self.load_analyses() # Recargar por si acaso
            except Exception as e:
                logger.error(f"Error eliminando análisis continuo '{analysis_name}': {e}", exc_info=True)
                messagebox.showerror("Error", f"No se pudo eliminar el análisis '{analysis_name}':\n{e}", parent=self)

    def destroy(self):
        """Destruye el frame principal de esta vista."""
        if self and self.winfo_exists():
             super().destroy()


# Para pruebas directas (opcional)
if __name__ == '__main__':
    from datetime import datetime # Necesario para el mock de load_analyses
    root = tk.Tk()
    root.title("Ventana Principal (Dummy para ContinuousAnalysisView)")
    # root.geometry("900x700")

    class DummyStudyService:
        def get_study_details(self, study_id): return {'aliases': {}}
        def get_study_aliases(self, study_id): return {}

    class DummyFileService:
        def _get_study_path(self, study_id): return Path(f"/tmp/study_{study_id}")

    class DummyAnalysisService:
        def __init__(self):
            self.study_service = DummyStudyService()
            self.file_service = DummyFileService()
            self.continuous_analyses_store = {} # {study_id: {analysis_name: info}}

        def list_continuous_analyses(self, study_id):
            logger.info(f"Dummy: list_continuous_analyses para estudio {study_id}")
            base_path = self.file_service._get_study_path(study_id) / "Analisis Continuo"
            
            # Simular algunos análisis si no existen para la prueba
            if study_id not in self.continuous_analyses_store:
                 self.continuous_analyses_store[study_id] = {}
                 # Crear algunos análisis dummy
                 for i in range(1, 4):
                    name = f"SPM_Test_{i}"
                    analysis_path = base_path / name
                    analysis_path.mkdir(parents=True, exist_ok=True)
                    
                    config_data = {
                        "analysis_name": name, "data_type": "Cinematica",
                        "column": f"LAnkleAngles/X/deg" if i % 2 == 0 else "RKneeAngles/Y/deg",
                        "groups": [f"Condicion=PRE;Salto=CMJ", f"Condicion=POST;Salto=CMJ"] if i == 1 else [f"GrupoA", f"GrupoB"],
                        "grouping_mode": "2VIs" if i == 1 else "1VI",
                        "primary_vi_name": "Algo" if i != 1 else None,
                        "fixed_vi_name": "Condicion" if i == 1 else None,
                        "fixed_descriptor_display": "PRE (Antes)" if i == 1 else None,
                        "mtime": datetime.now().timestamp() - (i * 3600)
                    }
                    config_file = analysis_path / "config_continuous.json"
                    with open(config_file, 'w') as f_cfg: json.dump(config_data, f_cfg)
                    
                    plot_file = analysis_path / "spm_plot.png"
                    plot_file.touch() # Crear archivo dummy

                    self.continuous_analyses_store[study_id][name] = {
                        'name': name, 'path': analysis_path, 'config': config_data,
                        'mtime': config_data['mtime'],
                        'plot_path': plot_file,
                        'spm_results_path': analysis_path / "spm_results.json" # Podría no existir
                    }
            
            return list(self.continuous_analyses_store.get(study_id, {}).values())

        def delete_continuous_analysis(self, study_id, analysis_name):
            logger.info(f"Dummy: delete_continuous_analysis ({study_id}, {analysis_name})")
            if study_id in self.continuous_analyses_store and analysis_name in self.continuous_analyses_store[study_id]:
                analysis_path = self.continuous_analyses_store[study_id][analysis_name]['path']
                # Simular eliminación de carpeta
                if analysis_path.exists():
                    import shutil
                    shutil.rmtree(analysis_path)
                del self.continuous_analyses_store[study_id][analysis_name]
                logger.info(f"Dummy: Análisis '{analysis_name}' eliminado.")
            else:
                raise FileNotFoundError(f"Análisis '{analysis_name}' no encontrado.")
        
        def perform_continuous_analysis(self, study_id, config):
            logger.info(f"Dummy: perform_continuous_analysis para estudio {study_id} con config: {config}")
            analysis_name = config.get("analysis_name")
            if not analysis_name: return {"status": "error", "message": "Nombre de análisis requerido."}

            if study_id not in self.continuous_analyses_store:
                self.continuous_analyses_store[study_id] = {}

            base_path = self.file_service._get_study_path(study_id) / "Analisis Continuo"
            analysis_path = base_path / analysis_name
            analysis_path.mkdir(parents=True, exist_ok=True)
            
            config_file = analysis_path / "config_continuous.json"
            with open(config_file, 'w') as f_cfg: json.dump(config, f_cfg)
            
            plot_file = analysis_path / "spm_plot.png"
            plot_file.touch()

            self.continuous_analyses_store[study_id][analysis_name] = {
                'name': analysis_name, 'path': analysis_path, 'config': config,
                'mtime': datetime.now().timestamp(),
                'plot_path': plot_file,
                'spm_results_path': analysis_path / "spm_results.json"
            }
            return {"status": "success", "message": "Análisis dummy completado.", "output_dir": str(analysis_path)}

        # Métodos necesarios para ContinuousAnalysisConfigDialog
        def get_available_frequencies_for_study(self, study_id): return ["Cinematica"]
        def get_data_columns_for_frequency(self, study_id, frequency):
            return ["LAnkleAngles/X/deg", "RKneeAngles/Y/deg", "LHipForce/Z/N"]
        def get_filtered_discrete_analysis_groups(self, study_id, frequency, mode, primary_vi_name=None, fixed_vi_name=None, fixed_descriptor_value=None):
            if mode == "1VI":
                return {f"{primary_vi_name}=A": f"{primary_vi_name}: A", f"{primary_vi_name}=B": f"{primary_vi_name}: B"}
            elif mode == "2VIs":
                 # Clave original : Display name
                return {f"VarVI=X;{fixed_vi_name}={fixed_descriptor_value}": f"VarVI: X",
                        f"VarVI=Y;{fixed_vi_name}={fixed_descriptor_value}": f"VarVI: Y"}
            return {}


    class DummyMainWindow:
        def __init__(self, root_window):
            self.root = root_window
            self.study_service = DummyStudyService() # Necesario para get_study_aliases
            self.file_service = DummyFileService() # Necesario para _get_study_path

        def show_study_view(self, study_id):
            print(f"DummyMainWindow: Navegando a StudyView para estudio {study_id}")
            # En una app real, esto limpiaría y mostraría la StudyView
            # Para la prueba, podemos simplemente cerrar la vista actual si existe
            if hasattr(root, "current_view_for_test") and root.current_view_for_test:
                root.current_view_for_test.destroy()
            # Y quizás reabrir una landing page o algo así
            ttk.Label(root, text=f"Volvió a Estudio {study_id} (Simulado)").pack()


        def open_folder(self, folder_path_str):
            folder_path = Path(folder_path_str)
            print(f"DummyMainWindow: Solicitado abrir carpeta: {folder_path}")
            if folder_path.exists():
                if sys.platform == "win32": os.startfile(folder_path)
                elif sys.platform == "darwin": subprocess.run(["open", folder_path], check=True)
                else: subprocess.run(["xdg-open", folder_path], check=True)
            else:
                print(f"DummyMainWindow: Carpeta no encontrada: {folder_path}")


    dummy_main_window = DummyMainWindow(root)
    dummy_analysis_service = DummyAnalysisService()
    test_study_id = 1

    # Limpiar directorio de prueba si existe de ejecuciones anteriores
    test_study_path = dummy_analysis_service.file_service._get_study_path(test_study_id)
    if (test_study_path / "Analisis Continuo").exists():
        import shutil
        shutil.rmtree(test_study_path / "Analisis Continuo")

    # Crear la vista
    app_view = ContinuousAnalysisView(root, dummy_main_window, dummy_analysis_service, test_study_id)
    root.current_view_for_test = app_view # Para que el dummy_main_window pueda "cerrarla"

    root.mainloop()
