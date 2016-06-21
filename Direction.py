class Direction:

    UP = 0x00
    DOWN = 0x01

    def __init__(self, direction):
        self.direction = direction

    def get(self):
        return self.direction

    def set(self, direction):
        self.direction = direction
