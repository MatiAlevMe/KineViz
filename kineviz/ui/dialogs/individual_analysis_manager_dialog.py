import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
import os
import sys
import subprocess
from datetime import datetime # Para formatear fecha

# Importar servicios y otros diálogos necesarios
from kineviz.core.services.analysis_service import AnalysisService
from kineviz.ui.dialogs.configure_individual_analysis_dialog import ConfigureIndividualAnalysisDialog


logger = logging.getLogger(__name__)


class IndividualAnalysisManagerDialog(tk.Toplevel):
    """Diálogo para gestionar (listar, crear, eliminar) análisis individuales."""

    def __init__(self, parent, analysis_service: AnalysisService, study_id: int):
        super().__init__(parent)
        self.parent = parent
        self.analysis_service = analysis_service
        self.study_id = study_id

        self.title(f"Gestor de Análisis Individuales - Estudio {study_id}")
        self.geometry("800x500")
        # self.grab_set() # Hacer modal

        self.analysis_list = [] # Lista de dicts con info de análisis guardados
        self.analysis_tree = None

        self.create_widgets()
        self.load_analyses()

    def create_widgets(self):
        """Crea los widgets del diálogo."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(1, weight=1) # Permitir que el treeview se expanda
        main_frame.columnconfigure(0, weight=1)

        # --- Acciones ---
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(action_frame, text="Nuevo Análisis...", command=self.open_new_analysis_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Ver/Abrir Gráfico", command=self.view_analysis_plot).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Eliminar Análisis", command=self.delete_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Abrir Carpeta", command=self.open_analysis_folder).pack(side=tk.LEFT, padx=5)
        # TODO: Añadir búsqueda/filtrado si es necesario

        # --- Lista de Análisis (Treeview) ---
        tree_frame = ttk.LabelFrame(main_frame, text="Análisis Guardados")
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Definir columnas iniciales (Grupos se añadirán dinámicamente si es necesario)
        self.columns = ("Nombre", "Fecha", "Frecuencia", "Cálculo",
                        "Columna Analizada", "Supuestos")
        self.analysis_tree = ttk.Treeview(
            tree_frame,
            columns=self.columns,
            show="headings"
        )
        self.analysis_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Cabeceras iniciales
        self.analysis_tree.heading("Nombre", text="Nombre Análisis")
        self.analysis_tree.heading("Fecha", text="Fecha Creación")
        self.analysis_tree.heading("Frecuencia", text="Frecuencia")
        self.analysis_tree.heading("Cálculo", text="Cálculo")
        self.analysis_tree.heading("Columna Analizada", text="Columna Analizada")
        self.analysis_tree.heading("Supuestos", text="Supuestos")

        # Ancho columnas iniciales (ajustar según necesidad)
        self.analysis_tree.column("Nombre", width=180, anchor=tk.W)
        self.analysis_tree.column("Fecha", width=140, anchor=tk.CENTER)
        self.analysis_tree.column("Frecuencia", width=80, anchor=tk.W)
        self.analysis_tree.column("Cálculo", width=80, anchor=tk.W)
        self.analysis_tree.column("Columna Analizada", width=150, anchor=tk.W)
        self.analysis_tree.column("Supuestos", width=150, anchor=tk.W)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.analysis_tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        self.analysis_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.analysis_tree.xview)
        hsb.grid(row=1, column=0, sticky='ew')
        self.analysis_tree.configure(xscrollcommand=hsb.set)

        # --- Botón Cerrar ---
        ttk.Button(main_frame, text="Cerrar", command=self.destroy).grid(row=2, column=0, sticky="e", pady=(10, 0))


    def load_analyses(self):
        """Carga la lista de análisis individuales guardados."""
        # Limpiar treeview
        for item in self.analysis_tree.get_children():
            self.analysis_tree.delete(item)

        try:
            self.analysis_list = self.analysis_service.list_individual_analyses(self.study_id)
        except Exception as e:
             logger.error(f"Error cargando lista de análisis individuales: {e}", exc_info=True)
             messagebox.showerror("Error", f"No se pudo cargar la lista de análisis:\n{e}", parent=self)
             self.analysis_list = []

        # Determinar el número máximo de grupos para añadir columnas dinámicas
        max_groups = 0
        if self.analysis_list:
            max_groups = max(len(a.get('config', {}).get('groups', [])) for a in self.analysis_list)
            max_groups = max(2, max_groups) # Mínimo 2 grupos si hay análisis

        # Añadir columnas de grupo dinámicamente si es necesario
        group_cols = [f"Grupo {i+1}" for i in range(max_groups)]
        current_cols = list(self.columns)
        new_cols = tuple(current_cols + group_cols)
        if self.analysis_tree["columns"] != new_cols:
             self.analysis_tree["columns"] = new_cols
             for i, g_col in enumerate(group_cols):
                  self.analysis_tree.heading(g_col, text=g_col)
                  self.analysis_tree.column(g_col, width=120, anchor=tk.W) # Ajustar ancho

        # Poblar Treeview
        if not self.analysis_list:
            # Crear valores vacíos para todas las columnas
            num_cols = len(self.analysis_tree["columns"])
            empty_values = tuple(["No hay análisis individuales guardados."] + [""] * (num_cols - 1))
            self.analysis_tree.insert("", tk.END, text="NoAnalyses",
                                      values=empty_values)
        else:
            for analysis_info in self.analysis_list:
                config = analysis_info.get('config', {})
                analysis_name = analysis_info.get('name', 'N/A')

                # Fecha
                date_str = "N/A"
                if 'mtime' in analysis_info:
                    date_str = datetime.fromtimestamp(
                        analysis_info['mtime']
                    ).strftime('%Y-%m-%d %H:%M:%S')

                # Frecuencia, Cálculo, Columna
                freq = config.get('frequency', '?')
                calc = config.get('calculation', '?')
                col_full = config.get('column', '?')

                # Supuestos
                parametric = config.get('parametric', True)
                paired = config.get('paired', False)
                supuestos_str = f"{'Pareado' if paired else 'No Pareado'}, {'Paramétrico' if parametric else 'No Paramétrico'}"

                # Grupos (con alias)
                group_keys = config.get('groups', [])
                group_display_names = []
                for g_key in group_keys:
                    parts = g_key.split('_')
                    aliased_parts = [self.analysis_service.settings.get_descriptor_alias(p) or p for p in parts]
                    display_name = ', '.join(aliased_parts) if g_key != "SinDescriptores" else "Sin Descriptores"
                    group_display_names.append(display_name)

                # Rellenar con "" si hay menos grupos que max_groups
                group_display_names.extend([""] * (max_groups - len(group_display_names)))

                # Construir tupla de valores para insertar
                values = (
                    analysis_name,
                    date_str,
                    freq,
                    calc,
                    col_full,
                    supuestos_str,
                    *group_display_names # Desempaquetar nombres de grupo
                )

                # Insertar en Treeview
                self.analysis_tree.insert(
                    "", tk.END,
                    text=analysis_name,  # Guardar nombre para identificar
                    values=values
                )

    def open_new_analysis_dialog(self):
        """Abre el diálogo para configurar un nuevo análisis."""
        dialog = ConfigureIndividualAnalysisDialog(self, self.analysis_service, self.study_id)
        # Esperar a que el diálogo se cierre y luego refrescar la lista
        self.wait_window(dialog)
        self.load_analyses()  # Recargar por si se creó uno nuevo

    def get_selected_analysis_info(self) -> dict | None:
        """Obtiene el diccionario de información del análisis seleccionado."""
        selected_item = self.analysis_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección",
                                   "Seleccione un análisis de la lista.",
                                   parent=self)
            return None
        analysis_name = self.analysis_tree.item(selected_item, "text")
        if analysis_name == "NoAnalyses":  # Verificar si es el placeholder
            messagebox.showwarning("Sin Selección",
                                   "No hay un análisis válido seleccionado.",
                                   parent=self)
            return None

        # Buscar la info completa en self.analysis_list
        for analysis_info in self.analysis_list:
            if analysis_info['name'] == analysis_name:
                return analysis_info
        logger.error(f"No se encontró la información para el análisis "
                     f"seleccionado: {analysis_name}")
        return None # No debería ocurrir si la lista está sincronizada

    def view_analysis_plot(self):
        """Abre el gráfico PNG del análisis seleccionado."""
        analysis_info = self.get_selected_analysis_info()
        if not analysis_info:
            return

        plot_path = analysis_info.get('plot_path') # Obtener ruta del gráfico

        if not plot_path or not plot_path.exists():
            messagebox.showerror("Error",
                                   f"No se encontró el archivo de gráfico para "
                                   f"'{analysis_info['name']}'.", parent=self)
            return

        try:
            logger.info(f"Intentando abrir gráfico: {plot_path}")
            if sys.platform == "win32":
                os.startfile(plot_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", plot_path], check=True)
            else:  # linux variants
                subprocess.run(["xdg-open", plot_path], check=True)
        except Exception as e:
            logger.error(f"Error abriendo gráfico para {analysis_info['name']}: "
                         f"{e}", exc_info=True)
            messagebox.showerror("Error al Abrir",
                                   f"No se pudo abrir el gráfico:\n{e}",
                                   parent=self)

    def delete_analysis(self):
        """Elimina el análisis seleccionado (carpeta y contenido)."""
        analysis_info = self.get_selected_analysis_info()
        if not analysis_info:
            return
        analysis_name = analysis_info['name']

        if not messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Está seguro de que desea eliminar permanentemente el "
                f"análisis '{analysis_name}' y todos sus archivos?",
                parent=self):
            return

        try:
            self.analysis_service.delete_individual_analysis(self.study_id,
                                                             analysis_name)
            messagebox.showinfo("Eliminación Exitosa",
                                f"El análisis '{analysis_name}' ha sido eliminado.",
                                parent=self)
            self.load_analyses()  # Recargar lista
        except (ValueError, FileNotFoundError) as e:
             logger.error(f"Error al intentar eliminar análisis {analysis_name}: {e}")
             messagebox.showerror("Error al Eliminar", f"{e}", parent=self)
             self.load_analyses() # Recargar por si el estado cambió
        except Exception as e:
            logger.error(f"Error eliminando análisis {analysis_name}: {e}",
                         exc_info=True)
            messagebox.showerror("Error al Eliminar",
                                   f"No se pudo eliminar el análisis:\n{e}",
                                   parent=self)

    def open_analysis_folder(self):
        """Abre la carpeta que contiene los archivos del análisis."""
        analysis_info = self.get_selected_analysis_info()
        if not analysis_info:
            return

        analysis_dir = analysis_info.get('path') # Obtener ruta del directorio

        if not analysis_dir or not analysis_dir.exists():
            messagebox.showerror("Error",
                                   f"No se encontró la carpeta para el análisis "
                                   f"'{analysis_info['name']}'.", parent=self)
            return

        try:
            logger.info(f"Intentando abrir carpeta: {analysis_dir}")
            if sys.platform == "win32":
                os.startfile(analysis_dir)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", analysis_dir], check=True)
            else:  # linux variants
                subprocess.run(["xdg-open", analysis_dir], check=True)
        except Exception as e:
            logger.error(f"Error abriendo carpeta para {analysis_info['name']}: "
                         f"{e}", exc_info=True)
            messagebox.showerror("Error al Abrir",
                                   f"No se pudo abrir la carpeta:\n{e}",
                                   parent=self)


# Para pruebas rápidas
if __name__ == '__main__':
    # Necesitamos Path para el dummy
    from pathlib import Path
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal

    # --- Dummies ---
    class DummyAnalysisService:
        # Añadir settings dummy para get_discrete_analysis_groups
        def __init__(self):
            class DummySettings:
                def get_descriptor_alias(self, desc):
                    return {'CMJ': 'Salto CM', 'PRE': 'Antes',
                            'POST': 'Despues'}.get(desc)
            self.settings = DummySettings()

        def list_individual_analyses(self, study_id):
            print(f"Dummy: list_individual_analyses({study_id})")
            # Simular algunos análisis con plot_path
            base = Path(f'/fake/study_{study_id}/Analisis Discreto/Individual')
            analysis1_path = base / 'Comp_CMJ_PRE_POST'
            analysis2_path = base / 'Comp_SJ_Tipos'
            return [
                {'name': 'Comp_CMJ_PRE_POST', 'path': analysis1_path,
                 'config': {'calculation': 'Maximo', 'column': 'H Salto/Alt/cm',
                            'groups': ['CMJ_PRE', 'CMJ_POST']},
                 'mtime': 1678886400.0, 'plot_path': analysis1_path / 'boxplot.png'},
                {'name': 'Comp_SJ_Tipos', 'path': analysis2_path,
                 'config': {'calculation': 'Rango', 'column': 'Art1/VelX/m/s',
                            'groups': ['SJ_TipoA', 'SJ_TipoB', 'SJ_TipoC']},
                 'mtime': 1678972800.0, 'plot_path': analysis2_path / 'boxplot.png'},
            ]

        def get_discrete_analysis_groups(self, study_id, frequency):
            print(f"Dummy: get_discrete_analysis_groups({study_id}, {frequency})")
            return ['CMJ_PRE', 'CMJ_POST', 'SJ_TipoA', 'SJ_TipoB', 'SJ_TipoC',
                    'SinDescriptores']
        def get_common_columns_for_groups(self, study_id, frequency,
                                          calculation, group_keys):
            print(f"Dummy: get_common_columns_for_groups({study_id}, "
                  f"{frequency}, {calculation}, {group_keys})")
            return ['Art1/PosX/mm', 'Art1/PosY/mm', 'Art2/VelX/m/s',
                    'H Salto/Alt/cm']

        def perform_individual_analysis(self, study_id, config):
            print(f"Dummy: perform_individual_analysis({study_id}, {config})")
            # Simular éxito
            fake_path = Path(f'/fake/study_{study_id}/Analisis Discreto/'
                             f'Individual/{config["name"]}')
            return {'plot_path': str(fake_path / 'boxplot.png'),
                    'config_path': str(fake_path / 'config.json')}

        def delete_individual_analysis(self, study_id, analysis_name):
            print(f"Dummy: delete_individual_analysis({study_id}, "
                  f"{analysis_name})")
            # Simular éxito

    # --- Ejecutar Diálogo ---
    dummy_service = DummyAnalysisService()
    dialog = IndividualAnalysisManagerDialog(root, dummy_service, 1)
    root.mainloop()
