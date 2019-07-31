#!/usr/bin/env python3

import socket # net connections
import time # manage cutoff times
import threading # multiple connections
import os # file checks and deletion
import random # generate random id for each BackgroundProcess obj
import subprocess # start shell-based commands (like starting test server)
import multiprocessing # start comms in background
import signal # catches term events
import psutil # gets all child processes for killing
import argparse # parsing CLI args
import logging # handles logs received from clients
import socketserver # handles network receive of client logs
import datetime # generates log files from tests

logname = "logs/" + str(datetime.datetime.now()).replace(" ", "_") + '.log'

logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(clientip)s %(message)s', filename=logname, filemode='a')


class SyslogHandler(socketserver.BaseRequestHandler):
	def handle(self):
		data = bytes.decode(self.request[0].strip())
		socket = self.request[1]
		print( "%s : " % self.client_address[0], str(data))
		logging.info(str(data), extra={"clientip": self.client_address[0]})

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
			proc = multiprocessing.Process(target=self.processName, args=(self.id,))
			proc.start()
		else:
			print("Starting command '%s'" % self.processName)
            
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


class ClientInfo:
	"""Class that holds the information of each client"""
	def __init__(self, socket, addr, cliType):
		self.socket = socket
		self.addr = addr
		self.type = cliType

class NetController:
	"""Main controller class. Handles all connections and timing"""
	def __init__(self, numClients, runtime):
		# sets up server socket
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s.bind(("0.0.0.0", 1337))

		self.execTime = runtime
		self.wait = True
		self.currTime = time.time()
		self.endTime = 0
		self.clientArray = []
		self.numClients = numClients

	def init(self, s):
		"""Initializes the connected client"""
		get = s.recv(1024).decode().split(' ')
		
		while get[0] != 'comp':
	
			if get[0] == 'cli':
				s.send(str(self.numClients).encode())
			elif get[0] == "list":
				s.send(str(os.listdir("files")).encode())
			else:
				self.sendfiles(get[1], s)
			
			get = s.recv(1024).decode().split(' ')
		s.close()
		print("[i] Initialized client")

	def beginTime(self):
		"""Starts all threads and sets up timing for waitloops"""
		
		self.currTime = time.time()
		self.endTime = self.currTime + (self.execTime * 60)
		for i in range(len(self.clientArray)):
			threading.Thread(target = self.waitloop,args = (self.clientArray[i].socket,i)).start()


	def sendfiles(self, filename, s):
		"""Sends requested file to client"""
		f = open('files/' + filename, 'rb')
		size = os.path.getsize('files/' + filename)
		data = f.read()
		f.close()
		s.send(str(size).encode())
		s.recv(32)
		s.sendall(data)

	def recvall(self, sock, n):
		"""Receives all data from self.s given size"""
		data = b''
		while len(data) < n:
			packet = sock.recv(n - len(data))
			if not packet:
				return None
			data += packet
		return data

	def waitloop(self, s, index):
		"""Manages sockets and execution time"""
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
		"""Waits for clients to connect, handles init and start"""
		print("[ ] Starting Syslog collection server...")
		proc = BackgroundProcess(syslogLoop)
		proc.start()
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
			
			struct = ClientInfo(sock, addr, cliType)
			self.clientArray.append(struct)
			
			if len(self.clientArray) == self.numClients:
				print("[+] Beginning timing loop...")
				self.wait = False
				self.beginTime()

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

def syslogLoop(param):
	try:
		host = '0.0.0.0'
		port = 10000
		server = socketserver.UDPServer((host,port), SyslogHandler)
		server.serve_forever(poll_interval=0.5)
	except (IOError, SystemExit):
		raise
	except KeyboardInterrupt:
		print ("[Syslog Server] Crtl+C Pressed. Shutting down.")

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
	
