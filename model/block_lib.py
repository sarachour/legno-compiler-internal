import block_model as bmodel
import noise_model as nzmodel

class SummerModel(bmodel.LinearBlockModel):

    def __init__(self):
        LinearBlockModel.__init__("+", \
                                  ['a','b','c','d'],"z",
                                  [1.0,1.0,1.0,1.0],0)

class InvModel(bmodel.LinearBlockModel):

    def __init__(self):
        LinearBlockModel.__init__("*c", \
                                  ['a'],"z",
                                  [-1],0)

class DACModel(bmodel.LinearBlockModel):

    def __init__(self,coeff):
        assert(coeff >= 0)
        LinearBlockModel.__init__("dac", \
                                  ['a'],"z",
                                  [1.0],0)

class GainModel(bmodel.LinearBlockModel):

    def __init__(self,coeff):
        assert(coeff >= 0)
        LinearBlockModel.__init__("*c", \
                                  ['a'],"z",
                                  [coeff],0)


class IntegModel(bmodel.LinearBlockModel):

    def __init__(self):
        assert(coeff >= 0)
        LinearBlockModel.__init__("integ", \
                                  ['a'],"z",
                                  [1.0],0,integrate=True)

class MultModel(bmodel.BlockModel):

    def __init__(self):
        BlockModel("*",BlockModel.MODE_TIME_ONLY,['x','y'],'z')


        def signal_time_domain(self,state,time,inputs):
            return inputs['x']*inputs['y']


class LPFilter():
    def __init__(self,lf):
        BlockModel("lpf",BlockModel.MODE_FREQ_ONLY,['x'],'z')
        self._freq_cutoff = lf

class HPFilter():
    def __init__(self,hf):
        BlockModel("lpf",BlockModel.MODE_FREQ_ONLY,['x'],'z')
        self._freq_cutoff = hf


class BPFilter():
    def __init__(self,lf,hf):
        BlockModel("bpf",BlockModel.MODE_FREQ_ONLY,['x'],'z')
        self._low_freq_cutoff = lf
        self._hi_freq_cutoff = hf


# build a block-diagram model.
def michaelis():
    sys = System()
    gnd = GndModel()
    E0 = 1.0
    e0 = sys.add(InvModel())
    e1 = sys.add(SummerModel())
    e2 = sys.add(DACModel(E0))
    sys.conn(e2,'z',e1,'a')
    sys.conn(e0,'z',e1,'b')
    sys.conn(gnd,'z',e1,'c')
    sys.conn(gnd,'z',e1,'d')
    sys.emit(e1,'z')

    s0 = sys.add(InvModel())
    s1 = sys.add(SummerModel())
    s2 = sys.add(DACModel(S0))
    sys.conn(s2,'z',s1,'a')
    sys.conn(s0,'z',s1,'b')
    sys.conn(gnd,'z',s1,'c')
    sys.conn(gnd,'z',s1,'d')
    sys.emit(s1,'z')


    es0 = sys.add(MultModel())
    es1 = sys.add(GainModel(kf))
    es2 = sys.add(InvModel())
    es3 = sys.add(GainModel(kr))
    es4 = sys.add(SummerModel())
    es5 = sys.add(IntegModel())
    sys.conn(s1,'z',es0,'x')
    sys.conn(e1,'z',es0,'y')
    # kf*E*S
    sys.conn(es0,'z',es1,'a')
    sys.conn(es1,'z',es4,'a')

    # -kr*ES
    sys.conn(es5,'z',es3,'a')
    sys.conn(es3,'z',es2,'a')
    sys.conn(es2,'z',es4,'a')
    sys.conn(es4,'z',es5,'a')

    sys.conn(es5,'z',e0,'a')
    sys.conn(es5,'z',s0,'a')
    return sys
