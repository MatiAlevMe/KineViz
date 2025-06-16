import tkinter as tk
from tkinter import ttk

class Tooltip:
    """
    Creates a tooltip for a given widget.
    The tooltip uses a ttk.Label styled with 'Tooltip.TLabel',
    which should be pre-configured with font scaling and colors.
    """
    def __init__(self, widget, text: str, wraplength: int = 350): # Increased default wraplength
        self.widget = widget
        self.text = text
        self.wraplength = wraplength
        self.tooltip_window = None
        self._id_show = None # For delayed show
        self._id_hide = None # For delayed hide

        self.widget.bind("<Enter>", self._schedule_show_tooltip)
        self.widget.bind("<Leave>", self._schedule_hide_tooltip)
        # Removing the ButtonPress binding on the widget to allow its own command to fire.
        # self.widget.bind("<ButtonPress>", self._hide_tooltip_now) 

    def _schedule_show_tooltip(self, event=None):
        self._cancel_tooltip_hiding() # Cancel any pending hide operations
        if not self.tooltip_window:
            # Schedule to show after a short delay (e.g., 500ms)
            self._id_show = self.widget.after(500, self._show_tooltip_now)

    def _schedule_hide_tooltip(self, event=None):
        self._cancel_tooltip_showing() # Cancel any pending show operations
        # Schedule to hide after a short delay, allows moving mouse into tooltip
        self._id_hide = self.widget.after(100, self._hide_tooltip_now)


    def _show_tooltip_now(self):
        if self.tooltip_window or not self.text:
            return

        # Get widget position relative to the screen
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty()
        
        # Position tooltip below the widget, centered or to the right
        x_offset = self.widget.winfo_width() // 2
        y_offset = self.widget.winfo_height() 

        final_x = x + x_offset
        final_y = y + y_offset + 5 # 5 pixels below the widget

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # No window decorations
        
        label = ttk.Label(tw, text=self.text, justify=tk.LEFT, wraplength=self.wraplength)
        label.configure(style="Tooltip.TLabel") # Style provides font, bg, fg, relief, borderwidth
        label.pack(ipadx=5, ipady=3) # Add some internal padding

        # Position tooltip after it's created and sized
        tw.update_idletasks() 
        tip_width = tw.winfo_width()
        tip_height = tw.winfo_height()

        # Adjust x to keep tooltip on screen
        screen_width = self.widget.winfo_screenwidth()
        if final_x + tip_width > screen_width:
            final_x = screen_width - tip_width - 5 # Move left
        if final_x < 0 : # If still off-screen left (e.g. widget is very left)
            final_x = 5
        
        # Adjust y to keep tooltip on screen (prefer below, then above)
        screen_height = self.widget.winfo_screenheight()
        if final_y + tip_height > screen_height:
            final_y = y - tip_height - 5 # Try above the widget
        if final_y < 0: # If still off-screen (e.g. widget at top and tooltip too tall)
            final_y = 5 # Position at top of screen

        tw.wm_geometry(f"+{int(final_x)}+{int(final_y)}")

        # Bindings for the tooltip window itself to allow mouse to enter it
        tw.bind("<Enter>", self._cancel_tooltip_hiding)
        tw.bind("<Leave>", self._schedule_hide_tooltip)
        tw.bind("<ButtonPress>", self._hide_tooltip_now)


    def _hide_tooltip_now(self, event=None):
        self._cancel_tooltip_showing()
        self._cancel_tooltip_hiding()
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

    def _cancel_tooltip_showing(self):
        if self._id_show:
            self.widget.after_cancel(self._id_show)
            self._id_show = None
            
    def _cancel_tooltip_hiding(self):
        if self._id_hide:
            self.widget.after_cancel(self._id_hide)
            self._id_hide = None
