#
# lorawan packet: mhdr(1) mac_payload(1..N) mic(4)
#
from MalformedPacketException import MalformedPacketException
from Direction import Direction
from MType import MType
from MacPayload import MacPayload
from MajorVersion import MajorVersion

class PhyPayload:

    def __init__(self, key):
        self.key = key

    def read(self, packet):
        if len(packet) < 12:
            raise MalformedPacketException("Invalid lorawan packet");

        self.mhdr = packet[0]
        self.mversion = MajorVersion(self.get_mhdr())
        self.mtype = MType(self.get_mhdr())
        self.direction = Direction(self.mtype.get())
        self.mac_payload = MacPayload()
        self.mac_payload.read(self.mtype.get(), packet[1:-4])
        self.mic = packet[-4:]

    def create(self, mtype, args):
        self.mhdr = MajorVersion.LORAWAN_R_1 | (mtype << 5)
        self.mversion = MajorVersion(self.get_mhdr())
        self.mtype = MType(self.get_mhdr())
        self.direction = Direction(self.mtype.get())
        self.mac_payload = MacPayload()
        self.mac_payload.create(self.mtype.get(), args)
        self.mic = None

    def length(self):
        return len(self.to_raw())

    def to_raw(self):
        phy_payload = [self.get_mhdr()]
        phy_payload += self.mac_payload.to_raw()
        phy_payload += self.get_mic()
        return phy_payload

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

    def set_direction(self):
        self.direction = Direction(self.mtype.get())

    def get_mac_payload(self):
        return self.mac_payload

    def set_mac_payload(self, mac_payload):
        self.mac_payload = mac_payload

    def get_mic(self):
        if self.mic == None:
            self.set_mic(self.compute_mic())
        return self.mic

    def set_mic(self, mic):
        self.mic = mic

    def compute_mic(self):
        return self.mac_payload.frm_payload.compute_mic(self.key, self.get_direction(), self.get_mhdr())

    def valid_mic(self):
        return self.get_mic() == self.mac_payload.frm_payload.compute_mic(self.key, self.get_direction(), self.get_mhdr())

    def get_payload(self):
        return self.mac_payload.frm_payload.decrypt_payload(self.key, self.get_direction())
