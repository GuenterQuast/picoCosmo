# Verteilung der Wartezeiten
import numpy as np, matplotlib.pyplot as plt

file = "pFilt_gamma_Uranglas.dat"

# Daten einlesen:
data = np.loadtxt(file, delimiter=',', unpack=True)              
T = data[1] # 2nd column

# Wartezeiten berechnen
dT = T[1:] - T[:-1]
print('Wartezeiten.py: Mittlere Zeit zwischen zwei Ereignissen:', dT.mean()) 

# grafische Darstellung:
mn=0. ; mx=75. ; nb=75 # minimum, maximum and number of bins
plt.hist(dT, bins=np.linspace(mn, mx, nb), log=True) # log. Darstellung
plt.ylabel('Anzahl Einträge pro Intervall', size='x-large')
plt.xlabel('$\Delta$t [s]', size='x-large')
plt.show()
