#!/usr/bin/env python3
'''RateAnalysis.py

   statistical analysis of arrival times of random events

   uses output provided by picocosmo.PulseFilter (option "logFile: <file name>")

   - number of events per time interval (rate)
   - distribution of rates (Poisson)
   - distribution of time between events (exponential)

'''

# -*- coding=utf-8 -*-
#python 2/3 compatibility
from __future__ import print_function, unicode_literals, division, absolute_import

import sys, numpy as np, matplotlib.pyplot as plt

# -*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - --*-

# -*- Eingabe-Parameter
if len(sys.argv)>1:
  fname = sys.argv[1]
else:
  fname = "pFilt_gamma_Uranglas.dat"   #  input file

Tinterval = 60                        #  time interval for rate

fig = plt.figure(1, figsize=(6., 9.))
fig.subplots_adjust(left=0.1, bottom=0.1, right=0.98, top=0.98,
                      wspace=0.3, hspace=0.5) 
ax_rate = fig.add_subplot(3, 1, 1)  # for rate vs. time
ax_rdist = fig.add_subplot(3, 1, 2) # for distribution of rates
ax_tw = fig.add_subplot(3, 1, 3)    # for wait-time
mn=0. ; mx=75. ; nb=75 # minimum, maximum and number of bins

# -*- Daten einlesen:
data = np.loadtxt(fname, delimiter=',', unpack=True)              
T = data[1] # 2nd column

Ttot = T[-1] - T[0]                # total time
Nbins = int(Ttot/Tinterval)    # number of time intervals
meanRate = len(T) / Ttot           # mean rate
meanN = meanRate * Tinterval       # number of events per time interval
dT = T[1:] - T[:-1]                # Zeiten zwischen zwei Ereignissen
meanTw=dT.mean()

# -*-  Ausgabe der statistischen Daten
print('\n*==* script ' + sys.argv[0]+ '\n',\
      '     Zeiten aus Datei ' + fname) 
print('   mittlere Rate: %.3g Hz'%(meanRate))
print('   mittlere Zeit zwischen zwei Ereignissen: %.3g s'%(meanTw) ) 
print('\n')

# -*- Erzeugen der Grafiken (als Häufigkeitsverteilungen)

# 1. Ereignisse über der Zeit (= Häufigkeit / Zeitinterval) 
tmn=0.; tmx= Nbins*Tinterval
bcR, beR, _ = ax_rate.hist(T, bins=np.linspace(tmn, tmx, Nbins)) 
ax_rate.set_ylabel('Anzahl Einträge', size='x-large')
ax_rate.set_xlabel('$t$ [s]', size='x-large')

# 2. Verteilung der Anzahlen n beobachteter Ereignisse pro Zeitintervall
nRbins = 30
bcP, beP, _ = ax_rdist.hist(bcR, nRbins) 
ax_rdist.set_ylabel('Anzahl Einträge', size='x-large')
ax_rdist.set_xlabel('$n$', size='x-large')

# 3. Wartezeiten
mn=0. ; mx=5*meanTw; nb=75 # minimum, maximum and number of bins
ax_tw.hist(dT, bins=np.linspace(mn, mx, nb), log=True) # log. Darstellung
ax_tw.set_ylabel('Anzahl Einträge', size='x-large')
ax_tw.set_xlabel('$\Delta$t [s]', size='x-large')

# Grafik anzeigen
plt.show()
