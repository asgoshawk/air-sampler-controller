import tkinter as tk
import tkinter.messagebox as msg
from tkinter.constants import CENTER, W, E
import settings
import time, datetime
# import pytz
# import board
# import busio
# from adafruit_ads1x15 import ads1115 as adafruit_ads1115
# from adafruit_ads1x15.analog_in import AnalogIn

class FS1012:
    '''
    FS1012 Pinout
    1   TP1+    Output  Analog
    2   TP1-    Output  GND
    3   HTR1    Input   3V/5V
    4   HTR2    Input   GND
    5   TP2-    Output  Analog
    6   TP2+    Output  GND
    '''
    def __init__(self, calObj):
        try:
            self.i2c            = busio.I2C(board.SCL, board.SDA)
            self.ads1115        = adafruit_ads1115.ADS1115(self.i2c)
            self.ads1115.gain   = 1
            self.channels       = [adafruit_ads1115.P0, adafruit_ads1115.P1, adafruit_ads1115.P2, adafruit_ads1115.P3]
            self.adschls        = [AnalogIn(self.ads1115, chl) for chl in self.channels] 
            self._status        = True
            self.error          = None
        except Exception as e:
            self._status        = False
            self.error          = e

        # TP1+, TP2+, calibration object for voltage-flow convertion
        self._tp1       = 0
        self._tp2       = 0
        self._calObj    = calObj
    
    @property
    def check_status(self):
        return self._status

    @property
    def tp1_value(self):
        self._tp1 = self.adschls[0].voltage if self._status else 0
        return self._tp1

    @property
    def tp2_value(self):
        self._tp2 = self.adschls[1].voltage if self._status else 0
        return self._tp2


class FlowFrame(tk.Frame):
    def __init__(self, master, width, height, xOffset, yOffset):
        super().__init__(master)
        self.width = width
        self.height = height
        self.xOffset = xOffset
        self.yOffset = yOffset
        # self.borderwidth = 0
        # self.hightlightthickness = 0
        self.configure(bg=settings.YELLOW)
        # self.flowSensor = FS1012()

        # Thread
        self.isLogging = False

        self.panelTitle_lb = tk.Label(text="Flow Sensor", font="Helvetica 18 bold", 
            fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.panelTitle_lb.place(x=320+xOffset, y=20+yOffset, anchor=CENTER)

        self.sensorIndicator_lb = tk.Label(text="Sensor Status", fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.sensorIndicator_cv = tk.Canvas(width=20, height=20, bg=settings.BG_COLOR, borderwidth=0, highlightthickness=0)
        self.sensorFlowRate_lb = tk.Label(text="Flow (mlpm)", fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.sensorFlowRateValue_lb = tk.Label(text="1000", fg=settings.FG_COLOR, bg=settings.BG_COLOR, width=10)

        self.sensorIndicator_lb.place(x=40+xOffset, y=60+yOffset, anchor=W)
        self.sensorIndicator_cv.place(x=160+xOffset, y=60+yOffset, anchor=CENTER)
        self.sensorFlowRate_lb.place(x=40+xOffset, y=100+yOffset, anchor=W)
        self.sensorFlowRateValue_lb.place(x=160+xOffset, y=100+yOffset, anchor=CENTER)     

        self.logFile_lb = tk.Label(text="Log File Location", fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.logFileSelect_btn = tk.Button(text="Select", 
             bg=settings.FG_COLOR, fg=settings.BG_COLOR, height=1, bd=0, pady=0,
             command=self.select_log_dir)
        self.logFileStartStop_btn = tk.Button(text="Start Logging", 
             bg=settings.FG_COLOR, fg=settings.BG_COLOR, height=1, bd=0, pady=0, width=16,
            command=self.toggle_logging_btn)
        self.logFile_en = tk.Entry(width=35)
        self.logFile_en.insert(0, 'Please select a directory.')

        self.logFile_lb.place(x=280+xOffset, y=60+yOffset, anchor=W)
        self.logFileSelect_btn.place(x=600+xOffset, y=100+yOffset, anchor=E)
        self.logFileStartStop_btn.place(x=600+xOffset, y=60+yOffset, anchor=E)
        self.logFile_en.place(x=280+xOffset, y=100+yOffset, anchor=W)

        self.update_indicator()

    def check_sensor(self):
        # return self.flowSensor.check_status
        return True

    def draw_indicator(self, canvasName, color):
        return canvasName.create_oval(1, 1, 19, 19, fill=color, outline="")

    def update_indicator(self):
        if self.check_sensor():
            self.draw_indicator(self.sensorIndicator_cv, settings.GREEN)
        else:
            self.draw_indicator(self.sensorIndicator_cv, settings.RED)

    def select_log_dir(self):
        if self.logFile_en.get() is None:
            dirPath = tk.filedialog.askdirectory()
            self.logFile_en.insert(0, dirPath)
        else:
            dirPath = tk.filedialog.askdirectory()
            self.logFile_en.delete(0,'end')
            self.logFile_en.insert(0, dirPath)

    def toggle_logging_btn(self):
        if not self.isLogging:
            if self.start_logging():
                self.logFileStartStop_btn.config(text="Stop Logging")
                self.isLogging = True
        else:
            self.stop_logging()
            self.logFileStartStop_btn.config(text="Start Logging")
            self.isLogging = False

    def start_logging(self):
        logDir = self.logFile_en.get()
        if logDir is None or len(self.logFile_en.get()) == 0:
            msg.showerror("Error", "Please select a directory to save the log file.")
            return False
        else:
            try:
                timeStamp = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
                with open(logDir + "/flow_log_" + timeStamp + ".csv", "w") as csv:
                    csv.write("Hello,")
                return True
            except FileNotFoundError:
                msg.showerror("Error", "No such file or directory. Please retry.")
                return False
    
    def stop_logging(self):
        pass