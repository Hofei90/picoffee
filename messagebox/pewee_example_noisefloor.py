import peewee
#import sqlite3

db = peewee.SqliteDatabase(':memory:')


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(BaseModel):
    name = peewee.CharField(unique=True)


class Message(BaseModel):
    text = peewee.TextField()


class MessageReadBy(BaseModel):
    message = peewee.ForeignKeyField(Message, backref='messages')
    user = peewee.ForeignKeyField(User, backref='users')

    class Meta:
        primary_key = peewee.CompositeKey('message', 'user')


db.create_tables([User, Message, MessageReadBy])


def mark_message_as_read(user_id=None, message_id=None):
    MessageReadBy.create(message=message_id, user=user_id)


# drei Nutzer anlegen
rainer = User(name='Rainer Titan')
rainer.save()
User.create(name='Otto Normal')
volker = User(name='Volker Racho')
volker.save()
# drei Nachrichten anlegen
m = Message(text='Hallo Welt')
m.save()
Message.create(text='Du brauchst Kaffee')
Message.create(text='Der Kaffee wird nächste Woche teurer')
# erste Nachricht für Raine rTitan als gelesen markieren
mark_message_as_read(user_id=rainer.id, message_id=m.id)
# Alle Nachrichten für Volker Racho als gelesen markieren
for message in Message.select():
    mark_message_as_read(user_id=volker.id, message_id=message.id)
# ungelesene Nachrichten anzeigen - Methode 1 ohne Nutzung von `backref`
for u in User.select():
    messages = MessageReadBy.select().join(User).where(User.id == u.id)
    read_messages = [message.message.id for message in messages]
    if read_messages:
        unread_messages = Message.select().where(Message.id.not_in(read_messages))
    else:
        unread_messages = Message.select()
    print('Ungelesene Nachrichten für {}:'.format(u.name))
    if not unread_messages.exists():
        print('Keine neuen Nachrichten!')
    else:
        for unread_message in unread_messages:
            print(unread_message.text)
            mark_message_as_read(message_id=unread_message.id, user_id=u.id)
    print('-' * 20)

##ungelesen Nachrichten anzeigen - Methode 2 via `backref`
# for u in User.select():
#    user = User.get(User.name==u.name)
#    read_messages = [message.message.id for message in user.users]
#    #ab gleicher Code wie oben
