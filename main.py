import os
import jinja2
import webapp2
import json
from google.appengine.api import users
from models import User
from models import Message
from google.appengine.api import urlfetch

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if params is None:
            params = {}
        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            logged_in = True
            logout_url = users.create_logout_url('/')
            registered_user_list = User.query(User.google_id == user.user_id()).fetch(1)
            if len(registered_user_list) == 0:
                registered_user = User(name=user.nickname(), email=user.email(), google_id=user.user_id())
                registered_user.put()
            else:
                registered_user = registered_user_list[0]
            params = {"logged_in": logged_in, "logout_url": logout_url, "registered_user": registered_user}
        else:
            logged_in = False
            login_url = users.create_login_url('/')
            params = {"logged_in": logged_in, "login_url": login_url}
        return self.render_template("index.html", params=params)


class UserListHandler(BaseHandler):
    def get(self):
        google_user = users.get_current_user()
        if google_user is None:
            return webapp2.redirect("/")
        contacts = User.query().fetch()
        return self.render_template("compose.html", {"contacts": contacts})


class SendMessageHandler(BaseHandler):
    def get(self, user_id):
        message = Message.query().fetch()
        user = User.get_by_id(int(user_id))
        params = {"user": user, "message": message}
        return self.render_template("send_message.html", params=params)


class SentHandler(BaseHandler):
    def post(self, receiver_id):
        receiver = User.get_by_id(int(receiver_id))
        title = self.request.get("email_title")
        message = self.request.get("message_text")
        user = users.get_current_user()
        sender = User.query(User.google_id == user.user_id()).fetch(1)[0]
        new_message = Message(sender_id=str(sender.key.id()), receiver_id=receiver_id, title=title,
                              message_text=message)
        new_message.put()
        return self.render_template("sent.html", {"new_message": new_message, "receiver": receiver, "sender": sender})


class InboxHandler(BaseHandler):
    def get(self):
        google_user = users.get_current_user()
        if google_user is None:
            return webapp2.redirect("/")
        google_user_id = google_user.user_id()
        receiver = User.query(User.google_id == google_user_id).fetch(1)[0]
        messages = Message.query(Message.receiver_id == str(receiver.key.id())).fetch()
        sender_list = []
        for message in messages:
            sender = User.get_by_id(int(message.sender_id))
            sender_list.append(sender)
        return self.render_template("inbox.html", {"messages": messages, "sender_list": sender_list,
                                                   "len_messages": len(messages)})


class ReadEmail(BaseHandler):
    def get(self, email_id):
        email = Message.get_by_id(int(email_id))
        sender = User.get_by_id(int(email.sender_id))
        return self.render_template("read_email.html", {"email": email, "sender": sender})


class OutboxHandler(BaseHandler):
    def get(self):
        google_user = users.get_current_user()
        if google_user is None:
            return webapp2.redirect("/")
        google_user_id = google_user.user_id()
        sender = User.query(User.google_id == google_user_id).fetch(1)[0]
        messages = Message.query(Message.sender_id == str(sender.key.id())).fetch()
        receiver_list = []
        for message in messages:
            receiver = User.get_by_id(int(message.receiver_id))
            receiver_list.append(receiver)
        return self.render_template("outbox.html", {"messages": messages, "receiver_list": receiver_list,
                                                    "len_messages": len(messages)})


class WeatherHandler(BaseHandler):
    def get(self):
        google_user = users.get_current_user()
        if google_user is None:
            return webapp2.redirect("/")
        url = "http://api.openweathermap.org/data/2.5/weather?q=Zagreb,cro&units=metric&appid=f5107885bf94ab9538be1c79dab3b654"
        result = urlfetch.fetch(url)
        weather_info = json.loads(result.content)
        params = {"weather_info": weather_info}
        self.render_template("weather.html", params)


app = webapp2.WSGIApplication([
    webapp2.Route("/", MainHandler),
    webapp2.Route("/compose", UserListHandler),
    webapp2.Route("/<user_id:\d+>", SendMessageHandler),
    webapp2.Route("/<receiver_id:\d+>/sent", SentHandler),
    webapp2.Route("/inbox", InboxHandler),
    webapp2.Route("/<email_id:\d+>/read", ReadEmail),
    webapp2.Route("/outbox", OutboxHandler),
    webapp2.Route('/weather', WeatherHandler),
], debug=True)
