

class Experiment:

    def __init__(self,time_su):
        self.simulation_time = time_su

class TimeSeriesExperiment(Experiment):

    def __init__(self,time_su):
        Experiment.__init__(self,time_su)


class ParameterSweepExperiment(Experiment):

    def __init__(self,time_su,npts):
        Experiment.__init__(self,time_su)
        self._params = {}
        self._npts = npts

    def sweep(self,label,minimum,maximum):
        self._params[label] = (minimum,maximum)

    def values(self,label):
        minimum,maximum = self._params[label]
        scale = maximum-minimum
        offset = minimum
        step = float(maximum-minimum)/self._npts
        values = map(lambda idx: float(idx)/self._npts*scale + offset,
            range(0,self._npts+1))
        return values
