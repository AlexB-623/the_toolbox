from base import db, login_manager
from datetime import datetime
from time import strftime
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
    # Foreign key that allows NULL for anonymous users
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=False, nullable=True, index=True)
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


class WeatherRequest(db.Model):
    __tablename__ = 'weather_requests'
    id = db.Column(db.Integer, primary_key=True)
    requesting_user = db.Column(db.Integer, db.ForeignKey('users.id'), unique=False, nullable=True, index=True)
    requested_month = db.Column(db.Integer, index=False)
    requested_day = db.Column(db.Integer, index=False)
    submitted_date = db.Column(db.DateTime, index=False, default=datetime.now)
    submitted_city = db.Column(db.String(30), index=True)
    gps_coordinates = db.Column(db.String(50), index=True)
    decoded_city = db.Column(db.String(50), index=True)
    decoded_state = db.Column(db.String(50), index=True)
    decoded_country = db.Column(db.String(50), index=True)
    job_status = db.Column(db.String(50), index=True, default="Pending")


    def __init__(self, requesting_user,
                 requested_month,
                 requested_day,
                 submitted_date,
                 submitted_city,
                 gps_coordinates,
                 decoded_city,
                 decoded_state,
                 decoded_country,
                 job_status):
        self.requesting_user = requesting_user
        self.requested_month = requested_month
        self.requested_day = requested_day
        self.submitted_date = submitted_date
        self.submitted_city = submitted_city
        self.gps_coordinates = gps_coordinates
        self.decoded_city = decoded_city
        self.decoded_state = decoded_state
        self.decoded_country = decoded_country
        self.job_status = job_status


    def to_dict(self):
        #convert model to dict
        return {
            'id': self.id,
            'requesting_user': self.requesting_user,
            'submitted_date': self.submitted_date.strftime('%d/%m/%Y'),
            'requested_date': str(f'{self.requested_month}-{self.requested_day}'),
            'submitted_city': self.submitted_city,
            'gps_coordinates': self.gps_coordinates,
            'decoded_city': self.decoded_city,
            'decoded_state': self.decoded_state,
            'decoded_country': self.decoded_country.upper(),
            'job_status': self.job_status
        }


#need to determine how to join with the Request table so they are linked
# class WeatherReport(db.Model):
#     __tablename__ = 'weather_reports'
#     id = db.Column(db.Integer, primary_key=True)