from requests import Response

from vaccination.login import LoginProvider


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


class ResponseFixtures:
    @classmethod
    def fixtures(self):
        return {
            'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect/auth?client_id=c19v-frontend&redirect_uri=https%3A%2F%2Fimpfzentren.bayern%2Fcitizen%2F&response_mode=fragment&response_type=code&scope=openid':
                ResponseFixture(200,
                                '<title>Anmeldung bei C19V-Citizen<form id="kc-form-login" action="http://test.login">'),
            'http://test.login':
                ResponseFixture(200, 'see response url', url='http://test.login#code=testcode'),
            'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect/token':
                ResponseFixture(200,
                                '{"token_type" : "Bearer", "access_token" : "test token", '
                                '"refresh_token" : "test refresh token"}'),
            'https://impfzentren.bayern/api/v1/users/current/citizens':
                ResponseFixture(200, '[{"id" : "citizen_id"}]'),
            'https://impfzentren.bayern/api/v1/citizens/citizen_id/appointments/next':
                ResponseFixture(200,
                                '{"siteId" : "site id", "vaccinationDate" : "2021-12-13", "vaccinationTime" : "15:00"}'),
            'https://impfzentren.bayern/api/v1/citizens/citizen_id/appointments/':
                ResponseFixture(200,
                                '{"futureAppointments":'
                                '[{"slotId":{"siteId" : "site id", '
                                '"date" : "2021-12-13", '
                                '"time" : "15:00"}}]}')
        }
