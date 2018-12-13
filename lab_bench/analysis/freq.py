import json
import numpy as np
import matplotlib.pyplot as plt
import itertools
import scipy
import math
import lab_bench.analysis.det_xform as dx
import matplotlib.collections as mcoll

class Phasor:
    def __init__(self,ampl,phase):
        self._ampl = ampl
        self._phase = phase


class Window:

    def __init__(self,name):
        self._name = name

    def name(self):
        return self._name

    def func(self,n,N):
        raise Exception("override me")

    def apply(self,values,dt):
        n = len(values)
        new_values = list(map(lambda t: t[1]*self.func(t[0],n),
                              enumerate(values)))
        assert(len(new_values) == len(values))
        return new_values

    def unapply(self,values,dt):
        def div(ampl,coeff):
            return ampl if coeff <= 1e-10 else ampl/coeff

        n = len(values)
        new_values = list(map(lambda t: div(t[1],self.func(t[0],n)),
                              enumerate(values)))
        assert(len(new_values) == len(values))
        return new_values

    def to_json(self):
        return {
            'name':self.name(),
            'params':{}
        }

class HannWindow(Window):

    def __init__(self):
        Window.__init__(self,HannWindow.name())
        pass

    @staticmethod
    def name():
        return 'hann'

    def to_json(self):
        data = Window.to_json(self)
        return data

    def func(self,n,N):
        return 0.5*(1.0-math.cos(2*math.pi*float(n)/N))

class PlanckTukeyWindow(Window):

    def __init__(self,alpha):
        Window.__init__(self,PlanckTukeyWindow.name())
        self._alpha = alpha
        pass

    def to_json(self):
        data = Window.to_json(self)
        data['params']['alpha'] = self._alpha
        return data

    @staticmethod
    def name():
        return "planck-tukey"

    def func(self,n,N):
        alpha = self._alpha
        lb = alpha*(N-1)/2.0
        ub = (1-alpha/2.0)*(N-1)
        if 0 <= n <= lb:
            inner = 2.0*n/(alpha*(N-1)) - 1
            return 0.5*(1.0 + math.cos(math.pi*inner))
        elif lb <= n <= ub:
            return 1.0
        else:
            inner = 2*n/(alpha*(N-1)) - 2.0/alpha + 1.0
            return 0.5*(1.0 + math.cos(math.pi*inner))
'''
    def func(self,n,N):
        epsilon = self._epsilon
        print(n,N)

        lb = (epsilon)*N
        ub = (1-epsilon)*N
        if lb <= n  and n <= ub:
            return 1.0
        elif n < lb:
            z_plus = 2*epsilon*(1/(1+(2*n/(N)-1)) + 1/(1-2*epsilon+(2*n/(N)-1)))
            return 1/(z_plus+1)
        elif ub < n :
            z_minus = 2*epsilon*(1/(1-(2*n/(N)-1)) + 1/(1-2*epsilon-(2*n/(N)-1)))
            return 1/(z_minus+1)
'''

def get_window(name,kwargs):
    windows = [
        HannWindow,
        PlanckTukeyWindow
    ]
    for win in windows:
        if win.name() == name:
            return win(**kwargs)

    return None

def db(ampl):
    return 20 * log10(ampl)

def db_to_ampl(db):
    return 10.0**(db/20.0)

def nearest_index(x,v):
    index = (np.abs(x-v)).argmin()
    return index

class FrequencyData:

    def __init__(self,freqs,phasors,num_samples=None, \
                 window=None,padding=0,time_scale=1.0,autopower=False):
        assert(len(freqs) == len(phasors))
        # real function, so symmetric about frequency
        selector = [f >= 0 for f,x in zip(freqs,phasors)]
        self._time_scale = time_scale
        # transform applied to signal
        self._num_samples = len(freqs) if num_samples is None else num_samples
        self._window = window
        self._padding = padding
        self._autopower = autopower
        self._freqs = list(itertools.compress(freqs, selector))
        self._phasors = list(itertools.compress(phasors,selector))
        self.cutoff(-200)


    def num_samples(self):
        return self._num_samples

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
        return FrequencyData(freqs,map(lambda tup: complex(tup[0],tup[1]), \
                                       zip(ampl,phase)))

    @property
    def fmax(self):
        return max(self._freqs)

    @property
    def fmin(self):
        return min(self._freqs)

    @property
    def freqs(self):
        return self._freqs

    def copy(self,autopower=False):
        return FrequencyData(freqs=self._freqs,
                             phasors=self._phasors,
                             num_samples=self._num_samples,
                             window=self._window,
                             padding=self._padding,
                             time_scale=self._time_scale,
                             autopower=autopower)

    def autopower(self):
        fd = self.copy(autopower=True)
        fd._phasors = np.conj(self._phasors)*self._phasors
        return fd

    def normalize(self):
        self.autopower()

    def power(self):
        if self._autopower:
            freq_power = sum(map(lambda q : abs(q), self._phasors))
        else:
            freq_power = sum(map(lambda q : abs(q**2), self._phasors))
        return freq_power

    def amplitudes(self):
        return map(lambda x: x.real, self._phasors)

    def phases(self):
        return map(lambda x: x.imag, self._phasors)

    @property
    def phasors(self):
        return self._phasors

    def inv_fft(self):
        import lab_bench.analysis.waveform as wf
        dt = self._time_scale
        n = self.num_samples()
        freqs = np.linspace(0.0,1/(2.0*dt),n)
        times = np.linspace(0.0, dt*n,n)
        phasors = [complex(0.0)]*n
        print("-> build frequency buffer [%d]" % self.num_samples())
        # y(j) = (x * exp(2*pi*sqrt(-1)*j*np.arange(n)/n)).mean()
        for freq,phasor in zip(self.freqs,self.phasors):
            index = abs(freqs-freq).argmin()
            phasors[index] += phasor

        # take inverse fft
        values = scipy.fftpack.ifft(phasors)
        # remove padding
        if self._padding > 0:
            values = values[:-self._padding]
            times = times[:-self._padding]
        # invert window
        values = self._window.unapply(values,dt)
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
                'properties': {
                    'n_samples':self._num_samples,
                    'padding':self._padding,
                    'is_autopower': self._autopower,
                    'window':self._window.to_json() if not \
                    self._window is None else None,
                    'time_scale':self._time_scale}
                },

    def write(self,filename):
        with open(filename,'w') as fh:
            fh.write(json.dumps(self.to_json()))

    def plot_figure(self,plot_ampl,do_log_x=False,do_log_y=False):
        def custom_stem(ax,x,y):
            ax.axhline(min(x),max(x),0, color='r')
            ax.vlines(x, 0, y, color='b')
            ax.set_ylim([1.05*min(-1e-6,min(y)), 1.05*max(y)])

        def symlog(_x,thresh=10.0):
            x = np.array(_x)
            conds = [
                x > thresh,
                x < -thresh,
                (x <= -thresh)*(x >= thresh),
            ]
            lambdas = [
                lambda el: np.log10(el),
                lambda el: -1*np.log10(el),
                lambda el: el

            ]
            return np.piecewise(x,conds,lambdas)

        def stem_plot(axname,x,y,do_log_x=False,do_log_y=False):
            fig, ax = plt.subplots()
            if do_log_x:
                x = symlog(x)
            if do_log_y:
                y = symlog(y)

            custom_stem(ax,x,y)
            if do_log_y:
               ax.set_ylabel('%s (log(V))' % axname)
            else:
                ax.set_ylabel('%s (V)' % axname)

            if do_log_x:
                ax.set_xlabel('Frequency (log(Hz))')
            else:
                ax.set_xlabel('Frequency (Hz)')

            return fig,ax

        if plot_ampl:
            pl = stem_plot("Amplitude",
                            self._freqs,np.real(self._phasors),do_log_x,do_log_y)
        else:
            pl = stem_plot("Phase",
                            self._freqs,np.imag(self._phasors),do_log_x,do_log_y)

        return pl

    def plot(self,amplfile,phasefile,do_log_x=False,do_log_y=False):
        if not amplfile is None:
            fig,ax = self.plot_figure(True,do_log_x,do_log_y)
            fig.savefig(amplfile)
            plt.clf()
            plt.cla()
        if not phasefile is None:
            fig,ax = self.plot_figure(False,do_log_x,do_log_y)
            fig.savefig(phasefile)
            plt.clf()
            plt.cla()

class FreqDataset:
    def __init__(self):
        self.signals = {}
        self.time_transform = None
        self.signal_transform = None

    def set_time_transform(self,xform):
        self.time_transform = xform

    def set_signal_transform(self,xform):
        self.signal_transform = xform


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
        for datum in self.signals.values()<= 1e-10:
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
    def from_aligned_time_dataset(dataset,window,trend):
        ds = FreqDataset()
        ds.add_noise(data=dataset.noise.fft(window=window,trend=trend))
        ds.add_output(data=dataset.reference.fft(window=window,\
                                                 trend=trend))
        for index,inp in dataset.inputs.items():
            ds.add_input(index, data=inp.fft(window=window, \
                                             trend=trend))

        return ds

    @staticmethod
    def from_json(data):
        import lab_bench.analysis.waveform as wf
        ds = FreqDataset()
        for key,inp in data['signals'].items():
            datum = data['signals'][key][0]
            ds.signals[key] = FrequencyData.from_json(datum)
        if not data['transforms']['time'] is None:
            ds.set_time_transform(dx.DetTimeXform.from_json(
                data['transforms']['time']
            ))
        if not data['transforms']['signal'] is None:
             ds.set_signal_transform(dx.DetSignalXform.from_json(
                data['transforms']['signal']
            ))

        return ds

    def read(filename):
        with open(filename,'r') as fh:
            return FreqDataset.from_json(json.loads(fh.read()))


    def to_json(self):
        signals= dict(map(lambda args : (args[0],args[1].to_json()),
                          self.signals.items()))
        return {
            'signals': signals,
            'transforms':{
                'time':self.time_transform.to_json(),
                'signal':self.signal_transform.to_json()
            }
        }

    def write(self,filename):
        with open(filename,'w') as fh:
            data = self.to_json()
            fh.write(json.dumps(data))
