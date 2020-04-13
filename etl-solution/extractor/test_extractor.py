# in-built
from unittest import TestCase
from unittest.mock import patch
import json

# Custom
import extract


class TestExtractorApp(TestCase):
    def setUp(self) -> None:
        self.app = extract.app.test_client

    def test_home_page_for_page_not_found(self):
        request, response = self.app.get('/')
        self.assertEqual(404, response.status_code)

    @patch('extract.Producer', autospec=True)
    def test_review_page_with_valid_record(self, mock_producer):
        record = {
            "vehicle": "Honda,CIVIC,2020",
            "fullname": "Tony Stark",
            "address": "10880 Malibu Point, 90265, Florida, USA",
            "time_of_accident": "2013 04-25-2013 10:10:07",
            "total_cost": 1000,
            "currency": "USD",
            "estimate": [
                {
                    "panel": "FRONT LEFT WING",
                    "cost": 1000,
                    "operation": "REPAIR"
                }
            ]

        }
        request, response = self.app.post('/review', data=json.dumps(record))
        self.assertEqual(200, response.status_code)

    def test_review_page_with_invalid_schema(self):
        record = {"1": 1}
        request, response = self.app.post('/review', data=json.dumps(record))
        print(response.json)
        self.assertEqual(400, response.json['status'])

    def test_review_page_with_invalid_currency(self):
        record = {
            "vehicle": "Honda,CIVIC,2020",
            "fullname": "Tony Stark",
            "address": "10880 Malibu Point, 90265, Florida, USA",
            "time_of_accident": "2013 04-25-2013 10:10:07",
            "total_cost": 1000,
            "currency": "SHREYA GHOSHAL",
            "estimate": [
                {
                    "panel": "FRONT LEFT WING",
                    "cost": 1000,
                    "operation": "REPAIR"
                }
            ]

        }
        expected_response = {"status": 400,
                             "error": "invalid currency code found"}

        request, response = self.app.post('/review', data=json.dumps(record))
        self.assertEqual(expected_response, response.json)
