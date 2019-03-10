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
from compiler.jaunt_pass.common import JauntEnv, JauntObjectiveFunctionManager, ExprVisitor, SCFPropExprVisitor, SCFLUTPropExprVisitor
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

class ScaleModelExprVisitor(ExprVisitor):

    def __init__(self,jenv,circ,block,loc):
        ExprVisitor.__init__(self,jenv,circ,block,loc,None)

    def visit_var(self,expr):
        block,loc = self.block,self.loc
        config = self.circ.config(block.name,loc)
        scale_model = block.scale_model(config.comp_mode)
        var= scale_model.var(expr.name)
        jaunt_var = sc_get_scm_var(self.jenv,block.name,loc,var)
        return jop.JVar(jaunt_var)

    def visit_const(self,expr):
        return jop.JConst(expr.value)

    def visit_mult(self,expr):
        expr1 = self.visit_expr(expr.arg1)
        expr2 = self.visit_expr(expr.arg2)
        return jop.JMult(expr1,expr2)

class SCFInferExprVisitor(SCFPropExprVisitor):

    def __init__(self,jenv,circ,block,loc,port):
        SCFPropExprVisitor.__init__(self,jenv,circ,block,loc,port)

    def coeff(self,handle):
      block,loc = self.block,self.loc
      config = self.circ.config(block.name,loc)
      model = block.scale_model(config.comp_mode)
      scale_mode = model.baseline
      coeff_const = block.coeff(config.comp_mode,scale_mode,self.port)
      coeff_var = self.jenv.get_coeff_var(self.block.name,self.loc, \
                                          self.port,handle=handle)
      return jop.JMult(jop.JConst(coeff_const), \
                       jop.JVar(coeff_var))


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

        visitor = ScaleModelExprVisitor(jenv,circ,block,loc)
        for lhs,rhs in scale_model.eqs():
            j_lhs = visitor.visit_expr(lhs)
            j_rhs = visitor.visit_expr(rhs)
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
    if block.name == 'lut':
        raise Exception("need to override lut")
    else:
        visitor = SCFInferExprVisitor(jenv,circ,block,loc,out)
        visitor.visit()

def sc_generate_problem(jenv,prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out in block.outputs:
            # ensure we can propagate the dynamics
            sc_traverse_dynamics(jenv,circ,block,loc,out)

        for port in block.outputs + block.inputs:
            for handle in block.handles(config.comp_mode,port):
                print(port,handle)
                input("TODO: add constraints previously added in traverse")

        print(port)
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

