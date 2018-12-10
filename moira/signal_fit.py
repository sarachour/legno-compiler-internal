import sys
import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import matplotlib.pyplot as plt
import os
import shutil
from moira.db import ExperimentDB
from moira.lib.bbmodel import BlackBoxModel
import scipy
import numpy as np
import json


def xform_build_dataset(paths,ident,trial):
    print("-> [%s:%d] read align model" % (ident,trial))
    align = wf.TimeXform.read(paths.time_xform_file(ident,trial))
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    print("-> [%s:%s] apply alignment" % (ident,trial))
    apply_align_model(align,dataset)
    npts = 200000
    ref,out = wf.TimeSeries.synchronize_time_deltas(dataset.reference,
                                                    dataset.output,
                                                    npts=npts)
    dataset.set_reference(ref.times,ref.values)
    dataset.set_output(out.times,out.values)
    print("-> [%s:%d] plot aligned waveforms" % (ident,trial))
    #dataset.plot(paths.plot_file(ident,trial,'align'))

    n = min(dataset.reference.n(), dataset.output.n())
    nsamps = 10000
    print("-> computed dataset size %s" % n)
    indices = np.random.choice(range(0,n),size=nsamps)
    xs = list(map(lambda i: dataset.reference.ith(i)[1], indices))
    ys = list(map(lambda i: dataset.output.ith(i)[1], indices))
    return xs,ys

def xform_fit_dataset(xs,ys):
    parnames = wf.SignalXform.param_names()
    init = np.random.uniform(size=len(parnames))
    pars,pcov = scipy.optimize.curve_fit(wf.SignalXform.compute,xs,ys,p0=init)
    for name,value in (zip(parnames,pars)):
        print("val %s=%s" % (name,value))
    print(pcov)
    perr = np.sqrt(np.diag(pcov))
    for name,err in zip(parnames,perr):
        print("std %s=%s" % (name,err))

    sig_xform = wf.SignalXform(dict(zip(parnames,pars)))
    return sig_xform


def execute(model):
    def compute_xformable_experiments():
        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.XFORMED):
            for trial in trials:
                if not model.db.paths.has_file(model.db.paths.signal_xform_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.ALIGNED)

        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.ALIGNED):
            for trial in trials:
                if model.db.paths.has_file(model.db.paths.signal_xform_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.XFORMED)
                    continue


                yield model.db.paths,ident,trial,period,period*n_cycles

    def compute_aligned_experiments():
        for ident,trial,_,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.all():
            if model.db.paths.has_file(model.db.paths.time_xform_file(ident,trial)):
                yield model.db.paths,ident,trial,period,period*n_cycles

    experiments = list(compute_xformable_experiments())
    xs, ys = [],[]
    if len(experiments) > 0:
        for db,ident,trial,period,sim_time in compute_aligned_experiments():
            print("====  DATUM %s / %d ==== "% (ident,trial))
            x,y = xform_build_dataset(db,ident,trial)
            xs += x
            ys += y

        with open('data.json','w') as fh:
            fh.write(json.dumps({'x':xs,'y':ys}))

        input("continue")
        xform = xform_fit_dataset(xs,ys)
        for db,ident,trial,period,sim_time in experiments:
            print("====  XFORM %s / %d ==== "% (ident,trial))
            xform_apply_model(xform,db,ident,trial)
