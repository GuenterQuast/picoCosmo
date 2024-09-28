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

# install special python weehls
python -m pip install libs/whl/*.whl # python wheels

# libraries by Pico Technology for Picoscope 
#   see  https://www.picotech.com/downloads

# for Raspberry Pi only
#!sudo dpkg -i libs/RasPi/picoscopelibs/*.deb # picoscope 
#!sudo usermod -a -G tty pi # grant acces to USB for user pi

# finally, install this package (picoCosmo)
# and the scripts CosmoGui.py and runCosmo.py
python -m pip install .

