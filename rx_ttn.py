#!/usr/bin/env python3
from time import sleep
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
import LoRaWAN

BOARD.setup()
parser = LoRaArgumentParser("LoRaWAN receiver")

class LoRaWANrcv(LoRa):
    def __init__(self, verbose = False):
        super(LoRaWANrcv, self).__init__(verbose)

    def on_rx_done(self):
        print("RxDone")

        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        print("".join(format(x, '02x') for x in bytes(payload)))

        lorawan = LoRaWAN.new(nwskey, appskey)
        lorawan.read(payload)
        print(lorawan.get_mhdr().get_mversion())
        print(lorawan.get_mhdr().get_mtype())
        print(lorawan.get_mic())
        print(lorawan.compute_mic())
        print(lorawan.valid_mic())
        print("".join(list(map(chr, lorawan.get_payload()))))
        print("\n")

        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def start(self):
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        while True:
            sleep(.5)


# Init
nwskey = [0xC3, 0x24, 0x64, 0x98, 0xDE, 0x56, 0x5D, 0x8C, 0x55, 0x88, 0x7C, 0x05, 0x86, 0xF9, 0x82, 0x26]
appskey = [0x15, 0xF6, 0xF4, 0xD4, 0x2A, 0x95, 0xB0, 0x97, 0x53, 0x27, 0xB7, 0xC1, 0x45, 0x6E, 0xC5, 0x45]
lora = LoRaWANrcv(False)

# Setup
lora.set_mode(MODE.SLEEP)
lora.set_dio_mapping([0] * 6)
lora.set_freq(868.1)
lora.set_pa_config(pa_select=1)
lora.set_spreading_factor(7)
lora.set_sync_word(0x34)
lora.set_rx_crc(True)

print(lora)
assert(lora.get_agc_auto_on() == 1)

try:
    print("Waiting for incoming LoRaWAN messages\n")
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("\nKeyboardInterrupt")
finally:
    sys.stdout.flush()
    lora.set_mode(MODE.SLEEP)
    BOARD.teardown()
