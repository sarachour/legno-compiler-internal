
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

    def __init__(self,freqs,phasors,cutoff=1e-8,power=False):
        assert(len(freqs) == len(phasors))
        # real function, so symmetric about frequency
        selector = [np.absolute(x) > cutoff and f >= 0 \
                    for f,x in zip(freqs,phasors)]
        self._freqs = list(itertools.compress(freqs, selector))
        if power:
            self._phasors = list(itertools.compress(
                map(lambda num: complex(abs(num.real),num.imag),phasors)
                    ,selector))
        else:
            self._phasors = list(itertools.compress(phasors,selector))

    @property
    def fmax(self):
        return max(self._freqs)

    @property
    def fmin(self):
        return min(self._freqs)

    def freqs(self):
        return self._freqs

    def amplitudes(self):
        return map(lambda x: x.real, self._phasors)

    def phases(self):
        return map(lambda x: x.imag, self._phasors)

    def phasors(self):
        for freq,ph in zip(self._freqs,self._phasors):
            yield freq,ph.real,ph.imag

    @staticmethod
    def from_json(data):
        freqs = data['freqs']
        phasors = list(map(lambda d: complex(d[0],d[1]),zip(data['ampl'],data['phase'])))
        return FrequencyData(freqs,phasors)

    def between(self,fmin,fmax):
        selector = [x >= fmin and x <= fmax \
                    for x in self._freqs]
        freqs = list(itertools.compress(self._freqs,selector))
        phasors = list(itertools.compress(self._phasors,selector))
        return freqs,phasors

    def average(self,fmin,fmax):
        freqs,phasors = self.between(fmin,fmax)
        if len(freqs) == 0:
            return 0,0

        ampl = sum(map(lambda phasor: phasor.real,phasors))/len(freqs)
        phase = sum(map(lambda phasor: phasor.imag,phasors))/len(freqs)
        return ampl,phase


    def bounds(self,fmin,fmax):
        freqs,phasors = self.between(fmin,fmax)
        if len(freqs) == 0:
            return (0,0),(0,0)

        ampls = list(map(lambda phasor: phasor.real,phasors))
        phases = list(map(lambda phasor: phasor.imag,phasors))
        ampl_b = min(ampls),max(ampls)
        phase_b = min(phases),max(phases)
        return ampl_b,phase_b


    def to_json(self):
        return {'freqs':list(self._freqs),
                'ampl':list(np.real(self._phasors)),
                'phase':list(np.imag(self._phasors))}

    def write(self,filename):
        with open(filename,'w') as fh:
            fh.write(json.dumps(self.to_json()))

    def plot(self,amplfile,phasefile):
        def stem_plot(filename,axname,x,y,do_log=False):
            fig, ax = plt.subplots()
            if len(x) > 0:
                ax.stem(x,y,markerfmt=' ')
                if do_log:
                    ax.set_yscale('log')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('%s (log(dB))' % axname)
            fig.savefig(filename)

        stem_plot(amplfile,"Amplitude",
                  self._freqs,np.real(self._phasors))
        stem_plot(phasefile,"Phase",
                  self._freqs,np.imag(self._phasors))

        plt.clf()

class FreqDataset:
    def __init__(self,delay,confidence):
        self._delay = delay
        self._confidence = confidence
        self.inputs = {}
        self.output = None
        self.noise = None



    def fmax(self):
        fmax= None
        for datum in [self.output,self.noise]\
            +list(self.inputs.values()):
            if fmax is None:
                fmax = datum.fmax
            fmax = max(fmax,self.output.fmax)

        return fmax



    def fmin(self):
        fmin = None
        for datum in [self.output,self.noise]\
            +list(self.inputs.values()):
            if fmin is None:
                fmin = datum.fmin
            fmin = min(fmin,self.output.fmin)

        return fmin

    @property
    def confidence(self):
        return self._confidence

    @property
    def delay(self):
        return self._delay

    @staticmethod
    def from_aligned_time_dataset(delay,confidence,dataset,trim=1e-4):
        print("delay:%s, confidence:%s" % (delay,confidence))
        ds = FreqDataset(delay,confidence)
        ds.noise = dataset.output\
                          .difference(dataset.reference)\
                          .trim(trim).fft()
        ds.output = dataset.reference.trim(trim).fft()
        for index,inp in dataset.inputs.items():
            inp_fft = inp.trim(trim).fft()
            ds.inputs[index] = inp_fft

        return ds

    @staticmethod
    def from_json(data):
        ds = FreqDataset(float(data['align']['delay']), \
                         float(data['align']['confidence'])
        )
        ds.output = FrequencyData.from_json(data['output'])
        ds.noise = FrequencyData.from_json(data['noise'])
        for index,inp in data['inputs'].items():
            ds.inputs[int(index)] = FrequencyData.from_json(data['inputs'][index])

        return ds

    def read(filename):
        with open(filename,'r') as fh:
            return FreqDataset.from_json(json.loads(fh.read()))


    def to_json(self):
        inputs = dict(map(lambda args : (args[0],args[1].to_json()),
                          self.inputs.items()))
        return {
            'output': self.output.to_json(),
            'noise': self.noise.to_json(),
            'inputs': inputs,
            'align': {
                'delay': self._delay,
                'confidence':self._confidence
            }
        }

    def write(self,filename):
        with open(filename,'w') as fh:
            data = self.to_json()
            fh.write(json.dumps(data))

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
            return self

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
            return result

        def plot_series(self,label="series"):
            plt.plot(self.times,self.values,label=label)

        def fft(self,basename=None,npts=1e4):
            ts = self.resample(int(npts))
            timestep = ts.time_delta()
            vf = 2.0/ts.n()*scipy.fftpack.fft(ts.values)
            tf = np.fft.fftfreq(ts.n(), d=timestep)
            #print("#phasors: %d" % len(vf))
            #print("#freqs: %d" % len(tf))
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
    def inputs(self):
        return self._inputs


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
            correlations= scipy.signal.correlate(ref_ts.values,
                                                 out_ts.values,'full')
            index = np.argmax(correlations)
            shift = (dx_out*(index-npts))
            out_ts.shift(shift)
            return dx_out,shift,correlations[index]

        delta_x,shift,best_corr = do_align(n)
        self.phase_delay += shift
        max_time = self.reference.max_time()
        for sig in [self.output]:
            sig.shift(shift)
            sig.truncate_before(0)
            sig.truncate_after(max_time)
        return self.phase_delay,best_corr

    def trim(self,amt):
        self.output.trim(amt)
        self.reference.trim(amt)
        for sig in self.inputs.values():
            sig.trim(amt)

        return self

class EmpiricalDatumType(Enum):
    INPUT = "input"
    REFERENCE = "reference"
    OUTPUT = "output"
