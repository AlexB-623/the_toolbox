from base import db
from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
import json, random
from os import getcwd
from flask_login import login_required, current_user

from base.models import Log_Entry, User

lumberjack_blueprint = Blueprint('lumberjack', __name__, template_folder='templates/lumberjack')


def lumberjack_do(timestamp, user_id, domain, event):
    # timestamp, user_id, domain, and event, and produces a log entry
    # lumberjack_do(datetime.utcnow(), current_user, "", )
    # maybe find a way to use an ENV variable to enable and disable this
    # log_entry = {'timestamp': str(timestamp),
    #              'user_id': str(user_id),
    #              'domain': str(domain).title(),
    #              'event': str(event)}
    log_entry = Log_Entry(timestamp=timestamp,
                          user_id=str(user_id), #tie this to the username
                          domain=str(domain).title(),
                          event=str(event)) #trim this to match the length of the model field
    db.session.add(log_entry)
    db.session.commit()
    return None


@lumberjack_blueprint.route('/')
def lumberjack():
    return render_template('lumberjack_home.html')


@lumberjack_blueprint.route('/view_logs')
def view_logs():
    #basic page for seeing last X events
    #make the page prettier
    # render timestamp in readable format
    #export to CSV
    # add a URL functionality to limit number of logs returned - &results=1000 - default = 100
    raw_logs = db.session.execute(
        db.select(Log_Entry).order_by(Log_Entry.timestamp.desc())
    ).scalars()
    #raw logs get refined into Lumber
    lumber = [log_entry.to_dict() for log_entry in raw_logs]
    #since the tables are not joined, we should make the username prettier
    for board in lumber:
        if "Anonymous" in str(board['user_id']):
            board['user_id'] = 'Anonymous User'
        else:
            raw_id = str(board['user_id']).replace("<User ", "").replace(">", "")
            username = db.session.execute(db.select(User.username).filter_by(id=raw_id)).scalar_one()
            board['user_id'] = str(username)
    return render_template('lumberjack_viewer.html', lumber=lumber)


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





