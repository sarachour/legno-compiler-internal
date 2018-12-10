
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
import fastdtw
from scipy.spatial.distance import euclidean

class TimeXform:
        def __init__(self,offset,warp=1.0):
            self._delay = offset
            self._warp = warp

        def set_warp(self,warp):
            self._warp = warp

        @property
        def delay(self):
            return self._delay

        def to_json(self):
            return {
                    'delay':self._delay,
                    'warp': self._warp
            }

        def write(self,name):
            with open(name,'w') as fh:
                strdata = json.dumps(self.to_json())
                fh.write(strdata)

        @staticmethod
        def read(name):
            with open(name,'r') as fh:
                data = json.loads(fh.read())
                return TimeXform(data['delay'],data['warp'])

class SignalXform:

        class Segment:
             def __init__(self,l,u,a,b,error=0.0):
                self._lower_bound = l
                self._upper_bound = u
                self._alpha = a
                self._beta = b
                self._error = error

             def set_error(self,e):
                self._error = e

             @property
             def lower_bound(self):
                return self._lower_bound

             @property
             def upper_bound(self):
                return self._upper_bound

             def contains(self,x):
                lb,ub =self._lower_bound,self._upper_bound
                if lb is None:
                   return x < ub
                if ub is None:
                   return lb <= x
                else:
                   return lb <= x and ub > x


             def apply(self,x):
                return self._alpha*x+self._beta

             @staticmethod
             def from_json(data):
                seg = SignalXform.Segment(
                        l=data['lower_bound'],
                        u=data['upper_bound'],
                        a=data['alpha'],
                        b=data['beta'],
                        error=data['error']
                )
                return seg

             def to_json(self):
                return {
                        'alpha':self._alpha,
                        'beta':self._beta,
                        'error':self._error,
                        'lower_bound':self._lower_bound,
                        'upper_bound':self._upper_bound
                }

             def __repr__(self):
                return "[%s,%s] %s*x+%s {%s}" % \
                        (self._lower_bound,
                         self._upper_bound,
                         self._alpha,
                         self._beta,
                         self._error)

        def __init__(self):
            self._segments = []

        @property
        def segments(self):
            for seg in self._segments:
                yield seg

        def _non_overlapping(self,l,u):
            for seg in self._segments:
                if not l is None and \
                   seg.contains(l):
                    return False
                if not u is None and \
                   seg.contains(u):
                    return False

            return True

        def add_segment(self,lower,upper,alpha,beta):
            assert(self._non_overlapping(lower,upper))
            seg = SignalXform.Segment(lower,upper,alpha,beta)
            self._segments.append(seg)
            return seg

        def error(self,x):
            segs = list(filter(lambda seg: seg.contains(x), self._segments))
            assert(len(segs) == 1)
            return segs[0].apply(x)


        def apply(self,x):
            segs = list(filter(lambda seg: seg.contains(x), self._segments))
            assert(len(segs) == 1)
            return x+segs[0].apply(x)

        def to_json(self):
            segj = list(map(lambda seg: seg.to_json(), self._segments))
            return segj

        def write(self,name):
            with open(name,'w') as fh:
                strdata = json.dumps(self.to_json())
                fh.write(strdata)

        @staticmethod
        def read(name):
            with open(name,'r') as fh:
                data = json.loads(fh.read())
                xform = SignalXform()
                for seg_json in data:
                        seg = SignalXform.Segment\
                                         .from_json(seg_json)
                        xform._segments.append(seg)

                return xform

        def __repr__(self):
            r = ""
            for seg in self._segments:
                r += "%s\n" % seg
            return r

class TimeSeries:
        def __init__(self,time,value):
            self._times = time;
            self._values = value;
            assert(len(self._times) == len(self._values))
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

        def set_values(self,v):
            assert(len(v) == len(self._times))
            self._values = v

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

        def fill_outliers_quartile(self,m=2,window=1000):
            q1 = np.percentile(self.values, m)
            median = np.percentile(self.values, 50)
            q3 = np.percentile(self.values, 100-m)
            pars = {'rejected':0}
            def fill_value(args):
                i,v = args
                if v < q1 or v > q3:
                    pars['rejected'] += 1
                    l = max(0,i-window/2)
                    u = min(len(self._values),i+window/2)
                    med = np.random.choice(self._values[l:u])
                    return med
                else:
                    return v

            values = list(map(fill_value, enumerate(self._values)))
            print("# rejected: %d" % pars['rejected'])
            return TimeSeries(list(self.times),list(values))


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
            self._end_index = index
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
            print("-> resampling [%d]" % npts)
            rsvals,rstimes = scipy.signal.resample( \
                self.values,npts,t=self.times)
            print("-> resampled [%d]" % npts)
            return TimeSeries(rstimes,rsvals)

        def resample(self,npts):
            if npts == self.n():
                return self.copy()
            return self.resample_fft(npts)

        @staticmethod
        def synchronize_time_deltas(s1,s2,npts=None):
            npts = max(s1.n(),s2.n()) if npts is None else npts
            max_time = s1.max_time() if s1.n() > s2.n() else \
                       s2.max_time()
            print("max_time: %s,%s,%s" % (s1.max_time(),s2.max_time(),max_time))
            print("npts: %s,%s,%s" % (s1.n(),s2.n(),npts))
            targ_delta = max_time/float(npts)
            n1 = int(round(s1.time_range()/targ_delta))
            n2 = int(round(s2.time_range()/targ_delta))
            s1_ts = s1.copy().resample(n1)
            s2_ts = s2.copy().resample(n2)

            s1._check_time_delta(targ_delta)
            s2._check_time_delta(targ_delta)
            return s1_ts,s2_ts

        def _check_time_delta(self,targ):
            thresh=1e-1
            return abs(self.time_delta() - targ < targ*thresh)

        def difference(self,other):
            assert(self._check_time_delta(other.time_delta()))
            values = list(map(lambda args: args[0]-args[1],
                              zip(self.values,other.values)))

            times = list(self.times) \
                    if self.n() < other.n() \
                    else list(other.times)
            result = TimeSeries(list(times),list(values))
            return result

        def plot_series(self,label="series"):
            plt.plot(list(self.times),list(self.values),label=label)

        def detrend(self,trend='constant'):
            Npts = self.n()
            # matrix A
            if  trend == 'linear':
                A = np.ones((Npts, 2), float)
                # random coefficients
                A[:, 0] = self.times
                coef, resids, rank, s = np.linalg.lstsq(A, self.values)
                new_values = self.values - np.dot(A, coef)
                m,b = coef
                return m,b,new_values
            elif trend == 'constant':
                bias = np.mean(self.values)
                new_values = self.values - bias
                return 1.0,bias,new_values
            else:
                return 1.0,0.0,self.values

        def apply_signal_xform(self,xform):
            self._values = list(map(xform.apply, self._values))

        def find_nonlinearity(self,targ_ts,m=None):
            assert(self._check_time_delta(targ_ts.time_delta()))
            n = min(self.n(),targ_ts.n())
            v1 = self.values[:n]
            v2 = targ_ts.values[:n]
            if not m is None:
                # outlier detect big errors
                error = list(map(lambda q : q[1] - q[0], zip(v2,v1)))
                q1 = np.percentile(error, m)
                median = np.percentile(error, 50)
                q3 = np.percentile(error, 100-m)
                selector = [q1 <= v and q3 >= v for v in error]
                v1 = list(itertools.compress(v1,selector))
                v2 = list(itertools.compress(v2,selector))


            parnames = SignalXform.param_names()
            init = np.random.uniform(size=len(parnames))
            pars,pcov = scipy.optimize.curve_fit(SignalXform.compute, \
                                                 v1,v2,p0=init)
            for name,value in (zip(parnames,pars)):
                print("%s=%s" % (name,value))
            perr = np.sqrt(np.diag(pcov))
            raise Exception("[FIXME] this is outdated. please debug.")
            return SignalXform(dict(zip(parnames,pars)))

        def find_time_warp(self,targ_ts):
            ds1 = list(zip(self.times,self.values))
            ds2 = list(zip(self.times,self.values))
            distance,path = fastdtw.fastdtw(ds1,ds2,dist=euclidean)
            print(path)
            print(distance)
            raise Exception("[FIXME] this is outdated. please debug.")

        def preprocess_signal_for_fft(self,trend=None,window=None,pad=True):
            dt = self.time_delta()
            values = self.values
            n = self.n()
            if not window is None:
                    values = window.apply(values,dt)
            else:
                    values = list(values)
            # pad with n zeroes.
            slope,bias,values = self.detrend(trend=trend)

            if pad:
                times = np.linspace(0.0,dt*n*2,n*2)
                pad = [0.0]*n
                values = list(values) + pad
                assert(len(values) == len(times))
            else:
                times = np.linspace(0.0,dt*n,n)

            return slope,bias,n,times,values

        def fft(self,window=None,trend='constant',autopower=True):
            dt = self.time_delta()
            slope,bias,padding,times,values = \
                self.preprocess_signal_for_fft(trend,window)
            phasors =scipy.fftpack.fft(values)
            freqs = scipy.fftpack.fftfreq(len(times), d=dt)
            n = len(freqs) - padding
            reg_phasors = math.sqrt(1.0/n)*phasors

            print("freqs: [%s,%s]" % (min(freqs),max(freqs)))
            print("#delta: %f" % dt)
            print("#phasors: %d" % len(phasors))
            print("#freqs: %d" % len(freqs))
            print("bias: %s" % bias)
            return fq.FrequencyData(freqs,reg_phasors,\
                                    time_scale=dt, \
                                    num_samples=n, \
                                    bias=bias, \
                                    padding=padding,window=window)

        @staticmethod
        def correlate(s1,s2,window=None):
            max_time = min(s1.max_time(),
                           s2.max_time())
            assert(s1._check_time_delta(s2.time_delta()))

            def index_to_shift(index):
                    return (index-npts)*dx_out

            _,_,_,s1_times,s1_values = \
                s1.preprocess_signal_for_fft(\
                                             window=window,
                                             trend='const',
                                             pad=False)
            _,_,_,s2_times,s2_values = \
                s2.preprocess_signal_for_fft(\
                                             window=window,
                                             trend='const',
                                             pad=False)
            TimeSeries(s1.times,s1.values).plot_series()
            TimeSeries(s2.times,s2.values).plot_series()
            plt.savefig('frame_o.png')
            plt.cla()

            s1_dt = TimeSeries(s1_times,s1_values).time_delta()
            print(len(s2_values),len(s1_values))
            n = len(s2_values)
            correlations= scipy.signal.correlate(s1_values,
                                                 s2_values,'full')
            print(len(s1_values),len(s2_values),len(correlations))
            offsets = list(map(lambda i : (i - n)*s1_dt,\
                               range(0,len(correlations))))

            TimeSeries(s1_times,s1_values).plot_series()
            TimeSeries(s2_times,s2_values).plot_series()
            plt.savefig('frame.png')
            plt.cla()
            plt.plot(offsets,correlations)
            plt.savefig('corr.png')
            plt.cla()
            return correlations,offsets

class TimeSeriesSet:

    def __init__(self,simulation_time,phase_delay=0):
        self._inputs = {}
        self._output = None
        self._noise = None
        self._reference = None
        self.phase_delay = phase_delay
        self.simulation_time = simulation_time

    @property
    def noise(self):
        return self._noise

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

    def set_noise(self,time,value):
        self._noise = TimeSeries(time,value)

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
        if not self._output is None:
                self._output.plot_series("out")
        if not self._reference is None:
                self._reference.plot_series("ref")
        if not self._noise is None:
                self._noise.plot_series('noise')
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


    def align(self,window=None,correlation_rank=1):
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
                noise = out.difference(self.reference)
                out.plot_series()
                noise.plot_series()
                self._reference.plot_series()
                plt.savefig('frame.png')
                plt.clf()
                noise_power = noise.power()
                return noise_power


        correlations,offsets = TimeSeries.correlate(self._reference,\
                                                    self._output, \
                                                    window)
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
                                (i+1,len(indices),index,correlations[index],\
                                 shift, \
                                 power))
                        errors.append(power)

                min_idx = np.argmin(errors)
                index = indices[min_idx]

        shift = offsets[index]

        self.phase_delay += shift
        max_time = self.reference.max_time()
        for sig in [self.output]:
            sig.time_shift(shift)
            sig.truncate_before(0)
            sig.truncate_after(max_time)


        return TimeXform(self.phase_delay)

    def trim(self,lo,hi):
        self.output.trim(lo,hi)
        self.reference.trim(lo,hi)
        for sig in self.inputs.values():
            sig.trim(lo,hi)

        return self
