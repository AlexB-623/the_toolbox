from flask_wtf import FlaskForm
from wtforms import (SubmitField,IntegerField)
from wtforms.validators import DataRequired, number_range

class LogCleanupByCount(FlaskForm):
    num_to_keep = IntegerField("Number of logs to keep", validators=[DataRequired(), number_range(20, 1000)], default=100)
    submit = SubmitField('Delete Logs')