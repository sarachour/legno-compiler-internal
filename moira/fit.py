import sys
import os
import lab_bench.analysis.waveform as wf
import numpy as np
import math
import pymc3 as pm
import sklearn.cluster as skclust
import scipy
import matplotlib.pyplot as plt
from theano.printing import pydotprint
from moira.db import ExperimentDB
import itertools
from rdp import rdp

print('Running on PyMC3 v{}'.format(pm.__version__))


class FeatureVectorSet:

    @staticmethod
    def hilbert(data,n):
        def min_pts(freqs,vals):
            fn = np.imag(scipy.signal.hilbert(vals))
            fn_min = rdp(list(zip(freqs,fn)),epsilon=0.002)
            return list(map(lambda x: x[0], fn_min))

        fmax = max(map(lambda datum: datum.fmax(),data))
        fmin = min(map(lambda datum: datum.fmin(),data))

        print("-> minifying point envelope")
        pts = []
        for datum in data:
            for freq in [datum.output,datum.noise]:
                pts += min_pts(freq.freqs(),list(freq.amplitudes()))
                pts += min_pts(freq.freqs(),list(freq.phases()))
                # transformed signal is imaginary

        print("-> finding minimal bins")
        np_pts = np.array(pts).reshape(-1,1)
        kmeans = skclust.KMeans(n_clusters=n)
        kmeans.fit(np_pts)
        centers = list(set(map(lambda c: c[0],kmeans.cluster_centers_)))
        centers.sort()

        freqs = []
        last_freq = fmin
        for index in range(1,len(centers)):
            midpt = (centers[index-1]+centers[index])/2
            freqs.append((last_freq,midpt))
            last_freq = midpt

        print(freqs)
        return freqs

    @staticmethod
    def uniform(data,n):
        fmax = max(map(lambda datum: datum.fmax(),data))
        fmin = min(map(lambda datum: datum.fmin(),data))
        fs = np.arange(fmin,fmax, \
                       (fmax-fmin)/n)
        # frequency bin
        freqs = []
        for idx in range(1,n):
            freqs.append((fs[idx-1],fs[idx]))

        return freqs

    @staticmethod
    def cluster(data,n):
        def angle(u,v):
            c = np.dot(u,v)/(np.linalg.norm(u)*np.linalg.norm(v))
            angle = np.arccos(np.clip(c, -1, 1))
            return angle

        fmax = max(map(lambda datum: datum.fmax(),data))
        fmin = min(map(lambda datum: datum.fmin(),data))

        points = []
        for datum in data:
            for freq in [datum.output,datum.noise]:
                for f,a,p in freq.phasors():
                    points.append([f,a,p])

        kmeans = skclust.KMeans(n_clusters=n)
        kmeans.fit(points)
        centers = list(kmeans.cluster_centers_)
        centers.sort(key=lambda c:c[0])
        freqs = []
        last_freq = fmin
        for index in range(1,n):
            midpoint = (centers[index-1] + centers[index])/2.0
            slope = (centers[index] - centers[index-1])
            mid_corner = [midpoint[0],0,0]
            # see phone for geometry of determining where to
            # put the cutoff for the bin border between two centroids.
            # side
            x = np.linalg.norm(midpoint-mid_corner)
            # angle
            a = angle(slope,[1,0,0])
            y = x*np.tan(a)
            if y > 0:
                print("[%s,%s] correction=%s" % (centers[index-1],centers[index],y))
            vect = [midpoint[0]-y,0,0]
            dist1 = (np.linalg.norm(vect-centers[index-1]))
            dist2 = (np.linalg.norm(vect-centers[index]))
            assert(abs(dist1-dist2) <= 1e-5)
            mid_freq = vect[0]
            freqs.append((last_freq,mid_freq))
            last_freq = mid_freq

        freqs.append((last_freq,fmax))
        return freqs

    def __init__(self,data,n=100):
        self._freqs = FeatureVectorSet.hilbert(data,n)
        self._data = data
        self._n = n

    @property
    def freqs(self):
        for fmin,fmax in self._freqs:
            yield fmin,fmax

    def shape(self):
        return (len(self._data),self._n)

    def vect(self,freq):
        vecta = [0]*self._n
        vectp = [0]*self._n
        for index,(fmin,fmax) in enumerate(self._freqs):
            abnd,pbnd = freq.bounds(fmin,fmax)
            amean,pmean = freq.average(fmin,fmax)
            vecta[index] = amean
            vectp[index] = pmean

        return vecta,vectp

    def multivect(self,datum,xform):
        av,pv = [],[]
        for freq in xform(datum):
            ampl_vect,phase_vect = self.vect(freq)
            av += ampl_vect
            pv += phase_vect

        return av,pv

    def vects(self,xform):
        for datum in self._data:
            yield self.multivect(datum,xform)

    def matrix(self,xform):
        ampl_mat,phase_mat = [],[]

        for ampl_vect,phase_vect in self.vects(xform):
            ampl_mat.append(ampl_vect)
            phase_mat.append(phase_vect)

        return np.array(ampl_mat),np.array(phase_mat)

def reject_outliers(dataset,stdevs=2):
    data = list(dataset.values())
    delays = list(map(lambda ds: ds.delay,data))
    median = np.median(delays)
    deviation = list(map(lambda delay: abs(delay - median), delays))
    median_deviation = np.mean(deviation)
    thresh = deviation/median_deviation if median_deviation else 0
    return list(filter(lambda ds: abs(ds[1].delay-median)/median_deviation<stdevs,
                       dataset.items()))

# for vdiv: 0 and 3 are issues
# observation: low frequency signals are easy to align. maybe start with that
def infer_phase_delay_model(data):
    weight = lambda c: (c**2)

    N = len(data)
    # weighted mean
    mean = sum(map(lambda ds: ds.delay, data))/N
    std = math.sqrt(sum(map(lambda ds: ((ds.delay-mean)**2),data))/N)
    print("phase: N(%s,%s)" % (mean,std))

def infer_noise_model(data):
    NITERS = 100000
    def report_loss(loss,filename):
        plt.clf()
        plt.plot(loss.hist)
        plt.savefig(filename)
        plt.clf()

    def compute_error(values):
        mean = np.mean(values,axis=0)
        std = np.std(values,axis=0)
        error = list(map(lambda args: args[1]/abs(args[0]), \
                         zip(mean,std)))
        return error

    def report_model(fv,model):
        print("==== MODEL =====")
        trace = model.sample(10000)
        data = None
        for datum in trace:
            if data is None:
                data = dict(map(lambda k: (k,[]), datum.keys()))
            for key,value in datum.items():
                data[key].append(value)

        print("=== Alpha ===")
        alpha_err = compute_error(data['alpha'])
        print("=== Beta ===")
        beta_err = compute_error(data['beta'])
        print("=== Sigma ===")
        sigma_err = compute_error(data['sigma'])

        for (fmin,fmax),alpha,beta,sigma in \
            zip(fv.freqs,alpha_err,beta_err,sigma_err):
            print("[%s,%s]\t| %s |\t %s + %s*freq + %s*" % \
                  (fmin,fmax,alpha+beta+sigma,alpha,beta,sigma))


    def linear_model(state,obs):
        n,dim = fv.shape()
        model = pm.Model()
        with model:
            alpha = pm.Normal('alpha', mu=0, sd=10, shape=(dim))
            beta = pm.Normal('beta', mu=0, sd=10, shape=(dim))
            mu = beta*state + alpha
            sigma = pm.HalfNormal('sigma', sd=1, shape=(dim))
            Y_obs = pm.Normal('Y_obs', mu=mu, sd=sigma, observed=obs, \
                              total_size=(n,dim))
            # write model
            pydotprint(model.logpt)
            loss = pm.fit(n=NITERS)
            return model,loss

    print("-> creating feature vector information")
    fv = FeatureVectorSet(data,n=100)
    print("-> creating model")
    state_ampl_mat,state_phase_mat = fv.matrix(lambda d: [d.output])
    obs_ampl_mat,obs_phase_mat = fv.matrix(lambda d: [d.noise])
    print("=== Ampl ===")
    ampl_model,ampl_loss = linear_model(state_ampl_mat,obs_ampl_mat)
    print("loss: %s" % ampl_loss)
    print("model: %s" % ampl_model)
    report_loss(ampl_loss,'ampl_loss.png')
    report_model(fv,ampl_loss)
    print("=== Phase ===")
    phase_model,phase_loss = linear_model(state_phase_mat,obs_phase_mat)
    print("loss: %s" % phase_loss)
    print("model: %s" % phase_model)
    report_loss(phase_loss,'phase_loss.png')
    report_model(fv,phase_loss)

def execute(model):
    data = {}
    for ident,trials,inputs,output in \
        itertools.chain(\
                        model.db.get_by_status(ExperimentDB.Status.ALIGNED),
                        model.db.get_by_status(ExperimentDB.Status.USED)):
        for trial in trials:
            filepath = model.db.freq_file(ident,trial)
            fds = wf.FreqDataset.read(filepath)
            data[ident,trial] = fds

    if len(data.keys()) == 0:
        return

    good_data = []
    for (ident,trial),datum in reject_outliers(data,2):
        model.db.set_status(ident,trial,ExperimentDB.Status.USED)
        good_data.append(datum)

    print("%d -> %d" % (len(data),len(good_data)))
    infer_phase_delay_model(good_data)
    infer_noise_model(good_data)
    # should save to model file.
