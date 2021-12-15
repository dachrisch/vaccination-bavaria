from __future__ import annotations
import logging
from logging import getLogger
from datetime import datetime, timedelta
from logging import basicConfig

from dateutil import rrule

from connectors import ImpzentrenBayerConnector
from entities import Appointment


def main():
    now = datetime.now()
    later = now + timedelta(days=60)
    log = getLogger(__name__).info
    log(f'looking for appointment [{now}] to [{later}]...')
    with ImpzentrenBayerConnector() as connector:
        for appointment in set(filter(lambda app: isinstance(app, Appointment),
                                      map(lambda start_date: connector.get_appointment(start_date.date()),
                                          rrule.rrule(rrule.DAILY, dtstart=now, until=later)))):
            log(appointment)
    log('done.')


if __name__ == '__main__':
    basicConfig(level=logging.INFO)
    getLogger(ImpzentrenBayerConnector.__name__).setLevel(logging.DEBUG)
    main()
