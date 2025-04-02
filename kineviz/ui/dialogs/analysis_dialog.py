import tkinter as tk
from tkinter import ttk, Toplevel, messagebox
import os
import sys
import subprocess

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

        # --- Placeholder ---
        ttk.Label(main_frame, text=f"Configuración de Análisis para Estudio ID: {self.study_id}",
                  font=('Helvetica', 14, 'bold')).pack(pady=10)

        ttk.Label(main_frame, text="Aquí irán los controles para seleccionar pacientes, frecuencias, tipos, periodos, cálculos, etc.").pack(pady=5)
        ttk.Label(main_frame, text="(Funcionalidad por implementar)").pack(pady=5)
        # --- Fin Placeholder ---

        # --- Ejemplo de controles futuros (comentados) ---
        # patient_frame = ttk.LabelFrame(main_frame, text="Pacientes")
        # patient_frame.pack(fill=tk.X, pady=5)
        # # ... Listbox, botones Add/Remove ...

        # frequency_frame = ttk.LabelFrame(main_frame, text="Frecuencias")
        # frequency_frame.pack(fill=tk.X, pady=5)
        # # ... Listbox, botones Add/Remove ...

        # calculation_frame = ttk.LabelFrame(main_frame, text="Cálculos")
        # calculation_frame.pack(fill=tk.X, pady=5)
        # # ... Listbox, botones Add/Remove ...
        # --- Fin Ejemplo ---


        # --- Botones de Acción ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Generar Reporte", command=self.generate_report).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Realizar Análisis", command=self.perform_analysis).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def perform_analysis(self):
        """Llama al servicio para realizar el análisis."""
        # Recolectar parámetros seleccionados (cuando se implementen los controles)
        selected_parameters = {
            "message": "Parámetros no implementados"
            # 'patients': [...], 'frequencies': [...], ...
        }
        try:
            results = self.analysis_service.perform_analysis(self.study_id, selected_parameters)
            # Mostrar resultados (en una nueva ventana, en este diálogo, etc.)
            messagebox.showinfo("Resultado Análisis (Placeholder)", f"{results}", parent=self)
        except Exception as e:
            messagebox.showerror("Error Análisis", f"Ocurrió un error: {e}", parent=self)

    def generate_report(self):
        """Llama al servicio para generar un reporte."""
        # Recolectar parámetros seleccionados
        selected_parameters = {
             "message": "Parámetros no implementados"
            # 'patients': [...], 'frequencies': [...], ...
        }
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
