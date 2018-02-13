#!/usr/bin/env python3
from time import sleep
import RPi.GPIO as GPIO
import dragino
import logging
from otaa_config import * 
GPIO.setwarnings(False)

D = dragino.Dragino("dragino.ini", logging_level=logging.DEBUG)
D.join()
while not D.registered():
    print("Waiting")
    sleep(2)
#sleep(10)
for i in range(0,5):
    D.send("Hello World")
    print("Sent message")
    sleep(1)
