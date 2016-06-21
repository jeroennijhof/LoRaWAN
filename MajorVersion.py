from MalformedPacketException import MalformedPacketException

class MajorVersion:

    LORAWAN_R_1 = 0x00;

    def __init__(self, mhdr):
        mversion = mhdr & 0x03
        if mversion == self.LORAWAN_R_1:
            self.mversion = mversion
        else:
            raise MalformedPacketException("Invalid major version")
        
    def get(self):
        return self.mversion
