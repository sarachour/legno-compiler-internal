import chip.props as props
import chip.units as units
import numpy as np
import os
import util.util as glbl_util
import lab_bench.lib.chipcmd.data as chipcmd
import ops.interval as interval

truncate = glbl_util.truncate
equals = glbl_util.equals

def datapath(filename):
    return "chip/hcdc/data/%s" % filename

def build_scale_model_coeff_cstr(cstrlst,allow_scale=False):
    contcstrlst = []
    for var,coeff in cstrlst:
        # do not allow scaling down, because it apparently behaves poorly.
        if coeff == 1.0:
            cstr = interval.Interval.type_infer(0.0,100.0)
            contcstrlst.append((var,cstr))
        elif allow_scale:
            cstr = interval.Interval.type_infer(0,0)
            contcstrlst.append((var,cstr))

    return contcstrlst


def build_scale_model_cstr(cstrlst,scale):
    contcstrlst = []
    for var,rng in cstrlst:
        if rng == chipcmd.RangeType.MED:
            cstr = interval.Interval.type_infer(0,scale*1.1)
        elif rng == chipcmd.RangeType.LOW:
            cstr = interval.Interval.type_infer(0,scale*0.11)
        elif rng == chipcmd.RangeType.HIGH:
            cstr = interval.Interval.type_infer(0,scale*10.1)

        contcstrlst.append((var,cstr))
    return contcstrlst

def make_ana_props(rng,lb,ub,min_sig):
    assert(lb < ub)
    prop = props.AnalogProperties() \
                .set_interval(lb*rng.coeff(),
                              ub*rng.coeff(),
                              unit=units.uA)
    prop.set_min_signal(min_sig,units.uA)
    return prop

def make_dig_props(rng,lb,ub,npts):
    start = lb*rng.coeff()
    end = ub*rng.coeff()
    hcdcv2_values = np.linspace(start,end,npts)
    info = props.DigitalProperties() \
                .set_values(hcdcv2_values)
    error = np.mean(np.diff(hcdcv2_values))
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
