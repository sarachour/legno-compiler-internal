import chip.units as units

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

    def set_bandwidth(self,lower,upper,unit):
        assert(lower is None or upper is None or lower <= upper)
        self._bandwidth = (lower,upper,unit)
        return self

    def set_interval(self,lower,upper,unit):
        assert(lower is None or upper is None or lower <= upper)
        self._bounds = (lower,upper,unit)
        return self

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

class DigitalProperties(Properties):

    def __init__(self):
        Properties.__init__(self,Properties.DIGITAL)
        self._values = None
        self._sample = (None,units.unknown)
        self._is_constant = None
        self._is_clocked = True
        self._delay = (None,units.unknown)

    def set_continuous(self):
        self._is_clocked = False
        #FIXME: store delay
        return self

    def interval(self):
        lb = min(self.values())
        ub = max(self.values())
        return IRange(lb,ub)


    def value(self,value):
        diff = map(lambda x : (x,abs(x-value)),self._values)
        choices = sorted(diff, key=lambda q: q[1])
        closest_value, error = choices[0]
        return closest_value

    def set_sample(self,rate,unit):
        self._sample = (rate,unit)
        self._is_constant = True
        self._is_clocked = True
        return self

    def set_values(self,values):
        self._values = list(values)
        return self

    def index(self,value):
        return self._values.index(value)

    def values(self):
        return self._values

    def set_constant(self):
        self._is_constant = True
        return self

    @property
    def is_constant(self):
        return self._is_constant

    def check(self):
        assert(not self._values is None)
        assert(self._is_constant or \
               not self._sample is None)
        return self
