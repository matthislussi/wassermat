#!/usr/bin/env bash

# from https://www.ramoonus.nl/2018/06/30/installing-python-3-7-on-raspberry-pi/

RELEASE=3.7.1

# install dependencies
sudo apt-get update
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev

# Compile (takes a while!)
wget https://www.python.org/ftp/python/$RELEASE/Python-$RELEASE.tar.xz
tar xf Python-$RELEASE.tar.xz
cd Python-$RELEASE
./configure --prefix=/usr/local/opt/python-$RELEASE
make -j 4

# Install
sudo make altinstall

# Make Python 3.7 the default version, make aliases
sudo ln -s /usr/local/opt/python-$RELEASE/bin/pydoc3.7 /usr/bin/pydoc3.7
sudo ln -s /usr/local/opt/python-$RELEASE/bin/python3.7 /usr/bin/python3.7
sudo ln -s /usr/local/opt/python-$RELEASE/bin/python3.7m /usr/bin/python3.7m
sudo ln -s /usr/local/opt/python-$RELEASE/bin/pyvenv-3.7 /usr/bin/pyvenv-3.7
sudo ln -s /usr/local/opt/python-$RELEASE/bin/pip3.7 /usr/bin/pip3.7
alias python='/usr/bin/python3.7'
alias python3='/usr/bin/python3.7'
alias pip='/usr/bin/pip3.7'

ls /usr/bin/python*
cd ..
sudo rm -r Python-$RELEASE
rm Python-$RELEASE.tar.xz
. ~/.bashrc

# make sure /usr/local/lib is in the path (/etc/ld.so.conf.d/libc.conf)
sudo ldconfig

