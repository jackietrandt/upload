#!/usr/bin/python3.5
from os import system
import socket
import threading
from threading import Thread
import _thread
import time
import queue
from socketserver import ThreadingMixIn
import Basket as bas
import pickle

basket_earth = bas.basket("192.168.0.112")
basket_deep = bas.basket("192.168.0.114")
basket_wind = bas.basket("192.168.0.110")
basket_mar = bas.basket("Mar")
tockenqueue = queue.Queue()
TrackingID = "68:9E:19:10:C7:94"
ZoneID = 8
Tape = []

def log_distance (TrackID,ZoneID):
    scanner1_dist = int(basket_earth.distance(TrackID))
    scanner2_dist = int(basket_deep.distance(TrackID))
    scanner3_dist = int(basket_wind.distance(TrackID))
    # zone ID, scanner 1 dist, scanner 2 dist, scanner 3 dist
    dataslide = [ZoneID,scanner1_dist,scanner2_dist,scanner3_dist]
    return dataslide
    
# Define a function for the thread
def mainfunc( threadName, delay):
    time.sleep(delay)
    print ("Wake up scanner 1")
    system("ssh root@jt.deep nohup python3 /home/jt/share/DeepOne/Tracker/PyBeacon.py -s jt.deep &")
    system("ssh root@jt.wind nohup python3 /home/jt/Share/DeepOne/Tracker/PyBeacon.py -s jt.wind &")
    system("python3 PyBeacon.py -s jt.earth &")
    while True:
        while not tockenqueue.empty():

            mytocken = tockenqueue.get()
            #print (" My tocken name :", mytocken.name)
            #print (" My tocken dist :", mytocken.distance)
            if basket_earth.chainname in mytocken.origin:
                basket_earth.addtocken(mytocken)
            elif basket_deep.chainname in mytocken.origin:
                basket_deep.addtocken(mytocken)
            elif basket_wind.chainname in mytocken.origin:
                basket_wind.addtocken(mytocken)
        print(chr(27) + "[2J")
        basket_earth.debug()
        basket_deep.debug()
        basket_wind.debug()
        basket_earth.update()
        basket_deep.update()
        basket_wind.update()
        #scan each slide of beacon distance to each scanner then put into tape
        Tape.append(log_distance(TrackingID,ZoneID))
        print (" Sample collected : ", len(Tape))
        if len(Tape) == 500:
            print (Tape)
            with open("datafile_zone8", 'wb') as f:
                pickle.dump(Tape, f)
        time.sleep(delay)
    
# Multithreaded Python server : TCP Server Socket Thread Pool
class ClientThread(Thread):
    def __init__(self, ip, port, conn):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        
        print ("[+] New server socket thread started for " + self.ip + ":" + str(port))
 
    def run(self):
        while True:
            linerec = self.conn.recv(2048)
            linerec = linerec.decode()
            linerec = linerec.strip().split('\n')
            for line in linerec:
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
                    tocken1 = bas.tocken(Localname,self.ip,MAC,Dist,50)
                    tockenqueue.put(tocken1)
          
 
 
# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0'
TCP_PORT = 2004
BUFFER_SIZE = 20  # Usually 1024, but we need quick response
 
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpServer.bind((TCP_IP, TCP_PORT))
print ("Listening on : ",TCP_IP)
print ("Port : ", TCP_PORT)
threads = []
tcpServer.listen(4)

# Create main thread
try:
    _thread.start_new_thread( mainfunc, ("Thread-M",0.3) )
    print ("Main thread started")
except:
    print ("Error: unable to start main thread")

while True:
       
    print ("Multithreaded Python server : Waiting for connections from TCP clients...")
    (conn, (ip, port)) = tcpServer.accept()
               
    newthread = ClientThread(ip, port, conn)
    newthread.start()
    threads.append(newthread)
    
for t in threads:
    t.join()