
class NoiseSources:

    @staticmethod
    def thermal_noise(lb,ub,temperature):
        mean_sq = 4*kv*T*R
        raise NotImplementedError

    @staticmethod
    def flicker_noise(lb,ub):
        raise NotImplementedError

    @staticmethod
    def shot_noise(lb,ub):
        raise NotImplementedError

    def harmonic_disto(lb,ub):
        raise NotImplementedError


    def amplitude_disto(lb,ub):
        raise NotImplementedError

    def freq_resp_disto(lb,ub):
        raise NotImplementedError

    def phase_disto(lb,ub):
        raise NotImplementedError

    def group_delay_disto(lb,ub):
        raise NotImplementedError


class Transform:
    LOW_FREQ = 0;
    HI_FREQ = 1e6;

    def __init__(self):
        pass

    def xform_independent(self):
        raise NotImplementedError

    def xform_dependent(self,phasors):
        raise NotImplementedError

    def xform(self,signals):
        raise NotImplementedError

class LinearTransform(Transform):

    def __init__(self):
        # convert phasors to phasors
        Transform.__init__(self)

    def xform(self,signals):
        out_signal = Signal()
        for signal in signals:
            assert(isinstance(signal,Signal))
            for phasor in signal.signal:
                for new_phasor in self.xform_phasor(phasor):
                    out_signal.add(new_phasor)

            for phasor in signal.noise:
                for new_phasor in self.xform_phasor(phasor):
                    out_signal.add(new_phasor)

            for phasor in self.xform_independent():
                out_signal.add(phasor)

        return out_signal

class PhasorDataEntry:

    def __init__(self,xform):
        self._inputs = []
        self._xform = xform
        self._signal = None
        self._noise = PhasorTrain()
        self._init_state = None
        self._end=1.0
        self._npts=10000


    def initial_state(self, init_state):
        self._init_state = init_state

    def add_input(self,time,signal):
        input_freq = phasor.fft(time,signal)
        self._inputs.append(input_freq)

    def set_output(self,time,signal):
        if self._signal is None:
            self._compute_ideal_output()
        output_freq = phasor.fft(time,signal)

        self._noise = output_freq.difference(self._signal)

    def _compute_ideal_output():
        inputs = []
        output = []
        end,npts = self._end, self._npts
        time = range(0,npts)*end/npts
        for inp in self._inputs:
            _,signal = inp.timeseries(end,npts)
            inputs.append(signal)

        state = self._init_state
        for inps in zip(inputs):
            new_state,output = self._xform(state,inputs)
            state = new_state

        output_freq = phasor.fft(time,output)
        self._signal = output_freq

class EmpiricalTransform(Transform):

    def __init__(self):
        Transform.__init__(self)

    # return analytical result given arguments
    def apply(self,state,inputs):
        raise NotImplementedError

    def xform(self,signals):
        raise NotImplementedError

    def ideal_output(self,input_signals):
        outputs = []
        for inputs in zip(input_signals):
            output = self.apply(inputs)
            outputs.append(output)

        return output

    def add_data(self,init_state,input_signals,output_signal):
        # input signals and output signal are in time domain.
        entry = PhasorDataEntry(self)
        for time,signal in input_signals:
            input_freq = phasor.fft(time,signal)
            entry.add_input(input_freq)

        entry.initial_state(init_state)
        time,signal = output_signal
        entry.compute_noise(time,signal)

