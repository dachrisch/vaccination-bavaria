from __future__ import annotations
import logging
from logging import getLogger
from datetime import datetime, timedelta
from logging import basicConfig

from vaccination.connectors import ImpzentrenBayernConnector
from vaccination.login import FileLoginProvider
from vaccination.services import VaccinationAppointmentService


def main():
    now = datetime.now()
    later = now + timedelta(days=60)
    log = getLogger(__name__).info
    log(f'looking for appointment [{now}] to [{later}]...')
    service = VaccinationAppointmentService(ImpzentrenBayernConnector)
    authentication = service.authentication(FileLoginProvider())
    if service.has_next_appointment(authentication):
        log(f'your next appointment is {service.current_appointment(authentication)}')
    else:
        for appointment in service.appointments_in_range(authentication, now, 60):
            log(appointment)
    log('done.')


if __name__ == '__main__':
    basicConfig(level=logging.INFO)
    getLogger(ImpzentrenBayernConnector.__name__).setLevel(logging.DEBUG)
    main()
