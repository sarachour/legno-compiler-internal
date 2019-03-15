
BMARK=$1
#rm -rf outputs/legno/default/$BMARK*
python3 legno.py $BMARK arco --xforms 1 --abs-circuits 1 --conc-circuits 1
python3 legno.py $BMARK jaunt --scale-circuits 1
python3 legno.py $BMARK skelter
python3 legno.py $BMARK jaunt --physical
python3 legno.py $BMARK skelter
python3 legno.py $BMARK srcgen default
