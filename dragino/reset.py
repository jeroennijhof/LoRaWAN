#!/usr/bin/env python

#Original Version Jeroen Nijhof http://www.jeroennijhof.nl
#Modified 2018-01-10 Philip Basford Compatibility with Dragino LoRa Sheild
import RPi.GPIO as GPIO  
import time
PIN = 11
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)
GPIO.output(PIN, GPIO.HIGH)  
time.sleep(.100)
GPIO.output(PIN, GPIO.LOW)  
GPIO.cleanup()   
