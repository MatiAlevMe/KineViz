import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, Canvas, Scrollbar, Frame
from pathlib import Path # Para construir ruta de ayuda
# Importar NUEVO validador de datos y validador de nombres de archivo
from kineviz.ui.utils.validators import validate_study_iv_data, validate_filename_for_study_criteria
import logging # Importar logging
# Importar FileService para obtener archivos y Path para manejar rutas
# Nota: FileService se importa aquí para consistencia, aunque también se usa en __init__
from kineviz.core.services.file_service import FileService
from pathlib import Path
# Import AppSettings for type hinting and style utilities for font scaling
from kineviz.config.settings import AppSettings
from kineviz.ui.utils.style import get_scaled_font, DEFAULT_FONT_SIZE
from kineviz.ui.widgets.tooltip import Tooltip # Import the new Tooltip class


logger = logging.getLogger(__name__) # Logger para este módulo

class StudyDialog(Toplevel):
    # Añadir study_to_edit, on_save_callback, and settings
    def __init__(self, parent, study_service, settings: AppSettings, study_to_edit=None, on_save_callback=None):
        super().__init__(parent)
        self.study_service = study_service
        self.settings = settings # Store AppSettings instance
        self.file_service = FileService(study_service, self.settings) # Necesitamos FileService para buscar archivos
        self.study_to_edit = study_to_edit
        self.on_save_callback = on_save_callback
        self.is_editing = bool(study_to_edit) # Flag para modo edición

        # Estructura para almacenar VIs y sus sub-valores en la UI
        # Lista de diccionarios: [{'name_var': StringVar, 'descriptor_vars': [StringVar], 'frame': Frame, 'desc_frames': [Frame], 'allows_combination_var': BooleanVar, 'is_mandatory_var': BooleanVar}]
        self.independent_variables_ui = []

        self.title("Editar Estudio" if self.is_editing else "Nuevo Estudio")
        # Aumentar altura para VIs/sub-valores
        # self.geometry("600x550") # Initial size will be determined by content or set after widgets are created
        self.resizable(True, True) # Permitir redimensionar

        # Variables para campos fijos
        self.var_nombre = tk.StringVar()
        self.var_num_sujetos = tk.StringVar()
        self.var_cantidad_intentos = tk.StringVar()

        # Calculate scaled font once
        self.scaled_font_tuple = get_scaled_font(DEFAULT_FONT_SIZE, self.settings.font_scale)

        # Cargar datos si estamos editando (ahora carga VIs)
        if self.is_editing:
            self._load_study_data()

        self.create_form()

        # Centrar diálogo en la ventana padre
        self.transient(parent)
        self.grab_set()
        # Calcular posición para centrar (opcional pero mejora UX)
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = 600
        dialog_height = 450
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')

    def _show_input_help(self, title: str, message: str):
        """Muestra un popup de ayuda simple."""
        messagebox.showinfo(title, message, parent=self)

    def _load_study_data(self):
        """Carga los datos del estudio existente en las variables del formulario."""
        try:
            # Obtener detalles del estudio usando el servicio
            study_details = self.study_service.get_study_details(self.study_to_edit['id']) # Asumiendo que study_to_edit tiene 'id'
            self.var_nombre.set(study_details.get('name', ''))
            self.var_num_sujetos.set(str(study_details.get('num_subjects', '')))
            self.var_cantidad_intentos.set(str(study_details.get('attempts_count', '')))

            # Cargar estructura de VIs y sub-valores
            # get_study_details ya devuelve la estructura Python parseada
            self.initial_independent_variables = study_details.get('independent_variables', [])

        except Exception as e:
            logger.error(f"No se pudieron cargar los datos del estudio {self.study_to_edit.get('id', 'N/A')} para edición: {e}", exc_info=True)
            messagebox.showerror("Error al Cargar", f"No se pudieron cargar los datos del estudio:\n{e}", parent=self)
            self.destroy() # Cerrar diálogo si no se pueden cargar datos


    def create_form(self):
        # --- Setup for scrollable area ---
        # Outer container that holds canvas and scrollbars
        dialog_content_container = ttk.Frame(self)
        dialog_content_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(dialog_content_container, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(dialog_content_container, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(dialog_content_container, orient="horizontal", command=canvas.xview)
        
        # This is the frame where all original dialog content will go
        scrollable_main_frame = ttk.Frame(canvas, padding="20")

        scrollable_main_frame.bind(
            "<Configure>",
            lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")) if c.winfo_exists() else None
        )
        # Removed problematic canvas.bind("<Configure>") that forced inner frame width


        canvas.interior_id = canvas.create_window((0, 0), window=scrollable_main_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout for canvas and scrollbars within dialog_content_container
        dialog_content_container.grid_rowconfigure(0, weight=1)
        dialog_content_container.grid_columnconfigure(0, weight=1)

        canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        # --- End scrollable area setup ---

        # All original content now goes into scrollable_main_frame
        main_frame = scrollable_main_frame

        # Configurar grid layout para mejor alineación
        main_frame.columnconfigure(1, weight=1) # Columna de Entries expandible

        row_idx = 0

        # --- Campos Fijos ---
        ttk.Label(main_frame, text="Nombre del Estudio:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        nombre_frame = ttk.Frame(main_frame)
        nombre_frame.grid(row=row_idx, column=1, sticky="ew")
        ttk.Entry(nombre_frame, textvariable=self.var_nombre, font=self.scaled_font_tuple).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        nombre_help_long_text = "Nombre descriptivo para el estudio.\nEj: Estudio Piloto Marcha, Análisis Comparativo CMJ"
        nombre_help_short_text = "Nombre descriptivo del estudio."
        nombre_help_button = ttk.Button(nombre_frame, text="?", width=3, style="Help.TButton",
                                        command=lambda: self._show_input_help("Ayuda: Nombre del Estudio", nombre_help_long_text))
        nombre_help_button.pack(side=tk.LEFT)
        Tooltip(nombre_help_button, text=nombre_help_long_text, short_text=nombre_help_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        ttk.Label(main_frame, text="Cantidad de Participantes:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        num_sujetos_frame = ttk.Frame(main_frame)
        num_sujetos_frame.grid(row=row_idx, column=1, sticky="ew")
        ttk.Entry(num_sujetos_frame, textvariable=self.var_num_sujetos, font=self.scaled_font_tuple).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        num_sujetos_long_text = "Número entero positivo que representa la cantidad máxima de participantes en el estudio.\nEj: 15"
        num_sujetos_short_text = "Cantidad máxima de participantes."
        num_sujetos_help_button = ttk.Button(num_sujetos_frame, text="?", width=3, style="Help.TButton",
                                             command=lambda: self._show_input_help("Ayuda: Cantidad de Participantes", num_sujetos_long_text))
        num_sujetos_help_button.pack(side=tk.LEFT)
        Tooltip(num_sujetos_help_button, text=num_sujetos_long_text, short_text=num_sujetos_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        ttk.Label(main_frame, text="Cantidad de Intento(s) de Prueba:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=5)
        intentos_frame = ttk.Frame(main_frame)
        intentos_frame.grid(row=row_idx, column=1, sticky="ew")
        ttk.Entry(intentos_frame, textvariable=self.var_cantidad_intentos, font=self.scaled_font_tuple).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        intentos_long_text = "Número entero positivo que representa la cantidad máxima de intentos por cada combinación de sub-valores de VIs para cada participante.\nEj: 3"
        intentos_short_text = "Cantidad máxima de intentos por prueba."
        intentos_help_button = ttk.Button(intentos_frame, text="?", width=3, style="Help.TButton",
                                          command=lambda: self._show_input_help("Ayuda: Cantidad de Intento(s)", intentos_long_text))
        intentos_help_button.pack(side=tk.LEFT)
        Tooltip(intentos_help_button, text=intentos_long_text, short_text=intentos_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1

        # --- Sección de Variables Independientes Dinámicas ---
        # Usar un Frame normal para poder añadir un botón de ayuda al título
        iv_title_frame = ttk.Frame(main_frame)
        iv_title_frame.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=5, pady=(10,0)) # pady top only
        
        # Use default TLabelframe.Label style for this title, which is scaled
        ttk.Label(iv_title_frame, text="Variable(s) Independientes (VIs)", style="TLabelframe.Label").pack(side=tk.LEFT, anchor="w")
        iv_title_long_text = ("Las VIs definen las condiciones o factores que varían en su estudio.\n"
                              "Cada VI tiene 'sub-valores' (niveles o categorías).\n"
                              "Ej: VI 'Condicion' con sub-valores 'PRE', 'POST'.\n"
                              "Los nombres de archivo deben reflejar estos sub-valores en el orden definido aquí.")
        iv_title_short_text = "Define condiciones/factores del estudio y sus niveles."
        iv_title_help_button = ttk.Button(iv_title_frame, text="?", width=3, style="Help.TButton",
                                          command=lambda: self._show_input_help("Ayuda: Variables Independientes (VIs)", iv_title_long_text))
        iv_title_help_button.pack(side=tk.LEFT, padx=(5,0))
        Tooltip(iv_title_help_button, text=iv_title_long_text, short_text=iv_title_short_text, enabled=self.settings.enable_hover_tooltips)
        row_idx += 1 # Incrementar fila para el contenedor de VIs

        iv_frame = ttk.Frame(main_frame, relief="groove", borderwidth=1) # Contenedor para el canvas de VIs
        iv_frame.grid(row=row_idx, column=0, columnspan=2, sticky="nsew", padx=5, pady=(0,10)) # pady bottom only
        iv_frame.columnconfigure(0, weight=1) 
        main_frame.rowconfigure(row_idx, weight=1) 
        self.iv_container = iv_frame 
        row_idx += 1

        # --- Canvas y Scrollbar para VIs ---
        iv_canvas = Canvas(self.iv_container, borderwidth=0, highlightthickness=0)
        iv_scrollbar = ttk.Scrollbar(self.iv_container, orient="vertical", command=iv_canvas.yview)
        # Frame interior que contendrá las VIs
        self.iv_scrollable_frame = ttk.Frame(iv_canvas)

        self.iv_scrollable_frame.bind(
            "<Configure>",
            lambda e: iv_canvas.configure(scrollregion=iv_canvas.bbox("all"))
        )
        iv_canvas.create_window((0, 0), window=self.iv_scrollable_frame, anchor="nw")
        iv_canvas.configure(yscrollcommand=iv_scrollbar.set)

        iv_canvas.pack(side="left", fill="both", expand=True)
        iv_scrollbar.pack(side="right", fill="y")
        # --- Fin Canvas y Scrollbar ---

        # Botón para añadir VI (dentro del frame principal, debajo del contenedor scrollable)
        add_iv_button_frame = ttk.Frame(main_frame)
        add_iv_button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=15, pady=(5,0))
        self.add_iv_button = ttk.Button(add_iv_button_frame, text="+ Añadir Variable Independiente", style="Celeste.TButton", command=self.add_independent_variable_ui)
        self.add_iv_button.pack()
        # Deshabilitar si estamos editando
        if self.is_editing:
            self.add_iv_button.config(state=tk.DISABLED)
        row_idx += 1

        # Cargar VIs iniciales (si estamos editando)
        initial_ivs_to_load = self.initial_independent_variables if self.is_editing else []
        if not initial_ivs_to_load and not self.is_editing:
             # Añadir una VI vacía por defecto al crear nuevo estudio
             self.add_independent_variable_ui()
        else:
             for iv_data in initial_ivs_to_load:
                 self.add_independent_variable_ui(
                     name_value=iv_data.get('name', ''),
                     descriptors_values=iv_data.get('descriptors', []),
                     allows_combination_value=iv_data.get('allows_combination', False), # Default to False if not present
                     is_mandatory_value=iv_data.get('is_mandatory', False) # Default to False
                 )

        # --- Frame para botones (Guardar, Cancelar, Ayuda) ---
        button_frame = ttk.Frame(main_frame)
        # Usar row_idx actual, que está después del botón "+ Añadir VI"
        button_frame.grid(row=row_idx, column=0, columnspan=2, sticky="se", pady=20, padx=5)
        # No configurar rowconfigure aquí, dejar que los botones estén al final

        # El estilo "Help.TButton" ahora se define globalmente en MainWindow
        # help_button = ttk.Button(button_frame, text="?", width=3, style="Help.TButton", command=self.show_iv_help) # Botón de ayuda eliminado
        # help_button.pack(side=tk.LEFT, padx=(0, 10)) # A la izquierda de Cancelar

        ttk.Button(button_frame, text="Guardar", style="Green.TButton", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

        # Set minsize after widgets are created in scrollable_main_frame
        self.update_idletasks() # Process pending operations
        # Ensure canvas and scrollable_main_frame have their sizes computed
        scrollable_main_frame.update_idletasks() 
        canvas.update_idletasks()
        
        # Set a minimum size for the Toplevel dialog
        self.minsize(500, 400) # Set a reasonable fixed minimum size
        # Initial geometry is set in __init__


    def add_independent_variable_ui(self, name_value="", descriptors_values=None, allows_combination_value=False, is_mandatory_value=False):
        """
        Añade una nueva sección para una Variable Independiente.
        Incluye checkboxes para 'allows_combination' y 'is_mandatory'.
        """
        if descriptors_values is None:
            descriptors_values = []

        # Frame principal para esta VI (dentro del scrollable_frame)
        vi_frame = ttk.Frame(self.iv_scrollable_frame, padding="5", relief="groove", borderwidth=1)
        vi_frame.pack(fill=tk.X, pady=5, padx=5)

        # --- Fila para Nombre VI y botones ---
        vi_header_frame = ttk.Frame(vi_frame)
        vi_header_frame.pack(fill=tk.X)

        vi_name_var = tk.StringVar(value=name_value)
        vi_name_entry = ttk.Entry(vi_header_frame, textvariable=vi_name_var, width=25, font=self.scaled_font_tuple) # Ajustar ancho para botón
        vi_name_entry.pack(side=tk.LEFT, padx=(5,0), pady=5, fill=tk.X, expand=True)
        # Permitir editar nombre VI en modo edición
        # vi_name_entry.config(state='readonly' if self.is_editing else 'normal')

        if not self.is_editing:
            vi_name_long_text = "Nombre corto y descriptivo para la Variable Independiente.\nEvite espacios y caracteres especiales.\nEj: Condicion, Grupo, TipoSalto"
            vi_name_short_text = "Nombre corto para la VI (sin espacios/especiales)."
            vi_name_help_button = ttk.Button(vi_header_frame, text="?", width=3, style="Help.TButton",
                                              command=lambda: self._show_input_help("Ayuda: Nombre de VI", vi_name_long_text))
            vi_name_help_button.pack(side=tk.LEFT, padx=(2,5), pady=5)
            Tooltip(vi_name_help_button, text=vi_name_long_text, short_text=vi_name_short_text, enabled=self.settings.enable_hover_tooltips)


        # Botón para añadir sub-valor a ESTA VI
        add_desc_button = ttk.Button(vi_header_frame, text="+", width=3, style="Celeste.TButton",
                                     command=lambda v=vi_name_var: self.add_descriptor_ui(v))
        add_desc_button.pack(side=tk.LEFT, padx=(0,5))
        if self.is_editing:
            add_desc_button.config(state=tk.DISABLED)

        # Botón para eliminar ESTA VI
        remove_vi_button = ttk.Button(vi_header_frame, text="🗑️", width=3,
                                      command=lambda f=vi_frame, v=vi_name_var: self.remove_independent_variable_ui(f, v))
        remove_vi_button.pack(side=tk.LEFT, padx=(0, 5))
        if self.is_editing:
            remove_vi_button.config(state=tk.DISABLED)

        # --- Contenedor para sub-valores de esta VI ---
        descriptors_container = ttk.Frame(vi_frame, padding="5 0 0 5") # Indentación izquierda
        descriptors_container.pack(fill=tk.X)

        # --- Checkboxes para flags de VI ---
        # Further reduced pady for vi_flags_frame to match inter-descriptor spacing
        vi_flags_frame = ttk.Frame(vi_frame, padding="5 0 0 5") # Padding: top, right, bottom, left
        vi_flags_frame.pack(fill=tk.X, pady=(1,0), anchor="w") # Anchor west, top padding changed from 2 to 1

        allows_combination_var = tk.BooleanVar(value=allows_combination_value)
        is_mandatory_var = tk.BooleanVar(value=is_mandatory_value)

        # Checkbox "¿Multiple?"
        multiple_frame = ttk.Frame(vi_flags_frame)
        multiple_frame.pack(anchor="w")
        allows_combination_cb = ttk.Checkbutton(
            multiple_frame,
            text="¿Multiple?",
            variable=allows_combination_var,
        )
        allows_combination_cb.pack(side=tk.LEFT)
        multiple_long_text = ("Permite que un archivo o intento se asocie con MÁS DE UN sub-valor de esta VI simultáneamente.\n\n"
                              "Ejemplo: VI 'Equipamiento' con sub-valores 'Zapatillas', 'Canilleras', 'Vendas'.\n"
                              "Si 'Equipamiento' es Múltiple, un archivo podría ser:\n"
                              "  `P01 Zapatillas 01.txt` y `P01 Zapatillas 01.txt` (P01 usa Zapatillas Y Canilleras).\n"
                              "Si NO es Múltiple, un archivo solo puede tener UN sub-valor de 'Equipamiento':\n"
                              "  `P01 Zapatillas 01.txt` O `P01 Canilleras 01.txt`, pero no ambos para la misma VI.")
        multiple_short_text = "Permite asociar múltiples sub-valores de esta VI a un archivo."
        multiple_help_button = ttk.Button(multiple_frame, text="?", width=3, style="Help.TButton",
                                          command=lambda: self._show_input_help("Ayuda: VI Múltiple", multiple_long_text))
        multiple_help_button.pack(side=tk.LEFT, padx=(2,0))
        Tooltip(multiple_help_button, text=multiple_long_text, short_text=multiple_short_text, enabled=self.settings.enable_hover_tooltips)


        # Checkbox "¿Obligatorio?" (se empaquetará/desempaquetará dinámicamente)
        # Crear el widget pero no empaquetarlo inicialmente si no es necesario
        # Este se empaqueta/desempaqueta en _update_mandatory_checkbox_visibility_and_state
        # por lo que el frame para el botón de ayuda debe ser creado aquí y pasado.
        self.mandatory_frame_for_vi = ttk.Frame(vi_flags_frame) # Guardar referencia al frame para empaquetar/desempaquetar
        # No empaquetar self.mandatory_frame_for_vi aquí, se hace en _update_mandatory_checkbox_visibility_and_state

        is_mandatory_cb_widget = ttk.Checkbutton(
            self.mandatory_frame_for_vi, 
            text="¿Obligatorio?",
            variable=is_mandatory_var
        )
        # is_mandatory_cb_widget se empaqueta dentro de self.mandatory_frame_for_vi en _update_mandatory_checkbox_visibility_and_state
        
        # El command de allows_combination_cb se define después de crear is_mandatory_cb_widget
        # y ahora también necesita el frame del botón de ayuda para el obligatorio.
        allows_combination_cb.config(command=lambda acv=allows_combination_var, im_cb=is_mandatory_cb_widget, im_frame=self.mandatory_frame_for_vi: self._on_allows_combination_changed(acv, im_cb, im_frame))


        if self.is_editing:
            allows_combination_cb.config(state=tk.DISABLED)
            multiple_help_button.config(state=tk.DISABLED) # También deshabilitar botón de ayuda
            # El estado de is_mandatory_cb_widget se manejará en _update_mandatory_checkbox_visibility_and_state

        # Guardar referencias
        vi_ui_data = {
            'name_var': vi_name_var,
            'descriptor_vars': [],
            'frame': vi_frame,
            'descriptors_container': descriptors_container,
            'desc_frames': [],
            'allows_combination_var': allows_combination_var,
            'is_mandatory_var': is_mandatory_var,
            'is_mandatory_cb_widget': is_mandatory_cb_widget # Guardar referencia al widget
        }
        self.independent_variables_ui.append(vi_ui_data)

        # Estado inicial y visibilidad del checkbox "Obligatorio" para esta VI específica
        self._update_mandatory_checkbox_visibility_and_state(
            allows_combination_var, # Pasar la variable
            is_mandatory_cb_widget, # Pasar el widget
            self.mandatory_frame_for_vi # Pasar el frame contenedor del checkbox y su ayuda
        )

        # Añadir sub-valores iniciales para esta VI
        if not descriptors_values and not self.is_editing:
            # Añadir 2 sub-valores vacíos por defecto al crear nueva VI
            self.add_descriptor_ui(vi_name_var)
            self.add_descriptor_ui(vi_name_var)
        else:
            for desc_value in descriptors_values:
                self.add_descriptor_ui(vi_name_var, value=desc_value)

    def remove_independent_variable_ui(self, frame_to_remove, vi_name_var_to_remove):
        """Elimina la sección de una Variable Independiente."""
        if self.is_editing: return # No permitir eliminar en modo edición

        found_index = -1
        for i, vi_data in enumerate(self.independent_variables_ui):
            if vi_data['name_var'] == vi_name_var_to_remove:
                found_index = i
                break

        if found_index != -1:
            self.independent_variables_ui.pop(found_index)
            frame_to_remove.destroy()
        else:
            logger.warning("Intento de eliminar una VI que no está en la lista UI.")

    def add_descriptor_ui(self, vi_name_var, value=""):
        """Añade una fila para un sub-valor dentro de una VI específica."""
        if self.is_editing: return # No permitir añadir en modo edición

        # Encontrar la VI correspondiente en la UI
        target_vi_data = None
        for vi_data in self.independent_variables_ui:
            if vi_data['name_var'] == vi_name_var:
                target_vi_data = vi_data
                break

        if not target_vi_data:
            logger.error(f"No se encontró la VI UI para añadir sub-valor (Nombre Var: {vi_name_var.get()})")
            return

        container = target_vi_data['descriptors_container']
        desc_frame = ttk.Frame(container)
        desc_frame.pack(fill=tk.X, pady=1)

        desc_var = tk.StringVar(value=value)
        desc_entry_frame = ttk.Frame(desc_frame) # Frame para entry y botón de ayuda
        desc_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))

        desc_entry = ttk.Entry(desc_entry_frame, textvariable=desc_var, font=self.scaled_font_tuple)
        desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if self.is_editing:
            desc_entry.config(state='readonly')
        else:
            desc_long_text = "Valor o nivel específico de la Variable Independiente.\nEvite espacios y caracteres especiales. No usar 'Nulo'.\nEj: PRE, POST, Control, Experimental, CMJ, SJ"
            desc_short_text = "Valor específico de la VI (sin espacios/especiales, no 'Nulo')."
            desc_help_button = ttk.Button(desc_entry_frame, text="?", width=3, style="Help.TButton",
                                           command=lambda: self._show_input_help("Ayuda: Sub-valor de VI", desc_long_text))
            desc_help_button.pack(side=tk.LEFT, padx=(2,0))
            Tooltip(desc_help_button, text=desc_long_text, short_text=desc_short_text, enabled=self.settings.enable_hover_tooltips)


        # Botón para eliminar este sub-valor
        remove_desc_button = ttk.Button(desc_frame, text="🗑️", width=3,
                                        command=lambda f=desc_frame, v=desc_var, vi_v=vi_name_var: self.remove_descriptor_ui(f, v, vi_v))
        remove_desc_button.pack(side=tk.LEFT, padx=(5,5)) # Ajustar padx
        if self.is_editing:
            remove_desc_button.config(state=tk.DISABLED)

        target_vi_data['descriptor_vars'].append(desc_var)
        target_vi_data['desc_frames'].append(desc_frame)

    def remove_descriptor_ui(self, frame_to_remove, desc_var_to_remove, vi_name_var):
        """Elimina una fila de sub-valor de una VI específica."""
        if self.is_editing: return # No permitir eliminar en modo edición

        # Encontrar la VI
        target_vi_data = None
        for vi_data in self.independent_variables_ui:
            if vi_data['name_var'] == vi_name_var:
                target_vi_data = vi_data
                break

        if not target_vi_data:
            logger.error(f"No se encontró la VI UI para eliminar sub-valor (Nombre Var VI: {vi_name_var.get()})")
            return

        # Encontrar el sub-valor dentro de la VI
        try:
            index = target_vi_data['descriptor_vars'].index(desc_var_to_remove)
            target_vi_data['descriptor_vars'].pop(index)
            target_vi_data['desc_frames'].pop(index)
            frame_to_remove.destroy()
        except ValueError:
            logger.warning("Intento de eliminar un sub-valor que no está en la lista de la VI.")

    def _on_allows_combination_changed(self, allows_combination_var, is_mandatory_cb_widget, mandatory_frame):
        """
        Callback cuando el estado de 'allows_combination' cambia.
        Actualiza la visibilidad y estado del checkbox 'is_mandatory' y su variable.
        """
        self._update_mandatory_checkbox_visibility_and_state(allows_combination_var, is_mandatory_cb_widget, mandatory_frame)

    def _update_mandatory_checkbox_visibility_and_state(self, allows_combination_var, is_mandatory_cb_widget, mandatory_frame):
        """
        Actualiza la visibilidad y el estado (habilitado/deshabilitado) del checkbox 'is_mandatory'
        y su botón de ayuda.
        También actualiza la variable 'is_mandatory_var' si es necesario.
        """
        # Encontrar la VI correcta para acceder a 'is_mandatory_var'
        target_vi_data = None
        for vi_data_item in self.independent_variables_ui:
            if vi_data_item['allows_combination_var'] == allows_combination_var:
                target_vi_data = vi_data_item
                break
        
        if not target_vi_data:
            logger.warning("No se pudo encontrar la VI data para el checkbox 'Obligatorio'.")
            if mandatory_frame.winfo_ismapped():
                mandatory_frame.pack_forget()
            return

        is_mandatory_var = target_vi_data['is_mandatory_var']
        allows_combination = allows_combination_var.get()

        # Limpiar el frame antes de re-empaquetar
        for widget in mandatory_frame.winfo_children():
            widget.pack_forget()

        if allows_combination:
            if not mandatory_frame.winfo_ismapped():
                mandatory_frame.pack(anchor="w")

            is_mandatory_cb_widget.pack(side=tk.LEFT) # Empaquetar checkbox
            
            # Crear y empaquetar botón de ayuda para "Obligatorio"
            # Este botón se crea aquí porque solo es relevante si "Multiple" está activo.
            mandatory_long_text = ("Este checkbox SOLO aplica si la VI es 'Múltiple'.\n\n"
                                   "Si una VI es Múltiple Y Obligatoria:\n"
                                   "  Se debe especificar AL MENOS UN sub-valor de esta VI en el nombre del archivo.\n"
                                   "  NO se permite 'Nulo' para esta VI.\n"
                                   "  Ej: VI 'Equipamiento' (Múltiple, Obligatoria). Archivo `P01 Zapatillas 01.txt` es válido. `P01 Nulo 01.txt` NO es válido para 'Equipamiento'.\n\n"
                                   "Si una VI es Múltiple pero NO Obligatoria:\n"
                                   "  Se PUEDE usar 'Nulo' para esta VI si no aplica ningún sub-valor.\n"
                                   "  Ej: VI 'Equipamiento' (Múltiple, No Obligatoria). Archivo `P01 Nulo VI2 01.txt` es válido para 'Equipamiento' siempre que exista al menos una VI no nula en el nombre del archivo.")
            mandatory_short_text = "Si Múltiple: ¿Se requiere al menos un sub-valor de esta VI (no 'Nulo')?"
            mandatory_help_button = ttk.Button(mandatory_frame, text="?", width=3, style="Help.TButton",
                                               command=lambda: self._show_input_help("Ayuda: VI Obligatoria (si es Múltiple)", mandatory_long_text))
            mandatory_help_button.pack(side=tk.LEFT, padx=(2,0))
            Tooltip(mandatory_help_button, text=mandatory_long_text, short_text=mandatory_short_text, enabled=self.settings.enable_hover_tooltips)

            current_state = tk.NORMAL if not self.is_editing else tk.DISABLED
            is_mandatory_cb_widget.config(state=current_state)
            mandatory_help_button.config(state=current_state)
        else:
            if mandatory_frame.winfo_ismapped():
                mandatory_frame.pack_forget()
            is_mandatory_var.set(False)
            is_mandatory_cb_widget.config(state=tk.DISABLED) # Estado base si está oculto


    # def show_iv_help(self): # Eliminado según solicitud de centralizar ayuda
    #     """Muestra el archivo de ayuda para VIs."""
    #     try:
    #         # Construir ruta relativa al archivo actual
    #         help_file_path = Path(__file__).parent.parent.parent / "docs" / "help" / "study_dialog_iv_help.txt"
    #         if help_file_path.exists():
    #             # Usar webbrowser para abrir el archivo (más portable)
    #             webbrowser.open(help_file_path.as_uri()) # as_uri() para formato file:///
    #         else:
    #             messagebox.showerror("Error", f"No se encontró el archivo de ayuda:\n{help_file_path}", parent=self)
    #     except Exception as e:
    #         logger.error(f"Error al abrir archivo de ayuda: {e}", exc_info=True)
    #         messagebox.showerror("Error", f"No se pudo abrir el archivo de ayuda:\n{e}", parent=self)


    def save(self):
        # Recolectar datos básicos
        study_data_base = {
            'name': self.var_nombre.get().strip(),
            'num_subjects': self.var_num_sujetos.get().strip(),
            'attempts_count': self.var_cantidad_intentos.get().strip(),
        }

        # Recolectar y validar estructura de VIs según modo (crear/editar)
        if self.is_editing:
            # --- Modo Edición ---
            # Reconstruir VIs usando nombres actualizados y sub-valores originales
            reconstructed_ivs = []
            # Mapear nombres originales a sub-valores originales para fácil acceso
            original_iv_map = {iv.get('name'): iv.get('descriptors', [])
                               for iv in self.initial_independent_variables}

            if len(self.independent_variables_ui) != len(self.initial_independent_variables):
                 # Esto no debería pasar si los botones están deshabilitados
                 logger.error("Discrepancia en número de VIs entre UI y datos iniciales en modo edición.")
                 messagebox.showerror("Error Interno", "Error al procesar VIs en modo edición.", parent=self)
                 return

            for i, vi_ui_data in enumerate(self.independent_variables_ui):
                updated_vi_name = vi_ui_data['name_var'].get().strip()
                # Obtener sub-valores originales basados en la posición inicial
                original_vi_data = self.initial_independent_variables[i]
                original_descriptors = original_vi_data.get('descriptors', [])
                # En modo edición, los flags no cambian, se toman de los datos iniciales
                original_allows_combination = original_vi_data.get('allows_combination', False)
                original_is_mandatory = original_vi_data.get('is_mandatory', False)


                if updated_vi_name and original_descriptors:
                    reconstructed_ivs.append({
                        'name': updated_vi_name,
                        'descriptors': original_descriptors,
                        'allows_combination': original_allows_combination,
                        'is_mandatory': original_is_mandatory
                    })
                else:
                    # Loggear error si falta nombre actualizado o sub-valores originales
                    logger.error(f"Error reconstruyendo VI #{i+1} en modo edición: Nombre='{updated_vi_name}', Sub-valores Originales={original_descriptors}, Flags: AC={original_allows_combination}, IM={original_is_mandatory}")
                    messagebox.showerror("Error Interno", f"Error procesando Variable Independiente #{i+1}.", parent=self)
                    return

            study_data_to_validate = {**study_data_base, 'independent_variables': reconstructed_ivs}

        else:
            # --- Modo Creación ---
            # Recolectar VIs y sub-valores directamente de la UI
            collected_ivs = []
            for vi_ui_data in self.independent_variables_ui:
                vi_name = vi_ui_data['name_var'].get().strip()
                # Recolectar sub-valores de las entradas de esta VI
                descriptors = [desc_var.get().strip() for desc_var in vi_ui_data['descriptor_vars']]
                # Filtrar sub-valores vacíos
                valid_descriptors = [d for d in descriptors if d]
                # Obtener valores de los checkboxes
                allows_combination = vi_ui_data['allows_combination_var'].get()
                is_mandatory = vi_ui_data['is_mandatory_var'].get()

                # Si no se permite combinación, 'is_mandatory' debe ser False
                if not allows_combination:
                    is_mandatory = False

                # Solo añadir VI si tiene nombre y sub-valores válidos
                if vi_name and valid_descriptors:
                    collected_ivs.append({
                        'name': vi_name,
                        'descriptors': valid_descriptors,
                        'allows_combination': allows_combination,
                        'is_mandatory': is_mandatory
                    })

            study_data_to_validate = {**study_data_base, 'independent_variables': collected_ivs}


        # Validar datos (estructura recolectada o reconstruida)
        is_valid, error_message = validate_study_iv_data(study_data_to_validate)
        if not is_valid:
            messagebox.showerror("Datos Inválidos", error_message, parent=self)
            return

        # --- Validación adicional en modo edición (Sujetos e Intentos) ---
        if self.is_editing:
            try:
                new_num_subjects_str = study_data_to_validate.get('num_subjects', '0')
                new_attempts_count_str = study_data_to_validate.get('attempts_count', '0')
                new_num_subjects = int(new_num_subjects_str) if new_num_subjects_str.isdigit() else 0
                new_attempts_count = int(new_attempts_count_str) if new_attempts_count_str.isdigit() else 0

                # Obtener estado actual de archivos
                _, actual_num_subjects, max_attempts_found = self.file_service._get_study_file_details(self.study_to_edit['id'])

                # Validar número de sujetos
                if new_num_subjects < actual_num_subjects:
                    messagebox.showerror(
                        "Error de Validación",
                        f"No se puede reducir el número de sujetos a {new_num_subjects} "
                        f"porque el estudio ya contiene {actual_num_subjects} sujetos distintos.",
                        parent=self
                    )
                    return # Detener guardado

                # Validar número de intentos
                if new_attempts_count < max_attempts_found:
                     messagebox.showerror(
                        "Error de Validación",
                        f"No se puede reducir la cantidad de intentos a {new_attempts_count} "
                        f"porque al menos un sujeto ya tiene {max_attempts_found} intentos registrados.",
                        parent=self
                    )
                     return # Detener guardado

                logger.info(f"Validación de edición (sujetos/intentos) pasada para estudio {self.study_to_edit['id']}.")

            except Exception as e_val_edit:
                 logger.error(f"Error durante validación de edición para estudio {self.study_to_edit['id']}: {e_val_edit}", exc_info=True)
                 messagebox.showerror("Error Interno", f"Ocurrió un error al validar los límites de sujetos/intentos:\n{e_val_edit}", parent=self)
                 return # Detener guardado

        # Preparar datos finales para el servicio (usar datos validados)
        final_study_data = study_data_to_validate.copy()
        # Si estamos editando, necesitamos obtener los alias existentes para no perderlos
        if self.is_editing:
            try:
                existing_details = self.study_service.get_study_details(self.study_to_edit['id'])
                final_study_data['aliases'] = existing_details.get('aliases', {})
            except Exception as e:
                 logger.error(f"Error obteniendo alias existentes para estudio {self.study_to_edit['id']} al guardar: {e}")
                 messagebox.showerror("Error", "No se pudieron obtener los alias existentes. Cambios no guardados.", parent=self)
                 return
        else:
             # Para nuevos estudios, inicializar alias como vacío
             final_study_data['aliases'] = {}


        try:
            if self.is_editing:
                # Actualizar estudio existente
                self.study_service.update_study(
                    self.study_to_edit['id'], final_study_data
                )
                messagebox.showinfo(
                    "Éxito", "Estudio actualizado correctamente", parent=self
                )
            else:
                # Crear nuevo estudio
                self.study_service.create_study(final_study_data)
                messagebox.showinfo(
                    "Éxito", "Estudio creado correctamente", parent=self
                )

            # Llamar al callback si existe
            if self.on_save_callback:
                self.on_save_callback()

            self.destroy()  # Cerrar el diálogo
        except ValueError as ve:  # Capturar errores específicos de validación (ej. nombre duplicado)
            logger.warning(f"Error de validación al guardar estudio: {ve}")
            messagebox.showerror("Error de Validación", str(ve), parent=self)
        except Exception as e:  # Capturar errores generales
            study_id_log = self.study_to_edit['id'] if self.is_editing else "nuevo"
            logger.error(
                f"Error inesperado al guardar estudio {study_id_log}: {e}", exc_info=True
            )
            messagebox.showerror(
                "Error al Guardar", f"Ocurrió un error inesperado:\n{str(e)}", parent=self
            )
