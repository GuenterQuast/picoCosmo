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

python -m install libs/whl/*.whl # python wheels
#sudo pip3 install libs/tgz/*.tar.gz # python packages 

# check for virtual python environment and create if not present
PHYPYENV="/usr/local/share/phypy"
if [ -d "$PHYPYENV" ];
    then
      echo "installing in virtual environment $PHYPYENV"
    else
      echo "creating Python virtual environment in directory $PHYPYENV"
      sudo mkdir $PHYPYENV
      sudo chown $USER $PHYPYENV
      sudo chmod a+rwx $PHYPYENV  # would be better to use separate group phypi
      python3 -m venv "$PHYPYENV" --system-site-packages 

      # copy activation script 
      cp libs/RasPi/activata_phypy.sh ~
fi

# activate virtual environment
source "$PHYPYENV"/bin/activate

# install this package (picoCosmo) 
## sudo pip3 install .
python -m pip install --no-build-isolation .

# install PicoScope C libraries for USB oscilloscope
sudo dpkg -i libs/RasPi/picoscopelibs/*.deb # picoscope 
sudo usermod -a -G tty pi # grant acces to USB for user pi

# generate desktop icons
cp libs/RasPi/*.desktop ~/Desktop

