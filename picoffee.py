#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Script zur Kaffeekontrolle

import datetime
import os
import random
import shlex
import sqlite3
import subprocess
import time

import gpiozero
from RPLCD.i2c import CharLCD
from pirc522 import RFID

import Xtendgpiozero.buttonxtendgpiozero as xgpiozero
import setup_logging
import sonderzeichen

SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))
LOGGER = setup_logging.create_logger("picoffee", 10)

# GPIO Buttons
TASTERMINUS = xgpiozero.Button(12)
TASTERPLUS = xgpiozero.Button(16)
TASTERMENUE = xgpiozero.Button(20)
TASTEROK = xgpiozero.Button(21)
MAHLWERK = xgpiozero.Button(7)
WASSER = xgpiozero.Button(5)

# GPIO Output
# O_LCD_LED = 27
TASTEN_FREIGABE = gpiozero.DigitalOutputDevice(6, initial_value=False)
RGBLED = gpiozero.RGBLED(13, 26, 19, active_high=True, initial_value=(1, 0, 0))
# LED_ROT = gpiozero.LED(13)
# LED_GELB = gpiozero.LED(19)
# LED_BLAU = gpiozero.LED(26)

PIN_RST = 25
PIN_CE = 0
PIN_IRQ = 24


class Datenbank:
    def __init__(self, datenbankpfad):
        self.datenbankpfad = datenbankpfad
        self.connection = None
        self.cursor = None
        self.datenbank_initialisieren()

    def datenbank_initialisieren(self):
        self.sqlite3_verbinden()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS config(kaffeepreis FLOAT, kasse FLOAT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS benutzer(uid INTEGER, vorname TEXT, nachname TEXT, "
                            "konto FLOAT, rechte INTEGER, PRIMARY KEY (uid))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS buch(timestamp FLOAT, uid INTEGER, "
                            "betrag FLOAT, PRIMARY KEY (uid))")
        self.connection.close()

    def sqlite3_verbinden(self):
        self.connection = sqlite3.connect(self.datenbankpfad)
        self.cursor = self.connection.cursor()

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def __enter__(self):
        self.sqlite3_verbinden()
        return self


class Display:
    def __init__(self):
        self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8, charmap='A02',
                           auto_linebreaks=True, backlight_enabled=True)
        self.displayinhalt = None
        self.displayhistory = []

    def display_schreiben(self, zeile1, zeile2=None):
        self.__set_displayinhalt(zeile1, zeile2)
        zeile1 = str(zeile1)
        self.lcd.clear()
        if zeile2 is None:
            self.lcd.write_string(zeile1)
        else:
            zeile2 = str(zeile2)
            if len(zeile1) > 16 or len(zeile2) > 16:
                self.lcd.write_string(zeile1)
                time.sleep(2)
                self.lcd.clear()
                self.lcd.write_string(zeile2)
                time.sleep(2)
            else:
                self.lcd.write_string(zeile1 + "\n\r" + zeile2)

    def __set_displayinhalt(self, zeile1, zeile2):
        self.__set_displayhistory()
        self.displayinhalt = [zeile1, zeile2]

    def __set_displayhistory(self):
        self.displayhistory.append(self.displayinhalt)
        if len(self.displayhistory) > 10:
            del self.displayhistory[0]


class Account:
    def __init__(self, display, db, userdatensatz, kaffeepreis):
        self.display = display
        self.db = db
        self.uid = userdatensatz[0]
        self.vorname = userdatensatz[1]
        self.nachname = userdatensatz[2]
        self.kontostand = userdatensatz[3]
        self.rechte = userdatensatz[4]
        self.menue = None
        self.menueposition = None
        self.kaffeepreis = kaffeepreis
        check_alle_taster()
        self.__create_menue()

    def __create_menue(self):
        self.menue = [["Aufladen", self.m_aufladen],
                      ["Statistik", self.m_statistik],
                      ["Auszahlen", self.m_auszahlen],
                      ["Letzter Kaffee", self.m_lastkaffee]]
        if self.rechte == 1:
            self.menue.append(["Registrieren", self.me_registrieren])
            self.menue.append(["L\357schen", self.me_delete])  # \357=ö
            self.menue.append(["Preis anpassen", self.me_preis_anpassen])
            self.menue.append(["Kasse angleichen", self.me_kasse_korrigieren])
            self.menue.append(["Entkalken", self.me_entkalken])
            self.menue.append(["Herunterfahren", self.me_herunterfahren])

    def startseite_schreiben(self):
        self.display.display_schreiben("Konto:{:.2f}EUR".format(self.kontostand), "Platzhalter")

    def menue_enter(self):
        self.menueposition = 0
        self.display.display_schreiben(self.menue[self.menueposition][0])

    def menue_up(self):
        self.menueposition += 1
        if self.menueposition >= len(self.menue) - 1:
            self.menueposition = 0
        self.display.display_schreiben(self.menue[self.menueposition][0])

    def menue_down(self):
        self.menueposition -= 1
        if self.menueposition < 0:
            self.menueposition = len(self.menue) - 1
        self.display.display_schreiben(self.menue[self.menueposition][0])

    def m_aufladen(self):
        check_alle_taster()
        betrag = 5.0
        self.display.display_schreiben("Aufladebetrag:", "{:.2f}".format(betrag) + "EUR")
        while True:
            if TASTERPLUS.check_status():
                betrag = betrag + 0.5
                self.display.display_schreiben("Aufladebetrag:", "{:.2f}".format(betrag) + "EUR")
            if TASTERMINUS.check_status():
                betrag = betrag - 0.5
                self.display.display_schreiben("Aufladebetrag:", "{:.2f}".format(betrag) + "EUR")
            if TASTEROK.check_status():
                self.display.display_schreiben("Bitte " + "{:.2f}".format(betrag) + "EUR", "einzahlen")
                while True:
                    if TASTERMENUE.check_status():
                        self.display.display_schreiben("Abgebrochen", "")
                        return
                    if TASTEROK.check_status():
                        self.kontostand += betrag
                        self.kontostand = round(self.kontostand, 2)
                        with self.db as db_:
                            db_.cursor.execute("UPDATE benutzer SET konto = :konto WHERE uid = :uid",
                                           {"uid": self.uid, "konto": self.kontostand})

                            db_.cursor.execute("UPDATE config SET kasse = kasse + :betrag", {"betrag": betrag})
                            db_.connection.commit()
                        self.display.display_schreiben("Betrag", "aufgeladen")
                        return
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen", "")
                return

    def m_statistik(self):
        check_alle_taster()

    def m_auszahlen(self):
        check_alle_taster()
        betrag = zahlen_einstellen(self.display)
        self.display.display_schreiben("{:.2f}".format(betrag) + "EUR von", "Kasse entnehmen")
        while True:
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen")
                return
            if TASTEROK.check_status():
                with self.db as db_:
                    db_.cursor.execute("UPDATE config SET kasse = kasse - :betrag", {"betrag": betrag})
                    db_.connection.commit()
                    db_.cursor.execute("SELECT kasse FROM config")
                    datensatz = []
                    for row in db_.cursor:
                        row = list(row)
                        datensatz = datensatz + row
                    betrag = float(string_generieren(datensatz))
                self.display.display_schreiben("Abgebucht", "Kasse: " + "{:.2f}".format(betrag) + "EUR")
                return

    def m_lastkaffee(self):
        check_alle_taster()

    def me_registrieren(self):
        check_alle_taster()

    def me_delete(self):
        check_alle_taster()

    def me_preis_anpassen(self):
        check_alle_taster()

    def me_kasse_korrigieren(self):
        check_alle_taster()

    def me_entkalken(self):
        check_alle_taster()
        TASTEN_FREIGABE.on()
        self.display.display_schreiben("Taster ok, wenn", "entkalken fertig")
        while True:
            if TASTEROK.check_status():
                TASTEN_FREIGABE.off()
                self.display.display_schreiben("Entkalken", "beendet")
                time.sleep(2)
                self.go_to_startseite()
                return
            time.sleep(0.2)

    def me_herunterfahren(self):
        check_alle_taster()
        self.display.display_schreiben("System herunterfahren?")
        while True:
            if TASTERMENUE.check_status():
                return
            if TASTEROK.check_status():
                kommando = "sudo poweroff"
                cmd = shlex.split(kommando)
                subprocess.run(cmd)

    def go_to_choose_menue(self):
        self.menue[self.menueposition][1]()

    def go_to_startseite(self):
        self.menueposition = None
        if check_kaffeefreigabe(self.kaffeepreis, self.kontostand):
            setze_kaffeefreigabe()
        else:
            entferne_kaffeefreigabe()
        self.startseite_schreiben()


# RGB Farben
def led_rot():
    RGBLED.color = (1, 0, 0)


def led_gruen():
    RGBLED.color = (0, 1, 0)


def led_blau():
    RGBLED.color = (0, 0, 1)


def get_zufallszahl(max_zahl):
    random.seed()
    zahl = random.randrange(max_zahl)
    return zahl


def get_welcome():
    now = datetime.datetime.now()
    if 5 < now.hour <= 9:
        zeitbereich = 1
    elif 9 < now.hour <= 12:
        zeitbereich = 2
    elif 12 < now.hour <= 13:
        zeitbereich = 3
    elif 13 < now.hour <= 18:
        zeitbereich = 4
    elif 18 < now.hour <= 22:
        zeitbereich = 5
    else:
        zeitbereich = 6

    # auswahl immer eine Liste mit string von Begrüßungswörtern
    if zeitbereich == 1:
        auswahl = ["Hallo", "Guten Morgen", "Seas"]
    elif zeitbereich == 2:
        auswahl = ["Hallo", "Servus", "Seas"]
    elif zeitbereich == 3:
        auswahl = ["Hallo", "Mahlzeit", "Servus", "Seas"]
    elif zeitbereich == 4:
        auswahl = ["Hallo", "Guten Tag", "Servus", "Seas"]
    elif zeitbereich == 5:
        auswahl = ["Guten Abend", "Hallo", "Seas", "Servus"]
    else:
        auswahl = ["Gute Nacht"]
    anzahl = len(auswahl)
    zufallszahl = get_zufallszahl(anzahl)
    welcome = auswahl[zufallszahl]
    return welcome


def check_alle_taster():
    if TASTERMINUS.check_status():
        pass
    if TASTERPLUS.check_status():
        pass
    if TASTERMENUE.check_status():
        pass
    if TASTEROK.check_status():
        pass
    if MAHLWERK.check_status():
        pass
    if WASSER.check_status():
        pass


def rfid_read(rdr):  # util
    (error, data) = rdr.request()
    print(error, data)
    (error, uid) = rdr.anticoll()
    if error:
        uid = None
    if not error:
        string = ""
        for i in uid:
            string = string + str(i)
        return string


def user_check(db_coffee, uid):
    with db_coffee as db:
        db.cursor.execute("SELECT * FROM benutzer WHERE uid = :uid", {"uid": uid})
        user_datensatz = db.cursor.fetchone()
        return user_datensatz


def user_unbekannt(display):
    RGBLED.blink(on_time=1, off_time=1, fade_in_time=0, fade_out_time=0, on_color=(1, 0, 0), off_color=(0, 0, 1),
                 n=3, background=True)
    display.display_schreiben("Unbekannt Bitte", "registrieren")


def check_erster_start(db_coffee, display, rdr):
    """Überprüft ob schon ein Benutzer vorhanden ist, wenn nicht wird ein Service Techniker Benutzer
    erstellt"""
    with db_coffee as db:
        db.cursor.execute("SELECT * FROM benutzer")
        datensatz = list(db.cursor)
        if len(datensatz) == 0:
            display.lcd.backlight_enabled = True
            led_blau()
            display.display_schreiben("Karte vor", "Leser halten")
            uid_ = None
            while uid_ is None:
                uid_ = rfid_read(rdr)
                time.sleep(0.2)
            db.cursor.execute("INSERT INTO benutzer VALUES (:uid, 'Service', 'Techniker', 10, 1)", {"uid": uid_})
            db.connection.commit()
            display.display_schreiben("Servicebenutzer", "angelegt")
            time.sleep(3)
            display.lcd.backlight_enabled = False


def zeitdifferenz_pruefen(dauer: int, zeitpunkt: datetime):
    now = datetime.datetime.now()
    if (now - zeitpunkt).total_seconds() > dauer:
        return True
    else:
        return False


def konfiguration_laden(db_coffee):
    with db_coffee as db:
        db.cursor.execute("SELECT * FROM config")
        datensatz = list(db.cursor)[0]
        if len(datensatz) == 0:
            # Erster Start, Standardwerte schreiben
            db.cursor.execute("INSERT INTO config VALUES(0.5, 0.0)")
            db.connection.commit()
            db.cursor.execute("SELECT * FROM config")
            datensatz = list(db.cursor)[0]
        return datensatz


# Ablaufkette
def wait_for_login(db_coffee, display: Display, rdr, kasse):
    led_rot()
    while True:
        user = rfid_read(rdr)
        if user is not None:
            display.lcd.backlight_enabled = True
            user_datensatz = user_check(db_coffee, user)
            if user_datensatz is None:
                user_unbekannt(display)
            else:
                login(db_coffee, display, kasse, user_datensatz)
        if TASTERMENUE.check_status():
            display.lcd.backlight_enabled = True
            display.display_schreiben("Kaffeepreis:{:.2f}".format(kasse["kaffeepreis"]))
            time.sleep(2)
            display.lcd.clear()
            display.lcd.backlight_enabled = False
        time.sleep(0.5)


def login(db_coffee, display, kasse, user_datensatz):
    max_inaktiv = 60  # Sekunden
    tastenfreigabe = 30
    letzte_aktivzeit = datetime.datetime.now()
    display.lcd.backlight_enabled = True
    angemeldeter_user = Account(display, db_coffee, user_datensatz)
    begruessung(angemeldeter_user)
    angemeldeter_user.startseite_schreiben()
    if check_kaffeefreigabe(kasse["kaffeepreis"], angemeldeter_user.kontostand):
        zu_wenig_geld(display)
    else:
        setze_kaffeefreigabe()
    while not zeitdifferenz_pruefen(max_inaktiv, letzte_aktivzeit):
        if TASTERMENUE.check_status():
            if angemeldeter_user.menueposition is None:
                angemeldeter_user.menue_enter()
            else:
                angemeldeter_user.go_to_startseite()
            letzte_aktivzeit = datetime.datetime.now()
        if TASTERPLUS.check_status() and angemeldeter_user.menueposition is not None:
            angemeldeter_user.menue_up()
            letzte_aktivzeit = datetime.datetime.now()
        if TASTERMINUS.check_status() and angemeldeter_user.menueposition is not None:
            angemeldeter_user.menue_down()
            letzte_aktivzeit = datetime.datetime.now()
        taster_ok_merker = TASTEROK.check_status()
        if taster_ok_merker and angemeldeter_user.menueposition is not None:
            angemeldeter_user.go_to_choose_menue()
            letzte_aktivzeit = datetime.datetime.now()
        if taster_ok_merker and angemeldeter_user.menueposition is None:
            logout(angemeldeter_user)
            return
        if zeitdifferenz_pruefen(tastenfreigabe, letzte_aktivzeit):
            TASTEN_FREIGABE.off()
            led_rot()

        if WASSER.check_status():
            heisswasser_bezug(angemeldeter_user)
            letzte_aktivzeit = datetime.datetime.now()
        if MAHLWERK.check_status():
            kaffee_ausgegeben = kaffee_bezug()
            if kaffee_ausgegeben:
                kaffee_verbuchen(angemeldeter_user, db_coffee, kasse)
                logout(angemeldeter_user)
                return
            else:
                angemeldeter_user.display.display_schreiben("Kaffeebezug abgebrochen")
                letzte_aktivzeit = datetime.datetime.now()
    logout(angemeldeter_user)


def kaffee_verbuchen(angemeldeter_user, db_coffee, kasse):
    timestamp = datetime.datetime.now().timestamp()
    angemeldeter_user.kontostand -= kasse["kaffeepreis"]
    angemeldeter_user.kontostand = round(angemeldeter_user.kontostand, 2)
    with db_coffee as db:
        db.cursor.execute("UPDATE benutzer SET konto = :konto WHERE uid = :uid",
                          {"uid": angemeldeter_user.uid, "konto": angemeldeter_user.kontostand})
        db.cursor.execute("INSERT INTO buch VALUES (:timestamp, :uid, :betrag)",
                          {"timestamp": timestamp, "uid": angemeldeter_user.uid, "betrag": kasse["kaffeepreis"]})
        db.connection.commit()
    angemeldeter_user.display.display_schreiben("Neuer Stand:", "{:.2f}EUR".format(angemeldeter_user.kontostand))
    time.sleep(2)


def heisswasser_bezug(angemeldeter_user):
    angemeldeter_user.display.display_schreiben("Heißwasser", "läuft")
    max_inaktiv = 6
    letzter_aktivzeitpunkt = datetime.datetime.now()
    while True:
        if WASSER.check_status():
            letzter_aktivzeitpunkt = datetime.datetime.now()
        if zeitdifferenz_pruefen(max_inaktiv, letzter_aktivzeitpunkt):
            angemeldeter_user.go_to_startseite()
            return
        time.sleep(0.4)


def kaffee_bezug():
    max_inaktiv = 25
    letzter_aktivzeitpunkt = datetime.datetime.now()
    while MAHLWERK.is_pressed:
        letzter_aktivzeitpunkt = datetime.datetime.now()
        time.sleep(0.2)
    while not zeitdifferenz_pruefen(max_inaktiv, letzter_aktivzeitpunkt):
        if WASSER.check_status():
            return True
    return False


def begruessung(user: Account):
    begruessung_ = get_welcome()
    user.display.display_schreiben("{}".format(begruessung_), "{}".format(user.vorname))
    time.sleep(2)


def logout(angemeldeter_user):
    angemeldeter_user.display.lcd.clear()
    angemeldeter_user.display.lcd.backlight_enabled = False
    TASTEN_FREIGABE.off()
    led_rot()
    del angemeldeter_user


def check_kaffeefreigabe(kaffeepreis, kontostand):
    if kontostand >= kaffeepreis:
        return True
    else:
        return False


def setze_kaffeefreigabe():
    TASTEN_FREIGABE.on()
    led_gruen()


def entferne_kaffeefreigabe():
    TASTEN_FREIGABE.off()
    led_rot()


def zu_wenig_geld(display):
    display.display_schreiben("Bitte Geld", "aufladen")
    RGBLED.blink(on_time=1, off_time=1, fade_in_time=0, fade_out_time=0, on_color=(1, 0, 0), off_color=(1, 1, 1),
                 n=3, background=False)


# # # # #

# Zahlen per Knöpfe einstellen
def zahlen_einstellen(display):
    check_alle_taster()
    display.lcd.cursor_mode = "blink"
    wert = ["0", "0", "0", ".", "0", "0"]
    select = 0
    cursor_position = 0
    display.display_schreiben("Betrag eingeben:", "000.00 EUR")
    display.lcd.cursor_pos = (1, cursor_position)
    while True:
        if TASTERMENUE.check_status():
            time.sleep(0.2)
            if TASTEROK.check_status():
                display.lcd.cursor_mode = "hide"
                display.display_schreiben("Abgebrochen", "")
                time.sleep(2)
                return
            else:
                display.lcd.cursor_mode = "hide"
                return round(float(string_generieren(wert)), 2)

        if TASTEROK.check_status():
            if select == 0:
                display.lcd.cursor_mode = "line"
                select = 1
            elif select == 1:
                display.lcd.cursor_mode = "blink"
                select = 0

        if TASTERPLUS.check_status():
            if select == 0:
                if cursor_position == 5:
                    cursor_position = 0
                    display.lcd.cursor_pos = (1, cursor_position)
                else:
                    cursor_position = cursor_position + 1
                    if cursor_position == 3:
                        cursor_position = 4
                    display.lcd.cursor_pos = (1, cursor_position)
            if select == 1:
                float_zeichen = int(wert[cursor_position])
                if float_zeichen == 9:
                    float_zeichen = 0
                else:
                    float_zeichen = float_zeichen + 1
                wert[cursor_position] = str(float_zeichen)
                display.lcd.write_string(wert[cursor_position])
                display.lcd.cursor_pos = (1, cursor_position)

        if TASTERMINUS.check_status():
            if select == 0:
                if cursor_position == 0:
                    cursor_position = 5
                    display.lcd.cursor_pos = (1, cursor_position)
                elif cursor_position == 3:
                    cursor_position = 2
                    display.lcd.cursor_pos = (1, cursor_position)
                else:
                    cursor_position = cursor_position - 1
                    if cursor_position == 3:
                        cursor_position = 2
                    display.lcd.cursor_pos = (1, cursor_position)
            if select == 1:
                float_zeichen = int(wert[cursor_position])
                if float_zeichen == 0:
                    float_zeichen = 9
                else:
                    float_zeichen = float_zeichen - 1
                wert[cursor_position] = str(float_zeichen)
                display.lcd.write_string(wert[cursor_position])
                display.lcd.cursor_pos = (1, cursor_position)


# String aus Liste generieren
def string_generieren(liste):
    string = [str(buchstabe) for buchstabe in liste if buchstabe != ""]
    return string


def count_taster(display):
    counter = [0] * 6
    while True:
        if TASTERMINUS.check_status():
            counter[0] += 1
            display.display_schreiben("{} {} {}".format(counter[0], counter[1], counter[2]),
                                      "{} {} {}".format(counter[3], counter[4], counter[5]))
        if TASTERPLUS.check_status():
            counter[1] += 1
            display.display_schreiben("{} {} {}".format(counter[0], counter[1], counter[2]),
                                      "{} {} {}".format(counter[3], counter[4], counter[5]))
        if TASTERMENUE.check_status():
            counter[2] += 1
            display.display_schreiben("{} {} {}".format(counter[0], counter[1], counter[2]),
                                      "{} {} {}".format(counter[3], counter[4], counter[5]))
        if TASTEROK.check_status():
            counter[3] += 1
            display.display_schreiben("{} {} {}".format(counter[0], counter[1], counter[2]),
                                      "{} {} {}".format(counter[3], counter[4], counter[5]))
        if MAHLWERK.check_status():
            counter[4] += 1
            display.display_schreiben("{} {} {}".format(counter[0], counter[1], counter[2]),
                                      "{} {} {}".format(counter[3], counter[4], counter[5]))
        if WASSER.check_status():
            counter[5] += 1
            display.display_schreiben("{} {} {}".format(counter[0], counter[1], counter[2]),
                                      "{} {} {}".format(counter[3], counter[4], counter[5]))
        time.sleep(0.3)


def main():
    global RECHTECK_KOMPLETT
    global RECHTECK_RAND
    db_coffee = Datenbank(os.path.join(SKRIPTPFAD, "db_coffee.sdb"))

    display = Display()
    display.lcd.backlight_enabled = False

    char_erstellen = sonderzeichen.Sonderzeichen(display.lcd)
    RECHTECK_KOMPLETT = char_erstellen.char_rechteck_komplett()
    RECHTECK_RAND = char_erstellen.char_rechteck_rand()

    # Initialisierung RFID
    rdr = RFID(pin_rst=PIN_RST, pin_ce=PIN_CE, pin_irq=PIN_IRQ, pin_mode=11)
    util = rdr.util()
    print(util)

    check_erster_start(db_coffee, display, rdr)
    kasse = {}
    datensatz = konfiguration_laden(db_coffee)
    kasse["kaffeepreis"] = datensatz[0]
    kasse["kasse"] = datensatz[1]

    TASTERMINUS.when_pressed = TASTERMINUS.set_event
    TASTERPLUS.when_pressed = TASTERPLUS.set_event
    TASTERMENUE.when_pressed = TASTERMENUE.set_event
    TASTEROK.when_pressed = TASTEROK.set_event
    MAHLWERK.when_pressed = MAHLWERK.set_event
    WASSER.when_pressed = WASSER.set_event
    try:
        wait_for_login(db_coffee, display, rdr, kasse)
        # count_taster(display)
    finally:
        TASTERMINUS.close()
        TASTERPLUS.close()
        TASTERMENUE.close()
        TASTEROK.close()
        MAHLWERK.close()
        WASSER.close()
        TASTEN_FREIGABE.close()
        RGBLED.close()
        display.lcd.clear()
        display.lcd.backlight_enabled = False
        display.lcd.close()


if __name__ == "__main__":
    main()
