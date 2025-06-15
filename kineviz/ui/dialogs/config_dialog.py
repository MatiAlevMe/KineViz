import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, StringVar

# Importar AppSettings para type hinting
from kineviz.config.settings import AppSettings

class ConfigDialog(Toplevel):
    """Diálogo para configurar los ajustes de la aplicación."""

    def __init__(self, parent, settings: AppSettings, reset_callback=None):
        """
        Inicializa el diálogo de configuración.

        :param parent: La ventana padre.
        :param settings: Instancia de AppSettings para cargar/guardar.
        :param reset_callback: Función a llamar cuando se presiona "Restablecer Valores por Defecto".
        """
        super().__init__(parent)
        self.settings = settings
        self.reset_callback = reset_callback # Callback para la acción de reseteo global

        self.title("Configuración")
        self.geometry("450x300") # Tamaño ajustado
        self.resizable(False, False)

        # Variables para los campos de entrada
        self.var_studies_per_page = StringVar()
        self.var_files_per_page = StringVar()
        self.var_pdfs_per_page = StringVar()
        self.var_font_scale = StringVar()
        self.var_theme = StringVar()

        self.load_current_settings()

        # Definir estilo para el botón de ayuda
        style = ttk.Style()
        style.configure("Help.TButton", foreground="white", background="blue")
        
        self.create_widgets()

        # Centrar diálogo
        self.transient(parent)
        self.grab_set()
        # Código para centrar (opcional, similar a StudyDialog)
        # ...

    def _show_input_help(self, title: str, message: str):
        """Muestra un popup de ayuda simple."""
        messagebox.showinfo(title, message, parent=self)

    def load_current_settings(self):
        """Carga los valores actuales desde AppSettings a las variables."""
        self.var_studies_per_page.set(str(self.settings.studies_per_page))
        self.var_files_per_page.set(str(self.settings.files_per_page))
        self.var_pdfs_per_page.set(str(self.settings.pdfs_per_page))
        self.var_font_scale.set(str(self.settings.font_scale))
        self.var_theme.set(self.settings.theme)

    def create_widgets(self):
        """Crea los widgets del diálogo."""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configurar grid layout
        main_frame.columnconfigure(1, weight=1)

        row_idx = 0

        # --- Campos de Configuración ---
        ttk.Label(main_frame, text="Estudios por página:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        studies_frame = ttk.Frame(main_frame)
        studies_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        studies_entry = ttk.Entry(studies_frame, textvariable=self.var_studies_per_page, width=7)
        studies_entry.pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(studies_frame, text="?", width=3, style="Help.TButton",
                   command=lambda: self._show_input_help("Ayuda: Estudios por Página",
                                                         "Número de estudios a mostrar por página en la vista principal.")
                  ).pack(side=tk.LEFT)
        row_idx += 1

        ttk.Label(main_frame, text="Archivos por página (vista estudio):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        files_frame = ttk.Frame(main_frame)
        files_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        files_entry = ttk.Entry(files_frame, textvariable=self.var_files_per_page, width=7)
        files_entry.pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(files_frame, text="?", width=3, style="Help.TButton",
                   command=lambda: self._show_input_help("Ayuda: Archivos por Página",
                                                         "Número de archivos a mostrar por página en el navegador de archivos de la vista de estudio.")
                  ).pack(side=tk.LEFT)
        row_idx += 1

        ttk.Label(main_frame, text="Reportes PDF por página (análisis):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        pdfs_frame = ttk.Frame(main_frame)
        pdfs_frame.grid(row=row_idx, column=1, sticky="w", pady=5, padx=5)
        pdfs_entry = ttk.Entry(pdfs_frame, textvariable=self.var_pdfs_per_page, width=7)
        pdfs_entry.pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(pdfs_frame, text="?", width=3, style="Help.TButton",
                   command=lambda: self._show_input_help("Ayuda: Reportes PDF por Página",
                                                         "Número de reportes PDF a mostrar por página en los gestores de análisis (funcionalidad futura).")
                  ).pack(side=tk.LEFT)
        row_idx += 1

        # --- Tamaño de Fuente ---
        ttk.Label(main_frame, text="Tamaño de Fuente (escala):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        font_scale_frame = ttk.Frame(main_frame)
        font_scale_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5) # Use ew for combobox
        font_scale_options = ["0.8", "0.9", "1.0", "1.1", "1.2", "1.3", "1.5", "1.75", "2.0"]
        font_scale_combo = ttk.Combobox(font_scale_frame, textvariable=self.var_font_scale, values=font_scale_options, width=5, state="readonly")
        font_scale_combo.pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(font_scale_frame, text="?", width=3, style="Help.TButton",
                   command=lambda: self._show_input_help("Ayuda: Tamaño de Fuente",
                                                         "Ajusta el tamaño general del texto en la aplicación.\n"
                                                         "1.0 es el tamaño normal. Valores mayores agrandan el texto, menores lo achican.")
                  ).pack(side=tk.LEFT)
        row_idx += 1

        # --- Tema de Aplicación ---
        ttk.Label(main_frame, text="Tema de Aplicación:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        theme_frame = ttk.Frame(main_frame)
        theme_frame.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=5) # Use ew for combobox
        theme_options = ["Light", "Dark"] # Add more themes as they are defined
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.var_theme, values=theme_options, width=10, state="readonly")
        theme_combo.pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(theme_frame, text="?", width=3, style="Help.TButton",
                   command=lambda: self._show_input_help("Ayuda: Tema de Aplicación",
                                                         "Cambia la apariencia visual de la aplicación (colores).\n"
                                                         "Light: Tema claro (predeterminado).\n"
                                                         "Dark: Tema oscuro.")
                  ).pack(side=tk.LEFT)
        row_idx += 1


        # --- Botón Restablecer ---
        reset_frame = ttk.Frame(main_frame)
        reset_frame.grid(row=row_idx, column=0, columnspan=2, pady=(20, 5))
        # Este botón llama al callback proporcionado (MainWindow.reset_to_defaults)
        # que maneja la eliminación de DB y archivos.
        reset_button = ttk.Button(reset_frame, text="Restablecer Valores por Defecto (Global)", command=self.trigger_reset_callback)
        reset_button.pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(reset_frame, text="?", width=3, style="Help.TButton",
                   command=lambda: self._show_input_help("Ayuda: Restablecer Valores por Defecto (Global)",
                                                         "Esta acción eliminará TODA la información de la aplicación:\n"
                                                         "- Todos los estudios y sus datos asociados.\n"
                                                         "- Todos los análisis guardados (discretos y continuos).\n"
                                                         "- La base de datos local de KineViz.\n"
                                                         "- Las configuraciones personalizadas se revertirán a los valores iniciales.\n\n"
                                                         "La aplicación se cerrará y deberá reiniciarse.\n"
                                                         "Esta acción es IRREVERSIBLE. Úsela con precaución.")
                  ).pack(side=tk.LEFT)
        row_idx += 1

        # --- Botones Guardar/Cancelar ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="e", pady=(15, 0))

        ttk.Button(button_frame, text="Guardar", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def validate_input(self) -> bool:
        """Valida que los valores ingresados sean enteros positivos."""
        inputs_int = {
            "Estudios por página": self.var_studies_per_page.get(),
            "Archivos por página": self.var_files_per_page.get(),
            "Reportes PDF por página": self.var_pdfs_per_page.get()
        }
        for label, value_str in inputs_int.items():
            try:
                value_int = int(value_str)
                if value_int <= 0:
                    messagebox.showerror("Valor Inválido", f"'{label}' debe ser un número entero positivo.", parent=self)
                    return False
            except ValueError:
                messagebox.showerror("Valor Inválido", f"'{label}' debe ser un número entero válido.", parent=self)
                return False

        # Validar Escala de Fuente
        try:
            font_scale_val = float(self.var_font_scale.get())
            if font_scale_val <= 0:
                messagebox.showerror("Valor Inválido", "'Tamaño de Fuente (escala)' debe ser un número positivo.", parent=self)
                return False
        except ValueError:
            messagebox.showerror("Valor Inválido", "'Tamaño de Fuente (escala)' debe ser un número válido.", parent=self)
            return False
        
        # Tema no necesita validación si se usa Combobox con state="readonly"
        return True

    def save_settings(self):
        """Valida y guarda las configuraciones usando AppSettings."""
        if not self.validate_input():
            return

        try:
            # Actualizar el objeto settings en memoria
            self.settings.studies_per_page = int(self.var_studies_per_page.get())
            self.settings.files_per_page = int(self.var_files_per_page.get())
            self.settings.pdfs_per_page = int(self.var_pdfs_per_page.get())
            self.settings.font_scale = float(self.var_font_scale.get())
            self.settings.theme = self.var_theme.get()

            # Guardar en el archivo config.ini
            self.settings.save_settings()
            messagebox.showinfo("Éxito", "Configuraciones guardadas correctamente.\nAlgunos cambios pueden requerir reiniciar la aplicación para verlos reflejados.", parent=self)
            self.destroy() # Cerrar diálogo después de guardar

        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudieron guardar las configuraciones:\n{e}", parent=self)

    def trigger_reset_callback(self):
        """Llama al callback de reseteo si existe."""
        if self.reset_callback:
            # Preguntar de nuevo aquí por seguridad, aunque MainWindow también lo hace
            if messagebox.askyesno("Confirmar Restablecimiento Global",
                                   "Esta acción restablecerá toda la aplicación a su estado inicial, eliminando todos los datos y estudios.\n\n¿Está seguro de que desea continuar?",
                                   icon='warning', parent=self):
                try:
                    self.reset_callback()
                    # Cerrar el diálogo de configuración después del reseteo global
                    self.destroy()
                except Exception as e:
                     messagebox.showerror("Error", f"Ocurrió un error durante el restablecimiento:\n{e}", parent=self)
        else:
            messagebox.showwarning("No Implementado", "La función de restablecimiento global no está conectada.", parent=self)

# Para pruebas directas (si es necesario)
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw() # Ocultar ventana raíz

    # Crear instancia dummy de AppSettings
    dummy_settings = AppSettings(config_filename='config_test.ini') # Usar archivo de prueba

    def dummy_reset():
        print("CALLBACK: Restablecer valores por defecto llamado!")
        # Aquí iría la lógica real de MainWindow.reset_to_defaults
        # Por ahora, solo reseteamos los settings en memoria/archivo
        dummy_settings.reset_to_defaults()
        messagebox.showinfo("Reseteo Simulado", "Valores por defecto restablecidos (simulado).", parent=root)


    dialog = ConfigDialog(root, dummy_settings, reset_callback=dummy_reset)
    root.wait_window(dialog)

    # Verificar si los settings se guardaron (opcional)
    print("\nSettings después de cerrar diálogo:")
    print(f"Studies per page: {dummy_settings.studies_per_page}")
    print(f"Files per page: {dummy_settings.files_per_page}")
    print(f"PDFs per page: {dummy_settings.pdfs_per_page}")

    # Limpiar archivo de prueba
    if dummy_settings.config_path.exists():
         dummy_settings.config_path.unlink()

    root.destroy()
