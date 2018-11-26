import sys
import os
import numpy as np
import math
import pymc3 as pm
import matplotlib.pyplot as plt
from moira.db import ExperimentDB
from moira.lib.fv import FeatureVectorSet
import itertools
import lab_bench.analysis.waveform as wf
from moira.lib.bayes import BayesInference, BayesianModel

print('Running on PyMC3 v{}'.format(pm.__version__))

def reject_outliers(dataset,stdevs=2):
    data = list(dataset.values())
    delays = list(map(lambda ds: ds.delay,data))
    median = np.median(delays)
    deviation = list(map(lambda delay: abs(delay - median), delays))
    median_deviation = np.mean(deviation)
    thresh = deviation/median_deviation if median_deviation else 0
    return list(filter(lambda ds: abs(ds[1].delay-median)/median_deviation<stdevs,
                       dataset.items()))

# for vdiv: 0 and 3 are issues
# observation: low frequency signals are easy to align. maybe start with that
def infer_phase_delay_model(dataset):
    data = list(dataset.values())
    N = len(data)
    weight = lambda c: (c**2)
    # weighted mean
    mean = sum(map(lambda ds: ds.delay, data))/N
    std = math.sqrt(sum(map(lambda ds: ((ds.delay-mean)**2),data))/N)
    return mean,std

def infer_noise_model(idx,model,fv):
    bayes = BayesInference(fv,10000)
    dataset_name = "ampl"
    bayes.model_linear(dataset_name)
    bayes.print_model(dataset_name)
    bayes.variational_inference(dataset_name)
    bayes.save_loss_graph(dataset_name,model.db.model_graph(idx,'loss'))
    variances,parameters = bayes.model_variation(dataset_name)
    #bayes.save_accuracy_graph(dataset_name,model.db.model_graph(idx,'accuracy'))
    bmod = BayesianModel(fv.freqs)
    for (fmin,fmax),variance in variances.items():
        bmod.add_variance(fmin,fmax,variance)

    for param,(mean,stdev) in parameters.items():
        bmod.add_parameter(param,mean,stdev)

    return bmod

def execute(model):
    data = {}
    round_no = model.db.last_round()
    n_pending = len(list( \
                               itertools.chain( \
                                                model.db.get_by_status(ExperimentDB.Status.RAN),
                                                model.db.get_by_status(ExperimentDB.Status.PENDING))))
    if n_pending > 0:
        print("cannot model. experiments pending..")
        return

    if model.db.has_file(model.db.model_file(round_no)):
        print("cannot model. model exists.")
        return

    for ident,trials,inputs,output in \
        itertools.chain(\
                        model.db.get_by_status(ExperimentDB.Status.ALIGNED),
                        model.db.get_by_status(ExperimentDB.Status.USED)):
        for trial in trials:
            filepath = model.db.freq_file(ident,trial)
            fds = wf.FreqDataset.read(filepath)
            data[ident,trial] = fds

    if len(data.keys()) == 0:
        return

    usable_data = {}
    for (ident,trial),datum in reject_outliers(data,2):
        model.db.set_status(ident,trial,ExperimentDB.Status.USED)
        usable_data[(ident,trial)] = datum

    fv = FeatureVectorSet(usable_data.values(),n=100)
    for (ident,trial),datum in usable_data.items():
        fv.plot_features(datum.output,'ampl.png','phase.png')
        break
    #print("%d -> %d" % (len(data),len(good_data)))
    mean,std = infer_phase_delay_model(usable_data)
    bmod = infer_noise_model(round_no,model,fv)
    bmod.set_phase_model(mean,std)
    bmod.write(model.db.model_file(round_no))
    
    # should save to model file.
