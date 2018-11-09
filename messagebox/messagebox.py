import peewee
import os

SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))
db = peewee.SqliteDatabase(os.path.join(SKRIPTPFAD, "messagebox.db3"))


class MessageBox(peewee.Model):
    nachricht = peewee.CharField()
    read_liste = peewee.TextField(default=[])
    erledigt = peewee.BooleanField(default=False)

    class Meta:
        database = db


def add_message(text):
    MessageBox.create(nachricht=text)


def get_new_message(uid):
    for read in MessageBox.select().where(MessageBox.read_liste.contains(uid)):
        print(read.nachricht)


if __name__ == "__main__":
    db.create_tables([MessageBox])
    get_new_message(3)
