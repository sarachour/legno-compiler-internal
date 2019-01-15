
BMARK=$1
MATHENV=$2
HWENV="default"
#python3 legno.py $BMARK execprog $MATHENV
#python3 legno.py $BMARK arco --xforms 0 --abs-circuits 25 --conc-circuits 1
python3 legno.py $BMARK jaunt --scale-circuits 15
#python3 legno.py $BMARK srcgen $MATHENV $HWENV
#python3 legno.py $BMARK skelter --math-env $MATHENV --hw-env $HWENV --gen-script-list

