import RPi.GPIO as GPIO          
import time
from time import sleep

#Hardware
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

clawServoPin = 17

hMotorPins = [21, 20, 16, 12]
vMotorPins = [26, 19, 13, 6]
baseMotorPins = [5, 22, 27, 18]

rangeMovement = 64

motorSequence = [
            [1, 0, 0, 1],
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1]
]

GPIO.setup(clawServoPin, GPIO.OUT)
clawPWM = GPIO.PWM(clawServoPin, 50)

#init states
def init_default_states():
    clawPWM.start(0)
    reset_all_pins()

#Set all pins as output
def reset_all_pins():
    for pin in hMotorPins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)
            
    for pin in vMotorPins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)
    
    for pin in baseMotorPins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)


### Define motion
def move_backwards(range_value : int):
    if range_value is None : range_value = rangeMovement
    for i in range(range_value):
         for halfstep in range(8):
                for pin in range(4):
                        GPIO.output(vMotorPins[pin], motorSequence[halfstep][pin])
                        time.sleep(0.001)
    reset_all_pins()
    
def move_forward(range_value : int):
    if range_value is None : range_value = rangeMovement
    for i in range(range_value):
         for halfstep in reversed(range(8)):
                for pin in reversed(range(4)):
                        GPIO.output(vMotorPins[pin], motorSequence[halfstep][pin])
                        time.sleep(0.001)
    reset_all_pins()

def move_up(range_value : int):
    if range_value is None : range_value = rangeMovement
    for i in range(range_value):
         for halfstep in reversed(range(8)):
                for pin in reversed(range(4)):
                        GPIO.output(hMotorPins[pin], motorSequence[halfstep][pin])
                        time.sleep(0.001)
    reset_all_pins()

def move_down(range_value : int):
    if range_value is None : range_value = rangeMovement
    for i in range(range_value):
         for halfstep in range(8):
                for pin in range(4):
                        GPIO.output(hMotorPins[pin], motorSequence[halfstep][pin])
                        time.sleep(0.001)
    reset_all_pins()
    
def rotate_base_clockwise(range_value : int):
    if range_value is None : range_value = rangeMovement
    for i in range(range_value):
         for halfstep in range(8):
                for pin in range(4):
                        GPIO.output(baseMotorPins[pin], motorSequence[halfstep][pin])
                        time.sleep(0.001)
    reset_all_pins()
    
def rotate_base_counter_clockwise(range_value : int):
    if range_value is None : range_value = rangeMovement
    for i in range(range_value):
         for halfstep in reversed(range(8)):
                for pin in reversed(range(4)):
                        GPIO.output(baseMotorPins[pin], motorSequence[halfstep][pin])
                        time.sleep(0.001)
    reset_all_pins()


def control_claw( angle):

    setAngle(angle)
    clawPWM.stop()

def setAngle(angle):
    if(angle == 0):
        clawPWM.start(0)
        clawPWM.ChangeDutyCycle(0)
        sleep(1)
        clawPWM.stop()
    else:
        #for i in range(2, 7, 1):
        clawPWM.ChangeDutyCycle(float(angle))
        sleep(0.2)
           
        clawPWM.ChangeDutyCycle(0)
        sleep(1)
    
        #print ('set Angle: ' + angle)
        #duty = float(angle)#/18+2
        #GPIO.output(clawServoPin, True)
        #clawPWM.ChangeDutyCycle(duty)
        #sleep(1)
        #GPIO.output(clawServoPin, False)
        #clawPWM.ChangeDutyCycle(0)
   
#We need to reset the pins after each action so that we don't keep the stepper motors under load

#Set all pins in default mode
def stopMovement():
    reset_all_pins()

#This metod will disable any action regarding GPIO pins
#After this method is called we need to reinitailize the GPIO pins
def close():
    GPIO.cleanup()