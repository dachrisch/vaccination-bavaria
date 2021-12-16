from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date, timedelta
from functools import cached_property
from logging import getLogger
from typing import Set
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from dateutil import rrule
from more_itertools import one
from pytz import timezone
from requests import Session

from entities import Appointment


class InvalidCredentialsException(Exception):
    pass


class LoginError(Exception):
    def __init__(self, error):
        self.error = error


class AuthenticationRefreshNeededException(Exception):
    def __init__(self, response):
        self.response = response


class LoginProvider(ABC):
    @abstractmethod
    def get_login_json(self):
        pass


class FileLoginProvider(LoginProvider):

    def __init__(self):
        self.credentials_json = 'credentials.json'

    def get_login_json(self):
        with open(self.credentials_json, 'r') as cred:
            return json.load(cred)


class UsernamePasswordLoginProvider(LoginProvider):
    def __init__(self):
        self.username = None
        self.password = None

    def get_login_json(self):
        return {'username': self.username, 'password': self.password}

    def provide(self, username, password):
        self.password = password
        self.username = username


class ImpzentrenBayerConnector:
    OPENID_CONNECT_URL = 'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect'
    VACCINATE_API_URL = 'https://impfzentren.bayern/api/v1'
    INVALID_CREDENTIALS_TEXT = 'Ungültiger Benutzername oder Passwort.'

    def __init__(self, login_provider: LoginProvider):
        self.login_provider = login_provider
        self._session = Session()
        self.log = getLogger(self.__class__.__name__).info
        self.debug = getLogger(self.__class__.__name__).debug

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
        login_form = soup.find('form', {'id': 'kc-form-login'})
        assert login_form
        login_link = login_form.get('action')
        self.debug(f'using login link: {login_link}')
        return login_link

    @cached_property
    def _auth_code(self):
        url = self._login()
        return parse_qs(urlparse(url).fragment)['code']

    @cached_property
    def _auth_header(self):
        response = self._session.post(f'{self.OPENID_CONNECT_URL}/token',
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

    def _login(self):
        login_json = self.login_provider.get_login_json()
        response = self._session.post(self._login_link, data=login_json)
        assert response.status_code == 200, response.text
        soup = BeautifulSoup(response.text, features='html.parser')
        errors = soup.find_all('div', {'class': 'alert alert-error'})
        feedback = soup.find('span', {'class': 'kc-feedback-text'})
        if errors:
            if feedback:
                if self.INVALID_CREDENTIALS_TEXT == feedback.text:
                    raise InvalidCredentialsException
            raise LoginError(errors)
        self.debug(f'successfully logged in [{login_json["username"]}]')
        return response.url

    @cached_property
    def citizen(self):
        self.authenticate_session()
        response = self._get(f'{self.VACCINATE_API_URL}/users/current/citizens')
        citizen_json = one(json.loads(response.text))
        self.debug(f'using citizen [{citizen_json["id"]}]')
        return citizen_json

    def get_next_appointment(self, first_day: date) -> Appointment:
        self.authenticate_session()
        response = self._get(f'{self.VACCINATE_API_URL}/citizens/{self.citizen["id"]}/appointments/next',
                             params={'timeOfDay': 'ALL_DAY',
                                     'lastDate': first_day.strftime("%Y-%m-%d"),
                                     'lastTime': '00:00'},
                             allowed_return=(200, 404))
        appointment = Appointment.from_json(response.json())
        self.debug(f'found [{appointment}] for day [{first_day}]')
        return appointment

    def book_appointment(self, appointment: Appointment):
        self.authenticate_session()
        book_data = self._book_json(appointment)
        response = self._session.post(
            f'{self.VACCINATE_API_URL}/citizens/{self.citizen["id"]}/appointments/',
            json=book_data)
        assert 200 == response.status_code, response.text

    def _book_json(self, appointment):
        homezone = timezone('Europe/Berlin')
        book_data = {
            "siteId": appointment.site,
            "vaccinationDate": appointment.date_time.date().isoformat(),
            "vaccinationTime": appointment.date_time.time().isoformat('minutes'),
            "zoneOffset": f'+{homezone.utcoffset(appointment.date_time).seconds / 3600:02.0f}:00',
            "reminderChannel": {
                "reminderBySms": True,
                "reminderByEmail": True
            }
        }
        return book_data

    def get_appointments_in_range(self, first_day: date, days=1) -> Set[Appointment]:
        now = first_day
        later = now + timedelta(days=days)
        return set(filter(lambda app: isinstance(app, Appointment),
                          map(lambda start_date: self.get_next_appointment(start_date.date()),
                              rrule.rrule(rrule.DAILY, dtstart=now, until=later))))

    def _get(self, url, params=None, allowed_return=(200,)):
        response = self._session.get(url, params=params)
        if response.status_code not in allowed_return:
            if 401 == response.status_code:
                raise AuthenticationRefreshNeededException(response)
        return response

    def authenticate_session(self):
        if 'Authorization' not in self._session.headers:
            self._session.headers.update(self._auth_header)
