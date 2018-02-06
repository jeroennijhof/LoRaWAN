#!/usr/bin/env python3
from time import sleep
import RPi.GPIO as GPIO
import dragino
from sch_config import * 
GPIO.setwarnings(False)
DATA=[1, 4, 99, 1, 200, 3, 21, 1, 194, 3, 232, 3, 233, 3, 234, 3, 235, 3, 236, 10, 11, 20, 21, 30, 31, 40, 41, 0, 95, 1, 47]
D = dragino.Dragino()
D.join(appkey, appeui, deveui)
while not D.registered():
    print("Waiting")
    sleep(2)
#sleep(10)
for i in range(0,5):
    D.send_bytes(DATA)
    print("Sent message")
    sleep(10)
