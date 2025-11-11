from flask_wtf import FlaskForm
from geopy.geocoders import Nominatim
#from base.models import weather model
from wtforms import (StringField,
                     SubmitField,
                     IntegerField,
                     ValidationError,
                     DateField)
from wtforms.validators import DataRequired, EqualTo, length
from base.lumberjack.views import lumberjack_do
from base.users.views import current_user
from datetime import datetime



class WeatherSubmitForm(FlaskForm):
    city = StringField('City', validators=[DataRequired(), length(max=30)])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_city(self, field):
        # if city is valid, then it needs to also generate GPS coordinates for the submission
        location = Nominatim(timeout=10000, user_agent="Geopy Library")
        get_location = location.geocode(field.data)
        try:
            lat = round(float(get_location.latitude), 5)
            long = round(float(get_location.longitude), 5)
            # print(lat, long)
            #storing lat & long so we don't have to redo this
            self.latitude = lat
            self.longitude = long
        except AttributeError:
            lumberjack_do(datetime.utcnow(), current_user, "the usual weather", {"type": "Invalid City", 'Submitted City': field.data})
            raise ValidationError('Invalid city name. Please check your spelling and try again.')
        location_details = location.reverse((lat, long))
        location_details_raw = location_details.raw
        #since city names are not unique, we should reverse lookup the coordinates to give a more descriptive location
        #need to account for non-english characters in the names
        try:
            self.decoded_city = location_details_raw['address']['city']
        except:
            self.decoded_city = "City not found - possibly an unincorporated location or other anomalous location"
        try:
            self.decoded_state = location_details_raw['address']['state']
        except:
            self.decoded_state = "State not found - possibly a federal territory or other anomalous location"
        try:
            self.decoded_country_code = location_details_raw['address']['country_code']
        except:
            self.decoded_country_code = "Is this Antarctica? I haven't tested for Antarctica."