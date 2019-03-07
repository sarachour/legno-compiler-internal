import gpkit
import itertools

import lab_bench.lib.chipcmd.data as chipcmd

from chip.config import Labels
import chip.cont as cont
import chip.props as props
from chip.conc import ConcCirc

from compiler.common import infer
import compiler.jaunt_pass.phys_opt as physoptlib
import compiler.jaunt_pass.basic_opt as boptlib
import compiler.jaunt_pass.scalecfg_opt as scalelib
from compiler.jaunt_pass.common import JauntEnv, JauntObjectiveFunctionManager
import compiler.jaunt_pass.common as jcomlib

import ops.jop as jop
import ops.op as ops
import ops.interval as interval

import signal
import random
import time
import numpy as np
import util.util as util
import util.config as CONFIG
import tqdm

class JauntScaleModelEnv(JauntEnv):

    def __init__(self):
        JauntEnv.__init__(self)

    def decl_op_range_var(self,block_name,loc,port,handle=None):
        return self.decl_jaunt_var(block_name,loc,port,handle,
                                   tag=jcomlib.JauntVarType.OP_RANGE_VAR.name)


    def decl_coeff_var(self,block_name,loc,port,handle=None):
        return self.decl_jaunt_var(block_name,loc,port,handle,
                                   tag=jcomlib.JauntVarType.COEFF_VAR.name)

    def get_coeff_var(self,block_name,loc,port,handle=None):
        return self.get_jaunt_var(block_name,loc,port,handle,
                                  tag=jcomlib.JauntVarType.COEFF_VAR.name)

    def get_op_range_var(self,block_name,loc,port,handle=None):
        return self.get_jaunt_var(block_name,loc,port,handle,
                                  tag=jcomlib.JauntVarType.OP_RANGE_VAR.name)

def sc_get_scm_var(jenv,block_name,loc,v):
    if v.type == cont.CSMVar.Type.OPVAR:
        jvar = jenv.get_op_range_var(block_name,loc,v.port,v.handle)
    elif v.type == cont.CSMVar.Type.COEFFVAR:
        jvar = jenv.get_coeff_var(block_name,loc,v.port,v.handle)
    else:
        raise Exception("unknown var type")
    return jvar

def sc_traverse_scm_expr(jenv,circ,block,loc,expr):
    config = circ.config(block.name,loc)
    scale_model = block.scale_model(config.comp_mode)
    if expr.op == ops.OpType.VAR:
        var= scale_model.var(expr.name)
        jaunt_var = sc_get_scm_var(jenv,block.name,loc,var)
        return jop.JVar(jaunt_var)
    elif expr.op == ops.OpType.CONST:
        return jop.JConst(expr.value)

    elif expr.op == ops.OpType.MULT:
        expr1 = sc_traverse_scm_expr(jenv,circ,block,loc,expr.arg1)
        expr2 = sc_traverse_scm_expr(jenv,circ,block,loc,expr.arg2)
        return jop.JMult(expr1,expr2)

    else:
        raise Exception("unimpl: %s" % expr)

def sc_decl_scale_model_variables(jenv,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        scale_model = block.scale_model(config.comp_mode)
        for v in scale_model.variables():
            if v.type == cont.CSMVar.Type.OPVAR:
                jvar = jenv.decl_op_range_var(block_name,loc,v.port,v.handle)
            elif v.type == cont.CSMVar.Type.COEFFVAR:
                jvar = jenv.decl_coeff_var(block_name,loc,v.port,v.handle)
            else:
                raise Exception("unknown")

def sc_generate_scale_model_constraints(jenv,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        scale_model = block.scale_model(config.comp_mode)
        for v in scale_model.variables():
            jvar = sc_get_scm_var(jenv,block_name,loc,v)
            ival = v.interval
            if not ival is None:
                jcomlib.cstr_in_interval(jenv,jop.JVar(jvar),
                                        interval.Interval.type_infer(1.0,1.0),
                                        ival)

        for lhs,rhs in scale_model.eqs():
            j_lhs = sc_traverse_scm_expr(jenv,circ,block,loc,lhs)
            j_rhs = sc_traverse_scm_expr(jenv,circ,block,loc,rhs)
            jenv.eq(j_lhs,j_rhs)

def sc_build_jaunt_env(prog,circ):
    jenv = JauntScaleModelEnv()
    # declare scaling factors
    infer.clear(circ)
    infer.infer_intervals(prog,circ)
    infer.infer_bandwidths(prog,circ)
    jcomlib.decl_scale_variables(jenv,circ)
    # build continuous model constraints
    sc_decl_scale_model_variables(jenv,circ)
    sc_generate_scale_model_constraints(jenv,circ)

    sc_generate_problem(jenv,prog,circ)
    return jenv

# traverse dynamics, also including coefficient variable
def sc_traverse_dynamics(jenv,circ,block,loc,out):
    scfvar = jop.JVar(jenv.get_scvar(block.name,loc,out))
    coeffvar = jop.JVar(jenv.get_coeff_var(block.name,loc,out))
    config = circ.config(block.name,loc)
    if block.name == "lut":
        expr = config.expr(out)
        scexpr = jcomlib.cstr_traverse_expr(jenv,circ,block,loc,out,expr)
        compvar = jop.JVar(jenv.get_scvar(block.name,loc,out, \
                                           handle=jenv.LUT_SCF_OUT))

        # also include coefficient variables
        jenv.eq(scfvar, jop.JMult(jop.JMult(compvar,scexpr),coeffvar))
    else:
        expr = config.dynamics(block,out)
        scexpr = jcomlib.cstr_traverse_expr(jenv,circ,block,loc,out,expr)
        # also include coefficient variables
        jenv.eq(scfvar,jop.JMult(scexpr,coeffvar))



def sc_generate_problem(jenv,prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out in block.outputs:
            sc_traverse_dynamics(jenv,circ,block,loc,out)

        for port in block.outputs + block.inputs:
            print(port)
            for handle in block.handles(config.comp_mode,port):
                print(port,handle)
                input("TODO: add constraints previously added in traverse")

        input("TODO: add operating range constraints")

    if not jenv.uses_tau():
        jenv.eq(jop.JVar(jenv.TAU), jop.JConst(1.0))
    else:
        jenv.lte(jop.JVar(jenv.TAU), jop.JConst(1e10))
        jenv.gte(jop.JVar(jenv.TAU), jop.JConst(1e-10))


def infer_scale_config(prog,circ,objfunmgr):
  assert(isinstance(circ,ConcCirc))
  jenv = sc_build_jaunt_env(prog,circ)
  jopt = JauntObjectiveFunctionManager(jenv)
  for optcls in methods:
    jopt.method = optcls.name()
    print("===== %s =====" % optcls.name())
    for idx,(gpprob,obj) in \
        enumerate(build_gpkit_problem(circ,jenv,jopt)):
      print("-> %s" % optcls.name())
      if gpprob is None:
        continue

