import numpy as np
import json

class DetTimeXform:
        def __init__(self,offset,warp=1.0):
            self._delay = offset
            self._warp = warp

        def set_warp(self,warp):
            self._warp = warp

        @property
        def warp(self):
            return self._warp


        @property
        def delay(self):
            return self._delay

        def to_json(self):
            return {
                    'delay':self._delay,
                    'warp': self._warp
            }
        @staticmethod
        def from_json(data):
            return DetTimeXform(data['delay'],data['warp'])

        def write(self,name):
            with open(name,'w') as fh:
                strdata = json.dumps(self.to_json())
                fh.write(strdata)

        @staticmethod
        def read(name):
            with open(name,'r') as fh:
                data = json.loads(fh.read())
                return DetTimeXform.from_json(data)



class DetSignalXform:

        class Segment:
             def __init__(self,l,u,a,b,error=0.0):
                self._lower_bound = l
                self._upper_bound = u
                self._alpha = a
                self._beta = b
                self._error = error

             def set_error(self,e):
                self._error = e

             @property
             def alpha(self):
                return self._alpha

             @property
             def beta(self):
                return self._beta

             @property
             def lower_bound(self):
                return self._lower_bound

             @property
             def upper_bound(self):
                return self._upper_bound

             def contains(self,x):
                lb,ub =self._lower_bound,self._upper_bound
                if lb is None:
                   return x < ub
                if ub is None:
                   return lb <= x
                else:
                   return lb <= x and ub > x


             def apply(self,x):
                return self._alpha*x+self._beta

             @staticmethod
             def from_json(data):
                seg = DetSignalXform.Segment(
                        l=data['lower_bound'],
                        u=data['upper_bound'],
                        a=data['alpha'],
                        b=data['beta'],
                        error=data['error']
                )
                return seg

             def to_json(self):
                return {
                        'alpha':self._alpha,
                        'beta':self._beta,
                        'error':self._error,
                        'lower_bound':self._lower_bound,
                        'upper_bound':self._upper_bound
                }

             def __repr__(self):
                return "[%s,%s] %s*x+%s {%s}" % \
                        (self._lower_bound,
                         self._upper_bound,
                         self._alpha,
                         self._beta,
                         self._error)

        def __init__(self,bias=0.0):
            self._segments = []
            self._bias = bias

        def set_bias(self, b):
            self._bias = b
        @property
        def segments(self):
            for seg in self._segments:
                yield seg

        @property
        def num_segments(self):
            return len(self._segments)

        def get_segment_by_id(self,idx):
                return self._segments[idx]

        def _non_overlapping(self,l,u):
            for seg in self._segments:
                if not l is None and \
                   seg.contains(l):
                    return False
                if not u is None and \
                   seg.contains(u):
                    return False

            return True

        def add_segment(self,lower,upper,alpha,beta):
            assert(self._non_overlapping(lower,upper))
            seg = DetSignalXform.Segment(lower,upper,alpha,beta)
            self._segments.append(seg)
            return seg

        def error(self,x):
            segs = list(filter(lambda seg: seg.contains(x), \
                               self._segments))
            assert(len(segs) == 1)
            return segs[0].apply(x)


        def get_segment_id(self,x):
            inds = list(filter(lambda i: self._segments[i].contains(x), \
                               range(0,self.num_segments)))
            assert(len(inds) == 1)
            return inds[0]

        def apply_segment_by_id(self,i,x):
            return x + seg[i].apply(x)+self._bias

        def apply(self,x):
            segs = list(filter(lambda seg: seg.contains(x), \
                               self._segments))
            assert(len(segs) == 1)
            return x+segs[0].apply(x)+self._bias

        def to_json(self):
            segj = list(map(lambda seg: seg.to_json(), \
                            self._segments))
            return {
                    'segments':segj,
                    'bias':self._bias
            }

        @staticmethod
        def from_json(data):
            xform = DetSignalXform(bias=data['bias'])
            for seg_json in data['segments']:
                    seg = DetSignalXform.Segment\
                                     .from_json(seg_json)
                    xform._segments.append(seg)

            return xform

        def write(self,name):
            with open(name,'w') as fh:
                strdata = json.dumps(self.to_json())
                fh.write(strdata)

        @staticmethod
        def read(name):
            with open(name,'r') as fh:
                data = json.loads(fh.read())
                return DetSignalXform.from_json(data)

        def __repr__(self):
            r = ""
            for seg in self._segments:
                r += "%s\n" % seg
            return r





class DetLinNoiseXformModel:

    def __init__(self,freqs,slopes,offsets,errors):
        self._freqs = freqs
        self._slopes = slopes
        self._nsigs = len(slopes)
        self._offsets = offsets
        self._errors = errors

    def slopes(self,i):
        return self._slopes[i]


    @property
    def offsets(self):
        return self._offsets

    @property
    def freqs(self):
        return self._freqs

    def apply(self,values):
        return self._slopes[0]*values + self._offsets

    def to_json(self):
        slopes = {}
        for i in range(0,self._nsigs):
            slopes[i] = list(self._slopes[i])

        return {
            'type': 'linear',
            'freqs':list(self._freqs),
            'slopes': slopes,
            'offsets': list(self._offsets),
            'errors': list(self._errors)
        }

    @staticmethod
    def from_json(data):
        nsigs = len(data['slopes'].keys())
        slopes = []
        for i in range(0,nsigs):
            slopes.append( \
                np.array(data['slopes'][str(i)])
            )

        freqs = np.array(data['freqs'])
        offsets = np.array(data['offsets'])
        errors = np.array(data['errors'])
        return DetLinNoiseXformModel(freqs,slopes,offsets,errors)

    def write(self,filename):
        with open(filename,'w') as fh:
            fh.write(json.dumps(self.to_json()))

    @staticmethod
    def read(filename):
        with open(filename,'r') as fh:
            return DetLinNoiseXformModel.from_json(json.loads(fh.read()))
