#
# fhdr: devaddr(4) fctrl(1) fcnt(2) fopts(0..N)
#
from MalformedPacketException import MalformedPacketException
from struct import unpack

class FHDR:

    def __init__(self, mac_payload):
        if len(mac_payload) < 7:
            raise MalformedPacketException("Invalid fhdr")

        self.devaddr = mac_payload[:4]
        self.fctrl = mac_payload[4]
        self.fcnt = mac_payload[5:7]
        self.fopts = mac_payload[7:7 + (self.fctrl & 0xf)]
    
    def length(self):
        return 4 + 1 + 2 + (self.fctrl & 0xf)

    def to_raw(self):
        fhdr = []
        fhdr += self.devaddr
        fhdr += [self.fctrl]
        fhdr += self.fcnt
        fhdr += self.fopts
        return fhdr

    def get_devaddr(self):
        return self.devaddr

    def set_devaddr(self, devaddr):
        self.devaddr = devaddr

    def get_fctrl(self):
        return self.fctrl

    def set_fctrl(self, fctrl):
        self.fctrl = fctrl

    def get_fcnt(self):
        return self.fcnt

    def set_fcnt(self, fcnt):
        self.fcnt = fcnt

    def get_fopts(self):
        return self.fopts

    def set_fopts(self, fopts):
        self.fopts = fopts
