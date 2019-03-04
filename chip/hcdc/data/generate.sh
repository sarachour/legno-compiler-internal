#!/bin/bash
#rm breaks.txt
GLOBAL_SCALE=0.01
DEP_FRAC=0.00
python3 genbb.py integ1x.csv in integ-m1x.bb  2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py integ1x.csv in integ-l1x.bb  0.2 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py integ1x.csv in integ-h1x.bb  20.0 ${DEP_FRAC} ${GLOBAL_SCALE}

python3 genbb.py integ1x.csv in integ-m10x.bb  2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
#python3 genbb.py integ1x.csv in integ-l10x.bb  0.2 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py integ1x.csv in integ-h10x.bb  20.0 ${DEP_FRAC} ${GLOBAL_SCALE}

python3 genbb.py integ1x.csv in integ-m01x.bb  2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py integ1x.csv in integ-l01x.bb  0.2 ${DEP_FRAC} ${GLOBAL_SCALE}
#python3 genbb.py integ1x.csv in integ-h01x.bb  20.0 ${DEP_FRAC} ${GLOBAL_SCALE}

# multiplication
GLOBAL_SCALE=1.0
DEP_FRAC=0.02
python3 genbb.py mult1x.csv out mult-m1x.bb 2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py mult1x.csv out mult-l1x.bb 0.2 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py mult1x.csv out mult-h1x.bb 20.0 ${DEP_FRAC} ${GLOBAL_SCALE}

python3 genbb.py mult10x.csv out mult-m10x.bb 2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
# for mul: l l -> l
python3 genbb.py mult10x.csv out mult-l10x.bb 0.2 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py mult10x.csv out mult-h10x.bb 20.0 ${DEP_FRAC} ${GLOBAL_SCALE}

python3 genbb.py mult1x.csv out mult-m01x.bb 2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py mult1x.csv out mult-l01x.bb 0.2 ${DEP_FRAC} ${GLOBAL_SCALE}
# for mul h h -> h
python3 genbb.py mult1x.csv out mult-h01x.bb 20.0 ${DEP_FRAC} ${GLOBAL_SCALE}


# vga
GLOBAL_SCALE=1.0
DEP_FRAC=0.02
python3 genbb.py mult1x.csv out vga-m1x.bb 2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py mult1x.csv out vga-l1x.bb 0.2 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py mult1x.csv out vga-h1x.bb 20.0 ${DEP_FRAC} ${GLOBAL_SCALE}

python3 genbb.py mult10x.csv out vga-m10x.bb 2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
#python3 genbb.py mult10x.csv out vga-l10x.bb 0.2 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py mult10x.csv out vga-h10x.bb 20.0 ${DEP_FRAC} ${GLOBAL_SCALE}

python3 genbb.py mult1x.csv out vga-m01x.bb 2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py mult1x.csv out vga-l01x.bb 0.2 ${DEP_FRAC} ${GLOBAL_SCALE}
#python3 genbb.py mult1x.csv out vga-h01x.bb 20.0 ${DEP_FRAC} ${GLOBAL_SCALE}

# fanout / globals
GLOBAL_SCALE=1.0
DEP_FRAC=0.00
python3 genbb.py fanout1x.csv in fanout1x.bb 2.0 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py fanout10x.csv in fanout10x.bb 20.0 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py global_xbar.csv in global_xbar.bb 20.0 ${DEP_FRAC} ${GLOBAL_SCALE}
python3 genbb.py tile_xbar.csv in tile_xbar.bb 20.0 ${DEP_FRAC} ${GLOBAL_SCALE}
