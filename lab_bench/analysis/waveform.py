
# grendel generates scripts to exercise a component.
import json
from enum import Enum
import scipy,scipy.signal
import numpy as np
import matplotlib.pyplot as plt
import itertools
import math
from scipy.ndimage.filters import gaussian_filter

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

class TimeSeries:
        def __init__(self,time,value):
            self.times = time;
            self.values = value;
            self._copy_on_write_flag = False

        def _copy_on_write(self):
            if not self._copy_on_write_flag:
                self.times = list(self.times)
                self.values = list(self.values)
                self._copy_on_write_flag = True

        def min_time(self):
            return self.times[0]

        def max_time(self):
            return self.times[-1]

        def n(self):
            return len(self.times)

        def time_delta(self):
            return np.mean(np.diff(self.times))

        def shift(self,amount):
            self._copy_on_write()
            assert(len(self.values) == len(self.times))
            self.times[:] = map(lambda x: x+amount,self.times)
            return self

        def copy(self):
            return TimeSeries(self.times,self.values)

        def pad_samples(self,n_samples,value=0):
            assert(len(self.values) == len(self.times))
            delta = self.time_delta()
            start_time = self.max_time()
            timebuf = list(map(lambda i: start_time + delta*(i+1), \
                range(0,n_samples)))
            valbuf = [value]*n_samples
            self.times = self.times + timebuf
            self.values = self.values + valbuf
            assert(len(self.values) == len(self.times))

        def pad_time(self,max_time,value=0):
            if self.max_time() == max_time:
                pass

            elif self.max_time() > max_time:
                raise Exception("cannot pad %f to %f" % \
                                (self.max_time(),max_time))
            else:
                self._copy_on_write()
                delta = self.time_delta()
                pad_time = max_time-self.max_time()
                print("pad: %s" % pad_time)
                npts = int(np.round(pad_time/delta))
                self.pad_samples(npts,value=value)

            return self

        def manip_time(self,max_time,value=0):
            if self.max_time() == max_time:
                pass

            elif self.max_time() > max_time:
                self.truncate_after(max_time)

            else:
                self.pad_time(max_time,value)

            return self

        def find_first_index(self,array,predicate):
            for idx in filter(lambda x: predicate(array[x]),
                                 range(0,len(array))):
                return idx

        def find_last_index(self,array,predicate):
            for idx in filter(lambda x: predicate(array[x]),
                                 reversed(range(0,len(array)))):
                return idx


        def truncate_before(self,min_time):
            self._copy_on_write()
            # only first instance
            index = self.find_first_index(self.times,lambda x: x>=min_time)
            self.times = self.times[index:]
            self.values = self.values[index:]

        def truncate_after(self,max_time):
            self._copy_on_write()
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

        def resample(self,npts):
            n = len(self.times)
            mod_v = 8
            if n%mod_v > 0:
                self.pad_samples(mod_v-n%mod_v,self.values[-1])
            rsvals,rstimes = scipy.signal.resample( \
                self.values,npts,t=self.times)
            return TimeSeries(rstimes,rsvals)

        @staticmethod
        def align_samples(s1,s2,npts,scf,pad_time,s1_value,s2_value):
            s1_ts = s1.copy().resample(int(npts*scf)) \
                      .manip_time(pad_time, \
                                value=s1_value) \
                      .resample(int(npts))
            s2_ts = s2.copy().resample(int(npts*scf)) \
                       .manip_time(pad_time, \
                                 value=s2_value) \
                       .resample(int(npts))
            return s1_ts,s2_ts

        def difference(self,other,npts=1e4):
            if self.max_time() != other.max_time():
                max_time = max(self.max_time(),
                               other.max_time())
                my_ts,other_ts = TimeSeries.align_samples(self,
                                                    other,
                                                    npts,
                                                    10.0,
                                                    max_time,
                                                    self.values[-1],
                                                    other.values[-1])

            else:
                my_ts = self
                other_ts = other

            vsub = list(map(lambda args: args[0]-args[1],
                            zip(my_ts.values,other_ts.values)))

            result = TimeSeries(my_ts.times,vsub)
            result.plot_series("a-b")
            my_ts.plot_series("a")
            other_ts.plot_series("b")
            plt.legend()
            plt.savefig("testdiff.png")
            plt.clf()
            return result

        def plot_series(self,label="series"):
            plt.plot(self.times,self.values,label=label)

        def fft(self,basename=None,npts=1e4):
            ts = self.resample(int(npts))
            timestep = ts.time_delta()
            vf = 2.0/ts.n()*scipy.fftpack.fft(ts.values)
            tf = np.fft.fftfreq(ts.n(), d=timestep)
            print("#phasors: %d" % len(vf))
            print("#freqs: %d" % len(tf))
            return FrequencyData(tf,vf)

class EmpiricalData:

    def __init__(self):
        self._inputs = {}
        self._output = None
        self._reference = None
        self.phase_delay = 0

    @property
    def output(self):
        return self._output

    @property
    def reference(self):
        return self._reference

    def input(self,index):
        return self._inputs[index]

    def set_output(self,time,value):
        self._output = TimeSeries(time,value)
        self._last_output_value = self._output.values[-1]

    def set_reference(self,time,value):
        self._reference = TimeSeries(time,value)

    def set_input(self,index,time,value):
        self._inputs[index] = TimeSeries(time,value)


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

    def align(self,n=1000):
        def plot_series(filename,out_ts,ref_ts):
            out_ts.plot_series()
            ref_ts.plot_series()
            plt.savefig(filename)
            plt.clf()

        def do_align(npts,trim=0):
            max_time = max(self._output.max_time(),
                           self._reference.max_time())

            pad_value = self._last_output_value
            out_ts,ref_ts = TimeSeries.align_samples(self._output,
                                          self._reference,
                                          npts,
                                          10.0,
                                          max_time*2.0,
                                          pad_value,
                                          pad_value)

            dx_out= out_ts.time_delta()
            dx_ref= ref_ts.time_delta()
            plot_series("test.png",out_ts,ref_ts)
            correlations= scipy.signal.correlate(ref_ts.values,
                                                 out_ts.values,'full')
            index = np.argmax(correlations)
            shift = (dx_out*(index-npts))
            print("shift: %s" % shift)
            out_ts.shift(shift)
            plot_series("test2.png",out_ts,ref_ts)
            return dx_out,shift

        delta_x,shift = do_align(n)
        self.phase_delay += shift
        self.output.shift(shift)
        self.output.truncate_before(0)
        self.output.truncate_after(self.reference.max_time())

    def trim(self,amt):
        self.output.trim(amt)
        self.reference.trim(amt)

class EmpiricalDatumType(Enum):
    INPUT = "input"
    REFERENCE = "reference"
    OUTPUT = "output"
