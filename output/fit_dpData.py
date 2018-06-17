#!/usr/bin/env python
#coding=utf-8
from __future__ import print_function, unicode_literals, division, absolute_import

# script read_array.py
''' read data from file into 1d-array and plot
    - data vs. ordinal number 
    - frequency distribution

This example also illustrates how to read an argument
from the command line

.. author:: Guenter Quast <g.quast@kit.edu>
'''

import sys
import numpy as np
import matplotlib.pyplot as plt

def pdf(t, fbg=0.1, tau=2.2, a=1., b=9.75):
  pdf1 = np.exp(-t/tau) / tau /(np.exp(-a/tau) - np.exp(-b/tau) )
  pdf2 = 1./(b-a)
  return (1-fbg)*pdf1 + fbg*pdf2

# general negLogL Function 
def negLogL(p, f, x, *args, **kwargs):
# calulate neg logl L for lists of 
#   - parameters p_i and 
#   - observations x_i
#  for a pdf f(x, p, <other parameters>)
#  
  nlL=np.zeros(len(p))
  for i, p_i in enumerate(p):
    nlL[i]=np.sum(-np.log(f(x, p_i, *args, **kwargs) ) )
  return nlL

# ---------------------------------------------------------------

#read columns from file:
largv = len(sys.argv)
if largv>=2:
  infile=sys.argv[1]
  dtmin=1.5  # range of useful pulses distances
  dtmax=15.0 # 
  if largv>=3: dtmin= float(sys.argv[2])
  if largv>=4: dtmax= float(sys.argv[3])
else:
  infile='dpKanne.dat'
print('*==* script ' + sys.argv[0] +  ' reading from file ' + infile)

#read columns from file:
A = np.loadtxt(infile, dtype=np.float32, delimiter=',', unpack=True)
#print(A)
# clean data
dT=np.array([dt for dt in A[2] if dt>dtmin and dt<dtmax])

# unbinned logL analysis
bgVals = np.linspace(0.1, 0.9, 240)
#bgVals = np.linspace(0.084, 0.084, 1) 2l-Kanne, 13 musec
#bgVals = np.linspace(0.03, 0.03, 1) # 1l-Kanne, 8 musec

#tauVals = np.linspace(1.9, 2.3, 200)
tauVals = np.linspace(1.0, 4., 300)
#tauVals = np.linspace(2.2, 2.2, 1)

profL=np.empty(len(tauVals))
for i, tau in enumerate(tauVals):
  plL = negLogL(bgVals, pdf, dT, tau, dtmin, dtmax)
  profL[i] = min(plL)

idmin = np.argmin(profL) # index of minimum
tau = tauVals[idmin] # best-fit value for tau
DprofL=profL-min(profL)
bg= bgVals[ np.argmin(negLogL(bgVals, pdf, dT, tau, dtmin, dtmax) ) ]
print('%i measurements in interval %.1fµs - %.1fµs'%(len(dT), dtmin, dtmax))
print('result of unbinned negLogL fit:')
print('   tau=%.4gµs  UG-Anteil = %.2g'%(tau, bg) )

# histogram data 
bins=np.linspace(dtmin, dtmax, 2*(dtmax-dtmin)+1)
bw = bins[1]-bins[0]
bc, be =np.histogram(dT, bins, normed=0) 
bcent=(be[:-1]+be[1:])/2
norm=np.sum(bc)

# plot as histogram
fig=plt.figure(figsize=(10., 5.))
axh=fig.add_subplot(1,2,1)
tt = np.linspace(dtmin, dtmax, 101)
axh.plot(tt, norm*bw * pdf(tt, bg, tau, dtmin, dtmax), color='darkgreen', lw=2 )
axh.errorbar(bcent, bc, yerr=np.sqrt(bc), fmt='.', color='chocolate')
axh.grid(True)
# set log-scale, comment out to see linear scale
#  axh.set_yscale('log')

# axh.set_title("Myon-Lebensdauer mit Cosmo-Panels")
axh.set_title("Myon-Lebensdauer mit Kamiokanne")

axh.set_xlabel(r'$\tau (\mu s)$',size='x-large')
axh.set_ylabel('Häufigkeit',size='x-large')
axh.text(0.6, 0.93, r'$\tau=$' + '%.2f'%(tau)+r'$\mu$s',
         transform=axh.transAxes ) 
axh.text(0.6, 0.85, 'UG-Anteil= %.2f'%(bg),
         transform=axh.transAxes ) 

axpL=fig.add_subplot(1,2,2)
axpL.plot(tauVals, DprofL, '.-')
axpL.axhline(0.5, color='r')
axpL.set_xlabel(r'$\tau (\mu s)$', size='x-large')
axpL.set_ylabel(r'$\Delta\, -{\rm ln}{\cal{L}}_p(\tau)$', size='large')

plt.show()
