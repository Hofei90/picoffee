from RPLCD.i2c import CharLCD
import time
from pirc522 import RFID
import sys
import sqlite3


class Display:
    def __init__(self):
        self.lcd = self.init()
        self.lcd.cursor_mode = "hide"

    def init(self):
        lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
                      cols=16, rows=2, dotsize=8, charmap='A02',
                      auto_linebreaks=True, backlight_enabled=True)
        return lcd

    def display_schreiben(self, zeile1, zeile2):
        zeile1 = str(zeile1)
        zeile2 = str(zeile2)
        self.lcd.clear()
        if len(zeile1) > 16 or len(zeile2) > 16:
            self.lcd.write_string(zeile1)
            time.sleep(2)
            self.lcd.clear()
            self.lcd.write_string(zeile2)
            time.sleep(2)
        else:
            self.lcd.write_string(zeile1 + "\n\r" + zeile2)


class Datenbank:
    def __init__(self, datenbankpfad):
        self.connection = sqlite3.connect(datenbankpfad)
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self.cursor

    def __exit__(self):
        self.connection.close()


def check_rfid():
    rdr = RFID()
    util = rdr.util()
    util.debug = True
    user = rfid_read(rdr, util)
    if user != None:
        check_user(user)


def check_user(user):
    pass


def main():
    try:
        while True:
            check_rfid()
    except KeyboardInterrupt:
        print("Durch Benutzer abgebrochen")
    finally:
        sys.exit()


if __name__ == "__main__":
    main()
