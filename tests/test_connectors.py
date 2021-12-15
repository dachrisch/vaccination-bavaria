import unittest
from datetime import date, datetime

from requests import Response

from connectors import ImpzentrenBayerConnector
from entities import Appointment


class TestResponse(Response):
    def __init__(self, status_code, text):
        super().__init__()
        self._text = text
        self.status_code = status_code

    @property
    def text(self) -> str:
        return self._text


class MyTestCase(unittest.TestCase):
    def test_get_appointment(self):
        connector = ImpzentrenBayerConnector()
        connector._auth_code = 'test code'
        fixture = {
            'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect/token':
                TestResponse(200,
                             '{"token_type" : "Bearer", "access_token" : "test token"}'),
            'https://impfzentren.bayern/api/v1/users/current/citizens':
                TestResponse(200, '[{"id" : "citizen_id"}]'),
            'https://impfzentren.bayern/api/v1/citizens/citizen_id/appointments/next':
                TestResponse(200,
                             '{"siteId" : "site id", "vaccinationDate" : "2021-12-13", "vaccinationTime" : "15:00"}')
        }
        connector._session.get = lambda url, params: fixture[url]
        connector._session.post = lambda url, data: fixture[url]
        self.assertEqual(Appointment('site id', datetime(2021, 12, 13, 15, 00, 00)),
                         connector.get_appointment(date(2021, 12, 12)))


if __name__ == '__main__':
    unittest.main()
