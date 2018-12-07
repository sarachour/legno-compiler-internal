from moira.lib.bayes_inf import BayesianModel
import numpy as np
import itertools
from moira.db import ExperimentDB
from moira.lib.bbmodel import BlackBoxModel
import math

def sin_signal(model,ampl,freq_hz,phase,round_no,model_no,trials=10,n_cycles=1):
    inp_fun = "%f*math.sin(%f*t+%f)" % (ampl,freq_hz*2*math.pi,phase)
    period = 1.0/freq_hz
    for idx in range(0,model.n_outputs):
        inputs = [inp_fun]*model.n_inputs
        model.db.insert(round_no,
                        inputs=inputs,
                        output=idx,
                        trials=trials,
                        period=period,
                        num_periods=n_cycles,
                        model=model_no)

def dc_signal(model,value,round_no,model_no,trials=10):
    inp_fun = "%s" % value
    for idx in range(0,model.n_outputs):
        inputs = [inp_fun]*model.n_inputs
        model.db.insert(model_no,inputs,idx,trials,model=model_no)

def uniform_random_signal(model,amplitude):
    raise Exception("unimpl")

def execute(model):
    round_no = model.db.last_round()
    n_pending = len(list( \
                          itertools.chain( \
                                           model.db.get_by_status(ExperimentDB.Status.RAN),
                                           model.db.get_by_status(ExperimentDB.Status.PENDING))))
    if n_pending > 0:
        print("cannot model. experiments pending..")
        return
    if not round_no is None:
        if not model.db.paths.has_file(model.db.paths.model_file(round_no)):
            print("[no model] can't generate new inputs.")
            return

    print("round no: %s" % round_no)
    if round_no == None:
        sin_signal(model,ampl=1.0,freq_hz=100.0,phase=0.0,round_no=0,model_no=None,trials=5,n_cycles=1)
        sin_signal(model,ampl=1.0,freq_hz=100.0,phase=0.0,round_no=0,model_no=None,trials=5,n_cycles=20)
        sin_signal(model,ampl=0.3,freq_hz=100.0,phase=0.0,round_no=0,model_no=None,trials=5,n_cycles=1)
        sin_signal(model,ampl=0.3,freq_hz=100.0,phase=0.0,round_no=0,model_no=None,trials=5,n_cycles=20)
        #sin_signal(model,0.5,1.0,0.0,round_no=0,model_no=None)
        #sin_signal(model,1.0,2.0,0.0,round_no=0,model_no=None)
    elif round_no == 0:
        print("burn-in: dc signals")
        raise Exception("unknown")
        #dc_signal(model,0.0,round_no=1,model_no=0)
        #dc_signal(model,1.0,round_no=1,model_no=0)
        #dc_signal(model,-1.0,round_no=1,model_no=0)
    elif round_no == 1:
        print("reproduce signals")
        raise Exception("unknown")
        #dc_signal(model,0.0,round_no=2,model_no=1)
        #dc_signal(model,1.0,round_no=2,model_no=1)
        #dc_signal(model,-1.0,round_no=2,model_no=1)
        #sin_signal(model,1.0,1.0,0.0,round_no=2,model_no=1)
        #sin_signal(model,0.5,1.0,0.0,round_no=2,model_no=1)
        #sin_signal(model,1.0,2.0,0.0,round_no=2,model_no=1)

    else:
        raise Exception("unknown")

    if not round_no is None:
        bmod = BlackBoxModel.read(model.db.model_file(round_no))
        scores = []
        input("<adding input: [%s,%s]>" % (fmin,fmax))
    #for fmin,fmax,snr in bmod.variances():
    #    score = snr+(fmax-fmin)
    #    scores.append((score,fmin,fmax,snr))

    #scores.sort(key=lambda d:d[0])

    #for score,fmin,fmax,variance in scores:
    #    print("%s: [%s,%s] %s" % (score,fmin,fmax,variance))

    #_,fmin,fmax,_ = scores[0]
    #identity_func(model,fmin,fmax,round_no)
