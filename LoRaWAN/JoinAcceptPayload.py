#
# frm_payload: appnonce(3) netid(3) devaddr(4) dlsettings(1) rxdelay(1) cflist(0..16)
#
from .MalformedPacketException import MalformedPacketException
from .AES_CMAC import AES_CMAC
from Crypto.Cipher import AES

class JoinAcceptPayload:

    def read(self, payload):
        if len(payload) < 12:
            raise MalformedPacketException("Invalid join accept");
        self.encrypted_payload = payload

    def create(self, args):
        pass

    def length(self):
        return len(self.encrypted_payload)

    def to_raw(self):
        return self.encrypted_payload

    def to_clear_raw(self):
        return self.payload

    def get_appnonce(self):
        return self.appnonce

    def get_netid(self):
        return self.netid

    def get_devaddr(self):
        return list(map(int, reversed(self.devaddr)))

    def get_dlsettings(self):
        return self.dlsettings

    def get_rxdelay(self):
        return self.rxdelay

    def get_cflist(self):
        return self.cflist

    def compute_mic(self, key, direction, mhdr):
        mic = []
        mic += [mhdr.to_raw()]
        mic += self.to_clear_raw()

        cmac = AES_CMAC()
        computed_mic = cmac.encode(bytes(key), bytes(mic))[:4]
        return list(map(int, computed_mic))

    def decrypt_payload(self, key, direction, mic):
        a = []
        a += self.encrypted_payload
        a += mic

        cipher = AES.new(bytes(key))
        self.payload = cipher.encrypt(bytes(a))[:-4]

        self.appnonce = self.payload[:3]
        self.netid = self.payload[3:6]
        self.devaddr = self.payload[6:10]
        self.dlsettings = self.payload[10]
        self.rxdelay = self.payload[11]
        self.cflist = None
        if self.payload[12:]:
            self.cflist = self.payload[12:]

        return list(map(int, self.payload))

    def encrypt_payload(self, key, direction, mhdr):
        a = []
        a += self.to_clear_raw()
        a += self.compute_mic(key, direction, mhdr)

        cipher = AES.new(bytes(key))
        return list(map(int, cipher.decrypt(bytes(a))))

    def derive_nwskey(self, key, devnonce):
        a = [0x01]
        a += self.get_appnonce()
        a += self.get_netid()
        a += devnonce
        a += [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        cipher = AES.new(bytes(key))
        return list(map(int, cipher.encrypt(bytes(a))))

    def derive_appskey(self, key, devnonce):
        a = [0x02]
        a += self.get_appnonce()
        a += self.get_netid()
        a += devnonce
        a += [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        cipher = AES.new(bytes(key))
        return list(map(int, cipher.encrypt(bytes(a))))
