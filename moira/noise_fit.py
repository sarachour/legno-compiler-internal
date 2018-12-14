import itertools
from moira.db import ExperimentDB
from lab_bench.analysis.det_xform import DetNoiseModel
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
    obj = {'Fs':[],'As':[],'Fn':[],'An':[]}

    for expid,data in dataset.items():
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

        data[ident] = freqs

    return get_dataset(data,filename)


def preprocess_data(data,model):
    def compute_function(x,fs,vs):
        fxn_s = np.interp(x,fs,np.real(vs))
        #fxn_s = scipy.signal.hilbert(d_s)
        return np.real(fxn_s)


    print("--- compute frequency range ---")
    min_f = min(map(lambda freqs: min(freqs), data['Fn']+data['Fs']))
    max_f = max(map(lambda freqs: max(freqs), data['Fn']+data['Fs']))
    n = 100000
    log_freqs = np.linspace(np.log10(min_f),\
                            np.log10(max_f),\
                            n)
    print("--- compute freqs ---")
    freqs = np.array(list(map(lambda lf: 10**lf, log_freqs)))
    print("--- compute signals ---")
    signals = np.array(list(map(lambda t: compute_function(freqs,\
                                                           t[0],t[1]), \
                                zip(data['Fs'],data['As']))))
    print("--- compute noise ---")
    noises = np.array(list(map(lambda t: compute_function(freqs,t[0],t[1]), \
                               zip(data['Fn'],data['An']))))
    return freqs,signals,noises

def multi_linear(data,model):
    freqs,signals,noises = preprocess_data(data,model)

    dx.DetNoiseModel.fit(freqs,signals,noises,1)
    raise Exception("hmm.")
    n = len(signals)
    nf = len(freqs)
    nsigs = 1
    S = np.zeros((n,nsigs))
    N = np.zeros(n).reshape(-1,1)
    def update_slice(j):
        for i in range(0,n):
            S[i][0] = signals[i][j]
            N[i][0] = noises[i][j]

        return S,N

    M = np.zeros((nsigs,nf))
    B = np.zeros(nf)
    E = np.zeros(nf)
    print("--- begin iterative fit---")
    for i in range(0,len(freqs)):
        if i % 1000 == 0:
            print("-> %d" % i)

        update_slice(i)
        regr = linear_model.LinearRegression()
        regr.fit(S,N)
        N_pred = regr.predict(S)
        error = mean_squared_error(N, N_pred)
        for k in range(0,nsigs):
            M[k][i] = regr.coef_[0][k]
        B[i] = regr.intercept_[0]
        E[i] = error

    for i in range(0,nsigs):
        plt.loglog(freqs,M[i],label='slope')
        plt.savefig('coeff_m%d.png' % i)
        plt.cla()

    plt.loglog(freqs,B,label='intercept')
    plt.savefig('coeff_b.png')
    plt.cla()

    plt.loglog(freqs,E,label='error')
    plt.savefig('error.png')
    plt.cla()

    for idx,(signal,noise) in enumerate(zip(signals,noises)):
        N_pred = M[0]*signal+B
        plt.loglog(freqs,noise,label='obs')
        plt.loglog(freqs,N_pred,label='pred',alpha=0.5)
        plt.savefig('pred_%d.png' % idx)
        plt.cla()

    return LinearNoiseModel(freqs,M,B,E)


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
        print("no noise models to infer")
        return



    tmpfile = 'data.json'
    #tmpfile = None
    data = build_dataset(model,tmpfile)
    noise_model= multi_linear(data,model)
    print("TODO: fit a symbolic curve to reduce complexity")
    #fit_symbolic_curve(model)
    for ident,trials,this_round_no,period,n_periods,\
        inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.FFTED):
        for trial in trials:
            noise_model.write(model.db.paths.noise_file(ident,trial))
            model.db.set_status(ident,trial, \
                                ExperimentDB.Status.DENOISED)

    if not tmpfile is None:
        os.remove('data.json')
