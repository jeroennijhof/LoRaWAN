#!/usr/bin/env python3
from time import sleep
from datetime import datetime
import RPi.GPIO as GPIO
import logging

import dragino
from otaa_config import * 

PER_MESSAGE_WAIT = 3600 #How long to wait between messages (seconds)
GPIO.setwarnings(False)

LOGGER = logging.getLogger("LoRaHAT Test")
LOGGER.setLevel(logging.DEBUG)
logging.basicConfig(format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')

D = dragino.Dragino()
LOGGER.info("Connecting")
D.join(appkey, appeui, deveui)
while not D.registered():
    LOGGER.info("Waiting")
    sleep(2)
LOGGER.info("Connected")
while True:
    try:
        D.send(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        LOGGER.info("Sent message")
    except Exception as e:
        LOGGER.error(str(e))
    sleep(PER_MESSAGE_WAIT)
