from datetime import datetime, date
from unittest import TestCase

from more_itertools import one

from tests.fixtures import FixtureLoginProvider, ResponseFixture, ResponseFixtures
from vaccination.connectors import Authentication, ImpzentrenBayernConnector
from vaccination.entities import Appointment
from vaccination.services import VaccinationAppointmentService


class ImpzentrenBayernConnectorMock(ImpzentrenBayernConnector):
    def __init__(self):
        super().__init__()
        self.fixtures = ResponseFixtures.fixtures()
        self._get = lambda url, params=None, allowed_returns=None: self.fixtures[url]
        self._post = lambda url, data=None, json=None: self.fixtures[url]


class VaccinationAppointmentServiceTest(TestCase):
    def setUp(self) -> None:
        self.service = VaccinationAppointmentService(ImpzentrenBayernConnectorMock)
        self.authentication = self.service.authentication(FixtureLoginProvider())

    def test_login(self):
        self.assertEqual(
            Authentication.from_access_token({'token_type': 'Bearer', 'access_token': 'test token', 'refresh_token': 'test refresh token'}),
            self.service.authentication(FixtureLoginProvider()))

    def test_current_appointment(self):
        self.assertEqual(Appointment('site id', datetime(2021, 12, 13, 15, 0, 0)),
                         self.service.current_appointment(self.authentication))

    def test_next_appointment(self):
        self.assertEqual(Appointment('site id', datetime(2021, 12, 13, 15, 0, 0)),
                         self.service.next_appointment(self.authentication, date(2021, 12, 13)))

    def test_find_one_appointment(self):
        self.assertEqual(Appointment('site id', datetime(2021, 12, 13, 15, 00, 00)),
                         one(self.service.appointments_in_range(self.authentication,
                                                                first_day=date(2021, 12, 13),
                                                                days=1)))

    def test_book_appointment(self):
        self.service.book_appointment(self.authentication, Appointment('site id', datetime(2021, 12, 13, 15, 00, 00)))