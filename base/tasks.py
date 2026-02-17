from base import db
from base.models import WeatherRequest


def process_weather_request(request):
    #api code
    #save to WeatherReport table
    pass

def process_pending_weather_requests(app):
    #query db for list of pending requests
    with app.app_context():
        raw_list = db.session.execute(
            db.select(WeatherRequest).filter_by(job_status='Pending').order_by(WeatherRequest.submitted_date.asc())
        ).scalars()
        pretty_list = [weather_request.to_dict() for weather_request in raw_list]
        print(pretty_list)
    #for loop thru reqs
        #execute process_weather_request(request)
    #stop
    #print("this works")
    pass