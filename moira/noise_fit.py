import itertools
from moira.db import ExperimentDB
import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import random
import json

def write_dataset(dataset,test_train_split=0.0):
    from sklearn import tree
    import graphviz

    with open('dataset_test.json', 'w') as ftest, \
         open('dataset_train.json','w') as ftrain:

        for expid,data in dataset.items():
            if data is None:
                continue
            train_data = random.random() <= test_train_split
            for datum in data:
                noise = datum.noise().autopower()
                output = datum.output().autopower()
                Fn = noise.freqs()
                An = list(map(lambda t: t[1],
                                noise.phasors()))
                Pn = noise.power()

                Fs = output.freqs()
                As = list(map(lambda t: t[1],
                              output.phasors()))
                Ps = output.power()

                row = {
                    'Fs':Fs,
                    'Ps':Ps,
                    'As':As,
                    'Fn':Fn,
                    'Pn':Pn,
                    'An':An
                }
                if not train_data:
                    ftrain.write(json.dumps(row))
                    ftrain.write('\n')
                else:
                    ftest.write(json.dumps(row))
                    ftest.write('\n')


def build_dataset(model):
    data = {}
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
    for ident,trials,this_round_no,period,n_periods,\
        inputs,output,model_id in \
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


        if not burn_in:
            data[ident] = freqs


    write_dataset(data,test_train_split=0.0)

def read_dataset(name):
    data = {'Ps':[],'Fs':[],'As':[],'Pn':[],'Fn':[],'An':[]}
    with open(name,'r') as fh:
        for row in fh:
            datum = json.loads(row)
            for key in data.keys():
                data[key].append(datum[key])


    return data

from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import scipy
import matplotlib.pyplot as plt
import seaborn as sns

def plot_powers(data):
    n = len(data['Ps'])
    inds = np.argsort(data['Ps'])
    Ps = list(map(lambda i: data['Ps'][i], \
                  range(0,n)))
    Pn = list(map(lambda i: data['Pn'][i], \
                  range(0,n)))

    plt.scatter(Ps,Pn)
    plt.savefig('power_relation.png')
    plt.clf()
    score = np.corrcoef(Ps,Pn)
    print("corr: %s" % score)

def compute_bounds(dataset):
    minbnd = min(map(lambda datum: min(datum),dataset))
    maxbnd = max(map(lambda datum: max(datum),dataset))
    return minbnd,maxbnd

def compute_power_dataset(freqs,ampls,lb,ub):
    powers = []
    for freq,ampl in zip(freqs,ampls):
        indices = list(filter(lambda i: freq[i] >= lb and freq[i]< ub, \
                              range(0,len(freq))))

        if len(indices) == 0:
            power = 0.0
        else:
            power = sum(map(lambda i: ampl[i],indices))
        powers.append(power)

    return powers

class NoiseModel:

    def __init__(self,name,param_names):
        self._name = name
        self._params = dict(map(lambda name: (name,None), \
                                param_names))
        self._param_names = param_names

    @property
    def name(self):
        return self._name

    def params(self):
        return self._params.items()

    def param(self,name):
        assert(not self._params[name] is None)
        return self._params[name]

    def initial(self):
        return np.random.uniform(0.0,1.0,len(self._params.keys()))

    def param_names(self):
        return self._param_names

    def set_params(self,pars):
        for k in self._params.keys():
            if not (k in pars):
                raise Exception("%s not in pars" % k)
            self._params[k] = pars[k]

class UncorrelatedNoiseModel(NoiseModel):
    def __init__(self,name,param_names):
        NoiseModel.__init__(self,name,param_names)
        self._params = dict(map(lambda name: (name,None), \
                                param_names))
        self._param_names = param_names

    def apply(self,freq):
        raise Exception("unimplemented")

    def apply_all(self,f,n):
        xps = []
        xp = self.apply(f)
        for _ in range(0,n):
            xps.append(xp)

        result = np.concatenate(xps)
        print(result.shape)
        return result

    def subtract(self,freq,fn):
        new_fn = fn - self.apply(freq)
        overapprox = sum(filter(lambda v: v < 0.0, new_fn))
        new_fn_pos = np.where(new_fn > 0.0, new_fn, 0.0)
        return overapprox,new_fn_pos

class SignalDependentNoiseModel(NoiseModel):

    def __init__(self,name,param_names):
        NoiseModel.__init__(self,name,param_names)

    def apply(self,freq,signal):
        raise Exception("unimplemented")

    def apply_all(self,f,xs):
        xps = []
        for x in xs:
            xps.append(self.apply(f,x))

        return np.concatenate(xps)

    def subtract(self,freq,fs,fn):
        new_fn = fn - self.apply(freq,fs)
        overapprox = sum(filter(lambda v: v < 0.0, new_fn))
        new_fn_pos = np.where(new_fn > 0.0, new_fn, 0.0)
        return overapprox,new_fn_pos

class MultExpSignalModel(SignalDependentNoiseModel):

    def __init__(self,degree=1):
        params = []
        self.degree = degree
        for i in range(0,degree):
            params.append('a%d' % i)
            params.append('b%d' % i)
            params.append('c%d' % i)

        SignalDependentNoiseModel.__init__(self,'mult-exp-sig',params)

    def apply(self,f,x):
        # (a*f+b)*(x)
        i=0
        a = self.param('a%d' % i)
        b = self.param('b%d' % i)
        c = self.param('c%d' % i)
        xp = a*x + b*f + c
        return xp

class RecBiasModel(UncorrelatedNoiseModel):

    def __init__(self):
        UncorrelatedNoiseModel.__init__(self,'rec-bias',['a','b','c'])

    def apply(self,f):
        a = self.param('a')
        b = self.param('b')
        c = self.param('c')
        pred  = b*1.0/f + a*f
        return pred

def xform(sigs,fn):
    for sig in sigs:
        yield fn(sig)

def debug_plots(model,freqs,sig,noise,new_noise):
    plt.loglog(freqs, sig, 'b-', label='sig')
    plt.loglog(freqs, noise, 'b-', label='noise')
    plt.legend()
    plt.savefig('hilbert_signal.png')
    plt.cla()

    plt.loglog(freqs, noise, 'b-', label='data')
    if isinstance(model,UncorrelatedNoiseModel):
        noise_pred = model.apply(freqs)
    else:
        noise_pred = model.apply(freqs,sig)
    plt.loglog(freqs, noise_pred, 'r-', label='fit')
    plt.savefig('hilbert_fit.png')
    plt.cla()
    plt.loglog(freqs,new_noise)
    plt.savefig('hilbert_new_noise.png')
    plt.cla()
    input("<continue>")

def preprocess_data(model):
    def compute_function(x,fs,vs):
        fxn_s = np.interp(x,fs,np.real(vs))
        #fxn_s = scipy.signal.hilbert(d_s)
        return np.real(fxn_s)

    print("--- read dataset ---")
    data = read_dataset('dataset_train.json')

    print("--- compute frequency range ---")
    min_f = min(map(lambda freqs: min(freqs), data['Fn']+data['Fs']))
    max_f = max(map(lambda freqs: max(freqs), data['Fn']+data['Fs']))
    n = 100000
    log_freqs = np.linspace(np.log10(min_f),\
                            np.log10(max_f),\
                            n)
    freqs = np.array(list(map(lambda lf: 10**lf, log_freqs)))
    print("--- compute dataset ---")
    signals = np.array(list(map(lambda t: compute_function(freqs,t[0],t[1]), \
                                zip(data['Fs'],data['As']))))
    noises = np.array(list(map(lambda t: compute_function(freqs,t[0],t[1]), \
                               zip(data['Fn'],data['An']))))
    return freqs,signals,noises

class ValueGridSegment:

    def __init__(self,n=3):
        self.n = n
        return

    def bins(self,min_val,max_val,log=True):
        n = self.n
        if log:
            min_val = max(1e-20,min_val)
            log_vals= np.linspace(np.log10(min_val),\
                                  np.log10(max_val),\
                                  n)
            vals = np.array(list(map(lambda lf: 10**lf, log_vals)))
        else:
            vals= np.linspace(min_val,max_val,n)

        for i in range(0,len(vals)-1):
            yield vals[i],vals[i+1]

    def get_indices(self,low,high,data):
        inds = []
        n = 0
        for i in range(0,len(data)):
            subinds = list(filter(lambda j : data[i][j] >= low \
                                  and data[i][j] <= high, \
                               range(0,len(data[i]))
            ))
            n += len(subinds)
            inds.append(subinds)

        return n,inds

    def apply_indices(self,data,inds):
        new_data = []
        for i in range(0,len(data)):
            if len(inds[i]) > 0:
                new_datum = list(map(lambda x: data[i][x], inds[i]))
            else:
                new_datum = []
            new_data.append(np.array(new_datum))

        return np.array(new_data)

    def set_indices(self,data,inds,new_data):
        for i,subarr in enumerate(inds):
            for sj,j in enumerate(subarr):
                data[i][j] = new_data[i][sj]

    def segment(self,freqs,signal,noise,log=True):
        for low,hi in self.bins(np.amin(signal),np.amax(signal)):
            n,idxs = self.get_indices(low,hi,signal)
            sub_freqs = self.apply_indices(freqs,idxs)
            sub_signals = self.apply_indices(signal,idxs)
            sub_noise = self.apply_indices(noise,idxs)
            yield n,(low,hi),idxs,sub_freqs,sub_signals,sub_noise

def subtractive_analysis(model):
    _freqs,signals,noises = preprocess_data(model)
    n = len(signals)
    freqs = np.array([_freqs]*n)
    print("--- begin iterative fit---")
    sig_models = [
        MultExpSignalModel(),
    ]
    seg_models = [
        ValueGridSegment()
    ]
    uncorr_models = [
        RecBiasModel()
    ]
    for model in sig_models:
        parnames = model.param_names()
        def model_apply(args,*params):
            model.set_params(dict(zip(parnames,params)))
            return model.apply(args[0],args[1])

        for seg in seg_models:
            for nels,binv,inds,freq_i,signal_i,noise_i in \
                seg.segment(freqs,signals,noises):
                if nels < 100*n:
                    continue

                print("==== BIN %s ====" % str(binv))
                Fi = np.concatenate(freq_i)
                Si = np.concatenate(signal_i)
                Ni = np.concatenate(noise_i)
                result,_ = scipy.optimize.curve_fit(model_apply,[Fi,Si],Ni, \
                                                    p0=model.initial())

                for j,(freq_i_j,signal_i_j,noise_i_j) in \
                    enumerate(zip(freq_i,signal_i,noise_i)):
                    print("=== %d/%d ===" % (j,len(signal_i)))
                    for pname,pval in model.params():
                        print("%s = %s" % (pname,pval))
                        print("----------")
                    error, noise_i_j_new = model.subtract(np.array(freq_i_j),signal_i_j,noise_i_j)
                    print("overapprox error: %s" % error)
                    debug_plots(model,freq_i_j,signal_i_j,noise_i_j,noise_i_j_new)
                    noise_i[j] = noise_i_j_new

                seg.set_indices(noises,inds,noise_i)
'''
    for model in uncorr_models:
        parnames = model.param_names()
        def model_apply(freqs,*params):
            model.set_params(dict(zip(parnames,params)))
            return model.apply_all(freqs,len(noises))

        print("---- optimize %s ---" % model.name)
        results = []
        xformed_signals = list(xform(signals, lambda x: x))
        parvalues,_ = scipy.optimize.curve_fit(model_apply,freqs,\
                                          noises_flat,\
                                          p0=model.initial())

        for i,(sig,noise) in enumerate(zip(xformed_signals,noises)):
            print("=== %d/%d ===" % (i,len(signals)))
            model.set_params(dict(zip(parnames,parvalues)))
            for pname,pval in model.params():
                print("%s = %s" % (pname,pval))
            print("----------")
            error, new_noise = model.subtract(freqs,noise)
            print("overapprox error: %s" % error)
            debug_plots(model,freqs,sig,noise,new_noise)
            noises[i] = new_vn
'''

from GPyOpt.methods import BayesianOptimization
import GPyOpt

def multi_linear(model):
    freqs,signals,noises = preprocess_data(model)
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

    slopes = {}
    for i in range(0,nsigs):
        slopes[i] = list(M[i])
    data = {
        'slope':slopes,
        'intercept':list(B),
        'error':list(E),
        'freqs':list(freqs)
    }
    with open('noise_model.json', 'w') as fh:
        fh.write(json.dumps(data))


def fit_symbolic(model):
    with open('noise_model.json', 'r') as fh:
        precise_model = json.loads(fh.read())


def execute(model):
    #build_dataset(model)
    #multi_linear(model)
    fit_symbolic(model)
    #subtractive_analysis(model)
    raise Exception("stop here")
