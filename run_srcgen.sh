
BMARK=$1
HWENV="default"
python3 legno.py $BMARK srcgen $HWENV && \
    python3 legno.py $BMARK scriptgen --hw-env $HWENV

