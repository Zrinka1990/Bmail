from google.appengine.ext import ndb


class User(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    google_id = ndb.StringProperty()


class Message(ndb.Model):
    sender_id = ndb.StringProperty()
    receiver_id = ndb.StringProperty()
    title = ndb.StringProperty()
    message_text = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)