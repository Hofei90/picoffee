import os
import db_coffee_model as db


SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))
db.database.initialize(db.peewee.SqliteDatabase(os.path.join(SKRIPTPFAD, 'db_coffee_test.db3'), **{}))
db.db_create_table()

uid = 12345678

"""
user = db.Benutzer.create(vorname="vor", nachname="nach", konto=0.0, kaffeelimit=3, rechte=0)
db.Chip.create(uid=uid, benutzer=user)"""


def user_check(uid):
    account = db.Chip.get_or_none(db.Chip.uid == uid)
    return account


def get_letzten_kaffee_bezug():
    """
    :return:
    """
    abfrage = db.Buch.select().where(db.Buch.typ == "kaffee").order_by(db.Buch.timestamp.desc())\
                .limit(1).execute()
    abfrage_liste = []
    for query in abfrage:
        abfrage_liste.append(query)
    return abfrage


user = user_check(uid)
print(user.benutzer.vorname)


#db.Buch.create(betrag=0.2, timestamp=2, typ="kaffee", benutzer=user.benutzer)
letzter_kaffee = get_letzten_kaffee_bezug()
print(letzter_kaffee.benutzer.vorname)