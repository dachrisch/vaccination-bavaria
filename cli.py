from __future__ import annotations
import logging
from logging import getLogger
from datetime import datetime, timedelta
from logging import basicConfig

from dateutil import rrule

from connectors import ImpzentrenBayerConnector, FileLoginProvider
from entities import Appointment


def main():
    now = datetime.now()
    later = now + timedelta(days=60)
    log = getLogger(__name__).info
    log(f'looking for appointment [{now}] to [{later}]...')
    with ImpzentrenBayerConnector(FileLoginProvider()) as connector:
        for appointment in connector.get_appointments_in_range(now, 60):
            log(appointment)
    log('done.')


if __name__ == '__main__':
    basicConfig(level=logging.INFO)
    getLogger(ImpzentrenBayerConnector.__name__).setLevel(logging.DEBUG)
    main()
