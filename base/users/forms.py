from flask_wtf import FlaskForm
from datetime import datetime
from base.models import User
from base.lumberjack.views import lumberjack_do
from flask_login import login_required, current_user
from wtforms import (StringField,
                     SubmitField,
                     EmailField,
                     PasswordField,
                     IntegerField,
                     ValidationError)
from wtforms.validators import DataRequired, EqualTo, Email, email

class RegistrationForm(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('pass_confirm', message='Passwords must match.')])
    pass_confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            lumberjack_do(datetime.utcnow(), current_user, "users",f'Someone tried to register with an existing email {field.data.lower()}.')
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.lower()).first():
            lumberjack_do(datetime.utcnow(), current_user, "users", f'Someone tried to register with an existing username {field.data.lower()}.')
            raise ValidationError('Username already registered.')

class LoginForm(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')