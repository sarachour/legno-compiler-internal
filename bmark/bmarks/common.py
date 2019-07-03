from ops import op, opparse
from scipy.integrate import ode
import matplotlib.pyplot as plt
import numpy as np
import math
import os
import tqdm

def measure_var(prob,invar,outvar):
  prob.bind(outvar,
            op.Emit(op.Mult(op.Const(0.999999), op.Var(invar)), \
                    loc='A0'))


def parse_fn(expr,params):
    expr_conc = expr.format(**params)
    return opparse.parse(expr_conc)


def parse_diffeq(expr,ic, handle,params):
    deriv = opparse.parse(expr.format(**params))
    const = params[ic]
    return op.Integ(deriv,op.Const(const),handle=handle)

def _evaluate(expr,vmap):
    vmap['math'] = math
    return np.real(eval(expr,vmap))

def plot_diffeq(menv,prob,T,Y):
    stvars,ics,derivs,fnvars,fns = prob.build_ode_prob()

    def fn_func(t,values):
        vs = dict(zip(map(lambda v: "%s_" % v, stvars), \
                      values))
        vals = {}
        for fvar in fnvars:
            vals[fvar] = _evaluate(fns[fvar],vs)
        for v in stvars:
            vals[v] = vs['%s_' % v]
        return vals

    cwd = os.getcwd()
    filedir = "%s/BMARK_REF/%s_%s" % (cwd,prob.name,menv.name)

    if not os.path.exists(filedir):
        os.makedirs(filedir)

    Z =dict(map(lambda v: (v,[]), stvars+fnvars))
    for t,y in zip(T,Y):
        for var,value in fn_func(t,y).items():
            Z[var].append(value)

    for series_name,values in Z.items():
        print("%s: %d" % (series_name,len(values)))

    for series_name,values in Z.items():
        filepath = "%s/%s.png" % (filedir,series_name);
        print('plotting %s' % series_name)
        plt.plot(T,values,label=series_name)
        plt.savefig(filepath)
        plt.clf()


def run_diffeq(menv,prob):
    stvars,ics,derivs,fnvars,fns = prob.build_ode_prob()

    def dt_func(t,values):
        vs = dict(zip(map(lambda v: "%s_" % v, stvars), \
                      values))
        for fvar in fnvars:
            vs["%s_" % fvar] = _evaluate(fns[fvar],vs)

        next_vs = {}
        for stvar in stvars:
            next_vs[stvar] = _evaluate(derivs[stvar],vs)

        return list(map(lambda v: next_vs[v],stvars))

    print("[run_diffeq] initializing")

    time = menv.sim_time
    n = 1000.0
    dt = time/n
    r = ode(dt_func).set_integrator('zvode',method='bdf')
    x0 = list(map(lambda v: _evaluate(ics[v],{}),stvars))
    r.set_initial_value(x0,t=0.0)
    T = []
    Y = []
    tqdm_segs = 500
    last_seg = 0
    print("[run_diffeq] running")
    with tqdm.tqdm(total=tqdm_segs) as prog:
        while r.successful() and r.t < time:
            T.append(r.t)
            Y.append(r.y)
            r.integrate(r.t + dt)
            seg = int(tqdm_segs*float(r.t)/float(time))
            if seg != last_seg:
                prog.n = seg
                prog.refresh()
                last_seg = seg

    return T,Y

