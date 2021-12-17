from __future__ import annotations

from datetime import datetime

from more_itertools import only


class Appointment:

    @classmethod
    def no_appointment(cls):
        return NoAppointment()

    @classmethod
    def from_json(cls, _json):
        if 'siteId' not in _json:
            return cls.no_appointment()
        else:
            return cls(_json['siteId'],
                       datetime.fromisoformat(f'{_json["vaccinationDate"]} {_json["vaccinationTime"]}'))

    def __init__(self, site: str, date_time: datetime):
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

    @classmethod
    def from_future_json(cls, json_appointment):
        assert 'futureAppointments' in json_appointment
        slot_json = only(json_appointment['futureAppointments'], {}).get('slotId')
        if slot_json:
            return cls(slot_json['siteId'],datetime.fromisoformat(f'{slot_json["date"]} {slot_json["time"]}'))
        else:
            return cls.no_appointment()


class NoAppointment(Appointment):
    def __init__(self):
        super().__init__('None', datetime(1970, 1, 1, 0, 0, 0))

    def __repr__(self):
        return f'{self.__class__.__name__}()'
