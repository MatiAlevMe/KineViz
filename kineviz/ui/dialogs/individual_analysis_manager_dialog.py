import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path
import os
import sys
import subprocess
from datetime import datetime # Para formatear fecha
import numpy as np # Importar numpy
import webbrowser # Para abrir HTML

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
        self.grab_set()  # Hacer modal

        self.analysis_list = []  # Lista de dicts con info de análisis guardados
        self.analysis_tree = None
        # Añadir "Valores Clave"
        self.columns = ("Nombre", "Fecha", "Frecuencia", "Cálculo",
                        "Columna Analizada", "Supuestos", "Valores Clave",
                        "Grupos Comparados")

        self.create_widgets()
        self.load_analyses()

    def create_widgets(self):
        """Crea los widgets del diálogo."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(1, weight=1)  # Permitir que el treeview se expanda
        main_frame.columnconfigure(0, weight=1)

        # --- Acciones ---
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(action_frame, text="Nuevo Análisis...",
                   command=self.open_new_analysis_dialog) \
            .pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Ver/Abrir Gráfico",
                   command=self.view_analysis_plot) \
            .pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Eliminar Análisis",
                   command=self.delete_analysis) \
            .pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Abrir Carpeta",
                    command=self.open_analysis_folder) \
             .pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Ver Gráfico Interactivo",
                   command=self.view_interactive_plot) \
            .pack(side=tk.LEFT, padx=5)
        # TODO: Añadir búsqueda/filtrado si es necesario

        # --- Lista de Análisis (Treeview) ---
        tree_frame = ttk.LabelFrame(main_frame, text="Análisis Guardados")
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Columnas definidas en __init__
        self.analysis_tree = ttk.Treeview(
            tree_frame,
            columns=self.columns, # Usar self.columns
            show="headings"
        )
        self.analysis_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Cabeceras iniciales
        self.analysis_tree.heading("Nombre", text="Nombre Análisis")
        self.analysis_tree.heading("Fecha", text="Fecha Creación")
        self.analysis_tree.heading("Frecuencia", text="Frecuencia")
        self.analysis_tree.heading("Cálculo", text="Cálculo")
        self.analysis_tree.heading("Columna Analizada", text="Columna")
        self.analysis_tree.heading("Supuestos", text="Supuestos")
        # Añadir cabecera para Valores Clave
        self.analysis_tree.heading("Valores Clave", text="Resultado Test")
        self.analysis_tree.heading("Grupos Comparados", text="Grupos Comparados") # Renombrar Descriptores

        # Ancho columnas (ajustar según necesidad)
        self.analysis_tree.column("Nombre", width=150, anchor=tk.W)
        self.analysis_tree.column("Fecha", width=140, anchor=tk.CENTER)
        self.analysis_tree.column("Frecuencia", width=80, anchor=tk.W)
        self.analysis_tree.column("Cálculo", width=80, anchor=tk.W)
        self.analysis_tree.column("Columna Analizada", width=150, anchor=tk.W)
        self.analysis_tree.column("Supuestos", width=140, anchor=tk.W)
        # Añadir ancho para Valores Clave
        self.analysis_tree.column("Valores Clave", width=120, anchor=tk.W)
        self.analysis_tree.column("Grupos Comparados", width=250, anchor=tk.W) # Renombrar Descriptores

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.analysis_tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        self.analysis_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.analysis_tree.xview)
        hsb.grid(row=1, column=0, sticky='ew', padx=5) # Añadir padx
        self.analysis_tree.configure(xscrollcommand=hsb.set)

        # --- Botón Cerrar ---
        ttk.Button(main_frame, text="Cerrar", command=self.destroy) \
            .grid(row=2, column=0, sticky="e", pady=(10, 0))

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

        # Asegurar que todos los encabezados estén definidos
        # (Importante si se reabre el diálogo y las columnas cambiaron)
        self.analysis_tree["columns"] = self.columns
        for col in self.columns:
            # Usar el texto del encabezado ya definido si existe, si no, usar el ID
            header_text = self.analysis_tree.heading(col, 'text') or col
            self.analysis_tree.heading(col, text=header_text)

        # Poblar Treeview
        if not self.analysis_list:
                # Crear valores vacíos para todas las columnas
                # Ajustar el mensaje para que quepa en la primera columna
                num_empty_cols = len(self.columns) - 1
                empty_values = tuple(["No hay análisis guardados."] + [""] * num_empty_cols)
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
                supuestos_str = (f"{'Pareado' if paired else 'No Pareado'}, "
                                 f"{'Paramétrico' if parametric else 'No Paramétrico'}")

                # Resultado Test (Valores Clave)
                stats_results = config.get('stats_results')
                valores_clave_str = "N/A"
                if stats_results:
                    test_name = stats_results.get('test_name', 'Test')
                    p_value = stats_results.get('p_value')
                    # Usar isnan para verificar NaN de forma segura
                    if p_value is not None and not isinstance(p_value, str) and not np.isnan(p_value): # Check for NaN
                         # Formatear p-valor
                        if p_value < 0.001: p_text = "p < 0.001"
                        else: p_text = f"p = {p_value:.3f}"
                        valores_clave_str = f"{test_name}: {p_text}"
                    elif p_value is not None: # Podría ser NaN
                         valores_clave_str = f"{test_name}: p=NaN"
                    else: # p_value es None
                         valores_clave_str = f"{test_name}: N/A"
                elif 'test_name' in config: # Compatibilidad con configs antiguas sin p-valor
                    valores_clave_str = f"{config.get('test_name', 'Test')}: ?"


                # Grupos (con alias, usando claves nuevas)
                group_keys = config.get('groups', []) # Claves originales "VI=Desc;..."
                group_display_names = []
                # Obtener alias una vez
                study_aliases = self.analysis_service.study_service.get_study_aliases(self.study_id)
                for group_key in group_keys:
                    display_parts = []
                    if group_key != "SinGrupo":
                        for part in group_key.split(';'):
                            vi_name, desc_value = part.split('=', 1)
                            alias = study_aliases.get(desc_value, desc_value)
                            display_parts.append(f"{vi_name}: {alias}")
                    display_name = ", ".join(display_parts) if display_parts else "Grupo General"
                    group_display_names.append(display_name)

                # Unir nombres de grupo legibles para la columna "Grupos Comparados"
                grupos_comparados_str = " vs ".join(group_display_names)

                # Construir tupla de valores para insertar
                values = (
                    analysis_name,
                    date_str,
                    freq,
                    calc,
                    col_full,
                    supuestos_str,
                    valores_clave_str, # Añadir valores clave
                    grupos_comparados_str # Añadir string de grupos
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
        logger.error(f"No se encontró información para análisis seleccionado: "
                      f"{analysis_name}")
        return None  # No debería ocurrir si la lista está sincronizada

    def view_interactive_plot(self):
        """Abre el gráfico HTML interactivo del análisis seleccionado."""
        analysis_info = self.get_selected_analysis_info()
        if not analysis_info:
            return

        # Buscar la ruta interactiva en la info cargada
        interactive_plot_path_obj = analysis_info.get('interactive_plot_path')

        if not interactive_plot_path_obj or not interactive_plot_path_obj.exists():
            messagebox.showwarning("No Disponible",
                                   f"No se encontró archivo de gráfico interactivo "
                                   f"para '{analysis_info['name']}'.\n"
                                   f"(Es posible que Plotly no esté instalado o "
                                   f"haya fallado la generación).", parent=self)
            return

        try:
            # Convertir Path a string y luego a URL file://
            interactive_plot_url = interactive_plot_path_obj.as_uri()
            logger.info(f"Intentando abrir gráfico interactivo: {interactive_plot_url}")
            webbrowser.open(interactive_plot_url, new=2) # new=2: nueva pestaña si es posible
        except Exception as e:
            logger.error(f"Error abriendo gráfico interactivo para {analysis_info['name']}: "
                         f"{e}", exc_info=True)
            messagebox.showerror("Error al Abrir",
                                   f"No se pudo abrir el gráfico interactivo:\n{e}",
                                   parent=self)

    def view_analysis_plot(self):
        """Abre el gráfico PNG del análisis seleccionado."""
        analysis_info = self.get_selected_analysis_info()
        if not analysis_info:
            return

        plot_path = analysis_info.get('plot_path')  # Obtener ruta del gráfico

        if not plot_path or not plot_path.exists():
            messagebox.showerror("Error",
                                   f"No se encontró archivo de gráfico para "
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
            logger.error(f"Error al intentar eliminar análisis "
                         f"{analysis_name}: {e}")
            messagebox.showerror("Error al Eliminar", f"{e}", parent=self)
            self.load_analyses()  # Recargar por si el estado cambió
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

        analysis_dir = analysis_info.get('path')  # Obtener ruta del directorio

        if not analysis_dir or not analysis_dir.exists():
            messagebox.showerror("Error",
                                   f"No se encontró carpeta para análisis "
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
        # Añadir study_service dummy para get_study_aliases
        def __init__(self):
            class DummyStudyService:
                 def get_study_aliases(self, study_id):
                     print(f"DummyStudyService: get_study_aliases({study_id})")
                     return {'CMJ': 'Salto CM', 'PRE': 'Antes', 'POST': 'Despues',
                             'SJ_TipoA': 'SJ A', 'SJ_TipoB': 'SJ B', 'SJ_TipoC': 'SJ C'}
            self.study_service = DummyStudyService()

        def list_individual_analyses(self, study_id):
            print(f"Dummy: list_individual_analyses({study_id})")
            # Simular algunos análisis con plot_path e interactive_plot_path
            base = Path(f'/fake/study_{study_id}/Analisis Discreto/Individual')
            analysis1_path = base / 'Comp_Costo_Mortal_Antes_Despues' # Usar alias
            analysis2_path = base / 'Comp_SJ_Tipos'
            analysis3_path = base / 'Sin_Plotly' # Simular uno sin HTML
            # Simular claves de grupo con formato VI=Desc
            return [
                {'name': 'Comp_SaltoCM_Cond', 'path': analysis1_path,
                 'config': {'calculation': 'Maximo',
                            'column': 'H Salto/Alt/cm',
                            'groups': ['Tipo=CMJ;Cond=PRE', 'Tipo=CMJ;Cond=POST'], # Claves nuevas
                            'parametric': True, 'paired': True,
                            'stats_results': {'test_name': 'T-test rel.', 'p_value': 0.0005}},
                 'mtime': 1678886400.0,
                 'plot_path': analysis1_path / 'boxplot.png',
                 'interactive_plot_path': analysis1_path / 'boxplot_interactive.html'},
                {'name': 'Comp_SJ_Tipos', 'path': analysis2_path,
                 'config': {'calculation': 'Rango',
                            'column': 'Art1/VelX/m/s',
                            'groups': ['Tipo=SJ;Cond=TipoA', 'Tipo=SJ;Cond=TipoB', 'Tipo=SJ;Cond=TipoC'], # Claves nuevas
                            'parametric': False, 'paired': False,
                            'stats_results': {'test_name': 'Kruskal', 'p_value': 0.06}},
                 'mtime': 1678972800.0,
                 'plot_path': analysis2_path / 'boxplot.png',
                 'interactive_plot_path': analysis2_path / 'boxplot_interactive.html'},
                 {'name': 'Sin_Plotly', 'path': analysis3_path,
                 'config': {'calculation': 'Minimo',
                            'column': 'Art2/PosY/mm',
                            'groups': ['Cond=PRE', 'Cond=POST'], # Asumiendo solo una VI 'Cond'
                            'parametric': True, 'paired': False,
                            'stats_results': {'test_name': 'T-test indep.', 'p_value': 0.87}},
                 'mtime': 1678999999.0,
                 'plot_path': analysis3_path / 'boxplot.png',
                 'interactive_plot_path': None},
            ]

        # Los dummies de get_discrete_analysis_groups y get_common_columns_for_groups
        # ya están en ConfigureIndividualAnalysisDialog, no se necesitan aquí.

        def delete_individual_analysis(self, study_id, analysis_name):
            print(f"Dummy: get_common_columns_for_groups({study_id}, "
                  f"{frequency}, {calculation}, {group_keys})")
            return ['Art1/PosX/mm', 'Art1/PosY/mm', 'Art2/VelX/m/s',
                    'H Salto/Alt/cm']

        def perform_individual_analysis(self, study_id, config):
            print(f"Dummy: perform_individual_analysis({study_id}, {config})")
            # Simular éxito y devolver ambas rutas
            fake_path = Path(f'/fake/study_{study_id}/Analisis Discreto/'
                             f'Individual/{config["name"]}')
            # Asegurarse que el dummy devuelva la ruta interactiva
            return {'plot_path': str(fake_path / 'boxplot.png'),
                    'config_path': str(fake_path / 'config.json'),
                    'interactive_plot_path': str(fake_path / 'boxplot_interactive.html')}


        def delete_individual_analysis(self, study_id, analysis_name):
            print(f"Dummy: delete_individual_analysis({study_id}, "
                  f"{analysis_name})")
            # Simular éxito

    # --- Ejecutar Diálogo ---
    dummy_service = DummyAnalysisService()
    dialog = IndividualAnalysisManagerDialog(root, dummy_service, 1)
    root.mainloop()
