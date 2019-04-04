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
import socket
from optparse import OptionParser
import matplotlib.pyplot as plt

version = "1.0"


def usage():
	usage = "USAGE: "
	usage += "%prog m5spec-file  \n\n"
	usage += "This script plots 16 PFB channels from a given m5spec dataset.\n"
	

	return(usage)


def plotM5spec(infile):
	
	file = open(infile, "r")
	xData = []
	bandData = {}
	for i in range(16):
		bandData[str(i+1)] = []
	
	for line in file:
		cols = line.split(" ")
		xData.append(cols[0])
		for i in range(16):
			bandData[str(i+1)].append(cols[i+2])
			
	file.close()

	
	hostname = socket.gethostname()
	fig = plt.figure()
	plt.rc("font", size=8)
	fig.suptitle("%s: %s" % (hostname, infile), fontsize=16)
	for i in range(16):
		plt.subplot(4,4,i+1)
		plt.plot(xData,bandData[str(i+1)])
		plt.title ("band " + str(i+1))
		plt.subplots_adjust(hspace=0.6,wspace=0.4)
	plt.show()


# MAIN
parser = OptionParser(usage=usage(),version=version)


(options, args) = parser.parse_args()

if len(args) != 1:
	parser.print_help()
	sys.exit(1)

infile = args[0]

# check that input m5spec file exists
if not os.path.exists(infile):
	sys.exit("input file (%s) does not exist" % (infile))

# read m5spec output and plot
plotM5spec(infile)




