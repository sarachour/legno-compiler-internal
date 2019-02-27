import lab_bench.analysis.waveform as wf
import matplotlib.pyplot as plt
from rdp import rdp
import numpy as np
import scipy
import sklearn.cluster as skclust
import itertools

def binning(data,n,xform):
    def to_bin(mu,sigma):
        lo = max(0,(mean-stdev))
        hi = (mean+stdev)
        return lo,hi

    fmax = max(map(lambda datum: datum.fmax(),data))
    fmin = min(map(lambda datum: datum.fmin(),data))

    points = []
    fpoints= []
    for datum in data:
        for freq in xform(datum):
            delta = 1e-10
            for idx,(f,a,p) in enumerate(freq.phasors()):
                points.append([idx*delta,a,p])
                fpoints.append(f)

    kmeans = skclust.KMeans(n_clusters=n-1)
    kmeans.fit(points)
    centers = list(kmeans.cluster_centers_)
    freqs = []
    for idx,center in enumerate(centers):
        selector = [x == idx for x in kmeans.labels_]
        pts = list(itertools.compress(fpoints,selector))
        stdev = np.std(pts) + 1e-6
        mean = np.mean(pts)
        lo,hi = to_bin(mean,stdev)
        freqs.append((lo,hi))
        print("%s -> N(%s,%s)" % (center,mean,stdev))
        print("      [%s, %s]" % (lo,hi))

    freqs.append((fmin,fmax))
    return list(set(freqs))

def hilbert(data,n,xform):
    def min_pts(freqs,vals):
        fn = np.imag(scipy.signal.hilbert(vals))
        fn_min = rdp(list(zip(freqs,fn)),epsilon=0.002)
        return list(map(lambda x: x[0], fn_min))

    fmax = max(map(lambda datum: datum.fmax(),data))
    fmin = min(map(lambda datum: datum.fmin(),data))

    print("-> minifying point envelope")
    pts = []
    for datum in data:
        for freq in xform(datum):
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

def cluster(data,n,xform):
    def angle(u,v):
        c = np.dot(u,v)/(np.linalg.norm(u)*np.linalg.norm(v))
        angle = np.arccos(np.clip(c, -1, 1))
        return angle

    fmax = max(map(lambda datum: datum.fmax(),data))
    fmin = min(map(lambda datum: datum.fmin(),data))

    points = []
    for datum in data:
        for freq in xform(datum.output,datum.noise):
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


class FeatureVectorSet:


    def __init__(self,data,n=100):
        self._freqs = binning(data,n,lambda d: [d.output,d.noise])
        #self._freqs = hilbert(data,n,lambda d: [d.output,d.noise])
        self._data = data
        self._n = len(self._freqs)

    @property
    def freqs(self):
        for fmin,fmax in self._freqs:
            yield fmin,fmax

    def shape(self):
        return (len(self._data),self._n)

    def plot_features(self,datum,ampl_image,phase_image):
        (fig_ampl,ax_ampl),(fig_phase,ax_phase) = \
                datum.plot_figure(do_log_x=False,do_log_y=False)

        ampl_lo,ampl_hi = ax_ampl.get_ylim()
        phase_lo,phase_hi = ax_phase.get_ylim()
        for index,(flo,fhi) in enumerate(self._freqs):
            color = "green" if index % 2 == 0 else "blue"
            ax_ampl.fill_between([flo,flo,fhi,fhi],\
                                 [ampl_lo,ampl_hi,ampl_hi,ampl_lo],
                                 facecolor=color,alpha=0.4)
            ax_phase.fill_between([flo,flo,fhi,fhi],\
                                 [phase_lo,phase_hi,phase_hi,phase_lo],
                                 facecolor=color,alpha=0.4)


        ax_ampl.set_xscale('log')
        ax_phase.set_xscale('log')
        fig_ampl.savefig(ampl_image)
        fig_phase.savefig(phase_image)
        plt.clf()

    def vect(self,freq):
        vecta = [0]*len(self._freqs)
        vectp = [0]*len(self._freqs)
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
