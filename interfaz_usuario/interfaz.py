import tkinter as tk
from main import create_deck

def abrir_interfaz():
    deck = create_deck() 

    ventana = tk.Tk()
    ventana.title('Solitaire')

    # (For now, just display the first card as an example)
    card_label = tk.Label(ventana, text=str(deck[0])) 
    card_label.pack()

    ventana.mainloop()

if __name__ == "__main__":
    abrir_interfaz()
