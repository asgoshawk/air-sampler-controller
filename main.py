import tkinter as tk
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

        # Menu
        self.menuBar = tk.Menu(self)
        self.fileMenu = tk.Menu(self.menuBar, tearoff=0)
        self.fileMenu.add_command(label='Exit')
        self.helpMenu = tk.Menu(self.menuBar, tearoff=0)
        self.helpMenu.add_command(label='About')
        self.menuBar.add_cascade(label='File', menu=self.fileMenu)
        self.menuBar.add_cascade(label='Help', menu=self.helpMenu)
        self.config(menu=self.menuBar)

        # Frame
        self.sensorFrame = FlowFrame(self, width=settings.WIDTH, height=settings.HEIGHT*0.4, xOffset=0, yOffset=0)
        self.motorFrame = MotorFrame(self, width=settings.WIDTH, height=settings.HEIGHT*0.4, xOffset=0, yOffset=140)

if __name__ == "__main__":
    print("Start the APP.")
    window = Window()
    window.mainloop()
    window.motorFrame.shutdown_pumps()
    