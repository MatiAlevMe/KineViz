import tkinter as tk

class ToolTip:
    """
    Crea un tooltip (ventana emergente con texto) para un widget dado.
    """
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave) # Ocultar al hacer clic

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        # Esperar 500ms antes de mostrar
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def showtip(self, event=None):
        # Obtener posición del cursor relativa a la pantalla
        x = self.widget.winfo_pointerx() + 10
        y = self.widget.winfo_pointery() + 20

        # Crear ventana Toplevel si no existe
        if self.tooltip_window:
            return
        self.tooltip_window = tk.Toplevel(self.widget)
        # Hacerla sin bordes y siempre encima
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"), wraplength=200)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()

    # Permitir actualizar el texto del tooltip dinámicamente
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        # Si el tooltip está visible, actualizarlo (opcional)
        # if self.tooltip_window:
        #     # Necesitaría acceder al Label interno para cambiar el texto
        #     pass

# Ejemplo de uso (si se ejecuta este archivo directamente)
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Tooltip Test")
    btn1 = tk.Button(root, text="Hover over me")
    btn1.pack(pady=10, padx=10)
    ToolTip(btn1, "This is a tooltip message.\nIt can span multiple lines.")

    lbl = tk.Label(root, text="Another widget")
    lbl.pack(pady=10, padx=10)
    tooltip_lbl = ToolTip(lbl, "Info for the label.")

    # Ejemplo de actualización dinámica
    def update_tooltip():
        tooltip_lbl.text = f"Updated text: {datetime.now()}"
    from datetime import datetime
    btn_update = tk.Button(root, text="Update Label Tooltip", command=update_tooltip)
    btn_update.pack(pady=5)

    root.mainloop()
