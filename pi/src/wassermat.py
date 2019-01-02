#!/usr/bin/env python3

# Main wassermat system controller

import signal
import threading

from providers import DataProvider
from providers import ConfigurationProvider
from gcp_iot_client import GcpIotClient
from device_control import DeviceControl

CONFIG_FILE = '../resources/wassermat.json'

threads = []
stopEvent = threading.Event()
configuration = ConfigurationProvider(CONFIG_FILE)
data = DataProvider()

def quit_gracefully(signum, frame):
    print('quit_gracefully called')
    stopEvent.set()

signal.signal(signal.SIGINT, quit_gracefully)
signal.signal(signal.SIGTERM, quit_gracefully)

def main():

    thread1 = DeviceControl(data, configuration, stopEvent)
    thread1.start()
    threads.append(thread1)

    thread2 = GcpIotClient(data, configuration, stopEvent)
    thread2.start()
    threads.append(thread2)

    # Wait for all threads to complete
    for t in threads:
        t.join()

    print ("Exiting Main Thread")


if __name__ == '__main__':
    main()
