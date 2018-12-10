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
import pymc3
import theano
import pickle


def apply_align_model(align,dataset):
    dataset.output.time_shift(align.delay)
    dataset.output.truncate_before(0)
    dataset.output.truncate_after(dataset.reference.max_time())


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
'''
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
'''


def gen_parameters(idx):
    params = {}
    params['A'] = pymc3.Normal('A_%d' % (idx),0.0,1e-1)
    params['B'] = pymc3.Normal('B_%d' % (idx),0.0,1e-1)
    params['eps'] = pymc3.HalfNormal('E_%d' % (idx),1e-1)
    return params


def generate_variables(n):
    vals_vs = np.ones((n))
    vs = {}
    vs['X'] = theano.shared(vals_vs.astype(float))
    vs['Y'] = theano.shared(vals_vs.astype(float))
    return vs

def generate_linear_model(n):
    pars = gen_parameters(0)
    variables = generate_variables(n)
    one = theano.tensor.constant(1)
    mean = pars['B'] + (pars['A']+one)*variables['X']
    variance = pars['eps']
    model = pymc3.Normal("DistoModel",
                        mean,
                        variance,
                        observed=variables['Y'])
    return variables,pars,model


def test_model(model):
    for _ in range(0,5):
        print("======")
        for RV in model.basic_RVs:
            log_prob = RV.logp(model.test_point)
            print(RV.name, log_prob)
            if np.isinf(log_prob):
                raise Exception("found infinite log prob with test point.")

def print_params(params):
    for k,v in params.items():
        print("%s = %s" % (k,v))
    print("-------")


def plot_stats(basename,trace):
    ax = pymc3.plot_posterior(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_posterior.png' % basename)
    plt.cla()

    ax = pymc3.densityplot(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_density.png' % basename)
    plt.cla()

    ax = pymc3.energyplot(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_energy.png' % basename)
    plt.cla()

    ax = pymc3.autocorrplot(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_autocorr.png' % basename)
    plt.cla()

    ax = pymc3.traceplot(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_traceplot.png' % basename)
    plt.cla()

def save_model(model_name,trace, network):
    with open ('%s.pkl' % model_name, 'wb') as buff:
        pickle.dump ({'model': network, 'trace': trace}, buff)


def gen_model(model_name,data,n,approximate=False):
    with pymc3.Model() as model:

        #vs,gm = generate_binned_model(1,n,m_sig,m_noise)
        variables,parameters,obs_dist = generate_linear_model(n)
        print('--- model generated ---')
        for parname in parameters:
            print("par %s = %s" % (parname,parameters[parname]))
        for varname in variables:
            print("var %s" % varname)
            variables[varname].set_value(data[varname])

        test_model(model)
        print('--- values set ---')
        params = pymc3.find_MAP()
        print('--- initial ---')
        print_params(params)
        if approximate:
            print("--- approximate ---")
            inference = pymc3.ADVI()
            #niters = 50000
            niters = 20000
            approx = pymc3.fit(niters,method=inference)
            plt.plot(approx.hist)
            plt.savefig('%s_loss.png' % model_name)
            plt.clf()
            trace = approx.sample()
        else:
            trace = pymc3.sample(4000)

        save_model(model_name,trace,model)
        print(trace)
        plot_stats(model_name,trace)


def xform_fit_dataset(xs,ys):
    data = {'X':xs,'Y':ys}
    gen_model('disto',data,n=len(xs),approximate=True)


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
    if len(experiments) == 0:
        return

    xs, ys = [],[]
    '''
    for db,ident,trial,period,sim_time in compute_aligned_experiments():
        print("====  DATUM %s / %d ==== "% (ident,trial))
        x,y = xform_build_dataset(db,ident,trial)
        xs += x
        ys += y

    with open('data.json','w') as fh:
        fh.write(json.dumps({'x':xs,'y':ys}))
    '''
    with open('data.json','r') as fh:
        dat = json.loads(fh.read())
        xs = dat['x']
        ys = dat['y']

    model = xform_fit_dataset(xs,ys)
    xform_evaluate_dataset(model)

    '''
    xform = xform_fit_dataset(xs,ys)
    for db,ident,trial,period,sim_time in experiments:
        print("====  XFORM %s / %d ==== "% (ident,trial))
        xform_apply_model(xform,db,ident,trial)
    '''
