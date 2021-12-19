from flask import g

from vaccination.connectors import ImpzentrenBayernConnector
from vaccination.login import UsernamePasswordLoginProvider
from vaccination.services import VaccinationAppointmentService


class WithService:
    def __init__(self):
        self.service = VaccinationAppointmentService(ImpzentrenBayernConnector)

