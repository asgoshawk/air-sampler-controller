import RPi.GPIO as GPIO
from motor import MotorDriver

def shutdown():
    try:
        GPIO.setmode(GPIO.BCM)
        # GPIO.setwarnings(False)
        inpA1   = 14
        inpA2   = 15
        inpB1   = 17
        inpB2   = 18
        driver  = MotorDriver(inpA1, inpA2, inpB1, inpB2)

        driver.runMotorA(False)
        driver.runMotorB(False)

    except Exception as e:
        print("The program is exiting due to", e)
    
    finally:
        driver.runMotorA(False)
        driver.runMotorB(False)
        GPIO.cleanup()

if __name__ == '__main__':
    shutdown()