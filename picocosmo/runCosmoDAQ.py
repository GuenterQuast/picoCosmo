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

  Functions:
 
    - set up PicoScope channel ranges and trigger
    - PicoScope configuration from yaml file
    - acquire data (implemented as subprocess)
    - manage event data and distribute to obligatory and random consumers
    - analyse data: trigger validation, search for coincidences and double-pulses
    - live plot of data rates, storage of filtered data (raw data and oscilloscope
      pictures, double-pulse features)
"""

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
def kbdwait():
  ''' 
    wait for keyboard input
  '''
  # 1st, remove pyhton 2 vs. python 3 incompatibility for keyboard input
  if sys.version_info[:2] <=(2,7):
    get_input = raw_input
  else: 
    get_input = input
 #  wait for input
  get_input(50*' '+'type <ret> to exit -> ')

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

  
class runCosmoDAQ(object):

  def __init__(self, verbose=1):
    self.verbose = verbose

    # check for / read command line arguments
    # read DAQ configuration file
    if len(sys.argv)==2:
      self.DAQconfFile = sys.argv[1]
    else: 
      self.DAQconfFile = 'default.daq'
    print('    DAQconfiguration from file ' + self.DAQconfFile)
    try:
      with open(self.DAQconfFile) as f:
        self.DAQconfdict = yaml.load(f, Loader=yaml.Loader)
    except Exception as e:
      print('     failed to read DAQ configuration file ' + self.DAQconfFile)
      print(str(e))
      kbdwait()
      exit(1)

    if "DeviceFile" in self.DAQconfdict: 
      self.DeviceFile = self.DAQconfdict["DeviceFile"] # configuration file for scope
    else:
      print('     no device configuration file - exiting')
      kbdwait()
      exit(1)

    if "BMfile" in self.DAQconfdict: 
      self.BMfile = self.DAQconfdict["BMfile"] # Buffer Manager configuration file 
    else:
      print('     no BM configuration file - exiting')
      kbdwait()
      exit(1)

    if "verbose" in self.DAQconfdict: 
      self.verbose= self.DAQconfdict["verbose"] # Buffer Manager configuration file 
    else:
      self.verbose = 1
 
    if "PFfile" in self.DAQconfdict: 
      self.PFfile = self.DAQconfdict["PFfile"] # Buffer Manager configuration file 
    else:
      print('     no pulse filter configuration file - exiting')
      kbdwait()
      exit(1)

    if 'DAQmodules' in self.DAQconfdict:
      self.modules = self.DAQconfdict["DAQmodules"]
    else:
      self.modules = [] 

    # read scope configuration file
    print('    Device configuration from file ' + self.DeviceFile)
    try:
      with open(self.DeviceFile) as f:
        self.PSconfdict = yaml.load(f, Loader=yaml.Loader)
    except Exception as e:
      print('     failed to read scope configuration file ' + self.DeviceFile)
      print(str(e))
      kbdwait()
      exit(1)

    # read Buffer Manager configuration file
    print('    Buffer Manager configuration from file ' + self.BMfile)
    try:
      with open(self.BMfile) as f:
        self.BMconfdict=yaml.load(f, Loader=yaml.Loader)
    except Exception as e:
      print('     failed to read BM input file ' + self.BMfile)
      print(str(e))
      kbdwait()
      exit(1)

    # read Pulse Filter configuration file
    print('    Pulse Filter configuration from file ' + self.PFfile)
    try:   
      with open(self.PFfile) as f:
        self.PFconfdict = yaml.load(f, Loader=yaml.Loader)
    except Exception as e:
      print('     failed to read Pulse Filter input file ' + PFfile)
      print(str(e))
      kbdwait()
      exit(1)

  def setup(self):
    """set-up picoscope and processes
    """

    # initialize PicoScope
    print(' -> initializing PicoScope')
  # configure and initialize PicoScope
  #   set appropriate defaults for this use-case
    if 'frqSG' not in self.PSconfdict:
      self.PSconfdict['frqSG'] = 0.
    if 'trgTO' not in self.PSconfdict:
      self.PSconfdict['trgTO'] = 5000
    try:   
      self.PSconf = picodaqa.picoConfig.PSconfig(self.PSconfdict)
      self.PSconf.init()
    except Exception as e:
      print("!!! failed to set-up PicoScope device")
      print("Exception: ", e)
      exit(1)
    
    # copy some of the important configuration variables ...
    self.NChannels = self.PSconf.NChannels # number of channels in use
    self.TSampling = self.PSconf.TSampling # sampling interval
    self.NSamples = self.PSconf.NSamples   # number of samples
  
  # configure Buffer Manager  ...
    print(' -> initializing BufferMan')
    self.BM = BMan.BufferMan(self.BMconfdict, self.PSconf)
  # ... tell device what its buffer manager is ...
    self.PSconf.setBufferManagerPointer(self.BM)

  # ... and start data acquisition thread.
    if self.verbose:
      print(" -> starting Buffer Manager Threads")   
    self. BM.start() # set up buffer manager processes  

    if 'DAQmodules' in self.BMconfdict:
      self.modules = self.modules + self.BMconfdict["DAQmodules"]
                       
  # list of modules (= backgound processes) to start
    if type(self.modules) != list:  
      modules = [modules]
  #

    if 'modules' in self.PFconfdict:
      self.PFmodules = self.PFconfdict['modules']
    else:
      self.PFmodules = ['RMeter', 'Hists', 'Display' ]

  # run PulseFilter: signal filtering and analysis
    print(' -> initializing PulseFilter')
    PF = PulseFilter( self.BM, self.PFconfdict, self.verbose)
    #                 BM   config   verbose    
    PF.run()
    time.sleep(1.)

  def run(self):
    """Data acquition loop
    """

    # start Buffer Manager
    self.BM.run() 

    # --- DAQ LOOP
    try:
    # ->> read keyboard (control Buffermanager)<<- 
      self.BM.kbdCntrl()
      print(sys.argv[0]+': End command received - closing down ...')

    # ---> user-specific end-of-run code could go here
      print('Data Acquisition ended normally')
    # <---

    except KeyboardInterrupt:
      print(sys.argv[0]+': keyboard interrupt - closing down ...')
      self.BM.end()  # shut down BufferManager
      time.sleep(3.)
      self.PF.end()

    finally:
    # END: code to clean up
      self.PSconf.closeDevice() # close down hardware device
      self.PF.end()  # stop PulseFilter sub-processes
      print('*==* runCosmo: normal end')
        
if __name__ == "__main__": # - - - - - - - - - - - - - - - - - - - - - -

  print('\n*==* script ' + sys.argv[0] + ' running \n')

  daq = runCosmoDAQ(verbose=1)

  daq.setup()

  daq.run()
