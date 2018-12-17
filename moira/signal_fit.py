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
        xs = []
        ys = []
        for i in range(0,round_no+1):
            xs += list(data[i]['X'])
            ys += list(map(lambda args: args[0]-args[1], \
                           zip(data[i]['Y'],data[i]['X'])))

        return np.array(xs),np.array(ys)

    nbins = 1000
    xform_models = {}
    for round_no in data.keys():
        print("=== Fit Round %s ==" % round_no)
        print("-> computing dataset")
        xs,ys=build_round_dataset(data,round_no)
        bins = np.linspace(min(xs),max(xs),nbins)
        print(ys)
        ls = np.array(list(map(lambda x: \
                               bins[dx.find_index_in_sorted_array(bins,x)], \
                               xs.reshape(-1))))
        print("-> fitting model [offsets only]")
        locs,slopes,offsets,nsamps = dx.DetSignalXform.fit(
                                                           ls,
                                                           xs,
                                                           ys, 0)

        xform = dx.DetSignalXform(locs,slopes,offsets,nsamps)
        xform_models[round_no] = xform

    return xform_models

def compute_xformable_experiments(model):
    # downgrade xformed,ffted and dnoised to aligned, if we're
    # missing an xform file
    for ident,trials,round_no,period,n_cycles,\
        inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.ALIGNED):
        for trial in trials:
            yield ident,trial,round_no

def compute_time_xformed_experiments(model):
    for ident,trial,_,round_no,period,n_cycles,\
        inputs,output,model_id in \
        model.db.all():
        if model.db.paths.has_file(model.db.paths \
                                    .time_xform_file(ident,trial)):

            yield ident,trial,round_no

def apply_existing_signal_models(model):
    data_experiments = list(compute_time_xformed_experiments(model))
    update_experiments = list(compute_xformable_experiments(model))
    if len(update_experiments) == 0:
        return True

    xforms = {}
    for ident,trial,round_no in data_experiments:
        signal_file = model.db.paths.signal_xform_file(ident,trial)
        if model.db.paths.has_file(signal_file):
            print("==== GET XFORM [%d] %s / %d ==== "% (round_no,ident,trial))
            xforms[round_no] = dx.DetSignalXform.read(signal_file)

    for ident,trial,round_no in update_experiments:
        if not round_no in xforms:
            continue
        print("====  APPLY XFORM %s / %d ==== "% (ident,trial))
        apply_signal_xform_model(model, \
                                 xforms[round_no],ident,trial)
        model.db.set_status(ident,trial, \
                            ExperimentDB.Status.XFORMED)

    return False

def load_tmpfile(tmpfile):
    if not tmpfile is None and \
       os.path.exists(tmpfile):
        with open(tmpfile,'r') as fh:
            print("-> reading <%s>" % tmpfile)
            data = json.loads(fh.read())
            new_data = {}
            for round_no,datum in data.items():
                new_data[int(round_no)] = {}
                new_data[int(round_no)]['X'] = np.array(datum['X'])
                new_data[int(round_no)]['Y'] = np.array(datum['Y'])

            return new_data
    return None

def save_tmpfile(tmpfile,obj):
    if not tmpfile is None:
        print("-> writing <%s>" % tmpfile)
        with open(tmpfile,'w') as fh:
            fh.write(json.dumps(obj))

def remove_tmpfile(tmpfile):
    if not tmpfile is None:
        os.remove(tmpfile)

def fit_new_signal_models(model):
    data_experiments = list(compute_time_xformed_experiments(model))
    update_experiments = list(compute_xformable_experiments(model))
    tmpfile = 'data.json'
    if len(update_experiments) == 0:
        return

    data = load_tmpfile(tmpfile)
    if data is None:
        data = {}
        for ident,trial,round_no in data_experiments:
            print("====  DATUM [%d] %s / %d ==== "% (round_no,ident,trial))
            x,y = xform_build_dataset(model,ident,trial)
            if not round_no in data:
                data[round_no] = {'X':[],'Y':[]}

            data[round_no]['X'] += x
            data[round_no]['Y'] += y



        save_tmpfile(tmpfile,data)

    print("==== FIT XFORM ===")
    xforms = xform_fit_dataset(data)
    for ident,trial,round_no in update_experiments:
        if not round_no in xforms:
            continue
        print("====  APPLY XFORM %s / %d ==== "% (ident,trial))
        apply_signal_xform_model(model, \
                                 xforms[round_no],ident,trial)
        model.db.set_status(ident,trial, \
                            ExperimentDB.Status.XFORMED)

    remove_tmpfile(tmpfile)

def execute(model):
    n_pending = len(list(itertools.chain( \
        model.db.get_by_status(ExperimentDB.Status.PENDING),
        model.db.get_by_status(ExperimentDB.Status.RAN)
    )))

    if n_pending > 0:
        print("cannot model. experiments pending..")
        return

    if apply_existing_signal_models(model):
        return

    if fit_new_signal_models(model):
        return
