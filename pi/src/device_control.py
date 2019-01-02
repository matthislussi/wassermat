#!/usr/bin/env python3

#import RPi.GPIO as GPIO
import time
import datetime
import random
import ssl
import jwt
import json
import threading

# GPIO SETUP
channel = 21
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(channel, GPIO.IN)

class DeviceControl(threading.Thread):
    """The device control object polls the humidity sensor and controls pump and light activity based on config values
    The following configurationProvider config values are consumed:
    - device_poll_interval: poll interval in sec. (eg. 50ms -> 0.05)
    - humidity_threshold: water pump is activated when humidity level falls below this value (in %)
    - humidity_threshold_lag: humidity level must stay below the threshold for this time (in sec.) before the pump is activated
    - lightning_start: lightning start time in format hh:mm
    - lightning_end": lightning end time in format hh:mm
    """

    def __init__(self, dataProvider, configurationProvider, stopEvent):
        super(DeviceControl, self).__init__()
        self.stopEvent = stopEvent
        self.dataProvider = dataProvider
        self.configurationProvider = configurationProvider
        self.lightActivated = False
        self.pumpActivated = False
        now = datetime.datetime.now().time()
        self.humRaisedAbove = now
        self.humRaisedBelow = now

        # GPIO.add_event_detect(channel, GPIO.BOTH, bouncetime=300)  # let us know when the pin goes HIGH or LOW
        # GPIO.add_event_callback(channel, self.callback)  # assign function to GPIO PIN, Run function on change

    def makeTime(self, hhMidateStr):
        t = time.strptime(hhMidateStr,"%H:%M")
        return datetime.time(hour=t.tm_hour,minute=t.tm_min,second=t.tm_sec)

    def addSecs(self, tm, secs):
        fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
        fulldate = fulldate + datetime.timedelta(seconds=secs)
        return fulldate.time()

    def activateLight(self):
        startTime = self.makeTime(self.configurationProvider.getParam('lightning_start'))
        endTime = self.makeTime(self.configurationProvider.getParam('lightning_end'))
        now = datetime.datetime.now().time()
        if (not self.lightActivated):
            if (now > startTime and now < endTime):
                print('Light activated at '+str(now))
                self.lightActivated = True
        else:
            if (now < startTime or now > endTime):
                print('Light deactivated at '+str(now))
                self.lightActivated = False

    def activatePump(self, humidity):
        th = self.configurationProvider.getParam('humidity_threshold')
        lag = self.configurationProvider.getParam('humidity_threshold_lag')
        now = datetime.datetime.now().time()

        if (humidity < th):
            if (self.humRaisedAbove > self.humRaisedBelow):
                # from high to low threshold crossing
                self.humRaisedBelow = now
                print('humRaisedBelow='+str(self.humRaisedBelow))
            else:
                # during below threshold phase
                lagUntil = self.addSecs(self.humRaisedBelow, lag)
                if (not self.pumpActivated and lagUntil < now):
                    self.pumpActivated = True
                    self.humRaisedBelow = now
                    print('humRaisedBelow='+str(self.humRaisedBelow)+', lagUntil='+str(lagUntil))
                    print('humidity is '+str(humidity)+', pump activated at '+str(now))
        else:
            if (self.humRaisedAbove < self.humRaisedBelow):
                # from low to high threshold crossing
                self.humRaisedAbove = now
                print('humRaisedAbove='+str(self.humRaisedAbove))
            else:
                # during below threshold phase
                lagUntil = self.addSecs(self.humRaisedAbove, lag)
                if (self.pumpActivated and lagUntil < now):
                    self.pumpActivated = False
                    self.humRaisedAbove = now
                    print('humRaisedAbove='+str(self.humRaisedAbove)+', lagUntil='+str(lagUntil))
                    print('humidity is '+str(humidity)+', pump deactivated at '+str(now))


    def run(self):
        print("DeviceControl starting ")
        while (not self.stopEvent.is_set()):
            # TODO: remove test data on pi
            humidity = random.randint(50,70)

            self.activateLight()
            self.activatePump(humidity)
            self.dataProvider.setData(humidity, self.pumpActivated, self.lightActivated)
            time.sleep(self.configurationProvider.getParam('device_poll_interval'))
            # print(str(datetime.datetime.now().time())+' Polling...')
        print('DeviceControl stopped')

def callback(self, channel):
        print('Callback called')
        # if GPIO.input(channel):
        #     print("Water Detected!")
        # else:
        #     print("Water Detected!")
