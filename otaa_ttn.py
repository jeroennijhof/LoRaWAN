#!/usr/bin/env python3
import sys
from time import sleep
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
import LoRaWAN
from LoRaWAN.MHDR import MHDR

BOARD.setup()
parser = LoRaArgumentParser("LoRaWAN sender")

class LoRaWANsend(LoRa):
    def __init__(self, deveui = [], appeui = [], appkey = [], devnonce = [], verbose = False):
        super(LoRaWANsend, self).__init__(verbose)
        self.deveui = deveui
        self.appeui = appeui
        self.appkey = appkey
        self.devnonce = devnonce

    def on_rx_done(self):
        print("RxDone")

        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)

        lorawan = LoRaWAN.new([], appkey)
        lorawan.read(payload)
        print(lorawan.get_payload())
        print(lorawan.get_mhdr().get_mversion())
        print(lorawan.get_mhdr().get_mtype())
        print(lorawan.get_mic())
        print(lorawan.compute_mic())
        print(lorawan.valid_mic())
        print(lorawan.derive_nwkey(devnonce))
        print(lorawan.derive_appkey(devnonce))
        print("\n")
        sys.exit(0)

    def on_tx_done(self):
        self.clear_irq_flags(TxDone=1)
        print("TxDone")

        self.set_mode(MODE.STDBY)
        self.set_dio_mapping([0,0,0,0,0,0])
        self.set_invert_iq(1)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def on_cad_done(self):
        print("on_CadDone")
        print(self.get_irq_flags())

    def on_rx_timeout(self):
        print("on_RxTimeout")
        print(self.get_irq_flags())

    def on_valid_header(self):
        print("on_ValidHeader")
        print(self.get_irq_flags())

    def on_payload_crc_error(self):
        print("on_PayloadCrcError")
        print(self.get_irq_flags())

    def on_fhss_change_channel(self):
        print("on_FhssChangeChannel")
        print(self.get_irq_flags())

    def start(self):
        self.tx_counter = 1

        lorawan = LoRaWAN.new(self.appkey)
        lorawan.create(MHDR.JOIN_REQUEST, {'deveui': self.deveui, 'appeui': self.appeui, 'devnonce': self.devnonce})

        self.write_payload(lorawan.to_raw())
        self.set_mode(MODE.TX)
        while True:
            sleep(1)


# Init
deveui = [0x00, 0x82, 0xAA, 0x0D, 0x42, 0x9C, 0x79, 0x34]
appeui = [0x70, 0xB3, 0xD5, 0x7E, 0xF0, 0x00, 0x4D, 0xBC]
appkey = [0x13, 0x1C, 0x8A, 0xF7, 0xA3, 0xE4, 0x35, 0xD0, 0xD5, 0xE9, 0x47, 0x6B, 0x04, 0xB9, 0x16, 0x39]
devnonce = [0x01, 0x25]
lora = LoRaWANsend(deveui, appeui, appkey, devnonce, False)

# Setup
lora.set_mode(MODE.SLEEP)
lora.set_dio_mapping([1,0,0,0,0,0])
lora.set_freq(868.1)
lora.set_pa_config(pa_select=1)
lora.set_spreading_factor(7)
lora.set_pa_config(max_power=0x0F, output_power=0x0E)
lora.set_sync_word(0x34)
lora.set_rx_crc(True)

print(lora)
assert(lora.get_agc_auto_on() == 1)

try:
    print("Sending LoRaWAN message\n")
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("\nKeyboardInterrupt")
finally:
    sys.stdout.flush()
    print("")
    lora.set_mode(MODE.SLEEP)
    print(lora)
    BOARD.teardown()
