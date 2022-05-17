from threading import Thread, Event
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as msg
from tkinter.constants import CENTER, W, E
import random
import settings
import time, datetime
import os
import board
import busio
from adafruit_ads1x15 import ads1115 as adafruit_ads1115
from adafruit_ads1x15.analog_in import AnalogIn

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

        # Thread (Logging)
        self.isLogging = False
        self.loggingThread = None
        self.csv = None

        # Thread (Sensor)
        self.flowSensor = FS1012({})
        self.flowSensorTP1 = 0
        self.flowSensorTP2 = 0
        self.sensorThread = LoopThread(1, self.read_sensor)

        # GUI
        self.panelTitle_lb = tk.Label(text="Flow Sensor", font="Helvetica 18 bold", 
            fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.panelTitle_lb.place(x=320+xOffset, y=20+yOffset, anchor=CENTER)

        self.sensorIndicator_lb = tk.Label(text="Sensor Status", fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.sensorIndicator_cv = tk.Canvas(width=20, height=20, bg=settings.BG_COLOR, borderwidth=0, highlightthickness=0)
        self.sensorFlowRate_lb = tk.Label(text="Flow (mlpm)", fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.sensorFlowRateValue_lb = tk.Label(text="0", fg=settings.FG_COLOR, bg=settings.BG_COLOR, width=10)

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

        # Initialization
        self.update_indicator(False)
        self.sensorThread.setDaemon(True)
        self.sensorThread.start()
        print("[Sensor frame] The sensor reading starts.")

    def check_sensor(self):
        # return True #if (random.random() > 0.2) else False
        return self.flowSensor.check_status

    def draw_indicator(self, canvasName, color):
        return canvasName.create_oval(1, 1, 19, 19, fill=color, outline="")

    def update_indicator(self, status):
        if status:
            self.draw_indicator(self.sensorIndicator_cv, settings.GREEN)
        else:
            self.draw_indicator(self.sensorIndicator_cv, settings.RED)

    def read_sensor(self):
        if self.check_sensor():
            self.update_indicator(True)
            self.flowSensorTP1 = self.flowSensor.tp1_value()
            self.flowSensorTP2 = self.flowSensor.tp2_value()
            # self.flowSensorTP1 = random.randint(1,2000)     # Fake value
            # self.flowSensorTP2 = random.randint(1,2000)     # Fake value
            self.sensorFlowRateValue_lb.config(text=str(self.flowSensorTP1))
        else:
            self.update_indicator(False)
            self.sensorFlowRateValue_lb.config(text="0")
    
    def stop_read_sensor(self):
        if self.sensorThread is not None and self.sensorThread.is_alive():
            self.sensorThread.stop()
            print("[Sensor frame] The sensor reading stops.")
        return self.sensorThread.isStopped()

    def select_log_dir(self):
        if self.logFile_en.get() is None:
            dirPath = filedialog.askdirectory()
            self.logFile_en.insert(0, dirPath)
        else:
            dirPath = filedialog.askdirectory()
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
        self.logDir = self.logFile_en.get()
        if self.logDir is None or len(self.logFile_en.get()) == 0:
            msg.showerror("Error", "Please select a directory to save the log file.")
            return False
        else:
            try:
                timeStamp = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
                self.csv = open(self.logDir + "/flow_log_" + timeStamp + ".csv", "w")
                self.write_csv_header()
                self.loggingThread = LoopThread(3, self.record_csv)
                self.loggingThread.setDaemon(True)
                self.loggingThread.start()
                print("[Sensor frame] The logging starts.")
                return True
            except FileNotFoundError:
                msg.showerror("Error", "No such file or directory. Please retry.")
                return False
    
    def stop_logging(self):
        if self.loggingThread is not None and self.loggingThread.is_alive():
            self.loggingThread.stop()
            if self.csv is not None:
                self.csv.close()
            print("[Sensor frame] The logging stops.")
            return self.loggingThread.isStopped()
        else:
            return True

    def write_csv_header(self):
        self.csv.write("Time,TP1,TP2,Flow_Rate")
        self.csv.seek(self.csv.tell() - 1, os.SEEK_SET)
        self.csv.write("\n")

    def record_csv(self):
        if time.localtime().tm_min%60 == 0 and time.localtime().tm_sec == 0:
            timeStamp = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
            self.csv = open(self.logDir + "/flow_log_" + timeStamp + ".csv", "w")
            self.write_csv_header()
        
        self.csv.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+",")
        self.csv.write(str(self.flowSensorTP1)+","+str(self.flowSensorTP2)+","+str(self.flowSensorTP1 - self.flowSensorTP2))
        self.csv.write("\n")

    def force_stop_threads(self):
        self.stop_logging()
        time.sleep(0.5)
        self.stop_read_sensor()
        time.sleep(0.5)

class LoopThread(Thread):
    def __init__(self, interval, func, *args):
        Thread.__init__(self)
        self.event = Event()
        self.interval = interval
        self.func = func
        self.args = args
        
    def run(self):
        while not self.event.wait(self.interval - time.time() % self.interval):
            self.func(*self.args)
            if self.isStopped():
                return
            time.sleep(0.01)
    
    def stop(self):
        self.event.set()
    
    def isStopped(self):
        return self.event.is_set()


def test_sensor():
    fs1012 = FS1012({})
    print(fs1012.check_status)

    while True:
        print("TP1: %.4f mV, TP2: %.4f mV" %(fs1012.tp1_value*1000, fs1012.tp2_value*1000))
        time.sleep(1)

if __name__ == "__main__":
    try:
        test_sensor()
    except Exception as e:
        print(e)