import tkinter as tk
from ui.main_window import MainWindow

def main():
    root = tk.Tk()
    root.title('KineViz')
    root.geometry('1000x600')
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
