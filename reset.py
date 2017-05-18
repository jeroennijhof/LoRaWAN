#!/usr/bin/env python
import RPi.GPIO as GPIO  
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)  
time.sleep(.100)
GPIO.output(17, GPIO.LOW)  
GPIO.cleanup()   
