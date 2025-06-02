import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Tuple # Añadir Tuple para type hint

from kineviz.core.services.analysis_service import AnalysisService
# Importar validador necesario
from kineviz.ui.utils.validators import validate_filename_for_study_criteria


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

        # --- Nuevas variables de estado para el flujo ---
        self.vi_grouping_mode = tk.StringVar(value="") # '1VI' o '2VIs'
        self.primary_vi_var = tk.StringVar() # VI seleccionada en modo 1VI
        self.fixed_vi_var = tk.StringVar() # VI a fijar en modo 2VIs
        self.fixed_descriptor_var = tk.StringVar() # Descriptor a fijar en modo 2VIs
        self.all_vi_names = [] # Nombres de las VIs del estudio
        self.all_descriptors_by_vi = {} # {vi_name: [desc1, desc2]}
        self.study_aliases = {} # Alias del estudio

        # --- Variables existentes (algunas se reutilizan) ---
        self.frequency_var = tk.StringVar()
        self.calculation_var = tk.StringVar()
        self.available_frequencies = [] # Se carga dinámicamente
        self.available_calculations = ["Maximo", "Minimo", "Rango"] # Mantener fijos por ahora

        self.group_selector_frames = [] # Lista de frames para cada selector de grupo
        self.group_selector_vars = [] # Lista de StringVars para grupos seleccionados (reutilizado)
        self.available_groups_filtered = {} # Diccionario {display_name: original_key} - AHORA FILTRADO

        # Variables para la columna y supuestos (reutilizadas)
        self.column_var = tk.StringVar()
        self.available_columns = []
        self.parametric_var = tk.BooleanVar(value=True)
        self.paired_var = tk.BooleanVar(value=False)

        # Variable para el nombre del análisis (reutilizada)
        self.analysis_name_var = tk.StringVar()

        self.create_widgets()
        self.load_initial_data() # Cargará VIs, alias, frecuencias

    def create_widgets(self):
        """Crea los widgets del diálogo."""
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1) # Columna de Combobox/Entry expandible

        row_idx = 0

        # --- Selección de Tipo de Dato y Cálculo (Sin cambios iniciales) ---
        ttk.Label(main_frame, text="Tipo de Dato:").grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        self.freq_combo = ttk.Combobox(main_frame, textvariable=self.frequency_var, state="readonly", postcommand=self.load_frequencies)
        self.freq_combo.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=5)
        # Bind se hará después o se llamará manualmente
        row_idx += 1

        ttk.Label(main_frame, text="Cálculo:").grid(row=row_idx, column=0, sticky="w", padx=5, pady=5)
        self.calc_combo = ttk.Combobox(main_frame, textvariable=self.calculation_var, values=self.available_calculations, state="readonly")
        self.calc_combo.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=5)
        # Bind se hará después o se llamará manualmente
        row_idx += 1

        # --- NUEVO: Selección de Modo de Agrupación (1 VI vs 2 VIs) ---
        vi_mode_frame = ttk.Frame(main_frame)
        vi_mode_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=10)
        ttk.Label(vi_mode_frame, text="Agrupar por:").pack(side=tk.LEFT, padx=(0, 10))
        self.one_vi_button = ttk.Button(vi_mode_frame, text="1 Variable Independiente", command=lambda: self.set_vi_grouping_mode('1VI'))
        self.one_vi_button.pack(side=tk.LEFT, padx=5)
        self.two_vi_button = ttk.Button(vi_mode_frame, text="2 Variables Independientes", command=lambda: self.set_vi_grouping_mode('2VIs'))
        self.two_vi_button.pack(side=tk.LEFT, padx=5)
        row_idx += 1

        # --- Contenedores para los pasos siguientes (inicialmente ocultos) ---
        # Frame para selección de VI primaria (modo 1VI)
        self.one_vi_config_frame = ttk.Frame(main_frame)
        self.one_vi_config_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=0)
        self.one_vi_config_frame.grid_remove() # Ocultar inicialmente
        self.one_vi_config_frame.columnconfigure(1, weight=1) # Permitir que el combo se expanda
        ttk.Label(self.one_vi_config_frame, text="Agrupar por VI:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.primary_vi_combo = ttk.Combobox(self.one_vi_config_frame, textvariable=self.primary_vi_var, state="readonly")
        self.primary_vi_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.primary_vi_combo.bind("<<ComboboxSelected>>", self.update_available_groups) # Actualizar grupos al seleccionar VI primaria

        # Frame para selección de VI fija y descriptor fijo (modo 2VIs)
        self.two_vi_config_frame = ttk.Frame(main_frame)
        self.two_vi_config_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=0)
        self.two_vi_config_frame.grid_remove() # Ocultar inicialmente
        self.two_vi_config_frame.columnconfigure(1, weight=1)

        ttk.Label(self.two_vi_config_frame, text="VI a Fijar:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.fixed_vi_combo = ttk.Combobox(self.two_vi_config_frame, textvariable=self.fixed_vi_var, state="readonly")
        self.fixed_vi_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.fixed_vi_combo.bind("<<ComboboxSelected>>", self._update_fixed_descriptor_options) # Actualizar descriptores al seleccionar VI fija

        self.fixed_descriptor_label = ttk.Label(self.two_vi_config_frame, text="Valor Fijo:")
        self.fixed_descriptor_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.fixed_descriptor_combo = ttk.Combobox(self.two_vi_config_frame, textvariable=self.fixed_descriptor_var, state="readonly")
        self.fixed_descriptor_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.fixed_descriptor_combo.bind("<<ComboboxSelected>>", self.update_available_groups) # Actualizar grupos al seleccionar descriptor fijo

        row_idx += 1 # Incrementar fila para el siguiente elemento

        # --- Selección Dinámica de Grupos (Reutilizado, pero dentro de su propio frame) ---
        self.group_selection_outer_frame = ttk.LabelFrame(main_frame, text="Selección de Grupos a Comparar")
        self.group_selection_outer_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=10)
        self.group_selection_outer_frame.columnconfigure(0, weight=1)
        self.group_selection_outer_frame.grid_remove() # Ocultar inicialmente
        # Frame interno para los selectores (el que se usaba antes como group_frame)
        self.group_selectors_frame = ttk.Frame(self.group_selection_outer_frame)
        self.group_selectors_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Botón para añadir más grupos (movido aquí)
        add_group_button = ttk.Button(self.group_selection_outer_frame, text="+ Añadir Grupo",
                                      command=self.add_group_selector)
        add_group_button.pack(pady=5, anchor='w', padx=5) # Anclar a la izquierda
        row_idx += 1

        # --- Selección de Columna (En su propio frame) ---
        self.column_frame = ttk.LabelFrame(main_frame, text="Variable a Analizar") # Usar LabelFrame
        self.column_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.column_frame.columnconfigure(1, weight=1)
        self.column_frame.grid_remove() # Ocultar inicialmente
        ttk.Label(self.column_frame, text="Columna:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.column_combo = ttk.Combobox(self.column_frame, textvariable=self.column_var, state="readonly", width=50) # Ajustar width si es necesario
        self.column_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.column_combo.bind("<<ComboboxSelected>>", self._on_column_selected) # Llamar al seleccionar columna
        row_idx += 1

        # --- Supuestos Estadísticos (En su propio frame) ---
        self.assumptions_frame = ttk.LabelFrame(main_frame, text="Supuestos Estadísticos")
        self.assumptions_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        self.assumptions_frame.grid_remove() # Ocultar inicialmente
        ttk.Checkbutton(self.assumptions_frame, text="Datos Paramétricos (Normalidad/Homocedasticidad)", variable=self.parametric_var).pack(anchor="w", padx=5)
        ttk.Checkbutton(self.assumptions_frame, text="Muestras Pareadas (Mismos sujetos en todos los grupos)", variable=self.paired_var).pack(anchor="w", padx=5)
        row_idx += 1

        # --- Nombre del Análisis (En su propio frame) ---
        self.analysis_name_frame = ttk.LabelFrame(main_frame, text="Guardar Análisis Como") # Usar LabelFrame
        self.analysis_name_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.analysis_name_frame.columnconfigure(1, weight=1)
        self.analysis_name_frame.grid_remove() # Ocultar inicialmente
        ttk.Label(self.analysis_name_frame, text="Nombre:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.analysis_name_frame, textvariable=self.analysis_name_var).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        row_idx += 1

        # --- Botones de Acción (En su propio frame) ---
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="e", pady=10)
        self.button_frame.grid_remove() # Ocultar inicialmente
        self.save_button = ttk.Button(self.button_frame, text="Generar Gráfico y Guardar", command=self.generate_analysis, state=tk.DISABLED) # Llamar a generate_analysis
        self.save_button.pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)


    def set_vi_grouping_mode(self, mode):
        """Configura la UI según se elija agrupar por 1 o 2 VIs."""
        self.vi_grouping_mode.set(mode)
        logger.info(f"Modo de agrupación seleccionado: {mode}")

        # Resetear selecciones dependientes
        self.primary_vi_var.set("")
        self.fixed_vi_var.set("")
        self.fixed_descriptor_var.set("")
        self.available_groups_filtered = {}
        self._clear_group_selectors(update_columns=False) # No actualizar columnas aún
        self.column_var.set("")
        self.column_combo['values'] = []
        self.save_button.config(state=tk.DISABLED)

        # Ocultar todos los frames de configuración específicos
        self.one_vi_config_frame.grid_remove()
        self.two_vi_config_frame.grid_remove()
        self.group_selection_outer_frame.grid_remove()
        self.column_frame.grid_remove()
        self.assumptions_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()

        # Mostrar el frame correspondiente al modo seleccionado
        if mode == '1VI':
            self.one_vi_config_frame.grid()
            self.primary_vi_combo['values'] = self.all_vi_names
            # Habilitar/deshabilitar botón 2VI
            self.one_vi_button.state(['pressed', 'disabled'])
            self.two_vi_button.state(['!pressed', '!disabled'])
        elif mode == '2VIs':
            if len(self.all_vi_names) < 2:
                 messagebox.showwarning("No disponible", "Se requieren al menos 2 Variables Independientes definidas en el estudio para agrupar por 2 VIs.", parent=self)
                 self.vi_grouping_mode.set("") # Resetear modo
                 self.one_vi_button.state(['!pressed', '!disabled']) # Resetear botones
                 self.two_vi_button.state(['!pressed', '!disabled'])
                 return
            self.two_vi_config_frame.grid()
            self.fixed_vi_combo['values'] = self.all_vi_names
            self.fixed_descriptor_combo['values'] = [] # Limpiar descriptores fijos
            # Habilitar/deshabilitar botón 1VI
            self.one_vi_button.state(['!pressed', '!disabled'])
            self.two_vi_button.state(['pressed', 'disabled'])
        else: # Si se resetea
             self.one_vi_button.state(['!pressed', '!disabled'])
             self.two_vi_button.state(['!pressed', '!disabled'])


    def _update_fixed_descriptor_options(self, event=None):
        """Actualiza el combobox de descriptores fijos basado en la VI fija seleccionada."""
        fixed_vi_name = self.fixed_vi_var.get()
        self.fixed_descriptor_var.set("") # Limpiar selección anterior
        self.fixed_descriptor_combo['values'] = []
        self.available_groups_filtered = {} # Limpiar grupos disponibles
        self._clear_group_selectors(update_columns=False) # No actualizar columnas aún

        if fixed_vi_name:
            descriptors = self.all_descriptors_by_vi.get(fixed_vi_name, [])
            # Mostrar alias si existen
            display_descriptors = [f"{d} ({self.study_aliases.get(d)})" if self.study_aliases.get(d) else d for d in descriptors]
            self.fixed_descriptor_combo['values'] = sorted(display_descriptors)
            self.fixed_descriptor_label.config(text=f"Valor Fijo para '{fixed_vi_name}':") # Actualizar label
        else:
             self.fixed_descriptor_label.config(text="Valor Fijo:")

        # Ocultar/mostrar pasos siguientes
        self.group_selection_outer_frame.grid_remove()
        self.column_frame.grid_remove()
        self.assumptions_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        self.save_button.config(state=tk.DISABLED)


    def load_initial_data(self):
        """Carga datos iniciales: VIs, alias, frecuencias."""
        try:
            # Cargar detalles del estudio (VIs y Alias)
            details = self.analysis_service.study_service.get_study_details(self.study_id)
            self.all_vi_names = [vi['name'] for vi in details.get('independent_variables', [])]
            self.all_descriptors_by_vi = {vi['name']: vi['descriptors'] for vi in details.get('independent_variables', [])}
            self.study_aliases = details.get('aliases', {})
            logger.debug(f"Datos iniciales cargados: VIs={self.all_vi_names}, Descriptores={self.all_descriptors_by_vi}, Alias={self.study_aliases}")

            # Cargar frecuencias (sin cambios)
            self.load_frequencies()

        except Exception as e:
            logger.error(f"Error cargando datos iniciales para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los datos iniciales del estudio: {e}", parent=self)
            self.destroy()


    def update_available_groups(self, event=None):
        """Actualiza la lista de grupos FILTRADOS basados en las selecciones previas."""
        frequency = self.frequency_var.get()
        mode = self.vi_grouping_mode.get()
        primary_vi = self.primary_vi_var.get() if mode == '1VI' else None
        fixed_vi = self.fixed_vi_var.get() if mode == '2VIs' else None
        fixed_descriptor_display = self.fixed_descriptor_var.get() if mode == '2VIs' else None

        # Limpiar si falta información clave
        if not frequency or not mode or (mode == '1VI' and not primary_vi) or \
           (mode == '2VIs' and (not fixed_vi or not fixed_descriptor_display)):
            self.available_groups_filtered = {}
            self._clear_group_selectors(update_columns=False) # No actualizar columnas aún
            self.group_selection_outer_frame.grid_remove() # Ocultar frame de grupos
            logger.debug("Limpiando grupos: falta información previa.")
            return

        # Obtener el descriptor original si hay alias
        fixed_descriptor = None
        if fixed_descriptor_display:
             # Buscar descriptor original que coincide con el display name (con o sin alias)
             for desc_orig, alias in self.study_aliases.items():
                 if f"{desc_orig} ({alias})" == fixed_descriptor_display:
                     fixed_descriptor = desc_orig
                     break
             if not fixed_descriptor: # Si no tenía alias o no se encontró
                 # Asumir que es el original si no tiene formato de alias
                 fixed_descriptor = fixed_descriptor_display.split(" (")[0]


        try:
            logger.debug(f"Actualizando grupos filtrados: mode={mode}, freq={frequency}, primary={primary_vi}, fixed_vi={fixed_vi}, fixed_desc={fixed_descriptor}")

            # LLAMAR A NUEVO MÉTODO DEL SERVICIO
            filtered_groups = self.analysis_service.get_filtered_discrete_analysis_groups(
                study_id=self.study_id,
                frequency=frequency,
                mode=mode,
                primary_vi_name=primary_vi,
                fixed_vi_name=fixed_vi,
                fixed_descriptor_value=fixed_descriptor
            )

            # Mapear display_name -> original_key
            self.available_groups_filtered = {display_name: key for key, display_name in filtered_groups.items()}
            logger.debug(f"Grupos filtrados disponibles: {self.available_groups_filtered}")

            # Mostrar el frame de selección de grupos y actualizar combos
            self.group_selection_outer_frame.grid()
            self._update_group_combobox_values()

            # Añadir selectores iniciales si no existen
            if not self.group_selector_vars:
                 self.add_group_selector()
                 self.add_group_selector()

            # Ocultar/mostrar pasos siguientes
            self.column_frame.grid_remove()
            self.assumptions_frame.grid_remove()
            self.analysis_name_frame.grid_remove()
            self.button_frame.grid_remove()
            self.save_button.config(state=tk.DISABLED)


        except Exception as e:
            logger.error(f"Error actualizando grupos filtrados: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar los grupos filtrados:\n{e}", parent=self)
            self.available_groups_filtered = {}
            self._clear_group_selectors(update_columns=False) # No actualizar columnas
            self.group_selection_outer_frame.grid_remove()
    def load_frequencies(self):
        """Carga las frecuencias disponibles basadas en las tablas resumen generadas."""
        logger.debug(f"Cargando frecuencias desde tablas resumen para estudio {self.study_id}")
        self.available_frequencies = []
        self.frequency_var.set("") # Limpiar selección
        self.freq_combo['values'] = [] # Limpiar combo

        try:
            # Obtener la ruta base de las tablas resumen
            tables_path = self.analysis_service.get_discrete_analysis_tables_path(self.study_id)
            if tables_path and tables_path.exists():
                # Listar subdirectorios (que representan frecuencias)
                for item in tables_path.iterdir():
                    if item.is_dir():
                        self.available_frequencies.append(item.name)
                self.available_frequencies.sort()
                self.freq_combo['values'] = self.available_frequencies
                logger.debug(f"Tipos de Datos encontradas en tablas resumen: {self.available_frequencies}")
            else:
                 logger.warning(f"Directorio de tablas resumen no encontrado o no existe: {tables_path}")
                 messagebox.showwarning("Sin Tablas", "No se encontraron tablas resumen generadas. Genérelas desde la vista 'Análisis Discreto'.", parent=self)

            if not self.available_frequencies:
                messagebox.showwarning("Sin Tipos de Datos", "No hay frecuencias disponibles en las tablas resumen para análisis.", parent=self)

        except Exception as e:
            logger.error(f"Error cargando frecuencias desde tablas resumen para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar las frecuencias disponibles desde las tablas resumen:\n{e}", parent=self)
            self.available_frequencies = []
            self.freq_combo['values'] = []

    def add_group_selector(self, initial_value=""):
        """Añade una nueva fila para seleccionar un grupo."""
    def add_group_selector(self, initial_value=""):
        """Añade un nuevo selector de grupo (Combobox + botón eliminar)."""
        if not self.group_selectors_frame: return

        selector_frame = ttk.Frame(self.group_selectors_frame)
        selector_frame.pack(fill=tk.X, pady=2)

        group_var = tk.StringVar(value=initial_value)
        # Usar los grupos filtrados
        group_combo = ttk.Combobox(selector_frame, textvariable=group_var, state="readonly",
                                   values=sorted(list(self.available_groups_filtered.keys())))
        group_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        group_combo.bind("<<ComboboxSelected>>", self.update_available_columns)

        # Botón para eliminar este selector (icono basura)
        remove_button = ttk.Button(selector_frame, text="🗑️", width=3, # Usar icono
                                   command=lambda f=selector_frame, v=group_var: self.remove_group_selector(f, v))
        remove_button.pack(side=tk.LEFT)

        # Deshabilitar botón si solo quedan 2 selectores
        if len(self.group_selector_vars) < 2:
             remove_button.config(state=tk.DISABLED)
        # Habilitar botones de los anteriores si ahora hay más de 2
        elif len(self.group_selector_vars) == 2:
             # Habilitar botón del segundo selector (índice 1)
             if len(self.group_selector_frames) > 1:
                 second_frame = self.group_selector_frames[1]
                 if len(second_frame.winfo_children()) > 1:
                     second_frame.winfo_children()[1].config(state=tk.NORMAL)


        self.group_selector_vars.append(group_var)
        self.group_selector_frames.append(selector_frame) # Guardar frame

    def remove_group_selector(self, frame_to_remove, var_to_remove):
        """Elimina una fila de selector de grupo."""
        if len(self.group_selector_frames) <= 2:
            messagebox.showwarning("Acción no permitida",
                                   "Se requieren al menos dos grupos.",
                                   parent=self)
    def remove_group_selector(self, frame_to_remove, var_to_remove):
        """Elimina un selector de grupo."""
        if len(self.group_selector_vars) <= 2:
            messagebox.showwarning("Acción no permitida", "Debe seleccionar al menos dos grupos para comparar.", parent=self)
            return

        try:
            index = self.group_selector_frames.index(frame_to_remove)
            self.group_selector_vars.pop(index)
            self.group_selector_frames.pop(index)
            frame_to_remove.destroy()

            # Deshabilitar botón de eliminar si solo quedan 2
            if len(self.group_selector_vars) == 2:
                 for i in range(2):
                     if len(self.group_selector_frames[i].winfo_children()) > 1:
                         self.group_selector_frames[i].winfo_children()[1].config(state=tk.DISABLED)


            self.update_available_columns()
        except (ValueError, IndexError):
            logger.warning("Intento de eliminar un selector de grupo que ya no existe o índice inválido.")


    def _update_group_combobox_values(self):
        """Actualiza las opciones en todos los combobox de grupo existentes con los grupos FILTRADOS."""
        group_names = sorted(list(self.available_groups_filtered.keys()))
        # Limpiar combos existentes antes de actualizar
        self._clear_group_selectors(update_columns=False) # No actualizar columnas todavía

        # Re-añadir selectores si es necesario (mínimo 2)
        while len(self.group_selector_vars) < 2:
             self.add_group_selector()

        # Actualizar valores en los combos existentes
        for i, var in enumerate(self.group_selector_vars):
             # Encontrar el combo asociado a esta variable (asumiendo orden)
             # Necesitamos iterar sobre los frames guardados
             if i < len(self.group_selector_frames):
                 selector_frame = self.group_selector_frames[i]
                 combo = selector_frame.winfo_children()[0]
                 if isinstance(combo, ttk.Combobox):
                     combo['values'] = group_names
             else:
                 logger.warning(f"Índice {i} fuera de rango para group_selector_frames al actualizar valores.")


        # Disparar actualización de columnas ahora que los combos están listos
        self.update_available_columns()


    def _clear_group_selectors(self, update_columns=True):
        """Limpia las opciones y valores de los selectores de grupo."""
        # Destruir frames existentes y limpiar variables
        for frame in self.group_selector_frames:
            frame.destroy()
        self.group_selector_frames = [] # Limpiar lista de frames
        self.group_selector_vars = [] # Limpiar lista de variables

        if update_columns:
            self.update_available_columns() # Columnas dependen de grupos


    def get_selected_group_keys(self) -> List[str]:
        """Obtiene las claves originales de los grupos seleccionados y válidos de los FILTRADOS."""
        selected_keys = []
        selected_display_names = set()  # Para detectar duplicados
        has_duplicates = False # Inicializar aquí

        for group_var in self.group_selector_vars: # <--- CORREGIR AQUÍ
            display_name = group_var.get()
            if not display_name:
                # Si una variable está vacía, no la consideramos para la selección
                # pero no invalidamos toda la selección necesariamente.
                # Podríamos simplemente continuar al siguiente.
                continue # Saltar variables vacías
                break  # Salir si uno está vacío

            if display_name in selected_display_names:
                messagebox.showerror(
                    "Error de Selección",
                    f"El grupo '{display_name}' está seleccionado más de una vez.",
                    parent=self)
                return []  # Devolver vacío si hay duplicados

            selected_display_names.add(display_name)
            # Buscar en los grupos filtrados
            original_key = self.available_groups_filtered.get(display_name)
            if original_key:
                selected_keys.append(original_key)
            else:
                logger.error(f"Clave original no encontrada para el grupo filtrado seleccionado: '{display_name}'")

        if has_duplicates:
                messagebox.showwarning("Grupos Duplicados", "Ha seleccionado el mismo grupo más de una vez. Los duplicados serán ignorados.", parent=self)
                unique_keys = []
                seen_keys = set()
                for key in selected_keys:
                    if key not in seen_keys:
                        unique_keys.append(key)
                        seen_keys.add(key)
                return unique_keys

        return selected_keys


    def update_available_columns(self, event=None):
        """Actualiza la lista de columnas comunes y muestra los siguientes pasos."""
        frequency = self.frequency_var.get()
        calculation = self.calculation_var.get()
        selected_group_keys = self.get_selected_group_keys()

        # Limpiar columnas y ocultar pasos siguientes si falta info o grupos
        if not frequency or not calculation or len(selected_group_keys) < 2:
            self.available_columns = []
            self.column_combo['values'] = []
            self.column_var.set("")
            self.column_frame.grid_remove()
            self.assumptions_frame.grid_remove()
            self.analysis_name_frame.grid_remove()
            self.button_frame.grid_remove()
            self.save_button.config(state=tk.DISABLED)
            logger.debug("Limpiando columnas y ocultando pasos: falta info o grupos.")
            return

        try:
            logger.debug(f"Actualizando columnas para freq={frequency}, calc={calculation}, grupos={selected_group_keys}")
            common_columns = self.analysis_service.get_common_columns_for_groups(
                self.study_id, frequency, calculation, selected_group_keys
            )
            self.available_columns = sorted(common_columns)
            self.column_combo['values'] = self.available_columns
            logger.debug(f"Columnas comunes encontradas: {self.available_columns}")

            # Mostrar frame de columna
            self.column_frame.grid()

            # Mantener selección si aún es válida, sino limpiar y ocultar resto
            current_column = self.column_var.get()
            if current_column not in self.available_columns:
                self.column_var.set("")
                self._hide_final_steps() # Ocultar pasos finales
            elif self.available_columns: # Si hay columnas y la selección es válida (o se acaba de seleccionar)
                self._show_final_steps() # Mostrar pasos finales
            else: # Si no hay columnas comunes
                 self._hide_final_steps()
                 messagebox.showinfo(
                     "Sin Columnas Comunes",
                     "No se encontraron columnas de datos comunes para la "
                     "combinación de cálculo y grupos seleccionada.",
                     parent=self)


        except Exception as e:
            logger.error(f"Error actualizando columnas comunes: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron cargar las columnas comunes:\n{e}", parent=self)
            self.available_columns = []
            self.column_combo['values'] = []
            self.column_var.set("")
            self._hide_final_steps() # Ocultar pasos finales en caso de error


    def _on_column_selected(self, event=None):
        """Se llama cuando se selecciona una columna, muestra los pasos finales."""
        if self.column_var.get():
            self._show_final_steps()
        else:
            self._hide_final_steps()

    def _show_final_steps(self):
        """Muestra los frames de supuestos, nombre y botones."""
        self.assumptions_frame.grid()
        self.analysis_name_frame.grid()
        self.button_frame.grid()
        self.save_button.config(state=tk.NORMAL) # Habilitar botón de guardar

    def _hide_final_steps(self):
        """Oculta los frames de supuestos, nombre y botones."""
        self.assumptions_frame.grid_remove()
        self.analysis_name_frame.grid_remove()
        self.button_frame.grid_remove()
        self.save_button.config(state=tk.DISABLED) # Deshabilitar botón de guardar


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
                f"{invalid_chars}",
                parent=self)
            return

        if not selected_freq or not selected_calc:
            messagebox.showerror("Error de Validación",
                                   "Seleccione Tipo de Dato y Cálculo.",
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
            "parametric": is_parametric,}
        is_parametric = self.parametric_var.get()
        is_paired = self.paired_var.get()
        mode = self.vi_grouping_mode.get() # Obtener modo
        primary_vi = self.primary_vi_var.get() if mode == '1VI' else None
        fixed_vi = self.fixed_vi_var.get() if mode == '2VIs' else None
        fixed_descriptor_display = self.fixed_descriptor_var.get() if mode == '2VIs' else None

        # --- Validaciones (igual que antes) ---
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
                f"{invalid_chars}",
                parent=self)
            return

        if not selected_freq or not selected_calc:
            messagebox.showerror("Error de Validación",
                                   "Seleccione Tipo de Dato y Cálculo.",
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

        # --- Crear Configuración (añadir modo y VIs seleccionadas) ---
        config = {
            "name": analysis_name, # Cambiado de analysis_name a name
            "frequency": selected_freq,
            "calculation": selected_calc,
            "groups": selected_group_keys,  # Guardar las claves originales
            "column": selected_col,
            "parametric": is_parametric,
            "paired": is_paired,
            # Nuevos campos para reconstruir título/leyenda y para lógica interna
            "grouping_mode": mode,
            "primary_vi_name": primary_vi,
            "fixed_vi_name": fixed_vi,
            "fixed_descriptor_display": fixed_descriptor_display, # Guardar display name con alias
        }


        # --- Llamar al Servicio ---
        try:
            self.title("Ejecutando Análisis...")
            self.save_button.config(state=tk.DISABLED) # Deshabilitar botón
            self.update_idletasks()

            logger.info(f"Llamando a perform_individual_analysis con config: {config}") # LOG ANTES
            result = self.analysis_service.perform_individual_analysis(
                self.study_id, config
            )
            logger.info("Llamada a perform_individual_analysis completada.") # LOG DESPUÉS
            messagebox.showinfo(
                "Análisis Generado",
                f"El análisis '{analysis_name}' se generó correctamente.\n"
                f"Gráfico guardado en: {result['plot_path']}",
                parent=self.parent)  # Mostrar sobre el gestor
            self.destroy()  # Cerrar diálogo de configuración

        except (ValueError, FileNotFoundError) as e:
            logger.warning(f"Error de validación o datos al generar análisis "
                           f"'{analysis_name}': {e}")
            # Añadir log específico para ValueError
            if isinstance(e, ValueError):
                 logger.error(f"ValueError durante generate_analysis: {e}", exc_info=True)
            messagebox.showerror("Error al Generar Análisis", f"{e}",
                                   parent=self)
            self.title("Configurar Análisis Individual") # Restaurar título
            self.save_button.config(state=tk.NORMAL) # Rehabilitar botón
        except Exception as e:
            logger.critical(f"Error inesperado al generar análisis "
                            f"'{analysis_name}': {e}", exc_info=True)
            messagebox.showerror("Error Crítico",
                                   f"Ocurrió un error inesperado:\n{e}",
                                   parent=self)
            self.title("Configurar Análisis Individual") # Restaurar título
            self.save_button.config(state=tk.NORMAL) # Rehabilitar botón


# Para pruebas rápidas
if __name__ == '__main__':
    from pathlib import Path  # Importar Path para el dummy
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal

    # --- Dummies (igual que en el manager) ---
    class DummyAnalysisService:
        def __init__(self):
            # Simular StudyService anidado para alias y VIs
            class DummyStudyService:
                 def get_study_details(self, study_id):
                     print(f"DummyStudyService: get_study_details({study_id})")
                     # Simular VIs para _identify_study_groups
                     return {'independent_variables': [
                                 {'name': 'Tipo', 'descriptors': ['CMJ', 'SJ']},
                                 {'name': 'Cond', 'descriptors': ['PRE', 'POST', 'TipoA', 'TipoB', 'TipoC']}
                             ]}
                 def get_study_aliases(self, study_id):
                     print(f"DummyStudyService: get_study_aliases({study_id})")
                     return {'CMJ': 'Salto CM', 'PRE': 'Antes', 'POST': 'Despues'}
            self.study_service = DummyStudyService()
            # Simular FileService mínimo
            class DummyFileService:
                def _get_study_path(self, study_id): return Path(f'/fake/study_{study_id}')
                def get_study_files(self, study_id, page, per_page, file_type, frequency):
                    # Simular algunos archivos válidos
                    return ([
                        {'path': Path('/fake/study_1/Pte01/Cinematica/Pte01_CMJ_PRE_01_Cinematica.txt')},
                        {'path': Path('/fake/study_1/Pte01/Cinematica/Pte01_CMJ_POST_01_Cinematica.txt')},
                        {'path': Path('/fake/study_1/Pte02/Cinematica/Pte02_SJ_TipoA_01_Cinematica.txt')},
                        {'path': Path('/fake/study_1/Pte02/Cinematica/Pte02_SJ_TipoB_01_Cinematica.txt')},
                    ], 4)
            self.file_service = DummyFileService()

        # Reimplementar _identify_study_groups aquí para el dummy
        def _identify_study_groups(self, study_id: int, frequency: str = "Cinematica") -> tuple[dict[str, str], set[str]]:
            groups_by_file_base = {}
            unique_group_keys = set()
            study_details = self.study_service.get_study_details(study_id)
            independent_variables = study_details.get('independent_variables', [])
            processed_files, _ = self.file_service.get_study_files(study_id, 1, 1000, 'Processed', frequency)
            for file_info in processed_files:
                filename = file_info['path'].name
                is_valid, extracted = validate_filename_for_study_criteria(filename, independent_variables)
                if is_valid:
                    group_parts = []
                    for i, desc in enumerate(extracted):
                        vi_name = independent_variables[i].get('name', f'VI{i+1}')
                        value = desc if desc is not None else "Nulo"
                        group_parts.append(f"{vi_name}={value}")
                    group_key = ";".join(group_parts) if group_parts else "SinGrupo"
                    file_base_key = file_info['path'].stem.split(f'_{frequency}')[0]
                    groups_by_file_base[file_base_key] = group_key
                    unique_group_keys.add(group_key)
            return groups_by_file_base, unique_group_keys

        def get_discrete_analysis_groups(self, study_id, frequency):
            print(f"Dummy: get_discrete_analysis_groups({study_id}, {frequency})")
            # Usar _identify_study_groups del dummy
            _, unique_group_keys = self._identify_study_groups(study_id, frequency)
            aliases = self.study_service.get_study_aliases(study_id)
            groups = []
            for group_key in unique_group_keys:
                display_parts = []
                if group_key != "SinGrupo":
                    for part in group_key.split(';'):
                        vi_name, desc_value = part.split('=', 1)
                        alias = aliases.get(desc_value, desc_value)
                        display_parts.append(f"{vi_name}: {alias}")
                display_name = ", ".join(display_parts) if display_parts else "Grupo General"
                groups.append((display_name, group_key))
            groups.sort()
            return groups

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
