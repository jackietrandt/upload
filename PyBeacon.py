#!/usr/bin/python3.5
#
# Copyright 2015 Opera Software ASA. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Python script for scanning and advertising urls over Eddystone-URL.
"""
import re
import os
import signal
import subprocess
import sys
import time
import argparse
import Basket as bas
import socket


application_name = 'PyBeacon'

if (sys.version_info > (3, 0)):
    DEVNULL = subprocess.DEVNULL
else:
    DEVNULL = open(os.devnull, 'wb')


#---------------------------------------------------------
parser = argparse.ArgumentParser(prog=application_name, description= __doc__)

parser.add_argument('-s','--scan', action='store_true',
                    help='Scan for URLs.')
parser.add_argument('host', metavar='H', type=str, nargs='+',
                    help='Host name of current computer')

args = parser.parse_args()

#---------------------------------------------------------
basket1 = bas.basket(args.host[0])

host = "jt.earth"
port = 2004

tcpClientA = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
tcpClientA.connect((host, port))
print ("Connecting to :" , host)
print ("Port :" , port)
#---------------------------------------------------------

def scan(duration = None):
    """
    Scan for beacons. This function scans for [duration] seconds. If duration
    is set to None, it scans until interrupted.
    """
    Localname = ''
    print("Scanning...")
    subprocess.call("sudo hciconfig hci0 reset", shell = True, stdout = DEVNULL)

    lescan = subprocess.Popen(
            ["sudo", "-n", "hcitool", "lescan", "--duplicates"],
            stdout = DEVNULL)
    
    dump = subprocess.Popen(
            ["sudo", "-n", "hcidump", "-a"],
            stdout = subprocess.PIPE)

    packet = None

    try:
        startTime = time.time()
        
        for line in dump.stdout:
            #--- Send to TCP server
            tcpClientA.send(line) 
            #--- Then decode and put in basket
            line = line.decode()
            line = line.strip().split('\n')
            if 'HCI Event' in line[0]:
                Localname = ''
            if 'local name' in line[0]:
                Localname = line[0][22:]
                Localname = Localname[:-1]
            if 'bdaddr' in line[0]:
                MAC = line[0][7:25]
            if 'RSSI' in line[0]:
                Dist = line[0][6:]
                tocken1 = bas.tocken(Localname,basket1.chainname,MAC,Dist,50)
                basket1.addtocken(tocken1)
                #print(chr(27) + "[2J")
                #basket1.debug()
                time.sleep(0.3)


    except KeyboardInterrupt:
        pass

    subprocess.call(["sudo", "kill", str(dump.pid), "-s", "SIGINT"])
    subprocess.call(["sudo", "-n", "kill", str(lescan.pid), "-s", "SIGINT"])


def main():    
    if args.scan:
        scan()

if __name__ == "__main__":
    main()
