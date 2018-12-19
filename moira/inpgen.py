from moira.lib.bayes_inf import BayesianModel
import numpy as np
import itertools
from moira.db import ExperimentDB
from moira.lib.blackbox import BlackBoxModel
import math
import numpy as np
import fractions
import functools


def sin_signal(model,ampl,freq_hz,phase,round_no,model_no,trials=10,n_cycles=1):
    inp_fun = "%f*math.sin(%f*t+%f)" % (ampl,freq_hz*2*math.pi,phase)
    period = 1.0/freq_hz
    for idx in range(0,model.n_outputs):
        inputs = [inp_fun]*model.n_inputs
        model.db.insert(round_no=round_no,
                        inputs=inputs,
                        output=idx,
                        trials=trials,
                        period=period,
                        num_periods=n_cycles,
                        model=model_no)

def multi_sin_signal(model,ampls,freq_hzs,phases,round_no,model_no,trials=10,n_cycles=1):

    def inp_fun(ampl,freq_hz,phase):
        return "%f*math.sin(%f*t+%f)" % (ampl,freq_hz*2*math.pi,phase)


    weights = list(map(lambda a : a/sum(ampls), ampls))
    inp = "+".join(map(lambda args: inp_fun(*args),
                 zip(weights,freq_hzs,phases)))

    freq_hzs_frac = list(map(lambda f: fractions.Fraction(f), \
                             freq_hzs))
    beat_freq = functools.reduce(lambda f1,f2: fractions.gcd(f1,f2), \
                                 freq_hzs)
    beat_period = 1/float(beat_freq)
    for idx in range(0,model.n_outputs):
        inputs = [inp]*model.n_inputs
        model.db.insert(round_no=round_no,
                        inputs=inputs,
                        output=idx,
                        trials=trials,
                        period=beat_period,
                        num_periods=n_cycles,
                        model=model_no)


def random_periodic_signal(model,
                           max_freq, \
                           period, \
                           seed, \
                           round_no,\
                           model_no, \
                           trials=10, \
                           n_cycles=1):
    util.random_periodic_signal(seed,max_freq,period)
    raise Exception('f')

def dc_signal(model,value,round_no,model_no,trials=10,n_cycles=1):
    inp_fun = "%s" % value
    period = 0.01
    for idx in range(0,model.n_outputs):
        inputs = [inp_fun]*model.n_inputs
        model.db.insert(round_no=round_no,
                        inputs=inputs,
                        output=idx,
                        trials=trials,
                        period=period,
                        num_periods=n_cycles,
                        model=model_no)


def execute(model):
    round_no = model.db.last_round()
    n_pending = len(list( \
                          itertools.chain( \
                                           model.db.get_by_status(ExperimentDB.Status.RAN),
                                           model.db.get_by_status(ExperimentDB.Status.RAN),
                                           model.db.get_by_status(ExperimentDB.Status.ALIGNED),
                                           model.db.get_by_status(ExperimentDB.Status.FFTED)

                          )))
    if n_pending > 0:
        print("cannot model. experiments pending..")
        return
    if not round_no is None:
        if not model.db.paths.has_file(model.db.paths.model_file(round_no)):
            print("[no model] can't generate new inputs.")
            return

    print("round no: %s" % round_no)
    if round_no == None:
        sin_signal(model,ampl=1.0,freq_hz=500.0,phase=0.0,
                   round_no=0,model_no=None,trials=5,n_cycles=20)
        sin_signal(model,ampl=0.3,freq_hz=500.0,phase=0.0,
                   round_no=0,model_no=None,trials=5,n_cycles=20)

        sin_signal(model,ampl=1.0,freq_hz=100.0,phase=0.0,
                   round_no=0,model_no=None,trials=5,n_cycles=20)
        sin_signal(model,ampl=0.3,freq_hz=100.0,phase=0.0, \
                   round_no=0,model_no=None,trials=5,n_cycles=20)
        multi_sin_signal(
            model,ampls=[0.5,1.0],freq_hzs=[100.0,500.0],\
            phases=[0.0,0.0],round_no=0,model_no=0,
            trials=5,n_cycles=20
        )
        multi_sin_signal(
            model,ampls=[1.0,0.5],freq_hzs=[300.0,700.0],\
            phases=[0.0,0.0],round_no=0,model_no=0,
            trials=5,n_cycles=20
        )
        dc_signal(model,value=0.0,round_no=0,model_no=0,\
                  trials=5,n_cycles=20
        )
    elif round_no == 0:
         random_periodic_signal(model,
                                seed=0, \
                                freq_hz=10000.0, \
                                period=0.1, \
                                round_no=1, \
                                model_no=0, \
                                trials=5, \
                                n_cycles=20)

    else:
        raise Exception("unknown: only three rounds impl")

