#!/usr/bin/python3
#Script zur Kaffeekontrolle
#Update

#Import
import sqlite3
import time
import RPi.GPIO as GPIO
from RPLCD import CharLCD, BacklightMode, cleared, cursor, CursorMode
from pirc522 import RFID
import sys 
import os

#Datenbankverbindung
def sqlite3_verbinden():
    global connection
    global cursor
    connection = sqlite3.connect("/home/pi/kaffee.sqlite")
    cursor = connection.cursor()

#Display Initialisierung
lcd = CharLCD(pin_rs=7, pin_e=11, pins_data=[12, 15, 16, 18], 
              numbering_mode=GPIO.BOARD,
              cols=16, rows=2, dotsize=8,
              auto_linebreaks=True,
              pin_backlight=None, backlight_enabled=True,
              backlight_mode=BacklightMode.active_low)
lcd.close(clear=True)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
lcd.cursor_mode = CursorMode.hide

#INIT
#GPIO.setmode(GPIO.BOARD)
i_tasterminus = 32  #Input
i_tasterplus = 36
i_tastermenue = 38
i_tasterok = 40
i_mahlwerk = 26
i_wasser = 29
GPIO.setup(i_tasterminus, GPIO.IN)
GPIO.setup(i_tasterplus, GPIO.IN)
GPIO.setup(i_tastermenue, GPIO.IN)
GPIO.setup(i_tasterok, GPIO.IN)
GPIO.setup(i_mahlwerk, GPIO.IN)
GPIO.setup(i_wasser, GPIO.IN)

#Output
o_lcd_led = 13
o_freigabe = 31
o_led_r = 33
o_led_g = 35
o_led_b = 37

GPIO.setup(o_lcd_led, GPIO.OUT)
GPIO.setup(o_freigabe, GPIO.OUT)
GPIO.setup(o_led_r, GPIO.OUT)
GPIO.setup(o_led_g, GPIO.OUT)
GPIO.setup(o_led_b, GPIO.OUT)

GPIO.output(o_lcd_led, 0)



# # Datenbank Initialisieren # #
#connection = sqlite3.connect("/home/pi/lernumgebung/Projekte/Kaffeemaschine/kaffee.sqlite")
#cursor = connection.cursor()
sqlite3_verbinden()
cursor.execute("CREATE TABLE IF NOT EXISTS config(kaffeepreis FLOAT, kasse FLOAT)")
cursor.execute("CREATE TABLE IF NOT EXISTS benutzer(uid INTEGER, vorname TEXT, nachname TEXT, konto FLOAT, rechte INTEGER, PRIMARY KEY (uid))")
cursor.execute("CREATE TABLE IF NOT EXISTS buch(datum TEXT, vorname TEXT, nachname TEXT, betrag FLOAT)")
cursor.execute("CREATE TABLE IF NOT EXISTS log(timestamp FLOAT, uid TEXT, logwert INTEGER, kaffeepreis FLOAT, unbekannt INTEGER)")

# # RFID Initialisieren # #
rdr = RFID()
util = rdr.util()
util.debug = True

# # Funktionen # #

#Display aktualisieren
def display_schreiben(zeile1, zeile2 = ""):
    zeile1 = str(zeile1)
    zeile2 = str(zeile2)
    lcd.clear()
    if len(zeile1) > 16 or len(zeile2) > 16:
        lcd.write_string(zeile1)
        time.sleep(2)
        lcd.clear()
        lcd.write_string(zeile2)
        time.sleep(2)
    else:
        lcd.write_string(zeile1+"\n\r"+zeile2)

#String aus Liste generieren
def string_generieren(liste):
    anzahl = liste.count("")
    print(anzahl)
    print(liste)
    for i in range(0, anzahl):
        liste.remove("")
        i +=1
    string = ""
    for buchstabe in liste:
        string = string + str(buchstabe)
    return string

#Zahlen per Knöpfe einstellen
def zahlen_einstellen():
    clear_event()
    lcd.cursor_mode = CursorMode.blink
    wert = ["0", "0", "0", ".", "0", "0"] 
    select = 0
    cursor_position = 0
    float_zeichen = 0
    maxlen = 6
    display_schreiben("Betrag eingeben:", "000.00 EUR")
    lcd.cursor_pos = (1, cursor_position)
    while True:
        if GPIO.event_detected(i_tastermenue):
            time.sleep(0.2)
            if GPIO.event_detected(i_tasterok):
                lcd.cursor_mode = CursorMode.hide
                display_schreiben("Abgebrochen", "")
                time.sleep(2)
                return
            else:
                lcd.cursor_mode = CursorMode.hide
                return float(string_generieren(wert))
        
        if GPIO.event_detected(i_tasterok):
            if select == 0:
                lcd.cursor_mode = CursorMode.line
                select = 1
            elif select == 1:
                lcd.cursor_mode = CursorMode.blink
                select = 0
                
        if GPIO.event_detected(i_tasterplus):
            if select == 0:
                if cursor_position == 5:
                    cursor_position = 0
                    lcd.cursor_pos = (1, cursor_position)
                else:
                    cursor_position = cursor_position + 1
                    if cursor_position == 3:
                        cursor_position = 4
                    lcd.cursor_pos = (1, cursor_position)
            if select == 1:
                float_zeichen = int(wert[cursor_position])
                if float_zeichen == 9:
                    float_zeichen = 0
                else:
                    float_zeichen = float_zeichen + 1
                wert[cursor_position] = str(float_zeichen)    
                lcd.write_string(wert[cursor_position])
                lcd.cursor_pos = (1, cursor_position)
                
        if GPIO.event_detected(i_tasterminus):
            if select == 0:
                if cursor_position == 0:
                    cursor_position = 5
                    lcd.cursor_pos = (1, cursor_position)
                elif cursor_position == 3:
                    cursor_position = 2
                    lcd.cursor_pos = (1, cursor_position)
                else:
                    cursor_position = cursor_position - 1
                    if cursor_position == 3:
                        cursor_position = 2                    
                    lcd.cursor_pos = (1, cursor_position)
            if select == 1:
                float_zeichen = int(wert[cursor_position])
                if float_zeichen == 0:
                    float_zeichen = 9
                else:
                    float_zeichen = float_zeichen - 1
                wert[cursor_position] = str(float_zeichen)    
                lcd.write_string(wert[cursor_position])
                lcd.cursor_pos = (1, cursor_position)


#Eingänge Events leeren
def clear_event():
    if GPIO.event_detected(i_mahlwerk): pass
    if GPIO.event_detected(i_tastermenue): pass
    if GPIO.event_detected(i_tasterminus): pass
    if GPIO.event_detected(i_tasterok): pass
    if GPIO.event_detected(i_tasterplus): pass
    if GPIO.event_detected(i_wasser):pass

#Benutzer registrierung
def me_register():
    logbit[5] = 1
    clear_event()
    display_schreiben("Neuen Chip", "einlesen")
    while True:
        if GPIO.event_detected(i_tastermenue):
            display_schreiben("Abgebrochen")
            logbit[5] = 2
            return        
        user = rfid_read(rdr, util)
        if user != None:
            user_datensatz = user_check(user)
            if user_datensatz == None:
                uid = user
                break
            else:
                display_schreiben("Chip schon", "registriert")
                led_rot()
                time.sleep(2)
                display_schreiben("Neuen Chip", "einlesen")
                led_blau()
                user = None
                continue
    display_schreiben("Vorname")
    lcd.cursor_mode = CursorMode.blink
    reg_name = [""] * 16
    select = 0
    cursor_position = 0
    ord_zeichen = 0
    maxlen = 16
    unterfunktion = 0
    while True:
        if GPIO.event_detected(i_tastermenue):
            time.sleep(0.2)
            if GPIO.event_detected(i_tasterok):
                lcd.cursor_mode = CursorMode.hide
                display_schreiben("Abgebrochen", "")
                time.sleep(2)
                return
            if unterfunktion == 0:
                vorname = string_generieren(reg_name)
                reg_name = [""] * 16
                display_schreiben("Nachname", "")
                cursor_position = 0
                lcd.cursor_pos = (1, cursor_position)
            
            if unterfunktion == 1:
                nachname = string_generieren(reg_name)
                cursor.execute("INSERT INTO benutzer VALUES (:uid, :vorname, :nachname, 0, 0)",{"uid" : uid, "vorname" : vorname, "nachname" : nachname})
                connection.commit()
                display_schreiben(vorname, nachname)
                time.sleep(2)
                display_schreiben("erfolgreich", "registriert")
                lcd.cursor_mode = CursorMode.hide
                logbit[5] = 2
                return
            unterfunktion += 1
                
        
        if GPIO.event_detected(i_tasterok):
            if select == 0:
                lcd.cursor_mode = CursorMode.line
                select = 1
            elif select == 1:
                lcd.cursor_mode = CursorMode.blink
                select = 0
                
        if GPIO.event_detected(i_tasterplus):
            if select == 0:
                if cursor_position == 15:
                    cursor_position = 0
                    lcd.cursor_pos = (1, cursor_position)
                else:
                    cursor_position = cursor_position + 1
                    lcd.cursor_pos = (1, cursor_position)
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
                lcd.write_string(reg_name[cursor_position])
                lcd.cursor_pos = (1, cursor_position)
                
        if GPIO.event_detected(i_tasterminus):
            if select == 0:
                if cursor_position == 0:
                    cursor_position = 15
                    lcd.cursor_pos = (1, cursor_position)
                else:
                    cursor_position = cursor_position - 1
                    lcd.cursor_pos = (1, cursor_position)
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
                lcd.write_string(reg_name[cursor_position])
                lcd.cursor_pos = (1, cursor_position)        

#Benutzer löschen
def me_delete():
    logbit[6] = 1
    clear_event()
    display_schreiben("Chip zum", "l\357schen einlesen") #\357 = ö
    while True:
        if GPIO.event_detected(i_tastermenue):
            display_schreiben("Abgebrochen", "")
            logbit[6] = 2
            return
        user = rfid_read(rdr, util)
        if user != None:
            user_datensatz = user_check(user)
            if user_datensatz == None:  
                display_schreiben("Chip", "unbekannt")
                logbit[6] = 2
                return
            else:
                tmp, vorname, name, konto, rechte = user_datensatz
                if rechte == 1:
                    display_schreiben("root kann sich", "nicht l\357schen")
                    logbit[6] = 2
                    return
                clear_event()
                display_schreiben("weiter mit ok", "Chip geh\357rt")
                while True:
                    if GPIO.event_detected(i_tastermenue):
                        display_schreiben("Abgebrochen", "")
                        logbit[6] = 2
                        return       
                    if GPIO.event_detected(i_tasterok):
                        display_schreiben(vorname, name)
                        while True:
                            if GPIO.event_detected(i_tastermenue):
                                display_schreiben("Abgebrochen", "")
                                logbit[6] = 2
                                return                            
                            if GPIO.event_detected(i_tasterok):
                                display_schreiben("Restguthaben:", "{:.2f}".format(konto) + "EUR")
                                while True:
                                    if GPIO.event_detected(i_tastermenue):
                                        display_schreiben("Abgebrochen", "")
                                        logbit[6] = 2
                                        return                                    
                                    if GPIO.event_detected(i_tasterok):
                                        display_schreiben("Betrag", "ausbezahlen")
                                        while True:
                                            if GPIO.event_detected(i_tastermenue):
                                                display_schreiben("Abgebrochen", "")
                                                logbit[6] = 2
                                                return                                            
                                            if GPIO.event_detected(i_tasterok):
                                                while True:
                                                    display_schreiben("L\357schen", "mit ok")
                                                    time.sleep(2)
                                                    display_schreiben("Abbruch", "beliebige Taste")
                                                    time.sleep(2)
                                                    if GPIO.event_detected(i_tastermenue):
                                                        logbit[6] = 2
                                                        return
                                                    if GPIO.event_detected(i_tasterplus):
                                                        logbit[6] = 2
                                                        return
                                                    if GPIO.event_detected(i_tasterminus):
                                                        logbit[6] = 2
                                                        return
                                                    if GPIO.event_detected(i_tasterok):
                                                        cursor.execute("DELETE FROM benutzer WHERE uid = :user",{"user" : user})
                                                        cursor.execute("UPDATE config SET kasse = kasse - :konto",{"konto" : konto})
                                                        connection.commit()
                                                        display_schreiben("Benutzer", "gel\357scht")
                                                        logbit[6] = 2
                                                        return

#Karte aufladen
def m_aufladen():
    global user
    global konto
    logbit[1] = 1
    betrag = 5.0
    clear_event()
    display_schreiben("Aufladebetrag:", "{:.2f}".format(betrag) + "EUR")
    while True:
        if GPIO.event_detected(i_tasterplus):
            betrag = betrag + 0.5
            display_schreiben("Aufladebetrag:", "{:.2f}".format(betrag) + "EUR")
        if GPIO.event_detected(i_tasterminus):
            betrag = betrag - 0.5
            display_schreiben("Aufladebetrag:", "{:.2f}".format(betrag) + "EUR")
        if GPIO.event_detected(i_tasterok):
            display_schreiben("Bitte " + "{:.2f}".format(betrag) + "EUR", "einzahlen")
            while True:
                if GPIO.event_detected(i_tastermenue): 
                    display_schreiben("Abgebrochen", "")
                    logbit[1] = 2
                    return
                if GPIO.event_detected(i_tasterok):
                    konto = konto + betrag
                    cursor.execute("UPDATE benutzer SET konto = :konto WHERE uid = :user",{"user" : user, "konto" : konto})
                    display_schreiben("Betrag", "aufgeladen")
                    cursor.execute("UPDATE config SET kasse = kasse + :betrag",{"betrag" : betrag})
                    connection.commit()
                    logbit[1] = 2
                    return
        if GPIO.event_detected(i_tastermenue): 
            display_schreiben("Abgebrochen", "")
            logbit[1] = 2
            return


#Kaffeepreis anpassen
def me_preis():
    logbit[9] = 1
    global kaffeepreis
    global kaffeepreisfix
    clear_event()
    display_schreiben("Preis:", "{:.2f}".format(kaffeepreis) + "EUR")
    while True:
        if GPIO.event_detected(i_tasterminus):
            if kaffeepreis <= 0.05:
                display_schreiben("Nix zu", "verschenken")
                continue
            kaffeepreis = kaffeepreis - 0.05
            kaffeepreis = round(kaffeepreis, 2)
            display_schreiben("Preis:", "{:.2f}".format(kaffeepreis) + "EUR")
            
        if GPIO.event_detected(i_tasterplus):
            if kaffeepreis >= 1.00:
                display_schreiben("Wohlstand", "ausgebrochen?")
                continue
            kaffeepreis = kaffeepreis + 0.05
            kaffeepreis = round(kaffeepreis, 2)
            display_schreiben("Preis:", "{:.2f}".format(kaffeepreis) + "EUR")
            
        if GPIO.event_detected(i_tasterok):
            cursor.execute("UPDATE config SET kaffeepreis = :kaffeepreis",{"kaffeepreis" : kaffeepreis})
            connection.commit()
            kaffeepreisfix = kaffeepreis
            display_schreiben("Neuer Preis:", "{:.2f}".format(kaffeepreis) + "EUR")
            logbit[9] = 2
            return
        
        if GPIO.event_detected(i_tastermenue):
            display_schreiben("Abgebrochen", "")
            logbit[9] = 2
            return
    
#Ausgleichsbuchung für Kasse erzeugen
def me_kasse_korrigieren():
    logbit[7] = 1
    clear_event()
    display_schreiben("Differenzbetrag", "eingeben")
    time.sleep(2)
    betrag = zahlen_einstellen()
    display_schreiben("Betrag zuviel? -", "Betrag zuwenig +")
    clear_event()
    while True:
        if GPIO.event_detected(i_tastermenue):
            display_schreiben("Abgebrochen")
            return
        if GPIO.event_detected(i_tasterplus):
            cursor.execute("UPDATE config SET kasse = kasse + :betrag",{"betrag" : betrag})
            break
        if GPIO.event_detected(i_tasterminus):
            cursor.execute("UPDATE config SET kasse = kasse - :betrag",{"betrag" : betrag})
            break        
    connection.commit()
    cursor.execute("SELECT kasse FROM config")
    datensatz = []
    for row in cursor:
        row = list(row)
        datensatz = datensatz + row
    betrag = float(string_generieren(datensatz))
    display_schreiben("Verbucht", "Kasse: " + "{:.2f}".format(betrag) + "EUR")
    logbit[7] = 2
    return

#Entkalkungsmodus
def me_entkalken():
    global logbit
    logbit[8] = 1
    GPIO.output(o_freigabe, 1)
    clear_event()
    while True:
        display_schreiben("Taster ok, wenn", "entkalken fertig")
        if GPIO.event_detected(i_tasterok):
            GPIO.output(o_freigabe, 0)
            logbit[8] = 2
            display_schreiben("Entkalken", "beendet")
            return

#Geld auszahlen
def m_auszahlen():
    logbit[3] = 1
    betrag = zahlen_einstellen()
    display_schreiben("{:.2f}".format(betrag) + "EUR von", "Kasse entnehmen")
    while True:
        if GPIO.event_detected(i_tastermenue):
            display_schreiben("Abgebrochen")
            return
        if GPIO.event_detected(i_tasterok):
            cursor.execute("UPDATE config SET kasse = kasse - :betrag",{"betrag" : betrag})
            connection.commit()
            cursor.execute("SELECT kasse FROM config")
            datensatz = []
            for row in cursor:
                row = list(row)
                datensatz = datensatz + row
            betrag = float(string_generieren(datensatz))
            display_schreiben("Abgebucht", "Kasse: " + "{:.2f}".format(betrag) + "EUR")
            logbit[3] = 2
            return

#LED blau
def led_blau():
    GPIO.output(o_led_b, 1)
    GPIO.output(o_led_g, 0)
    GPIO.output(o_led_r, 0)

#LED grün
def led_gruen():
    GPIO.output(o_led_b, 0)
    GPIO.output(o_led_g, 1)
    GPIO.output(o_led_r, 0)

#LED rot
def led_rot():
    GPIO.output(o_led_b, 0)
    GPIO.output(o_led_g, 0)
    GPIO.output(o_led_r, 1)

#Statistik ansehen    
def m_statistik():
    logbit[2] = 1
    cursor.execute("SELECT count(*), sum(kaffeepreis) AS kaffesumme FROM log WHERE logwert > 118098")
    datensatz = cursor.fetchone()
    if type(datensatz) == None:
        display_schreiben("Fehler")
    else:
        display_schreiben("Gesamtstatistik")
        time.sleep(2)
        display_schreiben(str(datensatz[0]) + "Stk f\365r", str(datensatz[1]) + "EUR getrunken") #\365 = ü
        time.sleep(2)
    logbit[2] = 2

#Letzte Person eingeloggt    
def m_lastkaffee():
    logbit[4] = 1
    cursor.execute("SELECT benutzer.vorname, benutzer.nachname, log.timestamp FROM benutzer LEFT JOIN log ON benutzer.uid = log.uid WHERE log.logwert > 118098 ORDER BY log.timestamp DESC LIMIT 1")
    #datensatz = []
    datensatz = cursor.fetchone()
    print(datensatz)
    print(type(datensatz))
    if type(datensatz) == None:
        display_schreiben("Noch kein Kaffee", "getrunken")
    else:
        display_schreiben("Letzer Kaffe von", datensatz[0] + datensatz[1])
    time.sleep(2)
    logbit[4] = 2

#Herunterfahren
def me_herunterfahren():
    display_schreiben("System wird", "heruntergefahren")
    GPIO.cleanup()
    os.system("sudo shutdown -h now")

#RFID lesen
def rfid_read(rdr, util):
    (error, data) = rdr.request()
    (error, uid) = rdr.anticoll()
    if error: uid = None
    if not error:
        string = ""
        for i in uid:
            string = string + str(i)
        return string

#User Check
def user_check(user):
    global timestamp
    timestamp = time.time()    
    cursor.execute("SELECT * FROM benutzer WHERE uid = :uid",{"uid" : user})
    user_datensatz = cursor.fetchone()
    return user_datensatz

# # Menü # #
def f_menue(userrechte):
    menue = [["Aufladen", m_aufladen],
             ["Statistik", m_statistik],
             ["Auszahlen", m_auszahlen],
             ["Letzter Kaffee", m_lastkaffee]]
    if userrechte == 1:
        menue.append(["Registrieren", me_register])
        menue.append(["L\357schen", me_delete]) #\357=ö
        menue.append(["Preis anpassen", me_preis])
        menue.append(["Kasse angleichen", me_kasse_korrigieren])
        menue.append(["Entkalken", me_entkalken])
        menue.append(["Herunterfahren", me_herunterfahren])
    return menue

def menuesteuerung(menue):
    GPIO.add_event_detect(i_tasterok, GPIO.FALLING, bouncetime=200)
    GPIO.add_event_detect(i_tasterminus, GPIO.FALLING, bouncetime=200)
    GPIO.add_event_detect(i_tasterplus, GPIO.FALLING, bouncetime=200)
    GPIO.output(o_freigabe, 0)
    led_blau()
    counter = 0
    anmeldezeit = 0
    display = False
    while anmeldezeit < 20: # Wert * 0.5 entspricht die Anmeldezeit im Menü
        if display == False:
            display_schreiben(menue[counter][0], "ok?")
            display = True
        if GPIO.event_detected(i_tastermenue):
            if len(menue) - 1 == counter:
                counter = 0
            else:
                counter += 1
            display = False
            anmeldezeit = 0
        if GPIO.event_detected(i_tasterok):
            menue[counter][1]()
            anmeldezeit = 0
        anmeldezeit += 1
        time.sleep(0.5)
    #Exit
    GPIO.remove_event_detect(i_tasterok)
    GPIO.remove_event_detect(i_tasterminus)
    GPIO.remove_event_detect(i_tasterplus)

#Logbits:
#Index0 = Login -> 0 = nicht durchgeführt, 1 = Eingeloggt, 2 = Ausgeloggt
#Index1 = M_Aufladen -> 0 = nicht aufgerufen, 1 = ausgeführt, 2 = verlassen
#Index2 = M_Statistik -> 0 = nicht aufgerufen, 1 = ausgeführt, 2 = verlassen
#Index3 = M_Auszahlen -> 0 = nicht aufgerufen, 1 = ausgeführt, 2 = verlassen
#Index4 = M_Last Kaffee -> 0 = nicht aufgerufen, 1 = ausgeführt, 2 = verlassen
#Index5 = Me_Registrieren -> 0 = nicht aufgerufen, 1 = ausgeführt, 2 = verlassen
#Index6 = Me_Löschen -> 0 = nicht aufgerufen, 1 = ausgeführt, 2 = verlassen
#Index7 = Me_Kasse angleichen -> 0 = nicht aufgerufen, 1 = ausgeführt, 2 = verlassen
#Index8 = Me_Entkalken -> 0 = nicht aufgerufen, 1 = ausgeführt, 2 = verlassen
#Index9 = Me_Preis anpassen -> 0 = nicht aufgerufen, 1 = ausgeführt, 2 = verlassen
#Index10 = Kaffebezug -> 0 = nicht gemahlen, 1 = gemahlen, 2 = Kaffee erfolgreich
def logbit_schreiben(unbekannt):
    global timestamp
    global user
    global logbit
    logwert = 0
    zähler = 0
    if timestamp == None:
        timestamp = time.time()
    for bit in logbit:
        logwert = logwert + bit * 3 **zähler
        zähler += 1
    cursor.execute("INSERT INTO log VALUES (:timestamp, :user, :logwert, :kaffeepreis, :unbekannt)",{"timestamp" : timestamp, "user" : user, "logwert" : logwert, "kaffeepreis" : kaffeepreis, "unbekannt" : unbekannt})
    connection.commit()
    logbit = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# # Programminitialisierung # #
#Überprüfen ob ein Benutzer vorhanden ist 
menue = []
cursor.execute("SELECT * FROM benutzer")
datensatz = []
for row in cursor:
    row = list(row)
    datensatz = datensatz + row
if len(datensatz) == 0:
    GPIO.output(o_lcd_led, 1)
    led_blau()
    display_schreiben("Karte vor", "Leser halten")
    uid = None
    while uid == None:
        uid = rfid_read(rdr, util)
        time.sleep(0.3)
    cursor.execute("INSERT INTO benutzer VALUES (:uid, 'Service', 'Technicka', 10, 1)",{"uid" : uid})
    connection.commit()
    display_schreiben("Servicebenutzer", "angelegt")
    
#config abholen
cursor.execute("SELECT * FROM config")
datensatz = []
for row in cursor:
    row = list(row)
    datensatz = datensatz + row
if len(datensatz) == 0: #Erster Start, Standardwerte schreiben
    cursor.execute("INSERT INTO config VALUES(0.5, 0.0)")
    connection.commit()
    cursor.execute("SELECT * FROM config") #nochmals auslesen
    datensatz = []
    for row in cursor:
        row = list(row)
        datensatz = datensatz + row    
    
kaffeepreis = kaffeepreisfix = datensatz[0]
kasse = datensatz[1]



# # Start Hauptprogramm # #
try:
    connection.close()
    GPIO.output(o_freigabe, 0)
    GPIO.output(o_lcd_led, 0)
    freigabe_status = 0
    led_rot()
    user = ""
    logbit = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    unbekannt = 1
    timestamp = None
    GPIO.add_event_detect(i_tastermenue, GPIO.FALLING, bouncetime=200)
    
    while True:
        if GPIO.event_detected(i_tastermenue):
            GPIO.output(o_lcd_led, 1)
            display_schreiben("Kaffeepreis: ", "{:.2f}".format(kaffeepreis))
            time.sleep(2)
            lcd.clear()
            GPIO.output(o_lcd_led, 0)        
        user = rfid_read(rdr, util)
        if user != None:
            sqlite3_verbinden()
            GPIO.output(o_lcd_led, 1)
            #Userdatensatz abholen, auswerten und Freigabe sofern maxkredit nicht ausgeschöpft
            user_datensatz = user_check(user)
            if user_datensatz == None:
                unbekannt = 1
                connection.commit()
                display_schreiben("Unbekannt", "Bitte /nregistrieren")
                led_blau()
                time.sleep(1)
                led_rot()
                time.sleep(1)
                led_blau()
                time.sleep(1)
                led_rot()
                logbit_schreiben(unbekannt)
                time.sleep(5)
                lcd.clear()
                GPIO.output(o_lcd_led, 0)
                continue
            unbekannt = 0
            logbit[0] = 1
            tmp, vorname, name, konto, rechte = user_datensatz
            display_schreiben("Hallo", vorname)
            if  kaffeepreis < konto:
                led_gruen()
                GPIO.output(o_freigabe, 1)
                freigabe_status = 1
                GPIO.add_event_detect(i_mahlwerk, GPIO.FALLING, bouncetime=200)
                GPIO.add_event_detect(i_wasser, GPIO.FALLING, bouncetime=200)
            else:
                display_schreiben("Bitte Geld", "aufladen")
                led_blau()
                time.sleep(0.5)
                led_rot()
                time.sleep(0.5)
                led_blau()
                time.sleep(0.5)
                led_rot()
            menue = f_menue(rechte)
            anmeldezeit = 0
            time.sleep(1)
            display_schreiben(vorname, "Konto: " + "{:.2f}".format(konto) + "EUR")
            while anmeldezeit < 40:
                if GPIO.event_detected(i_wasser): pass
                if GPIO.event_detected(i_tastermenue): #Überwachen ob das Menü gestartet werden muss
                    menuesteuerung(menue)
                if GPIO.event_detected(i_mahlwerk): #Kaffeezubereitung
                    logbit[10] = 1
                    zeitkaffee = 0
                    while zeitkaffee < 30: #Wert * 0.5, innerhalb dieser Zeit muss Wasser auch gestartet sein, sonst wurde abgeborchen
                        if GPIO.event_detected(i_wasser):
                            if rechte != 1:
                                konto = konto - kaffeepreis
                                display_schreiben("Neuer Stand:", "{:.2f}".format(konto) + "EUR")
                                #Kontostand updaten
                                cursor.execute("UPDATE benutzer SET konto = :konto WHERE uid = :user",{"user" : user, "konto" : konto})
                                connection.commit()
                                logbit[10] = 2
                            if rechte == 1:
                                kaffeepreis = 0
                                display_schreiben("Gratis Kaffee?")
                                logbit[10] = 2
                            time.sleep(3)
                            zeitkaffee = anmeldezeit = 1000 #Wert muss größer als gewählte Anmeldezeit sein, somit logout
                        zeitkaffee += 1
                        time.sleep(0.5)
                anmeldezeit += 1
                time.sleep(0.5)
            #Logout
            if freigabe_status == 1:
                GPIO.output(o_freigabe, 0)
                GPIO.remove_event_detect(i_mahlwerk)
                GPIO.remove_event_detect(i_wasser)
                freigabe_status = 0
            logbit[0] = 2
            logbit_schreiben(unbekannt)                
            vorname = name = konto = rechte = 0
            timestamp = None
            kaffeepreis = kaffeepreisfix
            led_rot()
            display_schreiben("Erfolgreich", "abgemeldet")
            unbekannt = 1
            time.sleep(2)
            lcd.clear()
            GPIO.output(o_lcd_led, 0)
            connection.close()
        time.sleep(0.5)

except KeyboardInterrupt:
    lcd.clear()
    GPIO.cleanup()
    sys.exit()

finally:
    sqlite3_verbinden()
    logbit_schreiben(unbekannt)
    display_schreiben("Fehler", "")
    GPIO.cleanup()
    


"""Select count(*), sum(kaffepreis) as kaffesumme from log where timestamp < ..... and timestamp > ...... and step = 999
1 0 1
1 * 3^0 + 0 * 3^1 + 1 * 3^2 = 5
"""
