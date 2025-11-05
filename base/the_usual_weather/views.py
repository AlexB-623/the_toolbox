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