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
import argparse
import shutil
import subprocess
from datetime import datetime
import shlex
import json

progs = ["mk6record.py", "mountRecorder.sh", "unmountRecorder.sh", "getM5specTone.py"]

def description():

    d = "A program for recovering injected tones from data recorded on a Mark6 VLBI recorder. "
    d += "For this a short test recording is carried out on a remote Mark6 recorder, the data. "
    d += "is then fuse mounted and m5spec is executed on the recorder to create the spectra "
    d += "for both polarizations. The tones are recovered from the spectra and are reported. "
    d += "Optionally plots of the spectra with the discovered tones can be displayed. "

    return(d)

def checkPrerequisits():
    '''
    Validates that required programs etc. are available
    '''

    error = 0
    for prog in progs:
        path = shutil.which(prog)
        if path is None:
            error += 1
            print ("Required executable: %s not found in the path" % (prog))
    
    if error > 0:
        sys.exit("Exiting")

def plotM5spec(lowFreq):

    arg = ""
    if args.showPlot:
        arg = "-X"
    elif args.json:
        arg = "-j"

    #workDir = "/home/oper/tonecheck/test"
    pol1Cmd = "getM5specTone.py %s -l %d -t %s %s/pol1.m5spec " % (arg, lowFreq, "Polarization_1", workDir)
    pol2Cmd = "getM5specTone.py %s -l %d -t %s %s/pol2.m5spec " % (arg, lowFreq, "Polarization_2", workDir)

    if args.showPlot:
        os.system(pol1Cmd + "&")
        os.system(pol2Cmd + "&")
    else:
        p = subprocess.Popen(shlex.split(pol1Cmd),  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = p.stdout.readlines()
        # the serialized string must be deserialized into a list
    
        if (args.json):
            tones = json.loads(result[0].decode('utf-8'))
            print (tones)
        else:
            print (result)

        p = subprocess.Popen(shlex.split(pol2Cmd),  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = p.stdout.readlines()
        # the serialized string must be deserialized into a list
        if (args.json):
            tones = json.loads(result[0].decode('utf-8'))
            print (tones)

    
def recordScan(recorder, scanname, code):

    ret = subprocess.run(['mk6record.py', '-d 5', '-c %s'%(code), '-s %s'%(scanname), '-e tone', recorder])
    if ret.returncode > 0:
        return(False)

    return(True)

def fuseUnmount(recorder, slot):

    ret = subprocess.Popen(['unmountRecorder.sh', recorder, slot], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = ret.stdout.readlines()

    return(True)

def fuseMount(recorder, slot):

    ret = subprocess.Popen(['mountRecorder.sh', recorder, slot], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = ret.stdout.readlines()

    for token in result:
        if 'Found 0 scans' in token.decode('utf-8'):
            return(False)
    return(True)

def runRemoteM5spec(recorder, slot, code, scanname):

    # To do: check if remote mount directory exists
    # To do: handle abolute path on the remote side (remote which ?)
    command = "/home/oper/shared/difx/latest/bin/m5spec /mnt/diskpack/%s/tone_%s_%s.vdif %s 512 1024 /tmp/%s_%s.m5spec" % (slot, code, scanname, dataFormat, scanname, slot)

    ssh = subprocess.Popen(["ssh", recorder, command], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()

    return("/tmp/%s_%s.m5spec"%(scanname, slot))

def copyM5spec(recorder, inname, outname):

    ret = subprocess.run(['scp', 'oper@%s:%s'%(recorder, inname), "%s/%s" % (workDir, outname)])
    return(True)


def startModeOCT(args):
    global dataFormat
    print ("Starting OCT processing")
    dataFormat = "VDIF_8192-8192-1-2"

def startModeDDC(args):
    global dataFormat
    print ("Starting DDC processing")
    dataFormat = "VDIF_%d-%d-%d-2" % (args.payloadSize, args.dataRate, args.numChannels)

    
# parse the command line options
parser = argparse.ArgumentParser( description=description())


subparsers = parser.add_subparsers (help="subcomand help")
subparsers.required = True

parser_ddc = subparsers.add_parser ('ddc', help='ddc mode help')
parser_oct = subparsers.add_parser ('oct', help='oct mode help')

# ddc mode
group = parser_ddc.add_mutually_exclusive_group(required=True)
group.add_argument("-j","--json",  action='store_true', help="Print the tone information in serialized json format")
group.add_argument("-X", dest='showPlot', action='store_true', help="Show a graphical display of the spectrum and the detected tones.")
parser_ddc.add_argument("-ps", '--payload-size', type=int, default=8192, dest='payloadSize', help='The size (in bytes) of the VDIF packet payload (default: %(default)s).')
parser_ddc.add_argument("-dr", '--data-rate', type=int, default=8192, dest='dataRate', help='The recording data rate (in Mpbs) per polarisation (default: %(default)s).')
parser_ddc.add_argument("-nc", '--num-channels', type=int, default=1, dest='numChannels', help='The number of VDIF channels (default: %(default)s).')
parser_ddc.add_argument("-p1", "--pol1-slot", type=str, default="1", dest="pol1Slot", help="The slot(s) in the recorder used for the 1st polarization. If data is in a group use e.g. 12 or 34 (default: %(default)s)")
parser_ddc.add_argument("-p2", "--pol2-slot", type=str, default="2", dest="pol2Slot", help="The slot(s) in the recorder used for the 2nd polarization. If data is in a group use e.g. 12 or 34 (default: %(default)s)")
parser_ddc.add_argument("-l", "--low-freq", type=int, dest="lowChan", default=0, help="The frequency of the lowest baseband channel [MHz] (default: %(default)s).")
parser_ddc.add_argument("-c", "--station-code", type=str, dest="code", default='Pv', help="The 2-letter station code to use for the recording default: %(default)s).")

parser_ddc.add_argument("recorder", type=str, help="The hostname or IP of the mark6 recorder.")
parser_ddc.set_defaults(func=startModeDDC)


# oct mode (not yet implemented
parser_oct.set_defaults(func=startModeOCT)
parser_oct.add_argument("recorder", type=str, help="The hostname or IP of the mark6 recorder.")

#group2.add_argument("--previous", action='store_true', help="Path to previously created m5spec files. Tone extraction is done on these files; no recording is executed.")

args = parser.parse_args()
# got to the different processing modes
args.func(args)

print (dataFormat)

now = datetime.now().strftime("%y%m%d-%H%M%S")
# set the working directory 
workDir = "/home/oper"
try:
    workDir = os.environ['HOME']
except:
    pass
workDir += "/tonecheck/%s" % now

# create working directory if it does not exist
if not os.path.exists(workDir):
    os.makedirs(workDir)

print ("=== The working directory is: %s" % workDir)

checkPrerequisits()

scan = datetime.now().strftime("%y%m%d-%H%M%S")

state = True
# start a recording
print ("=== Starting recording on %s" % args.recorder)
state = recordScan(args.recorder, scan, args.code)
if not state:
    sys.exit("An error has occured during recording. Exiting")

# fuse mount the remote modules for pol1 and pol2
print ("=== Fuse mounting the modules")
state = fuseMount(args.recorder, args.pol1Slot)
if not state:
    print("An error has occured during fuse mounting of slot %s in %s" % (args.pol1Slot, args.recorder))
    print("The recording was expected to be done in slot(s)=%s (for pol 1) and slot(s)=%s (for pol 2)" % (args.pol1Slot, args.pol2Slot))
    print("Different setups can be specified with the -p1 and -p2 options. See help for details.")
    sys.exit(1)

state = fuseMount(args.recorder, args.pol2Slot)
if not state:
    sys.exit("An error has occured during fuse mounting of slot %s in %s. Exiting" % (args.pol2Slot, args.recorder))

# run m5spec on the recorder
print ("=== Running m5spec")
file = runRemoteM5spec(args.recorder, args.pol1Slot, args.code, scan)
copyM5spec(args.recorder, file, "pol1.m5spec")

file = runRemoteM5spec(args.recorder, args.pol2Slot, args.code, scan)
copyM5spec(args.recorder, file, "pol2.m5spec")

if not os.path.exists(workDir + "/pol1.m5spec") or not os.path.exists(workDir + "/pol2.m5spec"):
    sys.exit("Error in obtaining the m5spec file. Exiting")


# plotting the spectra
print ("=== Extracting the tones")
plotM5spec(args.lowChan)

print ("=== Fuse umounting the modules")
state = fuseUnmount(args.recorder, args.pol1Slot)
