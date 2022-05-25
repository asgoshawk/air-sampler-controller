import RPi.GPIO as GPIO
import settings
from motor import MotorDriver

def shutdown():
    try:
        if settings.GPIO_MODE == "BOARD":
            GPIO.setmode(GPIO.BOARD)
        else:
            GPIO.setmode(GPIO.BCM)
        # GPIO.setwarnings(False)
        inpA1   = settings.INPA1
        inpA2   = settings.INPA2
        inpB1   = settings.INPB1
        inpB2   = settings.INPB2
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