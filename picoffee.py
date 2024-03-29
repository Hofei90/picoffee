#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Script zur Kaffeekontrolle

import datetime
import random
import shlex
import signal
import subprocess
import time
from pathlib import Path
from sys import exit

import gpiozero
import toml
from RPLCD.i2c import CharLCD
from pirc522 import RFID

import Xtendgpiozero.buttonxtendgpiozero as xgpiozero
import db_coffee_model as db
import mail_bei_aufladung
import messagebox.anzeige as MessageboxAnzeige
import messagebox.messagebox as messagebox
import setup_logging
import sonderzeichen


SKRIPTPFAD = Path(__file__).parent
MAILCONFIG = toml.load(SKRIPTPFAD / "mailconfig.toml")["mail"]
LOGGER = setup_logging.create_logger("picoffee", 10, SKRIPTPFAD)

db.database.initialize(db.peewee.SqliteDatabase(SKRIPTPFAD / "db_coffee.db3", **{}))

# GPIO Buttons
TASTERMINUS = xgpiozero.Button(12, pull_up=None, active_state=False)
TASTERPLUS = xgpiozero.Button(16, pull_up=None, active_state=False)
TASTERMENUE = xgpiozero.Button(20, pull_up=None, active_state=False)
TASTEROK = xgpiozero.Button(21, pull_up=None, active_state=False)
MAHLWERK = xgpiozero.Button(14, pull_up=None, active_state=False)
WASSER = xgpiozero.Button(5, pull_up=None, active_state=False)

# GPIO Output
TASTEN_FREIGABE = gpiozero.DigitalOutputDevice(6, initial_value=False)
RGBLED = gpiozero.RGBLED(13, 26, 19, active_high=True, initial_value=(1, 0, 0))

PIN_RST = 25
PIN_CE = 0
PIN_IRQ = 24


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
    def __init__(self, display, chip, kaffeepreis, rdr):
        self.display = display
        self.rdr = rdr
        self.uid = chip.uid
        self.vorname = chip.benutzer.vorname
        self.nachname = chip.benutzer.nachname
        self.kontostand = chip.benutzer.konto
        self.kaffeelimit = chip.benutzer.kaffeelimit
        self.rechte = chip.benutzer.rechte
        self.benutzer = chip.benutzer  # Peewee Objekt Model
        self.konfig_neu_laden = False
        self.menue = None
        self.menueposition = None
        self.kaffeepreis = kaffeepreis
        self.kaffeebezugszeit = None  # Debugvariable
        self.letzte_aktivzeit = datetime.datetime.now()
        check_alle_taster()
        self.__create_menue()

    def __create_menue(self):
        self.menue = [["Aufladen", self.m_aufladen],
                      ["Reinigung", self.m_reinigung],
                      ["Statistik", self.m_statistik],
                      ["Auszahlen", self.m_auszahlen],
                      ["Letzter Kaffee", self.m_lastkaffee],
                      ["Manuell buchen", self.m_kaffee_manuell_buchen],
                      ["Kaffee Limit", self.m_kaffeelimit]]
        if self.rechte == 1:
            self.menue.append(["Benutzer erstellen", self.me_benutzer_erstellen])
            self.menue.append(["Registrieren", self.me_registrieren])
            self.menue.append(["Chip L\357schen", self.me_chip_loeschen])  # \357=ö
            self.menue.append(["Benutzer L\357schen", self.me_benutzer_loeschen])
            self.menue.append(["Preis anpassen", self.me_preis_anpassen])
            self.menue.append(["Kasse angleichen", self.me_kasse_korrigieren])
            self.menue.append(["Entkalken", self.me_entkalken])
            self.menue.append(["Herunterfahren", self.me_herunterfahren])

    def startseite_schreiben(self):
        kaffee_anzeige = self.get_kaffeelimit_zustand()
        self.display.display_schreiben("Konto:{:.2f}EUR".format(self.kontostand),
                                       "{}".format(kaffee_anzeige))

    def menue_enter(self):
        entferne_kaffeefreigabe()
        self.menueposition = 0
        self.display.display_schreiben(self.menue[self.menueposition][0])

    def menue_up(self):
        self.menueposition += 1
        if self.menueposition >= len(self.menue):
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
                betrag = betrag + 5.0
                self.display.display_schreiben("Aufladebetrag:", "{:.2f}".format(betrag) + "EUR")
            if TASTERMINUS.check_status():
                betrag = betrag - 5.0
                if betrag < 5:
                    betrag = 5.0
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
                        self.benutzer.konto = self.kontostand
                        self.benutzer.save()
                        db.Config.update(kasse=db.Config.kasse + betrag).execute()
                        versende_mail(self, betrag)
                        schreiben_in_buch(self.benutzer, betrag, "aufladen")

                        self.display.display_schreiben("Betrag", "aufgeladen")
                        return
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen", "")
                return

    def m_reinigung(self):
        self.display.display_schreiben("Reinigung", "eintragen?")
        while True:
            if TASTEROK.check_status():
                schreiben_in_reinigung(self.benutzer, "reinigung")
                self.display.display_schreiben("Eingetragen!")
                time.sleep(2)
                return
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen", "")
                time.sleep(2)
                return
            time.sleep(0.2)

    def m_statistik(self):
        check_alle_taster()
        self.display.display_schreiben("Jahr <+>", "Gesamt <->")
        while True:
            if TASTERPLUS.check_status():
                timestamp = timestamp_jahr_generieren()
                anzahl, summe = get_kaffee_bezuge(timestamp)
                summe = round(summe, 2)
                self.display.display_schreiben("{} Kaffee zu".format(anzahl),
                                               "{} EUR".format(summe))
                time.sleep(4)
                break

            if TASTERMINUS.check_status():
                anzahl, summe = get_kaffee_bezuge()
                summe = round(summe, 2)
                self.display.display_schreiben("{} Kaffee zu".format(anzahl),
                                               "{} EUR".format(summe))
                time.sleep(4)
                break

    def m_auszahlen(self):
        check_alle_taster()
        betrag = zahlen_einstellen(self.display)
        self.display.display_schreiben("{:.2f}EUR von".format(betrag), "Kasse entnehmen")
        while True:
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen")
                time.sleep(2)
                return
            if TASTEROK.check_status():
                db.Config.update(kasse=db.Config.kasse - betrag).execute()
                kassenstand = db.Config.select(db.Config.kasse).scalar()
                schreiben_in_buch(self.benutzer, betrag, "auszahlen")
                self.display.display_schreiben("Abgebucht", "Kasse: {:.2f}EUR".format(kassenstand))
                time.sleep(2)
                return

    def m_lastkaffee(self):
        check_alle_taster()
        benutzer = get_letzten_kaffee_bezug()
        name = "{} {}".format(benutzer.vorname, benutzer.nachname)
        self.display.display_schreiben("Letzter Kaffee:", "{:.{widght}}".format(name, widght=16))
        time.sleep(2)

    def m_kaffee_manuell_buchen(self):
        self.display.display_schreiben("Kaffee manuell", "verbuchen?")
        while True:
            if TASTEROK.check_status():
                kaffee_verbuchen(self, {"kaffeepreis": self.kaffeepreis})
                return
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen")
                time.sleep(2)
                return

    def m_kaffeelimit(self):
        check_alle_taster()
        self.display.display_schreiben("Limit setzen:", self.kaffeelimit)
        while True:
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen")
                time.sleep(2)
                return
            if TASTEROK.check_status():
                self.benutzer.kaffeelimit = self.kaffeelimit
                self.benutzer.save()
                self.display.display_schreiben("Neues Limit:", self.kaffeelimit)
                time.sleep(2)
                break
            if TASTERPLUS.check_status():
                self.kaffeelimit += 1
                if self.kaffeelimit > 16:
                    self.kaffeelimit = 0
                self.display.display_schreiben("Limit setzen:", self.kaffeelimit)
            if TASTERMINUS.check_status():
                self.kaffeelimit -= 1
                if self.kaffeelimit < 0:
                    self.kaffeelimit = 16
                self.display.display_schreiben("Limit setzen:", self.kaffeelimit)
            time.sleep(0.1)
        return

    def me_benutzer_erstellen(self):
        check_alle_taster()
        self.display.display_schreiben("Vorname")
        self.display.lcd.cursor_mode = "blink"
        reg_name = [""] * 16
        select = 0
        cursor_position = 0
        self.display.lcd.cursor_pos = (1, cursor_position)

        unterfunktion = 0
        vorname = None

        while True:
            if TASTERMENUE.check_status():
                if unterfunktion == 0:
                    vorname = string_generieren(reg_name)
                    reg_name = [""] * 16
                    self.display.display_schreiben("Nachname", "")
                    cursor_position = 0
                    self.display.lcd.cursor_pos = (1, cursor_position)

                if unterfunktion == 1:
                    if vorname != "":
                        nachname = string_generieren(reg_name)
                        db.Benutzer.create(vorname=vorname, nachname=nachname,
                                           kaffeelimit=0, rechte=0, konto=0)
                        self.display.lcd.cursor_mode = "hide"
                        self.display.display_schreiben(vorname, nachname)
                        time.sleep(2)
                        self.display.display_schreiben("erfolgreich", "registriert")
                        break
                unterfunktion += 1

            if TASTEROK.check_status():
                if select == 0:
                    self.display.lcd.cursor_mode = "line"
                    select = 1
                elif select == 1:
                    self.display.lcd.cursor_mode = "blink"
                    select = 0

            if TASTERPLUS.check_status():
                if select == 0:
                    if cursor_position == 15:
                        cursor_position = 0
                        self.display.lcd.cursor_pos = (1, cursor_position)
                    else:
                        cursor_position = cursor_position + 1
                        self.display.lcd.cursor_pos = (1, cursor_position)
                if select == 1:
                    if reg_name[cursor_position] == "":
                        if cursor_position != 0:
                            reg_name[cursor_position] = "a"
                        else:
                            reg_name[cursor_position] = "A"
                    else:
                        ord_zeichen = ord(reg_name[cursor_position]) + 1
                        if ord_zeichen == 91:
                            ord_zeichen = 32
                        elif ord_zeichen == 33:
                            ord_zeichen = 97
                        elif ord_zeichen == 123:
                            ord_zeichen = 65
                        reg_name[cursor_position] = chr(ord_zeichen)
                    self.display.lcd.write_string(reg_name[cursor_position])
                    self.display.lcd.cursor_pos = (1, cursor_position)

            if TASTERMINUS.check_status():
                if select == 0:
                    if cursor_position == 0:
                        cursor_position = 15
                        self.display.lcd.cursor_pos = (1, cursor_position)
                    else:
                        cursor_position = cursor_position - 1
                        self.display.lcd.cursor_pos = (1, cursor_position)
                if select == 1:
                    if reg_name[cursor_position] == "":
                        if cursor_position != 0:
                            reg_name[cursor_position] = "z"
                        else:
                            reg_name[cursor_position] = "Z"
                    else:
                        ord_zeichen = ord(reg_name[cursor_position]) - 1
                        if ord_zeichen == 96:
                            ord_zeichen = 32
                        elif ord_zeichen == 31:
                            ord_zeichen = 90
                        elif ord_zeichen == 64:
                            ord_zeichen = 122
                        reg_name[cursor_position] = chr(ord_zeichen)
                    self.display.lcd.write_string(reg_name[cursor_position])
                    self.display.lcd.cursor_pos = (1, cursor_position)
            time.sleep(0.2)

    def me_registrieren(self):
        check_alle_taster()
        benutzer = benutzer_auswaehlen(self.display)
        if benutzer is None:
            return
        self.display.display_schreiben("Neuen Chip", "einlesen")
        nicht_abgebrochen = True
        while nicht_abgebrochen:
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen")
                nicht_abgebrochen = False
            user = rfid_read(self.rdr)
            if user is not None:
                user_datensatz = user_check(user)
                if user_datensatz is None:
                    uid = user
                    db.Chip.create(uid=uid, benutzer=benutzer)
                    self.display.display_schreiben("Registrierung abgeschlossen")
                    break
                else:
                    self.display.display_schreiben("Chip schon", "registriert")
                    led_rot()
                    time.sleep(2)
                    self.display.display_schreiben("Neuen Chip", "einlesen")
                    led_blau()
            time.sleep(0.2)
        time.sleep(2)

    def me_chip_loeschen(self):
        check_alle_taster()
        self.display.display_schreiben("Chip", "entfernen")
        benutzer = benutzer_auswaehlen(self.display)
        if benutzer is not None:
            self.display.display_schreiben("Auswahl:", "Chip entfernen?")
            time.sleep(2)
            self.display.display_schreiben(benutzer.vorname, benutzer.nachname)
            while True:
                if TASTEROK.check_status():
                    db.Chip.delete().where(db.Chip.benutzer == benutzer).execute()
                    self.display.display_schreiben("Chip", "entfernt")
                    time.sleep(2)
                    return

                if TASTERMENUE.check_status():
                    self.display.display_schreiben("Abgebrochen")
                    time.sleep(2)
                    return

    def me_benutzer_loeschen(self):
        check_alle_taster()
        self.display.display_schreiben("Benutzer", "entfernen")
        time.sleep(2)
        self.display.display_schreiben("Auswahl treffen", "+-ok Taster")
        TASTEROK.wait_for_press()
        benutzer = benutzer_auswaehlen(self.display)
        if benutzer is None:
            return
        check_alle_taster()
        self.display.display_schreiben("AUSWAHL:")
        TASTEROK.wait_for_press()
        check_alle_taster()
        self.display.display_schreiben(benutzer.vorname, benutzer.nachname)
        TASTEROK.wait_for_press()
        check_alle_taster()
        self.display.display_schreiben("Restguthaben:", "{:.2f}EUR".format(benutzer.konto))
        TASTEROK.wait_for_press()
        check_alle_taster()
        self.display.display_schreiben("Betrag", "auszahlen")
        TASTEROK.wait_for_press()
        check_alle_taster()
        self.display.display_schreiben("Abbrechen mit", "Men\365taster")  # \365 = ü
        check_alle_taster()
        while True:
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen", "")
                time.sleep(2)
                return
            if TASTEROK.check_status():
                unbekannter_user = get_or_create_unbekannter_user()
                db.Buch.update(benutzer=unbekannter_user).where(db.Buch.benutzer == benutzer).execute()
                db.Config.update(kasse=db.Config.kasse - benutzer.konto).execute()
                db.Reinigung.update(benutzer=unbekannter_user).where(db.Reinigung.benutzer == benutzer).execute()
                db.Chip.delete().where(db.Chip.benutzer == benutzer).execute()
                db.Benutzer.delete().where(db.Benutzer.id == benutzer.id).execute()
                self.display.display_schreiben("Benutzer", "gel\357scht")
                time.sleep(2)
                return
            time.sleep(0.2)

    def me_preis_anpassen(self):
        check_alle_taster()
        self.display.display_schreiben("Preis:", "{:.2f}".format(self.kaffeepreis) + "EUR")
        while True:
            if TASTERMINUS.check_status():
                if self.kaffeepreis <= 0.00:
                    pass
                else:
                    self.kaffeepreis -= 0.05
                    self.kaffeepreis = round(self.kaffeepreis, 2)
                    self.display.display_schreiben("Preis:", "{:.2f}".format(self.kaffeepreis) + "EUR")

            if TASTERPLUS.check_status():
                if self.kaffeepreis >= 1.00:
                    pass
                else:
                    self.kaffeepreis = self.kaffeepreis + 0.05
                    self.kaffeepreis = round(self.kaffeepreis, 2)
                    self.display.display_schreiben("Preis:", "{:.2f}".format(self.kaffeepreis) + "EUR")

            if TASTEROK.check_status():
                db.Config.update(kaffeepreis=self.kaffeepreis).execute()
                self.konfig_neu_laden = True
                return

            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen")
                return

    def me_kasse_korrigieren(self):
        """
        Differenzbetrag = Hardwarekasse - Softwarekasse
        Bsp: 15 - 14 = 1 (Differenzbetrag)
        Somit +1 EUR erforderlich damit Software mit Hardware Kasse übereinstimmt
        :return:
        """
        check_alle_taster()
        self.display.display_schreiben("Differenzbetrag", "eingeben")
        time.sleep(2)
        betrag = zahlen_einstellen(self.display)
        self.display.display_schreiben("S-K verringern -", "S-K erh\357hen +")
        while True:
            if TASTERMENUE.check_status():
                self.display.display_schreiben("Abgebrochen")
                time.sleep(2)
                return
            if TASTERPLUS.check_status():
                buch_typ = "korrektur_plus"
                break
            if TASTERMINUS.check_status():
                betrag *= -1
                buch_typ = "korrektur_minus"
                break
            time.sleep(0.1)
        db.Config.update(kasse=db.Config.kasse + betrag).execute()
        schreiben_in_buch(self.benutzer, abs(betrag), buch_typ)
        datensatz = konfiguration_laden()
        kasse = datensatz[1]
        self.display.display_schreiben("Verbucht", "Kasse: {:.2f}EUR".format(kasse))
        time.sleep(2)
        return

    def me_entkalken(self):
        check_alle_taster()
        TASTEN_FREIGABE.on()
        RGBLED.blink(on_time=0.5, off_time=0.5, fade_in_time=0, fade_out_time=0, on_color=(1, 0.6, 0),
                     off_color=(0, 0, 0), background=True)
        self.display.display_schreiben("Taster ok, wenn", "entkalken fertig")
        while True:
            if TASTEROK.check_status():
                TASTEN_FREIGABE.off()
                self.display.display_schreiben("Entkalken", "beendet")
                time.sleep(2)
                break
            time.sleep(0.2)
        RGBLED.off()
        led_rot()
        self.display.display_schreiben("Wer entkalkte?", "Chip anhalten")
        while True:
            user = rfid_read(self.rdr)
            if user is not None:
                schreiben_in_reinigung(user, "entkalken")
                self.display.display_schreiben("Eingetragen!")
                time.sleep(2)
                break
        check_alle_taster()

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
        self.go_to_startseite()

    def go_to_startseite(self):
        self.menueposition = None
        if check_kaffeefreigabe(self.kaffeepreis, self.kontostand):
            setze_kaffeefreigabe()
        else:
            entferne_kaffeefreigabe()
        self.startseite_schreiben()
        self.letzte_aktivzeit = datetime.datetime.now()

    def get_kaffeelimit_zustand(self):
        timestamp = timestamp_heute_generieren()
        anzahl_kaffee_heute = get_kaffee_bezuge_eigen(self.benutzer, timestamp)[0]
        offene_kaffee = self.kaffeelimit - anzahl_kaffee_heute
        if offene_kaffee == 0:
            anzeige = "{}".format(RECHTECK_KOMPLETT * anzahl_kaffee_heute)
        elif offene_kaffee > 0:
            anzeige = "{getrunken}{offen}".format(getrunken=RECHTECK_KOMPLETT * anzahl_kaffee_heute,
                                                  offen=RECHTECK_RAND * offene_kaffee)
        else:
            zuviel_kaffee = offene_kaffee * -1

            anzeige = "{getrunken}{getrunken_zuviel}".format(getrunken=RECHTECK_KOMPLETT * self.kaffeelimit,
                                                             getrunken_zuviel=RECHTECK_SCHRAFFIERT * zuviel_kaffee)
        return anzeige


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
    if 4 < now.hour <= 9:
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


def benutzer_auswaehlen(display):
    abfrage = [query for query in db.Benutzer.select().order_by(db.Benutzer.nachname.desc())]
    index = 0
    neuer_text = True
    check_alle_taster()
    while True:
        if neuer_text:
            display.display_schreiben(abfrage[index].vorname, abfrage[index].nachname)
            neuer_text = False

        if TASTERPLUS.check_status():
            index += 1
            if index >= len(abfrage):
                index = 0
            neuer_text = True

        if TASTERMINUS.check_status():
            index -= 1
            if index < 0:
                index = len(abfrage) - 1
            neuer_text = True

        if TASTEROK.check_status():
            benutzer = abfrage[index]
            return benutzer

        if TASTERMENUE.check_status():
            display.display_schreiben("Abgebrochen")
            time.sleep(2)
            return
        time.sleep(0.2)


def rfid_read(rdr):  # util
    (_, _) = rdr.request()
    (error, uid) = rdr.anticoll()
    if error:
        uid = None
    if not error:
        string = ""
        for i in uid:
            string = string + str(i)
        return string


def user_check(uid):
    return db.Chip.get_or_none(db.Chip.uid == uid)


def user_unbekannt(display):
    display.display_schreiben("Unbekannt Bitte", "registrieren")
    RGBLED.blink(on_time=1, off_time=1, fade_in_time=0, fade_out_time=0, on_color=(1, 0, 0), off_color=(0, 0, 1),
                 n=3, background=False)
    display.lcd.clear()
    display.lcd.backlight_enabled = False
    led_rot()


def get_or_create_unbekannter_user():
    unbekannter_user, _ = db.Benutzer.get_or_create(vorname="unbekannter",
                                                    nachname="user")
    unbekannter_user.konto = 0
    unbekannter_user.kaffeelimit = 0
    unbekannter_user.rechte = 0
    unbekannter_user.save()
    return unbekannter_user


def check_erster_start(display, rdr):
    """Überprüft ob schon ein Benutzer vorhanden ist, wenn nicht wird ein Service Techniker Benutzer
    erstellt"""
    abfrage = [benutzer for benutzer in db.Benutzer.select().tuples()]
    if not abfrage:
        display.lcd.backlight_enabled = True
        led_blau()
        display.display_schreiben("Karte vor", "Leser halten")
        uid_ = None
        while uid_ is None:
            uid_ = rfid_read(rdr)
            time.sleep(0.2)
        benutzer = db.Benutzer.create(vorname="Service", nachname="Techniker", konto=10, kaffeelimit=0, rechte=1)
        db.Chip.create(uid=uid_, benutzer=benutzer)
        display.display_schreiben("Servicebenutzer", "angelegt")
        time.sleep(3)
        display.lcd.backlight_enabled = False


def zeitdifferenz_pruefen(dauer: int, zeitpunkt: datetime):
    now = datetime.datetime.now()
    if (now - zeitpunkt).total_seconds() > dauer:
        return True
    else:
        return False


def konfiguration_laden():
    config, _ = db.Config.get_or_create(defaults={"kaffeepreis": 0.5, "kasse": 0})
    kaffeepreis = config.kaffeepreis
    kasse = config.kasse
    return kaffeepreis, kasse


def wait_for_login(display: Display, rdr, kasse):
    led_rot()
    while True:
        user = rfid_read(rdr)
        if user is not None:
            display.lcd.backlight_enabled = True
            chip = user_check(user)
            if chip is None:
                LOGGER.info("Unbekannter Chip: {}".format(user))
                user_unbekannt(display)
            else:
                login(display, kasse, chip, rdr)
        if TASTERMENUE.check_status():
            display.lcd.backlight_enabled = True
            display.display_schreiben("Kaffeepreis:", "{:.2f}EUR".format(kasse["kaffeepreis"]))
            time.sleep(2)
            display.lcd.clear()
            display.lcd.backlight_enabled = False
        time.sleep(0.5)


def messagebox_abrufen(angemeldeter_user, display):
    messagebox.check_user(angemeldeter_user.uid, "{} {}".format(angemeldeter_user.vorname, angemeldeter_user.nachname))
    neue_nachrichten = messagebox.get_new_message(angemeldeter_user.uid)
    if neue_nachrichten:
        anzeige_messagebox = MessageboxAnzeige.Display(lcd=display.lcd)
        led_blau()
        for neue_nachricht in neue_nachrichten:
            quittiert = False
            while not quittiert:
                anzeige_messagebox.display_schreiben(neue_nachricht.text)
                anzeige_messagebox.display_schreiben("-"*16)
                time.sleep(1.5)
                if TASTEROK.check_status():
                    quittiert = True
            messagebox.set_read_message(angemeldeter_user.uid, neue_nachricht.id)


def login(display, kasse, chip, rdr):
    display.lcd.backlight_enabled = True
    angemeldeter_user = Account(display, chip, kasse["kaffeepreis"], rdr)
    begruessung(angemeldeter_user)
    messagebox_abrufen(angemeldeter_user, display)

    max_inaktiv = 60  # Sekunden
    tastenfreigabe = 30
    if check_kaffeefreigabe(kasse["kaffeepreis"], angemeldeter_user.kontostand):
        setze_kaffeefreigabe()
        zeile1, zeile2 = get_letzter_kaffee_bei_anmeldung()
        angemeldeter_user.display.display_schreiben(zeile1, zeile2)
        time.sleep(2)
        angemeldeter_user.startseite_schreiben()
    else:
        zu_wenig_geld(display)
        angemeldeter_user.startseite_schreiben()
    while not zeitdifferenz_pruefen(max_inaktiv, angemeldeter_user.letzte_aktivzeit):
        if TASTERMENUE.check_status():
            if angemeldeter_user.menueposition is None:
                angemeldeter_user.menue_enter()
            else:
                angemeldeter_user.go_to_startseite()
            angemeldeter_user.letzte_aktivzeit = datetime.datetime.now()
        if TASTERPLUS.check_status() and angemeldeter_user.menueposition is not None:
            angemeldeter_user.menue_up()
            angemeldeter_user.letzte_aktivzeit = datetime.datetime.now()
        if TASTERMINUS.check_status() and angemeldeter_user.menueposition is not None:
            angemeldeter_user.menue_down()
            angemeldeter_user.letzte_aktivzeit = datetime.datetime.now()
        taster_ok_merker = TASTEROK.check_status()
        if taster_ok_merker and angemeldeter_user.menueposition is not None:
            angemeldeter_user.go_to_choose_menue()
            angemeldeter_user.letzte_aktivzeit = datetime.datetime.now()
            taster_ok_merker = False
        if taster_ok_merker and angemeldeter_user.menueposition is None:
            logout(angemeldeter_user)
            return
        if zeitdifferenz_pruefen(tastenfreigabe, angemeldeter_user.letzte_aktivzeit):
            TASTEN_FREIGABE.off()
            led_rot()

        if WASSER.check_status():
            heisswasser_bezug(angemeldeter_user)
            angemeldeter_user.letzte_aktivzeit = datetime.datetime.now()
        if MAHLWERK.check_status():
            kaffee_ausgegeben = kaffee_bezug(angemeldeter_user)
            if kaffee_ausgegeben:
                if not angemeldeter_user.rechte == 1:
                    kaffee_verbuchen(angemeldeter_user, kasse)
                    LOGGER.info("Kaffee verbucht")
                else:
                    angemeldeter_user.display.display_schreiben("Gratis", "Kaffee")
                    LOGGER.info("Gratis Kaffee")
                logout(angemeldeter_user)
                return
            else:
                LOGGER.info("Kaffeebezug abgebrochen, UID:{}".format(angemeldeter_user.uid))
                angemeldeter_user.display.display_schreiben("Kaffeebezug abgebrochen")
                time.sleep(2)
                angemeldeter_user.letzte_aktivzeit = datetime.datetime.now()
                angemeldeter_user.go_to_startseite()

        if angemeldeter_user.konfig_neu_laden:
            datensatz = konfiguration_laden()
            kasse["kaffeepreis"] = datensatz[0]
            kasse["kasse"] = datensatz[1]
            angemeldeter_user.konfig_neu_laden = False
    logout(angemeldeter_user)


def kaffee_verbuchen(angemeldeter_user, kasse):
    angemeldeter_user.kontostand -= kasse["kaffeepreis"]
    angemeldeter_user.kontostand = round(angemeldeter_user.kontostand, 2)
    db.Benutzer.update(konto=angemeldeter_user.kontostand).where(db.Benutzer.id == angemeldeter_user.benutzer).execute()
    schreiben_in_buch(angemeldeter_user.benutzer, kasse["kaffeepreis"], "kaffee")
    angemeldeter_user.display.display_schreiben("Neuer Stand:", "{:.2f}EUR".format(angemeldeter_user.kontostand))
    time.sleep(2)


def schreiben_in_buch(benutzer, betrag, typ):
    timestamp = datetime.datetime.now().timestamp()
    db.Buch.create(timestamp=timestamp, benutzer=benutzer, betrag=betrag, typ=typ)


def schreiben_in_reinigung(benutzer, typ):
    timestamp = datetime.datetime.now().timestamp()
    db.Reinigung.create(timestamp=timestamp, benutzer=benutzer, typ=typ)


def heisswasser_bezug(angemeldeter_user):
    angemeldeter_user.display.display_schreiben("Hei\342wasser",
                                                "l\341uft")  # \341= ä \342 = ß
    max_inaktiv = 6
    letzter_aktivzeitpunkt = datetime.datetime.now()
    while True:
        if WASSER.check_status():
            letzter_aktivzeitpunkt = datetime.datetime.now()
        if zeitdifferenz_pruefen(max_inaktiv, letzter_aktivzeitpunkt):
            angemeldeter_user.go_to_startseite()
            return
        time.sleep(0.4)


def kaffee_bezug(angemeldeter_user):
    max_inaktiv = 40
    letzter_aktivzeitpunkt = datetime.datetime.now()
    angemeldeter_user.display.display_schreiben("Mahlwerk aktiv", "Warte auf Wasser")
    while not zeitdifferenz_pruefen(max_inaktiv, letzter_aktivzeitpunkt):
        if MAHLWERK.check_status() or MAHLWERK.is_pressed:
            letzter_aktivzeitpunkt = datetime.datetime.now()
        if WASSER.check_status():
            bezugszeit = (datetime.datetime.now() - letzter_aktivzeitpunkt).total_seconds()
            LOGGER.info("Kaffeebezugszeit: {}s".format(bezugszeit))
            return True
        time.sleep(0.2)
    bezugszeit = (datetime.datetime.now() - letzter_aktivzeitpunkt).total_seconds()
    LOGGER.info("!!!Kaffeebezugszeit: {}s".format(bezugszeit))
    angemeldeter_user.display.display_schreiben("Kein Kaffee", "verbucht?!")
    RGBLED.blink(on_time=0.5, off_time=0.5, fade_in_time=0, fade_out_time=0, on_color=(1, 0, 0), off_color=(0, 0, 1),
                 n=6, background=False)
    return False


def versende_mail(account, aufladebetrag):
    mail_bei_aufladung.email_versenden(
        f"{account.vorname} {account.nachname} hat {aufladebetrag:.2f}€ aufgeladen.",
        MAILCONFIG)


def begruessung(user: Account):
    begruessung_ = get_welcome()
    user.display.display_schreiben("{}".format(begruessung_), "{}".format(user.vorname))
    time.sleep(1.5)


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
    RGBLED.blink(on_time=0.5, off_time=0.5, fade_in_time=0, fade_out_time=0, on_color=(1, 0, 0), off_color=(1, 1, 1),
                 n=3, background=False)
    led_rot()


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


def get_kaffee_bezuge(timestamp=0.0):
    abfrage = db.Buch.select(db.fn.sum(db.Buch.betrag)).where((db.Buch.timestamp >= timestamp)
                                                              & (db.Buch.typ == "kaffee"))
    anzahl = abfrage.count()
    summe = abfrage.scalar()
    return anzahl, summe


def get_kaffee_bezuge_eigen(benutzer, timestamp=0.0):
    abfrage = db.Buch.select(db.fn.sum(db.Buch.betrag)).where((db.Buch.timestamp >= timestamp)
                                                              & (db.Buch.typ == "kaffee") & (
                                                                          db.Buch.benutzer == benutzer))
    anzahl = abfrage.count()
    summe = abfrage.scalar()
    return anzahl, summe


def get_letzten_kaffee_bezug():
    """
    :return:
    """
    query = db.Buch.select().where(db.Buch.typ == "kaffee").order_by(db.Buch.timestamp.desc()) \
        .limit(1).execute()[0]
    return query.benutzer


def get_letzter_kaffee_bei_anmeldung():
    benutzer = get_letzten_kaffee_bezug()
    name = "{} {}".format(benutzer.vorname, benutzer.nachname)
    name = "{:.{widght}}".format(name, widght=16)
    return "Letzter Kaffee:", name


# String aus Liste generieren
def string_generieren(liste):
    string_liste = [str(buchstabe) for buchstabe in liste if buchstabe != ""]
    string = "".join(string_liste)
    return string


def count_taster(display, beleuchtung):
    counter = [0] * 6
    display.lcd.backlight_enabled = beleuchtung
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


def timestamp_heute_generieren():
    now = datetime.datetime.now()
    heute = now.replace(hour=0, minute=0, second=0, microsecond=0)
    timestamp_heute = heute.timestamp()
    return timestamp_heute


def timestamp_jahr_generieren():
    now = datetime.datetime.now()
    jahr = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    timestamp_jahr = jahr.timestamp()
    return timestamp_jahr


def anzeige_test(display):
    display.lcd.backlight_enabled = True
    a = RECHTECK_KOMPLETT * 0
    b = RECHTECK_RAND * 6
    display.display_schreiben("{}{}".format(a, b))
    TASTEROK.wait_for_press()
    a = RECHTECK_KOMPLETT * 1
    b = RECHTECK_RAND * 5
    display.display_schreiben("{}{}".format(a, b))
    TASTEROK.wait_for_press()
    a = RECHTECK_KOMPLETT * 6
    b = RECHTECK_RAND * 0
    display.display_schreiben("{}{}".format(a, b))


def skript_beenden(display):
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


def skript_beenden_signal_handler(_, __):
    exit("SIGTERM wurde gesendet")


def main():
    global RECHTECK_KOMPLETT
    global RECHTECK_RAND
    global RECHTECK_SCHRAFFIERT

    display = Display()
    display.lcd.backlight_enabled = False

    signal.signal(signal.SIGTERM, skript_beenden_signal_handler)

    char_erstellen = sonderzeichen.Sonderzeichen(display.lcd)
    RECHTECK_KOMPLETT = char_erstellen.char_rechteck_komplett()
    RECHTECK_RAND = char_erstellen.char_rechteck_rand()
    RECHTECK_SCHRAFFIERT = char_erstellen.char_rechteck_schraffiert()

    # Initialisierung RFID
    rdr = RFID(pin_rst=PIN_RST, pin_ce=PIN_CE, pin_irq=PIN_IRQ, pin_mode=11)
    # util = rdr.util()

    check_erster_start(display, rdr)
    datensatz = konfiguration_laden()
    kasse = {"kaffeepreis": datensatz[0], "kasse": datensatz[1]}

    TASTERMINUS.when_pressed = TASTERMINUS.when_pressed_
    TASTERPLUS.when_pressed = TASTERPLUS.when_pressed_
    TASTERMENUE.when_pressed = TASTERMENUE.when_pressed_
    TASTEROK.when_pressed = TASTEROK.when_pressed_
    MAHLWERK.when_pressed = MAHLWERK.when_pressed_
    WASSER.when_pressed = WASSER.when_pressed_

    TASTERMINUS.when_released = TASTERMINUS.when_released_
    TASTERPLUS.when_released = TASTERPLUS.when_released_
    TASTERMENUE.when_released = TASTERMENUE.when_released_
    TASTEROK.when_released = TASTEROK.when_released_
    MAHLWERK.when_released = MAHLWERK.when_released_
    WASSER.when_released = WASSER.when_released_

    LOGGER.debug("Initialisierung abgeschlossen")
    try:
        wait_for_login(display, rdr, kasse)
        # count_taster(display, True)
    finally:
        skript_beenden(display)


if __name__ == "__main__":
    try:
        main()
    finally:
        LOGGER.exception("Schwerwiegender Fehler aufgetreten")
