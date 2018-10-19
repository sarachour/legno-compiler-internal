
def LowPassFilter:

    def __init__(self,cutoff):
        self._cutoff = cutoff

def HighPassFilter:

    def __init__(self,cutoff):
        self._cutoff = cutoff

def BandPassFilter:

    def __init__(self,low_cutoff,high_cutoff):
        self._low_cutoff = low_cutoff
        self._high_cutoff = high_cutoff
