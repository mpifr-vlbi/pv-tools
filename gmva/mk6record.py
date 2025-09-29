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
import argparse
from mark6control import Mark6, Mark6Exception
from datetime import datetime
import time

# parse the command line options
parser = argparse.ArgumentParser( description='Program to do a test recording on a Mark6 VLBI recorder.')
parser.add_argument("-d", "--duration", type=int, default=5, help="the duration of the recording in seconds (default: %(default)s)")
parser.add_argument("-c", "--station-code", default="Zz", dest="code", help="The 2-letter station code used for the metadata of the recording (default: %(default)s)")
parser.add_argument("-e", "--experiment", default="test", dest="experiment", help="The experiment name used for the metadata of the recording (default: %(default)s)")
parser.add_argument("-s", "--scanname", type=str, default="test", dest="scanname", help="The scan name to be used for the recording (default: %(default)s)")
parser.add_argument("recorder", type=str, help="The hostname or IP of the mark6 recorder.")
args = parser.parse_args()

scanname = args.scanname.strip()

# make a connection to the recorder
mark6 = Mark6(args.recorder, 14242, commMethod="cplane")

try:
    mark6.connect()
except Exception as e:
    print ("Error: ", e)
    print ("Check that the recorder is reachable and the cplane/dplane daemons are running")
    sys.exit(1)

# check for loaded modules    
mark6.readSlotInfo()
#{'group': '1234', 'slot': 1, 'eMSN': 'BHC%0076/64008/4/8', 'vsn': 'BHC%0076', 'capacity': '64008', 'datarate': '4', 'numDisksDiscovered': 8, 'numDisksRegistered': 8, 'capacityRemainingGB': 0, 'freePercentage': 0.0, 'groupCapacityGB': 64008, 'status1': 'unmounted', 'status2': 'unprotected', 'type': 'sg'}

slots = mark6.slots
ready = False

# check if there are any modules in a recordable state
for i in range(len(slots)):
    print ("Slot %d:" % (i+1) , "VSN=", slots[i].vsn, "State: %s/%s" % (slots[i].status1,slots[i].status2))

    if slots[i].status1 == 'open':
        ready = True
if not ready:
    print ("None of the modules are in an open/ready state, Exiting.")
    sys.exit(1)

# check if there are defined input_streams
streams = mark6.getInputStreams()
if (len(streams) == 0):
    print ("There are no input_streams defined. Exiting.")
    sys.exit(1)

# check if we are currently recording 
ret = mark6.sendCommand("record?")
if ret.fields[0] != "off":
    print ("There is a running recording. Exiting.")
    sys.exit(1)

# start the recording
command="record=on:%d:1:%s:%s:%s" % (args.duration, scanname, args.experiment, args.code)
ret = mark6.sendCommand(command)

time.sleep(args.duration+1)

print ("Verifying the recording...")
count = 0
while count < 10:
    ret = mark6.sendCommand("record?")
    if ret.fields[0] == "off" and ret.fields[2].strip() == scanname:
        print ("Recording sucessfull")
        sys.exit(0)
    time.sleep(1)
    count += 1
    print ("Retrying %d/10" % count)

print ("The recording seems to have failed. Check the state directly with the mark6 software e.g. da-client")
sys.exit(1)
