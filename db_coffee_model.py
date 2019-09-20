from peewee import *

database = SqliteDatabase('db_coffee.db3', **{})

class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class Benutzer(BaseModel):
    uid = AutoField(null=True)
    vorname = TextField(null=True)
    nachname = TextField(null=True)
    konto = FloatField(null=True)
    kaffeelimit = IntegerField(null=True)
    rechte = IntegerField(null=True)

    class Meta:
        table_name = 'benutzer'


class Buch(BaseModel):
    betrag = FloatField(null=True)
    timestamp = FloatField(null=True, primary_key=True)
    typ = TextField(null=True)
    uid = IntegerField(null=True)

    class Meta:
        table_name = 'buch'

class Config(BaseModel):
    kaffeepreis = FloatField(null=True)
    kasse = FloatField(null=True)

    class Meta:
        table_name = 'config'
        primary_key = False

class Reinigung(BaseModel):
    timestamp = FloatField(null=True, primary_key=True)
    typ = TextField(null=True)
    uid = IntegerField(null=True)

    class Meta:
        table_name = 'reinigung'

