import chip.units as units
from enum import Enum

class Properties:
    CURRENT = 'current'
    VOLTAGE = 'voltage'
    DIGITAL = 'digital'
    ANALOG = 'analog'

    def __init__(self,typ):
        typ = Properties.ANALOG if Properties.is_analog(typ) else typ

        self._type = typ


    @property
    def type(self):
        return self._type

    @staticmethod
    def is_analog(typ):
        return typ == Properties.CURRENT or typ == Properties.VOLTAGE \
            or typ == Properties.ANALOG

CURRENT = Properties.CURRENT
VOLTAGE = Properties.VOLTAGE
DIGITAL = Properties.DIGITAL
ANALOG = Properties.ANALOG
from ops.interval import Interval, IRange, IValue


class AnalogProperties(Properties):
    class SignalType(Enum):
        CONSTANT = "constant"
        DYNAMIC = "dynamic"

    def __init__(self):
        Properties.__init__(self,Properties.ANALOG)
        self._bounds = (None,None,units.unknown)
        self._bandwidth = (None,None,units.unknown)
        self._min_signal = {}

    def set_bandwidth(self,lower,upper,unit):
        assert(lower is None or upper is None or lower <= upper)
        self._bandwidth = (lower,upper,unit)
        return self

    def set_interval(self,lower,upper,unit):
        assert(lower is None or upper is None or lower <= upper)
        self._bounds = (lower,upper,unit)
        return self

    def set_min_signal(self,typ,min_sig,units):
        self._min_signal[typ] = (min_sig,units)

    def min_signal(self,typ):
        sig,unit = self._min_signal[typ]
        return sig

    def interval(self):
        lb,ub,unit = self._bounds
        return IRange(lb,ub)

    def bandwidth(self):
         lb,ub,unit = self._bandwidth
         lb = lb*unit if not lb is None else None
         ub = ub*unit if not ub is None else None
         return Interval.type_infer(lb,ub)


    def check(self):
        assert(not self._bounds[0] is None)
        assert(not self._bounds[1] is None)
        assert(not self._bounds[1] is units.unknown)
        assert(not self._min[0] is None)
        assert(not self._min[1] is units.unknown)

    def __repr__(self):
        return "Analog(bounds=%s, bw=%s, min=%s)" \
            % (self._bounds,self._bandwidth,self._min)

class DigitalProperties(Properties):
    class ClockType(Enum):
        CLOCKED = "clocked"
        CONTINUOUS = "continuous"
        CONSTANT = "constant"
        UNKNOWN = "unknown"

    class SignalType(Enum):
        CONSTANT = "constant"
        DYNAMIC = "dynamic"

    def __init__(self):
        Properties.__init__(self,Properties.DIGITAL)
        self._values = None
        self._max_error = None
        self._kind = DigitalProperties.ClockType.UNKNOWN
        # for clocked
        self._sample_rate = (None,units.unknown)
        # for continuous
        self._bandwidth = (None,None,units.unknown)
        # quantization
        self._min_quantize = {}

    def __repr__(self):
        clk = "Synch(kind=%s, rate=%s, samps=%s, bw=%s)" % \
              (self._kind,self._sample_rate, self._max_samples,self._bandwidth)
        dig = "Digital(min=%s, max=%s)" % (min(self._values), max(self._values))
        return dig + " " + clk

    def set_continuous(self,lb,ub,unit):
        self._kind = DigitalProperties.ClockType.CONTINUOUS
        self._bandwidth = (lb,ub,unit)
        return self

    def set_clocked(self,sample_rate,max_samples,unit):
        self._kind = DigitalProperties.ClockType.CLOCKED
        self._sample_rate = (sample_rate,unit)
        self._max_samples = max_samples
        return self

    def set_min_quantize(self,typ,v):
        assert(not typ in self._min_quantize)
        self._min_quantize[typ] = v

    def min_quantize(self,typ):
        if not typ in self._min_quantize:
            for k,q in self._min_quantize.items():
                print("%s=%s" % (k,q))
            raise Exception("not in min-quantize: <%s>" % typ)
        return self._min_quantize[typ]

    def interval(self):
        lb = min(self.values())
        ub = max(self.values())
        return IRange(lb,ub)


    def value(self,value):
        diff = map(lambda x : (x,abs(x-value)),self._values)
        choices = sorted(diff, key=lambda q: q[1])
        closest_value, error = choices[0]
        return closest_value

    @property
    def kind(self):
        return self._kind

    @property
    def sample_rate(self):
        rate,unit = self._sample_rate
        return rate*unit


    @property
    def max_samples(self):
        return self._max_samples

    def bandwidth(self):
         lb,ub,unit = self._bandwidth
         lb = lb*unit if not lb is None else None
         ub = ub*unit if not ub is None else None
         return Interval.type_infer(lb,ub)


    def set_values(self,values):
        self._values = list(values)
        return self

    def index(self,value):
        return self._values.index(value)

    def values(self):
        return self._values

    def set_constant(self):
        self._kind = DigitalProperties.ClockType.CONSTANT
        return self

    @property
    def is_constant(self):
        return self._is_constant

    def check(self):
        assert(not self._values is None)
        assert(not self._max_error is None)
        assert(self._kind != DigitalProperties.ClockType.UNKNOWN)
        return self
