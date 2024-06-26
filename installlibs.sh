#!/bin/bash
#
# script to install libraries picoCosmo depends on
#    for debian-based systems like debian, ubuntu, mint
# ------------------------------------------------

sudo apt-get install python3-yaml
sudo apt-get install python3-scipy
sudo apt-get install python3-matplotlib
sudo apt-get install python3-pyqt5
sudo apt-get install libatlas-base-dev # needed to build nupmy

# install this package (picoCosmo) 
## sudo pip3 install .

sudo pip3 install libs/whl/*.whl # python wheels
#sudo pip3 install libs/tgz/*.tar.gz # python packages 

# libraries by Pico Technology for Picoscope 
#   see  https://www.picotech.com/downloads

# for Raspberry Pi only
#!sudo dpkg -i libs/RasPi/picoscopelibs/*.deb # picoscope 
#!sudo usermod -a -G tty pi # grant acces to USB for user pi
