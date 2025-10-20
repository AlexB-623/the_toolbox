from flask_wtf import FlaskForm
from base.models import User
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

    def check_dupe_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email already registered.')

    def check_dupe_username(self, email):
        if User.query.filter_by(username=email.data).first():
            raise ValidationError('Username already registered.')

class LoginForm(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')