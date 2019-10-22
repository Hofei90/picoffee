import os
import db_coffee_model as db


SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))
db.database.initialize(db.peewee.SqliteDatabase(os.path.join(SKRIPTPFAD, 'db_coffee_test.db3'), **{}))
db.db_create_table()

"""
user = db.Benutzer.create(vorname="vor", nachname="nach", konto=0.0, kaffeelimit=3, rechte=0)
uid = db.Chip.create(uid=12345678)
account = db.Account.create(uid=uid, benutzer=user)"""

uid = 12345678
account = db.Account.get(backref="uid")

print(account)