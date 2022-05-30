import argparse
import json
import os
import time, datetime
from threading import Thread, Event, Timer
import settings
from flow import FS1012
from motor import MotorDriver
import RPi.GPIO as GPIO

initialTime = datetime.datetime.now()
def print_info(infoString):
   print("[{:>11.4f}]".format((datetime.datetime.now() - initialTime).total_seconds()), infoString)
print_info("[Main  ] Starting the program at {}.".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

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

class MotorHandler:
    def __init__(self) -> None:
        pass
        # Tasks
        self.pumpTasks = []

        # Pumps setup
        GPIO.setmode(GPIO.BCM)
        if settings.GPIO_MODE == "BOARD":
            GPIO.setmode(GPIO.BOARD)
        # GPIO.setwarnings(False)
        inpA1   = settings.INPA1
        inpA2   = settings.INPA2
        inpB1   = settings.INPB1
        inpB2   = settings.INPB2
        self.pumps  = MotorDriver(inpA1, inpA2, inpB1, inpB2)
        self.pumps.runMotorA(False)
        self.pumps.runMotorB(False)
        self.pumpStatus = self.check_pump_status()

    def check_pump_status(self):
        return {"A": self.pumps.runMotorAStatus(), "B":self.pumps.runMotorBStatus()}

    def set_task(self, execTimeObj, func, *args):
        funcArgs = ",".join(map(str, args))
        funcName = func.__name__
        def wrap_func():
            tmp = func(*args)
            print_info(str(tmp))

        secToExec = (execTimeObj - datetime.datetime.now()).total_seconds()
        if secToExec > 0:
            print_info("[Motor ] {}({}) will execute at {}."
                .format(funcName, funcArgs, execTimeObj.strftime("%Y-%m-%d %H:%M:%S")))
            taskTimer = Timer(secToExec, wrap_func)
            taskTimer.daemon = True
            taskTimer.start()
            return taskTimer
        else:
            return None 

    def set_pump_task(self, taskDict):
        targetPump = [taskDict["pumpA"], taskDict["pumpB"]]
        if not True in targetPump:
            print_info("[Motor ] Please set at least one pump to true. Skipping this task.")
        else:
            startTime = taskDict["startTime"]
            duration = taskDict["duration"]
            durationUnit = taskDict["durationUnit"]
            deltaTime = datetime.timedelta(seconds=1)
            if durationUnit == "sec":
                deltaTime = datetime.timedelta(seconds=int(duration))
            elif durationUnit == "min":
                deltaTime = datetime.timedelta(minutes=int(duration))
            elif durationUnit == "hr":
                deltaTime = datetime.timedelta(hours=int(duration))
            else:
                print_info("[Motor ] Invalid time unit. Skipping this task.")
                return

            try:
                startTimeObj = datetime.datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S")
                if (startTimeObj - datetime.datetime.now()).total_seconds() < 0:
                    print_info("[Motor ] Invalid start time. Skipping this task.")
                    return
                stopTimeObj = startTimeObj + deltaTime
                print_info("[Motor ] A task will be execute at {} for {} {}"
                            .format(startTime, duration, durationUnit))
                
                taskA = []
                taskB = []
                if targetPump[0]:
                    taskA = [self.set_task(startTimeObj, self.pumps.runMotorA, True),
                        self.set_task(stopTimeObj, self.pumps.runMotorA, False)]
                if targetPump[1]:
                    taskB = [self.set_task(startTimeObj, self.pumps.runMotorA, True),
                        self.set_task(stopTimeObj, self.pumps.runMotorA, False)]
                # taskDict = {"taskA": taskA, "taskB": taskB }
                self.pumpTasks.append({"taskA": taskA, "taskB": taskB })

            except Exception as e:
                print_info("[Motor ] Error: {}. Skipping this task.".format(e))
                return

    def delete_tasks(self):
        for task in self.pumpTasks:
            for taskKey in task:
                for item in task[taskKey]:
                    item.cancel()
        print_info("[Motor ] All tasks are deleted.")
            # self.pumpTasks.pop(task)

    def check_remain_tasks(self):
        remainTasks = 0
        for task in self.pumpTasks:
            for taskKey in task:
                for item in task[taskKey]:
                    if item != None and item.is_alive(): 
                        remainTasks += 1
        return remainTasks

    def shutdown_pumps(self):
        self.pumps.runMotorA(False)
        self.pumps.runMotorB(False)
        print_info("[Motor ] All pumps are stopped.")
        # GPIO.cleanup()


class FlowHandler:
    def __init__(self) -> None:
        # Thread (Logging)
        self.isLogging = False
        self.loggingThread = None
        self.csv = None
        self.outputEvery = settings.OUTPUT_SEC

        # Thread (Sensor)
        calParams = settings.CAL_PARAMS
        self.flowSensor = FS1012(calParams)
        self.flowSensorTP1 = 0
        self.flowSensorTP2 = 0
        self.flowRate = 0
        self.sensorThread = LoopThread(0.5, self.read_sensor)
        self.sensorThread.setDaemon(True)
        self.sensorThread.start()
        print_info("[Sensor] The sensor reading starts.")

    def check_sensor(self):
        return self.flowSensor.check_status

    def read_sensor(self):
        if self.check_sensor():
            self.flowSensorTP1 = self.flowSensor.tp1_value
            self.flowSensorTP2 = self.flowSensor.tp2_value
            self.flowRate = self.flowSensor.flow_rate       # Need to execute after updating tp1, tp2.
        else:
            self.flowSensorTP1 = 0
            self.flowSensorTP2 = 0
            self.flowRate = 0
    
    def stop_read_sensor(self):
        if self.sensorThread is not None and self.sensorThread.is_alive():
            self.sensorThread.stop()
            print_info("[Sensor] The sensor reading stops.")
        return self.sensorThread.isStopped()

    def start_logging(self, logDir):
        self.logDir = logDir
        try:
            timeStamp = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
            self.csv = open(self.logDir + "/flow_log_" + timeStamp + ".csv", "w")
            self.write_csv_header()
            self.loggingThread = LoopThread(self.outputEvery, self.record_csv)
            self.loggingThread.setDaemon(True)
            self.loggingThread.start()
            print_info("[Sensor] The logging starts.")
            return True
        except FileNotFoundError:
            print_info("[Sensor] No such file or directory. Please retry.")
            return False
    
    def stop_logging(self):
        if self.loggingThread is not None and self.loggingThread.is_alive():
            self.loggingThread.stop()
            if self.csv is not None:
                self.csv.close()
            print_info("[Sensor] The logging stops.")
            return self.loggingThread.isStopped()
        else:
            return True

    def write_csv_header(self):
        self.csv.write("Time,TP1(mV),TP2(mV),Flow_Rate")
        self.csv.seek(self.csv.tell() - 1, os.SEEK_SET)
        self.csv.write("\n")

    def record_csv(self):
        if time.localtime().tm_min%60 == 0 and time.localtime().tm_sec == 0:
            timeStamp = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
            self.csv = open(self.logDir + "/flow_log_" + timeStamp + ".csv", "w")
            self.write_csv_header()
        
        self.csv.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+",")
        self.csv.write("{:.2f},{:.2f},{:.2f}".format(self.flowSensorTP1*1000,self.flowSensorTP2*1000,self.flowRate))
        self.csv.write("\n")

    def force_stop_threads(self):
        self.stop_logging()
        time.sleep(0.5)
        self.stop_read_sensor()
        time.sleep(0.5)


class Main():
    def __init__(self) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("taskJson",
                            help="Choose the JSON file where stores the tasks.")
        args = parser.parse_args()
        self.taskJson = args.taskJson
        print_info("[Main  ] Using the task file: {}".format(self.taskJson))

        with open(self.taskJson, 'r') as file:
            jsonData = json.load(file)

        print_info("[Main  ] Finished reading json file.")

        self.haveSensor = jsonData["haveSensor"]
        self.setLogging = jsonData["flowRateLogging"]
        self.setLoggingLocation = jsonData["flowRateLoggingLocation"]
        self.pumpTasks = jsonData["pumpTasks"]

    def run(self):
        self.pumpHandler = MotorHandler()
        self.pumpHandler.shutdown_pumps()
        
        if self.haveSensor and self.setLogging:
            self.sensorHandler = FlowHandler()
            self.sensorHandler.start_logging(self.setLoggingLocation)

        for task in self.pumpTasks:
            self.pumpHandler.set_pump_task(task)

    def stop(self):
        if self.haveSensor and self.setLogging:
            self.sensorHandler.force_stop_threads()
        self.pumpHandler.delete_tasks()
        self.pumpHandler.shutdown_pumps()

if __name__ == "__main__":
    try:
        main = Main()
        main.run()
    
        while True:
            if main.pumpHandler.check_remain_tasks() < 1:
                print_info("[Main  ] No task to run.")
                break
            time.sleep(5)

    except Exception as e:
        print_info(e)
    
    finally:
        print_info("[Main  ] Exiting the program.")
        main.stop()
        GPIO.cleanup()