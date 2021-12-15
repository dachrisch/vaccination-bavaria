from __future__ import annotations

from datetime import datetime


class Appointment:
    class NoAppointment:
        def __eq__(self, other):
            return type(other) is type(self)

    @classmethod
    def from_json(cls, _json):
        if 'siteId' not in _json:
            return Appointment.NoAppointment
        else:
            return cls(_json['siteId'],
                       datetime.fromisoformat(f'{_json["vaccinationDate"]} {_json["vaccinationTime"]}'))

    def __init__(self, site, date_time):
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