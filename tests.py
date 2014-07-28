"""
Unit tests for the Food Truck Locator API
"""

import unittest
import json
import sqlite3
import food_truck_locator

class FoodTruckLocatorTestCase(unittest.TestCase):
    def setUp(self):
        """Connect to the database and retrieve the test client"""
        self.db_conn = food_truck_locator.connect_db()
        # Enable error progation to test client
        food_truck_locator.app.config['TESTING'] = True
        self.app = food_truck_locator.app.test_client()

    def tearDown(self):
        """Close the database connection"""
        self.db_conn.close()

    def test_good_location(self):
        """Verify that a valid location yields results"""
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        # We have results!
        self.assertTrue(data['num_results'] > 0)

    def test_missing_location(self):
        """Verify that we receive an error if no search location is given"""
        rv = self.app.get('/api/food_trucks')
        self.assertEqual(rv.status_code, 400)
        # Check error message
        data = json.loads(rv.data)
        self.assertIsNotNone(data.get('error'))
        self.assertEquals(data['error'].get('type'), 'Missing location')

    def test_invalid_location(self):
        """Verify that we receive an error if the search location is invalid"""
        # Test with non-latitude/longitude input 
        rv = self.app.get('/api/food_trucks?location=kljsfsfj')
        self.assertEqual(rv.status_code, 400)
        # Check error message
        data = json.loads(rv.data)
        self.assertIsNotNone(data.get('error'))
        self.assertEquals(data['error'].get('type'), 'Invalid location')

        # Test with only latitude
        rv = self.app.get('/api/food_trucks?location=39.001')
        self.assertEqual(rv.status_code, 400)
        # Check error message
        data = json.loads(rv.data)
        self.assertIsNotNone(data.get('error'))
        self.assertEquals(data['error'].get('type'), 'Invalid location')

    def test_limit(self):
        """Verify that the limit parameter is restricting the number of results returned"""
        # Verify that default number of items returned if limit parameter isn't provided
        default = food_truck_locator.app.config['DEFAULT_LIMIT']
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEquals(data['num_results'], default)

        # Check valid user-specified limit
        limit = 25
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846&limit=%d' % limit)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEquals(data['num_results'], limit)

    def test_bad_limit(self):
        """Verify that an invalid user-specified limit falls back on the default value"""
        default = food_truck_locator.app.config['DEFAULT_LIMIT']

        # Negative value 
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846&limit=-20')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEquals(data['num_results'], default)

        # Non-numeric value
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846&limit=ksdfjslf')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertEquals(data['num_results'], default)

    def test_max_dist(self):
        """Verify that the max_dist parameter is properly filtering the results"""
        max_dist = 0.1
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846&max_dist=%.10g' % max_dist)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        # Verify each result has a distance within our max_dist value
        for item in data.get('items', []):
            self.assertTrue(item['distance'] <= max_dist)

    def test_bad_max_dist(self):
        """Verify that a bad max_dist value doesn't cause a request to fail"""
        # Negative value
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846&max_dist=-0.001')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertTrue(data['num_results'] > 0)

        # Non-numeric value
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846&max_dist=ksfjsflj')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertTrue(data['num_results'] > 0)

    def test_offset(self):
        """Verify that changing the offset parameter shifts the result set, 
           e.g. for pagination
        """
        # Get the first 10 results (offset=0 by default)
        rv = self.app.get('/api/food_trucks?location=37.7905483182,-122.4003336737&limit=10')
        data = json.loads(rv.data)
        first_set_ids = {item.get('id') for item in data.get('items', [])}

        # Get next 10 results
        rv = self.app.get('/api/food_trucks?location=37.7905483182,-122.4003336737&limit=10&offset=10')
        data = json.loads(rv.data)
        second_set_ids = {item.get('id') for item in data.get('items', [])}

        # Verify that the first and second set of results are disjoint
        # (no overlap, results have completely shifted to the next set)
        self.assertFalse(first_set_ids & second_set_ids)

    def test_bad_offset(self):
        """Verify that a bad offset value doesn't cause a request to fail"""
        # Negative value
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846&offset=-100')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertTrue(data['num_results'] > 0)

        # Non-numeric value
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846&offset=A B C')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertTrue(data['num_results'] > 0)

    def test_all_params(self):
        """Test a request using all available input params"""
        rv = self.app.get('/api/food_trucks?location=37.7901490737,-122.3986581846&max_dist=1.00&limit=10&offset=20')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)
        self.assertTrue(data['num_results'] > 0)


if __name__ == '__main__':
    unittest.main()
