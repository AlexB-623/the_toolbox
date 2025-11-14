from base import db, login_manager
from sqlalchemy import func
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
    is_admin = db.Column(db.Boolean, default=False)
    registration_date = db.Column(db.DateTime, nullable=True)
    last_login_date = db.Column(db.DateTime, nullable=True)
    banned = db.Column(db.Boolean, default=False)
    expired_password =db.Column(db.Boolean, default=False)

    def __init__(self, email, username, password, registration_date):
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.registration_date = registration_date

    def to_dict(self):
        return {
            'id': int(self.id),
            'email': self.email,
            'username': self.username,
            'is_admin': self.is_admin,
            'registration_date': self.registration_date.strftime('%m/%d/%y'),
            'last_login': self.last_login_date.strftime('%m/%d/%Y %H:%M'),
            'banned': self.banned,
            'expired_password': self.expired_password
        }

    @property
    def has_admin_access(self):
        from flask import current_app
        # Check database flag OR env variable
        admin_emails = current_app.config.get('ADMIN_EMAIL', [])
        return self.is_admin or self.email in admin_emails

    def sync_admin_status(self):
        """Update is_admin flag based on environment variable."""
        from flask import current_app
        admin_emails = current_app.config.get('ADMIN_EMAIL', [])
        should_be_admin = self.email in admin_emails

        if should_be_admin and not self.is_admin:
            self.is_admin = True
            return True  # Changed
        return False  # No change


    @classmethod
    def check_email(cls, email):
        #query db to see if email exists
        return db.session.query(db.exists().where(cls.email == email)).scalar()

    @classmethod
    def check_username(cls, username):
        #query db to see if uname exists
        return db.session.query(db.exists().where(func.lower(cls.username) == func.lower(username))).scalar()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class BouncerList(db.Model):
    __tablename__ = 'bouncer_list'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)

    def __init__(self, email):
        self.email = email


# need to get the event field flattened and expanded to HTTP Code, Target, and event details separately.
# Maybe add IP address too
# Should not have an underscore - may need to do a branch for a safe fix
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
    #these cover the month and day the user wants to know about
    requested_month = db.Column(db.Integer, index=False)
    requested_day = db.Column(db.Integer, index=False)
    #the date the user submitted the request
    submitted_date = db.Column(db.DateTime, index=False, default=datetime.now)
    #the string that the user entered for city
    submitted_city = db.Column(db.String(30), index=True)
    #all 4 of the below cover the geo details that we inferred from the user's city
    gps_coordinates = db.Column(db.String(50), index=True)
    decoded_city = db.Column(db.String(50), index=True)
    decoded_state = db.Column(db.String(50), index=True)
    decoded_country = db.Column(db.String(50), index=True)
    #tracking info
    job_id = db.Column(db.String(50), index=True)
    job_status = db.Column(db.String(50), index=True, default="Pending")
    #I may need some way to track elapsed time to note long-running jobs

    def __init__(self, requesting_user,
                 requested_month,
                 requested_day,
                 submitted_date,
                 submitted_city,
                 gps_coordinates,
                 decoded_city,
                 decoded_state,
                 decoded_country,
                 job_id,
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
        self.job_id = job_id
        self.job_status = job_status


    def to_dict(self):
        #convert model to dict
        return {
            'id': self.id,
            'requesting_user': self.requesting_user,
            'submitted_date': self.submitted_date.strftime('%m/%d/%Y'),
            'requested_date': str(f'{self.requested_month}-{self.requested_day}'),
            'requested_city': self.submitted_city,
            'gps_coordinates': self.gps_coordinates,
            'decoded_city': self.decoded_city,
            'decoded_state': self.decoded_state,
            'decoded_country': self.decoded_country.upper(),
            'job_id': self.job_id,
            'job_status': self.job_status
        }


#need to determine how to join with the Request table so they are linked
# think about how to handle db table drops - can we generate a unique token for job_id? UUID?
# class WeatherReport(db.Model):
#     __tablename__ = 'weather_reports'
#     id = db.Column(db.Integer, primary_key=True)