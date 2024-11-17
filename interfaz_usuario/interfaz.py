import tkinter as tk
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
