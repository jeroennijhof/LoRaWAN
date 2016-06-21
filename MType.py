from MalformedPacketException import MalformedPacketException

class MType:

    JOIN_REQUEST = 0x00
    JOIN_ACCEPT = 0x01
    UNCONF_DATA_UP = 0x02
    UNCONF_DATA_DOWN = 0x03
    CONF_DATA_UP = 0x04
    CONF_DATA_DOWN = 0x05
    RFU = 0x06
    PROPRIETARY = 0x07

    def __init__(self, mhdr):
        mtype = (mhdr >> 5) & 0x07
        if mtype < 0x08:
            self.mtype = mtype
        else:
            raise MalformedPacketException("Invalid mtype")
        
    def get(self):
        return self.mtype
