#!/usr/bin/env python
###########################################################################
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################
# Original author: Helge Rottmann (MPIfR) rottmann(AT)mpifr.de
###########################################################################

import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import argparse
import json


def processSingleBand():

    tones = []
    y = data[:,1]

    peaks =  findPeaks(y)
    for peak in peaks:
        peakFreq = x[peak]
        #peakY.append(y[peak])
        #peakIdx.append(peakFreq)

        verbose("Found peak at Freq=%f Amplitude=%f (Idx=%d)" % (peakFreq, y[peak], peak))
        tones.append({'freq': peakFreq, 'amp': y[peak]})

    return (y, tones)
    
def processDDC():

    tones = []
    y = np.empty([0])
    for band in range(0,numBands,2):

        # for DDC modes the vdif channel order is BBC1-USB,BBC1-LSB,BBC2-USB,BBC2-LSB,...
        peaks = []
        lsb = np.flipud(data[:, band+2])
        usb = data[:, band+1]

        peaks =  findPeaks(lsb)
        for peak in peaks:
            peakFreq = x[band*pointsPerBand+peak+1]
            tones.append({'freq': peakFreq, 'amp': lsb[peak]})
            verbose("Found tone (LSB) at Freq=%f Amplitude=%f (Idx=%d)" % (peakFreq, lsb[peak], peak))
        

        peaks =  findPeaks(usb)
        for peak in peaks:
            peakFreq = x[(band+1)*pointsPerBand+peak]
            tones.append({'freq': peakFreq, 'amp': usb[peak]})
            verbose("Found tone (USB) at Freq=%f Amplitude=%f (Idx=%d)" % (peakFreq, lsb[peak], peak))

        # how to properly deal with the LSB / USB inversion ?
        # does the DC frequency  correspond to channel 0 in USB or the last channel of LSB?
        # for now go with USB(0).
        # This means that the frequency in LSB must be shifted by one channel
        temp = np.empty([1])
        temp = np.append(temp, lsb)
        temp = np.delete(temp,len(temp)-1)
        # concenate the columns data
        # lower sideband first flipped 
        y = np.append(y, temp)
        # then upper sideband
        y = np.append(y, usb)

    if len(tones) == 0:
        verbose("No tones found")

    return (y, tones)

def plotSpectrum(x,y,tones, xticks):

    data = []

    columns = ('Frequency [MHz]', 'Amplitude')
    
    # table rows
    rows = []
    peakX = []
    peakY = []
    for i in range(len(tones)):
        rows.append("tone %d" % (i+1))
        #row = [peakX[i], peakY[i]]
        row = [tones[i]['freq'], tones[i]['amp']]
        data.append(row)
        peakX.append(tones[i]['freq'])
        peakY.append(tones[i]['amp'])


    plt.figure(figsize=(10, 6))
    plt.plot(x, y)

    if len(tones) > 0:
            plt.plot(peakX, peakY, "o", color='r', label="Peaks")

    plt.xlabel("baseband frequency [MHz]")
    plt.ylabel("amplitude")
    #plt.legend()
    plt.xticks(xticks)
    plt.grid(True)
    plt.title(args.title)

    if len(data) > 0:
        table = plt.table(cellText=data,
                          rowLabels=tuple(rows),
                          colLabels=columns,
                  loc = "best")
        table.auto_set_column_width(0)
        table.auto_set_column_width(1)
        table.auto_set_font_size(True)

    if args.showPlot:
        plt.show()
    if args.pngPath:
        try:
            plt.savefig(args.pngPath)
        except Exception as e:
            print("Error saving figure to: %s (%s)" % (args.pngPath, e))

def findPeaks(y):

    z_threshold = 4.5         # Threshold for Z-Score
    minDist= 1            # Mindestabstand zwischen Peaks in Punkten
    peaks = []

    # calculate the z-scores
    mean_y = np.mean(y)
    std_y = np.std(y)
    z_scores = (y - mean_y) / std_y

    lastPeakPos = -minDist - 1
    
    for i in range(1, len(y)-1):
        if z_scores[i] >= z_threshold:                  # Z-score above threshold?
            if y[i] > y[i-1] and y[i] > y[i+1]:          # local minimum
                if i - lastPeakPos > minDist:
                    peaks.append(i)
                    lastPeakPos = i

    return(peaks)

def verbose(message):
    if not args.json:
        print (message)
        


parser = argparse.ArgumentParser( description='Program to plot the results from m5spec')

parser.add_argument("-t", "--title", default="spectrum", help="The title to use for the plot. Only relevant together with the -X or --png options.")
parser.add_argument("-l", "--low-freq", type=int, dest="lowChan", default=0, help="The frequency of the lowest baseband channel [MHz]")
group = parser.add_mutually_exclusive_group()
group.add_argument("-X", dest='showPlot', action='store_true', help="Show a graphical display of the spectrum and the detected peaks.")
group.add_argument("-j","--json",  action='store_true', help="Print the tone information in serialized json format")
parser.add_argument("--png", type=str, dest="pngPath", help="The filename of the png file to be saved to hard disk.")
parser.add_argument("m5spec", type=str, help="The filename of the .m5spec file")

args = parser.parse_args()

# load the m5spec file
data = np.loadtxt(args.m5spec, delimiter=None)
verbose("Loaded m5spec file: %s" % args.m5spec)

if data.shape[1] == 2:
    # in case of a single subband the m5spec file will not contain any additional cross-spectrum columns
    numBands = 1
else:
    numBands = int((data.shape[1]-1) / 2)

freqRes = data[1][0] - data[0][0]
bandwidth = data.shape[0] * freqRes

pointsPerBand = len (data[:,0])
verbose("Found %s bands with a band width of %d [MHz]"% (numBands, bandwidth))
verbose("The frequency resolution is %f [MHz]" % freqRes);

xticks = range(int(args.lowChan), int(args.lowChan) + numBands*int(bandwidth)+1, int(bandwidth))

x = np.linspace(args.lowChan, args.lowChan + numBands*bandwidth, num=numBands*pointsPerBand, endpoint=False)

if numBands == 1:
    y, tones = processSingleBand()
else:
    # if more than one subband we assume the data has been observed in the DBBC3 DDC mode
    # with alternating USB and LSB subbands
    y, tones = processDDC()

if (args.showPlot or args.pngPath):
    plotSpectrum(x,y, tones, xticks)

if (args.json):
    print(json.dumps(tones))
