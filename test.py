#!/usr/bin/env python3
"""
    Test harness for dragino module - sends hello world out over LoRaWAN 5 times
"""
import logging
from time import sleep
import RPi.GPIO as GPIO
from dragino import Dragino


GPIO.setwarnings(False)

D = Dragino("dragino.ini", logging_level=logging.DEBUG)
D.join()
while not D.registered():
    print("Waiting")
    sleep(2)
#sleep(10)
for i in range(0, 5):
    D.send("Hello World")
    print("Sent message")
    sleep(1)
