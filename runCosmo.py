#!/usr/bin/python3
# -*- coding: utf-8 -*-
# script runCosmo.py
"""
  **runCosmo** run Data Aquisition with Picoscpe 
   (modified version of runDAQ from picoDAQ project) 

  Relies on python drivers by Colin O'Flynn and Mark Harfouche,
  see https://github.com/colinoflynn/pico-python

  and on package *picodaqa*,
  see https://github.com/GuenterQuast/picoDAQ

    - initialisation of picoScope device vial class picoConfig 
    - creates a BufferMan instance
    - graphics implemented with matplotlib

  tested with  PS2000a, PS3000a and PS4000

    - set up PicoScope channel ranges and trigger
    - PicoScope configuration from yaml file
    - acquire data (implemented as subprocess)
    - manage event data and distribute to obligatory and random consumers
    - analyse data: trigger validation, search for coincidences and double-pulses
    - live plot of data rates, storage of filtered data (raw data and oscilloscope
      pictures, double-pulse features)

    This code simply calls the executable part of module picocosmo.runCosmoDAQ

"""

from picocosmo.runCosmoDAQ import *
import sys, subprocess

if __name__ == "__main__":  # - - - - - - - - - - - - - - - - - - - -

    if len(sys.argv) != 2:
        print("\n!!! runCosmo.py usage:\n" + 10 * ' ' + "runCosmo.py <config>.daq\n")
        exit()
        
    arg = sys.argv[1]
    
    subprocess.run(args=
        [sys.executable, '-m', 'picocosmo.runCosmoDAQ', arg])

