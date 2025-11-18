from base import db
from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
import markdown
import json, random
from os import getcwd
from flask_login import login_required, current_user
from os import getcwd

from base.decorators import admin_required
from base.models import Log_Entry, User
cwd = getcwd()
lumberjack_blueprint = Blueprint('lumberjack', __name__, template_folder='templates/lumberjack')


def lumberjack_do(timestamp, user_id, domain, event):
    """
    Takes timestamp, user_id, domain, and event, and produces a log entry
    :param timestamp: datetime.utcnow()
    :param user_id: current_user (can be authenticated or anonymous)
    :param domain: typically the blueprint being loaded
    :param event: notes about what is being logged
    :return: True if successful, False otherwise
    """
    try:
        # Check if user is authenticated (not anonymous)
        if user_id and user_id.is_authenticated:
            user = user_id.id
        else:
            user = None

        log_entry = Log_Entry(
            timestamp=timestamp,
            user_id=user,
            domain=str(domain).title()[:20],
            event=str(event)[:500]
        )

        db.session.add(log_entry)
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Logging error: {e}")
        return False


@lumberjack_blueprint.route('/')
def lumberjack():
    with open (f'{cwd}/lumberjack/data/about.txt', 'r') as f:
        md_about = f.read()
        f.close()
        about = markdown.markdown(md_about)
    return render_template('lumberjack_home.html', about=about)


@lumberjack_blueprint.route('/view_logs')
@login_required
def view_logs():
    #basic page for seeing last X events
    #export to CSV
    # add pagination to limit number of logs returned, default = 100
    # raw_logs = db.session.execute(db.select(Log_Entry).order_by(Log_Entry.timestamp.desc())).scalars()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    pagination = db.paginate(
        db.select(Log_Entry).order_by(Log_Entry.timestamp.desc()),
        page=page,
        per_page=per_page,
        error_out=False
    )
    raw_logs = pagination.items
    #raw logs get refined into Lumber
    lumber = [log_entry.to_dict() for log_entry in raw_logs]
    #I should make this a class method on Users
    for board in lumber:
        if "None" in str(board['user_id']):
            board['user_id'] = 'Anonymous User'
        else:
            username = db.session.execute(db.select(User.username).filter_by(id=board['user_id'])).scalar_one()
            board['user_id'] = str(username)
    return render_template('lumberjack_viewer.html', lumber=lumber, pagination=pagination)


@lumberjack_blueprint.route('/filter_logs', methods=['GET', 'POST'])
@login_required
def filter_logs():
    #complex page for filtering logs
    #export filtered to CSV
    pass


@lumberjack_blueprint.route('/manage_logs/', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_logs():
    #allows removal of old logs
    #requires admin user
    #look at log id of most recent log
    #subtract ~1000
    #delete any logs lt the current highest number
    pass





