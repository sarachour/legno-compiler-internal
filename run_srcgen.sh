
BMARK=$1
HWENV=$2
if [ -z "$HWENV" ]
then
	HWENV="default"
fi

python3 legno.py $BMARK srcgen $HWENV

