class Zone:
    def __init__(self, zone_id, x, y, width, height):
        self.zone_id = zone_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def center(self):
        return [
            self.x + self.width / 2,
            self.y + self.height / 2
        ]

    def contains(self, position):
        x, y = position

        return (
            self.x <= x <= self.x + self.width
            and
            self.y <= y <= self.y + self.height
        )