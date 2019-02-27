from sklearn.model_selection import train_test_split
import pymc3 as pm
import theano.tensor as tt
from theano.printing import pydotprint
import theano
import matplotlib.pyplot as plt
import numpy as np
import json

class BayesianModel:

    def __init__(self,freqs):
        self._phase = None
        self._freqs = list(freqs)
        self._variances = {}
        self._parameters = {}

    def phase_model(self):
        return self._phase['mean'],self._phase['stdev']

    def variances(self):
        for (fmin,fmax),snr in self._variances.items():
            yield fmin,fmax,snr

    def add_parameter(self,param,mean,stdev):
             self._parameters[param] = {'mean':list(mean),
                                       'stdev':list(stdev)}

    def add_variance(self,fmin,fmax,variance):
        self._variances[fmin,fmax] = variance

    def set_phase_model(self,mean,std):
        self._phase = {
            'mean':mean,'stdev':std
        }

    def to_json(self):
        return {
            'phase_model':{'mean':self._phase['mean'], 'stdev':self._phase['stdev']},
            'noise_model':{
                'freqs':self._freqs,
                'variance': list(self._variances.items()),
                'params': self._parameters
            }
        }

    @staticmethod
    def from_json(obj):
        bmod = BayesianModel(obj['noise_model']['freqs'])
        bmod.set_phase_model( \
                              obj['phase_model']['mean'],
                              obj['phase_model']['stdev']
        )
        for (fmin,fmax),variance in obj['noise_model']['variance']:
            bmod.add_variance(fmin,fmax,variance)

        for param,data in obj['noise_model']['params'].items():
            bmod.add_parameter(param,data['mean'],data['stdev'])

        return bmod

    @staticmethod
    def read(filename):
        with open(filename,'r') as fh:
            obj = json.loads(fh.read())
            return BayesianModel.from_json(obj)

    def write(self,filename):
        jsonobj = self.to_json()
        jsonstr = json.dumps(jsonobj)
        with open(filename,'w') as fh:
            fh.write(jsonstr)

class BayesInference:

    #niters = 10000
    def __init__(self,fv,niters=10000,nsamples=1000):
        self._iters = niters
        self._samples = nsamples
        self._models = {}
        self._results = {}
        self._fv = fv
        self._dataset = {}
        out_ampl_mat,out_phase_mat = fv.matrix(lambda d: [d.output])
        noise_ampl_mat, noise_phase_mat = fv.matrix(lambda d : \
                                                    [d.noise])

        x_train,x_test,y_train,y_test = \
                    train_test_split(out_ampl_mat,noise_ampl_mat)
        #x_train,y_train,x_test,y_test= out_ampl_mat,noise_ampl_mat,[],[]

        self._dataset['ampl'] = ((x_train,y_train),(x_test,y_test))

        x_train,x_test,y_train,y_test = \
                    train_test_split(out_phase_mat,noise_phase_mat)
        #x_train,y_train,x_test,y_test= out_phase_mat,noise_phase_mat,[],[]
        self._dataset['phase'] = ((x_train,y_train),(x_test,y_test))

    def model_linear(self,data_name):
        #settings = {'config.compute_test_value': 'off'}
        settings = {}
        model = pm.Model(settings)

        (state,obs),_ = self._dataset[data_name]
        _,dim = self._fv.shape()
        with model:
            Xt = theano.shared(state)
            yt = theano.shared(obs)
            alpha = pm.Normal('alpha', mu=0, sd=10, shape=(dim))
            beta = pm.Normal('beta', mu=0, sd=10, shape=(dim))
            mu = beta*Xt + alpha
            sigma = pm.HalfNormal('sigma', sd=1, shape=(dim))
            Y_obs = pm.Normal('obs', mu=mu, sd=sigma, observed=yt, \
                              total_size=(dim))

        self._models[data_name] = (model,Y_obs,Xt,yt)



    def print_model(self,name):
        model,_,_,_ = self._models[name]
        pydotprint(model.logpt)
        print("free-vars: %s" % model.free_RVs)
        print("deterministic: %s" % model.deterministics)



    def save_accuracy_graph(self,data_name,filename):
        _,acc_tracker = self._results[data_name]
        plt.clf()
        plt.plot(np.asarray(acc_tracker['test_accuracy']).T,
                 color='red')
        plt.plot(np.asarray(acc_tracker['train_accuracy']).T,
                 color='blue')
        plt.legend(['test_accuracy', 'train_accuracy'])
        plt.title('Training Progress')
        plt.savefig(filename)
        plt.clf()

    def save_loss_graph(self,data_name,filename):
        result,_,_ = self._results[data_name]
        plt.clf()
        plt.plot(result.hist)
        plt.savefig(filename)
        plt.clf()

    def compute_accuracy(self,data_name):
        (tr_X,tr_Y),(te_X,te_Y) = self._dataset[data_name]
        model,prob,Xt,yt = self._models[data_name]
        result,sampler,_ = self._results[data_name]
        def _compute(X,Y):
            with model:
                Xt.set_value(X)
                yt.set_value(Y)
                post_pred = pm.sample_ppc(sampler, samples=500)
                avg = post_pred['obs'].mean(axis=0)
                std = post_pred['obs'].std(axis=0)
                return avg,std

        avg,std = _compute(te_X,te_Y)
        for mu,sigma,y in zip(avg,std,te_Y):
            print("===== VECTOR =====")
            for (lo,hi),m,s,v in zip(self._fv.freqs,mu,sigma,y):
                print("[%s,%s]\t\tN(%s,%s) = %s" % (lo,hi,m,s,v))


    def model_variation(self,data_name):

        def compute_snr(values):
            mean = np.mean(values,axis=0)
            std = np.std(values,axis=0)
            snr = list(map(lambda args: abs(args[0])/args[1], \
                           zip(mean,std)))
            return mean,std,snr

        result,sampler,_ = self._results[data_name]
        params = None
        for datum in sampler:
            if params is None:
                params = dict(map(lambda k: (k,[]), datum.keys()))

            for key,value in datum.items():
                params[key].append(value)

        snrs = {}
        parvals = {}

        for pname,values in params.items():
            mean,std,snr = compute_snr(values)
            parvals[pname] = (mean,std)
            snrs[pname] = snr

        variances = {}
        for idx,(fmin,fmax) in enumerate(self._fv.freqs):
            indiv_snr = list(map(lambda param: snrs[param][idx], ['alpha','beta']))
            snr = min(indiv_snr)
            print("[%s,%s]]\t\t%s [%s]" % (fmin,fmax,snr,indiv_snr))
            variances[(fmin,fmax)] = snr

        return variances,parvals

    def variational_inference(self,data_name):
        model,prob,Xt,yt = self._models[data_name]
        (tr_X,tr_Y),(te_X,te_Y) = self._dataset[data_name]
        with model:
            def acc_tracker():
                advi = pm.ADVI()
                approx = advi.approx
                # Here we need `more_replacements` to change train_set to test_set
                test_probs = approx.sample_node(prob,
                                                more_replacements={Xt: te_X[0]},
                                                size=len(te_Y))

                # For train set no more replacements needed
                train_probs = approx.sample_node(prob,
                                                more_replacements={Xt:tr_X[0]},
                                                size=len(tr_Y))

                test_ok = tt.eq(test_probs.argmax(1), te_Y)
                train_ok = tt.eq(train_probs.argmax(1), tr_Y)
                test_accuracy = test_ok.mean(-1)
                train_accuracy = train_ok.mean(-1)
                acc_tracker = pm.callbacks.Tracker(
                    test_accuracy=test_accuracy.eval,
                    train_accuracy=train_accuracy.eval
                )
                return

            cbks = []
            result = pm.fit(n=self._iters,callbacks=cbks)
            sampler = pm.sample(self._samples)
            self._results[data_name] = (result,sampler,{})

