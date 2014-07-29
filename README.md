Food Truck Locator API
===

## Project Information
* Project: Food Trucks
* Technical track: Back-end

### Technologies Used
* Python: I wrote the app in Python, which is my favorite language to code in. I've been coding in Python for about 4 years (splitting my time with other languages).
* Flask: I chose Flask for the web framework as it's lightweight and works well for a small project such as this. This was the first application I built using Flask (outside of the example application from the Flask tutorial).
* SQLite: For the database engine, I chose SQLite since it's fast and easy to set up. The database requirements for this app are minimal (e.g. data set is small and all contained in one small table, only read access is required, low volume traffic) so the feature set provided by SQLite is ample (plus we get the benefit of simplicity). Also since SQLite databases are file-based, they are portable and easy to deploy (to Heroku, for instance). I've used SQLite a couple times in previous projects.
* Heroku: I deployed my application to Heroku. I've never used Heroku before so I wanted to try it out.


### Trade-offs
* The app currently computes the distance for every food truck in our database (before sorting and filtering the results). This isn't a big issue now since the data set is small (655 food trucks) but will become problematic as the data set grows. We can find ways to reduce the number of distance computations we perform.
  * For example, if the user wants to get all food trucks within a 1 mile distance, instead of retrieving all food trucks from the database, calculating the distance for each, and filtering out trucks > 1 mile away, we can construct a bounding box around the search location (1 mile in each direction). We can determine the latitude and longitude ranges for this bounding box and only retrieve food trucks from the database that are located within the box (these are the only food trucks that potentially fall within a 1 mile of the search location). We then compute the distances for this smaller set, and sort and filter as we did before.
* If I had more time, I'd add more flexibilty to the location specification. The API only accepts latitude/longitude pairs, but it would be useful to also handle addresses, intersections, or even points of interest. 
* It also would be handy to be able to filter the results on other criteria, e.g. food items offered, food truck name.

### Resume
* https://drive.google.com/file/d/0Bw0LfFdBEwtPbE5ySFlyOURRSVU/edit?usp=sharing

===

## API Reference

Also at http://dl-food-truck-locator.herokuapp.com/

### Overview
* The Food Truck Locator API computes the distance of food trucks from an initial search location (provided by the user).
* By default, the API returns a list of food trucks sorted by proximity (nearest trucks first).
* However, a maximum distance can be specified to filter results based on distance from the search location.

### Data Retrieval
* API entry point: http://dl-food-truck-locator.herokuapp.com/food_trucks_api (method: GET)
  * e.g. http://dl-food-truck-locator.herokuapp.com/food_trucks_api?location=37.7904067199,-122.3992758861&max_dist=4.1
* The API returns a JSON response.
* Curl response
```
$ curl -i "http://dl-food-truck-locator.herokuapp.com/food_trucks_api?location=37.7901490737,-122.3986581846&max_dist=0.2&limit=2&offset=0"
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 601
Server: Werkzeug/0.9.6 Python/2.7.5
Date: Tue, 29 Jul 2014 01:18:17 GMT

{
  "items": [
    {
      "address": "50 01ST ST", 
      "distance": 0.0, 
      "food_items": "Cupcakes", 
      "id": 1, 
      "latitude": 37.7901490737, 
      "longitude": -122.3986581846, 
      "vendor": "Cupkates Bakery, LLC"
    }, 
    {
      "address": "525 MARKET ST", 
      "distance": 0.03819310144774475, 
      "food_items": "Hot Indian Chai", 
      "id": 421, 
      "latitude": 37.7904067199, 
      "longitude": -122.3992758861, 
      "vendor": "The Chai Cart"
    }
  ], 
  "location_query": "37.7901490737,-122.398658185", 
  "num_results": 2, 
  "total_results_found": 39
}
```

### Request Parameters
|Name|Description|Required|Default|
|---|-------|-----|-------|
|location|Latitude, longitude of the search location|Required|N/A|
|max_dist|Filter results that are located within max_dist of the search location (distance is specified in miles)|Optional|If not provided, all results are returned|
|offset|Index of first result|Optional|0|
|limit|Maximum number of results to return|Optional|10|


### Response Parameters
| Name | Description |
| ----- | ---------- |
| location_query	| Latitude, longitude of the user-specified search location |
| num_results | Number of results in the response |
| total_results_found | Total number of results matching search criteria |
| items | List of results |
| error | Errors encountered while processing the request |


