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
import os
import re
import socket
from optparse import OptionParser
import matplotlib.pyplot as plt

version = "1.0"


def usage():
	usage = "USAGE: "
	usage += "%prog m5bstate-Output  \n\n"
	usage += "This script plots the results of m5bstate.\n"
	
	return(usage)


def plotM5bstate(infile):
	
	file = open(infile, "r")
	bandData = {}
	for i in range(16):
		bandData[str(i+1)] = []
	
#Ch    --      -     +     ++        --      -      +     ++     gfact
# 0   17621   29602   29995   17782      18.5   31.2   31.6   18.7   0.98

	hostname = socket.gethostname()
	fig = plt.figure()
	fig.suptitle("%s: %s" % (hostname, infile), fontsize=16)

	plt.rc('font', size=8)

	xLabels = ["- -", "-", "+", "++"]
	xData = [0,1,2,3]

	reM5bstate = re.compile("\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)")
	for line in file:
		match = reM5bstate.match(line)
		if match:
			ydata = [float(match.group(6)),float(match.group(7)),float(match.group(8)),float(match.group(9))] 
			# check quality of bit statistics
			if abs(ydata[0]-19) > 6 or abs(ydata[3]-19) > 6 or abs(ydata[1]-31) > 6 or abs(ydata[2]-31) > 6:
				color = "red"
			elif abs(ydata[0]-19) > 3 or abs(ydata[3]-19) > 3 or abs(ydata[1]-31) > 3 or abs(ydata[2]-31) > 3:
                                color = "orange"
			else:
				color = "green"
	 		plt.subplot(4,4,int(match.group(1))+1)
	 		rects = plt.bar(xData,ydata, align='center', color=color)
	 		plt.title ("band %d" % (int(match.group(1))+1))
			plt.xticks(xData, xLabels)
			plt.ylabel("%")
	 		plt.subplots_adjust(hspace=0.6,wspace=0.4)
			count = 0
			for rect in rects:
        			width = int(rect.get_width())
				xloc = rect.get_x() + rect.get_width()/2.0
				yloc = rect.get_y() + rect.get_height()/2.0
				perc = ydata[count]
				label = plt.text(xloc, yloc, perc, horizontalalignment='center', verticalalignment='center', clip_on=True, color="white")
				count +=1
				
			
	plt.show()
			
	file.close() 


# MAIN
parser = OptionParser(usage=usage(),version=version)


(options, args) = parser.parse_args()

if len(args) != 1:
	parser.print_help()
	sys.exit(1)

infile = args[0]

# check that input  file exists
if not os.path.exists(infile):
	sys.exit("input file (%s) does not exist" % (infile))

# read m5spec output and plot
plotM5bstate(infile)




