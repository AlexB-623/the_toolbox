from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
import json, random
from os import getcwd
from flask_login import login_required, current_user

lumberjack_blueprint = Blueprint('lumberjack', __name__, template_folder='templates/lumberjack')
def lumberjack_do(timestamp, user_id, domain, event):
    # timestamp, user_id, domain, and event, and produces a log entry
    # lumberjack_do(datetime.utcnow(), current_user, "", )
    # maybe find a way to use an ENV variable to enable and disable this
    log_entry = {'timestamp': str(timestamp),
                 'user_id': str(user_id), #tie this to the username
                 'domain': str(domain).title(),
                 'event': str(event)} #trim this to match the length of the model field
    print(log_entry)
    #need to get this adding to a database
    return None


@lumberjack_blueprint.route('/')
def lumberjack():
    return render_template('lumberjack_home.html')


@lumberjack_blueprint.route('/view_logs')
def view_logs():
    #basic page for seeing last X events
    #export to CSV
    pass


@lumberjack_blueprint.route('/filter_logs', methods=['GET', 'POST'])
def filter_logs():
    #complex page for filtering logs
    #export filtered to CSV
    pass


@lumberjack_blueprint.route('/manage_logs/', methods=['GET', 'POST'])
def manage_logs():
    #allows removal of select logs
    #requires admin user
    pass





