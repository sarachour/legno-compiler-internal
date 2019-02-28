import sys
import os
import common
import numpy as np
sys.path.insert(0,os.path.abspath("../../../"))
import chip.phys as phys
import ops.nop as nops
import json

def make_const(v,deterministic):
    if deterministic:
        return nops.NConstRV(v,0.0)
    else:
        return nops.NConstRV(0.0,v)

def make_freq(port,expo):
    return nops.NFreq(port,power=expo)

def make_lin(port,slope,off,deterministic):
    return nops.mkadd([
        nops.mkmult([
            make_const(slope,deterministic),
            make_freq(port,1.0)
        ]),
        make_const(off,deterministic)

    ])

def make_posy(model,port,idx,deterministic,dependent=False):
    get = lambda key : model[key][idx]
    x,y,w = get('x'),get('y'),get('w')
    u,v = get('u'),get('v')
    assert(x >= 0.0)
    assert(y >= 0.0)
    assert(w >= 0.0)
    assert(u >= 0.0)
    assert(v >= 0.0)
    # x*f^u + y*f^v + w
    result = nops.mkadd([
        nops.mkmult([
            make_const(x,deterministic),
            make_freq(port,u)
        ]),
        nops.mkmult([
            make_const(y,deterministic),
            make_freq(port,-v)
        ]),
        make_const(w,deterministic)
    ])
    if dependent:
        result = nops.mkmult([result,nops.NSig(port)])

    return result

def make_expr(model,port,method,idx,deterministic=True,dependent=False):
    if method == 'posy':
        return make_posy(model,port,idx,
                         deterministic=deterministic,
                         dependent=dependent)
    elif method == 'lin':
        return make_lin(model,port,idx,
                        deterministic=deterministic,
                        dependent=dependent)

    else:
        raise Exception("unknown")

def to_nop_expr(indep_dict, dep_dict, break_idx, \
                port, method,\
                deterministic=False):

    indep_expr = make_expr(indep_dict,port,method,break_idx,\
                           deterministic,dependent=False)
    if not dep_dict is None:
        dep_expr = make_expr(dep_dict,port,method,break_idx, \
                             deterministic,dependent=True)

        return nops.mkadd([dep_expr,indep_expr])

    else:
        return indep_expr

print("=== Read Data ===")

filename = sys.argv[1]
port = sys.argv[2]
outfile = sys.argv[3]
basename = filename.split(".")[0]

raw_data = common.load_raw_data(filename)
data = common.process_raw_data(raw_data)
print("=== Fit Data ===")
X = raw_data['freqs']

method = 'posy'
if method == 'posy':
    model = common.compute_posy_nobreaks(basename,X,data)
else:
    raise Exception("unimpl")

ph = phys.PhysicalModel(port)
bias_expr = to_nop_expr(model['ampl_bias_indep'],
                        model['ampl_bias_dep'],
                        0,
                        port=port,
                        method=method,
                        deterministic=True)

noise_expr = to_nop_expr(model['ampl_noise_indep'],
                        model['ampl_noise_dep'],
                        0,
                        port=port,
                        method=method,
                        deterministic=False)

delay_mean = to_nop_expr(model['delay_mean'],
                        None,0,
                        port=port,
                        method=method,
                        deterministic=True)

delay_std = to_nop_expr(model['delay_std'],
                        None,0,
                        port=port,
                        method=method,
                        deterministic=False)

delay_expr = nops.mkadd([delay_mean,delay_std])

ph.delay = delay_expr
ph.noise = noise_expr
ph.bias = bias_expr


with open(outfile,'w') as fh:
  obj= ph.to_json()
  objstr = json.dumps(obj,indent=4)
  fh.write(objstr)
