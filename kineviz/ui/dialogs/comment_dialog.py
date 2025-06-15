import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, Text
import logging

logger = logging.getLogger(__name__)

MAX_COMMENT_LENGTH = 150

class CommentDialog(Toplevel):
    def __init__(self, parent, study_id: int, study_name: str, current_comment: str | None, study_service, on_save_callback=None):
        super().__init__(parent)
        self.study_id = study_id
        self.study_name = study_name
        self.study_service = study_service
        self.on_save_callback = on_save_callback

        self.title(f"Comentario para Estudio: {self.study_name}")
        self.geometry("450x300") # Ajustar tamaño según necesidad
        self.resizable(False, False)

        self.comment_var = tk.StringVar(value=current_comment if current_comment is not None else "")
        self.char_count_var = tk.StringVar()

        self.create_widgets()
        self._update_char_count() # Actualizar contador inicial

        self.transient(parent)
        self.grab_set()
        # Centrar diálogo
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f'+{x}+{y}')


    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=f"Editar comentario para el estudio: '{self.study_name}'").pack(pady=(0, 5), anchor="w")

        # Text widget para el comentario
        self.comment_text = Text(main_frame, height=8, width=50, wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
        self.comment_text.insert(tk.END, self.comment_var.get())
        self.comment_text.pack(pady=5, fill=tk.BOTH, expand=True)
        self.comment_text.bind("<<Modified>>", self._on_text_modified) # Para actualizar contador en tiempo real

        # Contador de caracteres
        self.char_count_label = ttk.Label(main_frame, textvariable=self.char_count_var)
        self.char_count_label.pack(pady=(0,10), anchor="e")


        # Frame para botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=(5,0))
        self.save_button = ttk.Button(button_frame, text="Guardar", command=self.save_comment)
        self.save_button.pack(side=tk.RIGHT)


    def _on_text_modified(self, event=None):
        # Esta flag es necesaria porque <<Modified>> se dispara múltiples veces
        # y también antes de que el widget Text actualice su contenido interno.
        # Usamos after_idle para asegurar que el contenido del Text widget esté actualizado.
        if hasattr(self, '_after_id_text_modified'):
            self.after_cancel(self._after_id_text_modified)
        self._after_id_text_modified = self.after_idle(self._update_char_count_from_text_widget)
        
    def _update_char_count_from_text_widget(self):
        current_text = self.comment_text.get("1.0", tk.END).strip() # strip() para quitar newline final
        self.comment_var.set(current_text) # Actualizar la variable de control
        self._update_char_count()


    def _update_char_count(self):
        current_length = len(self.comment_var.get())
        self.char_count_var.set(f"{current_length}/{MAX_COMMENT_LENGTH} caracteres")
        if current_length > MAX_COMMENT_LENGTH:
            self.char_count_label.config(foreground="red")
            self.save_button.config(state=tk.DISABLED)
        else:
            self.char_count_label.config(foreground="") # Color por defecto
            self.save_button.config(state=tk.NORMAL)


    def save_comment(self):
        comment_to_save = self.comment_var.get() # Obtener de la variable que se actualiza en tiempo real

        if len(comment_to_save) > MAX_COMMENT_LENGTH:
            messagebox.showerror("Error", f"El comentario no puede exceder los {MAX_COMMENT_LENGTH} caracteres.", parent=self)
            return

        try:
            self.study_service.update_study_comment(self.study_id, comment_to_save if comment_to_save else None)
            logger.info(f"Comentario para estudio {self.study_id} guardado.")
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        except ValueError as ve:
            logger.error(f"Error de validación al guardar comentario para estudio {self.study_id}: {ve}", exc_info=True)
            messagebox.showerror("Error de Validación", str(ve), parent=self)
        except Exception as e:
            logger.error(f"Error inesperado al guardar comentario para estudio {self.study_id}: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo guardar el comentario:\n{e}", parent=self)

if __name__ == '__main__':
    # Ejemplo de uso (requiere un StudyService dummy)
    root = tk.Tk()
    root.withdraw() # Ocultar ventana raíz principal para el ejemplo

    class DummyStudyService:
        def get_study_comment(self, study_id):
            print(f"DummyStudyService: get_study_comment({study_id})")
            if study_id == 1:
                return "Este es un comentario de prueba existente."
            return None

        def update_study_comment(self, study_id, comment):
            print(f"DummyStudyService: update_study_comment({study_id}, '{comment}')")
            if comment is not None and len(comment) > MAX_COMMENT_LENGTH:
                raise ValueError(f"El comentario excede los {MAX_COMMENT_LENGTH} caracteres.")
            print("Comentario guardado (simulado).")
        
        def get_study_details(self, study_id): # Necesario para update_study_comment en el servicio real
            return {'id': study_id, 'name': f'Estudio {study_id}', 'comentario': self.get_study_comment(study_id)}


    dummy_service = DummyStudyService()
    
    def on_save_test():
        print("Callback de guardado ejecutado.")
        # En una aplicación real, aquí se refrescaría la vista principal.

    # Simular obtener comentario actual
    test_study_id = 1
    test_study_name = f"Estudio de Prueba {test_study_id}"
    # current_comment_for_dialog = dummy_service.get_study_comment(test_study_id) # No es necesario, el diálogo lo hace

    dialog = CommentDialog(root, test_study_id, test_study_name, "Comentario inicial de prueba", dummy_service, on_save_callback=on_save_test)
    root.mainloop()
