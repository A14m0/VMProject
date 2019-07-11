#!/usr/bin/env python3

import socket
import time
import threading
import os
import random
import subprocess
import multiprocessing
import syslog
import signal
import psutil
import argparse

def log(data):
    syslog.syslog(str(data))
    print(data)


class BackgroundProcess:
    def __init__(self, processName):
        self.processName = processName
        self.id = hex(random.getrandbits(128))
        self.alive = True
        
        if os.path.exists('.' + self.id):
            os.remove('.' + self.id)
        
    def start(self):
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
        # this is used because you cant pass "shell=True" through the args of multiprocessing
        subprocess.call(self.processName, shell=True)
        f = open('.' + self.id, 'w')
        f.write("dead")
        f.close()
        print("Process has died")


    def isAlive(self):
        return not os.path.exists('.' + self.id)


class ClientInfo:
	def __init__(self, socket, addr, cliType):
		self.socket = socket
		self.addr = addr
		self.type = cliType

class NetController:
	def __init__(self, numClients, runtime):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s.bind(("0.0.0.0", 1337))
		self.execTime = runtime
		self.wait = True
		self.currTime = time.time()
		self.endTime = 0
		self.clientArray = []
		self.numClients = numClients

	def beginTime(self):
		self.currTime = time.time()
		self.endTime = self.currTime + (self.execTime * 60)
		for i in range(len(self.clientArray)):
			threading.Thread(target = self.waitloop,args = (self.clientArray[i].socket,i)).start()

	def init(self, s):
		get = s.recv(1024).decode().split(' ')
		
		while get[0] != 'comp':
	
			if get[0] == 'cli':
				s.send(str(self.numClients).encode())
			
			elif get[1] == "zombie.py":
				f = open("files/zombie.py", 'rb')
				size = os.path.getsize("files/zombie.py")
				data = f.read()
				f.close()
				s.send(str(size).encode())
				s.recv(32)
				s.sendall(data)

			elif get[1] == 'collector':
				f = open('files/collector', 'rb')
				size = os.path.getsize('files/collector')
				data = f.read()
				f.close()
				s.send(str(size).encode())
				s.recv(32)
				s.sendall(data)

			elif get[1] == "MemAlloc":
				f = open("files/MemAlloc", 'rb')
				size = os.path.getsize("files/MemAlloc")
				data = f.read()
				f.close()
				s.send(str(size).encode())
				s.recv(32)
				s.sendall(data)
			#elif

			
			get = s.recv(1024).decode().split(' ')
		s.close()
		print("[i] Initialized client")


	def recvall(self, sock, n):
		data = b''
		while len(data) < n:
			packet = sock.recv(n - len(data))
			if not packet:
				return None
			data += packet
		return data

	def waitloop(self, s, index):
		s.send(b"begin")
		
		s.recv(16).decode()
		while True:
			if int(self.endTime) <= int(self.currTime):
				print("[+] Complete")
				s.send(b"Complete")
				s.close()
				print("[!] Don't forget to turn back on the firewall!!!")
				time.sleep(5)
				killall()
				return
			else:
				self.currTime = time.time()
				print("[%s]: Time remaining: %s seconds" % (index + 1, int(self.endTime - self.currTime)))
				s.send(b'no')
				s.recv(16)
				
	def waitForConnections(self):
		self.s.listen(5)
		print("[+] Listening for %s clients..." % str(self.numClients))
		while self.wait:
			sock, addr = self.s.accept()
			print("[ ] Got connection from %s" % addr[0])
			cliType = sock.recv(32).decode()
			if cliType == "init":
				sock.send(b'ok')
				self.init(sock)
				continue
			elif cliType == "tester":
				if not os.path.exists(".server"):
					proc = BackgroundProcess("server/server 13337")
					proc.start()
					print("[i] Started analysis server")

			struct = ClientInfo(sock, addr, cliType)
			self.clientArray.append(struct)
			
			if len(self.clientArray) == self.numClients:
				print("[+] Beginning timing loop...")
				self.wait = False
				self.beginTime()

def killall():
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


def main():
	parser = argparse.ArgumentParser(description="Control server to synchronize execution across multiple clients")
	parser.add_argument("-p", "--port", help="Define port to connect to. Default is 1337", default=1337, type=int)
	parser.add_argument("-u", "--update", help="Update the local file store then exit", action='store_true')
	parser.add_argument('clients', help="The number of clients for the server to handle", type=int)
	parser.add_argument('time', help="Time (in minutes) that the connected clients should execute for", type=float)
	args = parser.parse_args()

	print("[ ] Updating local source storage")
	os.system("./do_update.sh")
	print("[+] Local update complete")
	
	if args.update:
		return 0
	
	try:
		cont = NetController(args.clients, args.time)
		cont.waitForConnections()
	except KeyboardInterrupt:
		print("\n[i] Caught ^C. Exiting...")
		exit(1)
	
if __name__ == "__main__":
	main()
	