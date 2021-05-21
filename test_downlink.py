#!/usr/bin/env python3
"""
    downlink message testing

    NOTE: you need to setup a queued downlink message in the TTN console before
    running this test.

    Downlink messages are only sent for class A devices after an uplink
    message is received by TTN.
"""
import logging
from time import sleep,time
import RPi.GPIO as GPIO
from dragino import Dragino
from dragino.LoRaWAN.MHDR import *


GPIO.setwarnings(False)

logLevel=logging.DEBUG
logging.basicConfig(filename="test_downlink.log", format='%(asctime)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s', level=logLevel)

logging.info("Starting session")

callbackReceived=False

def downlinkCallback(payload,mtype):
    '''
    Called by dragino.on_rx_done() when an UNCONF_DATA_DOWN or CONF_DATA_DOWN downlink message arrives.
    Scheduling a CONF_DATA_DOW message requires an uplink response which
    impacts on the fair use policy. Not recommended!

    payload: bytearray
    mtype: one of UNCONF_DATA_DOWN or CONF_DATA_DOWN
    '''
    global callbackReceived
    callbackReceived = True
    print("downlink message received")

    if mtype==MHDR.UNCONF_DATA_DOWN:
        print("Received UNCONF_DATA_DOWN payload:",payload)
    else:
        print("Received CONF_DATA_DOWN payload:",payload)


D = Dragino("dragino.ini", logging_level=logLevel)

D.setDownlinkCallback(downlinkCallback)

D.join()
while not D.registered():
    print("Waiting for JOIN_ACCEPT")
    sleep(2)


print("Sending a message to prompt for any scheduled downlinks.")
D.send("hello")

print("Waiting for callback message. Press CTRL-C to quit.")
try:
    while not callbackReceived:
        sleep(2)

except Exception as e:
    print("Exception:",e)

print("test_downlink.py Finished")
