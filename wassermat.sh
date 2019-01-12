#!/usr/bin/env bash

# To use as systemd service create file "/lib/systemd/system/wassermat.service":
#
# [Unit]
# Description=wassermat Service
# After=multi-user.target
#
# [Service]
# Type=idle
# ExecStart=/home/pi/wassermat/wassermat.sh
#
# [Install]
# WantedBy=multi-user.target
#
cd /home/pi/wassermat/pi
source env/bin/activate
cd src
./wassermat.py

