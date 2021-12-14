from __future__ import annotations
import json
from datetime import date, datetime, timedelta
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
from dateutil import rrule
from more_itertools import one
from requests import Session


class Appointment:
    class NoAppointment:
        def __eq__(self, other):
            return type(other) is type(self)

    @classmethod
    def from_json(cls, _json):
        if 'siteId' not in _json:
            return Appointment.NoAppointment
        else:
            return cls(_json['siteId'],
                       datetime.fromisoformat(f'{_json["vaccinationDate"]} {_json["vaccinationTime"]}'))

    def __init__(self, site, date_time):
        self.date_time = date_time
        self.site = site

    def __repr__(self):
        key_values = ','.join(map(lambda item: f'{item[0]}->{item[1]}', self.__dict__.items()))
        return f'{self.__class__.__name__}({key_values})'

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __hash__(self):
        return hash(tuple(map(lambda item: (item[0], item[1]), self.__dict__.items())))


class ImpzentrenBayerConnector:
    OPENID_CONNECT_URL = 'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect'

    def __init__(self):
        self._session = Session()
        self.credentials_json = 'credentials.json'

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._session.close()

    @property
    def _login_link(self):
        response = self._get(
            f'{self.OPENID_CONNECT_URL}/auth?client_id=c19v-frontend&redirect_uri=https%3A%2F%2Fimpfzentren.bayern%2Fcitizen%2F&response_mode=fragment&response_type=code&scope=openid')
        soup = BeautifulSoup(response.text, features='html.parser')
        assert 'Anmeldung bei C19V-Citizen' == soup.title.text
        login_form = soup.find('form')
        assert 'kc-form-login' == login_form.get('id')
        return login_form.get('action')

    @property
    def _auth_code(self):
        login_json = {}
        with open(self.credentials_json, 'r') as cred:
            login_json.update(json.load(cred))
        response = self._session.post(self._login_link, data=login_json)
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, features='html.parser')
        errors = soup.find_all('div', {'class': 'alert alert-error'})
        assert not errors, errors
        return parse_qs(urlparse(response.url).fragment)['code']

    @property
    def _auth_header(self):
        response = self._session.post(
            'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect/token',
            data={
                'code': self._auth_code,
                'grant_type': 'authorization_code',
                'client_id': 'c19v-frontend',
                'redirect_uri': 'https://impfzentren.bayern/citizen/'
            })
        assert response.status_code == 200, response.text
        authentication = json.loads(response.text)
        assert 'Bearer' == authentication['token_type']
        return {'Authorization': f"Bearer {authentication['access_token']}"}

    @property
    def citizen(self):
        self._authenticate_session()
        response = self._get('https://impfzentren.bayern/api/v1/users/current/citizens')
        return one(json.loads(response.text))

    def get_appointment(self, first_day: date):
        self._authenticate_session()
        response = self._get(f'https://impfzentren.bayern/api/v1/citizens/{self.citizen["id"]}/appointments/next',
                             params={'timeOfDay': 'ALL_DAY',
                                     'lastDate': first_day.strftime("%Y-%m-%d"),
                                     'lastTime': '00:00'},
                             allowed_return=(200, 404))
        return Appointment.from_json(response.json())

    def _get(self, url, params=None, allowed_return=(200,)):
        response = self._session.get(url, params=params)
        assert response.status_code in allowed_return, response.text
        return response

    def _authenticate_session(self):
        if 'Authorization' not in self._session.headers:
            self._session.headers.update(self._auth_header)


def main():
    now = datetime.now()
    later = now + timedelta(days=60)
    print(f'looking for appointment [{now}] to [{later}]...')
    with ImpzentrenBayerConnector() as connector:
        for appointment in set(filter(lambda app: isinstance(app, Appointment),
                                      map(lambda start_date: connector.get_appointment(start_date.date()),
                                          rrule.rrule(rrule.DAILY, dtstart=now, until=later)))):
            print(appointment)
    print('done.')


if __name__ == '__main__':
    main()
