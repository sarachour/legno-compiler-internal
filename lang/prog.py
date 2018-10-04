
class MathProg:

    def __init__(self):
        self._bindings = {}
        self._intervals = {}
        self._freqs = {}

    def bind(self,var,expr):
        assert(not var in self._bindings)
        self._bindings[var] = expr

    def bindings(self):
        for var,expr in self._bindings.items():
            yield var,expr


    def interval(self,v,min_v,max_v):
        assert(min_v <= max_v)
        self._intervals[v] = (min_v,max_v)

    def compile(self):
        for variable in self._bindings:
            assert(variable in self._intervals)

        for variable,expr in self._bindings.items():
            min_freq,max_freq = expr.frequency_range(self._intervals)
            self._freqs[variable] = (min_freq,max_freq)
