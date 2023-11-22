import sqlite3
import os
from scp import SCPClient
import paramiko
import datetime


SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))
PFAD_DB = "/home/pi/picoffee/"
DATEI_DB = "db_coffee.db3"


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


class Reinigungprotokoll:
    def __init__(self, db):
        self.db = db
        self.spaltenname = None
        self.spaltenwerte = None

    def get_db_reinigung(self, typ):
        daten = []
        with self.db as db:
            db.cursor.execute("""
                                            SELECT timestamp, uid, typ
                                            FROM reinigung
                                            WHERE typ = :typ""", {"typ": typ})
            for row in db.cursor:
                ts = convert_to_datetime(row[0])
                vorname, nachname = get_user_name(db, row[1])
                daten.append([ts, vorname, nachname, row[2]])
        return daten


def get_anmeldedaten():
    ip = input("IP: ")
    user = input("User: ")
    pw = input("Password: ")
    return ip, user, pw


def convert_to_datetime(ts):
    return convert_to_datum_ausgabe(datetime.datetime.fromtimestamp(ts))


def convert_to_datum_ausgabe(dt):
    return datetime.datetime.strftime(dt, "%d.%m.%Y %H:%M Uhr")


def get_user_name(db, uid):
    db.cursor.execute("""
                        SELECT vorname, nachname
                        FROM benutzer
                        WHERE uid = :uid""", {"uid": uid})
    daten = db.cursor.fetchone()
    vorname, nachname = daten
    return vorname, nachname


def datenbank_laden():
    anmeldedaten = get_anmeldedaten()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(anmeldedaten[0], username=anmeldedaten[1], password=anmeldedaten[2])

    with SCPClient(ssh.get_transport()) as scp:
        scp.get(os.path.join(PFAD_DB, DATEI_DB), SKRIPTPFAD)


def spaltenmax_ermitteln(spaltennamen, daten):
    spaltenmax = [0] * len(spaltennamen)
    for index, spalte in enumerate(spaltennamen):
        if spaltenmax[index] < len(spalte):
            spaltenmax[index] = len(spalte)
    for datensatz in daten:
        for index, spalte in enumerate(datensatz):
            if spaltenmax[index] < len(spalte):
                spaltenmax[index] = len(spalte)
    return spaltenmax


def ausgabe_schreiben(spaltenmax, spaltennamen, daten):
    ausgabe = "#" * (sum(spaltenmax) + 5)
    print(ausgabe)
    for index, spalte in enumerate(spaltennamen):
        print("#{:{align}{width}}".format(spalte, align="^", width=spaltenmax[index]), end="")
    print("#")
    print(ausgabe)
    for datensatz in daten:
        for index, spalte in enumerate(datensatz):
            print("#{:{width}}".format(spalte, width=spaltenmax[index]), end="")
        print("#")
    print(ausgabe)
    print()


def ausgabe_vorbereiten(spaltennamen, *args):
    daten = []
    for arg in args:
        for datensatz in arg:
            daten.append(datensatz)
    daten.sort()
    spaltenmax = spaltenmax_ermitteln(spaltennamen, daten)
    ausgabe_schreiben(spaltenmax, spaltennamen, daten)


def main():
    db = Datenbank(os.path.join(SKRIPTPFAD, DATEI_DB))
    protokoll = Reinigungprotokoll(db)

    spaltennamen = ["Datum", "Vorname", "Nachname", "Typ"]
    entkalken = protokoll.get_db_reinigung("entkalken")
    reinigung = protokoll.get_db_reinigung("reinigung")
    ausgabe_vorbereiten(spaltennamen, entkalken, reinigung)
    pass


if __name__ == "__main__":
    main()
