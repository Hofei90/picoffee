import os
import logging
import RPi.GPIO as GPIO
import traceback
import signal
import time

def Interrupt_event(pin):
    print(pin)
    if pin == 26:
        name = "Mahlwerk"
    elif pin == 29:
        name = "Wasser"
    else:
        return
    zustand = GPIO.input(pin)
    logger.info("Relais " + name + " Zustand:" + str(zustand) )

pfad = os.path.abspath(os.path.dirname(__file__))
#Logging
#setlevel = (logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)
setlevel = logging.DEBUG
handler = logging.FileHandler(pfad + "/relais.log")
frm = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%d.%m.%Y %H:%M:%S")
handler.setFormatter(frm)
logger = logging.getLogger("logger")
logger.addHandler(handler)
logger.setLevel(setlevel)

i_mahlwerk = 26
i_wasser = 29

GPIO.setmode(GPIO.BOARD)
#GPIO.setwarnings(False)
GPIO.setup(i_mahlwerk, GPIO.IN)
GPIO.setup(i_wasser, GPIO.IN)

#GPIO.add_event_detect(i_mahlwerk, GPIO.BOTH, callback=Interrupt_event, bouncetime=100)
#GPIO.add_event_detect(i_wasser, GPIO.BOTH, callback=Interrupt_event, bouncetime=100)

while True:
    pass
    time.sleep(0.02)
