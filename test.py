import os
import db_coffee_model as db


SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))
db.database.initialize(db.peewee.SqliteDatabase(os.path.join(SKRIPTPFAD, 'db_coffee_test.db3'), **{}))
db.db_create_table()

uid = 11111111

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
    return abfrage[0]



user = user_check(uid)
abfrage = [query for query in db.Benutzer.select().order_by(db.Benutzer.nachname.desc())]
print(abfrage[-3].vorname)

#db.Buch.create(betrag=0.2, timestamp=2, typ="kaffee", benutzer=user.benutzer)


