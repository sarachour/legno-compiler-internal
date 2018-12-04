import pymc3 as pm
import theano
import numpy as np
import scipy
import matplotlib.pyplot as plt
import json
import itertools
import pickle

# No frequency Scaling
#Af_0_mu 0.00602086901757
#Gv_0_mu -0.00484821499378
#Gv_0_sig 0.0966582304726
#Bv_0_mu -9.80952957186e-06
#Bv_0_sig 0.000229343134554

class NoiseStump:

    def __init__(self,
                 fmin, \
                 fmax, \
                 freq_scale, \
                 uncorr_bias, \
                 uncorr_noise, \
                 sig_corr_bias=0, \
                 sig_corr_noise=0, \
                 freq_corr_bias=0,
                 freq_corr_noise=0):
        self._freq_low = fmin
        self._freq_high = fmax
        self._freq_scale = freq_scale
        self._epsilon = 1.0
        self._signal_corr = (sig_corr_bias,sig_corr_noise)
        #self._freq_corr = (freq_corr_bias,freq_corr_noise)
        self._freq_corr = (freq_corr_bias,freq_corr_noise)
        self._uncorr = (uncorr_bias,uncorr_noise)

    def dist(self,sig_freqs,sig_vals,noise_freq):
        selector = [abs(self._freq_scale*freq - noise_freq) < self._epsilon \
                    for freq in sig_freqs]
        sig = sum(itertools.compress(sig_vals,selector))
        mu1,var1 = self._signal_corr
        mu2,var2 = self._freq_corr
        mu3,var3 = self._uncorr
        flow,fhigh = self._freq_low,self._freq_high
        mu = mu1*sig + mu2*(noise_freq-flow)/(fhigh-flow) + mu3
        var = var1*sig + var2*noise_freq + var3
        return scipy.stats.norm(mu,var)

    def generate(self,sig_freqs,sig_vals,noise_freq):
        dist = self.dist(sig_freqs,sig_vals,noise_freq)
        return dist.sample()

    def likelihood(self,sig_freqs,sig_vals,noise_freq,noise_ampl):
        dist = self.dist(sig_freqs,sig_vals,noise_freq)
        return dist.pdf(noise_ampl)




def to_narray(header,data,nsamples_sig=1000,nsamples_noise=1000):
    def closest_index(freqs,freq):
        for idx,cfreq in enumerate(freqs):
            if cfreq > freq:
                if idx == 0:
                    return 0

                err_prev = abs(freqs[idx-1]-freq)
                err_next = abs(cfreq-freq)
                if err_prev < err_next:
                    return idx-1
                else:
                    return idx

        return len(freqs) - 1

    def random_sample(buf,header,datum,freq_key,val_key,nsamples):
        # get datums
        vals = datum[header.index(val_key)]
        freqs = datum[header.index(freq_key)]
        # randomly sample points
        if len(freqs) == 0:
            freqs = [0]
            vals = [0]
        freq_min,freq_max = min(freqs),max(freqs)
        samp_freqs = np.random.uniform(freq_min,freq_max,size=nsamples)
        indices = list(map(lambda f: closest_index(freqs,f),samp_freqs))
        buf[freq_key] += list(map(lambda i: freqs[i], indices))
        buf[val_key] += list(map(lambda i: vals[i], indices))

    buf= {}

    for h in header:
        buf[h] = []
    for datum in data:
        random_sample(buf,header,datum,'Fn','Vn',nsamples_noise)
        random_sample(buf,header,datum,'Fs','Vs',nsamples_sig)

    dataset = {}
    for h in header:
        if h == 'Fn' or h == 'Vn':
            dataset[h] = np.reshape(buf[h], (-1,nsamples_noise))
        else:
            dataset[h] = np.reshape(buf[h], (-1,nsamples_sig))

    return dataset,len(data)

def read_data(filename):
    data = []
    with open(filename,'r') as fh:
        header = json.loads(fh.readline())
        for line in fh:
            args = json.loads(line.strip())
            datum = []
            for i in range(0,4):
                datum.append(args[i])

            data.append(np.array(datum))

    return header,data

def freq_slice(header,data,fmin,fmax):
    new_data = []
    for datum in data:
        fn_i= header.index('Fn')
        vn_i= header.index('Vn')
        fs_i= header.index('Fs')
        vs_i= header.index('Vs')

        selector = [freq <= fmax and freq >= fmin \
                    for freq in datum[fn_i]]
        new_datum = [None]*4
        new_datum[fn_i] = list(itertools.compress(datum[fn_i], selector))
        new_datum[vn_i] = list(itertools.compress(datum[vn_i], selector))
        new_datum[fs_i] = datum[fs_i]
        new_datum[vs_i] = datum[vs_i]
        new_data.append(new_datum)

    return new_data

def gen_pfun_params(idx,pref,positive=False,freq_shift=None):
        params = {}
        if freq_shift == None:
            params['Af'] = pm.HalfNormal('Af_%d_%s' % (idx,pref),0.01)
        else:
            params['Af'] = freq_shift

        if not positive:
            params['Gv'] = pm.Cauchy('Gv_%d_%s' % (idx,pref),0.0,5e-1)
            #params['Av'] = pm.Cauchy('Av_%d_%s' % (idx,pref),0.0,1e-4)
            params['Bv'] = pm.Normal('Bv_%d_%s' % (idx,pref),0.0,5e-1)
        else:
            params['Gv'] = pm.HalfCauchy('Gv_%d_%s' % (idx,pref),1e-1)
            #params['Av'] = pm.HalfCauchy('Av_%d_%s' % (idx,pref),1e-5)
            params['Bv'] = pm.HalfNormal('Bv_%d_%s' % (idx,pref),4e-1)

        return params

def gen_binned_params(fmax,n):
    last_cutoff = 0
    params = {'mu':{},'var':{},'n':{}}
    for idx in range(0,n):
        Af = pm.HalfNormal('Af_%d' % (idx),0.01)
        params['mu'][idx] = gen_pfun_params(idx,'mu',positive=False)
        params['var'][idx] = gen_pfun_params(idx,'sigma',positive=True, \
                                             freq_shift=params['mu']['Af'])
        var['Af'] = var
        if idx == 0:
            params['n'][idx] = pm.Uniform("N_%d" % idx,0,fmax)
        else:
            params['n'][idx] = pm.Uniform("N_%d" % idx,0,fmax-params['n'][idx-1])

    lower = []
    upper = []
    mupars = []
    varpars = []
    lower.append(0)
    for idx in range(0,n):
        mupars.append(params['mu'][idx])
        varpars.append(params['var'][idx])
        lower.append(params['n'][idx])
        upper.append(params['n'][idx])
    upper.append(fmax)
    return lower,upper,mupars,varpars


def gen_free_params():
    mu = gen_pfun_params(0,'mu',positive=False)
    var = gen_pfun_params(0,'sig',positive=True,freq_shift=mu['Af'])
    return mu,var

def gen_model_stump(pars,Fn,Fs,Vs,freq_min=0.0,freq_max=1.0,positive=False):
    print_shape = theano.printing.Print('vector', attrs = [ 'shape' ])
    print_vector = theano.printing.Print('vector')
    epsilon = theano.tensor.constant(1.0)
    one = theano.tensor.constant(1)
    Fs_vect = theano.tensor.reshape(Fs,(Fs.shape[0],one,Fs.shape[1]))
    Vs_vect = theano.tensor.reshape(Vs,(Vs.shape[0],one,Vs.shape[1]))
    Fn_vect = theano.tensor.reshape(Fn,(Fn.shape[0],Fn.shape[1],one))
    #print_shape(Fs_vect)
    #print_shape(Vs_vect)
    #print_shape(Fn_vect)
    G = pars['Af']*Fn_vect

    # broadcast Fs over Fn
    SIG = pm.math.sum(
        pm.math.switch(
            pm.math.le(abs(Fs_vect-G), epsilon),
            Vs_vect,
            0.0
        ), axis=2)

    LINFXN = pars['Bv']
    #fmin = theano.tensor.constant(freq_min)
    #fdist = theano.tensor.constant(freq_max-freq_min)
    #LINFXN += pars['Av']*(Fn-fmin)/(fdist)
    LINFXN += pars['Gv']*(abs(SIG) if positive else SIG)
    return LINFXN


def generate_variables(n,m_sig,m_noise):
    vals_vs = np.ones((n,m_sig))
    vals_fs = np.tile(range(0,m_sig), n).reshape(n,m_sig)
    vals_vn = np.ones((n,m_noise))
    vals_fn = np.tile(range(0,m_noise), n).reshape(n,m_noise)
    vs = {}
    vs['Vs'] = theano.shared(vals_vs.astype(float))
    vs['Fs'] = theano.shared(vals_fs.astype(float))
    vs['Fn'] = theano.shared(vals_fn.astype(float))
    vs['Vn']= theano.shared(vals_vn.astype(float))
    return vs

def generate_single_stump_model(freq_min,freq_max,n,m_sig,m_noise):
    mupars,varpars = gen_free_params()
    vs = generate_variables(n,m_sig,m_noise)
    mean = gen_model_stump(mupars,vs['Fn'],vs['Fs'],vs['Vs'],
                           freq_min=freq_min,
                           freq_max=freq_max)
    variance = gen_model_stump(varpars,vs['Fn'],vs['Fs'],vs['Vs'],
                               freq_min=freq_min,
                               freq_max=freq_max,positive=True)

    return vs,pm.Normal("NoiseModel",
                        mean,
                        variance,
                        observed=vs['Vn'])

def generate_bin_model(nbins,n,m_sig,m_noise):
    def generate_parametric(lower,upper,params,Fn,Fs,Vs):
        FXN = pm.math.switch(
            pm.math.le(Fn, upper) and
            pm.math.ge(Fn, lower),
            gen_model_stump(params,Fn,Fs,Vs),
            0.0
        )
        return FXN


    lower,upper,mupars,varpars = gen_binned_params(500000,nbins)
    vs = generate_variables(n,m_sig,m_noise)
    means = []
    varis = []
    print("-> created parameters")
    for idx,(mup,vap,lower,upper) in enumerate(zip(mupars,varpars,lower,upper)):
        means.append(generate_parametric(lower,upper,mup,vs['Fn'],vs['Fs'],vs['Vs']))
        varis.append(generate_parametric(lower,upper,vap,vs['Fn'],vs['Fs'],vs['Vs']))

    print("-> built distribution")
    return vs,pm.Normal("NoiseModel",
                        sum(means),
                        sum(varis),
                        observed=vs['Vn'])

def plot_stats(basename,trace):
    ax = pm.plot_posterior(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_posterior.png' % basename)
    plt.cla()

    ax = pm.densityplot(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_density.png' % basename)
    plt.cla()

    ax = pm.energyplot(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_energy.png' % basename)
    plt.cla()

    ax = pm.autocorrplot(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_autocorr.png' % basename)
    plt.cla()

    ax = pm.traceplot(trace)
    fig = plt.gcf() # to get the current figure...
    fig.savefig('%s_traceplot.png' % basename)
    plt.cla()

def print_params(params):
    for k,v in params.items():
        print("%s = %s" % (k,v))
    print("-------")

def test_model(model):
    for _ in range(0,5):
        print("======")
        for RV in model.basic_RVs:
            log_prob = RV.logp(model.test_point)
            print(RV.name, log_prob)
            if np.isinf(log_prob):
                raise Exception("found infinite log prob with test point.")

def evaluate_model(model_name,fmin,fmax,header,data):
    network,trace = load_model(model_name)
    with network as model:
        def get_param(name):
            pval = np.median(trace[name])
            print(name,pval)
            return pval

        idx = 0
        stump = NoiseStump(fmin,fmax,
            freq_scale=get_param('Af_%d_mu' % idx),
            sig_corr_bias=get_param('Gv_%d_mu' % idx),
            sig_corr_noise=get_param('Gv_%d_sig' % idx),
            #freq_corr_bias=get_param('Av_%d_mu' % idx),
            #freq_corr_noise=get_param('Av_%d_sig' % idx),
            uncorr_bias=get_param('Bv_%d_mu' % idx),
            uncorr_noise=get_param('Bv_%d_sig' % idx)
        )

    fig,(sub_dist,sub_prob) = plt.subplots(2,1)
    sub_dist.set_title('predicted distribution')
    sub_prob.set_title('predicted probability')
    print("=== Evaluating Model on Holdout Data")
    for idx,datum in enumerate(data):
        print(" -> datum %d" % idx)
        Fs = datum[header.index('Fs')]
        Vs = datum[header.index('Vs')]
        Fn = datum[header.index('Fn')]
        Vn = datum[header.index('Vn')]
        dists = list(map(lambda freq: stump.dist(Fs,Vs,freq), Fn))
        means = list(map(lambda dist: dist.mean(), dists))
        variances = list(map(lambda dist: dist.var(), dists))
        probs = list(map(lambda tup: min(1.0,tup[1].pdf(tup[0])), zip(Vn,dists)))
        ub = list(map(lambda tup: tup[0]+tup[1], zip(means,variances)))
        lb = list(map(lambda tup: tup[0]-tup[1], zip(means,variances)))
        sub_dist.scatter(Fn,means,alpha=0.5,s=0.7,color='red')
        sub_dist.scatter(Fn,ub,alpha=0.5,s=0.7,color='blue')
        sub_dist.scatter(Fn,lb,alpha=0.5,s=0.7,color='blue')
        sub_dist.scatter(Fn,Vn,alpha=0.5,s=0.7,color='black')
        sub_prob.scatter(Fn,probs,alpha=0.5,s=0.5)

    fig.savefig('%s_evaluation.png' % model_name)
    plt.close(fig)
    plt.clf()
    plt.cla()


def trace_to_stump(trace,idx):
    freq_scale = 'Af_%d_mu' % idx
    sig_corr_bias = 'Gv_%d_mu' % idx
    sig_corr_noise = 'Gv_%d_sig' % idx
    sig_corr_noise = 'Gv_%d_sig' % idx

def save_model(model_name,trace, network):
    with open ('%s.pkl' % model_name, 'wb') as buff:
        pickle.dump ({'model': network, 'trace': trace}, buff)


#reload trained model
def load_model(model_name):
    with open ('%s.pkl' % model_name, 'rb') as buff:
        data = pickle.load (buff)
        network, trace = data[ 'model' ], data[ 'trace' ]

    return network,trace

def gen_model(data,fmin,fmax, \
              n,m_sig,m_noise,model_name,approximate=False):
    with pm.Model() as model:

        #vs,gm = generate_binned_model(1,n,m_sig,m_noise)
        vs,gm = generate_single_stump_model(fmin,fmax,n,m_sig,m_noise)
        print('--- model generated ---')
        for key in vs:
            print("%s = %s" % (key,data[key]))
            vs[key].set_value(data[key])
        #test_model(model)
        print('--- values set ---')
        params = pm.find_MAP()
        print('--- initial ---')
        print_params(params)
        if approximate:
            print("--- approximate ---")
            inference = pm.ADVI()
            #niters = 50000
            niters = 20000
            approx = pm.fit(niters,method=inference)
            plt.plot(approx.hist)
            plt.savefig('%s_loss.png' % model_name)
            plt.clf()
            trace = approx.sample()
        else:
            trace = pm.sample(4000)

        save_model(model_name,trace,model)
        print(trace)
        plot_stats(model_name,trace)

train = True
corners = [0,400,1700]
#fmin,fmax = 1700,10000
#fmin,fmax = 0,1000
#fmin,fmax = 0,50
#fmin,fmax = 0,500000
fmin,fmax = 0,100000
nmodels = 2500
fbin_size= (fmax-fmin)/nmodels

nsamps_sig = 100
nsamps_noise = 100
print("=== Read Test Data ===")
train_header,train_data = read_data('ampl_mean_train.json')
print("=== Read Train Data ===")
#test_header,test_data = read_data('ampl_mean_test.json')
test_header,test_data = read_data('ampl_mean_train.json')
for model_idx in range(0,nmodels):
    c_fmin = fbin_size*model_idx
    c_fmax = fbin_size*(model_idx+1)

    print("=== Model %d [%f,%f] ===" % (model_idx,c_fmin,c_fmax))
    c_train_data = freq_slice(train_header,train_data,c_fmin,c_fmax)
    c_test_data = freq_slice(test_header,test_data,c_fmin,c_fmax)
    #assert(len(c_test_data[0][test_header.index('Fn')]) > 0)
    c_train_data,c_train_n = to_narray(train_header,c_train_data, \
                                       nsamps_sig, \
                                       nsamps_noise)

    model_name = "model_%d" % model_idx
    gen_model(c_train_data,c_fmin,c_fmax,
              c_train_n,nsamps_sig,nsamps_noise,
              model_name=model_name, \
              approximate=True)

    evaluate_model(model_name,c_fmin,c_fmax,
                   test_header,c_test_data)
