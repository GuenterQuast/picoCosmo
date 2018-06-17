#!/usr/bin/python3
# -*- coding: utf-8 -*-
# script runCosmo.py
'''
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

  Functions:
 
    - set up PicoScope channel ranges and trigger
    - PicoScope configuration from yaml file
    - acquire data (implemented as subprocess)
    - manage event data and distribute to obligatory and random consumers
    - analyse data: trigger validation, search for coincidences and double-pulses
    - live plot of data rates, storage of filtered data (raw data and oscilloscope
      pictures, double-pulse features)
'''

from __future__ import print_function, division, unicode_literals
from __future__ import absolute_import

import sys, time, yaml, numpy as np, threading
import multiprocessing as mp

# import relevant pieces from picodaqa
import picodaqa.picoConfig
import picodaqa.BufferMan as BMan

# animated displays running as background processes/threads
from picodaqa.mpOsci import mpOsci
from picodaqa.mpVMeter import mpVMeter
from picodaqa.mpRMeter import mpRMeter

# import pulse analyis
from picocosmo.PulseFilter import *

# !!!!
# import matplotlib.pyplot as plt
# !!!! matplot can only be used if no other active thread is using it 

# --------------------------------------------------------------
#     scope settings defined in .yaml-File, see picoConfig
# --------------------------------------------------------------


# some helper functions 

def stop_processes(proclst):
  '''
    Close all running processes at end of run
  '''
  for p in proclst: # stop all sub-processes
    if p.is_alive():
      print('    terminating ' + p.name)
      p.terminate()
    else:
      print('    ' + p.name + ' terminated ')
  time.sleep(2)

if __name__ == "__main__": # - - - - - - - - - - - - - - - - - - - - - -

  print('\n*==* script ' + sys.argv[0] + ' running \n')

# check for / read command line arguments
  # read DAQ configuration file
  if len(sys.argv)==2:
    DAQconfFile = sys.argv[1]
  else: 
    DAQconfFile = 'default.daq'
  print('    DAQconfiguration from file ' + DAQconfFile)
  try:
    with open(DAQconfFile) as f:
      DAQconfdict=yaml.load(f)
  except:
    print('     failed to read DAQ configuration file ' + DAQconfFile)
    exit(1)

  if "DeviceFile" in DAQconfdict: 
    DeviceFile = DAQconfdict["DeviceFile"] # configuration file for scope
  else:
    print('     no device configuration file - exiting')
    exit(1)

  if "BMfile" in DAQconfdict: 
    BMfile = DAQconfdict["BMfile"] # Buffer Manager configuration file 
  else:
    print('     no BM configuration file - exiting')
    exit(1)

  if "PFfile" in DAQconfdict: 
    PFfile = DAQconfdict["PFfile"] # Buffer Manager configuration file 
  else:
    print('     no pulse filter configuration file - exiting')
    exit(1)

  if 'DAQmodules' in DAQconfdict:
    modules = DAQconfdict["DAQmodules"]
  else:
    modules = [] 
  if "verbose" in DAQconfdict: 
    verbose = DAQconfdict["verbose"]
  else:
    verbose = 1   # print (detailed) info if >0 
    
  # read scope configuration file
  print('    Device configuration from file ' + DeviceFile)
  try:
    with open(DeviceFile) as f:
      PSconfdict=yaml.load(f)
  except:
    print('     failed to read scope configuration file ' + DeviceFile)
    exit(1)

  # read Buffer Manager configuration file
  print('    Buffer Manager configuration from file ' + BMfile)
  try:
    with open(BMfile) as f:
        BMconfdict=yaml.load(f)
  except:
   print('     failed to read BM input file ' + BMfile)
   exit(1)

  # read Pulse Filter configuration file
  print('    Pulse Filter configuration from file ' + PFfile)
  try:   
    with open(PFfile) as f:
      PFconfdict = yaml.load(f)
  except:
   print('     failed to read Pulse Filter input file ' + PFfile)
   exit(1)

# initialisation
  print(' -> initializing PicoScope')

# configure and initialize PicoScope
  # set appropriate defaults for this use-case
  if 'frqSG' not in PSconfdict:
    PSconfdict['frqSG'] = 0.
  if 'trgTO' not in PSconfdict:
    PSconfdict['trgTO'] = 5000
    
  PSconf = picodaqa.picoConfig.PSconfig(PSconfdict)
  PSconf.init()
  # copy some of the important configuration variables ...
  NChannels = PSconf.NChannels # number of channels in use
  TSampling = PSconf.TSampling # sampling interval
  NSamples = PSconf.NSamples   # number of samples
  
# configure Buffer Manager  ...
  print(' -> initializing BufferMan')
  BM = BMan.BufferMan(BMconfdict, PSconf)
# ... tell device what its buffer manager is ...
  PSconf.setBufferManagerPointer(BM)

# ... and start data acquisition thread.
  if verbose:
    print(" -> starting Buffer Manager Threads")   
  BM.start() # set up buffer manager processes  

  if 'DAQmodules' in BMconfdict:
    modules = modules + BMconfdict["DAQmodules"]
                       
# list of modules (= backgound processes) to start
  if type(modules) != list:  
    modules = [modules]
#

  if 'modules' in PFconfdict:
    PFmodules = PFconfdict['modules']
  else:
    PFmodules = ['RMeter', 'Hists', 'Display' ]

# run PulseFilter: signal filtering and analysis
  print(' -> initializing PulseFilter')
  PF = PulseFilter( BM, PFconfdict, 1)
  #                 BM   config   verbose    
  PF.run()
  time.sleep(1.)

# ...start run
  BM.run() 

# --- LOOP
  try:
# ->> read keyboard (control Buffermanager)<<- 
    BM.kbdCntrl()
    print(sys.argv[0]+': End command received - closing down ...')

# ---> user-specific end-of-run code could go here
    print('Data Acquisition ended normally')
# <---

  except KeyboardInterrupt:
    print(sys.argv[0]+': keyboard interrupt - closing down ...')
    BM.end()  # shut down BufferManager
    time.sleep(3.)
    PF.end()

  finally:
# END: code to clean up
    PSconf.closeDevice() # close down hardware device
    PF.end()  # stop PulseFilter sub-processes
    print('*==* runCosmo: normal end')
    
