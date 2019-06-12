
BMARK=$1
HWENV=$2
STANDARD="--standard"
PHYSICAL="--physical"
#STANDARD=""
if [ -z "$HWENV" ]
then
	  HWENV="default"
fi


#rm -rf outputs/legno/default/$BMARK*
echo python3 legno.py $STANDARD $BMARK arco --xforms 1 --abs-circuits 1 --conc-circuits 1
python3 legno.py $STANDARD $BMARK arco --xforms 1 --abs-circuits 1 --conc-circuits 1
echo python3 legno.py $STANDARD $BMARK jaunt $PHYSICAL --scale-circuits 3
python3 legno.py $STANDARD $BMARK jaunt $PHYSICAL --scale-circuits 3
#python3 legno.py $STANDARD $BMARK skelter --recompute
#python3 legno.py $BMARK jaunt --physical --sweep
#python3 legno.py $BMARK skelter
echo python3 legno.py $STANDARD $BMARK srcgen $HWENV --recompute
python3 legno.py $STANDARD $BMARK srcgen $HWENV --recompute

