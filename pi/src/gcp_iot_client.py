#!/usr/bin/env python3

import sys
import datetime
import random
import ssl
import time
import jwt
import paho.mqtt.client as mqtt
import json
import threading

# gcp configuration
device_id = 'raspi1'
sub_topic = 'events'
project_id = 'wassermat'
cloud_region = 'europe-west1'
registry_id = 'inventory1'
private_key_file = '../resources/rsa_private.pem'
algorithm = 'RS256'
ca_certs = '../resources/roots.pem'
mqtt_bridge_hostname = 'mqtt.googleapis.com'
mqtt_bridge_port = 8883

# system configuration
jwt_expires_minutes = 20
# The initial backoff time after a disconnection occurs, in seconds.
minimum_backoff_time = 1
# The maximum backoff time before giving up, in seconds.
MAXIMUM_BACKOFF_TIME = 32

# Whether to wait with exponential backoff before publishing.
should_backoff = False

# initial application configuration (overwritable from gcp)

# {
#     "gcp_send_interval": 3,
#     "humidity_threshold": 40,
#     "humidity_threshold_lag": 10,
#     "lightning_start": "08:00",
#     "lightning_end": "20:00"
# }

class GcpIotClient (threading.Thread):
    'The Google Clout IOT core client thread'

    def __init__(self, dataProvider, configurationProvider, stopEvent):
        super(GcpIotClient, self).__init__()
        self.stopEvent = stopEvent
        self.dataProvider = dataProvider
        self.configurationProvider = configurationProvider

    def create_jwt(self, project_id, private_key_file, algorithm):
        token = {
            # The time that the token was issued at
            'iat': datetime.datetime.utcnow(),
            # The time the token expires.
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            # The audience field should always be set to the GCP project id.
            'aud': project_id
        }

        # Read the private key file.
        with open(private_key_file, 'r') as f:
            private_key = f.read()

        print('Creating JWT using {} from private key file {}'.format(
            algorithm, private_key_file))

        return jwt.encode(token, private_key, algorithm=algorithm)


    def error_str(self, rc):
        """Convert a Paho error to a human readable string."""
        return '{}: {}'.format(rc, mqtt.error_string(rc))


    def on_connect(self, unused_client, unused_userdata, unused_flags, rc):
        """Callback for when a device connects."""
        print('on_connect', mqtt.connack_string(rc))

        # After a successful connect, reset backoff time and stop backing off.
        global should_backoff
        global minimum_backoff_time
        should_backoff = False
        minimum_backoff_time = 1


    def on_disconnect(self, unused_client, unused_userdata, rc):
        """Paho callback for when a device disconnects."""
        print('on_disconnect', self.error_str(rc))

        # Since a disconnect occurred, the next loop iteration will wait with
        # exponential backoff.
        global should_backoff
        should_backoff = True


    def on_publish(self, unused_client, unused_userdata, unused_mid):
        """Paho callback when a message is sent to the broker."""


    def on_message(self, unused_client, unused_userdata, message):
        """Callback when the device receives a message on a subscription."""
        global config
        if (message.topic == '/devices/raspi1/config'):
            try:
                self.configurationProvider.write(json.loads(message.payload))
            except:
                print("on_message, unexpected error:", sys.exc_info()[0])
                raise
        else:
            print('on_message: message topic "'+message.topic+'" not handled')


    def get_client(self, project_id, cloud_region, registry_id, device_id, private_key_file,
            algorithm, ca_certs, mqtt_bridge_hostname, mqtt_bridge_port):
        """Create our MQTT client. The client_id is a unique string that identifies
        this device. For Google Cloud IoT Core, it must be in the format below."""
        client = mqtt.Client(
            client_id=('projects/{}/locations/{}/registries/{}/devices/{}'
                .format(
                project_id,
                cloud_region,
                registry_id,
                device_id)))

        # With Google Cloud IoT Core, the username field is ignored, and the
        # password field is used to transmit a JWT to authorize the device.
        client.username_pw_set(
            username='unused',
            password=self.create_jwt(
                project_id, private_key_file, algorithm))

        # Enable SSL/TLS support.
        client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

        # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
        # describes additional callbacks that Paho supports. In this example, the
        # callbacks just print to standard out.
        client.on_connect = self.on_connect
        client.on_publish = self.on_publish
        client.on_disconnect = self.on_disconnect
        client.on_message = self.on_message

        # Connect to the Google MQTT bridge.
        client.connect(mqtt_bridge_hostname, mqtt_bridge_port)

        # This is the topic that the device will receive configuration updates on.
        mqtt_config_topic = '/devices/{}/config'.format(device_id)

        # Subscribe to the config topic.
        client.subscribe(mqtt_config_topic, qos=1)

        # The topic that the device will receive commands on.
        mqtt_command_topic = '/devices/{}/commands/#'.format(device_id)

        # Subscribe to the commands topic, QoS 1 enables message acknowledgement.
        print('Subscribing to {}'.format(mqtt_command_topic))
        client.subscribe(mqtt_command_topic, qos=0)

        return client


    def run(self):
        print ("GcpIotClient starting ")
        global minimum_backoff_time

        # Publish to the events or state topic based on the flag.
        mqtt_topic = '/devices/{}/{}'.format(device_id, sub_topic)

        jwt_iat = datetime.datetime.utcnow()
        jwt_exp_mins = jwt_expires_minutes

        client = self.get_client(
            project_id, cloud_region, registry_id, device_id,
            private_key_file, algorithm, ca_certs,
            mqtt_bridge_hostname, mqtt_bridge_port)

        while (not self.stopEvent.is_set()):
            # Process network events.
            client.loop()

            # Wait if backoff is required.
            if should_backoff:
                # If backoff time is too large, give up.
                if minimum_backoff_time > MAXIMUM_BACKOFF_TIME:
                    print('Exceeded maximum backoff time. Giving up.')
                    break

                # Otherwise, wait and connect again.
                delay = minimum_backoff_time + random.randint(0, 1000) / 1000.0
                print('Waiting for {} before reconnecting.'.format(delay))
                time.sleep(delay)
                minimum_backoff_time *= 2
                client.connect(mqtt_bridge_hostname, mqtt_bridge_port)

            payload = self.dataProvider.getData()
            print('Publishing message \'{}\''.format(payload))

            seconds_since_issue = (datetime.datetime.utcnow() - jwt_iat).seconds
            if seconds_since_issue > 60 * jwt_exp_mins:
                print('Refreshing token after {}s').format(seconds_since_issue)
                jwt_iat = datetime.datetime.utcnow()
                client = self.get_client(
                    project_id, cloud_region,
                    registry_id, device_id, private_key_file,
                    algorithm, ca_certs, mqtt_bridge_hostname,
                    mqtt_bridge_port)

            client.publish(mqtt_topic, payload, qos=1)

            # Send events every second. State should not be updated as often
            time.sleep(self.configurationProvider.getParam('gcp_send_interval'))

        print('GcpIotClient stopped')
