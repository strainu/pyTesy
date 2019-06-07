# -*- coding: utf-8 -*-

import logging
import json
from requests import session

__version__ = "0.0.30"

NAME = "pytesy"
VERSION = __version__

_LOGGER = logging.getLogger(NAME)

class PyTesy():
    """Library for Tesy devices, now only Boiler"""
    def __init__(self, email, password):
        self._email = email
        self._password = password
        self._conn = session()
        self._conn.proxies = {"http": "http://127.0.0.1:8888", "https":"http:127.0.0.1:8888"}
        self._conn.verify = False

    def login(self):
        payload = {
            'os':'',
            'token':'',
            'user' : self._email,
            'pass' : self._password
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html'
        }
        login = self._conn.post('https://www.mytesy.com/?do=login', data=payload, headers=headers)

    def poll(self):
        resp = self._conn.post('https://www.mytesy.com/?do=get_dev')
        if not resp.text.startswith('{'):
            self.login()
            resp = self._conn.post('https://www.mytesy.com/?do=get_dev')
        if resp.text.startswith('{'):
            return json.loads(resp.text)
        return None
  