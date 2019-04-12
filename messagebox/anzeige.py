import time

from RPLCD.i2c import CharLCD

COLS = 16  # Anzahl der Stellen am Display


class Display:
    def __init__(self, lcd=None):
        if lcd is None:
            self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=COLS, rows=2, dotsize=8, charmap='A02',
                               auto_linebreaks=True, backlight_enabled=True)
        else:
            self.lcd = lcd

        self.zeile_1 = None
        self.zeile_2 = None

    def display_schreiben(self, text):
        delay = 1.3
        buffer = text_zerlegen(text)
        while buffer:
            self.lcd.clear()
            try:
                self.lcd.write_string("{zeile1}\n\r{zeile2}".format(zeile1=buffer[0], zeile2=buffer[1]))
            except IndexError:
                self.lcd.write_string("{zeile1}\n\r{zeile2}".format(zeile1=buffer[0], zeile2=""))
            time.sleep(delay)
            if len(buffer) <= 2:
                break
            buffer.pop(0)


def text_zerlegen(text):
    buffer = []
    while len(text) > COLS:
        trenner = leerzeichen_finden(text)
        if trenner is not None:
            zeile = text[:trenner]
            text = text[trenner+1:]
        else:
            zeile = text[:COLS]
            text = text[COLS:]
        buffer.append(zeile)
    if len(text) > 0:
        buffer.append(text)
    return buffer


def leerzeichen_finden(text):
        min_ = 10
        max_ = COLS
        pos = text[min_:max_].find(" ")
        if pos < 0:
            pos = None
        else:
            pos += min_
        return pos


if __name__ == "__main__":
    display = Display()
    text_ = "Testtext mit mehreren Zeilenumbruechen zum Testen der Autoscrollfunktion"
    display.display_schreiben(text_)
    time.sleep(3)
    text_ = "Zwei Zeiler Test ohne Scroll"
    display.display_schreiben(text_)
    time.sleep(3)
    text_ = "Einzeiler"
    display.display_schreiben(text_)
    time.sleep(3)
