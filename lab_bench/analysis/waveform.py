
# grendel generates scripts to exercise a component.
import json
from enum import Enum
import scipy,scipy.signal
import numpy as np
import matplotlib.pyplot as plt
import itertools
import math
from scipy.ndimage.filters import gaussian_filter
import lab_bench.analysis.freq as fq
import pandas
import fractions

class TimeSeries:
        def __init__(self,time,value):
            self._times = time;
            self._values = value;
            self._start_index = 0;
            self._end_index = len(time)-1
            self._time_shift = 0.0;
            self._value_shift = 0.0;
            self._copy_on_write_flag = False

        def to_json(self):
            self._compute()
            return {
                    'times': self._times,
                    'values': self._values
            }

        @staticmethod
        def from_json(data):
            return TimeSeries(data['times'],data['values'])
        def _is_standard(self):
            return not (self._start_index > 0 or \
                        self._end_index < len(self._times) - 1 or \
                        self._time_shift != 0.0 or \
                        self._value_shift != 0.0)

        # compute array if we're currently using a transform over the array
        def _compute(self):
            if not self._is_standard():
                assert(len(self._times) == len(self._values))
                times = list(self.times)
                values = list(self.values)
                assert(len(self._times) == len(self._values))
                self._times = times
                self._values = values
                self._start_index = 0
                self._end_index = len(self._times) - 1
                self._time_shift = 0.0
                self._value_shift = 0.0
                return True

            else:
                return False

        # force copying array, computing is necessary.
        # otherwise
        def _copy_on_write(self):
            if self._compute():
                self._copy_on_write_flag = True

            if not self._copy_on_write_flag:
                self._times = list(self._times)
                self._values = list(self._values)
                self._copy_on_write_flag = True


        @property
        def values(self):
            assert(len(self._times) == len(self._values))
            if self._is_standard():
                return self._values

            si,ei = self._start_index,self._end_index
            value_shift = self._value_shift
            return map(lambda v: v + value_shift,
                       self._values[si:ei+1])

        @property
        def times(self):
            assert(len(self._times) == len(self._values))
            if self._is_standard():
                return self._times

            si,ei = self._start_index,self._end_index
            time_shift = self._time_shift
            return map(lambda v: v + time_shift,
                       self._times[si:ei+1])

        def power(self):
            return sum(map(lambda q : q**2, self.values))

        def min_time(self):
            si = self._start_index
            return self._times[si] + self._time_shift

        def max_time(self):
            ei = self._end_index
            return self._times[ei] + self._time_shift

        def time_range(self):
            return self.max_time() - self.min_time()

        def n(self):
            return self._end_index-self._start_index+1

        def time_delta(self):
            self._compute()
            return np.mean(np.diff(self.times))

        def ith(self,idx):
            si,ei = self._start_index,self._end_index
            if idx == -1:
                idx = ei-1

            time = self._times[idx] + self._time_shift
            value = self._values[idx] + self._value_shift
            return time,value

        def value_shift(self,amount):
            #self._copy_on_write()
            self._value_shift += amount
            #assert(len(self.values) == len(self.times))
            #self.values[:] = map(lambda x: x+amount,self.values)
            return self

        def time_shift(self,amount):
            #self._copy_on_write()
            self._time_shift += amount
            #assert(len(self.values) == len(self.times))
            #self.times[:] = map(lambda x: x+amount,self.times)
            return self

        def copy(self):
            ts = TimeSeries(self._times,self._values)
            ts._start_index = self._start_index
            ts._end_index = self._end_index
            ts._time_shift = self._time_shift
            ts._value_shift = self._value_shift
            return ts

        def reject_outliers(self, m=2):
            q1 = np.percentile(self.values, m)
            median = np.percentile(self.values, 50)
            q3 = np.percentile(self.values, 100-m)
            selector = [q1 <= v and q3 >= v for v in self.values]
            values = list(itertools.compress(self._values,selector))
            times = list(itertools.compress(self._times,selector))
            #print("n(%s,%s) rejected: %d" % (v_mean,v_std,self.n() - len(times)))
            print("m(%s,%s,%s) rejected: %d" % (q1,median,q3,self.n() - len(times)))
            return TimeSeries(list(times),list(values))

        def pad_samples(self,_n_samples,value=0):
            n_samples = int(_n_samples)
            self._copy_on_write()
            assert(self._is_standard())
            assert(len(self._values) == len(self._times))
            delta = self.time_delta()
            start_time = self.max_time()
            timebuf = list(map(lambda i: start_time + delta*i, \
                range(1,n_samples+1)))
            valbuf = [value]*n_samples
            self._times = self._times + timebuf
            self._values = self._values + valbuf
            self._end_index += n_samples

        def find_first_index(self,array,predicate,si,ei):
            for idx,el in enumerate(array[si:ei]):
                if predicate(el):
                        return idx+si

            raise Exception("cannot find first index for predicate")

        def find_first_index(self,array,predicate,si,ei):
            for idx in filter(lambda x: predicate(array[x]),
                                       range(si,ei+1)):
                return idx

            raise Exception("[first-index] cannot find last index for predicate[%d] in [%s,%s]" % (len(array),si,ei))


        def find_last_index(self,array,predicate,si,ei):
            for idx in filter(lambda x: predicate(array[x]),
                                       range(ei,si,-1)):
                return idx

            raise Exception("[last-index] cannot find last index for predicate[%d] in [%s,%s]" % (len(array),si,ei))

        def truncate_before(self,min_time):
            #self._copy_on_write()
            time_shift = self._time_shift
            ei, si =self._end_index,self._start_index
            # only first instance
            index = self.find_first_index(self._times,\
                                          lambda x: x+time_shift>=min_time,
                                          si,ei)
            self._start_index = index
            #self.times = self.times[index:]
            #self.values = self.values[index:]

        def truncate_after(self,max_time):
            #self._copy_on_write()
            time_shift = self._time_shift
            ei, si =self._end_index,self._start_index
            index = self.find_last_index(self._times,
                                         lambda x: x+time_shift<=max_time,
                                         si,ei)
            #self.times = self.times[:index+1]
            #self.values = self.values[:index+1]

        def trim(self,min_time,max_time):
            assert(len(self.values) == len(self.times))
            if min_time >= max_time:
                return

            self.truncate_before(min_time)
            self.truncate_after(max_time)
            self.time_shift(-min_time)
            return self


        def length(self):
            return self._end_index - self._start_index + 1

        def resample_fft(self,npts):
            self._copy_on_write()
            n = self.length()
            mod_v = 64
            if n%mod_v > 0:
                _,last_v = self.ith(-1)
                self.pad_samples(mod_v-n%mod_v,last_v)

            print("-> resampling [%d]" % npts)
            rsvals,rstimes = scipy.signal.resample( \
                self.values,npts,t=self.times)
            print("-> resampled [%d]" % npts)
            return TimeSeries(rstimes,rsvals)

        def resample(self,npts):
            return self.resample_fft(npts)

        @staticmethod
        def align_samples(s1,s2,npts,total_time,s1_value,s2_value):
            assert(not total_time is None)
            assert(not s1_value is None)
            targ_delta = total_time/float(npts)
            n1 = int(s1.time_range()/targ_delta)
            n2 = int(s2.time_range()/targ_delta)
            s1_ts = s1.copy().resample(n1)
            if s1_ts.n() < npts:
                   s1_ts.pad_samples(npts-s1_ts.n(),value=s1_value)
            elif s1_ts.n() > npts:
                   s1_ts._end_index -= int(s1_ts.n() - npts)

            s2_ts = s2.copy().resample(n2)
            if s2_ts.n() < npts:
                   s2_ts.pad_samples(npts-s2_ts.n(),value=s2_value)
            elif s2_ts.n() > npts:
                   s2_ts._end_index -= int(s2_ts.n() - npts)

            print(s1_ts.time_delta(), targ_delta)
            print(s2_ts.time_delta(), targ_delta)
            assert(abs(s1_ts.time_delta() - targ_delta) < targ_delta*1e-1)
            assert(abs(s2_ts.time_delta() - targ_delta) < targ_delta*1e-1)
            assert(s1_ts.n() == s2_ts.n())
            return s1_ts,s2_ts

        def difference(self,other,npts=1e4):
            if self.max_time() != other.max_time():
                max_time = min(self.max_time(),
                               other.max_time())

                _,my_last_val = self.ith(-1)
                _,other_last_val = other.ith(-1)
                my_ts,other_ts = TimeSeries.align_samples(self,
                                                    other,
                                                    npts,
                                                    max_time,
                                                    my_last_val,
                                                    other_last_val)

            else:
                my_ts = self
                other_ts = other

            vsub = map(lambda args: args[0]-args[1],
                       zip(my_ts.values,other_ts.values))

            act_max_time = min(self.max_time(),other.max_time())
            result = TimeSeries(list(my_ts.times),list(vsub))
            # trim resulting signal
            result.truncate_after(act_max_time)
            return result

        def plot_series(self,label="series"):
            plt.plot(list(self.times),list(self.values),label=label)

        def detrend(self,constant='constant'):
            Npts = self.n()
            # matrix A
            if not constant:
                A = np.ones((Npts, 2), float)
                # random coefficients
                A[:, 0] = self.times
                coef, resids, rank, s = np.linalg.lstsq(A, self.values)
                new_values = self.values - np.dot(A, coef)
                m,b = coef
                return m,b,new_values
            else:
                bias = np.mean(self.values)
                new_values = self.values - bias
                return 0,bias,new_values

        def preprocess_signal_for_fft(self,trend=False):
            dt = self.time_delta()
            n = self.n()
            # multiply signal by half-cosine
            hcos_freq = 1.0/(dt*n*2)*2*math.pi
            hcos_offset = math.pi/2.0
            if trend == 'constant' or trend == 'linear':
                    slope,bias,values = self.detrend(constant=trend)
            else:
                    slope,bias,values = 1.0,0.0,self._values

            values = list(map(lambda t: t[1]*math.cos(hcos_freq*dt*t[0]+hcos_offset),
                              enumerate(values)))
            # pad with n zeroes.
            values += [0.0]*n
            return slope,bias,range(0,2*n)*dt,values

        def fft(self,trend='constant'):
            dt = self.time_delta()
            slope,bias,values = self.detrend(constant=trend)

            phasors =scipy.fftpack.fft(values)
            freqs = np.linspace(0.0,1/(2.0*dt),self.n())
            print(len(freqs),len(phasors))
            #freqs = np.fft.rfftfreq(len(values),dt)
            print("#delta: %f" % dt)
            print("#trend: %f*t+%f" % (slope,bias))
            print("#phasors: %d" % len(phasors))
            print("#freqs: %d" % len(freqs))
            return fq.FrequencyData(freqs,phasors,bias=bias,time_scale=dt)

        @staticmethod
        def correlate(_s1,_s2,npts):
            max_time = min(_s1.max_time(),
                           _s2.max_time())

            # align samples with different sampling rate.
            s1,s2= TimeSeries.align_samples(_s1,
                                            _s2,
                                            npts/2,
                                            max_time,
                                            0.0,
                                            0.0)

            s1_dt = s1.time_delta()
            s2_dt = s2.time_delta()
            assert(abs(s2_dt - s1_dt) < min(s1_dt,s2_dt)*1e-1)
            def index_to_shift(index):
                    return (index-npts)*dx_out

            #_,_,s1_times,s1_values = s1.preprocess_signal_for_fft(trend='const')
            #_,_,s2_times,s2_values = s2.preprocess_signal_for_fft(trend='const')
            s1_times,s1_values = s1.times,s1.values
            s2_times,s2_values = s2.times,s2.values
            TimeSeries(s1_times,s1_values).plot_series()
            TimeSeries(s2_times,s2_values).plot_series()
            plt.savefig('frame.png')
            plt.cla()
            assert(len(s1_values) == len(s2_values))
            ncorr = len(s1_values)
            correlations= scipy.signal.correlate(s1_values,
                                                 s2_values,'full')
            offsets = list(map(lambda i : (i - ncorr)*s1_dt, range(0,ncorr+1)))
            return correlations,offsets

class TimeSeriesSet:

    def __init__(self,simulation_time,phase_delay=0):
        self._inputs = {}
        self._output = None
        self._reference = None
        self.phase_delay = phase_delay
        self.simulation_time = simulation_time

    @property
    def output(self):
        return self._output

    @property
    def inputs(self):
        return self._inputs

    @property
    def reference(self):
        return self._reference

    def input(self,index):
        return self._inputs[index]

    def set_output(self,time,value):
        self._output = TimeSeries(time,value)

    def set_reference(self,time,value):
        self._reference = TimeSeries(time,value)

    def set_input(self,index,time,value):
        self._inputs[index] = TimeSeries(time,value)


    def plot(self,figname,show_input=False):
        plt.clf()
        if show_input:
            for lb,inp in self._inputs.items():
                inp.plot_series("inp[%s]" % lb)
        self._output.plot_series("out")
        self._reference.plot_series("ref")
        plt.legend()
        plt.savefig(figname)
        plt.clf()

    def to_json(self):
        inputs = {}
        for idx,inp in self._inputs.items():
            inputs[idx] = inp.to_json()

        return {
                'output': self._output.to_json(),
                'reference': self._reference.to_json(),
                'inputs': inputs,
                'phase_delay': self.phase_delay,
                'simulation_time': self.simulation_time
        }

    @staticmethod
    def from_json(data):
        assert(not data is None)
        empd = TimeSeriesSet(data['simulation_time'],
                             data['phase_delay'])

        empd._output = TimeSeries.from_json(data['output'])
        empd._reference = TimeSeries.from_json(data['reference'])
        for inp,datum in data['inputs'].items():
                empd._inputs[inp] = TimeSeries.from_json(datum)

        return empd

    @staticmethod
    def read(filename):
        data = None
        with open(filename,'r') as fh:
            data = json.loads(fh.read())

        return TimeSeriesSet.from_json(data)


    def align(self,n=10000,correlation_rank=1):
        def compute_weight(phase_dist,npts,dt,index):
            shift = dt*(index-npts) + self.phase_delay
            prob = min(1.0,phase_dist.pdf(-shift))
            return prob

        def compute_timeseries_error(shift):
                out = self.output.copy()
                max_time = self._reference.max_time()
                out.time_shift(shift)
                out.truncate_before(0.0)
                out.truncate_after(max_time)
                noise = out.difference(self.reference,npts=n)
                out.plot_series()
                noise.plot_series()
                self._reference.plot_series()
                plt.savefig('frame.png')
                plt.clf()
                noise_power = noise.power()
                return noise_power

        def do_align(npts,trim=0):
            '''
            max_time = max(self._output.max_time(),
                           self._reference.max_time())

            _,pad_value = self._output.ith(-1)
            out_ts,ref_ts = TimeSeries.align_samples(self._output,
                                          self._reference,
                                          npts,
                                          max_time*2.0,
                                          pad_value,
                                          pad_value)

            dx_out= out_ts.time_delta()
            def index_to_shift(index):
                    return (index-npts)*dx_out

            correlations= scipy.signal.correlate(ref_ts.values,
                                                 out_ts.values,'full')

            '''
            correlations,offsets = TimeSeries.correlate(self._reference,self._output,npts)
            # top items
            if correlation_rank == 0:
                    print("[[ performing correlating alignment ]]")
                    index = np.argmax(correlations)
                    print("index=%d, score=%f, shift=%f" % (index,\
                                                            correlations[index], \
                                                            offsets[index]))
            else:
                    print("performing cross-checking alignment")
                    indices = np.argsort(correlations)[-correlation_rank:]
                    errors = []
                    for i,index in enumerate(indices):
                            shift = offsets[index]
                            power = compute_timeseries_error(shift)
                            print("[%s/%s] index=%d score=%f shift=%f, power=%f" % \
                                  (i+1,len(indices),index,correlations[index],shift,power))
                            errors.append(power)

                    min_idx = np.argmin(errors)
                    index = indices[min_idx]

            shift = offsets[index]
            return shift,correlations[index]


        shift,best_corr = do_align(n)
        self.phase_delay += shift
        max_time = self.reference.max_time()
        for sig in [self.output]:
            sig.time_shift(shift)
            sig.truncate_before(0)
            sig.truncate_after(max_time)


        return self.phase_delay,best_corr

    def trim(self,lo,hi):
        self.output.trim(lo,hi)
        self.reference.trim(lo,hi)
        for sig in self.inputs.values():
            sig.trim(lo,hi)

        return self
