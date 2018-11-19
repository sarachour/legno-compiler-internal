
# grendel generates scripts to exercise a component.
import json
from enum import Enum
import scipy,scipy.signal
import numpy as np
import matplotlib.pyplot as plt
import itertools
import math

class FrequencyData:

    def __init__(self,freqs,phasors,cutoff=1e-8):
        assert(len(freqs) == len(phasors))
        self._freqs = freqs
        self._phasors = phasors
        selector = [np.absolute(x) > cutoff for x in phasors]
        self._freqs = list(itertools.compress(freqs, selector))
        self._phasors = list(itertools.compress(phasors,selector))

    def write(self,filename):
        data = {'freqs':list(self._freqs),
                'ampl':list(np.real(self._phasors)),
                'phase':list(np.imag(self._phasors))}
        with open(filename,'w') as fh:
            fh.write(json.dumps(data))

    def plot(self,basename):
        def stem_plot(filename,axname,x,y,do_log=False):
            fig, ax = plt.subplots()
            if len(x) > 0:
                ax.stem(x,y,markerfmt=' ')
                if do_log:
                    ax.set_yscale('log')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('%s (log(dB))' % axname)
            fig.savefig(filename)

        stem_plot("%s_ampl.png" % basename,"Amplitude",
                  self._freqs,np.real(self._phasors))
        stem_plot("%s_phase.png" % basename,"Phase",
                  self._freqs,np.imag(self._phasors))

        plt.clf()

class EmpiricalData:
    class TimeSeries:
        def __init__(self,time,value):
            self.times = time;
            self.values = value;

        def shift(self,amount):
            assert(len(self.values) == len(self.times))
            self.times = np.add(self.times,amount)

        def find_first_index(self,array,predicate):
            for idx in filter(lambda x: predicate(array[x]),
                                 range(0,len(array))):
                return idx

        def find_last_index(self,array,predicate):
            for idx in filter(lambda x: predicate(array[x]),
                                 reversed(range(0,len(array)))):
                return idx


        def truncate_before(self,min_time):
            # only first instance
            index = self.find_first_index(self.times,lambda x: x>=min_time)
            self.times = self.times[index:]
            self.values = self.values[index:]

        def truncate_after(self,max_time):
            index = self.find_last_index(self.times,lambda x: x<=max_time)
            self.times = self.times[:index+1]
            self.values = self.values[:index+1]

        def trim(self,time):
            assert(len(self.values) == len(self.times))
            min_time,max_time = self.times[0]+time,self.times[-1]-time
            if min_time >= max_time:
                return

            self.truncate_before(min_time)
            self.truncate_after(max_time)
            self.shift(-min_time)
            assert(len(self.values) == len(self.times))
            print("trim: %s" % len(self.values))

        def resample(self,npts):
            times = self.times
            rsvals,rstimes = scipy.signal.resample(
                self.values,npts,
                t=times)
            return rstimes,rsvals

        def difference(self,other,npts=1e4):
            t1,v1 = self.resample(int(npts))
            t2,v2 = other.resample(int(npts))
            vsub = list(map(lambda args: args[0]-args[1],
                            zip(v1,v2)))
            return EmpiricalData.TimeSeries(t1,vsub)

        def plot_series(self):
            print("# times: %d" % len(self.times))
            print("# values: %d" % len(self.values))
            plt.plot(self.times,self.values)

        def fft(self,basename=None,npts=1e4):
            t,x = self.resample(int(npts))
            timestep = np.mean(np.diff(t))
            N = len(t)
            vf = 2.0/N*scipy.fftpack.fft(x)
            tf = np.fft.fftfreq(N, d=timestep)
            print("#phasors: %d" % len(vf))
            print("#freqs: %d" % len(tf))
            return FrequencyData(tf,vf)


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


    def plot(self,figname):
        self._output.plot_series()
        self._reference.plot_series()
        plt.savefig(figname)
        plt.clf()

    @staticmethod
    def from_json(data):
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

    @staticmethod
    def read(filename):
        data = None
        with open(filename,'r') as fh:
            data = json.loads(fh.read())

        return EmpiricalData.from_json(data)

    def align(self,npts=5000):
        def mse(targ,fn,offset):
            def get_shifted(array,idx):
                if idx < offset:
                    return targ[idx]
                else:
                    return array[idx-offset]

            error = sum(map(lambda idx : (get_shifted(fn,idx)-targ[idx])**2,\
                        range(0,len(targ))))

            error += sum(map(lambda idx: get_shifted(fn,idx)**2, \
                         range(len(targ),len(targ)+offset)))
            rnd_error = float('{:0.5e}'.format(error))
            npts = len(fn)-offset
            return rnd_error/npts

        time1,samp1= self._output.resample(npts)
        time2,samp2= self._reference.resample(npts)
        min_error = None
        best_offset = None
        for offset in range(0,npts):
            error = mse(samp1,samp2,offset)
            if min_error is None or error < min_error:
                min_error = error
                best_offset = offset

        print("best offset: %s" % best_offset)
        delta_x= np.mean(np.diff(time1))
        shift = best_offset*delta_x
        # save the phase delay from the empirical data
        self.phase_delay = shift
        # clip the output signal to only keep the part over the
        # reference signal
        self.output.shift(-1*shift)
        self.output.truncate_after(self.reference.times[-1])
        self.output.truncate_before(0)

class EmpiricalDatumType(Enum):
    INPUT = "input"
    REFERENCE = "reference"
    OUTPUT = "output"
