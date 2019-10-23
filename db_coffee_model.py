import peewee
from peewee import fn


database = peewee.Proxy()


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(peewee.Model):
    class Meta:
        database = database


class Benutzer(BaseModel):
    vorname = peewee.TextField(null=True)
    nachname = peewee.TextField(null=True)
    konto = peewee.FloatField(null=True)
    kaffeelimit = peewee.IntegerField(null=True)
    rechte = peewee.IntegerField(null=True)

    class Meta:
        table_name = 'benutzer'


class Chip(BaseModel):
    uid = peewee.IntegerField(primary_key=True)
    benutzer = peewee.ForeignKeyField(Benutzer, backref="benutzer")


class Buch(BaseModel):
    betrag = peewee.FloatField(null=True)
    timestamp = peewee.FloatField(null=True, primary_key=True)
    typ = peewee.TextField(null=True)
    benutzer = peewee.ForeignKeyField(Benutzer, backref="benutzer")

    class Meta:
        table_name = 'buch'


class Config(BaseModel):
    kaffeepreis = peewee.FloatField(null=True)
    kasse = peewee.FloatField(null=True)

    class Meta:
        table_name = 'config'
        primary_key = False


class Reinigung(BaseModel):
    timestamp = peewee.FloatField(null=True, primary_key=True)
    typ = peewee.TextField(null=True)
    benutzer = peewee.ForeignKeyField(Benutzer, backref="benutzer")

    class Meta:
        table_name = 'reinigung'


def db_create_table():
    database.create_tables([Benutzer, Buch, Chip, Config, Reinigung])

