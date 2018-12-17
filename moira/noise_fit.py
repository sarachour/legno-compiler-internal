import itertools
from moira.db import ExperimentDB
import lab_bench.analysis.det_xform as dx
import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import random
import json
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import scipy
import matplotlib.pyplot as plt
import os

import math

def get_dataset(dataset,filename=None):
    obj = {'R':[],'Fs':[],'As':[],'Fn':[],'An':[]}

    for (round_id,expid),data in dataset.items():
        if data is None:
            continue
        for datum in data:
            noise = datum.noise().autopower()
            output = datum.output().autopower()
            Fn = noise.freqs
            An = np.real(noise.phasors)

            Fs = output.freqs
            As = np.real(output.phasors)
            obj['Fs'].append(list(Fs))
            obj['Fn'].append(list(Fn))
            obj['As'].append(list(As))
            obj['An'].append(list(An))
            obj['R'].append(round_id)

    if not filename is None:
        print("-> writing <%s>" % filename)
        with open(filename,'w') as fh:
            fh.write(json.dumps(obj))

    return obj


def build_dataset(model,filename=None):
    data = {}

    if not filename is None and \
       os.path.exists(filename):
        with open(filename,'r') as fh:
            print("-> reading <%s>" % filename)
            return json.loads(fh.read())


    trial_dict = {}
    for ident,trials,this_round_no,period,n_periods,\
        inputs,output,model_id in \
        itertools.chain(\
            model.db.get_by_status(ExperimentDB.Status.FFTED)):
        trial_dict[ident] = trials
        freqs = []
        delays = []
        for trial in trials:
            print("==== %s / %d ==== "% (ident,trial))
            filepath = model.db.paths.freq_file(ident,trial)
            freqd = fq.FreqDataset.read(filepath)
            freqs.append(freqd)

        data[(this_round_no,ident)] = freqs

    return get_dataset(data,filename)


def preprocess_data(data,model):
    def compute_function(x,fs,vs):
        if len(fs) == 0:
            return np.array(list(map(
                lambda _ : [0],
                range(0,len(x))
            )))

        fxn_s = np.interp(x,fs,np.real(vs))
        #fxn_s = scipy.signal.hilbert(d_s)
        return np.real(fxn_s).reshape(-1,1)

    print("--- compute frequency range ---")
    Fn = data['Fn']
    Fs = data['Fs']
    n = 100000
    min_f,max_f = 1e10,0
    for d1,d2 in zip(Fn,Fs):
        min_f = min([min_f]+d1+d2)
        max_f = max([max_f]+d1+d2)

    print("--- compute log freqs ---")
    log_freqs = np.linspace(np.log10(min_f),\
                            np.log10(max_f),\
                            n)
    print("--- compute freqs ---")
    freqs = np.array(list(map(lambda lf: 10**lf, log_freqs)))

    data_by_round = {}
    for round_no in set(data['R']):
        print("==== round %d ====" % round_no)
        selector = [r <= round_no for r in data['R']]
        Fs = itertools.compress(data['Fs'],selector)
        Fn = itertools.compress(data['Fn'],selector)
        As = itertools.compress(data['As'],selector)
        An = itertools.compress(data['An'],selector)
        n = len(selector)
        print("--- compute signals ---")
        signals = np.array(list(map(lambda args:
                compute_function(freqs, *args), zip(Fs,As))))
        print("signal: %s" % str(signals.shape))
        print("--- compute noise ---")
        noises = np.array(list(map(lambda args:
                compute_function(freqs,*args), zip(Fn,An))))
        round_freqs = np.tile(freqs,n)
        print("noise: %s" % str(noises.shape))
        data_by_round[round_no] = (signals,noises)

    return freqs,data_by_round

def write_noise_model(model,noise_model,ident,trial):
    paths = model.db.paths
    noise_model.plot_offset(paths.plot_file(ident,trial,'offset'))
    noise_model.plot_slope(paths.plot_file(ident,trial,'slope'),0)
    noise_model.plot_num_samples(paths.plot_file(ident,trial,'nsamps'))

    filepath = model.db.paths.freq_file(ident,trial)
    freqd = fq.FreqDataset.read(filepath)
    noise = freqd.noise().autopower()
    output = freqd.output().autopower()
    noise_pred = noise_model.apply2(output.freqs,np.real(output.phasors))
    plt.loglog(noise.freqs,np.real(noise.phasors),label='data',\
               linewidth=0.5)
    plt.loglog(output.freqs,np.real(noise_pred),
               label='pred',linewidth=0.5,alpha=1.0)
    plt.legend()
    plt.savefig(paths.plot_file(ident,trial,'noise_pred'))
    plt.cla()
    noise_model.write(model.db.paths.noise_file(ident,trial))

def execute(model):
    n_pending = len(list(itertools.chain( \
        model.db.get_by_status(ExperimentDB.Status.PENDING),
        model.db.get_by_status(ExperimentDB.Status.RAN),
        model.db.get_by_status(ExperimentDB.Status.ALIGNED),
        model.db.get_by_status(ExperimentDB.Status.XFORMED)
    )))

    if n_pending > 0:
        print("cannot model. experiments pending..")
        return

    n_denoisable = len(list(itertools.chain( \
        model.db.get_by_status(ExperimentDB.Status.FFTED)
    )))
    if n_denoisable == 0:
        return


    tmpfile = 'data.json'
    data = build_dataset(model,tmpfile)
    freqs,data_by_round= preprocess_data(data,model)
    model_by_round = {}
    print("<<< Fitting Linear Model >>>")
    for round_no,(signals,noises) in data_by_round.items():
        print("=== Round %d ===" % round_no)
        locs,slopes,offsets,nsamps=dx.DetNoiseModel.fit_rr(freqs,
                                                           signals, \
                                                           noises,1)
        noise_model = dx.DetNoiseModel(locs,slopes,offsets,nsamps)
        model_by_round[round_no] = noise_model

    print("TODO: fit a symbolic curve to reduce complexity")
    #fit_symbolic_curve(model)
    for ident,trials,this_round_no,period,n_periods,\
        inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.FFTED):
        for trial in trials:
            write_noise_model(model,
                              model_by_round[this_round_no],\
                              ident,trial)
            model.db.set_status(ident,trial, \
                                ExperimentDB.Status.DENOISED)

    if not tmpfile is None:
        os.remove('data.json')
