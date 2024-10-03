#!/usr/bin/env python3
'''RateAnalysis.py

statistical analysis of arrival times of random events

uses output provided by picocosmo.PulseFilter (option "logFile: <file name>")

- number of events per time interval (rate)
- distribution of rates (Poisson)
- distribution of time between events (exponential)

Parameters:
  - file name
  - time interval

'''

import sys
import numpy as np
import matplotlib.pyplot as plt
import scipy.special as sp


# -*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - --*-
#
# -*- relevante Verteilungen
#
def fUniform(x, const=None):
    '''Gleichvderteilung'''
    if hasattr(x, "__iter__"):
        return const * np.ones(len(x))
    else:
        return const


def fExponential(x, tau=None, N=1.0):
    '''Exponenitalverteilung'''
    return N / tau * np.exp(-x / tau)


def fPoisson(x, mu=None, N=1.0):
    '''Poissonverteilung'''
    k = np.around(x)
    return N * (mu**k) / np.exp(mu) / sp.gamma(k + 1.0)


def getHistDistribution(bc, bw, f, **kwargs):
    return bw * f(bc, **kwargs)


# -*- Eingabe-Parameter
if len(sys.argv) > 1:
    fname = sys.argv[1]
else:
    fname = "pFilt.dat"  #  input file

if len(sys.argv) > 2:
    Tinterval = float(sys.argv[2])
else:
    Tinterval = 10  #  time interval for rate

fig = plt.figure(1, figsize=(6.0, 9.0))
fig.subplots_adjust(left=0.1, bottom=0.1, right=0.98, top=0.98, wspace=0.3, hspace=0.5)
ax_rate = fig.add_subplot(3, 1, 1)  # for rate vs. time
ax_rdist = fig.add_subplot(3, 1, 2)  # for distribution of rates
ax_tw = fig.add_subplot(3, 1, 3)  # for wait-time
mn = 0.0
mx = 75.0
nb = 75  # minimum, maximum and number of bins

# -*- Daten einlesen:
try:
    T = np.loadtxt(fname, usecols=(1), delimiter=',', unpack=True)
except Exception:
    print(' no input file given - abort')
    sys.exit(1)

N = len(T)
Ttot = T[-1] - T[0]  # total time
Nbins = int(Ttot / Tinterval)  # number of time intervals
meanRate = N / Ttot  # mean rate
meanN = meanRate * Tinterval  # number of events per time interval
dT = T[1:] - T[:-1]  # Zeiten zwischen zwei Ereignissen
meanTw = dT.mean()

# -*-  Ausgabe der statistischen Daten
print('\n*==* script ' + sys.argv[0] + '\n', '     Zeiten aus Datei ' + fname)
print(' Intervall: %.3gs' % (Tinterval))
print('   mittlere Rate: %.3g Hz' % (meanRate))
print('   mittlere Zeit zwischen zwei Ereignissen: %.3g s' % (meanTw))
print('\n')

# -*- Erzeugen der Grafiken (als Häufigkeitsverteilungen)

# 1. Ereignisse über der Zeit (= Häufigkeit / Zeitinterval)
tmn = 0.0
tmx = Nbins * Tinterval
bcR, beR, _ = ax_rate.hist(T, bins=np.linspace(tmn, tmx, Nbins))
ax_rate.set_ylabel('Anzahl Einträge', size='x-large')
ax_rate.set_xlabel('$t$ [s]', size='x-large')
# Mittelpunkt und Breite der Bins
bc = (beR[:-1] + beR[1:]) / 2.0
bw = beR[1] - beR[0]
# zeichne Gleichverteilung ein
hDist = getHistDistribution(bc, bw, fUniform, const=meanRate)
ax_rate.plot(bc, hDist, 'g--')

# 2. Verteilung der Anzahlen n beobachteter Ereignisse pro Zeitintervall
#      Bereich festlegen
meanEntries = int(meanRate * Tinterval)
nBins = int(5 * np.sqrt(meanEntries))
mn = max(meanEntries - nBins, 0)
mx = meanEntries + nBins
bins = np.arange(mn, mx, 1)
#      Verteilung als schmale Balken
bcP, beP, _ = ax_rdist.hist(bcR, bins, align='left', rwidth=0.3)
ax_rdist.set_ylabel('Anzahl Einträge', size='x-large')
ax_rdist.set_xlabel('$n$', size='x-large')
# Mittelpunkt und Breite der Bins
bc = (bins[:-1] + bins[1:]) / 2.0
bw = bins[1] - bins[0]
# zeichne Gleichverteilung ein
hDist = getHistDistribution(bins[:-1], bw, fPoisson, mu=meanN, N=len(beR) - 1)
ax_rdist.plot(bins[:-1], hDist, 'g--')

# 3. Wartezeiten
mn = 0.0
mx = 5 * meanTw
nb = 75  # minimum, maximum and number of bins
bcW, beW, _ = ax_tw.hist(dT, bins=np.linspace(mn, mx, nb), log=True, rwidth=0.8)  # log. Darstellung
ax_tw.set_ylabel('Anzahl Einträge', size='x-large')
ax_tw.set_xlabel('$\Delta$t [s]', size='x-large')
# Mittelpunkt und Breite der Bins
bc = (beW[:-1] + beW[1:]) / 2.0
bw = beW[1] - beW[0]
# zeichne Gleichverteilung ein
hDist = getHistDistribution(bc, bw, fExponential, tau=1.0 / meanRate, N=N)
ax_tw.plot(bc, hDist, 'g--')

# Grafiken anzeigen
plt.show()
