import sys
import os
import lab_bench.analysis.waveform as wf
import numpy as np
import math
import pymc3 as pm
import sklearn.cluster as skclust
print('Running on PyMC3 v{}'.format(pm.__version__))

class FeatureVectorSet:

    @staticmethod
    def uniform(data,n):
        fmax = max(map(lambda datum: datum.fmax(),data))
        fmin = min(map(lambda datum: datum.fmin(),data))
        fs = np.arange(fmin,fmax, \
                       (fmax-fmin)/self._n)
        # frequency bin
        freqs = []
        for idx in range(1,n):
            freqs.append((fs[idx-1],fs[idx]))

        return freqs

    @staticmethod
    def cluster(data,n):
        fmax = max(map(lambda datum: datum.fmax(),data))
        fmin = min(map(lambda datum: datum.fmin(),data))

        points = []
        for datum in data:
            for freq in [datum.noise,datum.output]:
                for f,a,p in freq.phasors():
                    points.append([f,a,p])

        kmeans = skclust.KMeans(n_clusters=n)
        kmeans.fit(points)
        centers = list(kmeans.cluster_centers_)
        centers.sort(key=lambda c:c[0])
        freqs = []
        last_freq = fmin
        for index in range(1,n):
            mid_freq = (centers[index-1][0]+centers[index][0])/2
            freqs.append((last_freq,mid_freq))
            last_freq = mid_freq

        freqs.append((last_freq,fmax))
        print(freqs)
        return freqs

    def __init__(self,data,n=30):
        self._freqs = FeatureVectorSet.cluster(data,n)
        self._data = data
        self._n = n

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

def reject_outliers(data,stdevs=2):
    delays = list(map(lambda ds: ds.delay,data))
    median = np.median(delays)
    deviation = list(map(lambda delay: abs(delay - median), delays))
    median_deviation = np.median(deviation)
    thresh = deviation/median_deviation if median_deviation else 0
    return list(filter(lambda ds: abs(ds.delay-median)/median_deviation<stdevs,
                       data))

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
    def linear_model(dim,state,obs):
        model = pm.Model()
        with model:
            alpha = pm.Normal('alpha', mu=0, sd=10, shape=(dim))
            beta = pm.Normal('beta', mu=0, sd=10, shape=(dim))
            mu = beta*state + alpha
            sigma = pm.HalfNormal('sigma', sd=1, shape=(dim))
            Y_obs = pm.Normal('Y_obs', mu=mu, sd=sigma, observed=obs)
            loss = pm.fit()
            return model,loss

    print("-> creating feature vector information")
    fv = FeatureVectorSet(data,n=100)
    print("-> creating model")
    n,dim = fv.shape()
    state_ampl_mat,state_phase_mat = fv.matrix(lambda d: [d.output])
    obs_ampl_mat,obs_phase_mat = fv.matrix(lambda d: [d.noise])
    print("=== Ampl ===")
    ampl_model,ampl_loss = linear_model(dim,state_ampl_mat,obs_ampl_mat)
    print(ampl_loss)
    print("=== Phase ===")
    phase_model,phase_loss = linear_model(dim,state_phase_mat,obs_phase_mat)
    print(phase_loss)

def main():
    data = []
    path = sys.argv[1]
    for path, subdirs, files in os.walk(path):
        for filename in files:
            if filename.endswith(".json") == True and "freqdp" in filename:
                print("-> %s/%s" % (path,filename))
                filepath = "%s/%s" % (path,filename)
                fds = wf.FreqDataset.read(filepath)
                print(fds.delay)
                data.append(fds)

    good_data = reject_outliers(data,2)
    print("%d -> %d" % (len(data),len(good_data)))
    infer_phase_delay_model(good_data)
    infer_noise_model(good_data)

main()
