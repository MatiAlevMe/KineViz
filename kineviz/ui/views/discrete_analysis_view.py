import tkinter as tk
from tkinter import ttk, messagebox
import logging
from kineviz.core.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

class DiscreteAnalysisView(ttk.Frame):
    """Vista para gestionar y visualizar el análisis discreto (Fase 6)."""

    def __init__(self, parent, main_window, analysis_service: AnalysisService, study_id: int):
        super().__init__(parent)
        self.parent = parent
        self.main_window = main_window
        self.analysis_service = analysis_service
        self.study_id = study_id

        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10) # Empaquetar el frame principal

        self.create_widgets()
        # self.load_tables() # Carga inicial de tablas (se implementará después)

    def create_widgets(self):
        """Crea los widgets para la vista de análisis discreto."""

        # --- Cabecera ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Botón Volver a la vista del estudio
        ttk.Button(header_frame, text="<< Volver al Estudio",
                   command=lambda: self.main_window.show_study_view(self.study_id)).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(header_frame, text=f"Análisis Discreto - Estudio {self.study_id}", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 20))

        # --- Acciones ---
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(action_frame, text="Generar/Actualizar Tablas Resumen (Cinemática)",
                   command=self.generate_tables).pack(side=tk.LEFT, padx=5)

        # Botón para abrir carpeta (se implementará después)
        # ttk.Button(action_frame, text="Abrir Carpeta de Tablas",
        #            command=self.open_tables_folder).pack(side=tk.LEFT, padx=5)

        # --- Placeholder para la lista de tablas ---
        list_frame = ttk.LabelFrame(self, text="Tablas Generadas")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        ttk.Label(list_frame, text="La lista de tablas generadas aparecerá aquí.").pack(padx=10, pady=10)
        # Aquí iría el Treeview y filtros para las tablas generadas (futura implementación)
        # self.create_table_list(list_frame)

    def generate_tables(self):
        """Llama al servicio para generar las tablas resumen CSV."""
        logger.info(f"Solicitando generación de tablas discretas para estudio {self.study_id}")
        try:
            # Mostrar un mensaje de "procesando" podría ser útil aquí
            results = self.analysis_service.generate_discrete_summary_tables(self.study_id)

            success_count = len(results.get('success', []))
            error_count = len(results.get('errors', []))

            message = f"Generación de tablas completada.\n\n"
            message += f"Tablas generadas/actualizadas: {success_count}\n"
            if error_count > 0:
                message += f"Errores encontrados: {error_count}\n\n"
                message += "Errores detallados:\n"
                message += "\n".join([f"- {err}" for err in results['errors'][:5]]) # Mostrar hasta 5 errores
                if error_count > 5:
                    message += f"\n... y {error_count - 5} más (ver logs)."
                messagebox.showwarning("Resultado Generación", message, parent=self)
            else:
                messagebox.showinfo("Resultado Generación", message, parent=self)

            # Refrescar la lista de tablas (cuando se implemente)
            # self.load_tables()

        except Exception as e:
            logger.critical(f"Error crítico al llamar a generate_discrete_summary_tables: {e}", exc_info=True)
            messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado al generar las tablas:\n{e}", parent=self)

    # def load_tables(self):
    #     """Carga la lista de tablas CSV generadas."""
    #     # Implementación futura: escanear directorio, parsear nombres, llenar treeview
    #     pass

    # def open_tables_folder(self):
    #      """Abre la carpeta que contiene las tablas generadas."""
    #      # Implementación futura: obtener ruta del estudio, construir ruta de tablas, llamar a main_window.open_folder
    #      pass

    def destroy(self):
        """Destruye el frame principal de esta vista."""
        super().destroy()

```

**5. Update `ROADMAP.md`:**

```markdown
ROADMAP.md
<<<<<<< SEARCH
**Fase 6: Análisis Estadístico Discreto y Reportes Avanzados**

*   **1. Generación de Matrices:** (Pendiente) Crear tablas por tipo de cálculo y descriptor (ej: "máximo_cinemática_obesidad").
*   **2. Selector de Variables y Etiquetas:** (Pendiente) Permitir que el usuario elija las variables a utilizar en el análisis.
*   **3. Interacción sobre Datos Pareados:** (Pendiente) Preguntar si los datos son pareados o independientes.
