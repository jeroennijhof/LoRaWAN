#!/usr/bin/env python3
from time import sleep
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
import LoRaWAN

BOARD.setup()
parser = LoRaArgumentParser("LoRaWAN receiver")

class LoRaWANrcv(LoRa):
    def __init__(self, nwkey = [], appkey = [], verbose = False):
        super(LoRaWANrcv, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
        self.nwkey = nwkey
        self.appkey = appkey

    def on_rx_done(self):
        print("RxDone")

        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        print("".join(format(x, '02x') for x in bytes(payload)))

        lorawan = LoRaWAN.new(self.nwkey, self.appkey)
        lorawan.read(payload)
        print(lorawan.get_mhdr().get_mversion())
        print(lorawan.get_mhdr().get_mtype())
        print(lorawan.get_mic())
        print(lorawan.compute_mic())
        print(lorawan.valid_mic())
        print("".join(list(map(chr, lorawan.get_payload()))))

        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def on_tx_done(self):
        print("TxDone")
        print(self.get_irq_flags())

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
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        while True:
            sleep(.5)


# Init
nwkey = [0xC3, 0x24, 0x64, 0x98, 0xDE, 0x56, 0x5D, 0x8C, 0x55, 0x88, 0x7C, 0x05, 0x86, 0xF9, 0x82, 0x26]
appkey = [0x15, 0xF6, 0xF4, 0xD4, 0x2A, 0x95, 0xB0, 0x97, 0x53, 0x27, 0xB7, 0xC1, 0x45, 0x6E, 0xC5, 0x45]
lora = LoRaWANrcv(nwkey, appkey, False)

# Setup
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
    print("")
    lora.set_mode(MODE.SLEEP)
    print(lora)
    BOARD.teardown()
