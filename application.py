from flask import Flask
from flask import abort
from flask import g
from flask import render_template

import db
import time
from geopy.distance import vincenty

database = db.DB()
application = Flask(__name__)
query_count = 0
naive_cache = {}

@application.before_request
def before_request():
  g.start = time.time()

@application.after_request
def after_request(response):
    global query_count
    diff_seconds = time.time() - g.start
    diff_miliseconds = diff_seconds * 1000
    if (response.response.__class__ is list):
        diag = "Execution time: %.2fms | Database queries: %s" % (diff_miliseconds ,query_count)
        new_response = response.response[0].replace('__DIAGNOSTICS__', diag)
        response.set_data(new_response)
    return response

@application.route("/")
def home():
    if "cities" not in naive_cache:
        query_increment()
        cities = database.query("SELECT id, name, icon, latitude, longitude from city;")
        naive_cache["cities"] = cities
    else:
        cities = naive_cache["cities"]
    return render_template('main.html', cities=cities)


@application.route("/<city_id>")
def city(city_id):
    if "cities" not in naive_cache:
        query_increment()
        cities = database.query("SELECT id, name, icon, latitude, longitude from city;")
        naive_cache["cities"] = cities
    else:
        cities = naive_cache["cities"]
    if city_id not in naive_cache:
        city = filter(lambda c: c['id'] == city_id, cities)
        if len(city) < 1:
            abort(404)
        latlng = (city[0]['latitude'], city[0]['longitude'])

        if "airports" not in naive_cache:
            query_increment()
            airports = database.query("SELECT name, latitude, longitude from airport;")
            naive_cache["airports"] = airports
        else:
            airports = naive_cache["airports"]
        for airport in airports:
            airport['distance'] = vincenty((airport['latitude'], airport['longitude']), latlng).miles
        closest = sorted(airports, key=lambda x: x['distance'])[:5]
        naive_cache[city_id] = closest
    else:
        closest = naive_cache[city_id]
    return render_template('main.html', cities=cities, airports=closest)

def query_increment():
    global query_count
    query_count = query_count + 1


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()
