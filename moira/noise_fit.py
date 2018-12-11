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

class SignalDependentNoiseModel:

    def __init__(self,param_names):
        self._params = dict(map(lambda name: (name,None), \
                                param_names))
        self._param_names = param_names

    def apply(self,freq,signal):
        raise Exception("unimplemented")

    def apply_all(self,f,xs):
        xps = []
        for x in xs:
            xps.append(self.apply(f,x))

        return np.concatenate(xps)

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

    def fit(self,freq,fs,fn,pn,pv):
        def underfit(x,xpred):
            normv = max(x)
            return np.where(x > xpred, (x-xpred)**2, (1.5*(xpred-x))**2)/normv

        self.set_params(dict(zip(pn,pv)))
        fn_pred = self.apply(freq,fs)
        return underfit(fn,fn_pred)

    def subtract(self,freq,fs,fn):
        new_fn = fn - self.apply(freq,fs)
        overapprox = sum(filter(lambda v: v < 0.0, new_fn))
        new_fn_pos = np.where(new_fn > 0.0, new_fn, 0.0)
        return overapprox,new_fn_pos

class MultExpSignalModel(SignalDependentNoiseModel):

    def __init__(self):
        SignalDependentNoiseModel.__init__(self,['a','b','n'])

    def initial(self):
        return [0.0,1.0,1.5]

    def apply(self,f,x):
        # s(f)*(x**n)
        a = self.param('a')
        b = self.param('b')
        n = self.param('n')
        c = a*f + b
        xp = c*x**n
        return xp


def subtractive_analysis(model):
    def compute_function(x,fs,vs):
        d_s = np.interp(x,fs,np.real(vs))
        fxn_s = scipy.signal.hilbert(d_s)
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
    signals = list(map(lambda t: compute_function(freqs,t[0],t[1]), \
                       zip(data['Fs'],data['As'])))
    noises = list(map(lambda t: compute_function(freqs,t[0],t[1]), \
    zip(data['Fn'],data['An'])))
    noises_flat = np.concatenate(noises)

    model = MultExpSignalModel()
    parnames = model.param_names()
    def model_apply(args,*params):
        model.set_params(dict(zip(parnames,params)))
        return model.apply_all(args[0],args[1])

    print("--- begin iterative fit---")
    for _ in range(0,15):
        print("---- optimize mult-exp---")
        results = []
        result,_ = scipy.optimize.curve_fit(model_apply,[freqs,signals],\
                                          noises_flat,\
                                          p0=model.initial())

        for i,(sig,noise) in enumerate(zip(signals,noises)):
            print("=== %d/%d ===" % (i,len(signals)))
            print(result)
            model.set_params(dict(zip(parnames,result)))
            plt.loglog(freqs, sig, 'b-', label='data')
            plt.savefig('hilbert_signal.png')
            plt.cla()

            plt.loglog(freqs, noise, 'b-', label='data')
            plt.loglog(freqs, model.apply(freqs,sig), 'r-',
                         label='fit')
            plt.savefig('hilbert_fit.png')
            plt.cla()
            error, new_vn = model.subtract(freqs,sig,noise)
            noises[i] = new_vn
            print("overapprox error: %s" % error)
            plt.loglog(freqs,new_vn)
            plt.savefig('hilbert_new_noise.png')
            plt.cla()
            input('<continue>')



def execute(model):
    #build_dataset(model)
    subtractive_analysis(model)
    raise Exception("stop here")
