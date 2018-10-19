

class ANoiseSt:
    def __init__(self,f1,f2,variance=True):
        self._min = f1;
        self._max = f2;
        self._variance = variance

# constant bias
class ABiasSt(ANoiseSt):

    def __init__(self,f1,f2,m,b):
        ANoiseSt.__init__(self,f1,f2,variance=False)
        self._slope = m;
        self._offset = b;

class ADeclSignalSt(ASignalStmt):

    def __init__(self,f1,f2,name,idx,variance=True):
        ASignalSt.__init__(self,self._index)
        self._index = idx
        self._variance = variance


class ACopySignalSt(ASignalStmt):

    def __init__(self,idx,idx2):
        ASignalStmt.__init__(self,idx)
        self._target_idx = idx2

# noise with a particular sigma
class AUncorrNoiseSt(ANoiseSt):

    def __init__(self,f1,f2,m,b):
        ANoiseSt.__init__(self,f1,f2)
        self._slope = m;
        self._offset = b;

class AFreqShiftSt(ASignalStmt):

    def __init__(self,idx,fshift_scale,fshift_offset):
        ASignalSt.__init__(self,idx)
        self._offset = fshift_offset
        self._scale = fhshift_scale

class APhaseShift(ASignalStmt):

    def __init__(self,idx,pshift_scale,phshift_offset):
        ASignalSt.__init__(self,idx)
        self._offset = pshift_offset
        self._scale = phshift_scale

class ASignalScale(ASignalStmt):

    def __init__(self,idx,scale,offset):
        ASignalSt.__init__(self,idx)
        self._scale = scale
        self._offset = offset

class AnalyticalNoiseModel:

    def __init__(self):
        self._prog = []
        self._var = 0

    def new_variable(self):
        v = self._var
        self._var += 1
        return v

    def add(self,stmt):
        self._prog.append(stmt)

room_temp = 25

def thermal_noise(self,noise_model,fmin,fmax):
    T = 273 + room_temp
    # Boltzmann constant in eV
    kb = 0.013
    # 1 ohm
    R = 1.0
    ampl = 4.0*kb*T*R/(fmax-fmin)
    noise_model.add(UncorrNoise(fmin,fmax,0,ampl))

def shot_noise(self,noise_model,fmin,fmax):
    raise NotImplementedError

def flicker_noise(self,noise_model,fmin,fmax):
    def ampl(freq):
        W = 1e-6
        L = 1e-6
        Cox = 1e6
        K = 273+room_temp
        return K/(Cox*W*L*freq)

    nsegs = 10.0
    delta = (fmax-fmin)/nsegs
    for seg_no in range(0,nsegs):
        fl,fh = seg_no*delta,(seg_no+1)*delta
        al,ah = ampl(fl),ampl(fh)
        slope = (ah-al)/(fh-fl)
        offset = al
        noise_model.add(UncorrNoise(fl,fh,slope,offset))


def correlation_noise(self,noise_model,signal):
    raise NotImplementedError

def harmonic_noise(self,noise_model,signal):
    n_harm = 5;
    for harm in range(0,n_harm):
        magnitude = 1.0/(harm+2)
        harm = noise_model.new_variable()
        noise_model.add(ADeclareSignalStatement(signal,harm,variance=False))
        noise_model.add(AFreqShiftSt(harm,(harm+1),0))
        noise_model.add(ASignalScale(harm,magnitude))


