#!/usr/bin/env python
import socket
import readline # rlcompleter dependency
import rlcompleter # command completion
import argparse # parse command line args

class Downloader:
    """Class that downloads files from controller server"""

    def __init__(self, ip, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.numCli = 0
        
        
    def doConnect(self):
        try:
            self.s.connect((self.ip, self.port))
            self.s.send(b'init')
            self.s.recv(32)
            return 0
        except ConnectionRefusedError:
            print("Connection to server failed: Connection refused")
            return 1
        except ConnectionResetError:
            print("Connection to server failed: Connection reset by server")
            return 1


    def getList(self):
        self.s.send(b"list")
        buff = self.s.recv(4096)
        return buff

    def doDisconnect(self):
        self.s.send(b'comp')

    def getfiles(self, file):
        """Gets target file from controller server"""

        self.s.send(b"get " + file.encode())
        size = int(self.s.recv(1028).decode())
        self.s.send(b'ok')
        dat = self.recvall(size)
        if dat == None:
            print("[-] Failed to get file. Server did not send data")
            self.s.send(b'err')
            return -1
        else:
            f = open(file, 'wb')
            f.write(dat)
            f.close()
            print("[i] Written file '%s'" % file)
            
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


class Completer(object):
    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [s for s in self.options 
                                    if s and s.startswith(text)]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        # return match indexed by state
        try: 
            return self.matches[state]
        except IndexError:
            return None



def main():
    ip = input("Enter controller ip >> ")
    port = int(input("Enter controller port >> "))

    completer = Completer({"exit", "list", "get"})

    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")

    obj = Downloader(ip, port)
    ret = obj.doConnect()
    if ret == 1:
        return
    cmd = "".split(' ')
    while cmd[0] != "exit":
        cmd = input(" > ").split(" ")
        if cmd[0] == "list":
            print(obj.getList())
        elif cmd[0] == "get":
            obj.getfiles(cmd[1])
        elif cmd[0] == "exit":
            print("Quitting...")
            obj.doDisconnect()
            break
        else:
            print("Not a command...")
    return

if __name__ == "__main__":
    main()