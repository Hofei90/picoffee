

class Sonderzeichen:
    def __init__(self, lcd):
        self.lcd = lcd

    def char_rechteck_rand(self):
        rechteck_rand = (
            0b11111,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b11111
        )
        self.lcd.create_char(0, rechteck_rand)
        return "\x00"

    def char_rechteck_komplett(self):
        rechteck_komplett = (
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111
        )
        self.lcd.create_char(1, rechteck_komplett)
        return "\x01"

    def char_rechteck_schraffiert(self):
        rechteck_schraffiert = (
            0b10101,
            0b01010,
            0b10101,
            0b01010,
            0b10101,
            0b01010,
            0b10101,
            0b01010
        )
        self.lcd.create_char(2, rechteck_schraffiert)
        return "\x02"
