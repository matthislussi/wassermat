#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import datetime
import random
import threading

# GPIO SETUP
GPIO_PUMP = 8
GPIO_LIGHT = 22
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(GPIO_PUMP, GPIO.OUT)
GPIO.setup(GPIO_LIGHT, GPIO.OUT)

# HIGH is off, LOW is on
GPIO.output(GPIO_PUMP, GPIO.HIGH)
GPIO.output(GPIO_LIGHT, GPIO.HIGH)

# --- sensor SPI configuration (MCP3008) ---
# see https://learn.adafruit.com/reading-a-analog-in-and-controlling-audio-volume-with-the-raspberry-pi/script

# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# humidity sensor connected to adc #0
sensor_adc = 0;

# --- END sensor SPI configuration (MCP3008) ---

def stopDevice(channel):
    GPIO.output(channel, GPIO.HIGH)

def startDevice(channel):
    GPIO.output(channel, GPIO.LOW)

class DeviceControl(threading.Thread):
    """The device control object polls the humidity sensor and controls pump and light activity based on these config values:
	- device_poll_interval: poll interval in sec. (eg. 50ms -> 0.05)
	- watering_scheme: fixed or dynamic (see below)
	- watering_threshold: if watering_scheme is fix: watering is skipped if humidity is above this % level
	                      if watering_scheme is dynamic: water pump is activated when humidity level falls below this % value
	- watering_threshold_lag: humidity level must stay below the threshold for sec. before watering starts (dynamic scheme only)
	- watering_start: watering starts at this time in format hh:mi (fixed scheme only)
	- watering_duration: watering duration in sec. (fixed scheme only)
	- lightning_start: ightning start time in format hh:mm
	- lightning_end: lightning end time in format hh:mm
    """

    def __init__(self, dataProvider, configurationProvider, stopEvent):
        super(DeviceControl, self).__init__()
        self.stopEvent = stopEvent
        self.dataProvider = dataProvider
        self.configurationProvider = configurationProvider

        # internal state values
        self.lightActivated = False
        self.pumpActivated = False
        now = datetime.datetime.now().time()
        self.humRaisedAbove = now
        self.humRaisedBelow = now

    def makeTime(self, hhMidateStr):
        """Make a time object based on a string"""
        t = time.strptime(hhMidateStr,"%H:%M")
        return datetime.time(hour=t.tm_hour,minute=t.tm_min,second=t.tm_sec)

    def addSecs(self, tm, secs):
        """Add secs to a time object"""
        fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
        fulldate = fulldate + datetime.timedelta(seconds=secs)
        return fulldate.time()

    def activateLight(self):
        """Activate or deactivate light based on configured start & end time"""
        startTime = self.makeTime(self.configurationProvider.getParam('lightning_start'))
        endTime = self.makeTime(self.configurationProvider.getParam('lightning_end'))
        now = datetime.datetime.now().time()
        if (not self.lightActivated):
            if (now > startTime and now < endTime):
                startDevice(GPIO_LIGHT)
                self.lightActivated = True
                print('Light activated at '+str(now))
        else:
            if (now < startTime or now > endTime):
                stopDevice(GPIO_LIGHT)
                self.lightActivated = False
                print('Light deactivated at '+str(now))

    def activatePumpFixed(self):
        """Activate or deactivate pump based on configured start & duration time"""
        startTime = self.makeTime(self.configurationProvider.getParam('watering_start'))
        endTime = self.addSecs(startTime, self.configurationProvider.getParam('watering_duration'))
        # print('fixed watering scheme from '+str(startTime)+' to '+str(endTime))
        now = datetime.datetime.now().time()
        if (not self.pumpActivated):
            if (now > startTime and now < endTime):
                startDevice(GPIO_PUMP)
                self.pumpActivated = True
                print('Pump activated at '+str(now))
        else:
            if (now < startTime or now > endTime):
                stopDevice(GPIO_PUMP)
                self.pumpActivated = False
                print('Pump deactivated at '+str(now))

    def activatePumpDynamic(self, humidity):
        """Activate or deactivate pump based on threshold and lag value"""
        th = self.configurationProvider.getParam('watering_threshold')
        lag = self.configurationProvider.getParam('watering_threshold_lag')
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
                    startDevice(GPIO_PUMP)
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
                    stopDevice(GPIO_PUMP)
                    self.pumpActivated = False
                    self.humRaisedAbove = now
                    print('humRaisedAbove='+str(self.humRaisedAbove)+', lagUntil='+str(lagUntil))
                    print('humidity is '+str(humidity)+', pump deactivated at '+str(now))


    # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
    def readadc(self, adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
            return -1

        GPIO.output(cspin, True)
        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
            if (commandout & 0x80):
                GPIO.output(mosipin, True)
            else:
                GPIO.output(mosipin, False)
            commandout <<= 1
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)
            adcout <<= 1
            if (GPIO.input(misopin)):
                adcout |= 0x1

        GPIO.output(cspin, True)

        adcout >>= 1       # first bit is 'null' so drop it
        return adcout


    def run(self):
        """The main loop"""
        print("DeviceControl starting ")
        while (not self.stopEvent.is_set()):

            # read the analog pin
            hsense = self.readadc(sensor_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
            set_humidity = hsense / 10.24        # convert 10bit adc0 (0-1024) sensor out read into 0-100 level
            set_humidity = round(set_humidity)   # round out decimal value
            humidity = int(set_humidity)         # cast volume as integer

            print(str(datetime.datetime.now().time())+' humidity='+str(humidity))

            if self.configurationProvider.getParam('watering_threshold') == 'dynamic':
                self.activatePumpDynamic(humidity)
            else:
                self.activatePumpFixed()
            self.activateLight()

            self.dataProvider.setData(humidity, self.pumpActivated, self.lightActivated)
            time.sleep(self.configurationProvider.getParam('device_poll_interval'))

        # turn off devices
        stopDevice(GPIO_LIGHT)
        stopDevice(GPIO_PUMP)

        print('DeviceControl stopped')

