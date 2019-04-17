
BMARK=$1
HWENV=$2
if [ -z "$HWENV" ]
then
	  HWENV="default"
fi


#rm -rf outputs/legno/default/$BMARK*
python3 legno.py $BMARK arco --xforms 1 --abs-circuits 1 --conc-circuits 1
python3 legno.py $BMARK jaunt --scale-circuits 3
python3 legno.py $BMARK skelter --recompute
#python3 legno.py $BMARK jaunt --physical --sweep
#python3 legno.py $BMARK skelter
python3 legno.py $BMARK srcgen $HWENV --recompute

