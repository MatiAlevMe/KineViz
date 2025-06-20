import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, filedialog # Añadir filedialog
import os
import sys
import subprocess
import logging # Importar logging
from tkinter import Listbox, Scrollbar, Frame # Necesario para las listas
from pathlib import Path # Necesario para manejar rutas de reportes

# Importar AnalysisService para type hinting
from kineviz.core.services.analysis_service import AnalysisService

# Importar AppSettings para type hinting
from kineviz.config.settings import AppSettings

logger = logging.getLogger(__name__) # Logger para este módulo

class AnalysisDialog(Toplevel):
    def __init__(self, parent, analysis_service: AnalysisService, study_id: int, app_settings: AppSettings):
        """
        Inicializa el diálogo de análisis.

        :param parent: La ventana padre.
        :param analysis_service: Instancia de AnalysisService.
        :param study_id: ID del estudio a analizar.
        """
        super().__init__(parent)
        self.analysis_service = analysis_service
        self.study_id = study_id
        self.app_settings = app_settings # Guardar referencia a AppSettings
        self.available_params = {} # Para almacenar los parámetros disponibles
        self.descriptor_alias_map = {} # Para mapear display_name -> original_descriptor

        self.title(f"Análisis - Estudio ID: {study_id}")
        self.geometry("850x650") # Aumentar tamaño para acomodar listas
        self.resizable(True, True)

        # Cargar parámetros disponibles ANTES de crear widgets
        self.load_available_parameters()

        # --- Frame principal que contendrá el Canvas y Scrollbar ---
        container_frame = ttk.Frame(self)
        container_frame.pack(fill=tk.BOTH, expand=True)

        # --- Canvas y Scrollbar ---
        self.canvas = tk.Canvas(container_frame)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=self.canvas.yview)
        # Este frame interior contendrá todos los widgets originales
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Crear widgets dentro del scrollable_frame ---
        self.create_widgets(self.scrollable_frame) # Pasar el frame desplazable como padre

        # Centrar diálogo
        self.transient(parent)
        self.grab_set()
        # Código para centrar (opcional, similar a StudyDialog)
        # ...

    def create_widgets(self, parent_frame): # Aceptar el frame padre (scrollable_frame)
        """Crea los widgets del diálogo de análisis."""
        # Usar parent_frame en lugar de 'self' para los widgets principales
        main_frame = ttk.Frame(parent_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True) # main_frame ahora está dentro del scrollable_frame

        # --- Selección de Parámetros ---
        params_frame = ttk.Frame(main_frame)
        params_frame.pack(fill=tk.BOTH, expand=True)

        # Crear selectores para cada parámetro
        self.patient_selector = self._create_parameter_selector(params_frame, "Participantes", self.available_params.get('patients', set()))
        self.frequency_selector = self._create_parameter_selector(params_frame, "Tipos de Datos", self.available_params.get('frequencies', set()), use_alias=False)
        # Reemplazar selectores de tipo/periodo por sub-valor, indicando usar alias
        self.descriptor_selector = self._create_parameter_selector(params_frame, "Sub-valores", self.available_params.get('descriptors', set()), use_alias=True)
        self.calculation_selector = self._create_parameter_selector(params_frame, "Cálculos", self.available_params.get('calculations', set()), use_alias=False)

        # --- Botones de Acción ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Generar Reporte PDF", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        # ttk.Button(button_frame, text="Realizar Análisis", command=self.perform_analysis, state=tk.DISABLED).pack(side=tk.LEFT, padx=5) # Deshabilitado por ahora
        ttk.Button(button_frame, text="Cerrar", command=self.destroy).pack(side=tk.RIGHT)

        # --- Separador ---
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=15)

        # --- Gestión de Reportes Existentes ---
        reports_frame = ttk.LabelFrame(main_frame, text="Reportes Generados")
        reports_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Frame para la tabla de reportes
        report_table_frame = ttk.Frame(reports_frame)
        report_table_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        report_columns = ('Nombre', 'Fecha Modificación', 'Ver', 'Eliminar')
        self.report_tree = ttk.Treeview(report_table_frame, columns=report_columns, show='headings')

        self.report_tree.heading('Nombre', text='Nombre Archivo')
        self.report_tree.heading('Fecha Modificación', text='Fecha Modificación')
        self.report_tree.heading('Ver', text='Ver', anchor='center')
        self.report_tree.heading('Eliminar', text='Eliminar', anchor='center')

        self.report_tree.column('Nombre', width=350, stretch=tk.YES)
        self.report_tree.column('Fecha Modificación', width=150, anchor='center')
        self.report_tree.column('Ver', width=60, anchor='center', stretch=tk.NO)
        self.report_tree.column('Eliminar', width=80, anchor='center', stretch=tk.NO)

        report_scrollbar = ttk.Scrollbar(report_table_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=report_scrollbar.set)

        report_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.report_tree.bind('<ButtonRelease-1>', self.on_report_tree_click)

        # Botón para refrescar lista de reportes
        refresh_button = ttk.Button(reports_frame, text="Refrescar Lista", command=self.load_reports)
        refresh_button.pack(pady=5)

        # Cargar reportes iniciales
        self.load_reports()

    def load_available_parameters(self):
        """Carga los parámetros disponibles desde el servicio."""
        try:
            self.available_params = self.analysis_service.get_analysis_parameters(self.study_id)
        except Exception as e:
            logger.error(f"No se pudieron cargar los parámetros de análisis para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los parámetros de análisis: {e}", parent=self)
            self.available_params = {} # Asegurar que sea un diccionario vacío
        # Cargar mapa de alias para sub-valores
        self.descriptor_alias_map = {
            desc: self.app_settings.get_descriptor_alias(desc)
            for desc in self.available_params.get('descriptors', set())
        }

    def _create_parameter_selector(self, parent, title: str, available_items: set, use_alias: bool = False):
        """
        Crea un conjunto de widgets para seleccionar un parámetro.
        Si use_alias es True, muestra 'Alias (Sub-valor)' o 'Sub-valor'.
        """
        container = ttk.LabelFrame(parent, text=title)
        container.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5) # Usar TOP para apilar verticalmente

        # Frame para listas y botones
        frame = ttk.Frame(container)
        frame.pack(fill=tk.BOTH, expand=True)

        # Lista Izquierda (Disponibles)
        left_list_frame = ttk.Frame(frame)
        left_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ttk.Label(left_list_frame, text="Disponibles:").pack(anchor='w')
        available_listbox = Listbox(left_list_frame, selectmode=tk.EXTENDED, exportselection=False, height=5)
        available_scrollbar = Scrollbar(left_list_frame, orient=tk.VERTICAL, command=available_listbox.yview)
        available_listbox.configure(yscrollcommand=available_scrollbar.set)
        available_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        available_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Poblar lista ordenada, aplicando formato de alias si es necesario
        display_map = {} # Mapa local para display_name -> original_item
        for item in sorted(list(available_items)):
            display_name = item
            if use_alias and title == "Sub-valores": # Solo aplicar alias a sub-valores
                alias = self.descriptor_alias_map.get(item)
                if alias:
                    display_name = f"{alias} ({item})"
            available_listbox.insert(tk.END, display_name)
            display_map[display_name] = item # Guardar mapeo

        # Botones Centrales
        button_frame = ttk.Frame(frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(button_frame, text=">", width=3, command=lambda: self._move_items(available_listbox, selected_listbox)).pack(pady=2)
        ttk.Button(button_frame, text="<", width=3, command=lambda: self._move_items(selected_listbox, available_listbox)).pack(pady=2)
        ttk.Button(button_frame, text=">>", width=3, command=lambda: self._move_all_items(available_listbox, selected_listbox)).pack(pady=2)
        ttk.Button(button_frame, text="<<", width=3, command=lambda: self._move_all_items(selected_listbox, available_listbox)).pack(pady=2)

        # Lista Derecha (Seleccionados)
        right_list_frame = ttk.Frame(frame)
        right_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        ttk.Label(right_list_frame, text="Seleccionados:").pack(anchor='w')
        selected_listbox = Listbox(right_list_frame, selectmode=tk.EXTENDED, exportselection=False, height=5)
        selected_scrollbar = Scrollbar(right_list_frame, orient=tk.VERTICAL, command=selected_listbox.yview)
        selected_listbox.configure(yscrollcommand=selected_scrollbar.set)
        selected_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        selected_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Devolver las listas y el mapa de display para sub-valores
        return {'available': available_listbox, 'selected': selected_listbox, 'display_map': display_map if use_alias else None}

    def _move_items(self, source_listbox: Listbox, dest_listbox: Listbox):
        """Mueve los elementos seleccionados de una lista a otra."""
        selected_indices = source_listbox.curselection()
        # Obtener los nombres mostrados
        display_names_to_move = [source_listbox.get(i) for i in selected_indices]

        # Añadir a destino si no existe y ordenar (usando display names)
        current_dest_display_names = set(dest_listbox.get(0, tk.END))
        new_display_names_added = False
        for display_name in display_names_to_move:
            if display_name not in current_dest_display_names:
                dest_listbox.insert(tk.END, display_name)
                current_dest_display_names.add(display_name)
                new_display_names_added = True

        if new_display_names_added:
             # Ordenar lista destino por display name
             all_dest_display_names = sorted(list(current_dest_display_names))
             dest_listbox.delete(0, tk.END)
             for display_name in all_dest_display_names:
                 dest_listbox.insert(tk.END, display_name)

        # Eliminar de origen (iterar en reversa)
        for i in reversed(selected_indices):
            source_listbox.delete(i)

    def _move_all_items(self, source_listbox: Listbox, dest_listbox: Listbox):
         """Mueve todos los elementos de una lista a otra."""
         all_display_names = source_listbox.get(0, tk.END)
         current_dest_display_names = set(dest_listbox.get(0, tk.END))
         new_display_names_added = False

         for display_name in all_display_names:
             if display_name not in current_dest_display_names:
                 dest_listbox.insert(tk.END, display_name)
                 current_dest_display_names.add(display_name)
                 new_display_names_added = True

         if new_display_names_added:
             # Ordenar lista destino por display name
             all_dest_display_names = sorted(list(current_dest_display_names))
             dest_listbox.delete(0, tk.END)
             for display_name in all_dest_display_names:
                 dest_listbox.insert(tk.END, display_name)

         # Limpiar origen
         source_listbox.delete(0, tk.END)


    def _get_selected_parameters(self) -> dict:
        """
        Recolecta los parámetros seleccionados de las listas.
        Para sub-valores, extrae el valor original del display name.
        """
        selected_display_descriptors = self.descriptor_selector['selected'].get(0, tk.END)
        original_descriptors = []
        for display_name in selected_display_descriptors:
            # Extraer el sub-valor original (ej: "CMJ" de "Salto Contra Movimiento (CMJ)")
            # o usar el display_name si no hay paréntesis
            if '(' in display_name and display_name.endswith(')'):
                original = display_name.split('(')[-1][:-1]
                original_descriptors.append(original)
            else:
                original_descriptors.append(display_name) # Asumir que es el original si no hay alias

        return {
            'patients': list(self.patient_selector['selected'].get(0, tk.END)),
            'frequencies': list(self.frequency_selector['selected'].get(0, tk.END)),
            'descriptors': original_descriptors, # Usar lista de sub-valores originales
            'calculations': list(self.calculation_selector['selected'].get(0, tk.END)),
        }

    def perform_analysis(self):
        """Llama al servicio para realizar el análisis con los parámetros seleccionados."""
        selected_parameters = self._get_selected_parameters()

        # Validar selecciones
        valid_patients = selected_parameters.get('patients', [])
        if len(valid_patients) < 2:
             messagebox.showwarning("Validación Fallida", "Debe seleccionar al menos dos participantes con datos procesados válidos para realizar el análisis.", parent=self)
             return
        # Añadir más validaciones si es necesario (ej. al menos una frecuencia, etc.)
        if not selected_parameters.get('frequencies'):
             messagebox.showwarning("Validación Fallida", "Debe seleccionar al menos una frecuencia.", parent=self)
             return
        if not selected_parameters.get('calculations'):
             messagebox.showwarning("Validación Fallida", "Debe seleccionar al menos un cálculo.", parent=self)
             return

        try:
            # Llamar al servicio con los parámetros recolectados
            results = self.analysis_service.perform_analysis(self.study_id, selected_parameters)
            # Mostrar resultados (en una nueva ventana, en este diálogo, etc.)
            logger.info(f"Análisis realizado para estudio {self.study_id}. Resultados: {results}") # Loggear resultados (puede ser largo)
            messagebox.showinfo("Resultado Análisis (Placeholder)", f"{results}", parent=self)
        except Exception as e:
            logger.error(f"Error al realizar análisis para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error Análisis", f"Ocurrió un error: {e}", parent=self)

    def generate_report(self):
        """Llama al servicio para generar un reporte con los parámetros seleccionados."""
        selected_parameters = self._get_selected_parameters()

        # Validar selecciones
        valid_patients = selected_parameters.get('patients', [])
        if len(valid_patients) < 2:
             messagebox.showwarning("Validación Fallida", "Debe seleccionar al menos dos participantes con datos procesados válidos para generar el reporte.", parent=self)
             return
        if not selected_parameters.get('frequencies'):
             messagebox.showwarning("Validación Fallida", "Debe seleccionar al menos una frecuencia para generar el reporte.", parent=self)
             return
        if not selected_parameters.get('calculations'):
             messagebox.showwarning("Validación Fallida", "Debe seleccionar al menos un cálculo para generar el reporte.", parent=self)
             return
        # Añadir validaciones para tipos/periodos si son obligatorios para el reporte (opcional)
        # if not selected_parameters.get('types'):
        #      messagebox.showwarning("Validación Fallida", "Debe seleccionar al menos un tipo de prueba.", parent=self)
        #      return
        # Ya no se validan tipos/periodos
        # if not selected_parameters.get('periods'):
        #      messagebox.showwarning("Validación Fallida", "Debe seleccionar al menos un periodo de prueba.", parent=self)
        #      return

        # Pedir ruta de guardado al usuario
        from tkinter import filedialog
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Guardar Reporte PDF",
            initialdir=os.path.expanduser("~") # Directorio inicial (ej. home)
        )

        if not output_path:
            return # Usuario canceló

        try:
            self.analysis_service.generate_report(self.study_id, selected_parameters, output_path)
            messagebox.showinfo("Reporte Generado", f"Reporte guardado exitosamente en:\n{output_path}", parent=self)
            # Preguntar si desea abrir el archivo
            if messagebox.askyesno("Abrir Reporte", "¿Desea abrir el reporte generado?", parent=self):
                 try:
                     if sys.platform == 'win32':
                         os.startfile(output_path)
                     elif sys.platform == 'darwin':
                         subprocess.run(['open', output_path], check=True)
                     else:
                         subprocess.run(['xdg-open', output_path], check=True)
                 except Exception as open_e:
                     messagebox.showwarning("Abrir Reporte", f"No se pudo abrir el archivo automáticamente:\n{open_e}", parent=self)

            # Refrescar la lista de reportes después de generar uno nuevo
            self.load_reports()

        except ValueError as ve: # Capturar errores específicos de validación o datos
             logger.warning(f"Error de validación al generar reporte para estudio {self.study_id}: {ve}")
             messagebox.showerror("Error Reporte", f"No se pudo generar el reporte:\n{ve}", parent=self)
        except Exception as e:
            logger.error(f"Error inesperado al generar reporte para estudio {self.study_id} en {output_path}: {e}", exc_info=True)
            messagebox.showerror("Error Reporte", f"Ocurrió un error inesperado al generar el reporte:\n{e}", parent=self)
            # import traceback # Ya no es necesario
            # traceback.print_exc() # Reemplazado por logger

    # --- Métodos para Gestión de Reportes ---

    def load_reports(self):
        """Carga la lista de reportes generados en el Treeview."""
        # Limpiar tabla
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)

        try:
            reports = self.analysis_service.list_reports(self.study_id)
            for report in reports:
                report_path = Path(report['path'])
                try:
                    # Obtener fecha de modificación
                    mtime = report_path.stat().st_mtime
                    # Necesitamos importar datetime
                    from datetime import datetime
                    mod_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    mod_date = "N/A"

                self.report_tree.insert('', 'end', values=(
                    report['name'],
                    mod_date,
                    'Ver',
                    'Eliminar'
                ), tags=(report['path'],)) # Guardar ruta completa en tags
        except Exception as e:
            logger.error(f"Error al listar reportes para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron listar los reportes: {e}", parent=self)

    def on_report_tree_click(self, event):
        """Maneja los clics en la tabla de reportes."""
        region = self.report_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column_id = self.report_tree.identify_column(event.x) # ej: '#3'
        row_id = self.report_tree.identify_row(event.y) # ej: 'I001'

        if not row_id: return

        item_tags = self.report_tree.item(row_id, "tags")
        if not item_tags or not item_tags[0]: return

        report_path_str = item_tags[0]
        report_path = Path(report_path_str)

        column_index = int(column_id.replace('#', '')) - 1 # Índice basado en 0

        if column_index == 2:  # Columna "Ver"
            self.view_report(report_path)
        elif column_index == 3:  # Columna "Eliminar"
            self.delete_report(report_path, row_id)

    def view_report(self, report_path: Path):
        """Abre el archivo PDF seleccionado."""
        if not report_path.exists():
             messagebox.showerror("Error", f"El archivo de reporte no existe:\n{report_path}", parent=self)
             self.load_reports() # Recargar lista si no existe
             return
        try:
            if sys.platform == 'win32':
                os.startfile(report_path)
            elif sys.platform == 'darwin': # macOS
                subprocess.run(['open', report_path], check=True)
            else: # Linux, etc.
                subprocess.run(['xdg-open', report_path], check=True)
        except Exception as e:
            logger.error(f"Error al abrir reporte {report_path}: {e}", exc_info=True)
            messagebox.showerror("Error al Abrir", f"No se pudo abrir el reporte '{report_path.name}':\n{str(e)}", parent=self)

    def delete_report(self, report_path: Path, item_id):
        """Solicita confirmación y elimina el reporte seleccionado."""
        if not report_path.exists():
             messagebox.showerror("Error", f"El archivo de reporte ya no existe:\n{report_path}", parent=self)
             self.load_reports()
             return

        report_name = report_path.name
        if messagebox.askyesno("Confirmar Eliminación",
                               f"¿Está seguro de que desea eliminar el reporte:\n'{report_name}'?",
                               icon='warning', parent=self):
            try:
                self.analysis_service.delete_report(str(report_path))
                messagebox.showinfo("Éxito", f"Reporte '{report_name}' eliminado.", parent=self)
                self.report_tree.delete(item_id) # Eliminar de la vista directamente
                # Opcional: recargar toda la lista con self.load_reports() si prefieres
            except FileNotFoundError:
                 messagebox.showerror("Error", f"El reporte no se encontró al intentar eliminarlo:\n{report_path}", parent=self)
                 self.load_reports() # Recargar lista completa
            except Exception as e:
                logger.error(f"Error al eliminar reporte {report_path}: {e}", exc_info=True)
                messagebox.showerror("Error al Eliminar", f"No se pudo eliminar el reporte:\n{e}", parent=self)
                # import traceback # Ya no es necesario
                # traceback.print_exc() # Reemplazado por logger

# Para pruebas directas (si es necesario)
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw() # Ocultar ventana raíz principal

    # Crear instancias dummy/reales de los servicios necesarios
    class DummyAnalysisService:
        def get_analysis_parameters(self, study_id): # Método dummy actualizado
            print(f"DummyAnalysisService: get_analysis_parameters({study_id})")
            # Devolver 'descriptors' en lugar de 'types'/'periods'
            return {'patients': {'P01', 'P02', 'P03'}, 'frequencies': {'Cinematica'}, 'descriptors': {'CMJ', 'PRE', 'POST'}, 'calculations': {'Maximo', 'Minimo'}}
        def list_reports(self, study_id): # Añadir método dummy
            print(f"DummyAnalysisService: list_reports({study_id})")
            return [{'name': 'dummy_report.pdf', 'path': '/tmp/dummy_report.pdf'}]
        def delete_report(self, report_path): # Añadir método dummy
            print(f"DummyAnalysisService: delete_report({report_path})")
        def perform_analysis(self, study_id, parameters):
            print(f"DummyAnalysisService: perform_analysis({study_id}, {parameters})")
            return f"Análisis simulado para {study_id} con {parameters}"
        def generate_report(self, study_id, parameters, output_path):
            print(f"DummyAnalysisService: generate_report({study_id}, {parameters}, {output_path})")
            # Crear un archivo dummy para probar la apertura
            try:
                with open(output_path, 'w') as f:
                    f.write(f"Reporte Dummy para Estudio {study_id}\n")
                    f.write(f"Parámetros: {parameters}\n")
                print(f"Archivo dummy creado: {output_path}")
            except Exception as e:
                 print(f"Error creando archivo dummy: {e}")


    dummy_service = DummyAnalysisService()
    dialog = AnalysisDialog(root, dummy_service, 99) # Usar un ID de prueba
    root.wait_window(dialog)
    root.destroy()
