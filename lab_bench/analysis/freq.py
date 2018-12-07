import json
import numpy as np
import matplotlib.pyplot as plt
import itertools
import scipy

class Phasor:
    def __init__(self,ampl,phase):
        self._ampl = ampl
        self._phase = phase


def db(ampl):
    return 20 * log10(ampl)

def db_to_ampl(db):
    return 10.0**(db/20.0)

def nearest_index(x,v):
    index = (np.abs(x-v)).argmin()
    return index

class FrequencyData:

    def __init__(self,freqs,phasors,bias=0.0,time_scale=1.0):
        assert(len(freqs) == len(phasors))
        # real function, so symmetric about frequency
        #selector = [f >= 0 \
        #            for f,x in zip(freqs,phasors)]
        selector = [True for f,x in zip(freqs,phasors)]
        self._time_scale = time_scale
        self._n_samples = len(freqs)
        self._bias = bias
        self._freqs = list(itertools.compress(freqs, selector))
        self._phasors = list(itertools.compress(phasors,selector))
        self.cutoff(-200)

    def num_samples(self):
        return self._n_samples

    def cutoff(self,db=-40):
        cutoff_ampl = db_to_ampl(db)
        selector = [abs(np.real(x)) >= cutoff_ampl \
                    for f,x in zip(self._freqs,self._phasors)]

        self._freqs = list(itertools.compress(self._freqs, selector))
        self._phasors = list(itertools.compress(self._phasors,selector))

    def apply_filter(self,fmin,fmax):
        selector = [(f >= fmin and f <= fmax) or f == 0.0 for f in self._freqs]
        self._freqs = list(itertools.compress(self._freqs,selector))
        self._phasors = list(itertools.compress(self._phasors,selector))

    @staticmethod
    def from_phase_ampl(freqs,phase,ampl):
        return FrequencyData(freqs,map(lambda tup: complex(tup[0],tup[1]), zip(ampl,phase)))

    @property
    def fmax(self):
        return max(self._freqs)

    @property
    def fmin(self):
        return min(self._freqs)

    def freqs(self):
        return self._freqs

    def power(self):
        freq_power = self._bias**2
        freq_power += sum(map(lambda q : abs(q**2), self._phasors))
        return freq_power/self.num_samples()

    def amplitudes(self):
        return map(lambda x: x.real, self._phasors)

    def phases(self):
        return map(lambda x: x.imag, self._phasors)

    def phasors(self):
        for freq,ph in zip(self._freqs,self._phasors):
            yield freq,ph.real,ph.imag

    def inv_fft(self):
        import lab_bench.analysis.waveform as wf
        dt = self._time_scale
        freqs = np.linspace(0.0,1/(2.0*dt),self.num_samples())
        times = np.linspace(0.0, dt,self.num_samples())
        phasors = [complex(0.0)]*self.num_samples()
        print("-> build frequency buffer [%d]" % self.num_samples())
        # y(j) = (x * exp(2*pi*sqrt(-1)*j*np.arange(n)/n)).mean()
        for freq,ampl,phase in self.phasors():
            index = abs(freqs-freq).argmin()
            phasors[index] += complex(ampl,phase)

        values = scipy.fftpack.ifft(phasors)
        return wf.TimeSeries(times,np.real(values))

    @staticmethod
    def from_json(data):
        freqs = data['freqs']
        phasors = list(map(lambda d: complex(d[0],d[1]),\
                           zip(data['ampl'],data['phase'])))
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
                'phase':list(np.imag(self._phasors)),
                'bias':self._bias,
                'time_scale':self._time_scale}

    def write(self,filename):
        with open(filename,'w') as fh:
            fh.write(json.dumps(self.to_json()))

    def plot_figure(self,plot_ampl,n=20000,do_log_x=False,do_log_y=False):
        def stem_plot(axname,x,y,n=1000,do_log_x=False,do_log_y=False):
            fig, ax = plt.subplots()
            min_x,max_x = min(x),max(x)
            if len(x) < n:
                x_new = x
                y_new = y
            else:
                xsel = np.random.uniform(min_x,max_x,size=int(n))
                indices = list(map(lambda value: nearest_index(x,value),xsel))
                x_new = list(map(lambda idx: x[idx], indices))
                y_new = list(map(lambda idx: y[idx], indices))
                assert(len(x_new) == n)
                assert(len(y_new) == n)

            if len(x) > 0:
                ax.stem(x_new,y_new,markerfmt=' ')
                if do_log_y:
                    ax.set_yscale('symlog')
                    ax.set_ylabel('%s (log(value))' % axname)
                else:
                    ax.set_ylabel('%s (value)' % axname)

                if do_log_x:
                    ax.set_xscale('log')
                    ax.set_xlabel('Frequency (log(Hz))')
                else:
                    ax.set_xlabel('Frequency (Hz)')

            return fig,ax


        if plot_ampl:
            pl = stem_plot("Amplitude",
                            self._freqs,np.real(self._phasors),n,do_log_x,do_log_y)
        else:
            pl = stem_plot("Phase",
                            self._freqs,np.imag(self._phasors),n,do_log_x,do_log_y)

        return pl

    def plot(self,amplfile,phasefile,n=20000,do_log_x=False,do_log_y=False):
        if not amplfile is None:
            (afig,aax) = self.plot_figure(True,n,do_log_x,do_log_y)
            afig.savefig(amplfile)
            plt.close(afig)
            plt.clf()
            plt.cla()
        if not phasefile is None:
            (pfig,pax) = self.plot_figure(False,n,do_log_x,do_log_y)
            pfig.savefig(phasefile)
            plt.close(pfig)
            plt.clf()
            plt.cla()

class FreqDataset:
    def __init__(self,delay):
        self._delay = delay
        self.signals = {}

    def noise(self,name=""):
        return self.signals['nz(%s)' % name]

    def output(self,name=""):
        return self.signals['out(%s)' % name]

    def input(self,name=""):
        return self.signals["in(%s)" % name]

    def add_signal(self,key,data):
        assert(not data is None)
        assert(not key in self.signals)
        self.signals[str(key)] = data

    def add_input(self,signame="",data=None):
        key = "in(%s)" % signame
        self.add_signal(key,data)


    def add_output(self,signame="",data=None):
        key = "out(%s)" % signame
        self.add_signal(key,data)

    def add_noise(self,signame="",data=None):
        key = "nz(%s)" % signame
        self.add_signal(key,data)

    def apply_filter(self,fmin,fmax):
        for sig in self.signals.values():
            sig.apply_filter(fmin,fmax)

    def fmax(self):
        fmax= None
        for datum in self.signals.values():
            if fmax is None:
                fmax = datum.fmax
            fmax = max(fmax,datum.fmax)

        return fmax

    def fmin(self):
        fmin= None
        for datum in self.signals.values():
            if fmin is None:
                fmin = datum.fmin
            fmin = min(fmin,datum.fmin)

        return fmin


    @property
    def confidence(self):
        return self._confidence

    @property
    def delay(self):
        return self._delay

    @staticmethod
    def from_aligned_time_dataset(delay,dataset,n=10000,percent_outliers_reject=2.0):
        ds = FreqDataset(delay)
        noise = dataset.output\
                       .difference(dataset.reference,n)\
                       .reject_outliers(m=percent_outliers_reject)
        ds.add_noise(data=noise.fft())

        ds.add_output(data=dataset.reference.resample(n).fft())
        for index,inp in dataset.inputs.items():
            ds.add_input(index, data=inp.resample(n).fft())

        return noise,ds

    @staticmethod
    def from_json(data):
        ds = FreqDataset(float(data['delay']))
        for key,inp in data['signals'].items():
            datum = data['signals'][key]
            ds.signals[key] = FrequencyData.from_json(datum)

        return ds

    def read(filename):
        with open(filename,'r') as fh:
            return FreqDataset.from_json(json.loads(fh.read()))


    def to_json(self):
        signals= dict(map(lambda args : (args[0],args[1].to_json()),
                          self.signals.items()))
        return {
            'signals': signals,
            'delay': self._delay,
        }

    def write(self,filename):
        with open(filename,'w') as fh:
            data = self.to_json()
            fh.write(json.dumps(data))
