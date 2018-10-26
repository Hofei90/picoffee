import sqlite3
import os
import matplotlib.pyplot as plt
import datetime
from collections import defaultdict
from scp import SCPClient
import paramiko

SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))
PFAD_DB = "/home/pi/Kaffee/"
DATEI_DB = "db_coffee.db3"


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
                            "konto FLOAT, kaffeelimit INTEGER, rechte INTEGER, PRIMARY KEY (uid))")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS buch(timestamp FLOAT, uid INTEGER, "
                            "betrag FLOAT, typ TEXT, PRIMARY KEY (timestamp))")
        self.connection.close()

    def sqlite3_verbinden(self):
        self.connection = sqlite3.connect(self.datenbankpfad)
        self.cursor = self.connection.cursor()

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def __enter__(self):
        self.sqlite3_verbinden()
        return self


class Auswertung:
    def __init__(self, db):
        self.db = db
        self._subplotnr = 221

    def _get_subplotnr(self):
        subplotnr = self._subplotnr
        self._subplotnr += 1
        return subplotnr

    def bezug_monat(self):
        with self.db as db:
            db.cursor.execute("""
                                SELECT strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch')) as 'Month', 
                                total(betrag) as 'Summe', count(betrag) as 'Stück'
                                FROM buch
                                WHERE typ = "kaffee"
                                GROUP BY strftime('%Y-%m', datetime(timestamp, 'unixepoch'))
                                ORDER BY timestamp ASC""")
            daten = db.cursor.fetchall()
        self.bezug_plotten(daten)

    def bezug_tag(self):
        with self.db as db:
            db.cursor.execute("""
                                SELECT strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch')) as 'Tag', 
                                total(betrag) as 'Summe', count(betrag) as 'Stück'
                                FROM buch
                                WHERE typ = "kaffee"
                                GROUP BY strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch'))
                                ORDER BY timestamp ASC""")
            daten = db.cursor.fetchall()
        self.bezug_plotten(daten)

    def bezug_plotten(self, daten):
        x = []
        y1 = []
        y2 = []
        for datensatz in daten:
            x.append(datetime.datetime.strptime(datensatz[0], "%Y-%m-%d"))
            y1.append(datensatz[1])
            y2.append(datensatz[2])
        daten_plotten(x, y1, "Summe", self._get_subplotnr())
        daten_plotten(x, y2, "Stück", self._get_subplotnr())

    def kassen_verlauf(self):
        betrag = self._get_positive_data()
        betrag.extend(self._get_negative_data())
        betrag = convert_to_datetime(betrag)
        betrag = datum_vereinen(betrag)
        betrag.sort()

        x = []
        y = []
        for datensatz in betrag:
            x.append(datensatz[0])
            y.append(datensatz[1])
        daten_plotten(x, y, "Kasse", self._get_subplotnr())

    def _get_positive_data(self):
        with self.db as db:
            db.cursor.execute("""
                                SELECT strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch')) as 'Tag', 
                                sum(betrag) as 'positiver_Betrag'
                                FROM buch
                                WHERE typ = "korrektur_plus" or typ = "aufladen"
                                GROUP BY strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch'))
                                ORDER BY timestamp ASC""")
            daten = db.cursor.fetchall()
        return daten

    def _get_negative_data(self):
        with self.db as db:
            db.cursor.execute("""
                                SELECT strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch')) as 'Tag', 
                                sum(betrag) * -1 as 'negativer_Betrag'
                                FROM buch
                                WHERE typ = "korrektur_minus" or typ = "auszahlen"
                                GROUP BY strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch'))
                                ORDER BY timestamp ASC""")
            daten = db.cursor.fetchall()
        return daten

    def anteil_kaffee(self):
        benutzer = self.get_uid()
        legende = []
        anzahl = []
        for user in benutzer:
            anzahl.append(self.get_anzahl(user)[0][0])
            legende.append(self.get_name(user)[0][0])

        fig1, ax1 = plt.subplots()
        ax1.pie(anzahl, labels=legende, shadow=True, startangle=90, autopct='%1.1f%%')
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.show()

    def get_uid(self):
        with self.db as db:
            db.cursor.execute("""
                                SELECT uid 
                                FROM benutzer""")
            daten = db.cursor.fetchall()
            return daten

    def get_anzahl(self, uid):
        uid = uid[0]
        with self.db as db:
            db.cursor.execute("""
                                SELECT count(betrag)
                                FROM buch
                                WHERE uid = :uid""", {"uid": uid})
            daten = db.cursor.fetchall()
        return daten

    def get_name(self, uid):
        uid = uid[0]
        with self.db as db:
            db.cursor.execute("""
                                SELECT vorname
                                FROM benutzer
                                WHERE uid = :uid""", {"uid": uid})
            daten = db.cursor.fetchall()
        return daten


def get_anmeldedaten():
    ip = input("IP: ")
    user = input("User: ")
    pw = input("Password: ")
    return ip, user, pw


def convert_to_datetime(daten):
    daten_neu = []
    for data in daten:
        daten_neu.append((datetime.datetime.strptime(data[0], "%Y-%m-%d"), data[1]))
    return daten_neu


def datum_vereinen(daten):
    daten_dict = defaultdict(int)
    for key, value in daten:
        daten_dict[key] += value
    daten_return = list(daten_dict.items())
    return daten_return


def daten_plotten(x, y, title, subplotnr):
    plt.subplot(subplotnr)
    plt.plot(x, y)
    plt.title(title)
    plt.grid(True)


def datenbank_laden():
    anmeldedaten = get_anmeldedaten()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(anmeldedaten[0], username=anmeldedaten[1], password=anmeldedaten[2])

    with SCPClient(ssh.get_transport()) as scp:
        scp.get(os.path.join(PFAD_DB, DATEI_DB), SKRIPTPFAD)


def main():
    datenbank_laden()
    db = Datenbank(os.path.join(SKRIPTPFAD, DATEI_DB))
    plt.figure(1)
    auswertung = Auswertung(db)
    auswertung.bezug_monat()
    auswertung.kassen_verlauf()
    #auswertung.anteil_kaffee()
    #plt.figure(2)
    #auswertung._subplotnr = 221
    #auswertung.bezug_tag()
    plt.show()

    os.remove(os.path.join(SKRIPTPFAD, DATEI_DB))


if __name__ == "__main__":
    main()
