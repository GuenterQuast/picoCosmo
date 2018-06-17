from __future__ import print_function,division,absolute_import,unicode_literals

# -- class PulseFilter 
import sys, os, time, yaml, numpy as np

from multiprocessing import Process, Queue

# animated displays running as background processes/threads
from picodaqa.mpRMeter import mpRMeter
from picodaqa.mpBDisplay import mpBDisplay
from picodaqa.mpHists import mpHists
from picodaqa.Oscilloscope import *


class PulseFilter(object):
  '''
  Analyse data read from CosMO detectors of Netzwerk Teilchenwelt
  with a PicoScope USB oscilloscpe

  Method: 
    Find a pulse similar to a template pulse by cross-correlatation with 
    template pulse

      - implemented as an obligatory consumer of BufferMan, 
        i.e. sees all data

      - pulse detection via correlation with reference pulse;

          - detected pulses are cleaned in a second step by subtracting 
           the pulse mean (increased sensitivity to pulse shape)

      - analysis proceeds in three steps:

          1. validation of pulse on trigger channel
          2. coincidences on other channels near validated trigger pulse
          3. seach for addtional pulses on any channel

  Results are viszalised as on-line displays (rate information and
  histograms of pulse properties) or dumped as raw wave-form
  information to a .yaml file or as "event pictures", i.e.
  oscilloscope displays, of wave-forms wiht delayed pulses 
  '''

  def __init__(self, BM, confDict = None, verbose=1):
    '''Args:    BufferManager instance as data provider
                configuration dictionary
    '''              

    self.BM = BM  # BufferMan instance
    self.confDict = confDict  # configuration
    self.verbose = verbose

    self.subprocs = [] # list of background processes
 
    self.setup() # setup everything else from information in confDict

  # --- end __init__

  def start_subprocesses(self, modules, histograms):
    '''Start sub-processes for live-displays
    '''
# set up data transfer Queues 
#  rate of accepted muons
    self.filtRateQ = None
    if 'RMeter' in modules:
      self.filtRateQ = Queue(1) # information queue for Filter
      self.subprocs.append(Process(name='RMeter',
             target = mpRMeter, 
             args=(self.filtRateQ, 12., 2500., 'muon rate history') ) )
#                  Queue  rate  update interval          

#  pulse shape and livetime histograms
    self.histQ = None
    if 'Hists' in modules:
      self.histQ = Queue(1) # information queue for Filter
      if histograms:
        HistDescr = histograms
      else:
        HistDescr = []
        HistDescr.append([0., 0.4, 50, 20., 'noise Trg. Pulse (V)', 0] )
#                   min max nbins ymax    title               lin/log
        HistDescr.append([0., 0.8, 50, 15., 'valid Trg. Pulse (V)', 0] )
        HistDescr.append([0., 15., 45, 7.5, 'Tau (µs)', 1] )
        HistDescr.append([0., 0.8, 50, 15., 'Pulse height (V)', 0] )

      self.subprocs.append(Process(name='Hists',
          target = mpHists, 
          args=(self.histQ, HistDescr, 2000., 'Filter Histograms') ) )
#                data Queue, Hist.Desrc  interval    

#  signal display
    self.VSigQ = None
    if 'Display' in modules:
      self.VSigQ = Queue(1) # information queue for Filter
      mode = 2 # 0:signed, 1: abs. 2: symmetric
      size = 1. # stretch factor for display
      self.subprocs.append(Process(name = 'ChannelSignals',
           target = mpBDisplay, 
           args=(self.VSigQ, self.BM.DevConf, mode, size, 'Panel Signals') ) )
#                 mp.Queue  Chan.Conf.            name          

# start sub-processes as deamons
    for p in self.subprocs:
      p.daemon = True
      p.start()    
      if self.verbose:
        print('      PF: starting process ', p.name, ' PID=', p.pid)

  def run(self):
    '''start Pulse Analysis as sub-process
    '''
    from multiprocessing import Process

    self.subprocs.append( Process( name='PulseAnalysis', 
                                   target=self.PAnalysis) ) 
    self.subprocs[-1].daemon = True
    self.subprocs[-1].start()
  # - end start_subprocesses()  -

  # helper functions to generate Reference Pulse for PulseFilter
  def trapezoidPulse(self, t, tr, ton, tf, tf2=0, toff=0., tr2=0., mode=0):
    '''
    create a single or double trapezoidal plulse, 
      normalised to pulse height one
         ______
        /      \  
     _ /_ _ _ _ \_ _ _ _ _ _ _   
                 \__________/
      r    on  f f2   off  r2 

    Args: 
     rise time, 
     on time, 
     fall time
     off-time  for bipolar pulse
     fall time for bipolar pulse
     mode: 0 single unipolar, 1: double bipolar
    '''

    from scipy.interpolate import interp1d

    ti = [0., tr, tr+ton, tr+ton+tf]
    ri = [0., 1.,     1.,     0. ]
    if mode: # for bipolar pulse
    # normalize neg. pulse to same integral as positive part
      voff = -(0.5*(tr+tf)+ton) / (0.5*(tf2+tr2)+toff) 
      ti = ti.append(tr+ton+tf+tf2)
      ri = ri.append(voff) 
      ti = ti.append(tr+ton+tf+tf2+toff)
      ri = ri.append(voff) 
      ti = ti.append(tr+ton+tf+tf2+toff+tr2)
      ri = ri.append(0.) 

    fpulse = interp1d(ti, ri, kind='linear', copy=False, assume_sorted= True)
    return fpulse(t)

  def setRefPulse(self, dT, taur=20E-9, tauon=12E-9, tauf=128E-9, mode=0,
                tauf2=0., tauoff=0., taur2=0.,
                pheight=-0.030):
    '''generate reference pulse shape for convolution filter
      Args: 
        time step
        rise time in sec
        fall-off time in sec
        pulse height in Volt
        mode : 0 uni-polar  1 bi-polar
    '''
    tp = taur + tauon + tauf
    l = np.int32( tp/dT +0.5 ) + 1  
    ti = np.linspace(0, tp, l)    
    rp = self.trapezoidPulse(ti, taur, tauon, tauf, mode) # uni-polar pulse
    rp = pheight * rp   # normalize to pulse height

    return rp

  def setReferencePulses(self, dT, refPulseDicts):
# generate reference pulse 
#   self.refP = self.setRefPulse(dT, taur, tauon, tauf, pheight)
    refP = []
    refPm = []
    lref = []
    for pDict in refPulseDicts:
      refP.append(self.setRefPulse(self.dT, **pDict) )
      refPm.append(refP[-1] - np.mean(refP[-1]) )
      lref.append(len(refP[-1]))
    self.refP = np.array(refP)
    self.refPm = np.array(refPm)
    self.lref = np.array(lref)

    Npulses=len(lref)
    self.taur = np.zeros(Npulses)
    self.tauon = np.zeros(Npulses)
    self.tauf = np.zeros(Npulses)
    self.pheight = np.zeros(Npulses)    
    for i in range(Npulses):
      self.taur[i] = refPulseDicts[i]['taur'] 
      self.tauon[i] = refPulseDicts[i]['tauon'] 
      self.tauf[i] =  refPulseDicts[i]['tauf']
      self.pheight[i] = refPulseDicts[i]['pheight'] 

    if self.verbose:
      print('*==*  Pulse Filter: pulse parameters set:')
      for iC in range(self.NChan):
        idP = min(iC, self.NShapes - 1) # Channel Pulse Shape 
        print(8*' '+\
            '%s: τ_r: %.3gs, τ_on: %.3gs, τ_f: %.3gs, height: %.3gV'\
          %(self.ChanNames[iC],
            self.taur[idP], self.tauon[idP], self.tauf[idP], self.pheight[idP]) )
      if self.useTrgShape:
        print(6*' '+'Trigger pulse shape:')
        print(8*' '\
                   +'%s: τ_r: %.3gs, τ_on: %.3gs, τ_f: %.3gs, height: %.3gV'\
           %(self.trgChan, 
             self.taur[-1], self.tauon[-1], self.tauf[-1], self.pheight[-1]) )

# calculate thresholds for correlation analysis
    # norm of reference pulse    
    self.pthr = np.sum(self.refP * self.refP, axis=1) 
    # norm of mean-subtracted reference pulse    
    self.pthrm = np.sum(self.refPm * self.refPm, axis=1) 

    if self.verbose > 1:
      print('PulseFilter: reference pulse(s)')
      for i in range(Npulses):
        print(np.array_str(self.refP[i]) )
        print('  thresholds: %.2g, %2g ' %(self.pthr[i], self.pthrm[i]))

  def setup(self):
    '''
    setup all internal variables from information provided in
    self.confDict
    '''

# buffermanager must be active at this stage
    if not self.BM.ACTIVE.value: 
      print("!!! pulseFilter: Buffer Manager not active, exiting")
      sys.exit(1)
    self.cId = self.BM.BMregister() # get a Buffer Manager Client Id

# print information to log-window via BufferManager prlog
    self.prlog = self.BM.prlog

  # read configuration dictionary
    try: 
      refPulseDicts=self.confDict['pulseShape']    
      self.NShapes = len(refPulseDicts)

      if 'trgPulseShape' in self.confDict:
        trgPulseDict=self.confDict['trgPulseShape'][0]    
        refPulseDicts.append(trgPulseDict)
        self.useTrgShape = True
      else:
        self.useTrgShape = False

      if "logFile" in self.confDict:
        logFile = self.confDict['logFile']
      else:
        logFile = None

      if "logFile2" in self.confDict:
        logFile2 = self.confDict['logFile2']
        if logFile2 == None: logFile2 = None
      else:
        logFile2 = 'dPFilt'

      if "rawFile" in self.confDict:
        rawFile = self.confDict['rawFile']
      else:
        rawFile = None

      if "pictFile" in self.confDict:
        pictDir = self.confDict['pictFile']
      else:
        pictDir = None
        
      if "modules" in self.confDict:
        modules = self.confDict['modules']
      else:
        modules = ['RMeter','Hists']

      if "histograms" in self.confDict:
        histograms = self.confDict['histograms']
      else:
        histograms = None

      if "doublePulse" in self.confDict:
        self.DPanalysis = self.confDict['doublePulse']
      else:
        self.DPanalysis = True      
      if not self.DPanalysis:  
        print("PF: no double pulse search")

    except:
      print('!!! PulseFilter failed to read pulseFilter configuration ')
      exit(1)

# now start sub-processes for live-displays
    self.start_subprocesses(modules, histograms)

# open and initialize output files
    datetime=time.strftime('%y%m%d-%H%M', time.localtime())
    if logFile is not None:
      self.logf = open(logFile + '_' + datetime+'.dat', 'w')
      print("# EvNr, EvT, Vs ...., Ts ...", 
        file=self.logf) # header line
    else:
      self.logf = None

    if logFile2 is not None:
      self.logfDP = open(logFile2 + '_' + datetime+'.dat', 'w', 1)
      print("# Nacc, Ndble, Tau, delT(iChan), ... V(iChan)", 
        file=self.logfDP) # header line 
    else:
      self.logfDP = None

    if rawFile is not None:
      self.rawf = open(rawFile + '_' + datetime+'.dat', 'w', 1)
      print("--- #raw waveforms",
        file=self.rawf) # header line     
      yaml.dump( {'OscConf': self.BM.DevConf.OscConfDict}, self.rawf )
      yaml.dump( {'pFConf' : self.confDict}, self.rawf )
      print('data: ',  file=self.rawf) # data tag    
    else:
      self.rawf = None  

    if pictDir is not None: # create a directory to store pictures
      self.pDir = (pictDir + '_' + datetime)
      if not os.path.exists(self.pDir): os.makedirs(self.pDir)
    # initialize oscolloscpe class used for plotting
      self.Osci = Oscilloscope(self.BM.DevConf.OscConfDict, 'DoublePulse') 
      self.figOs = self.Osci.fig
      self.Osci.init()
    else:
      self.pDir = None  

# retrieve relevant configuration parameters from BufferManager
    self.dT = self.BM.TSampling # get sampling interval
    self.idTprec = 2 # precision on time resolution of pulse search
    # precision on time resolution (in units of dT) 
    self.dTprec = self.idTprec * self.dT  
    self.NChan = self.BM.NChannels
    self.NSamples = self.BM.NSamples
    self.ChanNames = self.BM.DevConf.picoChannels   
    self.trgChan = self.BM.DevConf.trgChan     # trigger Channel
    # index of trigger T0
    self.idT0 = int(self.BM.DevConf.NSamples * self.BM.DevConf.pretrig) 
    self.iCtrg = -1
    for i, C in enumerate(self.ChanNames):   
      if C == self.trgChan: 
        self.iCtrg = i       # number of trigger Channel
        break

    # generate reference pulse and thresholds for PulseFilter  
    self.setReferencePulses(self.dT, refPulseDicts)

# --- end set-up

  
  def PAnalysis(self):
    '''Perform Pulse analysis
    '''
    from scipy.signal import argrelmax

# initialise event loop
    evcnt=0  # events seen
    Nval=0   # events with valid pulse shape on trigger channel
    Nacc=0
    Nacc2=0  # dual coincidences
    Nacc3=0  # triple coincidences
    Nacc4=0  # conincidence of four channels
    Ndble=0  # double pulses
    T0 = time.time()

# arrays for quantities to be histogrammed
    hnTrSigs = [] #  pulse height of noise signals
    hvTrSigs = [] #  pulse height of valid triggers
    hTaus = []  # deltaT of double pulses
    hVSigs = [] # pulse heights non-triggering channels
#
# copy important parameters to local variables
    verbose = self.verbose
    NChan = self.NChan # number of Channels
    iCtrg = self.iCtrg # trigger Channel
    dT = self.dT       # time base
    idT0 = self.idT0   # sample number of trigger point
    taur = self.taur   # pulse rise time
    tauon = self.tauon # pulse flat top
    idTprec = self.idTprec # precision of pulse timing
    refP = self.refP   # reference pulse(s)
    pthr = self.pthr   # pulse threshold(s)
    refPm = self.refPm # mean-subtacted reference pulse(s) ...
    pthrm = self.pthrm #  ... and relevant threshold(s)
    lref = self.lref  # length of reference pulse(s)

    if verbose:
      print("*==* Pulse Filter starting analysis")

# event loop
    while self.BM.ACTIVE.value:
      validated = False
      accepted = False
      doublePulse = False
    # get event as obligatory consumer (sees all events)
      e = self.BM.getEvent(self.cId, mode=0)
      if e == None:
        print('    PAnalysis: end event seen - closing down')
        break             # end if empty event or BM no longer active

      evNr, evTime, evData = e
      evcnt+=1
      if verbose > 1:
        self.prlog('*==* pulseFilter: event Nr %i, %i events seen'%(evNr,evcnt))

# find signal candidates by convoluting signal with reference pulse
#   data structure to collect properties of selected pulses:
      idSig = [ [0, 0] for i in range(NChan)] # time slice of valid pulse
      VSig = [ [0., 0.] for i in range(NChan)]  # signal height in Volts
      TSig = [ [0., 0.] for i in range(NChan)]  # time of valid pulse
      NSig = [0 for i in range(NChan)]

# 1. validate trigger pulse
      if iCtrg >= 0:  
        if(self.useTrgShape): # use trgger pulse shape if given ...
          idP = -1  
        else: # ... or Channel Pulse Shape otherwise
          idP = min(iCtrg, self.NShapes - 1 ) 

        offset = max(0, idT0 - int(taur[idP]/dT) - idTprec)
        cort = np.correlate(evData[iCtrg, offset:idT0+idTprec+lref[idP]], 
                            refP[idP], mode='valid')
        # set all values below threshold to threshold
        cort[cort<pthr[idP]] = pthr[idP] 
        idtr = np.argmax(cort) + offset # index of 1st maximum 
        if idtr > idT0 + (taur[idP] + tauon[idP])/dT + idTprec:
          if self.histQ: hnTrSigs.append(0.)
          continue #- while # no pulse near trigger, skip rest of event analysis
 
   # pulse candidate in right time window found ...
    # ... check pulse shape by requesting match with time-averaged pulse
        evdt = evData[iCtrg, idtr:idtr+lref[idP]]
        evdtm = evdt - evdt.mean()  # center signal candidate around zero
        cc = np.sum(evdtm * refPm[idP]) # convolute mean-corrected reference
        if cc > pthrm[idP]:
          validated = True # valid trigger pulse found, store
          Nval +=1
          V = max(abs(evdt)) # signal Voltage  
          VSig[iCtrg][0] = V 
          if self.histQ: hvTrSigs.append(V)
          T = idtr*dT*1E6      # signal time in musec
          TSig[iCtrg][0] = T 
          tevt = T  # time of event
        else:   # no valid trigger
          hnTrSigs.append( max(abs(evdt)) )
          continue #- while # skip rest of event analysis
      NSig[iCtrg] +=1

# 2. find coincidences
      Ncoinc = 1
      for iC in range(NChan):
        idP = min(iC, self.NShapes - 1) # Channel Pulse Shape 
        if iC != iCtrg:
          offset = max(0, idtr - idTprec)  # search around trigger pulse
    #  analyse channel to find pulse near trigger
          cor = np.correlate(evData[iC, offset:idT0+idTprec+lref[idP]], 
                 refP[idP], mode='valid')
          cor[cor<pthr[idP]] = pthr[idP] # set all values below threshold to threshold
          id = np.argmax(cor)+offset # find index of (1st) maximum 
          if id > idT0 + (taur[idP] + tauon[idP])/dT + idTprec:
            continue # no pulse near trigger, skip
          evd = evData[iC, id:id+lref[idP]]
          evdm = evd - evd.mean()   # center signal candidate around zero
          cc = np.sum(evdm * refPm[idP]) # convolute mean-corrected reference
          if cc > pthrm[idP]:
            NSig[iC] +=1
            Ncoinc += 1 # valid, coincident pulse
            V = max(abs(evd))
            VSig[iC][0] = V         # signal voltage  
            hVSigs.append(V)         
            T = id*dT*1E6 # signal time in musec
            TSig[iC][0] = T 
            tevt += T

# check wether event should be accepted 
      if (NChan == 1 and validated) or (NChan > 1 and Ncoinc >=2):
        accepted = True
        Nacc += 1
      else:
        continue #- while 

# fix event time:
      tevt /= Ncoinc
      if Ncoinc == 2:
        Nacc2 += 1
      elif Ncoinc == 3:
        Nacc3 += 1
      elif Ncoinc == 4:
        Nacc4 += 1

# search for double-pulses ?
      if self.DPanalysis:
#3. find subsequent pulses in accepted events
        offset = idtr + lref[idP] # search after trigger pulse
        for iC in range(NChan):
          cor = np.correlate(evData[iC, offset:], refP[idP], mode='valid')
          cor[cor<pthr[idP]] = pthr[idP] # set values below threshold to threshold
          idmx, = argrelmax(cor)+offset # find index of maxima in evData array
# clean-up pulse candidates by requesting match with time-averaged pulse
          iacc = 0
          for id in idmx:
            evd = evData[iC, id:id+lref[idP]]
            evdm = evd - evd.mean()  # center signal candidate around zero
            cc = np.sum(evdm * refPm[idP]) # convolute mean-corrected reference
            if cc > pthrm[idP]: # valid pulse 
              iacc+=1
              NSig[iC] += 1
              V = max(abs(evd)) # signal Voltage 
              if iacc == 1:
                VSig[iC][1] = V 
                TSig[iC][1] = id*dT*1E6   # signal time in musec
              else: 
                VSig[iC].append(V) # extend arrays if more than 1 extra pulse
                TSig[iC].append(id*dT*1E6)   
#     -- end loop over pulse candidates
#   -- end for loop over channels
     
#  statistics on double pulses on either channel
        delT2s=np.zeros(NChan)
        sig2s=np.zeros(NChan)
        sumdT2 = 0.
        N2nd = 0.
        for iC in range(NChan):
          if VSig[iC][1] > 0.:
            doublePulse = True
            N2nd += 1
            delT2s[iC] = TSig[iC][-1] - tevt  # take last pulse found 
            sig2s[iC] = VSig[iC][-1]
            sumdT2 += delT2s[iC]
        if doublePulse:
          Ndble += 1
          if self.histQ: hTaus.append( sumdT2 / N2nd )
    #   - end if self.DPanalysis
    
# eventually store results in file(s)
# 1. all accepted events
      if self.logf is not None and accepted:
        print('%i, %.2f'%(evNr, evTime), end='', file=self.logf)
        for ic in range(NChan):
          v = VSig[ic][0]
          t = TSig[ic][0]
          if v>0: t -=tevt
          print(', %.3f, %.3f'%(v,t), end='', file=self.logf)
        if doublePulse:
          for ic in range(NChan):
            v = VSig[ic][1]
            t = TSig[ic][1]
            if v>0: t -=tevt
            print(', %.3f, %.3f'%(v,t), end='', file=self.logf)
          for ic in range(NChan):
            if len(VSig[ic]) > 2:
              print(', %i, %.3f, %.3f'%(ic, VSig[ic][2], TSig[ic][2] ),
                  end='', file=self.logf)
        print('', file=self.logf)

# 2. double pulses
      if self.logfDP is not None and doublePulse:
        if NChan==1:
          print('%i, %i, %.4g,   %.4g, %.3g'\
              %(Nacc, Ndble, hTaus[-1], delT2s[0], sig2s[0]),
                file=self.logfDP)
        elif NChan==2:
          print('%i, %i, %.4g,   %.4g, %.4g,   %.3g, %.3g'\
                %(Nacc, Ndble, hTaus[-1], 
                  delT2s[0], delT2s[1], sig2s[0], sig2s[1]),
                  file=self.logfDP)
        elif NChan==3:
          print('%i, %i, %.4g,   %.4g, %.4g, %.4g,   %.3g, %.3g, %.3g'\
                %(Nacc, Ndble, hTaus[-1], 
                  delT2s[0], delT2s[1], delT2s[2], 
                  sig2s[0], sig2s[1], sig2s[2]),
                  file=self.logfDP)
        elif NChan==4:
          print('%i, %i, %.4g,   %.4g, %.4g, %.4g, %.4g,   %.3g, %.3g, %.3g, %.3g'\
                %(Nacc, Ndble, hTaus[-1], 
                  delT2s[0], delT2s[1], delT2s[2], delT2s[3], 
                  sig2s[0], sig2s[1], sig2s[2], sig2s[3]),
                  file=self.logfDP)

      if self.rawf is not None and doublePulse: # write raw waveforms
        print( ' - ' + yaml.dump(np.around(evData, 5).tolist(),  
                       default_flow_style=True ), 
             file=self.rawf) 

      if self.pDir is not None and doublePulse:
        evt = self.Osci( (3, Ndble, evTime, evData) ) # update figure ...
                #  use cnt=3 each time to avoid rate statistics 
        # ... and save to .png
        self.figOs.savefig(self.pDir+'/DPfig%03i'%(Ndble)+'.png') 

# print to log file 
      if accepted and verbose > 1:
        if NChan ==1:
          self.prlog ('*==* PF: %i, %i, %.2f, %.3g, %.3g'\
              %(evcnt, Nacc, tevt, VSig[0][0]) )
        elif NChan ==2:
          self.prlog ('*==* PF: %i, %i, i%, %.3g, %.3g, %.3g'\
               %(evcnt, Nval, Nacc, tevt, VSig[0][0], VSig[1][0]) )
        elif NChan ==3:
          self.prlog ('*==* PF: %i, %i, %i, %i, %i, %.3g'\
              %(evcnt, Nval, Nacc, Nacc2, Nacc3, tevt) )
        elif NChan ==4:
          self.prlog ('*==* PF: %i, %i, %i, %i, %i, %.3g'\
              %(evcnt, Nval, Nacc, Nacc2, Nacc3, Nacc4, tevt) )

      if(verbose == 1 and evcnt%1000==0):
        if NChan == 1:
          self.prlog("*==* PF: evt %i, Nval: %i"\
              %(evcnt, Nval))
        elif NChan == 2:
          self.prlog("*==* PF: evt %i, Nval, Nacc: %i, %i"\
                     %(evcnt, Nval, Nacc))
        elif NChan == 3:
          self.prlog("*==* PF: evt %i, Nval, Nacc, Nacc2, Nacc3: %i, %i, %i, %i"\
                     %(evcnt, Nval, Nacc, Nacc2, Nacc3))
        elif NChan == 4:
          self.prlog("*==* PF: evt %i, Nval, Nacc, Nacc2, Nacc3, Nacc4: %i, %i, %i, %i, %i"\
                     %(evcnt, Nval, Nacc, Nacc2, Nacc3, Nacc4))

      if verbose and doublePulse:
        s = '%i, %i, %.4g'\
                 %(Nacc, Ndble, hTaus[-1])
        self.prlog('*==* double pulse: Nacc, Ndble, dT ' + s)

# provide information for background display processes
# -- RateMeter
      if self.filtRateQ and self.filtRateQ.empty(): 
        self.filtRateQ.put( (Nacc, evTime) ) 

# -- histograms
      if len(hvTrSigs) and self.histQ and self.histQ.empty(): 
        self.histQ.put( [hnTrSigs, hvTrSigs, hTaus, hVSigs] )
        hnTrSigs = []
        hvTrSigs = []
        hVSigs = []
        hTaus = []

# -- Signal Display
      if self.VSigQ and self.VSigQ.empty(): 
        peaks = [VSig[iC][0] for iC in range(NChan) ]
        self.VSigQ.put( peaks ) 

# end BM.ACTIVE or break e == None  

# add summary information to log-files
    tag = "# pulseFilter Summary: " 
    if self.logf is not None:
      print(tag+"last evNR %i, Nval, Nacc: %i, %i "%(evcnt, Nval, Nacc), 
          end='', file=self.logf )
      nac = [Nacc2, Nacc3, Nacc4]
      for j in range(1, NChan):
        print("Nacc%i = %i "%(j+1, nac[j-2]),
          end='', file=self.logf )
      print('\n', file = self.logf)
      self.logf.close()

    if self.logfDP is not None: 
      print(tag+"last evNR %i, Nval, Nacc: %i, %i "%(evcnt, Nval, Nacc), 
          end='', file=self.logfDP )
      Nac = [Nacc2, Nacc3, Nacc4]
      for j in range(1, NChan):
        print("Nacc%i = %i "%(j+1, Nac[j-2]),
          end='', file=self.logfDP )
      print("\n#                       %i double pulses"%(Ndble), 
        file=self.logfDP )
      self.logfDP.close()

    if self.rawf is not None: 
      print("--- ", file=self.rawf )
      self.rawf.close()

    if self.pDir is not None:
      # put all figures in one zip-file 
      pass # not yet implemented

    return
#-end PulseFilter.PAnalysis()

  def end(self):
  # stop all sub-processes
    for p in self.subprocs:
      if p.is_alive():
        if self.verbose: print('    PulseFilter: terminating ' + p.name)
        p.terminate()
      else: 
       if self.verbose: print('    PulseFilter: ' + p.name + ' terminated')
