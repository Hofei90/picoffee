#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# v0.3 by meigrafd
#
import RPi.GPIO as GPIO
import time, signal
from subprocess import call
#------------------------------------------------------------------------

# use the raspi board pin number
GPIO.setmode(GPIO.BOARD)
# use the gpio number
#GPIO.setmode(GPIO.BCM)

shutdownPin = 5 # with GPIO.BOARD, pin#5 is gpio3
ledPin = 7 # with GPIO.BOARD, pin#7 is gpio4

# how often should the LED blink?
blinkRepeat = 5
# blink speed (sec)?
blinkSpeed = 0.5

#------------------------------------------------------------------------

GPIO.setup(ledPin, GPIO.OUT)
GPIO.output(ledPin, True)
GPIO.setup(shutdownPin, GPIO.IN)

def blinkLED(pin, speed):
    GPIO.output(pin, False)
    time.sleep(speed)
    GPIO.output(pin, True)

def Interrupt_event(pin):
    if GPIO.input(shutdownPin):
        for x in range(0, (blinkRepeat + 1)):
            blinkLED(int(ledPin), float(blinkSpeed))
        #run command
        call('poweroff', shell=False)

try:
    GPIO.add_event_detect(shutdownPin, GPIO.RISING, callback=Interrupt_event, bouncetime=150)
    #keep script running
    signal.pause()
except (KeyboardInterrupt, SystemExit):
    GPIO.cleanup() 