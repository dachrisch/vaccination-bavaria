from __future__ import annotations

import json
from datetime import date, timedelta
from functools import cached_property
from logging import getLogger
from typing import Set, Type
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from dateutil import rrule
from more_itertools import one
from pytz import timezone
from requests import Session

from vaccination.entities import Appointment, NoAppointment, HashableMixin
from vaccination.login import LoginProvider


class InvalidCredentialsException(Exception):
    pass


class AuthenticationRefreshNeededException(Exception):
    def __init__(self, response):
        self.response = response


class LoginError(Exception):
    def __init__(self, error):
        self.error = error


class Authentication(HashableMixin):
    def __init__(self, access_token, refresh_token=None):
        self.access_token = access_token
        self.refresh_token=refresh_token

    @classmethod
    def from_session(cls, session_auth):
        return cls(session_auth)

    @classmethod
    def from_access_token(cls, access_token):
        return cls(access_token['access_token'], access_token['refresh_token'])


class ImpzentrenBayernConnector:
    OPENID_CONNECT_URL = 'https://ciam.impfzentren.bayern/auth/realms/C19V-Citizen/protocol/openid-connect'
    VACCINATE_API_URL = 'https://impfzentren.bayern/api/v1'
    INVALID_CREDENTIALS_TEXT = 'Ungültiger Benutzername oder Passwort.'

    def __init__(self):
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

    def get_access_token(self, access_token):
        response = self._post(f'{self.OPENID_CONNECT_URL}/token',
                              data={
                                  'code': access_token,
                                  'grant_type': 'authorization_code',
                                  'client_id': 'c19v-frontend',
                                  'redirect_uri': 'https://impfzentren.bayern/citizen/'
                              })
        authentication = json.loads(response.text)
        assert 'Bearer' == authentication['token_type']
        return authentication

    def refresh_token(self, refresh_token):
        response = self._post(f'{self.OPENID_CONNECT_URL}/token',
                              data={
                                  'code': refresh_token,
                                  'grant_type': 'refresh_token',
                                  'client_id': 'c19v-frontend'
                              })
        authentication = json.loads(response.text)
        assert 'Bearer' == authentication['token_type']
        return authentication

    def login(self, login_json):
        response = self._post(self._login_link, data=login_json)
        soup = BeautifulSoup(response.text, features='html.parser')
        errors = soup.find_all('div', {'class': 'alert alert-error'})
        feedback = soup.find('span', {'class': 'kc-feedback-text'})
        if errors:
            if feedback:
                if self.INVALID_CREDENTIALS_TEXT == feedback.text:
                    raise InvalidCredentialsException
            raise LoginError(errors)
        self.debug(f'successfully logged in [{login_json["username"]}]')
        return one(parse_qs(urlparse(response.url).fragment)['code'])

    @cached_property
    def citizen(self):
        response = self._get(f'{self.VACCINATE_API_URL}/users/current/citizens')
        citizen_json = one(json.loads(response.text))
        self.debug(f'using citizen [{citizen_json["id"]}]')
        return citizen_json

    def get_next_appointment(self, first_day: date) -> Type[Appointment]:
        response = self._get(f'{self.VACCINATE_API_URL}/citizens/{self.citizen["id"]}/appointments/next',
                             params={'timeOfDay': 'ALL_DAY',
                                     'lastDate': first_day.strftime("%Y-%m-%d"),
                                     'lastTime': '00:00'},
                             allowed_returns=(200, 404))
        appointment = Appointment.from_json(response.json())
        self.debug(f'found [{appointment}] for day [{first_day}]')
        return appointment

    def get_current_appointment(self) -> Type[Appointment]:
        response = self._get(f'{self.VACCINATE_API_URL}/citizens/{self.citizen["id"]}/appointments/')
        appointment = Appointment.from_future_json(response.json())
        self.debug(f'currently {appointment}')
        return appointment

    def has_next_appointment(self)->bool:
        return not isinstance(self.get_current_appointment(),NoAppointment)

    def book_appointment(self, appointment: Appointment):
        book_data = self._book_json(appointment)
        response = self._post(
            f'{self.VACCINATE_API_URL}/citizens/{self.citizen["id"]}/appointments/',
            json=book_data)

    def get_appointments_in_range(self, first_day: date, days=1) -> Set[Type[Appointment]]:
        now = first_day
        later = now + timedelta(days=days)
        return set(filter(lambda app: app.__class__ == Appointment,
                          map(lambda start_date: self.get_next_appointment(start_date.date()),
                              rrule.rrule(rrule.DAILY, dtstart=now, until=later))))

    def authenticate_session(self, authentication:Authentication):
        self._session.headers.update({'Authorization': f"Bearer {authentication.access_token}"})

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

    def _get(self, url, params=None, allowed_returns=(200,)):
        response = self._session.get(url, params=params)
        if response.status_code not in allowed_returns:
            if 401 == response.status_code:
                raise AuthenticationRefreshNeededException(response)
        return response

    def _post(self, url, allowed_returns=(200, ), **kwargs):
        response = self._session.post(url, **kwargs)
        assert response.status_code in allowed_returns, response.text
        return response
