'''
import chip.props as props
import lab_bench.lib.chipcmd.data as chipcmd
from compiler.common import infer
from chip.config import Labels
import ops.op as ops
import gpkit
import itertools
import ops.jop as jop
import ops.op as op
import random
import time
import numpy as np
import util.util as util
import tqdm
'''

from compiler.common import infer

import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jaunt_common as jaunt_common
import compiler.jaunt_pass.jenv as jenvlib

from chip.conc import ConcCirc
from compiler.jaunt_pass.objective.obj_mgr import JauntObjectiveFunctionManager
import compiler.jaunt_pass.expr_visitor as exprvisitor
import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jaunt_common as jaunt_common
import compiler.jaunt_pass.jaunt_infer as jaunt_infer


import ops.jop as jop
import chip.props as props
import ops.interval as interval



def sc_interval_constraint(jenv,circ,prob,block,loc,port,handle=None):
    config = circ.config(block.name,loc)
    mrng = config.interval(port)
    mbw = config.bandwidth(port)
    # expression for scaling math range
    scfvar = jop.JVar(jenv.get_scvar(block.name,loc,port,handle))

    prop = block.props(config.comp_mode,config.scale_mode,port,handle=handle)
    hwrng,hwbw = prop.interval(), prop.bandwidth()
    if isinstance(prop, props.AnalogProperties):
        jaunt_common.analog_op_range_constraint(jenv,prop,scfvar,mrng,hwrng)
        jaunt_common.analog_bandwidth_constraint(jenv,circ,mbw,hwbw)

    elif isinstance(prop, props.DigitalProperties):
        jaunt_common.analog_op_range_constraint(jenv,prop,scfvar,mrng,hwrng)
        jaunt_common.digital_quantize_constraint(jenv,scfvar, \
                                   mrng, prop)
        jaunt_common.digital_bandwidth_constraint(jenv,prob,circ, \
                                                  mbw, prop)
    else:
        raise Exception("unknown")


# traverse dynamics, also including coefficient variable
def sc_traverse_dynamics(jenv,circ,block,loc,out):
    if block.name == 'lut':
        raise Exception("need to override lut")
    else:
        visitor = exprvisitor.SCFPropExprVisitor(jenv,circ,block,loc,out)
        visitor.visit()


def sc_generate_problem(jenv,prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out in block.outputs:
            # ensure we can propagate the dynamics
            sc_traverse_dynamics(jenv,circ,block,loc,out)

        for port in block.outputs + block.inputs:
            for handle in block.handles(config.comp_mode,port):
                sc_interval_constraint(jenv,circ,prob,block,loc,out,handle=handle)

            sc_interval_constraint(jenv,circ,prob,block,loc,out)

    if not jenv.uses_tau():
        jenv.eq(jop.JVar(jenv.TAU), jop.JConst(1.0))
    else:
        jenv.lte(jop.JVar(jenv.TAU), jop.JConst(1e10))
        jenv.gte(jop.JVar(jenv.TAU), jop.JConst(1e-10))


def sc_build_jaunt_env(prog,circ,infer=False):
    jenv = jenvlib.JauntEnv()
    # declare scaling factors
    if infer:
        infer.clear(circ)
        infer.infer_intervals(prog,circ)
        infer.infer_bandwidths(prog,circ)

    jaunt_common.decl_scale_variables(jenv,circ)
    # build continuous model constraints
    sc_generate_problem(jenv,prog,circ)
    return jenv

def apply_result(jenv,circ,sln):
    new_circ = circ.copy()
    for variable,value in sln['freevariables'].items():
        print("%s = %s" % (variable,value))
        if variable.name == jenv.TAU:
            new_circ.set_tau(value)
        else:
            block_name,loc,port,handle,tag = jenv.get_jaunt_var_info(variable.name)
            if(tag == jenvlib.JauntVarType.SCALE_VAR):
                new_circ.config(block_name,loc) \
                        .set_scf(port,value,handle=handle)
            else:
                raise Exception("unhandled: lut")

    return new_circ

def compute_scale(prog,circ,objfun):
    assert(isinstance(circ,ConcCirc))
    jenv = sc_build_jaunt_env(prog,circ)
    jopt = JauntObjectiveFunctionManager(jenv)
    jopt.method = objfun.name()
    for gpprob,thisobj in \
        jenvlib.build_gpkit_problem(circ,jenv,jopt):
        if gpprob is None:
            continue

        sln = jenvlib.solve_gpkit_problem(gpprob)
        new_circ = apply_result(jenv,circ,sln)
        yield thisobj,new_circ

def physical_scale(prog,circ):
    for opt,circ in scale_circuit(prog,circ,\
                                  JauntObjectiveFunctionManager.physical_methods()):
        yield opt,circ

def scale(prog,circ):
    for infer_obj,infer_circ in jaunt_infer.infer_scale_config(prog,circ):
        for final_obj,final_circ in compute_scale(prog,infer_circ,infer_obj):
            yield final_obj.name(), final_circ

