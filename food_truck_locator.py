"""
Food Truck Locator API

"""

import operator

from flask import Flask, jsonify, g, request, abort, make_response, url_for, render_template
import sqlite3
from geopy.point import Point
from geopy.distance import distance


app = Flask(__name__)

# Config
app.config.update(
    DEBUG = True,
    DATABASE = 'food_trucks.db',
    DEFAULT_LIMIT = 10,
)

## Database functions
def get_db():
    """ Return an existing db connection or set up a new one if one doesn't exist
        http://flask.pocoo.org/docs/patterns/sqlite3/
    """
    if not hasattr(g, 'db_conn'):
        g.db_conn = connect_db()
    return g.db_conn

def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'], check_same_thread=False)
    # Set the return type as sqlite3.Row objects which provide name-based access
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=()):
    cursor = get_db().cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    return results

@app.teardown_appcontext
def close_db(exception):
    if hasattr(g, 'db_conn'):
        g.db_conn.close()


## Request-handling functions
@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/food_trucks_api', methods=['GET'])
def get_items():
    # Retrieve request parameters
    # Location to search around (latitude/longitude pair expected)
    location = request.args.get('location')
    if not location:
        error = {'type': 'Missing location',
                 'message': 'Please provide latitude/longitude of the search location, e.g. location=40.779979, -73.980274',
                }
        abort(make_response(jsonify({'error': error}), 400))

    # Attempt to parse the latitude/longitude
    try:
        coords = Point(location.split(','))
    except ValueError:
        error = {'type': 'Invalid location',
                 'message': 'Please provide a valid latitude/longitude for the search location, e.g. location=40.779979, -73.980274',
                }
        abort(make_response(jsonify({'error': error}), 400))

    # Max distance -- only return results within {} miles of search location
    max_dist = request.args.get('max_dist')
    # Testing specifically for None since zero is an acceptable value
    if max_dist is not None:
        try:
            max_dist = float(max_dist)
            if max_dist < 0:
                max_dist = None
        except ValueError:
            max_dist = None

    # Max number of results to return
    default_limit = app.config.get('DEFAULT_LIMIT', 10)
    try:
        limit = int(request.args.get('limit', default_limit))
        # Force negative limit value to default
        if limit < 0:
            limit = default_limit
    except ValueError:
        limit = default_limit

    # Offset of the first result to return (e.g. for pagination) (default: 0)
    try:
        offset = int(request.args.get('offset', 0))
        # Force negative offset to default
        if offset < 0:
            offset = 0
    except ValueError:
        offset = 0

    # Get trucks
    trucks, total_results_found = retrieve_matching_trucks(coords, max_dist, offset, limit)

    # Prepare the response
    response = {'num_results': len(trucks),
                'total_results_found': total_results_found,
                'location_query' : "{},{}".format(*coords),
                'items': trucks,
               }

    return jsonify(response)


def retrieve_matching_trucks(location, max_dist, offset, limit):
    """Retrieve and filter results based on request criteria
       Input:
           location: Point object with latitude/longitude of the search location
           max_dist: Only return results with a certain distance of the search location
           offset: Index of the first result to return
           limit: Maximum number of results to return
    """

    rows = execute_query('select * from food_trucks')
    trucks = map(dict, rows)

    # Compute distance (in miles) of each truck from the search location
    # For trucks without coordinates, set the distance to an empty string
    for truck in trucks:
        if truck['latitude'] and truck['longitude']:
            truck['distance'] = distance(location, Point(truck['latitude'], truck['longitude'])).miles
        else:
            truck['distance'] = ""

    # Filter by distance
    # This also filters out trucks without distance data (i.e. an empty string)
    if max_dist is not None:
        trucks = filter(lambda x: x['distance'] <= max_dist, trucks)

    # Sort by nearest
    trucks = sorted(trucks, key=operator.itemgetter('distance'))

    # Keep track of the total number of results found
    total_results_found = len(trucks)

    # Offset and cap the results
    trucks = trucks[offset:offset+limit]

    return trucks, total_results_found


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
