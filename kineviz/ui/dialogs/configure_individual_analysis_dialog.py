import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List  # Para type hinting

from kineviz.core.services.analysis_service import AnalysisService


logger = logging.getLogger(__name__)


class ConfigureIndividualAnalysisDialog(tk.Toplevel):
    """Diálogo para configurar los parámetros de un análisis individual."""

    def __init__(self, parent, analysis_service: AnalysisService, study_id: int):
        super().__init__(parent)
        self.parent = parent
        self.analysis_service = analysis_service
        self.study_id = study_id

        self.title("Configurar Nuevo Análisis Individual")
        # self.geometry("500x600") # Ajustar según necesidad
        self.grab_set()  # Hacer modal

        # Variables de control
        self.analysis_name_var = tk.StringVar()
        self.frequency_var = tk.StringVar()
        self.calculation_var = tk.StringVar()
        self.column_var = tk.StringVar()
        self.parametric_var = tk.BooleanVar(value=True) # Asumir paramétrico por defecto
        self.paired_var = tk.BooleanVar(value=False)  # Asumir independiente

        # Listas para selectores dinámicos
        self.available_frequencies = ["Cinematica"]  # Por ahora solo Cinemática
        self.available_calculations = ["Maximo", "Minimo", "Rango"]
        self.available_groups = []  # Se carga dinámicamente
        self.available_columns = []  # Se carga dinámicamente

        # Gestión de grupos seleccionados
        # Lista de StringVars para grupos seleccionados
        self.selected_group_vars = []
        # Lista de frames para cada fila de grupo
        self.group_selector_frames = []

        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        """Crea los widgets del diálogo."""
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Nombre del Análisis ---
        ttk.Label(main_frame, text="Nombre del Análisis:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        ttk.Entry(main_frame, textvariable=self.analysis_name_var, width=40).grid(row=0, column=1, columnspan=2, sticky="ew", pady=(0, 5))

        # --- Selección de Parámetros Base ---
        param_frame = ttk.LabelFrame(main_frame, text="Parámetros Base")
        param_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)
        param_frame.columnconfigure(1, weight=1)

        ttk.Label(param_frame, text="Frecuencia:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.freq_combo = ttk.Combobox(
            param_frame, textvariable=self.frequency_var,
            values=self.available_frequencies, state="readonly"
        )
        self.freq_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        # Actualizar grupos al cambiar frecuencia
        self.freq_combo.bind("<<ComboboxSelected>>", self.update_available_groups)

        ttk.Label(param_frame, text="Cálculo:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.calc_combo = ttk.Combobox(
            param_frame, textvariable=self.calculation_var,
            values=self.available_calculations, state="readonly"
        )
        self.calc_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        # Actualizar columnas al cambiar cálculo
        self.calc_combo.bind("<<ComboboxSelected>>", self.update_available_columns)

        # --- Selección de Grupos ---
        group_frame = ttk.LabelFrame(main_frame,
                                     text="Grupos a Comparar (mínimo 2)")
        group_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)
        group_frame.columnconfigure(0, weight=1)

        # Frame contenedor para las entradas de grupo (se añadirá dinámicamente)
        self.group_entries_frame = ttk.Frame(group_frame)
        self.group_entries_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.group_entries_frame.columnconfigure(0, weight=1)

        # Botón para añadir más grupos
        add_group_button = ttk.Button(group_frame, text="+ Añadir Grupo",
                                      command=self.add_group_selector)
        add_group_button.grid(row=1, column=0, columnspan=2, pady=5)

        # --- Selección de Columna ---
        col_frame = ttk.LabelFrame(main_frame,
                                   text="Variable a Analizar")
        col_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)
        col_frame.columnconfigure(1, weight=1)

        ttk.Label(col_frame, text="Columna:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.col_combo = ttk.Combobox(col_frame, textvariable=self.column_var,
                                      values=[], state="readonly", width=50)
        self.col_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # --- Opciones Estadísticas ---
        stats_frame = ttk.LabelFrame(main_frame,
                                     text="Supuestos Estadísticos")
        stats_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)

        ttk.Checkbutton(
            stats_frame,
            text="Asumir Datos Paramétricos (distribución normal)",
            variable=self.parametric_var
        ).pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Checkbutton(
            stats_frame,
            text="Datos Pareados (misma unidad de muestreo en todos los grupos)",
            variable=self.paired_var
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # --- Botones de Acción ---
        action_button_frame = ttk.Frame(main_frame)
        action_button_frame.grid(row=5, column=0, columnspan=3, sticky="e",
                                 pady=(20, 0))

        ttk.Button(action_button_frame, text="Generar Gráfico y Guardar",
                   command=self.generate_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_button_frame, text="Cancelar",
                   command=self.destroy).pack(side=tk.LEFT, padx=5)

    def load_initial_data(self):
        """Carga los datos iniciales para los selectores."""
        # Establecer valores iniciales si hay disponibles
        if self.available_frequencies:
            self.frequency_var.set(self.available_frequencies[0])
        if self.available_calculations:
            self.calculation_var.set(self.available_calculations[0])

        # Cargar grupos disponibles para la frecuencia inicial
        self.update_available_groups()

        # Añadir los dos primeros selectores de grupo obligatorios
        self.add_group_selector()
        self.add_group_selector()

        # Cargar columnas iniciales (probablemente vacío hasta seleccionar grupos)
        self.update_available_columns()

    def update_available_groups(self, event=None):
        """Actualiza la lista de grupos disponibles basada en la frecuencia."""
        selected_freq = self.frequency_var.get()
        if not selected_freq:
            self.available_groups = []
        else:
            try:
                # Usar alias para mostrar en la UI
                raw_groups = self.analysis_service.get_discrete_analysis_groups(self.study_id, selected_freq)
                self.available_groups = []
                for g_key in raw_groups:
                    parts = g_key.split('_')
                    # Acceder a settings a través de analysis_service
                    aliased_parts = [
                        self.analysis_service.settings.get_descriptor_alias(p) or p
                        for p in parts
                    ]
                    display_name = ', '.join(aliased_parts) \
                        if g_key != "SinDescriptores" else "Sin Descriptores"
                    # Guardar tupla (display_name, original_key)
                    self.available_groups.append((display_name, g_key))
                # Ordenar por nombre visible
                self.available_groups.sort()

            except Exception as e:
                logger.error(f"Error obteniendo grupos para frecuencia {selected_freq}: {e}", exc_info=True)
                messagebox.showerror("Error", f"No se pudieron cargar los grupos disponibles:\n{e}", parent=self)
                self.available_groups = []

        # Actualizar los combobox de grupo existentes
        display_names = [g[0] for g in self.available_groups]
        for frame in self.group_selector_frames:
            combo = frame.winfo_children()[0] # Asumiendo que el Combobox es el primer hijo
            combo['values'] = display_names
            # Intentar mantener la selección si aún es válida
            current_display_selection = combo.get()
            if current_display_selection not in display_names:
                combo.set('')  # Limpiar si la selección ya no existe

        # Limpiar columnas ya que los grupos cambiaron
        self.column_var.set('')
        self.col_combo['values'] = []
        self.available_columns = []


    def add_group_selector(self, initial_value=""):
        """Añade una nueva fila para seleccionar un grupo."""
        row_index = len(self.group_selector_frames)
        frame = ttk.Frame(self.group_entries_frame)
        frame.grid(row=row_index, column=0, sticky="ew", pady=2)
        frame.columnconfigure(0, weight=1)

        group_var = tk.StringVar()
        display_names = [g[0] for g in self.available_groups]
        combo = ttk.Combobox(frame, textvariable=group_var,
                             values=display_names, state="readonly", width=35)
        combo.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        # Actualizar columnas al cambiar grupo
        combo.bind("<<ComboboxSelected>>", self.update_available_columns)

        # Botón para eliminar esta fila (deshabilitado para las 2 primeras)
        remove_button = ttk.Button(
            frame, text="-", width=3,
            command=lambda f=frame, v=group_var: self.remove_group_selector(f, v)
        )
        remove_button.grid(row=0, column=1, sticky="w")
        if row_index < 2:
            remove_button.config(state=tk.DISABLED)

        self.selected_group_vars.append(group_var)
        self.group_selector_frames.append(frame)

        if initial_value and initial_value in display_names:
            group_var.set(initial_value)

    def remove_group_selector(self, frame_to_remove, var_to_remove):
        """Elimina una fila de selector de grupo."""
        if len(self.group_selector_frames) <= 2:
            messagebox.showwarning("Acción no permitida",
                                   "Se requieren al menos dos grupos.",
                                   parent=self)
            return

        try:
            index = self.group_selector_frames.index(frame_to_remove)
            frame_to_remove.destroy()
            index = self.group_selector_frames.index(frame_to_remove)
            frame_to_remove.destroy()
            self.group_selector_frames.pop(index)
            self.selected_group_vars.pop(index)
            # Re-indexar grid de los frames restantes (opcional)
            for i, frame in enumerate(self.group_selector_frames):
                frame.grid(row=i, column=0, sticky="ew", pady=2)

            # Actualizar columnas disponibles
            self.update_available_columns()

        except ValueError:
            logger.error("Intento de eliminar un frame de grupo no listado.")

    def get_selected_group_keys(self) -> List[str]:
        """Obtiene las claves originales de los grupos seleccionados."""
        selected_keys = []
        selected_display_names = set()  # Para detectar duplicados
        valid = True

        for group_var in self.selected_group_vars:
            display_name = group_var.get()
            if not display_name:
                valid = False
                break  # Salir si uno está vacío

            if display_name in selected_display_names:
                messagebox.showerror(
                    "Error de Selección",
                    f"El grupo '{display_name}' está seleccionado más de una vez.",
                    parent=self)
                return []  # Devolver vacío si hay duplicados

            selected_display_names.add(display_name)

            # Encontrar la clave original correspondiente al display_name
            original_key = None
            for name, key in self.available_groups:
                if name == display_name:
                    original_key = key
                    break
            if original_key:
                selected_keys.append(original_key)
            else:
                # Esto no debería pasar si la UI funciona bien
                logger.error(f"No se encontró clave original para: {display_name}")
                valid = False
                break

        if not valid or len(selected_keys) < 2:
            return []  # Devolver vacío si no es válido o no hay suficientes

        return selected_keys


    def update_available_columns(self, event=None):
        """Actualiza la lista de columnas comunes basada en los grupos seleccionados."""
        selected_freq = self.frequency_var.get()
        selected_calc = self.calculation_var.get()
        selected_group_keys = self.get_selected_group_keys()

        # Limpiar selección actual
        self.column_var.set('')
        self.col_combo['values'] = []
        self.available_columns = []

        if selected_freq and selected_calc and len(selected_group_keys) >= 2:
            try:
                self.available_columns = \
                    self.analysis_service.get_common_columns_for_groups(
                        self.study_id, selected_freq, selected_calc,
                        selected_group_keys
                    )
                self.col_combo['values'] = self.available_columns
                if self.available_columns:
                    # Dejar vacío para que el usuario elija explícitamente
                    pass
                else:
                    messagebox.showinfo(
                        "Sin Columnas Comunes",
                        "No se encontraron columnas de datos comunes para la "
                        "combinación de cálculo y grupos seleccionada.",
                        parent=self)

            except Exception as e:
                logger.error(f"Error obteniendo columnas comunes: {e}",
                             exc_info=True)
                messagebox.showerror("Error", f"No se pudieron cargar las columnas comunes:\n{e}", parent=self)
                self.available_columns = []

    def generate_analysis(self):
        """Valida la config y llama al servicio para generar el análisis."""
        analysis_name = self.analysis_name_var.get().strip()
        selected_freq = self.frequency_var.get()
        selected_calc = self.calculation_var.get()
        selected_col = self.column_var.get()
        selected_group_keys = self.get_selected_group_keys()
        is_parametric = self.parametric_var.get()
        is_paired = self.paired_var.get()

        # --- Validaciones ---
        if not analysis_name:
            messagebox.showerror("Error de Validación",
                                   "Ingrese un nombre para el análisis.",
                                   parent=self)
            return
        # Validar caracteres inválidos en nombre (repetido de AnalysisService)
        invalid_chars = r'<>:"/\|?*'
        if any(char in analysis_name for char in invalid_chars):
            messagebox.showerror(
                "Error de Validación",
                f"El nombre del análisis contiene caracteres inválidos: "
                f"{invalid_chars}", parent=self)
            return

        if not selected_freq or not selected_calc:
            messagebox.showerror("Error de Validación",
                                   "Seleccione Frecuencia y Cálculo.",
                                   parent=self)
            return
        if len(selected_group_keys) < 2:
            messagebox.showerror(
                "Error de Validación",
                "Seleccione al menos dos grupos válidos y distintos.",
                parent=self)
            return
        if not selected_col:
            messagebox.showerror("Error de Validación",
                                   "Seleccione la columna a analizar.",
                                   parent=self)
            return

        # --- Crear Configuración ---
        config = {
            "name": analysis_name,
            "frequency": selected_freq,
            "calculation": selected_calc,
            "column": selected_col,
            "groups": selected_group_keys,  # Guardar las claves originales
            "parametric": is_parametric,
            "paired": is_paired
        }

        # --- Llamar al Servicio ---
        try:
            # TODO: Añadir feedback visual de "procesando..."
            result = self.analysis_service.perform_individual_analysis(
                self.study_id, config
            )
            messagebox.showinfo(
                "Análisis Generado",
                f"El análisis '{analysis_name}' se generó correctamente.\n"
                f"Gráfico guardado en: {result['plot_path']}",
                parent=self.parent)  # Mostrar sobre el gestor
            self.destroy()  # Cerrar diálogo de configuración

        except (ValueError, FileNotFoundError) as e:
            logger.warning(f"Error de validación o datos al generar análisis "
                           f"'{analysis_name}': {e}")
            messagebox.showerror("Error al Generar Análisis", f"{e}", parent=self)
        except Exception as e:
            logger.critical(f"Error inesperado al generar análisis "
                            f"'{analysis_name}': {e}", exc_info=True)
            messagebox.showerror("Error Crítico",
                                   f"Ocurrió un error inesperado:\n{e}",
                                   parent=self)


# Para pruebas rápidas
if __name__ == '__main__':
    from pathlib import Path  # Importar Path para el dummy
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal

    # --- Dummies (igual que en el manager) ---
    class DummyAnalysisService:
        def __init__(self):
            # Simular AppSettings
            class DummySettings:
                def get_descriptor_alias(self, desc):
                    return {'CMJ': 'Salto CM', 'PRE': 'Antes',
                            'POST': 'Despues'}.get(desc)
            self.settings = DummySettings()

        def get_discrete_analysis_groups(self, study_id, frequency):
            print(f"Dummy: get_discrete_analysis_groups({study_id}, "
                  f"{frequency})")
            return ['CMJ_PRE', 'CMJ_POST', 'SJ_TipoA', 'SJ_TipoB', 'SJ_TipoC',
                    'SinDescriptores']

        def get_common_columns_for_groups(self, study_id, frequency,
                                          calculation, group_keys):
            print(f"Dummy: get_common_columns_for_groups({study_id}, "
                  f"{frequency}, {calculation}, {group_keys})")
            # Simular que solo hay columnas si se eligen 2 grupos
            if len(group_keys) == 2:
                return ['Art1/PosX/mm', 'Art1/PosY/mm', 'Art2/VelX/m/s',
                        'H Salto/Alt/cm']
            else:
                return []

        def perform_individual_analysis(self, study_id, config):
            print(f"Dummy: perform_individual_analysis({study_id}, {config})")
            # Simular éxito
            fake_path = Path(f'/fake/study_{study_id}/Analisis Discreto/'
                             f'Individual/{config["name"]}')
            # Crear directorios dummy para que no falle el messagebox
            # fake_path.mkdir(parents=True, exist_ok=True)
            return {'plot_path': str(fake_path / 'boxplot.png'),
                    'config_path': str(fake_path / 'config.json')}

    # --- Ejecutar Diálogo ---
    dummy_service = DummyAnalysisService()
    dialog = ConfigureIndividualAnalysisDialog(root, dummy_service, 1)
    root.mainloop()
