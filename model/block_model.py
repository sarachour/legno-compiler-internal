from ops.phasor import phasor

class BlockModel:

    MODE_TIME_AND_FREQ = 0
    MODE_TIME_ONLY = 0
    MODE_FREQ_ONLY = 0

    def __init__(self,mode,name,inputs,output):
        self._inputs = inputs
        self._output = output
        self._noise_model = None
        self._name = name
        self._mode = mode

    def set_noise_model(model):
        assert(isinstance(model,NoiseModel))
        return model

    @property
    def name(self):
        return self._name

    @property
    def inputs(self):
        return self._inputs

    @property
    def output(self):
        return self._output


    def signal_time_domain(self,state,time,inputs):
        raise NotImplementedError

    def signal_freq_domain(self,input_freqs):
        raise NotImplementedError

    def noise_f2f(self,input_freqs,output_freq):
        assert(not self._noise_model is None)
        variables = {self._output:output_freq}
        for varname,sig in input_freqs.items():
            variables[varname] = sig

        noise_freq = self._noise_model.execute(variables)
        return noise_freq

    def signal_t2t(self,init_state,time,inputs):
        def extract(dictionary,index):
            return \
                dict(map(lambda k,v: (k,v[idx]),
                         dictionary.items()))

        if self._mode == BlockModel.MODE_FREQ_ONLY:
            raise NotImplementedError

        else:
            state = init_state
            outputs = []
            for idx,time in enumerate(time):
                value = self._signal_time_domain(state,time,
                                         extract(inputs,idx))
                outputs.append(value)

            return time,outputs

    @staticmethod
    def inputs_t2f(self,time,inputs):
        inp_freqs = {}
        for inp in inputs:
            inp_freqs[inp] = phasor.fft(time,inp)

        return inp_freqs

    def signal_f2f(self,inp_freqs):
        if self._mode == BlockModel.MODE_TIME_ONLY:
            raise NotImplementedError

        else:
            out_freq = self.signal_freq_domain(inp_freqs)
            return out_freq

    def signal_t2f(self,init_state,time,inputs):
        if self._mode == BlockModel.MODE_TIME_ONLY:
            _,outputs = self.signal_t2t(init_state,time,inputs)
            out_freq = phasor.fft(time,outputs)
            return out_freq

        elif self._mode == BlockModel.MODE_FREQ_ONLY:
            inp_freqs = BlockModel.inputs_t2f(time,inputs)
            return self.signal_f2f(inp_freqs)

    def nzsig_t2t(self,init_state,time,inputs):
        inp_freqs = BlockModel.inputs_t2f(time,inputs)
        out_freq = self.signal_f2f(inp_freqs)
        nz_freq = self.noise_f2f(inp_freqs,out_freq)
        out_freq.add(nz_freq)
        return out_freq


    def nzsig_t2f(self,init_state,time_inputs):
        inp_freqs = BlockModel.inputs_t2f(time,inputs)
        nzsig_freqs = self.nzsig_f2f(inp_freqs)
        return nzsig_freqs

    def nzsig_f2f(self,inp_freqs):
        out_freq = self.signal_f2f(inp_freqs)
        nz_freq = self.noise_f2f(inp_freqs,out_freq)
        out_freq.add(nz_freq)
        return out_freq

class LinearBlockModel(BlockModel):

    # \integ w1 a1 + w2 a2 + w3 a3 + w4 a4
    def __init__(self,name,inputs,output,weights,offset,\
                 integrate=False):
        BlockModel.__init__(self,name,inputs,output)
        assert(len(inputs) == len(weights))
        self._weights = weights
        self._integrate = integrate

    def signal_freq_domain(self,inputs):
        raise NotImplementedError

    def signal_time_domain(self,state,time,inputs):
        raise NotImplementedError

    def output_value(self,state,inputs):
        return state,inputs['x']
