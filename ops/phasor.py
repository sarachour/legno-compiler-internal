import ops.op as op
import math
import matplotlib.pyplot as plt
import numpy


def deg_to_rad(value):
    return value / 180.0 * math.pi

def hz_to_rad(value):
    return value*1/(2.0*math.pi)

def debug_figure(filename,times,ampls,freq,fftdata):
    old_size = plt.rcParams["figure.figsize"]
    plt.rcParams["figure.figsize"] = (6,8)
    fig,(ax0,ax1,ax2)= plt.subplots(3,1)
    ax0.plot(times,ampls)
    ax0.set_xlabel("time")
    ax0.set_ylabel("amplitude")
    ax1.plot(freq,fftdata.real)
    ax1.set_xlabel("freq")
    ax1.set_ylabel("energy")
    ax2.plot(freq,fftdata.imag)
    ax2.set_xlabel("freq")
    ax2.set_ylabel("energy")
    plt.savefig(filename)
    plt.rcParams["figure.figsize"] = old_size
    plt.clf()

def fft(times,ampls,threshhold=0.1,debug_fig=None):
    def complex_mag(x):
        return math.sqrt(x.real**2 + x.imag**2)

    fftdata = numpy.fft.fft(ampls)
    freq = numpy.fft.fftfreq(len(ampls),times[1]-times[0])
    if not debug_fig is None:
        debug_figure(debug_fig,times,ampls,freq,fftdata)

    max_ampl = max(map(lambda x : \
                       complex_mag(x), fftdata))

    relevent_freqs = filter(lambda x : \
           complex_mag(x[1])/max_ampl >= threshhold,
                            zip(freq,fftdata))

    phasor_train = PhasorTrain()
    for frequency,coordinate in relevent_freqs:
        phasor = Phasor(frequency,
                        coordinate.real,
                        coordinate.imag,
                        noise=False)
        x,y = phasor.to_rect()
        phasor_train.add_phasor(phasor)

    return phasor_train

class Phasor:

    # phase in degrees
    # magnitude in volts/amps
    def __init__(self,freq,M,P,scf=op.Const(1),noise=False):
        self._magnitude = M
        self._phase = P
        self._frequency = freq
        self._scf = scf
        self._noise = noise


    def __repr__(self):
        return "%s*%s*e^(i %s t)*e^(i %s)" % (self._scf,self._magnitude,self._frequency,self._phase)

    @property
    def freq(self):
        return self._frequency

    @staticmethod
    def scalar(self,magnitude,phase,scf=op.Const(1),noise=False):
        return Phasor(0,magnitude,phase,scf=scf,noise=noise)

    @property
    def phase(self):
        return self._phase

    @property
    def magnitude(self):
        return self._magnitude

    @property
    def scf(self):
        return self._scf


    def scaling_value(self,bindings):
        scf_val = self.scf.compute(bindings)
        return scf_val

    @property
    def is_noise(self):
        return self._noise

    def to_rect(self):
        x = self._magnitude*math.cos(self._phase)
        y = self._magnitude*math.sin(self._phase)
        return x,y


    def set_magnitude(self,v):
        self._magnitude = v
        return self

    def set_phase(self,v):
        self._phase = v
        return self

    def copy(self):
        return Phasor(self,
                      self.freq,
                      self.magnitude,
                      self.phase,
                      scf=self.scf,
                      noise=self.is_noise)

    def integrate(self):
        self._magnitude /= self._frequency
        self._phase -= math.pi/2.0

    def mult(self,phasor):
        assert(phasor.freq == 0)
        # multiply by M*e^{i*P}
        self._magnitude = M*self._magnitude
        self._phase = self._phase + P

    def add(self,new_phasor):
        if new_phasor.freq != self._frequency:
            return False

        if new_phasor.is_noise != self._noise:
            return False

        x1,y1 = self.to_rect()
        x2,y2 = new_phasor.to_rect()
        x = x1+x2
        y = y1+y2

        if self._scf == new_phasor.scf:
            # NOTE: the scaling factor doesn't change, since we can factor
            # it out of the magnitude.
            self._magnitude = math.sqrt(x**2+y**2)
            self._phase = math.atan(y/x)
            return True
        else:
            return False

    def value_at_time(self,t,bindings={}):
        ampl = self.scaling_value(bindings)*self._magnitude
        return ampl*math.cos(self._frequency*t + self._phase)


    def timeseries(self,end,npts,bindings={}):
        times = []
        signal = []
        t=0.0
        delta = float(end)/npts
        while t <= end:
            times.append(t)
            value = self.value_at_time(t,bindings=bindings)
            signal.append(value)
            t += delta

        return times,signal

class PhasorTrain:

    def __init__(self):
        self._phasors = {}
        self._n = 0

    @property
    def size(self):
        return self._n

    def add_phasor(self,new_phasor):
        if not new_phasor.freq in self._phasors:
            self._phasors[new_phasor.freq] = []

        for phasor in self._phasors[new_phasor.freq]:
            if phasor.add_phasor(new_phasor):
                return

        self._phasors[new_phasor.freq].append(new_phasor)
        self._n += 1

    def add(self,freq,M,P,scf=op.Const(1)):
        self.add_phasor(Phasor(freq,M,P,scf=scf))

    def value_at_time(self,t,bindings={}):
        value = 0.0
        for phasor_coll in self._phasors.values():
            for phasor in phasor_coll:
                value += phasor.value_at_time(t,bindings=bindings)

        return value

    def group_by_scaling_expr(self):
        group_by = {}
        for phasor_coll in self._phasors.values():
            for phasor in phasor_coll:
                if not phasor.scf in group_by:
                    group_by[phasor.scf] = PhasorTrain()

                group_by[phasor.scf].add_phasor(phasor)

        for scaling_expr, phasor_list in group_by.items():
            yield scaling_expr,phasor_list

    def max_freq(self):
        return max(map(lambda phasor: phasor.freq, self))


    def min_freq(self):
        return max(map(lambda phasor: phasor.freq, self))


    def phase_and_magnitude(self,bindings={}):
        magnitudes = []
        phases = []
        freqs = []
        for frequency,phasors in self._phasors.items():
            magnitude = 0
            phase = 0
            for phasor in phasors:
                magnitude += phasor.magnitude*phasor.scaling_value(bindings)
                phase += phasor.phase

            freqs.append(frequency)
            magnitudes.append(magnitude)
            phases.append(phase)

        return freqs,magnitudes, phases

    def power(self,bindings):
        value = 0
        for scaling_expr,phasor_list in self.group_by_scaling_expr():
            weight = sum(map(lambda phasor:
                             (phasor.scaling_value(bindings)*phasor.magnitude)**2,
                             self))
            value += weight

        return value


    def timeseries(self,end=1.0,npts=100,bindings={},times=None):
        delta = float(end)/npts
        if times is None:
            times = map(lambda t: t*delta, range(0,npts))

        signal = []
        for time in times:
            value = self.value_at_time(time,bindings=bindings)
            signal.append(value)

        return times,signal

    def __iter__(self):
        for ph_list in self._phasors.values():
            for phasor in ph_list:
                yield phasor

class Signal:

    def __init__(self):
        self.signal = PhasorTrain()
        self.noise = PhasorTrain()

    def add(self,phasor):
        if phasor.is_noise:
            self.noise.add_phasor(phasor)
        else:
            self.signal.add_phasor(phasor)

    def frequency(self):
        raise NotImplementedError

    def phase(self):
        raise NotImplementedError

    def snr(self,bindings):
        assert(not bindings is None)
        signal_power = self.signal.power(bindings)
        noise_power = self.noise.power(bindings)
        if noise_power != 0:
            snr = signal_power/noise_power
        else:
            snr = "inf"

        print("theo signal: %s" % signal_power)
        print("theo noise: %s" % noise_power)
        return snr


    def timeseries(self,end,npts,bindings={},times=None):
        time,signal = self.signal.timeseries(end,npts, \
                                             bindings=bindings, \
                                             times=times)
        time,noise = self.noise.timeseries(end,npts, \
                                           bindings=bindings, \
                                           times=times)

        return times,signal,noise
