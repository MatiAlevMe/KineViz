import tkinter as tk
from tkinter import ttk, messagebox
import logging
from pathlib import Path

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

        self.analysis_tree = ttk.Treeview(
            tree_frame,
            columns=("Nombre", "Fecha", "Parámetros"), # Añadir más columnas si es útil
            show="headings"
        )
        self.analysis_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Cabeceras
        self.analysis_tree.heading("Nombre", text="Nombre")
        self.analysis_tree.heading("Fecha", text="Fecha Creación")
        self.analysis_tree.heading("Parámetros", text="Parámetros Clave")

        # Ancho columnas
        self.analysis_tree.column("Nombre", width=200, anchor=tk.W)
        self.analysis_tree.column("Fecha", width=150, anchor=tk.CENTER)
        self.analysis_tree.column("Parámetros", width=350, anchor=tk.W)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.analysis_tree.yview)
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

        # TODO: Implementar self.analysis_service.list_individual_analyses(self.study_id)
        # Esta función debería devolver una lista de diccionarios, cada uno con:
        # {'name': str, 'path': Path (directorio del análisis), 'config': dict, 'mtime': float}
        logger.warning("Funcionalidad 'load_analyses' aún no implementada en AnalysisService.")
        self.analysis_list = [] # Placeholder

        if not self.analysis_list:
            self.analysis_tree.insert("", tk.END, text="NoAnalyses", values=("No hay análisis individuales guardados.", "", ""))
        else:
            for analysis_info in self.analysis_list:
                # Extraer info relevante de config para mostrar
                config = analysis_info.get('config', {})
                params_str = f"Calc: {config.get('calculation', '?')}, Col: {config.get('column', '?')}, Grupos: {len(config.get('groups', []))}"
                # Usar mtime del archivo config.json o del directorio
                date_str = "N/A" # Placeholder
                if 'mtime' in analysis_info:
                     from datetime import datetime
                     date_str = datetime.fromtimestamp(analysis_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')

                # Usar el nombre del análisis como ID interno (text)
                self.analysis_tree.insert(
                    "", tk.END,
                    text=analysis_info['name'], # Guardar nombre para identificar selección
                    values=(
                        analysis_info['name'],
                        date_str,
                        params_str
                    )
                )

    def open_new_analysis_dialog(self):
        """Abre el diálogo para configurar un nuevo análisis."""
        dialog = ConfigureIndividualAnalysisDialog(self, self.analysis_service, self.study_id)
        # Esperar a que el diálogo se cierre y luego refrescar la lista
        self.wait_window(dialog)
        self.load_analyses() # Recargar por si se creó uno nuevo

    def get_selected_analysis_name(self) -> str | None:
        """Obtiene el nombre del análisis seleccionado en el Treeview."""
        selected_item = self.analysis_tree.focus()
        if not selected_item:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un análisis de la lista.", parent=self)
            return None
        analysis_name = self.analysis_tree.item(selected_item, "text")
        if analysis_name == "NoAnalyses": # Verificar si es el mensaje placeholder
             messagebox.showwarning("Sin Selección", "No hay un análisis válido seleccionado.", parent=self)
             return None
        return analysis_name

    def view_analysis_plot(self):
        """Abre el gráfico PNG del análisis seleccionado."""
        analysis_name = self.get_selected_analysis_name()
        if not analysis_name: return

        # TODO: Necesitamos la ruta al archivo PNG. Esto debería venir de list_individual_analyses
        # o construirse a partir del nombre y la ruta base del estudio.
        logger.warning("Funcionalidad 'view_analysis_plot' aún no implementada.")
        messagebox.showinfo("Pendiente", "Abrir gráfico aún no implementado.", parent=self)
        # Ejemplo futuro:
        # try:
        #     plot_path = self.analysis_service.get_individual_analysis_plot_path(self.study_id, analysis_name)
        #     if plot_path and plot_path.exists():
        #         # Usar lógica de apertura de archivo como en DiscreteAnalysisView.view_table
        #         import os, sys, subprocess
        #         if sys.platform == "win32": os.startfile(plot_path)
        #         elif sys.platform == "darwin": subprocess.run(["open", plot_path], check=True)
        #         else: subprocess.run(["xdg-open", plot_path], check=True)
        #     else:
        #         messagebox.showerror("Error", f"No se encontró el archivo de gráfico para '{analysis_name}'.", parent=self)
        # except Exception as e:
        #     logger.error(f"Error abriendo gráfico para {analysis_name}: {e}", exc_info=True)
        #     messagebox.showerror("Error al Abrir", f"No se pudo abrir el gráfico:\n{e}", parent=self)


    def delete_analysis(self):
        """Elimina el análisis seleccionado (carpeta y contenido)."""
        analysis_name = self.get_selected_analysis_name()
        if not analysis_name: return

        if not messagebox.askyesno("Confirmar Eliminación",
                                   f"¿Está seguro de que desea eliminar permanentemente el análisis '{analysis_name}' y todos sus archivos?",
                                   parent=self):
            return

        # TODO: Implementar self.analysis_service.delete_individual_analysis(self.study_id, analysis_name)
        logger.warning("Funcionalidad 'delete_analysis' aún no implementada en AnalysisService.")
        messagebox.showinfo("Pendiente", "Eliminar análisis aún no implementado.", parent=self)
        # Ejemplo futuro:
        # try:
        #     self.analysis_service.delete_individual_analysis(self.study_id, analysis_name)
        #     messagebox.showinfo("Eliminación Exitosa", f"El análisis '{analysis_name}' ha sido eliminado.", parent=self)
        #     self.load_analyses() # Recargar lista
        # except Exception as e:
        #     logger.error(f"Error eliminando análisis {analysis_name}: {e}", exc_info=True)
        #     messagebox.showerror("Error al Eliminar", f"No se pudo eliminar el análisis:\n{e}", parent=self)

    def open_analysis_folder(self):
        """Abre la carpeta que contiene los archivos del análisis seleccionado."""
        analysis_name = self.get_selected_analysis_name()
        if not analysis_name: return

        # TODO: Necesitamos la ruta a la carpeta del análisis.
        logger.warning("Funcionalidad 'open_analysis_folder' aún no implementada.")
        messagebox.showinfo("Pendiente", "Abrir carpeta de análisis aún no implementado.", parent=self)
        # Ejemplo futuro:
        # try:
        #     analysis_dir = self.analysis_service.get_individual_analysis_path(self.study_id, analysis_name)
        #     if analysis_dir and analysis_dir.exists():
        #         # Usar lógica de apertura de carpeta
        #         import os, sys, subprocess
        #         if sys.platform == "win32": os.startfile(analysis_dir)
        #         elif sys.platform == "darwin": subprocess.run(["open", analysis_dir], check=True)
        #         else: subprocess.run(["xdg-open", analysis_dir], check=True)
        #     else:
        #         messagebox.showerror("Error", f"No se encontró la carpeta para el análisis '{analysis_name}'.", parent=self)
        # except Exception as e:
        #     logger.error(f"Error abriendo carpeta para {analysis_name}: {e}", exc_info=True)
        #     messagebox.showerror("Error al Abrir", f"No se pudo abrir la carpeta:\n{e}", parent=self)

# Para pruebas rápidas
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw() # Ocultar ventana principal

    # --- Dummies ---
    class DummyAnalysisService:
        def list_individual_analyses(self, study_id):
            print(f"Dummy: list_individual_analyses({study_id})")
            # Simular algunos análisis
            return [
                {'name': 'Comp_CMJ_PRE_POST', 'path': Path(f'/fake/study_{study_id}/Analisis Discreto/Individual/Comp_CMJ_PRE_POST'),
                 'config': {'calculation': 'Maximo', 'column': 'H Salto', 'groups': ['CMJ_PRE', 'CMJ_POST']}, 'mtime': 1678886400.0},
                {'name': 'Comp_SJ_Tipos', 'path': Path(f'/fake/study_{study_id}/Analisis Discreto/Individual/Comp_SJ_Tipos'),
                 'config': {'calculation': 'Rango', 'column': 'V Max', 'groups': ['SJ_TipoA', 'SJ_TipoB', 'SJ_TipoC']}, 'mtime': 1678972800.0},
            ]
        def get_discrete_analysis_groups(self, study_id, frequency):
             print(f"Dummy: get_discrete_analysis_groups({study_id}, {frequency})")
             return ['CMJ_PRE', 'CMJ_POST', 'SJ_TipoA', 'SJ_TipoB', 'SJ_TipoC', 'SinDescriptores']
        def get_common_columns_for_groups(self, study_id, frequency, calculation, group_keys):
             print(f"Dummy: get_common_columns_for_groups({study_id}, {frequency}, {calculation}, {group_keys})")
             return ['Art1/PosX/mm', 'Art1/PosY/mm', 'Art2/VelX/m/s', 'H Salto/Alt/cm']
        def perform_individual_analysis(self, study_id, config):
             print(f"Dummy: perform_individual_analysis({study_id}, {config})")
             # Simular éxito
             fake_path = Path(f'/fake/study_{study_id}/Analisis Discreto/Individual/{config["name"]}')
             return {'plot_path': str(fake_path / 'boxplot.png'), 'config_path': str(fake_path / 'config.json')}
        def delete_individual_analysis(self, study_id, analysis_name):
             print(f"Dummy: delete_individual_analysis({study_id}, {analysis_name})")
             # Simular éxito

    # --- Ejecutar Diálogo ---
    dummy_service = DummyAnalysisService()
    dialog = IndividualAnalysisManagerDialog(root, dummy_service, 1)
    root.mainloop()
