from __future__ import annotations

import json
from datetime import date
from functools import cached_property
from logging import getLogger
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from more_itertools import one
from requests import Session

from entities import Appointment


class ImpzentrenBayerConnector:
    OPENID_CONNECT_URL = 'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect'

    def __init__(self):
        self._session = Session()
        self.credentials_json = 'credentials.json'
        self.log = getLogger(self.__class__.__name__).info
        self.debug = getLogger(self.__class__.__name__).debug

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._session.close()

    @cached_property
    def _login_link(self):
        response = self._get(
            f'{self.OPENID_CONNECT_URL}/auth?client_id=c19v-frontend&redirect_uri=https%3A%2F%2Fimpfzentren.bayern%2Fcitizen%2F&response_mode=fragment&response_type=code&scope=openid')
        soup = BeautifulSoup(response.text, features='html.parser')
        assert 'Anmeldung bei C19V-Citizen' == soup.title.text
        login_form = soup.find('form')
        assert 'kc-form-login' == login_form.get('id')
        login_link = login_form.get('action')
        self.debug(f'using login link: {login_link}')
        return login_link

    @cached_property
    def _auth_code(self):
        login_json = {}
        with open(self.credentials_json, 'r') as cred:
            login_json.update(json.load(cred))
        response = self._session.post(self._login_link, data=login_json)
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, features='html.parser')
        errors = soup.find_all('div', {'class': 'alert alert-error'})
        assert not errors, errors
        self.debug(f'successfully logged in [{login_json["username"]}]')
        return parse_qs(urlparse(response.url).fragment)['code']

    @cached_property
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

    @cached_property
    def citizen(self):
        self._authenticate_session()
        response = self._get('https://impfzentren.bayern/api/v1/users/current/citizens')
        citizen_json = one(json.loads(response.text))
        self.debug(f'using citizen [{citizen_json["id"]}]')
        return citizen_json

    def get_appointment(self, first_day: date):
        self._authenticate_session()
        response = self._get(f'https://impfzentren.bayern/api/v1/citizens/{self.citizen["id"]}/appointments/next',
                             params={'timeOfDay': 'ALL_DAY',
                                     'lastDate': first_day.strftime("%Y-%m-%d"),
                                     'lastTime': '00:00'},
                             allowed_return=(200, 404))
        appointment = Appointment.from_json(response.json())
        self.debug(f'found [{appointment}] for day [{first_day}]')
        return appointment

    def _get(self, url, params=None, allowed_return=(200,)):
        response = self._session.get(url, params=params)
        assert response.status_code in allowed_return, response.text
        return response

    def _authenticate_session(self):
        if 'Authorization' not in self._session.headers:
            self._session.headers.update(self._auth_header)