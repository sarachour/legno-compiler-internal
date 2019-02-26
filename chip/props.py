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

    def __init__(self):
        Properties.__init__(self,Properties.ANALOG)
        self._bounds = (None,None,units.unknown)
        self._bandwidth = (None,None,units.unknown)
        self._min = (None,units.unknown)

    def set_bandwidth(self,lower,upper,unit):
        assert(lower is None or upper is None or lower <= upper)
        self._bandwidth = (lower,upper,unit)
        return self

    def set_interval(self,lower,upper,unit):
        assert(lower is None or upper is None or lower <= upper)
        self._bounds = (lower,upper,unit)
        return self

    def set_min_signal(self,min_sig,units):
        self._min = (min_sig,units)

    def min_signal(self):
        sig,unit = self._min
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

class DigitalProperties(Properties):
    class Type(Enum):
        CLOCKED = "clocked"
        CONTINUOUS = "continuous"
        CONSTANT = "constant"
        UNKNOWN = "unknown"

    def __init__(self):
        Properties.__init__(self,Properties.DIGITAL)
        self._values = None
        self._max_error = None
        self._kind = DigitalProperties.Type.UNKNOWN
        # for clocked
        self._sample_rate = (None,units.unknown)
        self._max_samples = None
        # for continuous
        self._bandwidth = (None,units.unknown)

    def set_continuous(self,lb,ub,unit):
        self._kind = DigitalProperties.Type.CONTINUOUS
        self._bandwidth = (lb,ub,unit)
        return self

    def set_clocked(self,sample_rate,max_samples,unit):
        self._kind = DigitalProperties.Type.CLOCKED
        self._sample_rate = (sample_rate,unit)
        self._max_samples = max_samples
        return self

    def set_max_error(self,v):
        assert(v >= 0.0 and v < 1.0)
        self._max_error = v

    @property
    def max_error(self):
        return self._max_error

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

    @property
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
        self._kind = DigitalProperties.Type.CONSTANT
        return self

    @property
    def is_constant(self):
        return self._is_constant

    def check(self):
        assert(not self._values is None)
        assert(not self._max_error is None)
        assert(self._kind != DigitalProperties.Type.UNKNOWN)
        return self
