
def benchmark_bmmrxn():
    prob = MathProg("bmmrxn")
    params = {
        'E0' : 4.4,
        'S0' : 6.4,
        'ES0' : 0.0,
        'P0' : 0.0,
        'kf' : 0.01,
        'kr' : 1.24,
        'kd': 1e-3,
        'krkd' : 1.24+1e-3
    }

    E = parse_fn('{E0}-ES-P',params)
    S = parse_fn('{S0}-ES-P',params)
    ES = parse("{kf}*E*S - {krkd}*ES", "ES0", ":z", params)
    P = parse("{kd}*ES","P0",":w", params)
    prob.bind("E",E)
    prob.bind("S",S)
    prob.bind("ES",ES)
    prob.bind("P",P)
    prob.set_interval("E",0,params['E0'])
    prob.set_interval("S",0,params['S0'])
    max_ES = min(params['E0'],params['S0'])
    prob.set_interval("ES",0,max_ES)
    prob.set_interval("P",0,max_ES)
    prob.set_interval("enz-sub",0,max_ES)
    prob.bind("enz-sub", op.Emit(op.Var("ES")))
    prob.compile()
    return prob
