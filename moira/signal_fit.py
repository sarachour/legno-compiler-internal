import sys
import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import matplotlib.pyplot as plt
import os
import shutil
from moira.db import ExperimentDB
import scipy
import numpy as np
import json
import pymc3
import theano
import pickle
import pwlf
import sklearn


def apply_time_xform_model(align,dataset):
    dataset.output.time_shift(align.delay)
    dataset.output.truncate_before(0)
    dataset.output.truncate_after(dataset.reference.max_time())


def apply_signal_xform_model(sig_xform,paths,ident,trial):
    print("-> [%s:%d] read time xform model" % (ident,trial))
    align = wf.TimeXform.read(paths.time_xform_file(ident,trial))
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    print("-> [%s:%s] apply time transform" % (ident,trial))
    apply_time_xform_model(align,dataset)
    print("[%s:%s] apply signal transform" % (ident,trial))
    dataset.reference.apply_signal_xform(sig_xform)
    print("[%s:%s] plot transformed signals" % (ident,trial))
    dataset.plot(paths.plot_file(ident,trial,'disto'))
    print("[%s:%s] write model" % (ident,trial))
    sig_xform.write(paths.signal_xform_file(ident,trial))


def xform_build_dataset(paths,ident,trial):
    print("-> [%s:%d] read time xform" % (ident,trial))
    align = wf.TimeXform.read(paths.time_xform_file(ident,trial))
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    print("-> [%s:%s] apply time xform" % (ident,trial))
    apply_time_xform_model(align,dataset)
    npts = 200000
    ref,out = wf.TimeSeries.synchronize_time_deltas(dataset.reference,
                                                    dataset.output,
                                                    npts=npts)
    dataset.set_reference(ref.times,ref.values)
    dataset.set_output(out.times,out.values)
    print("-> [%s:%d] plot time-xformed waveforms" % (ident,trial))
    #dataset.plot(paths.plot_file(ident,trial,'align'))

    n = min(dataset.reference.n(), dataset.output.n())
    nsamps = 10000
    print("-> computed dataset size %s" % n)
    indices = np.random.choice(range(0,n),size=nsamps)
    xs = list(map(lambda i: dataset.reference.ith(i)[1], indices))
    ys = list(map(lambda i: dataset.output.ith(i)[1], indices))
    return xs,ys
''


def xform_fit_prepare_dataset(data):
    def sort(x,y):
        inds = np.argsort(x)
        xn = list(map(lambda i : x[i], inds))
        en = list(map(lambda i : y[i]-x[i], inds))
        yn = list(map(lambda i : y[i], inds))
        return xn,yn,en

    xtrain,xtest,ytrain,ytest = sklearn.model_selection\
                                       .train_test_split(data['X'],data['Y'])
    return sort(xtrain,ytrain),sort(xtest,ytest)

def xform_fit_build_sig_xform_from_linsegs(_breaks,pwl_model):
    print("-> build signal xform")
    breaks = list(_breaks)
    slopes = pwl_model.slopes
    ys= pwl_model.predict(breaks)
    # set end breaks to undefined
    xform = wf.SignalXform()
    for idx in range(0,len(breaks)-1):
        x0,x1 = breaks[idx],breaks[idx+1]
        m = slopes[idx]
        y0 = ys[idx]
        b = y0-m*x0
        l = x0 if idx > 0 else None
        u = x1 if idx + 1 < len(breaks)-1 else None
        xform.add_segment(l,u,m,b)


    return xform

def xform_fit_dataset(nsegs,data):
    print("-> computing test and train")
    (xs,ys,es),(xt,yt,et)=xform_fit_prepare_dataset(data)
    print("-> performing fit")
    pwl_model = pwlf.PiecewiseLinFit(xs,es)
    breaks = pwl_model.fit(nsegs)
    xform = xform_fit_build_sig_xform_from_linsegs(breaks,pwl_model)
    print(xform)
    xform.to_json()
    print("-> testing on holdout data")
    for seg in xform.segments:
        inds = list(map(lambda i : seg.contains(xt[i]),
                        range(0,len(xt))))
        xt_s = list(map(lambda i: xt[i],inds))
        et_s = list(map(lambda i: et[i],inds))
        etpred_s = list(map(lambda i: xform.error(xt[i]),inds))
        sumsq_err = sum(map(lambda t: (t[0]-t[1])**2,
                            zip(et_s,etpred_s)))
        seg.set_error(sumsq_err)
        print(seg)
        print("error:%s" % sumsq_err)
        print("-------")

    et_pred = list(map(lambda el: xform.error(el), xt))
    plt.plot(xt, et, marker=' ',label = 'data',linewidth=0.1)
    plt.plot(xt,et_pred,marker=' ',label='fit')
    plt.legend()
    plt.savefig('predictions.png')

    return xform

def execute(model):
    def compute_xformable_experiments():
        for ident,trials,round_no,period,n_cycles,\
            inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.XFORMED):
            for trial in trials:
                if not model.db.paths.has_file(model.db.paths.signal_xform_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.ALIGNED)

        for ident,trials,round_no,period,n_cycles,\
            inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.ALIGNED):
            for trial in trials:
                if model.db.paths.has_file(model.db.paths.signal_xform_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.XFORMED)
                    continue


                yield model.db.paths,ident,trial,period,period*n_cycles

    def compute_aligned_experiments():
        for ident,trial,_,round_no,period,n_cycles,\
            inputs,output,model_id in \
            model.db.all():
            if model.db.paths.has_file(model.db.paths.time_xform_file(ident,trial)):
                yield model.db.paths,ident,trial,period,period*n_cycles

    experiments = list(compute_xformable_experiments())
    if len(experiments) == 0:
        return

    xs, ys = [],[]
    for db,ident,trial,period,sim_time in compute_aligned_experiments():
        print("====  DATUM %s / %d ==== "% (ident,trial))
        x,y = xform_build_dataset(db,ident,trial)
        xs += x
        ys += y

    print("==== FIT PIECEWISE MODEL ===")
    xform = xform_fit_dataset(8,{'X':xs,'Y':ys})
    for db,ident,trial,period,sim_time in experiments:
        print("====  XFORM %s / %d ==== "% (ident,trial))
        apply_signal_xform_model(xform,db,ident,trial)
        model.db.set_status(ident,trial, \
                            ExperimentDB.Status.XFORMED)
