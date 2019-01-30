
BMARK=$1
MATHENV=$2
HWENV="default"
#python3 legno.py $BMARK srcgen $MATHENV $HWENV
python3 legno.py $BMARK scriptgen --math-env $MATHENV --hw-env $HWENV 

