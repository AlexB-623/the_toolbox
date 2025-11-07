from flask_wtf import FlaskForm
#from base.models import weather model
from wtforms import (StringField,
                     SubmitField,
                     IntegerField,
                     ValidationError)
from wtforms.validators import DataRequired, EqualTo

class WeatherSubmitForm(FlaskForm):
    city = StringField('City', validators=[DataRequired()])