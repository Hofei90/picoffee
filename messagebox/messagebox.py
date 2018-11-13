import peewee
import os

SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))
DB = peewee.SqliteDatabase(os.path.join(SKRIPTPFAD, "messagebox.db3"))


class User(peewee.Model):
    uid = peewee.IntegerField(primary_key=True)
    name = peewee.CharField()

    class Meta:
        database = DB


class Message(peewee.Model):
    message_id = peewee.AutoField(primary_key=True)
    message_text = peewee.TextField()

    class Meta:
        database = DB


class MessageReadBy(peewee.Model):
    message_id = peewee.ForeignKeyField(Message, backref="message")
    uid = peewee.ForeignKeyField(User, backref="user")

    class Meta:
        primary_key = peewee.CompositeKey("message_id", "uid")
        database = DB


def add_message(text):
    Message.create(message_text=text)


def add_user(uid, name):
    User.create(uid=uid, name=name)



def get_new_message(uid):
    pass
    # Hier ist noch ein großes Fragezeichen


if __name__ == "__main__":
    DB.create_tables([User, Message, MessageReadBy])
    add_message("Testnachricht")
    add_user(1, "Test")
