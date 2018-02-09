#!/usr/bin/env python3
from time import sleep
import RPi.GPIO as GPIO
import dragino
from tx_config import * 
GPIO.setwarnings(False)

D = dragino.Dragino()
D.set_abp(devaddr, nwskey, appskey)
while not D.registered():
    print("Waiting")
    sleep(2)
#sleep(10)
for i in range(0,20):
    D.send("Hello World")
    print("Sent message")
    sleep(1)
