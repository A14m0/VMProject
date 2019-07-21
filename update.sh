#!/bin/bash

echo -e "\033[1mCompiling and moving MemAlloc.cpp\033[0m"
cd MemAlloc
g++ MemAlloc.cpp -o MemAlloc
mv MemAlloc ../control/controller/files/

echo -e "\033[1mCompiling and moving collector\033[0m"
cd ../collector
g++ collector.cpp ping.cpp -o collector -fpermissive -lpthread
mv collector ../control/controller/files/

echo -e "\033[1mCopying plotter.py\033[0m"
cd ../plotter
cp plotter.py ../control/controller/files/

echo -e "\033[1mCopying zombie.py\033[0m"
cd ../control/zombie
cp zombie.py ../controller/files/

echo -e "\033[1mCompiling server\033[0m"
cd ../controller/server
gcc server.c -o server

echo -e "\033[1mCopying downloader tool\033[0m"
cd ../../downloader
cp downloader.py ../controller/files

