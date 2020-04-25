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

import subprocess 
import sys
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from time import sleep
from optparse import OptionParser
import matplotlib.pyplot as plt

fuseDir = "/mnt/diskpack/temp"
rootDir = "/home/oper/GMVA"

m6ccCommand = "/usr/local/bin/M6_CC"

version = "1.1"


def usage():
	usage = "USAGE: "
	usage += "%prog [OPTIONS] xml-schedule \n\n"
	usage += "This script launches the GMVA observation schedule given by the xml-schedule argument.\n"
	usage += "In the scan gaps the following additional tasks are being performed:\n"
	usage += "1) 2-bit sampling statistics are obtained from the previous recording.\n"
	usage += "2) m5spec is called to obtain bandpasses for all 16 pfb channels\n"
	usage += "3) The bit statistics and bandpasses from the last scan are displayed graphically\n\n"
	usage += "The results are stored in text form under %s\n\n" % (rootDir)
	

	return(usage)

def validate():
	# check that schedule file exists
	if not os.path.isfile(schedule):
		sys.exit ("schedule file does not exist: %s" % schedule)

	# check that scripts exist:
	for script in [m6ccCommand]:
		if not os.path.isfile(script.strip()):
			sys.exit ("Required file does not exist: %s" % script)

def mountFuse():
	os.system("fuseMk6 -r '/mnt/disks/%d/*/data' %s" % (options.slot,fuseDir))

def umountFuse():
	os.system("fusermount -u %s" % fuseDir)



# MAIN
parser = OptionParser(usage=usage(),version=version)

parser.add_option("--postScanMargin", type="int", default=20, dest="postScanMargin", help="number of seconds after the end of the next scan in which no further commands will be executed (default=20)")
parser.add_option("-s", "--slot", type="int", default=1, help="The recorder slot used for recording (default: 1)")
parser.add_option("-m", "--monitor-only", action="store_true", dest="monitor", help="Do not start the schedule. Only monitor between the recordings")
parser.add_option("-3", "--dbbc3", action="store_true", dest="dbbc3", help="use a DBBC3 backend")


(options, args) = parser.parse_args()

if len(args) != 1:
	parser.print_help()
	sys.exit(1)

schedule = args[0]


postScanMargin = options.postScanMargin

validate()

# create dummy mount point for fuseMk6
if not os.path.exists(fuseDir):
	os.mkdir(fuseDir)

# make sure that there are no remaining fuse mounts
umountFuse()

# create output root directory
if not os.path.exists(rootDir):
        os.mkdir(rootDir)

# launch the mark6 schedule
if not options.monitor:
	schedArgs = "%s -f %s" % (m6ccCommand, schedule)
	m6cc = subprocess.Popen(["xterm", "-e", schedArgs], stderr=subprocess.STDOUT)

tree = ET.parse(schedule)
root = tree.getroot()

pM5spec = None
pM5bstate = None

for scan in root.findall("scan"):

	duration = int(scan.get('duration'))
	station = scan.get('station_code')
	scanName = scan.get('scan_name')
	exp = scan.get('experiment')

	# create output directory if it doesn't exist
	expDir = rootDir + "/" + exp
	if not os.path.exists(expDir):
        	os.mkdir(expDir)


	recFilename = "%s_%s_%s" %(exp,station,scanName)
	print recFilename

	dtStart = datetime.strptime(scan.get('start_time'), '%Y%j%H%M%S')
	dtStop = dtStart + timedelta(seconds=duration)
	dtNow = datetime.utcnow()

	print station, scanName, exp

	# running m5spec on the last
	
	if dtStop < dtNow:
		print "Scan %s lies in the past. Skipping" % scan.get('scan_name')
		continue

	# sleep until scan has finished
	deltaStop = dtStop  + timedelta(seconds=postScanMargin) - datetime.utcnow()
	print "sleeping until: ", datetime.utcnow() + deltaStop
	sleep(float(deltaStop.seconds))

	# if there are any plots from the previous scan close them now
	if pM5spec:
		pM5spec.terminate()
	if pM5bstate:
		pM5bstate.terminate()

	# fuse mount the module
	mountFuse()
	
	vdifFile = "%s/%s.vdif" % (fuseDir,recFilename)

	# run m5spec on the previous scan
	m5specFile = "%s/%s.m5spec" % (expDir, recFilename)

	os.system("m5spec %s VDIF_5000-2048-16-2 512 1024 %s" %(vdifFile,m5specFile))

	# read m5spec output and plot
	pM5spec = subprocess.Popen(["plot_pfb_m5spec.py", m5specFile], stdout=subprocess.PIPE)	

	# run m5bstate on the previous scan
	m5bstateFile = "%s/%s.m5bstate" % (expDir, recFilename)
	os.system("m5bstate %s VDIF_5000-2048-16-2 100 >  %s" %(vdifFile,m5bstateFile))

	# read m5bstate output and plot
	pM5bstate = subprocess.Popen(["plot_m5bstate.py", m5bstateFile], stdout=subprocess.PIPE)	

	umountFuse()
