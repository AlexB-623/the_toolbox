from datetime import datetime
from os import getcwd
from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
import json, random, markdown, uuid
from flask_login import login_required, current_user
from base import db
from base.decorators import admin_required
from base.lumberjack.views import lumberjack_do
from base.models import WeatherRequest, User
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
        # log it just in case
        job_id = str(uuid.uuid4())
        lumberjack_do(datetime.utcnow(), current_user, "the usual weather", {"type": "Submission",
                                                                             'User-Submitted city': form.city.data,
                                                                             'GPS Coordinates': str((form.latitude,
                                                                                                 form.longitude)),
                                                                             'Decoded City': form.decoded_city,
                                                                             'Decoded State': form.decoded_state,
                                                                             'Decoded Country Code': form.decoded_country_code,
                                                                             'job_id': job_id,
                                                                             'date': form.date.data})
        #commit to database
        weather_request = WeatherRequest(requesting_user=current_user.id,
                                         requested_month=form.date.data.month,
                                         requested_day=form.date.data.day,
                                         submitted_date=datetime.utcnow(),
                                         submitted_city=form.city.data,
                                         gps_coordinates=str((form.latitude, form.longitude)),
                                         decoded_city=form.decoded_city,
                                         decoded_state=form.decoded_state,
                                         decoded_country=form.decoded_country_code,
                                         job_id=job_id,
                                         job_status="Pending"
                                         )
        db.session.add(weather_request)
        db.session.commit()
        flash("Thanks for your submission!")
        return redirect(url_for('the_usual_weather.report_detail', job_id=job_id))
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field} error: {error}", "danger")
    return render_template('the_usual_weather_submit.html', form=form)


@the_usual_weather_blueprint.route('/report-list', methods=['GET'])
@login_required
def report_list():
    #get submitted jobs and shows progress
    #auto-refresh
    raw_list = db.session.execute(
        db.select(WeatherRequest).order_by(WeatherRequest.submitted_date.desc())
    ).scalars()
    pretty_list = [weather_request.to_dict() for weather_request in raw_list]
    #need a user class method for getting username by id
    for report in pretty_list:
        username = db.session.execute(db.select(User.username).filter_by(id=report['requesting_user'])).scalar_one()
        report['requesting_user'] = str(username)
    #we need to refresh the page every few minutes
    return render_template('the_usual_weather_report_list.html', pretty_list=pretty_list)

@the_usual_weather_blueprint.route('/report-detail/<job_id>', methods=['GET'])
@login_required
def report_detail(job_id):
    # takes a <job id> in the URL and returns the results
    #<job id> = weather_request.id

    #will need a new table in the db for saving/loading the API results

    # let's start by just loading a page with the request  as "pending, please refresh to check status"
    # this starts the job
    # when the job is done, you see results during a refresh

    #we need a method for checking if any jobs have been submitted and running them.
    # Maybe we just redirect here and conditionally run the job if it hasn't already been run
    #page should auto-refresh every 30 sec while job is incomplete
    report = db.session.execute(db.select(WeatherRequest).filter_by(job_id=job_id)).scalar()
    report_request = report.to_dict()
    # need a user class method for getting username by id
    username = db.session.execute(db.select(User.username).filter_by(id=report_request['requesting_user'])).scalar_one()
    report_request['requesting_user'] = str(username)
    if report_request['job_status'] != "Complete":
        #start job
        return render_template('the_usual_weather_report_detail.html',
                               report_request=report_request)
    else:
        #fetch the report and get it prepared for display
        return render_template('the_usual_weather_report_detail.html',
                               report_request=report_request,
                               report=report)


#admin function:
#Remove old results - must remove both the request and the results at the same time.
@the_usual_weather_blueprint.route('manage-reports', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_reports():
    pass