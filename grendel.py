
# grendel generates scripts to exercise a component.
import json
from enum import Enum
import scipy,scipy.signal
import numpy as np
import matplotlib.pyplot as plt

class EmpiricalData:
    class TimeSeries:
        def __init__(self,time,value):
            self.times = time;
            self.values = value;

        def shift_left(self,amount):
            self.times = list(filter(
                lambda t: t >= 0,
                map(lambda t: t-amount,
                    self.times)))
            offset = len(self.values) - len(self.times)
            self.values = self.values[offset:]

        def truncate_after(self,max_time):
            self.times = list(filter(
                lambda t: t <= max_time, self.times))
            offset = len(self.values) - len(self.times)
            self.values = self.values[:-offset]


        def resample(self,npts):
            times = self.times

            rsvals,rstimes = scipy.signal.resample(
                self.values,npts,
                t=times)
            return rstimes,rsvals

        def difference(self,other,npts=100000):
            t1,v1 = self.resample(npts)
            t2,v2 = other.resample(npts)
            vsub = list(map(lambda args: args[0]-args[1],
                            zip(v1,v2)))
            return EmpiricalData.TimeSeries(t1,vsub)

        def plot(self):
            plt.plot(self.times,self.values)

    def __init__(self):
        self._inputs = {}
        self._output = None
        self._reference = None

    @property
    def output(self):
        return self._output

    @property
    def reference(self):
        return self._reference

    def input(self,index):
        return self._inputs[index]

    def set_output(self,time,value):
        self._output = EmpiricalData.TimeSeries(time,value)

    def set_reference(self,time,value):
        self._reference = EmpiricalData.TimeSeries(time,value)

    def set_input(self,index,time,value):
        self._inputs[index] = EmpiricalData.TimeSeries(time,value)


    def plot(self):
        self._output.plot()
        self._reference.plot()
        plt.savefig('processed.png')
        plt.clf()

    def align(self,npts=1000):
        def mse(x,y,offset):
            error = sum(map(lambda val: val**2, x[:offset]))
            if offset == 0:
                error += sum(map(lambda args: (args[0]-args[1])**2,
                                 zip(x,y)))

            else:
                error += sum(map(lambda args: (args[0]-args[1])**2,
                                 zip(x[offset:],y[:-offset])))
            return error

        npts = 1000
        time1,samp1= self._output.resample(npts)
        time2,samp2= self._reference.resample(npts)
        min_error = None
        best_offset = None
        for offset in range(0,npts):
            error = mse(samp1,samp2,offset)
            if min_error is None or error < min_error:
                min_error = error
                best_offset = offset

        delta_x= np.mean(np.diff(time1))
        shift = best_offset*delta_x
        # save the phase delay from the empirical data
        self.phase_delay = shift
        # clip the output signal to only keep the part over the
        # reference signal
        self.output.shift_left(shift)
        max_time = max(self.reference.times)
        self.output.truncate_after(max_time)

class EmpiricalDatumType(Enum):
    INPUT = "input"
    REFERENCE = "reference"
    OUTPUT = "output"

def read(filename):
    data = None
    with open(filename,'r') as fh:
        data = json.loads(fh.read())
    
    assert(not data is None)
    empd = EmpiricalData()
    for key,datum in data.items():
        typ = EmpiricalDatumType(datum['type'])
        if typ == EmpiricalDatumType.INPUT:
            empd.set_input(datum['index'],datum['time'],datum['value'])
        elif typ == EmpiricalDatumType.OUTPUT:
            empd.set_output(datum['time'],datum['value'])
        elif typ == EmpiricalDatumType.REFERENCE:
            empd.set_reference(datum['time'],datum['value'])

    return empd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=int,help="number of inputs.")
    parser.add_argument("--block",type=str,help="block to exercise")
    parser.add_argument("--chip", type=int,help="chip number.")
    parser.add_argument("--tile", type=int,help="tile number.")
    parser.add_argument("--slice", type=int,help="slice number.")
    parser.add_argument("--index", type=int,help="index number.")

    args = parser.parse_args()


empdata=read('lab_bench/data.json')
print("=== Align Signals ===")
empdata.align()
empdata.plot()

print("=== Generate Noise ===")
noise = empdata.output.difference(empdata.reference)
noise.plot()
plt.savefig('noise.png')
plt.clf()
