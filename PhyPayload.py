#
# lorawan packet: mhdr(1) mac_payload(1..N) mic(4)
#
from MalformedPacketException import MalformedPacketException
from Direction import Direction
from MType import MType
from MacPayload import MacPayload
from MajorVersion import MajorVersion

class PhyPayload:

    def __init__(self):
        self.direction = Direction(Direction.UP)

    def length(self):
        return len(self.to_raw())

    def to_raw(self):
        phy_payload = [self.mhdr]
        phy_payload += self.mac_payload.to_raw()
        phy_payload += self.mic
        return phy_payload

    def packet(self, packet):
        if len(packet) < 12:
            raise MalformedPacketException("Invalid lorawan packet");

        self.mhdr = packet[0]
        self.mversion = MajorVersion(self.mhdr)
        self.mtype = MType(self.mhdr)
        self.mac_payload = MacPayload(self.mtype.get(), packet[1:-4]);
        self.mic = packet[-4:]
        self.packet = packet[:-4]

    def get_mtype(self):
        return self.mtype.get()

    def get_mversion(self):
        return self.mversion.get()

    def get_mhdr(self):
        return self.mhdr;

    def set_mhdr(self, mhdr):
        self.mhdr = mhdr

    def get_direction(self):
        return self.direction.get()

    def set_direction(self, direction):
        self.direction = Direction(direction)

    def get_mac_payload(self):
        return self.mac_payload

    def set_mac_payload(self, mac_payload):
        self.mac_payload = mac_payload

    def get_mic(self):
        return self.mic

    def set_mic(self, mic):
        self.mic = mic

    def compute_mic(self, key):
        return self.mac_payload.frm_payload.compute_mic(key, self.get_direction(), self.get_mhdr())

    def get_payload(self, key):
        return self.mac_payload.frm_payload.decrypt_payload(key, self.get_direction())
