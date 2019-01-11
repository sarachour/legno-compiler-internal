import chip.props as props
import chip.units as units
import numpy as np
import os

def equals(f1,f2):
    return abs(f1-f2) <= 1e-5

def datapath(filename):
    return "chip/hcdc/data/%s" % filename

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))


def make_ana_props(rng,lb,ub):
    assert(lb < ub)
    return props.AnalogProperties() \
                .set_interval(lb*rng.coeff(),
                              ub*rng.coeff(),
                              unit=units.uA)

def make_dig_props(rng,lb,ub,npts=256):
    start = lb*rng.coeff()
    end = ub*rng.coeff()
    hcdcv2_values = np.linspace(start,end,npts)
    info = props.DigitalProperties() \
                .set_values(hcdcv2_values) \
                .set_constant() \
                .check()
    return info

def apply_blacklist(options,blacklist):
    def in_blacklist(opt,blist):
        for entry in blacklist:
            match = True
            for ov,ev in zip(opt,entry):
                if not ev is None and ov != ev:
                    match = False

            if match:
                return True
        return False

    for opt in options:
        if in_blacklist(opt,blacklist):
            continue
        yield opt
