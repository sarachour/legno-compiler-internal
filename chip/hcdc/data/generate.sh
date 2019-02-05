#!/bin/bash
#rm breaks.txt
#python3 breakbb.py .
#BREAKFILE='breaks.txt'
python3 genbb.py integ1x.csv in integ1x.bb ${BREAKFILE}
python3 genbb.py mult10x.csv in0 mult10x.bb ${BREAKFILE}
python3 genbb.py mult1x.csv in0 mult1x.bb ${BREAKFILE}
python3 genbb.py fanout1x.csv in fanout1x.bb ${BREAKFILE}
python3 genbb.py fanout10x.csv in fanout10x.bb ${BREAKFILE}
python3 genbb.py global_xbar.csv in global_xbar.bb ${BREAKFILE}
python3 genbb.py tile_xbar.csv in tile_xbar.bb ${BREAKFILE}
