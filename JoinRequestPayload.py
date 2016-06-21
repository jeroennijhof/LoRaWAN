#
# frm_payload: appeui(8) deveui(8) devnonce(2)
#
class JoinRequestPayload:

    def __init__(self, payload):
        if len(payload) != 18:
            raise MalformedPacketException("Invalid join request");
        self.appeui = payload[:8]
        self.deveui = payload[8:16]
        self.devnonce = payload[16:18]

    def length(self):
        return 18

    def to_raw(self):
        payload = []
        payload += self.appeui
        payload += self.deveui
        payload += self.devnonce
        return payload

    def get_appeui(self):
        return self.appeui

    def get_deveui(self):
        return self.deveui

    def get_devnonce(self):
        return self.devnonce

    def compute_mic(self, key, direction, mhdr):
        mic = [mhdr]
        mic += self.to_raw()

        cmac = AES_CMAC()
        return cmac.encode(str(bytearray(key)), str(bytearray(mic)))[:4]

    def decrypt_payload(self, key, direction):
        return self.to_raw()
