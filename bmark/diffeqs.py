from lang.prog import MathProg
from ops import op, opparse
'''
def benchmark_smmrxn():
    prob = MathProg("smmrxn")
    kf = 0.5
    kr = 0.1
    E0 = 1.2
    S0 = 2.4
    ES = op.Integ(op.Add(
        op.Mult(op.Const(kf),
                op.Mult(op.Var("S"),op.Var("E"))),
        op.Mult(op.Const(-1*kr),op.Var("ES"))), op.Const(0),
                  handle=':z')

    E = op.Add(op.Const(E0),
               op.Mult(op.Var("ES"), op.Const(-1)))

    S = op.Add(op.Const(S0),
               op.Mult(op.Var("ES"), op.Const(-1)))

    prob.bind("E",E)
    prob.bind("S",S)
    prob.bind("ES",ES)
    prob.interval("E",0,E0)
    prob.interval("S",0,S0)
    prob.interval("ES",0,min(E0,S0))
    prob.interval("enz-sub",0,min(E0,S0))
    prob.bind("enz-sub", op.Emit(op.Var("ES")))
    prob.compile()
    return prob


def benchmark_bmmrxn():
    prob = MathProg("bmmrxn")
    kf = 0.1
    kr = 0.05
    E0 = 4400
    S0 = 6600
    ES = op.Integ(op.Add(
        op.Mult(op.Const(kf),
                op.Mult(op.Var("S"),op.Var("E"))),
        op.Mult(op.Const(-1*kr),op.Var("ES"))), op.Const(0),
                  handle=':z')

    E = op.Add(op.Const(E0),
               op.Mult(op.Var("ES"), op.Const(-1)))

    S = op.Add(op.Const(S0),
               op.Mult(op.Var("ES"), op.Const(-1)))

    prob.bind("E",E)
    prob.bind("S",S)
    prob.bind("ES",ES)
    prob.interval("E",0,E0)
    prob.interval("S",0,S0)
    prob.interval("ES",0,min(E0,S0))
    prob.interval("enz-sub",0,min(E0,S0))
    prob.bind("enz-sub", op.Emit(op.Var("ES")))
    prob.compile()
    return prob
'''

def parse(expr,ic, handle,params):
    deriv = opparse.parse(expr.format(**params))
    const = params[ic]
    return op.Integ(deriv,op.Const(const),handle=handle)

def benchmark_p53stoch():
    raise Exception("not implemented")


def benchmark_reprissilator():
    LacLm_ic = 0.5
    clm_ic = 0.25
    TetRm_ic = 0.12

    kd_mrna = 0.15051499783
    a0_tr = 0.0005
    prob = MathProg("repri")

    '''
    LacLm_dt = op.Op.parse("((%f + (TRLacLp)) - (%f*(LacLm)))", % (a0_tr, kd_mrna))
    clm_dt = op.Op.parse("((%f + (TRclp)) - (%f*(clm)))", % (a0_tr, kd_mrna))
    TetRm_dt = op.Op.parse("((%f + (TRTetRp)) - (%f*(TetRm)))", % (a0_tr, kd_mrna))

    prob.bind("LacLm",op.Integ(LacLm_dt,LAcLm_ic))
    prob.bind("clm",op.Integ(clm_dt,clm_ic))
    prob.bind("TetRm",op.Integ(TetRm_dt,TetRm_ic))

    LacLp_ic = 60
    clp_ic = 20
    TetRp_ic = 40

    k_tl = 3.01029995664
    kd_prot = 0.03010299956
    LacLp_dt = op.Op.parse("((%f*(LacLm)) - (%f*(LacLp)))" % (k_tl, kd_prot))
    clp_dt = op.Op.parse("((%f*(clm)) - (%f*(clp)))" % (k_tl, kd_prot))
    TetRp_dt = op.Op.parse("((%f*(TetRm)) - (%f*(TetRp)))" % (k_tl, kd_prot))

    prob.bind("LacLp",op.Integ(LacLp_dt,LAcLp_ic))
    prob.bind("clp",op.Integ(clp_dt,clp_ic))
    prob.bind("TetRp",op.Integ(TetRp_dt,TetRp_ic))

    n = 2
    a_tr  = 0.4995
    # K = Kd**2
    K = 20
    Kmp = math.sqrt(K)

    TRTetR_ic = a_tr
    # kf*(a_tr-*TetRp)*TetRp^2 - k_d*ITetRp
    # 2 TetRp + Act -> INH_TetRp, INH_TetRp + ACT_TetRp = a_tr
    # Act(0) = a_tr, Act' = k_d*(a_tr-Act) - k_f*Act*TetRp^2
    #------------------------------
    ACT_TetRp_dt = op.Op.parse("((%f)*(%f-ACTTetRp))-(%f*(ACTTetRp*(TetRp*TetRp)))" * (kf,a_tr,kd))
    ACT_clp_dt = op.Op.parse("((%f)*(%f-ACTclp))-(%f*(ACTclp*(clp*clp)))" * (kf,a_tr,kd))
    ACT_LacLp_dt = op.Op.parse("((%f)*(%f-ACTLacLp))-(%f*(ACTLacLp*(LacLp*LacLp)))" * (kf,a_tr,kd))

    prob.bind("ACTTetRp", op.Integ(ACT_TetRp_dt,a_tr))
    prob.bind("ACTclp", op.Integ(ACT_clp_dt,a_tr))
    prob.bind("ACTLacLp", op.Integ(ACT_LacLp_dt,a_tr))
    raise Exception("not implemented")
    '''
    return prob

def benchmark_spring():
    prob = MathProg("spring")
    dy2 = op.Add(
        op.Mult(op.Var("dy1"),op.Const(-0.2)),
        op.Mult(op.Var("y"),op.Const(-0.8))
    )
    dy1 = op.Integ(dy2, op.Const(-2),":z")
    y = op.Integ(op.Var("dy1"), op.Const(9),":w")

    prob.bind("dy1",dy1)
    prob.bind("y",y)
    prob.bind("Y", op.Emit(op.Var("y")))
    prob.set_interval("Y",-10,10)
    prob.set_interval("y",-10,10)
    prob.set_interval("dy1",-10,10)
    prob.compile()
    return prob

def benchmark_vanderpol():
    # y'' - u(1-y^2)*y'+y = 0
    # separated
    # y1' = y2
    # y2' = u*(1-y1*y1)*y2 - y1
    prob = MathProg("vanderpol")
    params = {
        'mu': 5.0,
        'Y0': 0.5,
        'X0': 0.0,
        'time': 100
    }
    Y = parse('(Y*{mu}*(1.0-X*X) - X)','Y0',':v',params)
    X = parse('Y','X0',':u',params)
    prob.bind("X",X)
    prob.bind("Y",Y)
    prob.bind("y",op.Emit(op.Var("Y")))
    prob.set_interval("X",-3,3)
    prob.set_interval("Y",-9,9)
    prob.set_interval("y",-9,9)
    prob.compile()
    return prob

def benchmark_inout1():
    prob = MathProg("inout1")
    prob.bind('O', op.Emit(
        op.Mult(op.ExtVar("I"),
                op.Const(0.5))
    ))
    prob.set_bandwidth("I",1e4)
    prob.set_interval("I",0,5)
    prob.set_interval("O",0,5)
    prob.compile()
    return prob


def benchmark_inout2():
    prob = MathProg("inout2")
    prob.bind('O1', op.Emit(
        op.Mult(op.ExtVar("I1"),
                op.Const(0.5))
    ))
    prob.bind('O2', op.Emit(
        op.Mult(op.ExtVar("I2"),
                op.Const(0.8))
    ))
    prob.set_bandwidth("I1",1e4)
    prob.set_interval("I1",0,5)
    prob.set_bandwidth("I2",1e4)
    prob.set_interval("I2",0,5)
    prob.set_interval("O1",0,5)
    prob.set_interval("O2",0,5)
    prob.compile()
    return prob

BMARKS = [
    benchmark_spring(),
    benchmark_inout1(),
    benchmark_inout2(),
    benchmark_vanderpol()
]

def get_prog(name):
    for bmark in BMARKS:
        if bmark.name == name:
            return bmark

    raise Exception("unknown benchmark: <%s>" % name)
