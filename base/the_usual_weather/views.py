from time import strftime
from datetime import datetime
from geopy.geocoders import Nominatim
from os import getcwd
from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
import json, random, markdown
from flask_login import login_required, current_user
from base.lumberjack.views import lumberjack_do
from base.the_usual_weather.forms import WeatherSubmitForm


cwd = getcwd()

the_usual_weather_blueprint = Blueprint('the_usual_weather', __name__, template_folder='templates/the_usual_weather')

@the_usual_weather_blueprint.route('/')
def the_usual_weather():
    with open (f'{cwd}/the_usual_weather/data/about.txt', 'r') as f:
        md_about = f.read()
        f.close()
        about = markdown.markdown(md_about)
    return render_template('the_usual_weather_home.html', about=about)

@the_usual_weather_blueprint.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    form = WeatherSubmitForm()
    if form.validate_on_submit():
        #commit to database
        lumberjack_do(datetime.utcnow(), current_user, "the usual weather", {"type": "Submission",
                                                                             'User-Submitted city': form.city.data,
                                                                             'GPS Coordinates': (form.latitude, form.longitude),
                                                                             'Decoded City': form.decoded_city,
                                                                             'Decoded State': form.decoded_state,
                                                                             'Decoded Country Code': form.decoded_country_code,
                                                                             'date': form.date.data})
        flash("Thanks for your submission!")
        return redirect(url_for('the_usual_weather.report_list'))
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field} error: {error}", "danger")
    return render_template('the_usual_weather_submit.html', form=form)


@the_usual_weather_blueprint.route('/report-list', methods=['GET'])
def report_list():
    #get submitted jobs and shows progress
    #auto-refresh
    return render_template('the_usual_weather_report_list.html')

@the_usual_weather_blueprint.route('/results', methods=['GET'])
def results():
    # takes a <job id> and returns the results
    pass

