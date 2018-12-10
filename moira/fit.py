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
import lab_bench.analysis.freq as fq
from moira.lib.bayes_inf import BayesInference
from moira.lib.bbmodel import BlackBoxModel
import json
import scipy
import random

print('Running on PyMC3 v{}'.format(pm.__version__))

# for vdiv: 0 and 3 are issues
# observation: low frequency signals are easy to align. maybe start with that
def infer_phase_delay_model(dataset):
    data= []
    for _,dels in dataset.values():
        data += dels

    N = len(data)
    weight = lambda c: (c**2)
    # weighted mean
    mean = np.mean(data)
    std = np.std(data)
    return mean,std


def write_dataset(dataset,test_train_split=0.0):
    from sklearn import tree
    import graphviz

    with open('dataset_test.json', 'w') as ftest, \
         open('dataset_train.json','w') as ftrain:

        for expid,(data,_) in dataset.items():
            if data is None:
                continue
            train_data = random.random() <= test_train_split
            for datum in data:
                Fn = datum.noise().freqs()
                An = list(map(lambda t: t[1],
                                datum.noise().phasors()))
                Pn = list(map(lambda t: t[2],
                                datum.noise().phasors()))

                Fs = datum.output().freqs()
                As = list(map(lambda t: t[1],
                              datum.output().phasors()))
                Ps =  list(map(lambda t: t[2],
                               datum.output().phasors()))


                row = {
                    'Fs':Fs,
                    'As':As,
                    'Ps':Ps,
                    'Fn':Fn,
                    'An':An,
                    'Pn':Pn
                }
                if not train_data:
                    ftrain.write(json.dumps(row))
                    ftrain.write('\n')
                else:
                    ftest.write(json.dumps(row))
                    ftest.write('\n')

def execute(model):
    data = {}
    round_no = model.db.last_round()
    #n_pending = len(list(itertools.chain( \
    #    model.db.get_by_status(ExperimentDB.Status.RAN),
    #    model.db.get_by_status(ExperimentDB.Status.PENDING))))

    n_pending = len(list(itertools.chain( \
        model.db.get_by_status(ExperimentDB.Status.PENDING))))

    if n_pending > 0:
        print("cannot model. experiments pending..")
        return

    #if model.db.has_file(model.db.model_file(round_no)):
    #    print("cannot model. model exists.")
    #    return

    trial_dict = {}
    for ident,trials,this_round_no,period,n_periods,inputs,output,model_id in \
        itertools.chain(\
            model.db.get_by_status(ExperimentDB.Status.FFTED),
            model.db.get_by_status(ExperimentDB.Status.USED)):
        burn_in = this_round_no < 1 and False

        trial_dict[ident] = trials
        freqs = []
        delays = []
        for trial in trials:
            print("==== %s / %d ==== "% (ident,trial))
            filepath = model.db.paths.freq_file(ident,trial)
            freqd = fq.FreqDataset.read(filepath)
            if not burn_in:
                freqs.append(freqd)

            delays.append(freqd.delay)

        if not burn_in:
            #freqd = fq.StochFreqDataset(map(lambda freq:freq.noise,freqs))
            #freqd.add_signal('out',map(lambda freq:freq.output, freqs))
            data[ident] = (freqs,delays)
        else:
            data[ident] = (None,delays)


    write_dataset(data,test_train_split=0.0)

    #delay_mean,delay_variance = infer_phase_delay_model(data)
    #bbmod.add_phase_model(delay_mean,delay_variance)
    #bbmod.write(model.db.model_file(round_no))
