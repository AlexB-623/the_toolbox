import datetime
from os import getcwd

import pandas as pd
from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash
import json, random, markdown, uuid
from flask_login import login_required, current_user
from base import db
from base.decorators import admin_required
from base.lumberjack.views import lumberjack_do
from base.models import User, WeatherRequest, WeatherReport, WeatherAnalysis
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
        #May need to verify we can get to Nominatim to take a submission
        job_id = str(uuid.uuid4())
        lumberjack_do(current_user, "the usual weather", {"type": "Submission",
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
                                         submitted_date=datetime.datetime.now(datetime.UTC),
                                         submitted_city=form.city.data,
                                         gps_coordinates=str((form.latitude, form.longitude)),
                                         decoded_city=form.decoded_city,
                                         decoded_state=form.decoded_state,
                                         decoded_country=form.decoded_country_code,
                                         decoded_timezone=form.decoded_timezone,
                                         job_id=job_id,
                                         job_status="Pending"
                                         )
        db.session.add(weather_request)
        db.session.commit()
        flash("Thanks for your submission!", "success")
        return redirect(url_for('the_usual_weather.report_detail', job_id=job_id))
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field} error: {error}", "warning")
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
    report_request = db.session.execute(db.select(WeatherRequest).filter_by(job_id=job_id)).scalar().to_dict()
    #report_request = report_detail.to_dict()
    # need a user class method for getting username by id
    username = db.session.execute(db.select(User.username).filter_by(id=report_request['requesting_user'])).scalar_one()
    report_request['requesting_user'] = str(username)
    if report_request['job_status'] != "Complete":
        #refresh page periodically
        return render_template('the_usual_weather_report_detail.html',
                               refresh = 'true',
                               report_request=report_request)
    else:
        #fetch the report and get it prepared for display
        # report_data = db.session.execute(db.select(WeatherReport).filter_by(job_id=job_id)).scalar().to_dict()
        report_data_raw = WeatherReport.query.filter_by(job_id=job_id).all()
        report_data = pd.DataFrame([{k: v for k, v in r.__dict__.items() if k != '_sa_instance_state'} for r in report_data_raw])
        report_data = report_data.drop(['job_id', 'id'], axis=1)
        report_data = report_data[['date', 'temperature_2m', 'precipitation', 'wind_speed_10m', 'cloud_cover', 'apparent_temperature', 'relative_humidity_2m']]
        report_data = report_data.to_html()
        report_details = db.session.execute(db.select(WeatherAnalysis).filter_by(job_id=job_id)).scalar().to_dict()
        # report_details = report_details.to_dict()
        #add a "download" data button that collects the report data and exports to a CSV
        #add a "download" analysis button that collects the report analysis and exports to a CSV
        return render_template('the_usual_weather_report_detail.html',
                               refresh='false',
                               report_request=report_request,
                               report_details=report_details,
                               report_data=report_data)


#admin function:
#Remove old results - must remove both the request and the results at the same time.
@the_usual_weather_blueprint.route('manage-reports', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_reports():
    #functionality needed
    #adjust speed to avoid hitting call limits (build delay between calls and set it here)
    #suspend all job processing
    #fail a specific job
    pass