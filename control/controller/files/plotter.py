#!/usr/bin/env python3
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import csv
import os
import datetime
from random import randint

class data:
    """Class for storing information from generated .CSV files"""
    def __init__(self, date, time, num, cpu, mem, net, filename):
        self.date = date # date array
        self.cpu = cpu # cpu access time avg array
        self.mem = mem # mem access time avg array
        self.net = net # net comm time avg array
        self.num = num # number of VMs
        self.time = time # time of each avg set write
        self.name = filename


filenames = []
allout = False

def getOpt(path):
    """Handles user file selection"""
    global allout
    files = []

    # finds all files in path that are .csv
    for r, d, f in os.walk(path):
        for filename in f:
            if '.csv' in filename:
                if "netDat_" not in filename:
                    if filename not in filenames:
                        files.append(filename)

    i = 1

    # tests if there are no files
    if len(files) == 0:
        return -1
    # tests if there are no NEW files
    elif len(files) == 1:
        allout = True

    print("Select files to graph: ")
    # prints listing of all files
    for filename in files:
        f = open(path + "/" + filename)
        f.readline()
        header = f.readline().split(",")[2]
        print("\t%s) %s (%s VMs)" % (str(i), filename, header))
        i += 1
    print("\t%s) All .CSV Files" % str(i))

    try:
        fileindex = int(input("File to make graph of? >> ")) -1
        if fileindex == i -1:
            return files
    except ValueError:
        print('[-] Value \'%s\' isn\'t an option' % str(filename))
        return -1

    if fileindex > len(files) -1 or fileindex < 0:
        print("[-] Value '%s' isn't an option" % str(fileindex))
        return -1

    return files[fileindex]


def getData(path, filename):
    """Loads data into Data object from file"""

    global allout

    if filename == -1:
        allout = True
        return

    # adds required path seperator
    if path[-1] != '/':
        path = path + '/'

    file = open(path + filename, 'r')
    reader = csv.reader(file, delimiter=',')
    
    datearr = []
    memarr = []
    cpuarr = []
    netarr = []
    timearr = []
    numVM = ""

    # reads in data information from .CSV file
    netfilename = ""
    

    foundName = False
    for row in reader:
        print(row)
        try:
            if not foundName:
                netfilename = row[5]
                print("Founded")
                foundName = True

            datearr.append(row[0])
            timearr.append(row[1])
            numVM = row[2]
            cpuarr.append(int(row[3]))
            memarr.append(int(row[4]))

        except ValueError:
            pass

    print(netfilename)
    netfile = open(path + netfilename, 'r')
    netreader = csv.reader(netfile, delimiter=',')

    for row in netreader:
        try:
            netarr.append(float(row[2]))
        except ValueError:
            pass

    

    # remove the header from the data
    datearr = datearr[1:]
    #memarr = memarr[1:]
    #cpuarr = cpuarr[1:]
    #netarr = netarr[1:]

    for i in range(len(datearr)):
        string = datearr[i]
        
        string = string.split(" ")[3]
        datearr[i] = string

    return data(datearr, timearr, numVM, cpuarr, memarr, netarr, filename)


def getSmallest(data):
    """Gets the smallest range for a data set"""
    
    smallest = len(data[0].date)
    
    for set in data:
        if len(set.date) < smallest:
            smallest = len(set.date)

    return smallest


def graph(data):
    """Generates graphs from passed data object"""

    print("[ ] Generating graph...")
    

    # gets the smallest data set size of all passed sets
    rng = getSmallest(data)
    t = np.arange(0, rng, 1)

    netT = np.arange(0, len(data[0].net), 1)

    gs = gridspec.GridSpec(3,1)
    fig = plt.figure(1, figsize=[40,40]) # Note that this is in inches

    colors = []
    cpu = fig.add_subplot(gs[0,0])
    for value in data:
        # randomizes color of any one passed .CSV data set
        r = float(randint(0,255)) / 255
        g = float(randint(0,255)) / 255
        b = float(randint(0,255)) / 255
        rgb = (r,g,b)
        colors.append(rgb)
        
        # cleans up displayed name up in the legend
        namearr = value.name.split(' ')
        name = namearr[:2]
    
        if namearr[2] == "":
            name.append(namearr[3])
        else:
            name.append(namearr[2])
    
        string = "%s (%s VMs)" % (" ".join(name), value.num)
    
        cpu.scatter(t, value.cpu[:rng], color=(r,g,b), marker='.', label=string)
    
    plt.legend(loc='upper left')
    plt.ylabel("CPU calculation times")
    plt.xlabel("Time")

    counter = 0
    mem = fig.add_subplot(gs[1,0])
    for value in data:
        r = float(randint(0,255)) / 255
        g = float(randint(0,255)) / 255
        b = float(randint(0,255)) / 255

        namearr = value.name.split(' ')
        name = namearr[:2]
    
        if namearr[2] == "":
            name.append(namearr[3])
        else:
            name.append(namearr[2])
    

        string = "%s (%s VMs)" % (" ".join(name), value.num)
        mem.scatter(t, value.mem[:rng], color=colors[counter], marker='.', label=string)
        counter +=1
    
    plt.legend(loc='upper left')
    plt.ylabel("Memory access times")
    plt.xlabel("Time")

    counter = 0
    net = fig.add_subplot(gs[2,0])
    for value in data:
        # randomizes color of any one passed .CSV data set
        r = float(randint(0,255)) / 255
        g = float(randint(0,255)) / 255
        b = float(randint(0,255)) / 255
        
        namearr = value.name.split(' ')
        name = namearr[:2]
    
        if namearr[2] == "":
            name.append(namearr[3])
        else:
            name.append(namearr[2])
    
        string = "%s (%s VMs)" % (" ".join(name), value.num)
        net.scatter(netT, value.net, color=(r,g,b), marker='.', label=string)
        counter += 1
    
    plt.legend(loc='upper left')
    plt.ylabel("Network transmission times")
    plt.xlabel("Time")

    date = str(datetime.datetime.today())
    plt.show()
    
    plt.savefig(date + ".png")
    print("[+] Graph saved")


def main():
    opt = 'y'
    datarr = []
    listex = []
    
    # checks if config file exists
    if not os.path.exists("path.cfg"):
        print("[i] Creating path.cfg...")
        f = open("path.cfg", 'w')
        f.write("files/data")
        f.close()
    
    # reads in config file
    f = open("path.cfg", 'r')
    filepath = f.read().strip("\n")
    f.close()
    global allout

    try:
        while opt != 'n':
            filename = getOpt(filepath)

            # catches generic fail
            if filename == -1:
                continue
            # catches "All CSV" option
            elif type(filename) == type(listex):
                for file in filename:
                    data = getData(filepath, file)
                    datarr.append(data)
                    allout = True
            else:
                filenames.append(filename)
        
                data = getData(filepath, filename)
                datarr.append(data)
        
            if allout:
                break
        
            opt = input("Add another CSV file to the graph? (Y/n) >> ").lower()
            if opt != '':
                if opt != 'n' and opt != 'y':
                    print("[-] '%s' isn't an option. Defaulting to 'Y'" % opt)
    
        # graph the data
        graph(datarr)
        return 0
    except KeyboardInterrupt:
        print("\n[!] Caught ^C. Exiting...")
        return 1

if __name__ == "__main__":
    main()



