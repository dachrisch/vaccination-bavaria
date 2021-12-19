from datetime import datetime, date
from typing import Type

from vaccination.connectors import ImpzentrenBayernConnector, Authentication
from vaccination.entities import Appointment, NoAppointment
from vaccination.login import LoginProvider


class VaccinationAppointmentService:
    def __init__(self, connector_type: Type[ImpzentrenBayernConnector]):
        self.connector_type = connector_type

    def authentication(self, login_provider: LoginProvider):
        with self._with_service() as connector:
            access_token = connector.login(login_provider.get_login_json())
            return Authentication.from_access_token(connector.get_access_token(access_token))

    def current_appointment(self, authentication: Authentication):
        with self._with_service_as_authenticated(authentication) as connector:
            return connector.get_current_appointment()

    def next_appointment(self, authentication: Authentication, first_day: date) -> Type[Appointment]:
        with self._with_service_as_authenticated(authentication) as connector:
            return connector.get_next_appointment(first_day)

    def appointments_in_range(self, authentication: Authentication, first_day: date, days: int):
        with self._with_service_as_authenticated(authentication) as connector:
            return connector.get_appointments_in_range(first_day=first_day, days=days)

    def book_appointment(self, authentication: Authentication, appointment: Appointment):
        with self._with_service_as_authenticated(authentication) as connector:
            connector.book_appointment(appointment)

    def has_next_appointment(self, authentication: Authentication):
        return not isinstance(self.current_appointment(authentication), NoAppointment)

    def _with_service_as_authenticated(self, authentication: Authentication) -> ImpzentrenBayernConnector:
        with self._with_service() as connector:
            connector.authenticate_session(authentication)
            return connector

    def _with_service(self) -> ImpzentrenBayernConnector:
        with self.connector_type() as connector:
            return connector
