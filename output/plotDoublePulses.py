#!/usr/bin/python3
"""visual display of raw wave forms saved by picoCosmo.py"""

import sys
import time
import yaml
import numpy as np
import zipfile
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('TkAgg')

# animated displays running as background processes/threads
from picodaqa.Oscilloscope import *


def readblock():
    # read data sequentially from input file (utf-8 or unpacked zip)
    #   end of block marked by ']]\n'
    global f
    txt = ''
    while True:
        if zipmode:
            _l = f.readline().decode('utf-8')
        else:
            _l = f.readline()
        if not _l:  # end of file
            # print('   end of file')
            return ''
        txt += _l
        if _l[-3:-1] == ']]':
            # print('   end of block')
            return txt


if __name__ == "__main__":  # -----------------------------
    print('\n*==* script ' + sys.argv[0] + ' running \n')
    if len(sys.argv) == 2:
        fname = sys.argv[1]
    else:
        fname = 'rawDPtest.dat'
    print('    input from file ' + fname)

    try:
        # read from zip file
        if fname.split('.')[-1] == 'zip':
            zipmode = True
            zf = zipfile.ZipFile(fname, 'r')
            fnam = zf.namelist()[0]  # first file
            f = zf.open(fnam)
            print('    reading from packed file ' + fnam)
        else:
            # read from unpacked file
            zipmode = False
            f = open(fname, 'r')
    except Ecxeption as e:
        print(' !!! failed to open input file ' + fname + " : " + str(e))
        exit(1)

    # read first block from file
    try:
        txt = readblock()
        obj = yaml.load(txt, Loader=yaml.Loader)
        conf = obj['OscConf']
    except Exception as e:
        print('     failed read oscillocope configuration : ' + str(e))
        exit(1)

    print(" ** start animation")
    plt.ion()
    # initialize oscilloscope display
    Osci = Oscilloscope(conf, 'DoublePulse')
    figOs = Osci.fig
    Osci.init()
    twait = 0.3  # time between figure updates in s
    cnt = 0

    while True:
        data = obj['data']
        for d in data:
            cnt += 1
            evt = (3, cnt, time.time(), np.array(d))
            print(" displaying event %i" % (cnt))
            Osci(evt)
            figOs.canvas.draw()
            time.sleep(twait)

        # read next block
        txt = readblock()
        if txt == '':
            break  # end of file
        obj = yaml.load('data: \n' + txt, Loader=yaml.Loader)
        data = obj['data']

    f.close()
    print(sys.argv[0] + " end *==*")
