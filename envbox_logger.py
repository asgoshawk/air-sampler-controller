import time
import statistics
import datetime
import pytz
import math
import board
import busio
import RPi.GPIO as GPIO
import adafruit_mlx90614
import adafruit_veml6070
from adafruit_bme280 import basic as adafruit_bme280
from adafruit_ads1x15 import ads1115 as adafruit_ads1115
from adafruit_ads1x15.analog_in import AnalogIn
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from multiprocessing import Queue
from threading import Event, Thread
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

class SG90:
    def __init__(self, pwmpin):
        self._servo = Servo(
            pwmpin,
            min_pulse_width=0.5/1000,
            max_pulse_width=2.5/1000,
            pin_factory=PiGPIOFactory())
        self._deg   = 0

    @property
    def deg(self):
        return self._deg
    
    @deg.setter
    def deg(self, value):
        if value < -90 or value > 90:
            raise AttributeError('The deg should be -90 to 90 deg.')
        else:
            self._deg           = value
            self._servo.value   = math.sin(math.radians(value))

class RainEventHandler:
    def __init__(self, threshold, maxRawSize):
        self.rawList    = []
        self.rainStart  = False
        self.threshold  = threshold
        self.maxRawSize = maxRawSize 

    def add(self, rawReadout):
        if self.rainStart:
            if len(self.rawList) < self.maxRawSize:
                self.rawList.append(rawReadout)
            else:
                self.rawList.pop(0)
                self.rawList.append(rawReadout)
        else:
            if rawReadout < self.threshold:
                self.rawList.append(rawReadout)
                self.rainStart = True

    def rawList(self):
        return self.rawList

    def checkRainStart(self):
        return self.rainStart

    def checkRainStop(self):
        if not self.rainStart:
            return True
        else:
            if len(self.rawList) < self.maxRawSize or statistics.mean(self.rawList) < self.threshold:
                return False
            else:
                self.rainStart  = False
                self.rawList = []
                return True

class UploadDataThread (Thread):
    def __init__(self, ifclient, iforg, ifbucket, queue): 
        Thread.__init__(self)
        self.client = ifclient
        self.org = iforg
        self.bucket = ifbucket
        self.queue = queue

    def run(self):
        print("Starting upload thread.")
        while True:
            val = self.queue.get()
            print("Uploading Data.")
            try:
                write_api = self.client.write_api(write_options=SYNCHRONOUS)
                write_api.write(self.bucket, self.org, val)
            except Exception as e:
                print(e)

class CallRepeatedly(Thread):
    def __init__(self, event, interval, func, args):
        Thread.__init__(self)
        self.stopped = event
        self.interval = interval
        self.func = func
        self.args = args

    def run(self):
        while not self.stopped.wait(self.interval - time.time() % self.interval): # the first call is in `interval` secs
            self.func(self.args)

###############################################################
# Parameter settings
###############################################################
pwmPin          = 12
uploadToDB      = False
token           = "kwDrnu5ZHJdjP2rjWHAA_CnB4PWsa7AZJfOhAFN5oWcd6d3jihLBAWp2S4gFbpqRnmiob5RYoCnXcZ2w2J7knQ=="
org             = "ACLab"
bucket          = "envBox"
url             = "http://140.112.66.46:8086"
utc             = pytz.UTC
tw              = pytz.timezone('Asia/Taipei')
rainThreshold   = 3.1
rainMaxRawSize  = 20
rainHandler     = RainEventHandler(rainThreshold, rainMaxRawSize)
rain            = {"raw": 0.0, "start": False, "stop": False}

###############################################################
# Initialization processes
###############################################################
print("\n", "="*50, sep ="")
print("Initializing the devices...")

# PWM servo
try:
    servo       = SG90(pwmPin)
    servo.deg   = 90
    print("SG90 is set.")
    time.sleep(2)
except Exception as e:
    print("Failed to set the SG90.")
    print("Error:",e)

# I2C device
i2c         = busio.I2C(board.SCL, board.SDA)

try:
    ads1115     = adafruit_ads1115.ADS1115(i2c)
    ads1115.gain= 1
    channels    = [adafruit_ads1115.P0, adafruit_ads1115.P1, adafruit_ads1115.P2, adafruit_ads1115.P3]
    adschls     = [AnalogIn(ads1115, chl) for chl in channels] 
    print("ADS1115  connected.")
except Exception as e:
    print("Failed to connect to ADS1115.")
    print("Error:",e)
time.sleep(0.5)

try:  
    bme280      = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
    print("BME280   connected.")
except Exception as e:
    print("Failed to connect to BME280.")
    print("Error:",e)
time.sleep(0.5)

try:
    mlx90614    = adafruit_mlx90614.MLX90614(i2c)
    print("MLX90614 connected.")
except Exception as e:
    print("Failed to connect to MLX90614.")
    print("Error:",e)
time.sleep(0.5)

try:
    veml6070    = adafruit_veml6070.VEML6070(i2c)
    print("VEML6070 connected.")
except Exception as e:
    print("Failed to connect to VEML6070.")
    print("Error:",e)
time.sleep(0.5)

print("Initialization completed.")

###############################################################
# Data logger
###############################################################
def data_logger(rain):

    temp_bme    = bme280.temperature
    humd_bme    = bme280.relative_humidity
    pres_bme    = bme280.pressure

    # adc_volts   = [chl.voltage for chl in adschls]

    temp_amb    = mlx90614.ambient_temperature
    temp_obj    = mlx90614.object_temperature
    uv_veml     = veml6070.uv_raw
    uv_guva     = adschls[0].voltage

    rain_event      = 0
    rain_raw        = rain["raw"]
    if rain["start"] or not rain["stop"]:
        rain_event = 1

    localTime   = tw.localize(datetime.datetime.now())

    print("="*50)
    print(localTime.strftime("%Y-%m-%d %H:%M:%S"))
    print("T_bme  : %5.2f C, RH_bme : %5.2f %%, P_bme: %6.1f hPa" %(temp_bme, humd_bme, pres_bme))
    print("AT_mlx : %5.2f C, OT_mlx : %5.2f C" %(temp_amb, temp_obj))
    print("UV_veml:   %5d, UV_guva: %7.2f" %(uv_veml, uv_guva))
    print("Rain_raw: %.4f, Rain_event: %d" %(rain_raw, rain_event))
    print(rainHandler.rawList)

    if uploadToDB:
        body = [
            {
                "measurment": "envProto0",
                "time": localTime.astimezone(utc),
                "fields": {
                    "temp_bme": float(temp_bme),
                    "humd_bme": float(humd_bme),
                    "pres_bme": float(pres_bme),
                    "temp_amb": float(temp_amb),
                    "temp_obj": float(temp_obj),
                    "uv_veml": float(uv_veml),
                    "uv_guva": float(uv_guva),
                    "rain_raw": float(rain_raw),
                    "rain_event": int(rain_event),
                }
            }
        ]
        dataQueue.put(body)

###############################################################
# Rain shield action
###############################################################
def rain_shield(rain):
    rain["raw"]     = adschls[1].voltage
    rainHandler.add(rain["raw"])
    rain["start"]   = rainHandler.checkRainStart()
    rain["stop"]    = rainHandler.checkRainStop()
    if rain["start"]:
        if servo.deg != 90:
            servo.deg   = 90
    if rain["stop"]:
        if servo.deg != -90:
            servo.deg    = -90

###############################################################
# Main loop and thread
###############################################################
dataQueue       = Queue(300)
if uploadToDB:
    client = InfluxDBClient(url="http://140.112.66.46:8086", token=token, debug=False)
    uploadDataThread(client, org, bucket, dataQueue).start()

repeatEvent     = Event()
repeatThread0   = CallRepeatedly(repeatEvent, 0.5, rain_shield, rain)
repeatThread1   = CallRepeatedly(repeatEvent, 2, data_logger, rain)
repeatThread0.start()
repeatThread1.start()

try:
    time.sleep(1)

except (KeyboardInterrupt, SystemExit):
    print()
    print("Exiting the program...")
    # if UploadData:
    #     client.close()
    repeatEvent.set()
    GPIO.cleanup()
    exit()
