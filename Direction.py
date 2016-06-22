from MType import MType

class Direction:

    UP = 0x00
    DOWN = 0x01
    MTYPE = {
        MType.JOIN_REQUEST: UP,
        MType.JOIN_ACCEPT: DOWN,
        MType.UNCONF_DATA_UP: UP,
        MType.UNCONF_DATA_DOWN: DOWN,
        MType.CONF_DATA_UP: UP,
        MType.CONF_DATA_DOWN: DOWN,
        MType.RFU: UP,
        MType.PROPRIETARY: UP }

    def __init__(self, mtype):
        self.set(mtype)

    def get(self):
        return self.direction

    def set(self, mtype):
        self.direction = self.MTYPE[mtype]
