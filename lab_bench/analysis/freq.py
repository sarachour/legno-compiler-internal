import json
import numpy as np
import matplotlib.pyplot as plt
import itertools

class StochPhasor:
    def __init__(self,ampls,phases):
        self._ampl = np.mean(ampls),np.std(ampls)
        self._phase = np.mean(phases),np.std(phases)
        self._n = len(ampls)

    def vector(self):
        return [self._ampl[0],\
                self._ampl[1],\
                self._phase[0],\
                self._phase[1]]

    def __repr__(self):
        amu,asigma = self._ampl
        pmu,psigma = self._phase
        return "<N(%s,%s), N(%s,%s)> [%s]" % \
            (amu,asigma,pmu,psigma,self._n)

class StochFrequencyData:
    ZERO_PHASOR = StochPhasor([0],[0])

    def __init__(self,freqdataset):
        by_freq = {}
        for freq_datum in freqdataset:
            for freq,ampl,phase in freq_datum.phasors():
                if not freq in by_freq:
                    by_freq[freq] = {'phase':[],'ampl':[]}

                by_freq[freq]['phase'].append(phase)
                by_freq[freq]['ampl'].append(ampl)

        self._freqs = list(by_freq.keys())
        self._freqs.sort()
        self._phasors = list(map(lambda freq: \
                StochPhasor(by_freq[freq]['ampl'],
                            by_freq[freq]['phase']),
                                 self._freqs))

    def phasors(self):
        for f,p in zip(self._freqs,self._phasors):
            yield f,p

    def nearest_phasor(self,freq,cutoff=None):
        if len(self._freqs) == 0:
            return freq,StochFrequencyData.ZERO_PHASOR

        minidx = np.abs(np.array(self._freqs) - freq).argmin()
        near_freq = self._freqs[minidx]
        if cutoff is None or abs(self._freqs[minidx] - freq) <= cutoff:
            return self._freqs[minidx],self._phasors[minidx]
        else:
            return freq,StochFrequencyData.ZERO_PHASOR

    def bounds(self):
        if len(self._freqs) == 0:
            return None,None

        return min(self._freqs),max(self._freqs)

    def freqs(self):
        return self._freqs

    def min_freq_delta(self):
        if len(self._freqs) <= 1:
            return None

        min_delta = np.min(np.diff(self._freqs))
        print(min_delta)
        return min_delta

    def freq_delta(self):
        if len(self._freqs) == 1:
            return -1

        return np.mean(np.diff(self._freqs))

    def fill_holes(self):
        freq_delta = self.freq_delta()
        print(freq_delta)
        input()

    def __repr__(self):
        st = ""
        for freq,phasor in self.phasors():
            st += "%s: %s\n" % (freq,phasor)
        return st

    def plot(self,outfile):
        x = self._freqs
        y = list(map(lambda p: p.vector()[0], self._phasors))
        yerr = list(map(lambda p: p.vector()[1], self._phasors))
        fig,axs = plt.subplots(nrows=2,ncols=1,sharex=True)
        ax0 = axs[0]
        ax0.errorbar(x,y,yerr=yerr,fmt='.',markersize=0.3,color='red',
                     ecolor='blue')
        ax0.set_title("Amplitude")
        ax0 = axs[1]
        y = list(map(lambda p: p.vector()[2], self._phasors))
        yerr = list(map(lambda p: p.vector()[3], self._phasors))
        ax0.errorbar(x,y,yerr=yerr,fmt='.',markersize=0.3,color='red',
                     ecolor='blue')
        ax0.set_title("Phase")

        fig.savefig(outfile)
        plt.close(fig)
        plt.clf()
        plt.cla()

class StochFreqDataset:

    def __init__(self,dataset):
        self._obs = StochFrequencyData(dataset)
        self._signals = {}

    @property
    def observation(self):
        return self._obs

    def get_signal(self,name):
        return self._signals[name]

    def add_signal(self,name,dataset):
        self._signals[name] = StochFrequencyData(dataset)

    def data(self):
        yield self._obs
        for sig in self._signals.values():
            yield sig

    def bounds(self):
        def update(min_f,max_f,bnd):
            cmin,cmax = bnd
            if cmin is None:
                cmin = min_f
            if cmax is None:
                cmax = max_f

            if min_f is None:
                min_f = cmin
            return min(cmin,min_f),max(cmax,max_f)

        min_f,max_f = None,0
        for sig in self.data():
            min_f,max_f = update(min_f,max_f,sig.bounds())

        return min_f,max_f

    def avg_freq_delta(self):
        return min(filter(lambda q: not q is None,
                          map(lambda sig: sig.freq_delta(), \
                              self.data())))

    def min_freq_delta(self):
        return min(filter(lambda q: not q is None,
                          map(lambda sig: sig.min_freq_delta(), \
                              self.data())))

    def __repr__(self):
        st = "==== Observations ====\n"
        st += str(self._obs)
        for name,sig in self._signals.items():
            st += "==== %s ====\n" % name
            st += str(sig)

        return st

class Phasor:
    def __init__(self,ampl,phase):
        self._ampl = ampl
        self._phase = phase


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

    def plot_figure(self,plot_ampl,do_log_x=False,do_log_y=False):
        def stem_plot(axname,x,y,do_log_x=False,do_log_y=False):
            fig, ax = plt.subplots()
            if len(x) > 0:
                ax.stem(x,y,markerfmt=' ')
                if do_log_y:
                    ax.set_yscale('symlog')
                    ax.set_ylabel('%s (log(dB))' % axname)
                else:
                    ax.set_ylabel('%s (dB)' % axname)

                if do_log_x:
                    ax.set_xscale('log')
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
        (afig,aax) = self.plot_figure(True,do_log_x,do_log_y)
        afig.savefig(amplfile)
        plt.close(afig)
        plt.clf()
        plt.cla()
        (pfig,pax) = self.plot_figure(False,do_log_x,do_log_y)
        pfig.savefig(phasefile)
        plt.close(pfig)
        plt.clf()
        plt.cla()

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
    def from_aligned_time_dataset(delay,confidence,dataset):
        print("delay:%s, confidence:%s" % (delay,confidence))
        ds = FreqDataset(delay,confidence)
        ds.noise = dataset.output\
                          .difference(dataset.reference)\
                          .fft()
        ds.output = dataset.reference.fft()
        for index,inp in dataset.inputs.items():
            inp_fft = inp.fft()
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
