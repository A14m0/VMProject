#!/usr/bin/env python3

import socket # network communications
import os # file checks/deletion
import time # timing 
import sys # handles program force exits
import multiprocessing # backgrounding commands
import subprocess # calling CLI programs
import random # random selection for process ID and comm selection
import simplecrypt as sc # encryption/decryption
import syslog # writing to syslog
import signal # catching system signals
import psutil # gets child processes
import glob # parsing all found hidden files to only include process hidden files
import argparse # parsing cli args
import traceback # debug import for troubleshooting
import hashlib # getting unique process IDs for management

def handle(signal, frame):
    """Handler for system signals"""
    syslog.syslog("Caught SIGTERM. Exiting")
    sys.exit(1)

signal.signal(signal.SIGTERM, handle)

def log(data):
    """Logs passed information to both syslog and console"""
    syslog.syslog(str(data))
    print(data)

def init(ip, port):
    """Initializes the client's files and working directory"""
    initializer = Initializer(ip, port)
    initializer.init()
    return initializer.numClients()



# TODO: ADD BACKGROUND PROCESS FORK FOR PROGRAMS
class Initializer:
    """Class that handles client initialization"""

    def __init__(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.numCli = 0
    
    def init(self):
        """Gets files from controller server"""

        self.s.connect((self.ip, self.port))
        self.s.send(b'init')

        resp = self.s.recv(32)

        if not os.path.isdir('files'):
            os.mkdir('files')

        self.getfiles('zombie.py')

        self.getfiles('collector')

        self.getfiles('MemAlloc')

        self.getfiles('passes.txt')
        
        self.s.send(b'cli')
        self.numCli = int(self.s.recv(32).decode())

        self.s.send(b'comp')
        self.s.close()
        return 

    def getfiles(self, file):
        """Gets target file from controller server"""

        self.s.send(b"get " + file.encode())
        size = int(self.s.recv(1028).decode())
        self.s.send(b'ok')
        dat = self.recvall(size)
        if dat == None:
            log("[-] Failed to get file. Server did not send data")
            self.s.send(b'err')
            return -1
        else:
            f = open("files/" + file, 'wb')
            f.write(dat)
            f.close()
            print("[i] Written file '%s'" % file)
            os.system('chmod +x files/' + file)


        return 0

    def recvall(self, n):
        """Receives all data from self.s given size"""
        data = b''
        while len(data) < n:
            packet = self.s.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def numClients(self):
        """Returns the server's expected number of clients"""
        return self.numCli




class BackgroundProcess:
    """Background Process class that takes a command and forks it 
    into a separate process"""
    def __init__(self, processName):
        self.processName = processName
        self.id = hex(random.getrandbits(128))
        self.alive = True
        
        if os.path.exists('.' + self.id):
            os.remove('.' + self.id)
        
    def start(self):
        """Parses and starts passed command"""

        if type(self.processName) != type("string"):
            string = str(self.processName).split(' ')[1]
            log("Starting command '%s'" % string)
            proc = multiprocessing.Process(target=self.processName, args=(self.id,))
            proc.start()
        else:
            log("Starting command '%s'" % self.processName)
            
            proc = multiprocessing.Process(target=self.callProc)
            proc.start()

    def callProc(self):
        """Wrapper process for CLI commands, as you cannot pass required args to subprocess.call()"""
        
        subprocess.call(self.processName, shell=True)
        f = open('.' + self.id, 'w')
        f.write("dead")
        f.close()
        print("Process has died")


    def isAlive(self):
        """Returns bool of whether the proc is dead or not"""
        return not os.path.exists('.' + self.id)


class Zombie:
    """Class that manages the start/stop/timing of all communications and commands"""

    def __init__(self, ip, port, cliType, numClients):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.go = ""
        self.numClients = numClients
        self.type = cliType
        self.pidArr = []

    def handleRando(self):
        """Handler for the random command set"""

        # below, you can add either functions or bash command strings
        randomcomms = ["ping -c 60 8.8.8.8", 
            "curl -o file.iso http://mirror.math.princeton.edu/pub/ubuntu-iso/14.04/ubuntu-14.04.6-desktop-amd64.iso", 
            maxCPU,
            crackPass, # crack the md5 hash of "SuperPassword"
            ]
        self.s.send(b"ok")
    
        while True:
            # choose random command from randomcomms
            index = random.randint(0, len(randomcomms) -1)
            
            proc = BackgroundProcess(randomcomms[index])
            proc.start()
            
            while proc.isAlive():
                self.go = self.s.recv(32).decode()
                
                # catches end of time signal from comms server
                if self.go == "Complete":
                    killall()
                    time.sleep(0.1)
                    self.s.close()
                    log("[i] Script complete")
                    return
                
                time.sleep(5)
                self.s.send(b'ok')
            log("[i] Process is complete, but time still exists on the clock. Choosing new proc...")
            
    def handleTester(self):
        """Handler for the tester command set"""

        proc = BackgroundProcess("files/collector n/a " + str(self.numClients))
        proc.start()
        self.s.send(b"ok")
        while True:
            self.go = self.s.recv(32).decode()
            if self.go == "Complete":
                killall()
                time.sleep(0.1)
                self.s.close()
                log("[i] Script complete.")
                return

            time.sleep(5)

            self.s.send(b"ok")

    def handleCPU(self):
        """Handler for the CPU-Intensive command set"""

        comms = [ "curl http://mirror.math.princeton.edu/pub/ubuntu-iso/14.04/ubuntu-14.04.6-desktop-amd64.iso -o file.iso",
            "files/MemAlloc file.iso 10",
            maxCPU
        ]
        currIndex = 0
        self.s.send(b"ok")
        while True:
            # tests if all commands have been run
            if currIndex >= len(comms) - 1:
                currIndex = 0
                log("[i] Completed one full cycle. Starting from the top")
            
            proc = BackgroundProcess(comms[currIndex])
            proc.start()
            
            while proc.isAlive():
                self.go = self.s.recv(32).decode()
                if self.go == "Complete":
                    killall()
                    time.sleep(0.1)
                    self.s.close()
                    log("[i] Script complete")
                    return
                time.sleep(5)
                self.s.send(b'ok')
            log("[i] Process is complete, but time still exists on the clock. Choosing new proc...")
            currIndex += 1   

    def start(self):
        """Starts the timing loop and selects correct handler function"""
        self.s.connect((self.ip, self.port))
        log("[+] Waiting for the go-ahead")
        
        self.s.send(self.type.encode())
        self.go = self.s.recv(32).decode()
        
        log("[i] Got: %s" % self.go)
        
        if self.type == "rando":
            self.handleRando()
        elif self.type == "tester":
            self.handleTester()
        elif self.type == "cpu":
            self.handleCPU()

endtime = 0

def encrypt(procnum):
    """Continuously encrypts and decrypts data until the endtime is hit"""
    global endtime

    while True:
        currTime = time.time()
        if currTime > endtime:
            log("Hit end time")
            return
        password = "superDuperPassword"
        data = "Secret something"
        enc = sc.encrypt(password, data)
        sc.decrypt(password, enc)

def maxCPU(id):
    """Utilizes as much CPU processing as possible"""

    global endtime

    endtime = time.time() + random.randint(0, 100000)

    processes = multiprocessing.cpu_count()
    log("Beginning encrypy/decrypt routines")
    log('Running load on CPU')
    log('Utilizing %d cores' % processes)
    pool = multiprocessing.Pool(processes)
    pool.map(encrypt, range(processes))
    log("Completed encrypt/decrypt routines")
    f = open('.' + id, 'w')
    f.write("dead")
    f.close()
        

def killall():
    """Kills all child processes and cleans up remaining ID files"""
    num = 1

    try:
        parent = psutil.Process(os.getpid())
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        log("[ ] Killing child process #%d" % num)
        process.send_signal(signal.SIGTERM)
        num += 1
    log("[i] All proceesses killed off. Cleaning up...")
    for file in glob.glob(".0x*"):
        print("[i] Found leftover file %s" % file)
        try:
            os.remove(file)
        except IsADirectoryError:
            pass
    
def crackPass():
    """Simple password cracking function (as an alternative to CLI-based programs)"""

    # hash for SuperDuperPassword
    target = "52101400a06b0d716b0092edf68c492b" 

    # Password hash
    f = open("files/passes.txt", 'r')
    data = f.readlines()
    f.close()

    for password in data:
        password = password.strip("\n")
        password = password.encode()
        hashobj = hashlib.md5()
        hashobj.update(password)
        guess = hashobj.hexdigest()
        if guess == target:
            print("Password identified: %s" % password.decode())
            return 0

    print("[-] No password identified for has: %s" % target)
    return 1
        
        