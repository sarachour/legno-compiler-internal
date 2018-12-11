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

    def param(self,name):
        assert(not self._params[name] is None)
        return self._params[name]

    def initial(self):
        return np.random.uniform(0.0,1.0,len(self._params.keys()))

    def param_names(self):
        return self._param_names

    def set_params(self,pars):
        for k in self._params.keys():
            assert(k in pars)
            self._params[k] = pars[k]

    def fit(self,freq,fs,fn,pn,pv):
        def underfit(x,xpred):
            return np.where(x > xpred, (x-xpred)**2, (2*x+xpred)**2)

        self.set_params(dict(zip(pn,pv)))
        fn_pred = self.apply(freq,fs)
        return underfit(fn,fn_pred)

class MultExpSignalModel(SignalDependentNoiseModel):

    def __init__(self):
        SignalDependentNoiseModel.__init__(self,['c', 'n'])

    def apply(self,f,x):
        c = self.param('c')
        n = self.param('n')
        return c*(x**n)

def subtractive_analysis(model):
    def under(x,xpred):
        return np.where(x > xpred, (x-xpred)**2, (2*x+xpred)**2)

    def model_scale(freqs,fs,slope,power):
         fn_pred = slope*(fs**power)
         return fn_pred

    def fit_scale(freqs,fs,fn,slope,offset):
        fn_pred = model_scale(freqs,fs,slope,offset)
        return under(fn,fn_pred)

    def compute_function(x,fs,vs):
        d_s = np.interp(x,fs,np.real(vs))
        #fxn_s = scipy.signal.hilbert(d_s)
        return np.real(d_s)

    print("--- read dataset ---")
    data = read_dataset('dataset_train_one.json')
    print("--- analyze data ---")
    for fs,vs,fn,vn in zip(data['Fs'],data['As'], \
                           data['Fn'],data['An']):

        print("compute range")
        max_f = max(max(fs),max(fn))
        min_f = min(min(fs),min(fn))
        print("compute log freqs")
        log_freqs = np.linspace(np.log10(min_f),\
                                np.log10(max_f),\
                                1000000)
        print("compute freqs")
        freqs = np.array(list(map(lambda lf: 10**lf, log_freqs)))
        print("compute signal envelope")
        fxn_s = compute_function(freqs,fs,vs)
        print("compute noise envelope")
        fxn_n = compute_function(freqs,fn,vn)
        print("plot")
        plt.semilogx(freqs,fxn_s)
        plt.savefig('hilbert_signal.png')
        plt.cla()
        plt.semilogx(freqs,fxn_n)
        plt.savefig('hilbert_noise.png')
        plt.cla()
        print("optimizing")
        model = MultExpSignalModel()
        parnames = model.param_names()
        result = scipy.optimize.least_squares(lambda parvalues: \
                                            model.fit(freqs,fxn_s,fxn_n,parnames,parvalues),
                                              model.initial())

        model.set_params(dict(zip(parnames,result.x)))
        print("cost: %s" % result.cost)
        print("optimality: %s" % result.optimality)
        print("plotting")
        plt.semilogx(freqs, fxn_n, 'b-', label='data')
        plt.semilogx(freqs, model.apply(freqs,fxn_s), 'r-',
                     label='fit')
        plt.savefig('hilbert_fit.png')
        plt.cla()
        input('-------')

def execute(model):
    #build_dataset(model)
    subtractive_analysis(model)
    raise Exception("stop here")
