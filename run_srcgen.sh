
BMARK=$1
MATHENV=$2
HWENV="default"
python3 legno.py $BMARK srcgen $MATHENV $HWENV
python3 legno.py $BMARK skelter --math-env $MATHENV --hw-env $HWENV --gen-script-list
