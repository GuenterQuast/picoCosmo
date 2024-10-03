#!/usr/bin/env python3
"""PanelSpectrum.py

Display of pulse height spectrum in a CosMO-panel from recorded data.

It is assumed that the CosMO panel to be analyzed (the "probe panel")
is located between two other panels of the same geometry. If both panels
of these "tag panels" show a signal, a muon track is also present in
the probe panel. If both show no signal, no muon track crossed the
probe panel and the signals are either noise or induced by background
ratiation.

For an unbiases pulse height spectrum in the probe panel (B),
these requirements can be achieved by triggering on B and
with the picoCosmo pulse filter configuration options:

```
logFile: pFilt
NminCoincidence: 1  # accept if valid signal in trigger Panel
```

Running this script on the output file

  `python PanelSignals.py pFilt.dat`

produces the pulse-height spectrum of the panel in the middle
for signals with and without a muon tag.

"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser(description="Efficiency determination of CosMO Panels")
parser.add_argument(
    "filename", type=str, default="", help="input file name (CSV format)"
)
parser.add_argument("--tag", type=str, default=r"", help="info tag")
parser.add_argument(
    "-b", "--bins", type=int, default=100, help="bins for Pulse Height Histogram"
)
parser.add_argument(
    "-c", "--cut", type=float, default=0.050, help="cut on minimal pulse height"
)

args = parser.parse_args()
inFileName = args.filename  # input file
info_tag = args.tag
NHbins = args.bins  # number of bins for pulse-height histogram
ph_cut = args.cut  # pulse height for probe panel

if inFileName == "":
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

# -*- selektiere Daten ohne oder mit muon tag
H_veto = Hprobe[(HTaga < ph_cut) & (HTagb < ph_cut)]
H_tag = Hprobe[(HTaga > ph_cut) & (HTagb > ph_cut)]

N_tot = len(Hprobe)
N_veto = len(H_veto)
N_tag = len(H_tag)
T = EvT[-1] - EvT[0]
rate = N_tot / T

# print summary
print("reading ", inFileName)
print(
    f"records read {N_tot}, with tag {N_tag},  duration {T:.1f} s, rate {rate:.1f} Hz"
)
print(f"  mean pulse height tag {H_tag.mean():.3g} V")


# Grafik für Pulshöhen erzeugen
fig = plt.figure("PulseHeight_Spectrum", figsize=(8.0, 5.0))
fig.suptitle("Pulse-height spectrum")
ax = fig.add_subplot(1, 1, 1)  # for pulse-height histogram
ax.set_ylabel("Anzahl Einträge")
ax.set_xlabel("Pulshöhe (V)")
ax.grid()
# plot all pulses
bc, be, _p = ax.hist(
    Hprobe, NHbins, rwidth=0.75, color="darkgreen", alpha=0.5, label="muon tag"
)
# plot pulses with muon tag
_h = ax.hist(H_veto, NHbins, rwidth=0.75, color="darkred", alpha=0.5, label="muon veto")
# set logarithmic scale
ax.set_yscale("log")
ax.legend(loc="best")
plt.show()
