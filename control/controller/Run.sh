#!/bin/bash

# THIS IS AN OUTDATED RUN SCRIPT USED FOR REFERENCE
# THIS IS NOT USED IN THE ACTUAL, CURRENT VERSION
# OF THE SCRIPTS




trap ctrl_c INT

function ctrl_c() {
	echo "Ending now..."
	logger "Caught ^C. Ending program"
	echo "`date`	Caught ^C. Ending program" >> info.log
	xrandr -d :0 --output Virtual1 --mode 1152x864
	exit
}


trap quitter TERM

function quitter() {
	echo "Caught SIGTERM. Ending Program..."
	pkill curl
	pkill Manager.py
	pkill MemAlloc
	logger "Caught SIGTERM. Program ended"
	echo "`date`	Caught SIGTERM. Program ended" >> info.log
	xrandr -d :0 --output Virtual1 --mode 1152x864
	exit 1
}

# Sets VM display output to 800x600 to minimize GUI impact on data c
xrandr -d :0 --output Virtual1 --mode 800x600

while [ true ] 
do
	logger "Beginning network download test"

	
	echo "`date`	Beginning network download test" >> info.log

	curl http://mirror.math.princeton.edu/pub/ubuntu-iso/14.04/ubuntu-14.04.6-desktop-amd64.iso -o file.iso & wait
#	curl https://i.ytimg.com/vi/pOmu0LtcI6Y/hqdefault.jpg -o file.iso
	
	logger "Completed network download. Beginning CPU maxout"
	echo "`date`	Completed network test. Starting CPU maxout" >> info.log

	python Manager.py 1000 & wait

	logger "CPU maxout complete. Beginning memory test"
	echo "`date`	CPU maxout complete. Beginning memory test" >> info.log

	./MemAlloc file.iso & wait

	logger "Full system pace routines complete. Beginning from the top"
	echo "`date`	Full system pace routines complete. Starting over" >> info.log

done
