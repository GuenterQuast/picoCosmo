#!/bin/bash
#
# script to initially copy files to user direcotry ~/picoCosmo/
#

USERDIR="picoCosmo"  # user directory

# -----------------------------------------

DIR=$HOME/$USERDIR
echo "copying files to "$DIR

mkdir -p $DIR

if [ -d $DIR ]; then
  # enter here, if direcotry exists
#
    # create desktop icon
  cp -auv *.desktop $HOME/Desktop

    # copy documentation
  mkdir -p $DIR/doc
  cp -auv doc/Anleitung.pdf $DIR/doc/
  cp -auv README_de.pdf $DIR
  cp -auv doc/*.html $DIR/doc/
#
    #copy python code
  cp -auv CosmoGui.py $DIR
  cp -auv runCosmo.py $DIR
  cp -auv images $DIR
#  
    #copy config examples
  cp -auv config/ $DIR
  cp -auv *.daq $DIR
#
fi
