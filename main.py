import tkinter as tk
from tkinter import font
import tkinter.messagebox as msg
import time
from flow import FlowFrame
from motor import MotorFrame
import settings


class Window(tk.Tk):
    def __init__(self):
        super().__init__()

        # Window settings
        self.configure(bg=settings.BG_COLOR)
        self.title('Air Sampler Controller')
        self.geometry('{}x{}'.format(settings.WIDTH, settings.HEIGHT))
        self.resizable(False, False)
        
        # Creating a Font object of "TkDefaultFont"
        self.defaultFont = font.nametofont("TkDefaultFont")
  
        # Overriding default-font with custom settings
        # i.e changing font-family, size and weight
        self.defaultFont.configure(family="Arial",  #"Helvetica",
                                   size=9)
  

        # Menu
        self.menuBar = tk.Menu(self)
        self.fileMenu = tk.Menu(self.menuBar, tearoff=0)
        self.fileMenu.add_command(label='Exit', command=self.close_window)
        self.helpMenu = tk.Menu(self.menuBar, tearoff=0)
        self.helpMenu.add_command(label='About', command=self.show_about)
        self.menuBar.add_cascade(label='File', menu=self.fileMenu)
        self.menuBar.add_cascade(label='Help', menu=self.helpMenu)
        self.config(menu=self.menuBar)
        self.protocol('WM_DELETE_WINDOW', self.close_window)

        self.sensorFrame = FlowFrame(self, width=settings.WIDTH, height=settings.HEIGHT*0.4, xOffset=0, yOffset=0)
        self.motorFrame = MotorFrame(self, width=settings.WIDTH, height=settings.HEIGHT*0.4, xOffset=0, yOffset=140)

    def show_about(self):
        msg.showinfo("About", "The GUI for air sampler controller",
        detail="For more instruction, please visit\n\ngithub.com/asgoshawk/air-sampler-controller\n\nVersion: 1.0.0, Author: Ching-Wei Chu")

    def close_window(self):
        self.motorFrame.shutdown_pumps()
        self.sensorFrame.force_stop_threads()
        time.sleep(1)
        self.destroy()

if __name__ == "__main__":
    try:
        print("[Main APP] Start the APP.")
        
        window = Window()
        window.mainloop()
    finally:
        print("[Main APP] Close the APP.")
    