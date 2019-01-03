## Resources

this repository: ```https://github.com/hlussi/wassermat.git```


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



## Install Raspbian

Taken from ``https://www.raspberrypi.org/forums/viewtopic.php?t=145706```

- Download the latest Raspbian image from https://www.raspberrypi.org/downloads/raspbian/
- Download the Etcher image writing software from https://etcher.io/
- Install Etcher and use it to write the Raspbian image to your SD card.
  - You don't need to extract the image or format the card prior to writing. Just run Etcher, choose the Raspbian .zip you 
    downloaded, pick your SD card and write. 
  - If you have trouble, verify the SHA256 checksum of the download.
  - Writing an image to your card will erase everything previously on it!
  - Remove and reinsert the SD card so that your Windows or Mac PC can see the small FAT32 partition on the card (labelled "boot").
  - If you get a message telling you the card must be formatted, cancel it (do NOT format the card).
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
}
```
  - Edit country=, ssid= and psk= with your information and save the file.
  - Use the 2 letter country abbreviation in CAPS.
  - Use a pure text editor, not a word processor, to edit the wpa_supplicant.conf file.
  - Make sure that both files are in the main directory of the small FAT32 partition, not in any folder.
  - Safely eject the card from your PC and use it to boot the Pi.

- If Raspbian finds an ssh file it will enable SSH and delete the file. If it finds a wpa_supplicant.conf file, it will move it 
  to its correct location and connect to your wireless network. Give your Pi some time to boot and connect to your network 
  (the first boot always takes longer), then you should be able to SSH into the Pi and configure it how you like.
- If you have a Zeroconf network service installed (Apple's iTunes, Bonjour or Quicktime install Zeroconf), you can 
  SSH into pi@raspberrypi.local (provided you don't have any other Pi computers on your network with the same default hostname). 
  Otherwise you must SSH into your Pi's IP address, which you can find by logging into your router and checking the list 
  of connected clients, or using a network scanner app (like Fing for smartphones) to find your Pi on your network.
- If you are using the Desktop version of Raspbian, and once you have successfully connected via SSH, you can use the 
  raspi-config utility to enable the VNC server and then use a RealVNC Viewer on your Windows/Mac PC to get remote desktop 
  access to the Pi.

Note: If you have attempted this and failed, then unplugged power to turn off your Pi, you should start over with a 
freshly imaged card. Improperly powering down the Pi can cause SSH key generation to fail, which will prevent SSH logins 
(even if everything else is correct).

Also note that the Mac's default note editor (I forget the exact name) automatically converts straight quotes to curly quotes, 
and that will break the wpa_supplicant.conf file, so be sure to disable that in the settings before creating or editing that 
file

## Config Raspberry

- default pwd changed (passwd)
- adjust timezone: sudo raspi-config

### install python 3.6.7
```
sudo apt-get install build-essential checkinstall
sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev

cd /usr/bin
sudo tar xzf Python-3.6.7.tgz
sudo bash
cd Python-3.6.7
./configure
make -j4
make altinstall

```

### get sources
```
sudo apt-get install git
git clone https://github.com/hlussi/wassermat.git
cd wassermat
```

### create virtual env
```
cd pi
sudo apt-get install python3-venv libffi-dev
python3.6 -m venv env
env/bin/pip install -U pip setuptools wheel
source env/bin/activate
pip install -r requirements.txt
```
