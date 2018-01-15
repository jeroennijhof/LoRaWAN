#!/usr/bin/env python3
from time import sleep
import RPi.GPIO as GPIO
import dragino
from otaa_config import * 
GPIO.setwarnings(False)

D = dragino.Dragino()
D.join(appkey, appeui, deveui)
while not D.registered():
    print("Waiting")
    sleep(2)
#sleep(10)
for i in range(0,5):
    D.send("Hello World")
    sleep(10)
