import ops.phasor as phasor
import math

# J/K
BOLTZMANN=1.38064852e-23
ELECTRON_CHARGE=0.0

# current (A) thermal noise of resistor
def thermal_noise(temperature,resistance,frequency,bandwidth):
    temperature_K = temperature + 273.15
    variance = math.sqrt( \
        4.0*BOLTZMANN*temperature_K*bandwidth/resistance)

    return variance

def shot_noise(current,bandwidth):
    variance = math.sqrt(2*ELECTRON_CHARGE*current*bandwidth)
    return variance

def flicker_noise(frequency):
    alpha = 2e-3
    Ntot = 1.0
    variance = (alpha/Ntot)*1.0/(frequency + 1e-6)
    return variance


class NoisyBlock:

    def __init__(self,name,inputs,output):
        self._name = name
        self._inputs = inputs
        self._output = output

    @property
    def name(self):
        return self._name

    @property
    def inputs(self):
        return self._inputs

    @property
    def output(self):
        return self._output

    def compute(self,state,inps):
        raise NotImplementedError

    def noise_spectrum(self,inp_freqs,out_freq):
        raise NotImplementedError

    def output_signal(self,init_state,inps):
        outputs = []
        inputs_fft = {}

        for varname,(time,sig) in inps.items():
            input_fft = phasor.fft(time,sig)
            inputs_fft[varname]=  input_fft

        time = inps[inps.keys()[0]][0]
        state = init_state
        for idx,t in enumerate(time):
            inp_dict = {}
            for varname,(_,sig) in inps.items():
                inp_dict[varname] = sig[idx]

            state,output = self.compute(state,inp_dict)
            outputs.append(output)

        output_fft = phasor.fft(time,outputs)
        noise_fft = self.noise_spectrum(inputs_fft,output_fft)

        _,noise_sig = noise_fft.timeseries(times=time)
        return map(lambda args: args[0]+args[1],
                   zip(outputs,noise_sig))




class DACBlock(NoisyBlock):

    def __init__(self):
        NoisyBlock.__init__(self,"dac",['x'],'z')

    def compute(self,state,inps):
        assert(len(inps) == 1)
        return None,inps['x']

    def noise_spectrum(self,inp_freqs,out_freq):
        bandwidth = int(1e5)
        delta = int(bandwidth/1000)
        spectrum = phasor.PhasorTrain()
        for freq in range(0,bandwidth,delta):
            noise = thermal_noise(23,5,freq,bandwidth)
            noise += flicker_noise(freq)
            phas = phasor.Phasor(freq,noise,0,noise=True)
            spectrum.add_phasor(phas)

        return spectrum



def get_block(name):
    blocks = [DACBlock()]
    for block in blocks:
        if block.name == name:
            return block

    raise Exception("unknown block <%s>" % name)
