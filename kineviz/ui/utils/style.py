import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk

# Define base font families and sizes (can be adjusted)
BASE_FONT_FAMILY = "Helvetica" # Consider Segoe UI for Windows, San Francisco for macOS
DEFAULT_FONT_SIZE = 10
LABEL_FONT_SIZE = 12
HEADER_FONT_SIZE = 12 # For TLabelframe.Label
TITLE_FONT_SIZE = 18 # Reduced from 24 for better scaling control
TREEVIEW_HEADING_FONT_SIZE = 10

THEMES = {
    "Claro": { # Renamed from "Light"
        "bg": "#F0F0F0",  # System-like light gray
        "fg": "#000000",  # Black
        "widget_bg": "#FFFFFF", # White for entry fields, treeview
        "widget_fg": "#000000",
        "button_bg": "#E1E1E1",
        "button_fg": "#000000",
        "disabled_fg": "#A3A3A3",
        "select_bg": "#0078D7",  # Blue selection
        "select_fg": "#FFFFFF",
        "treeview_heading_bg": "#3078E4",
        "tooltip_bg": "#FFFFE0", # Light yellow for tooltips
        "tooltip_fg": "#000000",
        "danger_bg": "#FF0000", # Red for danger buttons
        "danger_fg": "#FFFFFF",
        "help_bg": "#0078D7",   # Blue for help buttons
        "help_fg": "#FFFFFF",
        "green_bg": "#28A745",  # Green for success/green buttons
        "green_fg": "#FFFFFF",
        "celeste_bg": "#AFEEEE", # Pale turquoise
        "celeste_fg": "#000000",
        "hover_bg": "#000000",  # Blanco (background se ilumina en azul)
        "hover_text": "#F0F0F0",  # Blanco (texto cambia a blanco)
        "treeview_heading_hover_bg": "#F0F0F0",
        "treeview_heading_hover_text": "#252526",
    },
    "Oscuro": { # Renamed from "Dark"
        "bg": "#252526",  # Dark gray
        "fg": "#DADADA",  # Light gray text
        "widget_bg": "#1E1E1E", # Very dark gray for entry fields
        "widget_fg": "#DADADA",
        "button_bg": "#3E3E3E", # Medium-dark gray for buttons
        "button_fg": "#F1F1F1",
        "disabled_fg": "#6A6A6A",
        "select_bg": "#007ACC",  # Brighter blue for selection
        "select_fg": "#FFFFFF",
        "treeview_heading_bg": "#830808",
        "tooltip_bg": "#3E3E3E",
        "tooltip_fg": "#F1F1F1",
        "danger_bg": "#CF6679", # Darker red for danger
        "danger_fg": "#000000",
        "help_bg": "#1E5A96",   # Darker blue for help
        "help_fg": "#FFFFFF",
        "green_bg": "#004516",  # Darker green
        "green_fg": "#FFFFFF",
        "celeste_bg": "#285151", # Darker turquoise
        "celeste_fg": "#DADADA",
        "hover_bg": "#DADADA",  # Blanco (background se ilumina en azul)
        "hover_text": "#252526",  # Negro (texto cambia a negro)
        "treeview_heading_hover_bg": "#252526",
        "treeview_heading_hover_text": "#F0F0F0",
    }
}

def get_scaled_font(base_size: int, scale_factor: float, weight: str = "normal", family: str = BASE_FONT_FAMILY) -> tuple:
    """Calculates scaled font properties."""
    scaled_size = max(6, int(base_size * scale_factor)) # Ensure minimum font size
    return (family, scaled_size, weight)

def get_font_object(base_size: int, scale_factor: float, weight: str = "normal", family: str = BASE_FONT_FAMILY) -> tkFont.Font:
    """Returns a tkFont.Font object, scaled."""
    family, size, weight_str = get_scaled_font(base_size, scale_factor, weight, family)
    return tkFont.Font(family=family, size=size, weight=weight_str)


def apply_theme_and_font(root: tk.Tk, style: ttk.Style, theme_name: str, font_scale: float):
    """
    Applies the selected theme and font scaling to the ttk.Style object.
    :param root: The root tk.Tk window, needed for some global style settings like Combobox list.
    :param style: The ttk.Style object.
    :param theme_name: Name of the theme to apply ('Claro', 'Oscuro').
    :param font_scale: Font scaling factor.
    """
    colors = THEMES.get(theme_name, THEMES["Claro"]) # Default to Claro if theme_name is invalid

    # Attempt to use 'clam' as it's often more customizable. Fallback if not available.
    try:
        style.theme_use('clam')
    except tk.TclError:
        current_theme = style.theme_use() # Get the current theme if clam is not available
        logger.warning(f"'clam' theme not available. Using current theme: {current_theme}")


    # --- General Style Configurations ---
    style.configure('.',
                    background=colors['bg'],
                    foreground=colors['fg'],
                    font=get_scaled_font(DEFAULT_FONT_SIZE, font_scale),
                    relief='flat') # General relief

    style.configure('TFrame', background=colors['bg'])
    style.configure('TLabel',
                    background=colors['bg'],
                    foreground=colors['fg'],
                    font=get_scaled_font(LABEL_FONT_SIZE, font_scale))
    style.configure('Header.TLabel', # For main_view title
                    background=colors['bg'],
                    foreground=colors['fg'],
                    font=get_scaled_font(TITLE_FONT_SIZE, font_scale, weight="bold"))
    style.configure('Title.TLabel', # For dialog titles, study view titles
                    background=colors['bg'],
                    foreground=colors['fg'],
                    font=get_scaled_font(TITLE_FONT_SIZE, font_scale, weight="bold"))


    # --- Button Styles ---
    style.configure('TButton',
                    background=colors['button_bg'],
                    foreground=colors['button_fg'],
                    font=get_scaled_font(DEFAULT_FONT_SIZE, font_scale),
                    padding=6,
                    relief="raised",
                    borderwidth=1)
    style.map('TButton',
              background=[('active', colors['select_bg']), ('pressed', colors['select_bg']), ('disabled', colors['bg'])],
              foreground=[('active', colors['select_fg']), ('pressed', colors['select_fg']), ('disabled', colors['disabled_fg'])])

    style.configure("Help.TButton",
                    background=colors['help_bg'],
                    foreground=colors['help_fg'])
    style.map("Help.TButton",
              background=[('active', colors['select_bg']), ('pressed', colors['select_bg'])])

    style.configure("Danger.TButton",
                    background=colors['danger_bg'],
                    foreground=colors['danger_fg'])
    style.map("Danger.TButton",
              background=[('active', colors['select_bg']), ('pressed', colors['select_bg'])])
              
    style.configure("Green.TButton",
                    background=colors['green_bg'],
                    foreground=colors['green_fg'])
    style.map("Green.TButton",
              background=[('active', colors['select_bg']), ('pressed', colors['select_bg'])])

    style.configure("Celeste.TButton",
                    background=colors['celeste_bg'],
                    foreground=colors['celeste_fg'])
    style.map("Celeste.TButton",
              background=[('active', colors['select_bg']), ('pressed', colors['select_bg'])])


    # --- Entry and Combobox Styles ---
    # (Esta sección controla el padding escalado para Entry y Combobox)
    base_padding_x = 3
    base_padding_y = 2
    # Moderate the scaling of padding so it doesn't grow excessively
    padding_scale_factor = 1 + (font_scale - 1) * 0.4 
    scaled_padding_x = max(1, int(base_padding_x * padding_scale_factor))
    scaled_padding_y = max(1, int(base_padding_y * padding_scale_factor))

    style.configure('TEntry',
                    fieldbackground=colors['widget_bg'],
                    foreground=colors['widget_fg'],
                    insertcolor=colors['fg'], # Cursor color
                    font=get_scaled_font(DEFAULT_FONT_SIZE, font_scale),
                    padding=(scaled_padding_x, scaled_padding_y))
    style.map('TEntry',
              foreground=[('disabled', colors['disabled_fg'])],
              fieldbackground=[('disabled', colors['bg'])])

    # Configuración PRINCIPAL del Combobox (controla el widget visible)
    style.configure('TCombobox',
                    fieldbackground=colors['widget_bg'],  # Fondo del campo de texto
                    foreground=colors['widget_fg'],       # Color del texto
                    selectbackground=colors['select_bg'], # Fondo del texto seleccionado EN EL DROPDOWN
                    selectforeground=colors['select_fg'], # Color del texto seleccionado EN EL DROPDOWN
                    arrowcolor=colors['fg'],              # Color de la flecha del dropdown
                    font=get_scaled_font(DEFAULT_FONT_SIZE, font_scale), # Fuente del texto
                    padding=(scaled_padding_x, scaled_padding_y)) # Padding interno

    # Estados del Combobox (disabled)
    style.map('TCombobox',
        foreground=[('disabled', colors['disabled_fg'])],
        fieldbackground=[('disabled', colors['bg'])])

    # Configuración CRÍTICA del DROPDOWN (Listbox)
    try:
        # 1. Configuración de la FUENTE del dropdown
        tk_scaled_listbox_font = get_font_object(DEFAULT_FONT_SIZE, font_scale)
        font_string_for_option_add = tk_scaled_listbox_font.actual() 
        
        if isinstance(font_string_for_option_add, dict):
            font_tuple = (font_string_for_option_add['family'], 
                        font_string_for_option_add['size'], 
                        font_string_for_option_add['weight'])
            root.option_add('*TCombobox*Listbox.font', font_tuple)
        else:
            root.option_add('*TCombobox*Listbox.font', font_string_for_option_add)

        # 2. Configuración de COLORES del dropdown
        root.option_add('*TCombobox*Listbox.background', colors['widget_bg'])  # Fondo de la lista
        root.option_add('*TCombobox*Listbox.foreground', colors['widget_fg']) # Texto de los ítems
        root.option_add('*TCombobox*Listbox.selectBackground', colors['select_bg']) # Ítem seleccionado
        root.option_add('*TCombobox*Listbox.selectForeground', colors['select_fg']) # Texto seleccionado

        # Explicitly set tk.Canvas background for better theme consistency
        root.option_add('*Canvas.background', colors['bg'])
        # Also set highlightbackground to prevent unexpected border colors if highlightthickness > 0 (though usually it's 0)
        root.option_add('*Canvas.highlightBackground', colors['bg'])

        # Attempt to style tk.Menu (results may vary by OS, especially Windows)
        root.option_add('*Menu.background', colors['bg'])
        root.option_add('*Menu.foreground', colors['fg'])
        root.option_add('*Menu.activeBackground', colors['select_bg'])
        root.option_add('*Menu.activeForeground', colors['select_fg'])
        # For tearoff menus, if ever enabled (tearoff=1)
        root.option_add('*Menubutton.background', colors['button_bg'])
        root.option_add('*Menubutton.foreground', colors['button_fg'])
        
    except Exception as e:
        logger.warning(f"Could not apply global TCombobox Listbox or Menu/Canvas styles: {e}")


    # --- Treeview Style ---
    style.configure('Treeview',
                    background=colors['widget_bg'],
                    foreground=colors['widget_fg'],
                    fieldbackground=colors['widget_bg'], # Background of the rows
                    font=get_scaled_font(DEFAULT_FONT_SIZE, font_scale))
    style.map('Treeview',
              background=[('selected', colors['select_bg'])],
              foreground=[('selected', colors['select_fg'])])

    style.configure('Treeview.Heading',
                    background=colors['treeview_heading_bg'],
                    foreground=colors['fg'],
                    font=get_scaled_font(TREEVIEW_HEADING_FONT_SIZE, font_scale, weight="bold"),
                    relief='raised')
    
    style.map('Treeview.Heading',
              background=[('active', colors['treeview_heading_hover_bg'])],
              foreground=[('active', colors['treeview_heading_hover_text'])])

    # Adjust Treeview row height based on font size
    treeview_font_obj = get_font_object(DEFAULT_FONT_SIZE, font_scale)
    # Approximate row height: font's linespace + scaled padding
    row_height = treeview_font_obj.metrics("linespace") + int(8 * min(1.5, max(0.5, font_scale))) # Ensure scale_factor is positive for padding
    style.configure('Treeview', rowheight=max(18, row_height)) # Ensure a minimum row height


    # --- Other Widget Styles ---
    style.configure('TLabelframe',
                    background=colors['bg'],
                    foreground=colors['fg'],
                    font=get_scaled_font(LABEL_FONT_SIZE, font_scale)) # Font for the frame itself if it had text
    style.configure('TLabelframe.Label',
                    background=colors['bg'],
                    foreground=colors['fg'],
                    font=get_scaled_font(HEADER_FONT_SIZE, font_scale, weight="bold")) # Font for the title of the labelframe

    style.configure('TScrollbar',
                    background=colors['bg'],
                    troughcolor=colors['widget_bg'],
                    arrowcolor=colors['fg'],
                    relief='flat')
    style.map('TScrollbar',
        background=[('active', colors['select_bg'])],
        arrowcolor=[('active', colors['select_fg'])])

    style.configure('TNotebook', background=colors['bg'])
    style.configure('TNotebook.Tab',
                    background=colors['button_bg'],
                    foreground=colors['button_fg'],
                    font=get_scaled_font(DEFAULT_FONT_SIZE, font_scale),
                    padding=[5, 2])
    style.map('TNotebook.Tab',
              background=[('selected', colors['select_bg']), ('active', colors['widget_bg'])],
              foreground=[('selected', colors['select_fg']), ('active', colors['fg'])])

    # Tooltip style (if using a custom tooltip solution that uses ttk.Label)
    style.configure("Tooltip.TLabel",
                    background=colors['tooltip_bg'],
                    foreground=colors['tooltip_fg'],
                    font=get_scaled_font(DEFAULT_FONT_SIZE -1, font_scale), # Slightly smaller
                    borderwidth=1,
                    relief="solid")

    # Progressbar
    style.configure("TProgressbar",
                    thickness=int(20 * min(1.5, font_scale)), # Scale thickness a bit
                    background=colors['green_bg'], # Color of the bar
                    troughcolor=colors['widget_bg']) # Color of the trough
    
    # Checkbutton & Radiobutton
    style.configure("TCheckbutton",
                    background=colors['bg'],
                    foreground=colors['fg'],
                    indicatorbackground=colors['widget_bg'],
                    indicatormargin=5,
                    font=get_scaled_font(DEFAULT_FONT_SIZE, font_scale))
    style.map("TCheckbutton",
            indicatorbackground=[
                ('selected', colors['select_bg']),
                ('active', colors['widget_bg'])  # Color del checkbox al pasar el cursor
            ],
            foreground=[
                ('disabled', colors['disabled_fg']),
                ('active', colors['hover_text'])  # Color del texto al pasar el cursor
            ],
            background=[
                ('active', colors['hover_bg'])  # Fondo no cambia
            ])

    style.configure("TRadiobutton",
                    background=colors['bg'],
                    foreground=colors['fg'],
                    indicatorbackground=colors['widget_bg'],
                    indicatormargin=5,
                    font=get_scaled_font(DEFAULT_FONT_SIZE, font_scale))
    style.map("TRadiobutton",
              indicatorbackground=[('selected', colors['select_bg']), ('active', colors['widget_bg'])],
              foreground=[('disabled', colors['disabled_fg'])])

    style.configure('Hover.TCombobox',
                    fieldbackground=colors['hover_bg'],  # Fondo del campo de texto
                    foreground=colors['hover_text'],       # Color del texto
                    selectbackground=colors['select_bg'], # Fondo del texto seleccionado EN EL DROPDOWN
                    selectforeground=colors['select_fg'], # Color del texto seleccionado EN EL DROPDOWN
                    arrowcolor=colors['fg'],              # Color de la flecha del dropdown
                    font=get_scaled_font(DEFAULT_FONT_SIZE, font_scale), # Fuente del texto
                    padding=(scaled_padding_x, scaled_padding_y)) # Padding interno

# Logger for this module (add if not present)
import logging
logger = logging.getLogger(__name__)
