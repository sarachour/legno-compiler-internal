

BMARK=$1
python3 legno.py $BMARK arco --xforms 0 --abs-circuits 25 --conc-circuits 1
python3 legno.py $BMARK jaunt
python3 legno.py $BMARK gen
