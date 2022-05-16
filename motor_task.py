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
        GPIO.output(self.inpA1, GPIO.HIGH) if value else GPIO.output(self.inpA1, GPIO.LOW)

    # @property
    def runMotorBStatus(self):
        return self._runMotorB

    # @runMotorB.setter
    def runMotorB(self, value: bool):
        self._runMotorB = value
        GPIO.output(self.inpB1, GPIO.HIGH) if value else GPIO.output(self.inpB1, GPIO.LOW)


def set_task(startTimeObj, func, *args):
    funcArgs        = ",".join(map(str, args))
    funcName        = func.__name__
    
    def wrap_func():
        func(*args)
        execTime    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("%s(%s) finished at %s" %(funcName, funcArgs, execTime))

    secToExec   = (startTimeObj - datetime.datetime.now()).total_seconds()
    if secToExec > 0:
        print("%s(%s) will start at %s." 
            %(funcName, funcArgs, startTimeObj.strftime("%Y-%m-%d %H:%M:%S")))
        taskTimer   = Timer(secToExec, wrap_func)
        taskTimer.start()
        return taskTimer
    else:
        return None 


def demo():
    try:
        GPIO.setmode(GPIO.BCM)
        # GPIO.setwarnings(False)

        inpA1   = 14
        inpA2   = 15
        inpB1   = 17
        inpB2   = 18
        driver  = MotorDriver(inpA1, inpA2, inpB1, inpB2)

        print("\nThe following tasks are set:")
        tasks   = [
            set_task(datetime.datetime(2022, 3, 24, 14, 34, 10), driver.runMotorA, True),
            set_task(datetime.datetime(2022, 3, 24, 14, 34, 30), driver.runMotorA, False),
            set_task(datetime.datetime(2022, 3, 24, 14, 34, 50), driver.runMotorB, True)
        ]
        print("="*50)

        tmpCount = 0
        while True:
            remainTasks = 0
            for task in tasks:
                if task != None and task.is_alive(): 
                    remainTasks += 1
            if remainTasks == 0: 
                break
            
            if tmpCount != remainTasks:
                print("There are %d remaining tasks waiting to run." %(remainTasks))
                tmpCount = remainTasks
            time.sleep(1)

        print("\nAll the tasks is finished. Exiting the program.")

    except Exception as e:
        print("The program is exiting due to", e)
        for task in tasks:
            if task != None: 
                task.cancel()
    
    finally:
        driver.runMotorA(False)
        driver.runMotorB(False)
        GPIO.cleanup()

if __name__ == '__main__':
    demo()