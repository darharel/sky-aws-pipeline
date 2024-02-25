from datetime import datetime
from flask import Flask, render_template, request, Response
import boto3
import requests
app = Flask(__name__)


class Weather:
    def __init__(self):
        self.city = ""
        self.country = ""
        self.longitude = 0.0
        self.latitude = 0.0
        self.days = []
        self.error_message = ""


@app.route('/send_to_dynamodb', methods=['POST'])
def send_to_dynamodb():

    dynamodb = boto3.client('dynamodb', region_name='eu-central-1')

    table = dynamodb.table('skydb')
    response = table.put_item(
        Item={
            'City': "Tel Aviv",
            'Country': "Israel",
            'Current_Temperature': "25"
        }
    )
    # return response
    return "Sent To DB"


@app.route('/download_image', methods=['GET'])
def download_image():
    try:
        response = requests.get("https://dhbucketapp.s3.eu-central-1.amazonaws.com/sky.jpeg")
        if response.status_code == 200:
            return Response(response.content, mimetype='image/jpeg', headers={"Content-Disposition":"attachment; filename=sky.jpeg"})
        else:
            return "Failed to download image from S3", 500
    except Exception as e:
        return str(e), 500


def get_geocode(search_query):
    """ Get the coordinates for a given city name"""
    weather = Weather()
    url_geocoding = "https://geocoding-api.open-meteo.com/v1/search"                # set the URL for API
    params = {"name": search_query, "count": 1, "language": "en", "format": "json"} # set the PARAMs for the API
    response = requests.get(url_geocoding, params=params)                           # request send to API
    if response.status_code == 200:
        data = response.json()
        if data.get('results') and data['results']:
            weather.longitude = data['results'][0]['longitude']
            weather.latitude = data['results'][0]['latitude']
            weather.city = data['results'][0]['name']
            weather.country = data['results'][0]['country']
        else:
            weather.error_message = "City not found. Please try again."
    return weather


def get_weather(weather):
    """ get the temperatures and humidity levels for next 7 days."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": weather.latitude,
        "longitude": weather.longitude,
        "current": ["temperature_2m", "relative_humidity_2m"],
        "daily": ["temperature_2m_max", "temperature_2m_min", "relative_humidity_2m_mean"]
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        # weather.days = []
        for i in range(7):
            weather.days.append({
                "week_day": datetime.strptime(data['daily']['time'][i], "%Y-%m-%d").strftime("%A"),
                "date": data['daily']['time'][i],
                "max_temp": data['daily']['temperature_2m_max'][i],
                "min_temp": data['daily']['temperature_2m_min'][i],
                "humidity": data['daily']['relative_humidity_2m_mean'][i],
            })
    return weather


@app.route('/', methods=['GET', 'POST'])
def index():
    input_from_user = request.form.get('search_query')        # Get input from user
    weather = get_geocode(input_from_user)                    # send it Geocode API to Get long/lat and country
    weather = get_weather(weather)                            # send long/lat to Open Meteo API get daily temperatures
    return render_template("index.html", weather=weather)


if __name__ == '__main__':
    app.run()

