import sqlite3
import os

SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))

DB_ALT = "kaffee.sqlite"
DB_NEU = "db_coffee.db3"


class Datenbank:
    def __init__(self, datenbankpfad):
        self.datenbankpfad = datenbankpfad
        self.connection = None
        self.cursor = None

    def sqlite3_verbinden(self):
        self.connection = sqlite3.connect(self.datenbankpfad)
        self.cursor = self.connection.cursor()

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def __enter__(self):
        self.sqlite3_verbinden()
        return self


def datenbank_initialisieren(db):
    with db as db_:
        db_.cursor.execute("CREATE TABLE IF NOT EXISTS config(kaffeepreis FLOAT, kasse FLOAT)")
        db_.cursor.execute("CREATE TABLE IF NOT EXISTS benutzer(uid INTEGER, vorname TEXT, nachname TEXT, "
                           "konto FLOAT, kaffeelimit INTEGER, rechte INTEGER, PRIMARY KEY (uid))")
        db_.cursor.execute("CREATE TABLE IF NOT EXISTS buch(timestamp FLOAT, uid INTEGER, "
                           "betrag FLOAT, typ TEXT, PRIMARY KEY (timestamp))")


def kaffee_bezuege_auslesen(db):
    with db as db_:
        db_.cursor.execute("SELECT log.timestamp, benutzer.uid, log.kaffeepreis FROM benutzer "
                           "LEFT JOIN log ON benutzer.uid = log.uid WHERE log.logwert > 118098 ORDER BY log.timestamp")
        datensatz = list(db_.cursor)
        return datensatz


def kaffee_bezuege_schreiben(db, datensatz_liste):
    with db as db_:
        anzahl_gesamt = len(datensatz_liste) - 1
        for anzahl_akt, datensatz in enumerate(datensatz_liste):
            timestamp, uid, kaffeepreis = datensatz
            print("Datensatz {} von {}".format(anzahl_akt, anzahl_gesamt))
            db_.cursor.execute("INSERT INTO buch VALUES (:timestamp, :uid, :betrag, :typ)",
                               {"timestamp": timestamp, "uid": uid, "betrag": kaffeepreis,
                                "typ": "kaffee"})
        db_.connection.commit()


def benutzer_auslesen(db):
    with db as db_:
        db_.cursor.execute("SELECT * FROM benutzer")
        datensatz = list(db_.cursor)
        return datensatz


def benutzer_schreiben(db, benutzerliste):
    with db as db_:
        for benutzer in benutzerliste:
            uid = benutzer[0]
            vorname = benutzer[1]
            nachname = benutzer[2]
            konto = round(benutzer[3], 2)
            rechte = benutzer[4]
            db_.cursor.execute("INSERT INTO benutzer VALUES (:uid, :vorname, :nachname, :konto, 0, :rechte)",
                               {"uid": uid, "vorname": vorname, "nachname": nachname,
                                "konto": konto, "rechte": rechte})
        db_.connection.commit()


def config_auslesen(db):
    with db as db_:
        db_.cursor.execute("SELECT * FROM config")
        datensatz = list(db_.cursor)
        return datensatz


def config_schreiben(db, datensatz_liste):
    with db as db_:
        for datensatz in datensatz_liste:
            kaffeepreis = datensatz[0]
            kasse = datensatz[1]

            db_.cursor.execute("INSERT INTO config VALUES (:kaffeepreis, :kasse)",
                               {"kaffeepreis": kaffeepreis, "kasse": kasse})
        db_.connection.commit()


def main():
    db_alt = Datenbank(os.path.join(SKRIPTPFAD, DB_ALT))
    db_neu = Datenbank(os.path.join(SKRIPTPFAD, DB_NEU))
    datenbank_initialisieren(db_neu)
    config_datensatz = config_auslesen(db_alt)
    config_schreiben(db_neu, config_datensatz)
    benutzer_datensatz = benutzer_auslesen(db_alt)
    benutzer_schreiben(db_neu, benutzer_datensatz)
    bezug_datensatz = kaffee_bezuege_auslesen(db_alt)
    kaffee_bezuege_schreiben(db_neu, bezug_datensatz)


if __name__ == "__main__":
    main()
