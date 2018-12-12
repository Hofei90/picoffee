import peewee
import os

SKRIPTPFAD = os.path.abspath(os.path.dirname(__file__))
DB = peewee.SqliteDatabase(os.path.join(SKRIPTPFAD, "messagebox.db3"))


class BaseModel(peewee.Model):
    class Meta:
        database = DB


class User(BaseModel):
    uid = peewee.IntegerField(primary_key=True)
    name = peewee.CharField()


class Message(BaseModel):
    text = peewee.TextField()


class MessageReadBy(BaseModel):
    message = peewee.ForeignKeyField(Message, backref="messages")
    user = peewee.ForeignKeyField(User, backref="users")

    class Meta:
        primary_key = peewee.CompositeKey("message", "user")


def add_message(text):
    Message.create(text=text)


def add_user(uid, name):
    User.create(uid=uid, name=name)


def get_new_message(uid):
    messages = MessageReadBy.select().join(User).where(User.uid == uid)
    read_messages = [message.message.id for message in messages]
    if read_messages:
        unread_messages = Message.select().where(Message.id.not_in(read_messages))
    else:
        unread_messages = Message.select()
    return unread_messages


def set_read_message(uid, message_id):
    user = User.select().where(User.uid == uid).get()
    MessageReadBy.create(message=message_id, user=user.uid)


def check_user(uid, name):

    try:
        user = User.select().where(User.uid == uid).get()
    except:
        add_user(uid, name)


def db_create_table():
    DB.create_tables([User, Message, MessageReadBy])


if __name__ == "__main__":
    db_create_table()
    # add_user(43742121810, "Johannes")
    # add_message("Testmessage")
    # add_message("Hallo Welt2")
    # unread_message = get_new_message(1)
    # for message in unread_message:
    #    print(message.text)
    #    set_read_message(1, message.id)
    # add_message("Hallo Welt")
    # set_read_message(1)
    # check_user(2)
