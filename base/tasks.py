from base import db
from base.models import WeatherRequest, WeatherReport, WeatherAnalysis
from base.lumberjack.views import lumberjack_do
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import requests, openmeteo_requests, requests_cache, datetime, re
import pandas as pd
from pandas.core.interchange import dataframe
from openmeteo_requests import OpenMeteoRequestsError
from retry_requests import retry

#this page contains all functions needed to handle the background processing of a weather request

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
open_meteo = openmeteo_requests.Client(session = retry_session)


def process_pending_weather_requests(app):
    #query db for list of pending requests
    with app.app_context():
        #add logic for retry
        request_list = db.session.execute(
            db.select(WeatherRequest).filter_by(job_status='Pending').order_by(WeatherRequest.submitted_date.asc())
        ).scalars().all()
        #check num of jobs retrieved
        jobs = len(request_list)


        if jobs < 1:
            pass
        else:
            lumberjack_do(datetime.datetime.now(datetime.UTC), None, "Weather Processor",
                          f"{jobs} Pending Weather Requests")
            # # Check if OpenMeteo is currently responding:
            # try:
            #     api_check = requests.get("https://archive-api.open-meteo.com/v1/archive")
            # except:
            #
            # if api_check.status_code != 200:
            #     lumberjack_do(datetime.datetime.now(datetime.UTC), None, "Weather Processor", f"OpenMeteo not responding, aborting. HTTP: {api_check.status_code}.")
            #     pass
            #for loop thru reqs
            for request in request_list:
                # extract necessary data from req
                location = f"{request.decoded_city}, {request.decoded_state}, {request.decoded_country.upper()}"
                #taking the existing coords and making into a tuple for ease of use
                listgps = list(request.gps_coordinates.replace("(", "").replace(")", "").split(","))
                listgps[0] = float(listgps[0])
                listgps[1] = float(listgps[1])
                gps_coords = tuple(listgps)
                # print(type(gps_coords))
                month = request.requested_month
                day = request.requested_day
                timezone = request.decoded_timezone
                # log req start
                lumberjack_do(datetime.datetime.now(datetime.UTC), None, "Weather Processor",
                              f"Retrieving Weather for: {location}({str(gps_coords)}), {month}/{day} - Job ID: {request.job_id}")
                # update weather request to set job in progress
                request.job_status = "Processing"
                db.session.commit()
                #try/except
                try:
                    process_weather_request(gps_coords, location, timezone, month, day, request.job_id)
                    request.job_status = "Complete"
                    db.session.commit()
                except:
                    request.job_status = "Failed"
                    db.session.commit()
                    continue
                #log loop complete
                lumberjack_do(datetime.datetime.now(datetime.UTC), None, "Weather Processor", f"Background job completed.")
                pass
    #stop
    pass


def process_weather_request(gps_coords, location, timezone, month, day, job_id):
    #if check for errors,then abort, else return
    job_result = make_master_dataframe(input_location=gps_coords, month=month, day=day, job_id=job_id)
    if type(job_result) != pd.DataFrame:
        #here we're checking to confirm that we actually got data back and not an API error.
        raise Exception("API Error")
    else:
        lumberjack_do(datetime.datetime.now(datetime.UTC), None, "Weather Processor", f'Job ID: {job_id} - API retrieval completed.')
        # print("job run, attempting db commit")
        weather_report = job_result.to_dict(orient='records')
        db.session.bulk_insert_mappings(WeatherReport, weather_report)
        db.session.commit()
        lumberjack_do(datetime.datetime.now(datetime.UTC), None, "Weather Processor", f"Job ID: {job_id} - DB insert completed, performing analysis...")
        # print("db commit did not fail, I think")
        #perform analysis
        weather_analysis(job_result, job_id, month, day, location, timezone)
    pass


def weather_analysis(job_result, job_id, month, day, location, timezone):
    #localize the dataframe to the local time zone
    dataset = localize_dataframe(job_result, timezone)
    # calculate:
    # average daily low
    # average daily high
    daily_temps = dataset.groupby('Dates')['temperature_2m'].agg(
        daily_low='min',
        daily_high='max'
    )
    avg_low = daily_temps['daily_low'].mean()
    avg_high = daily_temps['daily_high'].mean()
    daily_probability = dataset.groupby('Dates')[['wind_speed_10m', 'precipitation', 'cloud_cover']].max()
    # probablilty wind is not 0
    wind_probability = (daily_probability['wind_speed_10m'] >= 12.5).mean() * 100
    # average daily wind speed
    average_wind_speed = dataset[dataset['wind_speed_10m'] > 0]['wind_speed_10m'].mean()
    # probablilty clouds is not 0
    cloud_probability = (daily_probability['cloud_cover'] >= 55).mean() * 100
    # average daily cloud cover
    average_cloud_cover = dataset[dataset['cloud_cover'] > 0]['cloud_cover'].mean()
    # probablilty precip is not 0
    precipitation_probability = (daily_probability['precipitation'] > 0.2).mean() * 100
    # average daily precip
    daily_precipitation = dataset.groupby('Dates')['precipitation'].sum()
    average_precipitation = daily_precipitation[daily_precipitation >= 0.1].mean()
    #average_precipitation = dataset[dataset['precipitation'] > 0]['precipitation'].mean()

    weather_analysis = WeatherAnalysis(job_id=job_id,
                                       month=month,
                                       day=day,
                                       location=location,
                                       average_low=avg_low,
                                       average_high=avg_high,
                                       wind_probability=wind_probability,
                                       average_wind_speed=average_wind_speed,
                                       cloud_probability=cloud_probability,
                                       average_cloud_cover=average_cloud_cover,
                                       precipitation_probability=precipitation_probability,
                                       average_precipitation=average_precipitation
                                       )
    db.session.add(weather_analysis)
    db.session.commit()
    lumberjack_do(datetime.datetime.now(datetime.UTC), None, "Weather Processor", f"Job ID: {job_id} - Analysis written to DB")
    pass

def localize_dataframe(dataframe, timezone):
    """
    Takes a dataframe, converts times to local, then groups by hour for analysis
    :param dataframe:
    :return:
    """
    dataframe['local'] = dataframe['date'].dt.tz_localize('utc').dt.tz_convert(timezone)
    dataframe = dataframe.drop('date', axis=1)
    dataframe['Dates'] = pd.to_datetime(dataframe['local']).dt.date
    dataframe['Time'] = pd.to_datetime(dataframe['local']).dt.time
    dataframe = dataframe.drop('local', axis=1)
    return dataframe

def make_master_dataframe(input_location, month, day, job_id):
    """
    Whatever you use to gather the input from a user, be sure to do some kind of input validation to get real locations and dates.
    :param input_location: tuple, gps
    :param month: 1-12
    :param day: 1-31
    :param job_id: job being done
    :return: pandas dataframe with weather data for the requested city/date or returns a string as "error"
    """
    is_first_result = True
    # location = convert_location_to_gps(input_location)
    # if type(location) == str:
    #     return location
    years_to_call = generate_master_date_list(month, day)
    for year in years_to_call:
        year_data = call_for_data(latitude=input_location[0], longitude=input_location[1], start_date=year[-1], end_date=year[0], job_id=job_id)
        #check if the API call had an error and abort
        if year_data == "error":
            master_dataframe = "error"
            break
        if is_first_result:
            master_dataframe = make_dataframe(year_data, job_id)
            is_first_result = False
        else:
            year_dataframe = make_dataframe(year_data, job_id)
            master_dataframe = pd.concat([master_dataframe, year_dataframe])
    return master_dataframe


# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
def call_for_data(latitude, longitude, start_date, end_date, job_id):
    """
    calls the openmeteo API for historical weather data
    :param latitude:
    :param longitude:
    :param start_date:
    :param end_date:
    :param job_id
    :return: API response or "error"
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
		"latitude": latitude,
		"longitude": longitude,
		"start_date": start_date,
		"end_date": end_date,
		"hourly": ["temperature_2m", "precipitation", "cloud_cover", "wind_speed_10m"],
        #confirm the time zone
		"timezone": "UTC",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch"
	}
    try:
        responses = open_meteo.weather_api(url, params=params)
        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
    except OpenMeteoRequestsError as e:
        # Handle gracefully — log it, return a default, retry, etc.
        lumberjack_do(datetime.datetime.now(datetime.UTC), None, "Weather Processor", f"Error calling OpenMeteo API: {e}. Job ID: {job_id}")
        return "error"
        #need to pass the error up, revert the job, and abort the loop
    except Exception as e:
        # Catch any unexpected errors (network issues, etc.)
        lumberjack_do(datetime.datetime.now(datetime.UTC), None, "Weather Processor", f"Error calling OpenMeteo API: {e}. Job ID: {job_id}")
        return "error"
        # need to pass the error up, revert the job, and abort the loop
    return response


def make_dataframe(api_response, job_id):
    """
    takes the result of call for data and transforms it into a dataframe
    :param api_response:
    :return:
    """
    # we may need to handle NoneType if a given location doesn't have recorded data for a given time
    hourly = api_response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
    hourly_cloud_cover = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(3).ValuesAsNumpy()
    hourly_data = {"date": pd.date_range(
		start = pd.to_datetime(hourly.Time(), unit = "s"),
		end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
		freq = pd.Timedelta(seconds = hourly.Interval()),
		inclusive = "left"
	)}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["cloud_cover"] = hourly_cloud_cover
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["job_id"] = job_id


    return pd.DataFrame(data = hourly_data)


def generate_master_date_list(month, day):
    """
    takes a month and a day and generates a list of lists,
    each list generated by get_dates_to_call_for_year
    :param month: Int 1-12
    :param day: Int 1-31
    :return: list of dates
    for each list in the list [-1] would be the start date and [0] would be the end date
    """
    current_year = str(datetime.datetime.today())
    # Added a -1 to account for a day of year that has not yet occurred for current year
    # this means we cannot look at the current year. Is this okay?
    year_only = int(re.findall(r"(\d{,4})-.+", current_year)[0])-1
    #do we want to use 1950? may need to look at request limits.
    #we might be fine with the past 25 years
    year_set = range(year_only, 1980, -1)
    master_date_list = []
    for year in year_set:
        #need to implement a try except loop for handling leap year or other nonexistent dates
        single_year_dates = get_dates_to_call_for_year(year, month, day)
        #take the dates from
        master_date_list.append(single_year_dates)
    return master_date_list

loc = Nominatim(user_agent="Geopy Library")


def get_dates_to_call_for_year(year, month, day):
    """
    takes a year, month, and day, and returns a list of dates, 7 before and 7 after, for that year, accounting for leap year and next/last year
    :param year:
    :param month:
    :param day:
    :return: a list of dates, 7 before and 7 after
    for each list [-1] would be the start date and [0] would be the end date
    """
    base = datetime.date(year, month, day)
    date_list = [base - datetime.timedelta(days=x+1) for x in range(-8, 7)]
    date_list_pretty = []
    for i in date_list:
        date_list_pretty.append(str(i))
    return date_list_pretty
