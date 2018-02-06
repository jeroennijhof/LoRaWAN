#!/usr/bin/env python3
###############################################################################
#Basic interface for dragino LoRa/GPS HAT
#Copyright (C) 2018 Philip Basford

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as
#published by the Free Software Foundation, either version 3 of the
#License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.

#You should have received a copy of the GNU Affero General Public License
#along with this program.  If not, see <https://www.gnu.org/licenses/>.
###############################################################################
from time import sleep
from random import randrange
from datetime import datetime, timedelta
import logging
from serial import Serial
from SX127x.LoRa import LoRa, MODE
from SX127x.board_config import BOARD
import LoRaWAN
from LoRaWAN.MHDR import MHDR
from FrequncyPlan import LORA_FREQS
import pynmea2

DEFAULT_SF = 7
MAX_POWER = 0x0F
OUTPUT_POWER = 0x0E
SYNC_WORD = 0x34
RX_CRC = True
TX_WAIT = 0
DEFAULT_LOG_LEVEL = logging.INFO #Change after finishing development
DEFAULT_BAUD_RATE = 9600
DEFAULT_SERIAL_PORT = "/dev/serial0"
DEFAULT_SERIAL_TIMEOUT = 1 # How long to timeout on reading a line
DEFAULT_WAIT_PERIOD = 10 # How long to wait to get a GPS position
class Dragino(LoRa):
    def __init__(self, freqs=LORA_FREQS, sf=DEFAULT_SF,
            logging_level=DEFAULT_LOG_LEVEL,
            gps_baud_rate=DEFAULT_BAUD_RATE,
            gps_serial_port=DEFAULT_SERIAL_PORT,
            gps_serial_timeout=DEFAULT_SERIAL_TIMEOUT):
        self.logger = logging.getLogger("Dragino")
        self.logger.setLevel(logging_level)
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        BOARD.setup()
        super(Dragino, self).__init__(logging_level < logging.INFO)
        self.devnonce = [randrange(256), randrange(256)] #random none
        self.logger.debug("Nonce = %s", self.devnonce)
        self.freqs = freqs
        self.device_addr = None
        self.network_key = None
        self.apps_key = None
        self.frame_count = 0
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([1, 0, 0, 0, 0, 0])
        freq = freqs[randrange(len(freqs))]#Pick a random frequency
        self.set_freq(freq)
        self.logger.info("Frequency = %s", freq)
        self.set_pa_config(pa_select=1)
        self.set_spreading_factor(sf)
        self.logger.info("SF = %s", sf)
        self.set_pa_config(max_power=MAX_POWER, output_power=OUTPUT_POWER)
        self.set_sync_word(SYNC_WORD)
        self.set_rx_crc(RX_CRC)
        assert self.get_agc_auto_on() == 1
        self.gps_serial = Serial(gps_serial_port, gps_baud_rate, timeout=gps_serial_timeout)



    def on_rx_done(self):
        self.logger.debug("Recieved message")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        lorawan = LoRaWAN.new([], self.appkey)
        lorawan.read(payload)
        lorawan.get_payload()
#        print(lorawan.get_mhdr().get_mversion())
        if lorawan.get_mhdr().get_mtype() == MHDR.JOIN_ACCEPT:
            self.logger.debug("Join resp")
            #It's a response to a join request
            lorawan.valid_mic()
            self.device_addr = lorawan.get_devaddr()
            self.logger.info("Device: %s", self.device_addr)
            self.network_key = lorawan.derive_nwskey(self.devnonce)
            self.logger.info("Network key: %s", self.network_key)
            self.apps_key = lorawan.derive_appskey(self.devnonce)
            self.logger.info("APPS key: %s", self.apps_key)

    def on_tx_done(self):
        self.logger.debug("TX Complete")
        self.clear_irq_flags(TxDone=1)
        self.set_mode(MODE.STDBY)
        self.set_dio_mapping([0, 0, 0, 0, 0, 0])
        self.set_invert_iq(1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def join(self, appkey, appeui, deveui):
        self.logger.debug("Performing Join")
        self.logger.info("App key = %s", appkey)
        self.logger.info("App eui = %s", appeui)
        self.logger.info("Dev eui = %s", deveui)
        self.appkey = appkey
        self.appeui = appeui
        self.deveui = deveui
        self.frame_count = 1
        lorawan = LoRaWAN.new(appkey)
        lorawan.create(
            MHDR.JOIN_REQUEST,
            {'deveui': deveui, 'appeui': appeui, 'devnonce': self.devnonce})
        self.write_payload(lorawan.to_raw())
        self.set_mode(MODE.TX)
        sleep(TX_WAIT)

    def registered(self):
        return self.device_addr is not None

    def send_bytes(self, message):
        lorawan = LoRaWAN.new(self.network_key, self.apps_key)
        lorawan.create(
            MHDR.UNCONF_DATA_UP,
            {'devaddr': self.device_addr,
             'fcnt': self.frame_count,
             'data': message})
        self.logger.debug("Frame count %d", self.frame_count)
        self.frame_count += 1
        self.write_payload(lorawan.to_raw())
        self.logger.debug("Packet = %s", lorawan.to_raw())
        self.set_dio_mapping([1, 0, 0, 0, 0, 0])
        self.set_mode(MODE.TX)
    
    def send(self, message):
        self.send_bytes(list(map(ord, str(message))))

    def get_gps(self, wait_period=DEFAULT_WAIT_PERIOD):
        start = datetime.utcnow()
        end = start + timedelta(seconds=wait_period)
        self.logger.info("Waiting for %d seconds until %s", wait_period, end)
        msg = None

        while datetime.utcnow() < end:
            gps_data = self.gps_serial.readline().decode() # read the serial port, convert to a string 
            gps_data_arr = gps_data.split(",")
            if gps_data[0] == "$GPGGA": #It's a position string
                print(gps_data)
                msg = pynmea2.parse(gps_data)
                break
        return msg # this will be None if no message is decoded, otherwise it'll contain the information
