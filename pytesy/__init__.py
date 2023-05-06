# -*- coding: utf-8 -*-

import json
import logging
import threading
import time

import requests
import urllib3

from requests import session
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__version__ = "0.0.3"

NAME = "pytesy"
VERSION = __version__

_LOGGER = logging.getLogger(NAME)
TESY_URL = "https://mytesy.com/v3/api.php"

class PyTesyDevice():
    def __init__(self, parent, data):
        self.id = data['id']
        self.name = data.get('DeviceShortName')
        self._parent = parent
        self.api_version = None

        self.get_api_version(data)

    def get_api_version(self, data):
        self.api_version = 1
        if data.get('DeviceStatus') != None:
            id = data['DeviceStatus'].get('id')
            if id is not None:
                self.id = id
                self.api_version = 2

    def turn_off(self):
        res = self._send_cmd(f'apiv{self.api_version}', 'power_sw', 'off')        

    def turn_on(self):
        res = self._send_cmd(f'apiv{self.api_version}', 'power_sw', 'on')        

    def set_temp(self, val):
        res = self._send_cmd(f'apiv{self.api_version}', 'tmpT', val)

    def _send_cmd(self, api, name, setv):
        return self._send_cmd({'cmd': api, 'name': name, 'set': setv, 'id': self.id})

    def _send_cmd(self, cmd: dict):
        if self.api_version != 1:
            raise NotImplementedError(f"Unknown API version {self.api_version}")

        query = "?"
        for key, val in cmd.items():
            query += f"?{key}={val}&"
        return self._parent._post(query)

    def __repr__(self):
        return str(self.__dict__)

class PyTesyWaterHeater(PyTesyDevice):
    def __init__(self, parent, data):
        super(PyTesyWaterHeater, self).__init__(parent, data)
        self.temp = None
        self.state = None
        self.target_temp = None
        self.on_updated = []

    def update(self, data):
        status = data['DeviceStatus']
        if status.get('cur_shower') is not None: # some models only
            self.temp = float(status['cur_shower'])
        else:
            self.temp = float(status['gradus'])
        self.state = status['Text']
        if status.get('ref_shower') is not None: # some models only
            self.target_temp = float(status['ref_shower'])
        else:
            self.target_temp = float(status['ref_gradus'])
        for func in self.on_updated:
            func(self)

class PyTesyHeater(PyTesyDevice):
    def __init__(self, parent, data):
        super(PyTesyHeater, self).__init__(parent, data)
        self.temp = None
        self.state = None
        self.target_temp = None
        self.heater_status = None
        self.watts = None
        self.on_updated = []

    def update(self, data):
        status = data['DeviceStatus']
        self.temp = float(status['gradus'])
        self.target_temp = float(status['ref_gradus'])
        if self.api_version == 1:
            self.heater_status = (status['heater_state'].lower() == "ready")
            self.state = (status['power_sw'].lower() == "on")
        else:
            self.heater_status = (int(status['ht']) == 1)
            self.state = (int(status['pwr']) == 1)
        self.watts = status['watts']
        for func in self.on_updated:
            func(self)

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

        self._login_headers = {}
        
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
        self._login_headers = resp.headers

    def _post(self, url):
        print(requests.utils.dict_from_cookiejar(self._conn.cookies))
        headers = {}
        for header in self._login_headers:
            if header.startswith("ACC"):
                headers["X-" + header.replace("_", "-")] = self._login_headers[header]
        resp = self._conn.post(TESY_URL + url, headers=headers)
        if not resp.text.startswith('{'):
            self.login()
            resp = self._conn.post(TESY_URL + url)
        if resp.text.startswith('{'):
            return json.loads(resp.text)
        return None

    def create_device(self, serial, value):
        device_type = serial[:3]
        if device_type in ['000', '200', '400']:
            return PyTesyWaterHeater(self, value)
        elif device_type in ['100', '150', '160', '300']:
            return PyTesyHeater(self, value)
        elif device_type == "2500": # special model, totally different API
            raise None
        else:
            return PyTesyDevice(self, value)


    def poll(self):
        timestamp = int(1000 * time.time())
        data = self._post(f'?do=get_dev&req={timestamp}')
        if data is not None:
            for key, value in data['device'].items():
                device = self._devices.get(key)
                if device is None:
                    device = self.create_device(key, value)
                    if device is None:
                        continue # unsupported
                    self._devices[key] = device
                    self.devices.append(device)
                    for func in self.on_device_added:
                            func(device)
                device.update(value)
        return None

  
