import sys
import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import matplotlib.pyplot as plt
import lab_bench.analysis.det_xform as dx
import os
import shutil
from moira.db import ExperimentDB
import scipy
import numpy as np
import json
import itertools

def apply_time_xform_model(align,dataset):
    dataset.output.time_shift(align.delay)
    dataset.output.truncate_before(0)
    dataset.output.truncate_after(dataset.reference.max_time())


def apply_signal_xform_model(model,sig_xform,ident,trial):
    paths = model.db.paths
    print("-> [%s:%d] read time xform model" % (ident,trial))
    align = dx.DetTimeXform.read(paths.time_xform_file(ident,trial))
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    print("-> [%s:%s] apply time transform" % (ident,trial))
    apply_time_xform_model(align,dataset)

    sig_xform.plot_offset(paths.plot_file(ident,trial,'offset'))
    sig_xform.plot_num_samples(paths.plot_file(ident,trial,'nsamps'))
    print("[%s:%s] apply signal transform" % (ident,trial))
    dataset.reference.apply_signal_xform(sig_xform)
    print("[%s:%s] plot transformed signals" % (ident,trial))
    dataset.plot(paths.plot_file(ident,trial,'disto'))
    print("[%s:%s] write model" % (ident,trial))
    sig_xform.write(paths.signal_xform_file(ident,trial))


def xform_build_dataset(model,ident,trial):
    paths = model.db.paths
    print("-> [%s:%d] read time xform" % (ident,trial))
    align = dx.DetTimeXform.read(paths.time_xform_file(ident,trial))
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    print("-> [%s:%s] apply time xform" % (ident,trial))
    apply_time_xform_model(align,dataset)
    print("-> [%s:%s] synchronize time xform" % (ident,trial))
    npts = 500000
    ref,out = wf.TimeSeries.synchronize_time_deltas(dataset.reference,
                                                    dataset.output,
                                                    npts=npts)
    dataset.set_reference(ref.times,ref.values)
    dataset.set_output(out.times,out.values)
    print("-> [%s:%d] plot time-xformed waveforms" % (ident,trial))
    dataset.plot(paths.plot_file(ident,trial,'align'))

    n = min(dataset.reference.n(), dataset.output.n())
    nsamps = 10000
    print("-> computed dataset size %s" % n)
    indices = np.random.choice(range(0,n),size=nsamps)
    xs = list(map(lambda i: [dataset.reference.ith(i)[1]], indices))
    ys = list(map(lambda i: dataset.output.ith(i)[1], indices))
    return xs,ys
''


def xform_fit_dataset(data):
    def build_round_dataset(data,round_no):
        ls = []
        xs = []
        ys = []
        for i in range(0,round_no+1):
            ls += data[i]['X']
            xs += list(map(lambda _ : [], range(len(data[i]['X']))))
            ys += list(map(lambda args: args[0]-args[1], \
                           zip(data[i]['Y'],data[i]['X'])))

        #xtrain,xtest,ytrain,ytest = sklearn.model_selection\
        #                                    .train_test_split(xs,ys)
        #return xtrain,ytrain,xtest,ytest
        return np.array(ls),np.array(xs),np.array(ys)

    nbins = 10000
    xform_models = {}
    for round_no in data.keys():
        print("=== Fit Round %d ==" % round_no)
        print("-> computing dataset")
        ls,xs,ys=build_round_dataset(data,round_no)
        xdim = len(xs[0])
        ls_trunc = list(map(lambda x: dx.sigfig(x,3),ls.reshape(-1)))
        print("-> fitting model")
        locs,slopes,offsets,nsamps = dx.DetSignalXform.fit(
                                                           ls_trunc,
                                                           xs,
                                                           ys, xdim)

        xform = dx.DetSignalXform(locs,slopes,offsets,nsamps)
        xform_models[round_no] = xform

    return xform_models

def execute(model):
    def compute_xformable_experiments():
        # downgrade xformed,ffted and dnoised to aligned, if we're
        # missing an xform file
        for ident,trials,round_no,period,n_cycles,\
            inputs,output,model_id in \
                model.db.get_by_status(ExperimentDB.Status.ALIGNED):
            for trial in trials:
                yield ident,trial,round_no

    def compute_time_xformed_experiments():
        for ident,trial,_,round_no,period,n_cycles,\
            inputs,output,model_id in \
            model.db.all():
            if model.db.paths.has_file(model.db.paths \
                                       .time_xform_file(ident,trial)):

                yield ident,trial,round_no

    n_pending = len(list(itertools.chain( \
        model.db.get_by_status(ExperimentDB.Status.PENDING),
        model.db.get_by_status(ExperimentDB.Status.RAN)
    )))

    if n_pending > 0:
        print("cannot model. experiments pending..")
        return

    data_experiments = list(compute_time_xformed_experiments())
    update_experiments = list(compute_xformable_experiments())
    if len(update_experiments) == 0:
        return

    data = {}
    for ident,trial,round_no in data_experiments:
        print("====  DATUM [%d] %s / %d ==== "% (round_no,ident,trial))
        x,y = xform_build_dataset(model,ident,trial)
        if not round_no in data:
            data[round_no] = {'X':[],'Y':[]}

        data[round_no]['X'] += x
        data[round_no]['Y'] += y

    print("==== FIT PIECEWISE MODEL ===")
    xforms = xform_fit_dataset(data)
    for ident,trial,round_no in update_experiments:
        if not round_no in xforms:
            continue
        print("====  XFORM %s / %d ==== "% (ident,trial))
        apply_signal_xform_model(model, \
                                 xforms[round_no],ident,trial)
        model.db.set_status(ident,trial, \
                            ExperimentDB.Status.XFORMED)
