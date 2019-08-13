"""This is a standalone version of the zombie testing stuff"""


import argparse # parses CLI args
import time
import multiprocessing
import random
import hashlib
import sys
import glob
import os
import subprocess
import simplecrypt as sc
import psutil
import signal

class timeout:
    def __init__(self, seconds=1, error_message='TimeoutError'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)

class CommStruct:
    def __init__(self, ptr, time):
        self.ptr = ptr
        self.time = time

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
            print("Starting command '%s'" % string)
            self.proc = multiprocessing.Process(target=self.processName, args=(self.id,))
            self.proc.start()
        else:
            print("Starting command '%s'" % self.processName)
            
            self.proc = multiprocessing.Process(target=self.callProc)
            self.proc.start()

    def callProc(self):
        """Wrapper process for CLI commands, as you cannot pass required args to subprocess.call()"""
        
        subprocess.call(self.processName, shell=True)
        f = open('.' + self.id, 'w')
        f.write("dead")
        f.close()
        print("Process has died")
    
    def isAlive(self):
        """Returns bool of whether the proc is dead or not"""
        self.proc.join(timeout=0)
        if self.proc.is_alive():
            return 1
        return 0



def encrypt(procnum):
    """Continuously encrypts and decrypts data until the endtime is hit"""
    global endtime

    while True:
        currTime = time.time()
        if currTime > endtime:
            print("Hit end time")
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
    print("Beginning encrypy/decrypt routines")
    print('Running load on CPU')
    print('Utilizing %d cores' % processes)
    pool = multiprocessing.Pool(processes)
    pool.map(encrypt, range(processes))
    print("Completed encrypt/decrypt routines")
    f = open('.' + id, 'w')
    f.write("dead")
    f.close()

def echoSleep(self):
    print("Hello world!")
    time.sleep(10)


def crackPass(catch):
    """Simple password cracking function (as an alternative to CLI-based programs)"""

    # hash for SuperPassword
    target = "52101400a06b0d716b0092edf68c492b" 

    # Password file
    f = open("passes.txt", 'rb')
    #f = open("/usr/share/wordlists/password/rockyou.txt", 'rb')
    data = b""
    ctr = 0
    end = False
    print("[+] Loading wordlist into memory")
    try:
        data = f.read()
        data = data.split(b'\n')
    except UnicodeDecodeError:
        pass

    ctr = 0
    f.close()
    print("[+] Passwords loaded: %s" % len(data))
    time.sleep(5)

    print("[+] Breaking password...")
    for password in data:
        password = password.strip(b"\n")
        hashobj = hashlib.md5()
        hashobj.update(password)
        guess = hashobj.hexdigest()
        if guess == target:
            print("[+] Password identified: %s" % password.decode())
            return 0
        if ctr % 10000 == 0:
            print("Current index: %d, Password: %s, Hash: %s" % (ctr, password, guess))
        ctr +=1

    print("[-] No password identified for hash: %s" % target)
    print("\tPasswords tried: %d" % ctr)
    return 1

def killall():
    """Kills all child processes and cleans up remaining ID files"""
    num = 1

    try:
        parent = psutil.Process(os.getpid())
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        print("[ ] Killing child process #%d" % num)
        process.send_signal(signal.SIGTERM)
        num += 1
    print("[i] All proceesses killed off. Cleaning up...")
    for file in glob.glob(".0x*"):
        print("[i] Found leftover file %s" % file)
        try:
            os.remove(file)
        except IsADirectoryError:
            pass



def main():
    parser = argparse.ArgumentParser(description="Synchronizes executions across multiple machines")
    parser.add_argument('type', help="Define the execution profile")
    
    args = parser.parse_args()

    comms = []

    if args.type == "basic":
        print("[+] Starting 'basic' VM command list...")
        comms = [CommStruct(echoSleep, 5*60)]
    elif args.type == "max":
        print("[+] Starting 'max' VM command list...")
        comms = [CommStruct(crackPass, 5*60)]
    elif args.type == "vary":
        print("[+] Starting 'vary' VM command list...")
        comms = [CommStruct(maxCPU, 2*60), 
            CommStruct("curl http://mirror.math.princeton.edu/pub/ubuntu-iso/14.04/ubuntu-14.04.6-desktop-amd64.iso -o file.iso", 0),
            CommStruct("rm file.iso", 0)]
    else:
        print("[-] Illegal type argument: '%s'" % args.type)
        sys.exit(1)


    currIndex = 0
    no_limit = False
    end_time = 0
    for process in comms:
        proc = BackgroundProcess(process.ptr)
        if process.time == 0:
            no_limit = True
        else:
            end_time = time.time() + process.time
        proc.start()

        if no_limit:
            while proc.isAlive():
                time.sleep(5)
        else:
            curr_time = time.time()
            while curr_time <= end_time:
                if not proc.isAlive():
                    print("[+] Process ended. Starting...")
                    proc = BackgroundProcess(process.ptr)
                    proc.start()
                time.sleep(5)
                print("Sleeping...")
                diff = end_time - curr_time
                print("Time diff: %f" % diff)
                curr_time = time.time()

        killall()





        currIndex += 1
        

main()