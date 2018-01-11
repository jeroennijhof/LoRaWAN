#!/usr/bin/env python3
#Original Version Jeroen Nijhof http://www.jeroennijhof.nl
#Modified 2018-01-10 Philip Basford Various changes to move confidential data
#Also print statments changed

import sys
from time import sleep
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
import LoRaWAN
from LoRaWAN.MHDR import MHDR
from random import randrange
from otaa_config import *
BOARD.setup()
parser = LoRaArgumentParser("LoRaWAN sender")

class LoRaWANotaa(LoRa):
    def __init__(self, verbose = False):
        super(LoRaWANotaa, self).__init__(verbose)

    def on_rx_done(self):
        print("RxDone")

        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)

        lorawan = LoRaWAN.new([], appkey)
        lorawan.read(payload)
        print(lorawan.get_payload())
        print(lorawan.get_mhdr().get_mversion())

        if lorawan.get_mhdr().get_mtype() == MHDR.JOIN_ACCEPT:
            print("Got LoRaWAN join accept")
            print(lorawan.valid_mic())
            devaddr = (lorawan.get_devaddr())
            print("Device ID: %s" % devaddr)
            nwskey = lorawan.derive_nwskey(devnonce)
            appskey = lorawan.derive_appskey(devnonce)
            print("Network Key: %s" % nwskey)
            print("Application Key: %s" %appskey)
            print("\n")
            fcnt = 0
            while(1):
                print("Sending message\n")
                lorawan = LoRaWAN.new(nwskey, appskey)
                lorawan.create(MHDR.UNCONF_DATA_UP, {'devaddr': devaddr, 'fcnt': fcnt, 'data': list(map(ord, 'Python rules!')) })
                fcnt += 1
                self.write_payload(lorawan.to_raw())
                self.set_mode(MODE.TX)
                sleep(10)
            sys.exit(0)

        print("Got LoRaWAN message continue listen for join accept")

    def on_tx_done(self):
        self.clear_irq_flags(TxDone=1)
        print("TxDone")

        self.set_mode(MODE.STDBY)
        self.set_dio_mapping([0,0,0,0,0,0])
        self.set_invert_iq(1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def start(self):
        self.tx_counter = 1

        lorawan = LoRaWAN.new(appkey)
        lorawan.create(MHDR.JOIN_REQUEST, {'deveui': deveui, 'appeui': appeui, 'devnonce': devnonce})

        self.write_payload(lorawan.to_raw())
        self.set_mode(MODE.TX)
        while True:
            sleep(1)


# Init
devnonce = [randrange(256), randrange(256)]
lora = LoRaWANotaa(False)

# Setup
lora.set_mode(MODE.SLEEP)
lora.set_dio_mapping([1,0,0,0,0,0])
lora.set_freq(868.1)
lora.set_pa_config(pa_select=1)
lora.set_spreading_factor(7)
lora.set_pa_config(max_power=0x0F, output_power=0x0E)
lora.set_sync_word(0x34)
lora.set_rx_crc(True)

#print(lora)
assert(lora.get_agc_auto_on() == 1)

try:
    print("Sending LoRaWAN join request\n")
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("\nKeyboardInterrupt")
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()
