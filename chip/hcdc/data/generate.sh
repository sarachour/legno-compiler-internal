#!/bin/bash
rm breaks.txt
python3 breakbb.py .
python3 genbb.py fanout1x.csv in breaks.txt fanout1x.bb
python3 genbb.py fanout10x.csv in breaks.txt fanout10x.bb
python3 genbb.py mult10x.csv in0 breaks.txt mult10x.bb
python3 genbb.py mult1x.csv in0 breaks.txt mult1x.bb
python3 genbb.py global_xbar.csv in breaks.txt global_xbar.bb
python3 genbb.py tile_xbar.csv in breaks.txt tile_xbar.bb
python3 genbb.py integ.csv in breaks.txt integ.bb
