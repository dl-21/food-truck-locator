"""
Food Truck Locator API

"""

import operator

from flask import Flask, jsonify, g, request, abort, make_response
import sqlite3
from geopy.point import Point
from geopy.distance import distance


app = Flask(__name__)

# Config
app.config.update(
    DEBUG = True,
    DATABASE = 'food_trucks.db'
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
    return 'hey!'


def retrieve_matching_trucks(location, max_dist, offset, limit):
    """Retrieve and filter results based on request criteria
       Input:
           location: Point object with search location coordinates
           max_dist: Only return results with a certain distance of the search location
           offset: Offset of the first result to return
           limit: Maximum number of results to send
    """

    rows = execute_query('select * from food_trucks')
    trucks = map(dict, rows) 

    # Compute distance (in miles) of each truck from the search location
    # For trucks without coordinates, set the distance to -1
    for truck in trucks:
        if truck['latitude'] and truck['longitude']:
            truck['distance'] = distance(location, Point(truck['latitude'], truck['longitude'])).miles
        else:
            truck['distance'] = ""

    # Filter by distance
    # With this filter, we skip trucks without distance data (i.e. an empty string)
    if max_dist is not None:
        trucks = filter(lambda x: x['distance'] <= max_dist, trucks)

    # Sort by nearest
    trucks = sorted(trucks, key=operator.itemgetter('distance'))

    # Offset and cap the results
    trucks = trucks[offset:offset+limit]
    
    return trucks


@app.route('/api/food_trucks', methods=['GET'])
def get_items():
    # Retrieve request parameters
    # Location to search around (latitude/longitude pair expected)
    location = request.args.get('location')
    if not location:
        error = {'category': 'Missing location',
                 'message': 'Please provide latitude/longitude of the search location, e.g. location=40.779979, -73.980274',
                }
        abort(make_response(jsonify({'error': error}), 400))

    # Attempt to parse the latitude/longitude
    try:
        coords = Point(location.split(','))
    except ValueError:
        error = {'category': 'Invalid location',
                 'message': 'Please provide a valid latitude/longitude for the search location, e.g. location=40.779979, -73.980274',
                }
        abort(make_response(jsonify({'error': error}), 400))

    # Max distance -- only return results within {} miles of search location
    max_dist = request.args.get('max_dist')
    if max_dist is not None:
        try:
            max_dist = float(max_dist)
        except ValueError:
            max_dist = None

    # Max number of results to return (default: 10)
    limit = request.args.get('limit', 10)
    try:
        limit = int(limit)
    except ValueError:
        limit = 10

    # Offset of the first result to return (e.g. for pagination) (default: 0)
    offset = request.args.get('offset', 0)
    try:
        offset = int(offset)
    except ValueError:
        offset = 0


    # Get trucks    
    trucks = retrieve_matching_trucks(coords, max_dist, offset, limit)

    # Prepare the response
    response = {'num_results': len(trucks),
                'location_query' : "{},{}".format(*coords),
                'items': trucks,
               }

    return jsonify(response)



if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
