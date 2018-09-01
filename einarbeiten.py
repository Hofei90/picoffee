# # # # # # # # # # # # # ## # # #

# # RFID Initialisieren # #
util.debug = True


# # Funktionen # #

# Display aktualisieren
def display_schreiben(zeile1, zeile2=""):
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
        lcd.write_string(zeile1 + "\n\r" + zeile2)


# String aus Liste generieren
def string_generieren(liste):
    anzahl = liste.count("")
    print(anzahl)
    print(liste)
    for i in range(0, anzahl):
        liste.remove("")
        i += 1
    string = ""
    for buchstabe in liste:
        string = string + str(buchstabe)
    return string





# Benutzer registrierung
def me_register():
    logbit[5] = 1
    clear_event()
    display_schreiben("Neuen Chip", "einlesen")
    while True:
        if GPIO.event_detected(i_tastermenue):
            display_schreiben("Abgebrochen")
            logbit[5] = 2
            return 0
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
    lcd.cursor_mode = "blink"
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
                lcd.cursor_mode = "hide"
                display_schreiben("Abgebrochen", "")
                time.sleep(2)
                return 0
            if unterfunktion == 0:
                vorname = string_generieren(reg_name)
                reg_name = [""] * 16
                display_schreiben("Nachname", "")
                cursor_position = 0
                lcd.cursor_pos = (1, cursor_position)

            if unterfunktion == 1:
                nachname = string_generieren(reg_name)
                cursor.execute("INSERT INTO benutzer VALUES (:uid, :vorname, :nachname, 0, 0)",
                               {"uid": uid, "vorname": vorname, "nachname": nachname})
                connection.commit()
                display_schreiben(vorname, nachname)
                time.sleep(2)
                display_schreiben("erfolgreich", "registriert")
                lcd.cursor_mode = "hide"
                logbit[5] = 2
                return 0
            unterfunktion += 1

        if GPIO.event_detected(i_tasterok):
            if select == 0:
                lcd.cursor_mode = "line"
                select = 1
            elif select == 1:
                lcd.cursor_mode = "blink"
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

            # Benutzer löschen


def me_delete():
    logbit[6] = 1
    clear_event()
    display_schreiben("Chip zum", "l\357schen einlesen")  # \357 = ö
    while True:
        if GPIO.event_detected(i_tastermenue):
            display_schreiben("Abgebrochen", "")
            logbit[6] = 2
            return 0
        user = rfid_read(rdr, util)
        if user != None:
            user_datensatz = user_check(user)
            if user_datensatz == None:
                display_schreiben("Chip", "unbekannt")
                logbit[6] = 2
                return 0
            else:
                tmp, vorname, name, konto, rechte = user_datensatz
                if rechte == 1:
                    display_schreiben("root kann sich", "nicht l\357schen")
                    logbit[6] = 2
                    return 0
                clear_event()
                display_schreiben("weiter mit ok", "Chip geh\357rt")
                while True:
                    if GPIO.event_detected(i_tastermenue):
                        display_schreiben("Abgebrochen", "")
                        logbit[6] = 2
                        return 0
                    if GPIO.event_detected(i_tasterok):
                        display_schreiben(vorname, name)
                        while True:
                            if GPIO.event_detected(i_tastermenue):
                                display_schreiben("Abgebrochen", "")
                                logbit[6] = 2
                                return 0
                            if GPIO.event_detected(i_tasterok):
                                display_schreiben("Restguthaben:", "{:.2f}".format(konto) + "EUR")
                                while True:
                                    if GPIO.event_detected(i_tastermenue):
                                        display_schreiben("Abgebrochen", "")
                                        logbit[6] = 2
                                        return 0
                                    if GPIO.event_detected(i_tasterok):
                                        display_schreiben("Betrag", "ausbezahlen")
                                        while True:
                                            if GPIO.event_detected(i_tastermenue):
                                                display_schreiben("Abgebrochen", "")
                                                logbit[6] = 2
                                                return 0
                                            if GPIO.event_detected(i_tasterok):
                                                while True:
                                                    display_schreiben("L\357schen", "mit ok")
                                                    time.sleep(2)
                                                    display_schreiben("Abbruch", "beliebige Taste")
                                                    time.sleep(2)
                                                    if GPIO.event_detected(i_tastermenue):
                                                        logbit[6] = 2
                                                        return 0
                                                    if GPIO.event_detected(i_tasterplus):
                                                        logbit[6] = 2
                                                        return 0
                                                    if GPIO.event_detected(i_tasterminus):
                                                        logbit[6] = 2
                                                        return 0
                                                    if GPIO.event_detected(i_tasterok):
                                                        cursor.execute("DELETE FROM benutzer WHERE uid = :user",
                                                                       {"user": user})
                                                        cursor.execute("UPDATE config SET kasse = kasse - :konto",
                                                                       {"konto": konto})
                                                        connection.commit()
                                                        display_schreiben("Benutzer", "gel\357scht")
                                                        logbit[6] = 2
                                                        return 0




# Kaffeepreis anpassen
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
            cursor.execute("UPDATE config SET kaffeepreis = :kaffeepreis", {"kaffeepreis": kaffeepreis})
            connection.commit()
            kaffeepreisfix = kaffeepreis
            display_schreiben("Neuer Preis:", "{:.2f}".format(kaffeepreis) + "EUR")
            logbit[9] = 2
            return 0

        if GPIO.event_detected(i_tastermenue):
            display_schreiben("Abgebrochen", "")
            logbit[9] = 2
            return 0


# Ausgleichsbuchung für Kasse erzeugen
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
            return 0
        if GPIO.event_detected(i_tasterplus):
            cursor.execute("UPDATE config SET kasse = kasse + :betrag", {"betrag": betrag})
            break
        if GPIO.event_detected(i_tasterminus):
            cursor.execute("UPDATE config SET kasse = kasse - :betrag", {"betrag": betrag})
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
    return 0



















# Muss neu programmiert werden



# Statistik ansehen
def m_statistik():
    logbit[2] = 1
    cursor.execute("SELECT count(*), sum(kaffeepreis) AS kaffesumme FROM log WHERE logwert > 118098")
    datensatz = cursor.fetchone()
    if type(datensatz) == None:
        display_schreiben("Fehler")
    else:
        display_schreiben("Gesamtstatistik")
        time.sleep(2)
        display_schreiben(str(datensatz[0]) + "Stk f\365r", str(round(datensatz[1], 2)) + "EUR getrunken")  # \365 = ü
        time.sleep(2)
    logbit[2] = 2
    return 0


# Letzte Person eingeloggt
def m_lastkaffee():
    logbit[4] = 1
    cursor.execute(
        "SELECT benutzer.vorname, benutzer.nachname, log.timestamp FROM benutzer LEFT JOIN log ON benutzer.uid = log.uid WHERE log.logwert > 118098 ORDER BY log.timestamp DESC LIMIT 1")
    # datensatz = []
    datensatz = cursor.fetchone()
    print(datensatz)
    print(type(datensatz))
    if type(datensatz) == None:
        display_schreiben("Noch kein Kaffee", "getrunken")
    else:
        display_schreiben("Letzer Kaffe von", datensatz[0] + datensatz[1])
    time.sleep(2)
    logbit[4] = 2
    return 0