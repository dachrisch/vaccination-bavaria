import unittest
from datetime import date, datetime

from requests import Response

from connectors import ImpzentrenBayerConnector, FileLoginProvider, LoginProvider, LoginError, \
    InvalidCredentialsException
from entities import Appointment


class ResponseFixture(Response):
    def __init__(self, status_code, text, url=None):
        super().__init__()
        self.url = url
        self._text = text
        self.status_code = status_code

    @property
    def text(self) -> str:
        return self._text


class FixtureLoginProvider(LoginProvider):
    def get_login_json(self):
        return {'username': None, 'password': None}


class ImpzentrenBayerConnectorTest(unittest.TestCase):

    def setUp(self) -> None:
        self.connector = ImpzentrenBayerConnector(FixtureLoginProvider())
        self.fixture = {
            'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect/auth?client_id=c19v-frontend&redirect_uri=https%3A%2F%2Fimpfzentren.bayern%2Fcitizen%2F&response_mode=fragment&response_type=code&scope=openid':
            ResponseFixture(200,'<title>Anmeldung bei C19V-Citizen<form id="kc-form-login" action="http://test.login">'),
            'http://test.login':
                ResponseFixture(200, 'see response url', url='http://test.login#code=testcode'),
            'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect/token':
                ResponseFixture(200,
                                '{"token_type" : "Bearer", "access_token" : "test token"}'),
            'https://impfzentren.bayern/api/v1/users/current/citizens':
                ResponseFixture(200, '[{"id" : "citizen_id"}]'),
            'https://impfzentren.bayern/api/v1/citizens/citizen_id/appointments/next':
                ResponseFixture(200,
                                '{"siteId" : "site id", "vaccinationDate" : "2021-12-13", "vaccinationTime" : "15:00"}'),
            'https://impfzentren.bayern/api/v1/citizens/citizen_id/appointments/':
            ResponseFixture(200, '')
        }
        self.connector._session.get = lambda url, params: self.fixture[url]
        self.connector._session.post = lambda url, data: self.fixture[url]

    def test_raises_login_error(self):
        self.fixture['http://test.login'] = ResponseFixture(200, '<div class="alert alert-error">')
        with self.assertRaises(LoginError) as e:
            self.connector.authenticate_session()

    def test_raises_credentials_error(self):
        self.fixture['http://test.login'] = ResponseFixture(200,
                                                            f'<div class="alert alert-error">'
                                                            f'<span class="kc-feedback-text">'
                                                            f'{self.connector.INVALID_CREDENTIALS_TEXT}')
        with self.assertRaises(InvalidCredentialsException) as e:
            self.connector.authenticate_session()

    def test_get_appointment(self):
        self.assertEqual(Appointment('site id', datetime(2021, 12, 13, 15, 00, 00)),
                         self.connector.get_next_appointment(date(2021, 12, 12)))

    def test_book_appointment(self):
        self.connector.book_appointment(Appointment('site', datetime.now()))


if __name__ == '__main__':
    unittest.main()
