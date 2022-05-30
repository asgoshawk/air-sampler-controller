import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msg
from tkinter.constants import CENTER, W, E, NW
import settings
import RPi.GPIO as GPIO
import time, datetime
from threading import Timer

class MotorDriver:
    '''
        This class is suitable for both DRV8833 and L9110(s),
        and the connections for both driver are shown below:

        ################### DRV8833 ###################
        VM        ==  power for motors (5V)
        GND       ==  ground
        STBY      ==  powering with 5V to enable driver
        ANI1      ==  inpA1
        ANI2      ==  inpA2
        BIN1      ==  inpB1
        BIN2      ==  inpB2
        AO1/BO1   ==  motor +
        AO2/BO2   ==  motor - 

        ################### L9110(S) ##################
        VCC       ==  power for motors (5V)
        GND       ==  ground
        A-IA      ==  inpA1
        A-IB      ==  inpA2
        B-IA      ==  inpB1
        B-IB      ==  inpB2
        OA1/OB1   ==  motor +
        OA2/OB2   ==  motor - 
    '''

    def __init__(self, inpA1, inpA2, inpB1, inpB2):
        self._runMotorA  = False
        self._runMotorB  = False
        self.inpA1    = inpA1
        self.inpA2    = inpA2
        self.inpB1    = inpB1
        self.inpB2    = inpB2
        
        GPIO.setup(self.inpA1, GPIO.OUT)
        GPIO.setup(self.inpA2, GPIO.OUT)
        GPIO.setup(self.inpB1, GPIO.OUT)
        GPIO.setup(self.inpB2, GPIO.OUT)
        
        GPIO.output(self.inpA1, GPIO.LOW)
        GPIO.output(self.inpA2, GPIO.LOW)
        GPIO.output(self.inpB1, GPIO.LOW)
        GPIO.output(self.inpB2, GPIO.LOW)

    # @property
    def runMotorAStatus(self):
        return self._runMotorA

    # @runMotorA.setter
    def runMotorA(self, value: bool):
        self._runMotorA = value
        if value:
            GPIO.output(self.inpA1, GPIO.HIGH)
            return "[MotorA] Is running."
        else: 
            GPIO.output(self.inpA1, GPIO.LOW)
            return "[MotorA] Is stopped."

    # @property
    def runMotorBStatus(self):
        return self._runMotorB

    # @runMotorB.setter
    def runMotorB(self, value: bool):
        self._runMotorB = value
        if value:
            GPIO.output(self.inpB1, GPIO.HIGH)
            return "[MotorB] Is running."
        else:
            GPIO.output(self.inpB1, GPIO.LOW)
            return "[MotorB] Is stopped."


class MotorFrame(tk.Frame):
    def __init__(self, master, width, height, xOffset, yOffset):
        super().__init__(master)
        self.width = width
        self.height = height
        self.xOffset = xOffset
        self.yOffset = yOffset
        # self.borderwidth = 0
        # self.hightlightthickness = 0
        # self.configure(bg=settings.YELLOW)
        
        # Tasks
        self.pumpTasks = {}

        # Pumps setup
        if settings.GPIO_MODE == "BOARD":
            GPIO.setmode(GPIO.BOARD)
        else:
            GPIO.setmode(GPIO.BCM)
        # GPIO.setwarnings(False)
        inpA1   = settings.INPA1
        inpA2   = settings.INPA2
        inpB1   = settings.INPB1
        inpB2   = settings.INPB2
        self.pumps  = MotorDriver(inpA1, inpA2, inpB1, inpB2)
        self.pumps.runMotorA(False)
        self.pumps.runMotorB(False)
        self.pumpStatus = self.check_pump_status()

        # GUI
        self.panelTitle_lb = tk.Label(text="Pump", font="Helvetica 18 bold", 
            fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.panelTitle_lb.place(x=320+xOffset, y=20+yOffset, anchor=CENTER)

        # Pump indicators
        self.pumpAIndicator_lb = tk.Label(text="Pump A Status", fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.pumpBIndicator_lb = tk.Label(text="Pump B Status", fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.pumpAIndicator_cv = tk.Canvas(width=20, height=20, bg=settings.BG_COLOR, borderwidth=0, highlightthickness=0)
        self.pumpBIndicator_cv = tk.Canvas(width=20, height=20, bg=settings.BG_COLOR, borderwidth=0, highlightthickness=0)
        self.pumpAIndicator_lb.place(x=40+xOffset, y=60+yOffset, anchor=W)
        self.pumpBIndicator_lb.place(x=40+xOffset, y=100+yOffset, anchor=W)
        self.pumpAIndicator_cv.place(x=160+xOffset, y=60+yOffset, anchor=CENTER)
        self.pumpBIndicator_cv.place(x=160+xOffset, y=100+yOffset, anchor=CENTER)

        # Pump manually control
        self.pumpAToggler_btn = tk.Button(text="ON", 
             bg=settings.FG_COLOR, fg=settings.BG_COLOR, height=1, bd=0, pady=0, width=4,
            command=self.toggle_pump_btn_a)
        self.pumpBToggler_btn = tk.Button(text="ON", 
             bg=settings.FG_COLOR, fg=settings.BG_COLOR, height=1, bd=0, pady=0, width=4,
            command=self.toggle_pump_btn_b)
        self.pumpAToggler_btn.place(x=220+xOffset, y=60+yOffset, anchor=CENTER)
        self.pumpBToggler_btn.place(x=220+xOffset, y=100+yOffset, anchor=CENTER)

        # Pump task setup
        self.setTaskPumpA_val = tk.IntVar()
        self.setTaskPumpB_val = tk.IntVar()
        self.setTaskPumpA_btn = tk.Checkbutton(text="Pump A", variable=self.setTaskPumpA_val,
            onvalue=True, offvalue=False, highlightthickness=0,
            bg=settings.BG_COLOR, fg=settings.FG_COLOR, selectcolor=settings.CUR_LINE,
            activebackground=settings.BG_COLOR, activeforeground=settings.FG_COLOR,)
        self.setTaskPumpB_btn = tk.Checkbutton(text="Pump B", variable=self.setTaskPumpB_val,
            onvalue=True, offvalue=False, highlightthickness=0,
            bg=settings.BG_COLOR, fg=settings.FG_COLOR, selectcolor=settings.CUR_LINE,
            activebackground=settings.BG_COLOR, activeforeground=settings.FG_COLOR,)
        self.setTaskPumpA_btn.place(x=265+xOffset, y=60+yOffset, anchor=W)
        self.setTaskPumpB_btn.place(x=265+xOffset, y=100+yOffset, anchor=W)

        self.setStartTime_lb = tk.Label(text="From", fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.setStarTime_en = tk.Entry(width=17)
        self.setStarTime_en.insert(0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.setDuration_lb = tk.Label(text="Duration", fg=settings.FG_COLOR, bg=settings.BG_COLOR)
        self.setDuration_sb = tk.Spinbox(from_=1, to=999, width=4, bd=0)
        self.setDurationUnit_cb = ttk.Combobox(values=['sec','min','hr'], width=3, state="readonly")
        self.setDurationUnit_cb.current(0)
        self.setTask_btn = tk.Button(text="Set Task", 
             bg=settings.FG_COLOR, fg=settings.BG_COLOR, height=1, bd=0, padx=5, pady=20,
             command=self.set_pump_task)
        self.setStartTime_lb.place(x=345+xOffset, y=60+yOffset, anchor=W)
        self.setStarTime_en.place(x=525+xOffset, y=60+yOffset, anchor=E)
        self.setDuration_lb.place(x=345+xOffset, y=100+yOffset, anchor=W)
        self.setDuration_sb.place(x=465+xOffset, y=100+yOffset, anchor=E)
        self.setDurationUnit_cb.place(x=525+xOffset, y=100+yOffset, anchor=E)
        self.setTask_btn.place(x=600+xOffset, y=80+yOffset, anchor=E)

        # Tree view of tasks
        self.taskCounts = 0
        self.taskList_tv = ttk.Treeview(
            columns=("id","start","stop", "duration","pumpA", "pumpB"),
            height=5, show="headings",
            )
        self.taskList_tv.column("id", width=40)
        self.taskList_tv.column("start", width=150)
        self.taskList_tv.column("stop", width=150)
        self.taskList_tv.column("duration", width=80)
        self.taskList_tv.column("pumpA", width=70)
        self.taskList_tv.column("pumpB", width=70)
        self.taskList_tv.heading("id", text="ID")
        self.taskList_tv.heading("start", text="Start")
        self.taskList_tv.heading("stop", text="Stop")
        self.taskList_tv.heading("duration", text="Duration")
        self.taskList_tv.heading("pumpA", text="Pump A")
        self.taskList_tv.heading("pumpB", text="Pump B")
        self.taskListDelete_btn = tk.Button(text="Delete Task", 
             bg=settings.FG_COLOR, fg=settings.BG_COLOR, height=1, bd=0, width=8,
             command=self.delete_pump_task)
        self.taskListDeleteAll_btn = tk.Button(text="Delete All", 
             bg=settings.FG_COLOR, fg=settings.BG_COLOR, height=1, bd=0, width=8,
             command=self.delete_all_tasks)

        self.taskList_tv.place(x=40+xOffset, y=140+yOffset, anchor=NW)
        self.taskListDelete_btn.place(x=40+xOffset, y=300+yOffset, anchor=W)
        self.taskListDeleteAll_btn.place(x=150+xOffset, y=300+yOffset, anchor=W)

        self.update_indicator(self.pumpAIndicator_cv, self.pumpBIndicator_cv)

    def draw_indicator(self, canvasName, color):
        return canvasName.create_oval(2, 2, 18, 18, fill=color, outline="")

    def check_pump_status(self):
        return {"A": self.pumps.runMotorAStatus(), "B":self.pumps.runMotorBStatus()}

    def update_indicator(self, canvasNameA, canvasNameB):
        self.pumpStatus = self.check_pump_status()
        # pumpStatus = {"A": True, "B":False}
        if self.pumpStatus["A"]:
            self.draw_indicator(canvasNameA, settings.GREEN)
            self.pumpAToggler_btn.config(text="OFF")
        else:
            self.draw_indicator(canvasNameA, settings.RED)
            self.pumpAToggler_btn.config(text="ON")

        if self.pumpStatus["B"]:
            self.draw_indicator(canvasNameB, settings.GREEN)
            self.pumpBToggler_btn.config(text="OFF")
        else:
            self.draw_indicator(canvasNameB, settings.RED)
            self.pumpBToggler_btn.config(text="ON")
    
    def toggle_pump_btn_a(self):
        if self.pumpStatus["A"]:
            self.pumps.runMotorA(False)
            # self.pumpStatus["A"] = False
        else:
            self.pumps.runMotorA(True)
            # self.pumpStatus["A"] = True
        self.update_indicator(self.pumpAIndicator_cv, self.pumpBIndicator_cv)

    def toggle_pump_btn_b(self):
        if self.pumpStatus["B"]:
            self.pumps.runMotorB(False)
            # self.pumpStatus["B"] = False
        else:
            self.pumps.runMotorB(True)
            # self.pumpStatus["B"] = True
        self.update_indicator(self.pumpAIndicator_cv, self.pumpBIndicator_cv)

    def test_task_a(self, var):
        self.pumpStatus["A"] = var
        self.update_indicator(self.pumpAIndicator_cv, self.pumpBIndicator_cv)
        print(var, "at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def test_task_b(self, var):
        self.pumpStatus["B"] = var
        self.update_indicator(self.pumpAIndicator_cv, self.pumpBIndicator_cv)
        print(var, "at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def set_task(self, execTimeObj, func, *args):
        funcArgs = ",".join(map(str, args))
        funcName = func.__name__
        def wrap_func():
            func(*args)

        secToExec = (execTimeObj - datetime.datetime.now()).total_seconds()
        if secToExec > 0:
            print("%s(%s) will execute at %s." 
                %(funcName, funcArgs, execTimeObj.strftime("%Y-%m-%d %H:%M:%S")))
            taskTimer = Timer(secToExec, wrap_func)
            taskTimer.daemon = True
            taskTimer.start()
            return taskTimer
        else:
            return None 

    def set_pump_task(self):
        targetPump = [self.setTaskPumpA_val.get(), self.setTaskPumpB_val.get()]
        if not True in targetPump:
            msg.showwarning("Warning", "Please select at least one pump.")
        else:
            startTime = self.setStarTime_en.get()
            duration = self.setDuration_sb.get()
            durationUnit = self.setDurationUnit_cb.get()
            deltaTime = datetime.timedelta(seconds=1)
            if durationUnit == "sec":
                deltaTime = datetime.timedelta(seconds=int(duration))
            elif durationUnit == "min":
                deltaTime = datetime.timedelta(minutes=int(duration))
            elif durationUnit == "hr":
                deltaTime = datetime.timedelta(hours=int(duration))
            else:
                msg.showerror("Error", "Invalid time unit. Please retry.")
                return

            try:
                startTimeObj = datetime.datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
                if (startTimeObj - datetime.datetime.now()).total_seconds() < 0:
                    msg.showerror("Error", "Invalid start time. Please retry.")
                    return

                stopTimeObj = startTimeObj + deltaTime
                checkMsg = "This task will start at {} for {} {}, continue?".format(startTime, duration, durationUnit)
                if msg.askokcancel("Set Task", checkMsg):
                    self.taskList_tv.insert(parent="", iid=self.taskCounts, index="end",
                    values=(self.taskCounts, startTime, stopTimeObj.strftime("%Y-%m-%d %H:%M:%S"),
                     str(duration)+" "+str(durationUnit), targetPump[0], targetPump[1]))
                    print("A task will be execute at %s for %s %s" %(startTime, duration, durationUnit))
                    taskDict = {}
                    taskA = []
                    taskB = []
                    if targetPump[0]:
                        taskA = [self.set_task(startTimeObj, self.pumps.runMotorA, True),
                            self.set_task(stopTimeObj, self.pumps.runMotorA, False)]
                        # taskA = [self.set_task(startTimeObj, self.test_task_a, True),
                                # self.set_task(stopTimeObj, self.test_task_a, False)]
                    if targetPump[1]:
                        taskB = [self.set_task(startTimeObj, self.pumps.runMotorA, True),
                            self.set_task(stopTimeObj, self.pumps.runMotorA, False)]
                        # taskB = [self.set_task(startTimeObj, self.test_task_b, True),
                                # self.set_task(stopTimeObj, self.test_task_b, False)]
                    taskDict[str(self.taskCounts)] = {"taskA": taskA, "taskB": taskB }
                    self.pumpTasks.update(taskDict)
                    self.taskCounts+=1

            except Exception as e:
                msg.showerror("Error", e)
                return

    def delete_task(self, tasks):
        for task in tasks:
            self.taskList_tv.delete(task)
            if len(self.pumpTasks) !=0:
                for pumpTaskKey in self.pumpTasks[task]:
                    for item in self.pumpTasks[task][pumpTaskKey]:
                        item.cancel()
                self.pumpTasks.pop(task)

    def delete_pump_task(self):
        tasks = self.taskList_tv.selection()
        if len(tasks) < 1:
            msg.showwarning("Delete Task", "No tasks to delete. Please select at least one task above.")
        else:
            deleteMsg = "The task {} will be delete, continue?".format(",".join(tasks))
            if msg.askokcancel("Delete Task",deleteMsg):
                self.delete_task(tasks)
        
    def delete_all_tasks(self):
        tasks = self.taskList_tv.get_children()
        if len(tasks) < 1:
            msg.showwarning("Delete Task", "No tasks to delete.")
        else:    
            if msg.askokcancel("Delete Task","All tasks will be delete, continue?"):
                self.delete_task(tasks)

    def shutdown_pumps(self):
        self.pumps.runMotorA(False)
        self.pumps.runMotorB(False)
        GPIO.cleanup()
