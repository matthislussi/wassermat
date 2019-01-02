#!/usr/bin/env python3

import json
import os.path
import random
import threading

class DataProvider:
    """Synchronized data entity holder holding value types as lists. Each set operation adds the value
    to the list of its type. Get operation returns a json structure containing the average of the values of each type.
    getData/getData methods are thread-safe"""

    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()
        self.humidity = []
        self.pumpActive = False
        self.lightActive = False

    def getData(self):
        """Get average values of all lists"""
        result = {}
        # single threaded
        self.lock.acquire()

        result['humidity'] = 0
        if (len(self.humidity) > 0):
            result['humidity'] = sum(self.humidity) / len(self.humidity)
            self.humidity = [] # clear

        result['pump_active'] = self.pumpActive
        result['light_active'] = self.lightActive

        self.lock.release()
        return json.dumps(result)

    def setData(self, humidity, pumpActive, lightActive):
        self.lock.acquire()
        self.humidity.append(humidity)
        self.pumpActive = pumpActive
        self.lightActive = lightActive
        self.lock.release()


class ConfigurationProvider:
    'A file configuration abstraction. All parameters must be hashable, not lists, dicts, etc.'
    config = {}

    def __init__(self, cfg_file):
        if (not os.path.isfile(cfg_file)):
            raise ValueError('Unable to read config file "'+cfg_file+'"')
        self.cfg_file = cfg_file
        # load cache
        self.read()

    def write(self, config):
        'Write received configuration to internal cache and save it to disk '
        unmatched_item = set(config.items()) ^ set(self.config.items())
        # write if changed
        if len(unmatched_item) != 0:
            print('Config has changed, persisting new version: \'{}\''.format(json.dumps(config, sort_keys=True, indent=4)))
            self.config = config
            with open(self.cfg_file, 'w') as outfile:
                json.dump(config, outfile)

    def read(self):
        'Load internal cache from disk and return it to caller'
        with open(self.cfg_file) as json_file:
            self.config = json.load(json_file)
        return self.config

    def getParam(self, param):
        'Return a config parameter'
        return self.config[param]
