## Resources

this repository: ```https://github.com/matthislussi/wassermat.git```


### GCP
```
https://medium.com/google-cloud/build-a-weather-station-using-google-cloud-iot-core-and-mongooseos-7a78b69822c5
https://github.com/GoogleCloudPlatform/python-docs-samples.git
```

### Raspi
```
https://computers.tutsplus.com/tutorials/build-a-raspberry-pi-moisture-sensor-to-monitor-your-plants--mac-52875
https://learn.adafruit.com/reading-a-analog-in-and-controlling-audio-volume-with-the-raspberry-pi/overview
```


## google cloud sdk

- download from google
```
cd ~/stash/projects.ext/google-cloud-sdk/
./install.sh
```


## pyenv
```
brew install pyenv
brew install pyenv-virtualenv
pyenv virtualenv 3.6.7 wassermat
pyenv local wassermat
pip install --proxy http://proxy.adnovum.ch:3128 -r requirements.txt
```


## Firebase installation & configuration

- project=wassermat
```
npm install -g firebase-tools
firebase login
firebase init
firebase functions:config:set bigquery.datasetname="wassermat_iot" bigquery.tablename="raw_data"
firebase deploy --only functions
firebase functions:config:get
```


## Big Query configuration

- project=wassermat
- dataset=wassermat_iot
- table=raw_data
  - deviceId:STRING:REQUIRED
  - timestamp:TIMESTAMP:REQUIRED
  - humidity:FLOAT:REQUIRED
  - pumpActive:BOOLEAN:REQUIRED
  - lightActive:BOOLEAN:REQUIRED



## Install & configure Raspbian

Taken from ``https://www.raspberrypi.org/forums/viewtopic.php?t=145706```

- Download the latest Raspbian stretch-light image from https://www.raspberrypi.org/downloads/raspbian/ -> 2018-11-13-raspbian-stretch-lite.zip
- Download the Etcher image writing software from https://etcher.io/
- Install Etcher and use it to write the Raspbian image to your SD card.
- On the small FAT32 "boot" partition, create a file with the name ssh (or ssh.txt). It can be empty, the contents don't matter.
- To connect to a wireless network, create another file on the card called wpa_supplicant.conf, which has the following inside:
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=CH

network={
    ssid="Your network name (router SSID)"
    psk="Your WPA/WPA2 security key"
    key_mgmt=WPA-PSK
    id_str="network1"
}
network={
    ssid="Your network name (router SSID)"
    psk="Your WPA/WPA2 security key"
    key_mgmt=WPA-PSK
    id_str="network2"
}
```

- If you have a Zeroconf network service installed (Apple's iTunes, Bonjour or Quicktime install Zeroconf), you can 
  SSH into pi@raspberrypi.local (provided you don't have any other Pi computers on your network with the same default hostname). 
  Otherwise you must SSH into your Pi's IP address, which you can find by logging into your router and checking the list 
  of connected clients, or using a network scanner app (like Fing for smartphones) to find your Pi on your network.
- update ```sudo apt-get update```
- upgrade ```sudo apt-get dist-upgrade```
- change default pwd 'raspberry'w. passwd
- adjust timezone: sudo raspi-config

### install python 3.6.7

run script ```pi/python3_install.sh```


### get sources
```
sudo apt-get install git
git clone https://github.com/matthislussi/wassermat.git
cd wassermat
```

### create virtual env
```
cd pi

sudo apt-get install python3.7-venv libffi-dev

apt-get install python3.7-venv

python3.7 -m venv env --without-pip
source env/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python
pip install -r requirements.txt
```

### install service

- create ```/lib/systemd/system/wassermat.service```
```
[Unit]
Description=wassermat Service
After=multi-user.target

[Service]
Type=idle
ExecStart=/home/pi/wassermat/wassermat.sh
WorkingDirectory=/home/pi/wassermat
Restart=always
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
```

- enable service
```
sudo chmod 644 /lib/systemd/system/wassermat.service
sudo systemctl daemon-reload
sudo systemctl enable wassermat.service
sudo reboot
```

- logging: ```journalctl -u wassermat -b```

### Devices
```
# GPIO.LOW = active, GPIO.LOW = inactive
GPIO_PUMP = 8
GPIO_LIGHT = 22
```

### Humidity Sensor

- SPI port on the ADC to the Cobbler
```
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

sensor_adc = 0;
```




