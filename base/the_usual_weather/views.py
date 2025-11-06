from time import strftime

from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
import json, random
from datetime import datetime
from os import getcwd
from flask_login import login_required, current_user
from base.lumberjack.views import lumberjack_do

the_usual_weather_blueprint = Blueprint('the_usual_weather', __name__, template_folder='templates/the_usual_weather')

@the_usual_weather_blueprint.route('/')
def the_usual_weather():
    return render_template('the_usual_weather_home.html')

@the_usual_weather_blueprint.route('/submission', methods=['GET', 'POST'])
def submission():
    if request.method == 'POST': #form.validate on submit
        #validates details and submits to a db
        #logs what was submitted
        #starts process of retrieving data
        pass
    else:
        return render_template('the_usual_weather_submission.html')

@the_usual_weather_blueprint.route('/waiting-page', methods=['GET'])
def waiting_page():
    #get submitted jobs and shows progress
    #auto-refresh
    pass

@the_usual_weather_blueprint.route('/result', methods=['GET'])
def result():
    # takes a <job id> and returns the results
    pass

