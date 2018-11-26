from moira.lib.bayes import BayesianModel
import numpy as np


def identity_func(model,fmin,fmax,round_no):
    freq_s = np.random.uniform(fmin,fmax)
    freq_ms = freq_s / 1000.0
    print("freq: %s" % freq_ms)
    inp_fun = "1.0*sin(%s*t)" % freq_ms
    for idx in range(0,model.n_outputs):
        inputs = [inp_fun]*model.n_inputs
        model.db.insert(round_no+1,inputs,idx,10,model=round_no)

    print(inp_fun)

def execute(model):
    round_no = model.db.last_round()
    n_pending = len(list( \
                          itertools.chain( \
                                           model.db.get_by_status(ExperimentDB.Status.RAN),
                                           model.db.get_by_status(ExperimentDB.Status.PENDING))))
    if n_pending > 0:
        print("cannot model. experiments pending..")
        return

    bmod = BayesianModel.read(model.db.model_file(round_no))
    scores = []
    for fmin,fmax,snr in bmod.variances():
        score = snr+(fmax-fmin)
        scores.append((score,fmin,fmax,snr))

    scores.sort(key=lambda d:d[0])

    for score,fmin,fmax,variance in scores:
        print("%s: [%s,%s] %s" % (score,fmin,fmax,variance))

    _,fmin,fmax,_ = scores[0]
    input("<adding input: [%s,%s]>" % (fmin,fmax))
    identity_func(model,fmin,fmax,round_no)
