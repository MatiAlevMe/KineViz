import tkinter as tk
from tkinter import ttk, Toplevel, messagebox
import os
import sys
import subprocess
from tkinter import Listbox, Scrollbar, Frame # Necesario para las listas

class AnalysisDialog(Toplevel):
    def __init__(self, parent, analysis_service, study_id):
        """
        Inicializa el diálogo de análisis.

        :param parent: La ventana padre.
        :param analysis_service: Instancia de AnalysisService.
        :param study_id: ID del estudio a analizar.
        """
        super().__init__(parent)
        self.analysis_service = analysis_service
        self.study_id = study_id

        self.title(f"Análisis - Estudio ID: {study_id}")
        self.geometry("700x500") # Tamaño inicial
        self.resizable(True, True)

        # Cargar parámetros disponibles ANTES de crear widgets
        self.load_available_parameters()

        self.create_widgets()

        # Centrar diálogo
        self.transient(parent)
        self.grab_set()
        # Código para centrar (opcional, similar a StudyDialog)
        # ...

    def create_widgets(self):
        """Crea los widgets del diálogo de análisis."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Selección de Parámetros ---
        params_frame = ttk.Frame(main_frame)
        params_frame.pack(fill=tk.BOTH, expand=True)

        # Crear selectores para cada parámetro
        self.patient_selector = self._create_parameter_selector(params_frame, "Pacientes", self.available_params.get('patients', set()))
        self.frequency_selector = self._create_parameter_selector(params_frame, "Frecuencias", self.available_params.get('frequencies', set()))
        self.type_selector = self._create_parameter_selector(params_frame, "Tipos Prueba", self.available_params.get('types', set()))
        self.period_selector = self._create_parameter_selector(params_frame, "Periodos Prueba", self.available_params.get('periods', set()))
        self.calculation_selector = self._create_parameter_selector(params_frame, "Cálculos", self.available_params.get('calculations', set()))

        # --- Botones de Acción ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Generar Reporte", command=self.generate_report).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Realizar Análisis", command=self.perform_analysis, state=tk.DISABLED).pack(side=tk.RIGHT, padx=5) # Deshabilitado por ahora
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def load_available_parameters(self):
        """Carga los parámetros disponibles desde el servicio."""
        try:
            self.available_params = self.analysis_service.get_analysis_parameters(self.study_id)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los parámetros de análisis: {e}", parent=self)
            self.available_params = {} # Asegurar que sea un diccionario vacío

    def _create_parameter_selector(self, parent, title: str, available_items: set):
        """Crea un conjunto de widgets para seleccionar un parámetro."""
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
        for item in sorted(list(available_items)): # Poblar lista ordenada
            available_listbox.insert(tk.END, item)

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

        # Devolver las listas para poder acceder a ellas
        return {'available': available_listbox, 'selected': selected_listbox}

    def _move_items(self, source_listbox: Listbox, dest_listbox: Listbox):
        """Mueve los elementos seleccionados de una lista a otra."""
        selected_indices = source_listbox.curselection()
        items_to_move = [source_listbox.get(i) for i in selected_indices]

        # Añadir a destino si no existe y ordenar
        current_dest_items = set(dest_listbox.get(0, tk.END))
        new_items_added = False
        for item in items_to_move:
            if item not in current_dest_items:
                dest_listbox.insert(tk.END, item)
                current_dest_items.add(item)
                new_items_added = True

        if new_items_added:
             # Ordenar lista destino
             all_dest_items = sorted(list(current_dest_items))
             dest_listbox.delete(0, tk.END)
             for item in all_dest_items:
                 dest_listbox.insert(tk.END, item)

        # Eliminar de origen (iterar en reversa)
        for i in reversed(selected_indices):
            source_listbox.delete(i)

    def _move_all_items(self, source_listbox: Listbox, dest_listbox: Listbox):
         """Mueve todos los elementos de una lista a otra."""
         all_items = source_listbox.get(0, tk.END)
         current_dest_items = set(dest_listbox.get(0, tk.END))
         new_items_added = False

         for item in all_items:
             if item not in current_dest_items:
                 dest_listbox.insert(tk.END, item)
                 current_dest_items.add(item)
                 new_items_added = True

         if new_items_added:
             # Ordenar lista destino
             all_dest_items = sorted(list(current_dest_items))
             dest_listbox.delete(0, tk.END)
             for item in all_dest_items:
                 dest_listbox.insert(tk.END, item)

         # Limpiar origen
         source_listbox.delete(0, tk.END)


    def _get_selected_parameters(self) -> dict:
        """Recolecta los parámetros seleccionados de las listas."""
        return {
            'patients': list(self.patient_selector['selected'].get(0, tk.END)),
            'frequencies': list(self.frequency_selector['selected'].get(0, tk.END)),
            'types': list(self.type_selector['selected'].get(0, tk.END)),
            'periods': list(self.period_selector['selected'].get(0, tk.END)),
            'calculations': list(self.calculation_selector['selected'].get(0, tk.END)),
        }

    def perform_analysis(self):
        """Llama al servicio para realizar el análisis con los parámetros seleccionados."""
        selected_parameters = self._get_selected_parameters()

        # Validar selecciones (ejemplo básico)
        if not selected_parameters['patients']:
             messagebox.showwarning("Parámetros Faltantes", "Debe seleccionar al menos un paciente.", parent=self)
             return
        # Añadir más validaciones si es necesario...

        try:
            # Llamar al servicio con los parámetros recolectados
            results = self.analysis_service.perform_analysis(self.study_id, selected_parameters)
            # Mostrar resultados (en una nueva ventana, en este diálogo, etc.)
            messagebox.showinfo("Resultado Análisis (Placeholder)", f"{results}", parent=self)
        except Exception as e:
            messagebox.showerror("Error Análisis", f"Ocurrió un error: {e}", parent=self)

    def generate_report(self):
        """Llama al servicio para generar un reporte con los parámetros seleccionados."""
        selected_parameters = self._get_selected_parameters()

        # Validar selecciones (ejemplo básico)
        if not selected_parameters['patients'] or not selected_parameters['frequencies'] or \
           not selected_parameters['calculations']:
             messagebox.showwarning("Parámetros Faltantes",
                                    "Debe seleccionar al menos un paciente, una frecuencia y un cálculo para generar el reporte.",
                                    parent=self)
             return
        # Añadir validaciones para tipos/periodos si son obligatorios para el reporte

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
            messagebox.showinfo("Reporte Generado (Placeholder)", f"Reporte guardado (o debería) en:\n{output_path}", parent=self)
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

        except Exception as e:
            messagebox.showerror("Error Reporte", f"Ocurrió un error al generar el reporte: {e}", parent=self)

# Para pruebas directas (si es necesario)
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw() # Ocultar ventana raíz principal

    # Crear instancias dummy/reales de los servicios necesarios
    class DummyAnalysisService:
        def perform_analysis(self, study_id, parameters):
            return f"Análisis simulado para {study_id} con {parameters}"
        def generate_report(self, study_id, parameters, output_path):
            print(f"Simulando generación de reporte para {study_id} en {output_path}")
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
