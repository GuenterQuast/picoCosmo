#!/usr/bin/env python3
"""PanelEfficiency.py
Analysis of CosMO-panel efficiencies from recorded data.

It is assumed that the CosMO panel to be measured is located between
two other panels of the same geometry, and these two panels should
have recorded a muon signal in coincidence. In this case, a myon is
also present in the panel in the middle. No requirements should be
put on the pulses in this panel.

These requirements can be achieved with the picoCosmo pulse filter with
the the configuration option:

```
logFile: pFilt
acceptPattern:
 - [1, 1, 1]  # valid pulse in channel A, B and C
 - [1, 0, 1]  # pulse in A and C but not in B
```
for the efficiency determination and

```
logFile: pFilt
acceptPattern:
 - [0, 1, 0]  # no pulses in A and C
```
for the determination of noise levls.

Alternatively, the tag panels can be used as veto-counters to
study signals not related to muons, i.e. noise and ambient radiation.


Running this script on the output file

  `python PanelEfficiency.py -f pFilt.dat`

produces the pulse-height spectrum of the panel in the middle
and calculates its efficiency and mean pulse height.

"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser(description="Efficiency determination of CosMO Panels")
parser.add_argument('filename', type=str, default='', help="input file name (CSV format)")
parser.add_argument('--tag', type=str, default=r'', help="info tag")
parser.add_argument('-b', '--bins', type=int, default=100, help="bins for Pulse Height Histogram")
parser.add_argument('-c', '--cut', type=float, default=0.050, help="cut on minimal pulse height")
parser.add_argument('-v', '--veto', action="store_true", help="tagging counters as veto")

args = parser.parse_args()
inFileName = args.filename  # input file
info_tag = args.tag
NHbins = args.bins  # number of bins for pulse-height histogram
ph_cut = args.cut  # pulse height for probe panel
veto = args.veto  # use tagging counters as veto

if inFileName == '':
    inFileName = "pFilt.csv"

print(f"*==* script {sys.argv[0]} executing, parameters: {sys.argv[1:]}\n")

# -*- Daten einlesen:
try:
    EvN, EvT, HTaga, TTaga, Hprobe, TProbe, HTagb, TTagb = np.loadtxt(
        inFileName, skiprows=1, delimiter=",", unpack=True
    )
except Exception as e:
    print(" Problem reading input - ", e)
    sys.exit(1)


# -*- selektiere Daten mit großer Pulshöhe
if veto:
    H = Hprobe[(HTaga < ph_cut) & (HTagb < ph_cut)]
else:
    H = Hprobe[(HTaga > ph_cut) & (HTagb > ph_cut)]
N_tot = len(H)
H_seen = H[H > ph_cut]
N_seen = len(H_seen)
T = EvT[-1] - EvT[0]
rate = N_seen / T

# calculate efficiency and uncertainty
eff = N_seen / N_tot
eeff = np.sqrt(eff * (1.0 - eff) / N_tot)

# print summary
print("reading ", inFileName)
print(f"records read {len(Hprobe)}, selected {N_tot},  duration {T:.1f} s, rate {rate:.1f} Hz")
print(f"  mean pulse height {H_seen.mean():.3g} V")
txt_eff = f"({eff*100.:.2f} +/- {eeff*100.:.2f})%"
print(" ==>   efficiency " + txt_eff)

# Grafik für Pulshöhen erzeugen
figH = plt.figure("PulseHeight", figsize=(8.0, 5.0))
ax_ph = figH.add_subplot(1, 1, 1)  # for pulse-height histogram
ax_ph.grid()
col = 'darkred' if veto else 'darkgreen'
bc, be, _p = ax_ph.hist(H, NHbins, rwidth=0.75, color=col)
bw = be[1] - be[0]
idx_cut = int((ph_cut - be[0]) / bw + 0.5)
ax_ph.set_ylabel("Anzahl Einträge")
ax_ph.set_xlabel("Pulshöhe (V)")
ax_ph.vlines(ph_cut, 0.9, max(bc), color="orangered", lw=2)
# set logarithmic scale
ax_ph.text(0.66, 0.96, info_tag, transform=ax_ph.transAxes)
ax_ph.text(0.66, 0.90, f" mean pluse height {H_seen.mean():.3g} V", transform=ax_ph.transAxes)
if not veto:
    ax_ph.text(0.70, 0.85, r"$\epsilon$ = " + txt_eff, transform=ax_ph.transAxes)
for i in range(idx_cut):
    _p[i].set_facecolor("darkred")
ax_ph.set_yscale("log")

# Grafiken anzeigen
plt.show()
