import old_db_model as odb
import db_coffee_model as db

db.database.initialize(db.peewee.SqliteDatabase("db_coffee_new.db3"))
db.db_create_table()
query = odb.Benutzer.select()
print("Schreibe Benutzertabelle")
unbekannt = db.Benutzer.create(vorname="unbekannt",
                               nachname="unbekannt",
                               konto=0,
                               kaffeelimit=0,
                               rechte=0)
for benutzer in query:
    benutzer_neu = db.Benutzer.create(vorname=benutzer.vorname,
                                      nachname=benutzer.nachname,
                                      konto=benutzer.konto,
                                      kaffeelimit=benutzer.kaffeelimit,
                                      rechte=benutzer.rechte)
    db.Chip.create(uid=benutzer.uid, benutzer=benutzer_neu)

print("Schreibe Buchtabelle")
query = odb.Buch.select()
for data in query:
    try:
        chip = db.Chip.get(db.Chip.uid == data.uid)
        db.Buch.create(betrag=data.betrag,
                       timestamp=data.timestamp,
                       typ=data.typ,
                       benutzer=chip.benutzer)
    except db.ChipDoesNotExist:
        db.Buch.create(betrag=data.betrag,
                       timestamp=data.timestamp,
                       typ=data.typ,
                       benutzer=unbekannt)

print("Schreibe Config")
query = odb.Config.select()
for data in query:
    db.Config.create(kaffeepreis=data.kaffeepreis,
                     kasse=data.kasse)

print("Schreibe Reinigungstabelle")
query = odb.Reinigung.select()
for data in query:
    chip = db.Chip.get(db.Chip.uid == data.uid)
    db.Reinigung.create(timestamp=data.timestamp,
                        typ=data.typ,
                        benutzer=chip.benutzer)