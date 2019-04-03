
BMARK=$1
#python3 legno.py $BMARK arco --xforms 1 --abs-circuits 2 --conc-circuits 1
#python3 legno.py $BMARK jaunt --scale-circuits 2
#python3 legno.py $BMARK skelter
python3 legno.py $BMARK jaunt --physical
#python3 legno.py $BMARK jaunt --physical --no-quality
python3 legno.py $BMARK skelter  --recompute
python3 legno.py $BMARK srcgen default --recompute
