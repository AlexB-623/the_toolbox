from base import db, login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

#create admin user functionality
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(20), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)

    @classmethod
    def check_email(cls, email):
        #query db to see if email exists
        return db.session.query(db.exists().where(cls.email == email)).scalar()

    @classmethod
    #confirm this works
    def check_username(cls, username):
        #query db to see if uname exists
        return db.session.query(db.exists().where(cls.username == username)).scalar()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# need to get the event field flattened and expanded to HTTP Code, Target, and event details separately.
# Maybe add IP address too
# Join on userID and handle anon users
class Log_Entry(db.Model):
    __tablename__ = 'log_entries'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=False, default=datetime.now)
    #the user relevant to the logged activity, if known
    user_id = db.Column(db.String(20), unique=False, index=True)
    #the part of the application where the action occurred
    domain = db.Column(db.String(20), unique=False, index=True)
    #logged info
    event = db.Column(db.String(500), unique=False, index=True)

    def __init__(self, timestamp, user_id, domain, event):
        self.timestamp = timestamp
        self.user_id = user_id
        self.domain = domain
        self.event = event

    def to_dict(self):
        #convert model to dict
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'domain': self.domain,
            'event': self.event
        }



