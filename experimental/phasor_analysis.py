import ops.op as op
import math
import matplotlib.pyplot as plt
import numpy

def deg_to_rad(value):
    return value / 180.0 * math.pi

def hz_to_rad(value):
    return value*1/(2.0*math.pi)

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


    def integrate(self):
        self._magnitude /= self._frequency

    def add_phasor(self,new_phasor):
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

    def mult_const(self,M,P):
        self._magnitude = M*self._magnitude
        self._phase = self._phase + P

    def value_at_time(self,t,bindings={}):
        ampl = self.scaling_value(bindings)*self._magnitude
        return ampl*math.cos(self._frequency*t + self._phase)

class PhasorTrain:

    def __init__(self):
        self._phasors = {}

    def add_phasor(self,new_phasor):
        if not new_phasor.freq in self._phasors:
            self._phasors[new_phasor.freq] = [new_phasor]
            return

        for phasor in self._phasors[new_phasor.freq]:
            if phasor.add_phasor(new_phasor):
                return

        self._phasors[new_phasor.freq].append(new_phasor)

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


    def timeseries(self,end,npts,bindings={}):
        t = 0.0
        delta = end/npts
        times = []
        signal = []
        noise = []
        while t <= end:
            times.append(t)
            value = self.signal.value_at_time(t,bindings=bindings)
            signal.append(value)
            value = self.noise.value_at_time(t,bindings=bindings)
            noise.append(value)
            t += delta

        return times,signal,noise

class LinearTransform:

    def __init__(self,low_freq,hi_freq):
        self._low_freq = low_freq
        self._hi_freq = hi_freq
        # convert phasors to phasors
        pass

    def xform_independent(self,phasor):
        raise NotImplementedError


    def xform_phasor(self,phasor):
        raise NotImplementedError

    def xform(self,signal):
        assert(isinstance(signal,Signal))
        out_signal = Signal()
        for phasor in signal.signal:
            for new_phasor in self.xform_phasor(phasor):
                out_signal.add(new_phasor)

        for phasor in signal.noise:
            for new_phasor in self.xform_phasor(phasor):
                out_signal.add(new_phasor)

        for phasor in self.xform_independent():
            out_signal.add(phasor)

        return out_signal

class DACTransform(LinearTransform):

    def __init__(self,lf,hf):
        LinearTransform.__init__(self,lf,hf)
        self._n = 10

    def xform_phasor(self,phasor):
        def harmonic_ampl(harmonic):
            return math.e**(-0.5*harmonic*4)

        block_phase = 1e-2
        for harmonic in range(1,self._n):
            yield Phasor(phasor.freq*harmonic,
                         harmonic_ampl(harmonic)*phasor.magnitude,
                         phasor.phase+block_phase,
                         noise=harmonic > 1 or phasor.is_noise,
                         scf=phasor.scf
            )

    def xform_independent(self):
        for i in range(0,100):
            freq = (self._hi_freq-self._low_freq)/100.0*i
            yield Phasor(freq,
                        5e-3,
                        deg_to_rad(10),
                        noise=True
            )


class HPFTransform(LinearTransform):
    def __init__(self,lf,hf,cutoff):
        LinearTransform.__init__(self,lf,hf)
        self._cutoff = cutoff


    def xform_phasor(self,phasor):
        if phasor.freq <= self._cutoff:
            yield phasor

    def xform_independent(self):
        yield Phasor(0,0,0,noise=True)
        return


class GainTransform(LinearTransform):

    def __init__(self,lf,hf,coeff,scf=op.Const(1)):
        LinearTransform.__init__(self,lf,hf)
        self._coeff = coeff
        self._scf = scf

    def xform_phasor(self,phasor):

        yield Phasor(phasor.freq,
                     phasor.magnitude*self._coeff,
                     phasor.phase,
                     noise=phasor.is_noise,
                     scf=op.Mult(phasor.scf,self._scf)
        )

    def xform_independent(self):
        for i in range(0,100):
            freq = (self._hi_freq-self._low_freq)/100.0*i
            yield Phasor(freq,
                        5e-3,
                        deg_to_rad(10),
                        noise=True
            )


class NonLinearTransform:

    def __init__(self):
        pass

def plot_timeseries(name,filename,times,signal,noise):
    plt.plot(times,signal)
    plt.plot(times,noise)
    plt.xlabel("time (realtime)")
    plt.ylabel("signal")
    plt.title(name)
    plt.savefig(filename)
    plt.clf()

def plot_phase_magnitude(name,filename,sig_freqs,signal_magnitude,signal_phase,
                         noise_freqs,noise_magnitude,noise_phase):
    fig, (ax1,ax2) = plt.subplots(2,1)
    ax1.stem(sig_freqs,signal_magnitude,markerfmt=' ',linefmt='b-',basefmt=' ',label='signal')
    if len(noise_freqs) > 0:
        ax1.stem(noise_freqs,noise_magnitude,markerfmt=' ',linefmt='r-',basefmt=' ',label='noise')

    ax2.stem(sig_freqs,signal_phase,markerfmt=' ',linefmt='b-',label='signal')
    if len(noise_freqs) > 0:
        ax2.stem(noise_freqs,noise_phase,markerfmt=' ',linefmt='r-',basefmt=' ',label='noise')

    ax1.set_xlabel("frequency (hz)")
    ax1.set_ylabel("power (db)")
    ax1.set_title(name)
    ax2.set_xlabel("frequency (hz)")
    ax2.set_ylabel("phase (degrees)")
    ax2.legend()
    plt.savefig(filename)
    plt.clf()



def compute_experimental_snr(signal,noise):
    signal_power = sum(map(lambda x : x**2, signal))/len(signal)
    noise_power = sum(map(lambda x : x**2, noise))/len(noise)

    print("exp signal: %s" % signal_power)
    print("exp noise: %s" % noise_power)
    if noise_power != 0:
        snr = signal_power/noise_power
    else:
        snr = "inf"

    return snr

def snr_to_decibals(snr):
    return 10*math.log(snr)

def dac_explore():
    dac_input = Signal()
    # the 0.5 is scaled
    dac_input.signal.add(hz_to_rad(500),0.5,0,scf=op.Var('dac1'))

    scfs = {"dac1":[1.0]}

    xform = DACTransform(0,1e4)
    dac_output = xform.xform(dac_input)

    choices = list(map(lambda v: dict([('dac1',v)]), scfs['dac1']))
    for choice in choices:
        times,signal,noise = dac_output.timeseries(1.0, 1000,bindings=choice)
        plot_timeseries("dac_output","dac_out_%f.png" % choice['dac1'],
                        times,signal,noise)


    xform = HPFTransform(0,1e4,hz_to_rad(10000))
    hpf_output = xform.xform(dac_output)
    for choice in choices:
        times,signal,noise = hpf_output.timeseries(1.0, 1000,bindings=choice)
        plot_timeseries("hpf_output","hpf_out_%f.png" % choice['dac1'],
                        times,signal,noise)

import gpkit

def gpkit_expr(variables,expr):
    if expr.op == op.Op.CONST:
        return expr.value
    elif expr.op == op.Op.MULT:
        arg1 = gpkit_expr(variables,expr.arg1)
        arg2 = gpkit_expr(variables,expr.arg2)
        return arg1*arg2
    elif expr.op == op.Op.VAR:
        return variables[expr.name]
    else:
        raise Exception(expr)

def optimize(variables,signal,low_noise=True):
    varmap = {}
    for variable in variables:
        varmap[variable] = gpkit.Variable(variable)

    posy = 0
    for expr,phasors in signal.signal.group_by_scaling_expr():
        gexpr = gpkit_expr(varmap,expr)
        weight = sum(map(lambda phasor: phasor.magnitude,phasors))
        posy = 1/(weight*gexpr) + posy if low_noise else weight*gexpr + posy

    for expr,phasors in signal.noise.group_by_scaling_expr():
        gexpr = gpkit_expr(varmap,expr)
        weight = sum(map(lambda phasor: phasor.magnitude,phasors))
        posy = weight*gexpr + posy if low_noise else 1/(weight*gexpr) + posy

    cstrs = []
    for variable in variables:
        cstrs.append(varmap[variable] <= 100)

    print(posy)
    model = gpkit.Model(posy, cstrs)
    result = model.solve(verbosity=0)
    bindings = {}
    for variable,value in result['variables'].items():
        bindings[str(variable)] = value

    return bindings

def energy(fn,max_time):
    n = 100
    delta = max_time/float(n)
    power = 0.0
    for i in  range(0,n):
        power += fn(delta*i)**2

    return math.sqrt(power/n)

def sinusoid(ampl,freq,phase):
    return lambda t : ampl*math.sin(freq*t + phase)

def gain_explore():
    dac_input = Signal()
    max_time = 1.0

    const_gains = [[2,0.5,0.25],[0.25,0.5,2],[0.5,2,0.25]]
    variables = ['dac1','coeff1','coeff0','coeff2']

    for const_gain_list in const_gains:
        dac_input = Signal()
        ampl = energy(sinusoid(0.5,hz_to_rad(500),0), max_time)
        dac_input.signal.add(hz_to_rad(500),ampl,0,scf=op.Var('dac1'))
        xform = DACTransform(0,1e4)
        dac_output = xform.xform(dac_input)
        curr_signal = dac_output

        for coeff,gain in enumerate(const_gain_list):
            xform = GainTransform(0,1e4,gain,scf=op.Var('coeff%d' % coeff))
            new_output = xform.xform(curr_signal)
            curr_signal = new_output

        bindings = optimize(variables,curr_signal,low_noise=True)
        #bindings = optimize(['dac1'],curr_input)
        print("{ %s }" % str(const_gain_list))
        print(bindings)
        times,signal,noise = curr_signal.timeseries(max_time,1000,bindings=bindings)
        plot_timeseries('gain_output','gain_time_%s.png' % str(const_gain_list),
                        times,signal,noise)

        sig_freqs,sig_mag,sig_phase = curr_signal.signal.phase_and_magnitude(bindings)
        nz_freqs,nz_mag,nz_phase = curr_signal.noise.phase_and_magnitude(bindings)
        plot_phase_magnitude('gain_output','gain_freq_%s.png' % str(const_gain_list),
                             sig_freqs,sig_mag,sig_phase,nz_freqs,nz_mag,nz_phase)
        snr_theo = curr_signal.snr(bindings)
        snr_exp = compute_experimental_snr(signal,noise)
        print("theoretical  snr: %s" % (snr_theo))
        print("experimental snr: %s" % (snr_exp))



#gain_explore()
import ops.transform as transform
import ops.phasor as phasor

#builder = transform.EmpiricalModelBuilder(lambda args: args[0],1)
#builder.process_directory('calib_dac',['INP'],'OUT+')

sig1 = phasor.Phasor( phasor.hz_to_rad(500), 1.0, 0 )
sig2 = phasor.Phasor( phasor.hz_to_rad(500), 1.0,
                      phasor.deg_to_rad(100))

times1,ampls1 = sig1.timeseries(1,1000)
phasor.fft(times1,ampls1,debug_fig='sig1.png')

times2,ampls2 = sig2.timeseries(1,1000)
phasor.fft(times2,ampls2,debug_fig='sig2.png')


total1 = list(map(lambda args: 1.0/(abs(args[0])+1.0),
                 zip(ampls1,ampls2)))

total2 = list(map(lambda args: 1.0/(abs(args[1])+1.0),
                 zip(ampls1,ampls2)))

phasor.fft(times2,total1,debug_fig='fn1.png')
phasor.fft(times2,total2,debug_fig='fn2.png')
