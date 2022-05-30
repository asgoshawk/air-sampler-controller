'''
##################################################################

Tkinter Window Settings

'''
HEIGHT  = 480
WIDTH   = 640
BG_COLOR    = '#282a36'
FG_COLOR    = '#f8f8f2'
CUR_LINE    = '#44475a'
COMMENT     = '#6272a4'
GREEN       = '#50fa7b'
RED         = '#ff5555'
PINK        = '#ff79c6'
YELLOW      = '#f1fa8c'
ORANGE      = '#ffb86c'

'''
##################################################################

Flow Settings

CAL_PARAMS: 
    Calibration parameters for flow rate.
    For a n-dim params array (p), the flow rate equals:
    p[0]*x**n + p[1]*x**(n-1) + ... + p[n-2]*x + p[n-1] 
    where x is (TP2 - TP1) in current version. 

OUTPUT_SEC:
    Write the analog output and flow rate every n sec to csv file.

ADC_ADDR:
    The ADS1115 I2C address. Default is 0x48.

ADC_GAIN:
    The gain of ADS1115:
    GAIN    RANGE (V)
    ----    ---------
     2/3    +/- 6.144
       1    +/- 4.096
       2    +/- 2.048
       4    +/- 1.024
       8    +/- 0.512
      16    +/- 0.256

'''
CAL_PARAMS  = [11.32749266, 36.21084542, 13.66281863]   
OUTPUT_SEC  = 3
ADC_ADDR    = 0x48
ADC_GAIN    = 1

'''
##################################################################

Motor Settings

GPIO_MODE:
    Set the GPIO mode of RPi to "BCM" of "BOARD". 
    More information please visit: https://pinout.xyz/

INPA1, INPA2:
    GPIO pins that control the positive and negative pins of motor A.

INPB1, INPB2:
    GPIO pins that control the positive and negative pins of motor B.

'''
GPIO_MODE   = "BCM" 
INPA1       = 17
INPA2       = 27
INPB1       = 23
INPB2       = 24
