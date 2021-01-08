import RPi.GPIO as GPIO
from time import sleep
from threading import Timer
from timeout import timeout

stt = False

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.cleanup()

buzzerPin = 21
GPIO.setup(buzzerPin, GPIO.OUT)

def beep():
    print("Beep")
    def offBeep():
        GPIO.output(buzzerPin, GPIO.LOW)

    GPIO.output(buzzerPin, GPIO.HIGH)

    timer = Timer(1, offBeep)
    timer.start()

@timeout(1000)
def beepdlu() :
    global stt, buzzer, GPIO

    if stt :
        # GPIO.output(buzzer,GPIO.HIGH)
        print("Beep")
    else :
        # GPIO.output(buzzer,GPIO.LOW)
        print("No Beep")
    
    stt = not stt

try:
    # while True:
    beep()
except KeyboardInterrupt:
    pass

GPIO.cleanup()
