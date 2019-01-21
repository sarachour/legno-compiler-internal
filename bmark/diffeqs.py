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
    K = 40.0
    params = {
        'LacLm0':0,
        'clm0':0,
        'TetRm0':0,
        'LacLp0':0,
        'clp0':0,
        'TetRp0':0,
        'a_tr':0.4995,
        'a0_tr':0.0005,
        'k_tl': 3.01029995664,
        'kd_prot': 0.03010299956,
        'kd_mrna' : 0.15051499783,
        'kf_bind':0.1,
        'kd_bind':0.1/K

    }
    LacLm_ic = 0.5
    clm_ic = 0.25
    TetRm_ic = 0.12

    kd_mrna = 0.15051499783
    a0_tr = 0.0005
    prob = MathProg("repri")

    LacLm  = parse('({a0_tr}+Aclp-{kd_mrna}*LacLm)', \
                   'LacLm0',':a',params)

    clm = parse('({a0_tr}+ATetRp-{kd_mrna}*clm)', \
                   'clm0',':b',params)

    TetRm = parse('({a0_tr}+ALacLp-{kd_mrna}*TetRm)', \
                  'TetRm0',':c',params)

    mrna_bnd = 2.5
    prob.bind("LacLm",LacLm)
    prob.bind("clm",clm)
    prob.bind("TetRm",TetRm)
    prob.set_interval("LacLm",0,mrna_bnd)
    prob.set_interval("clm",0,mrna_bnd)
    prob.set_interval("TetRm",0,mrna_bnd)

    LacLp = parse('{k_tl}*LacLm - {kd_prot}*LacLp', \
                  'LacLp0',':d',params)
    clp = parse('{k_tl}*clm - {kd_prot}*clp', \
                  'clp0',':e',params)
    TetRp = parse('{k_tl}*TetRm - {kd_prot}*TetRp', \
                  'TetRp0',':f',params)

    prot_bnd = 150
    prob.bind("LacLp",LacLp)
    prob.bind("clp",clp)
    prob.bind("TetRp",TetRp)
    prob.set_interval("LacLp",0,prot_bnd)
    prob.set_interval("clp",0,prot_bnd)
    prob.set_interval("TetRp",0,prot_bnd)


    ALacLp = parse('{kf_bind}*({a_tr}-ALacLp) - {kd_bind}*ALacLp*LacLp*LacLp',
                   'a_tr',':g',params)

    ATetRp = parse('{kf_bind}*({a_tr}-ATetRp) - {kd_bind}*ATetRp*TetRp*TetRp',
                   'a_tr',':g',params)

    Aclp = parse('{kf_bind}*({a_tr}-Aclp) - {kd_bind}*Aclp*clp*clp',
                   'a_tr',':g',params)

    prob.bind("ALacLp",ALacLp)
    prob.bind("Aclp",Aclp)
    prob.bind("ATetRp",ATetRp)

    act_bnd = params['a_tr']
    prob.set_interval("ALacLp",0,act_bnd)
    prob.set_interval("Aclp",0,act_bnd)
    prob.set_interval("ATetRp",0,act_bnd)
    prob.compile()
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
        'mu': 1.2,
        'Y0': 0.5,
        'X0': 0.0,
        'time': 100
    }
    Y = parse('(Y*{mu}*(1.0-X*X) - X)','Y0',':v',params)
    X = parse('Y','X0',':u',params)
    prob.bind("X",X)
    prob.bind("Y",Y)
    prob.bind("y",op.Emit(op.Var("Y")))
    prob.set_interval("X",-2.2,2.2)
    prob.set_interval("Y",-3.2,3.2)
    prob.set_interval("y",-3.2,3.2)
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
    benchmark_vanderpol(),
    benchmark_reprissilator()
]

def get_prog(name):
    for bmark in BMARKS:
        if bmark.name == name:
            return bmark

    raise Exception("unknown benchmark: <%s>" % name)
