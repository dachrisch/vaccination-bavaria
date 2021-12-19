from __future__ import annotations

import json
from abc import ABC, abstractmethod


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