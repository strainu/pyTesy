# -*- coding: utf-8 -*-

import logging
import json
import threading

from requests import session
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__version__ = "0.0.3"

NAME = "pytesy"
VERSION = __version__

_LOGGER = logging.getLogger(NAME)
TESY_URL = "https://www.mytesy.com/"

class PyTesyDevice():
    def __init__(self, parent, data):
        self.id = data['id']
        self._parent = parent

    def _send_cmd(self, cmd, val):
        return self._parent._post("?cmd={}&val={}&id={}".format(cmd, val, self.id))

class PyTesyWaterHeater(PyTesyDevice):
    def __init__(self, parent, data):
        super(PyTesyWaterHeater, self).__init__(parent, data)
        self.temp = None
        self.state = None
        self.target_temp = None
        self.on_updated = []

    def update(self, data):
        status = data['DeviceStatus']
        self.temp = float(status['gradus'])
        self.state = status['Text']
        self.target_temp = float(status['ref_gradus'])
        for func in self.on_updated:
            func(self)

    def turn_off(self):
        res = self._send_cmd('power2status', 'off')        

    def turn_on(self):
        res = self._send_cmd('power2status', 'on')        

    def set_temp(self, val):
        res = self._send_cmd('setTemp', val)        

class PyTesy():
    """Library for Tesy devices, now only Boiler"""
    def __init__(self, email, password):
        self._email = email
        self._password = password
        self._conn = session()
        #self._conn.proxies = {"http": "http://127.0.0.1:8888", "https":"http:127.0.0.1:8888"}
        self._conn.verify = False
        self.version = VERSION
        self.on_device_added = []

        self._devices = {}
        self.devices = []
        
        self._stop_event = threading.Event()
        
    def start(self, poll_delay):
        self._poll_delay = poll_delay
        self._poll_thread = threading.Thread(target=self.poll_thread)
        self._poll_thread.daemon = True
        self._poll_thread.start()

    def stop(self):
        self._stop_event.set()

    def poll_thread(self):
        while(not self._stop_event.is_set()):

            self.poll()
            self._stop_event.wait(self._poll_delay)

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
        resp = self._conn.post(TESY_URL + '?do=login', data=payload, headers=headers)

    def _post(self, url):
        resp = self._conn.post(TESY_URL + url)
        if not resp.text.startswith('{'):
            self.login()
            resp = self._conn.post(TESY_URL + url)
        if resp.text.startswith('{'):
            return json.loads(resp.text)
        return None

    def poll(self):
        data = self._post('?do=get_dev')
        if data is not None:
            for key, value in data['device'].items():
                device = self._devices.get(key)
                if device is None:
                    device = PyTesyWaterHeater(self, value)
                    self._devices[key] = device
                    self.devices.append(device)
                    for func in self.on_device_added:
                            func(device)
                device.update(value)
        return None

  