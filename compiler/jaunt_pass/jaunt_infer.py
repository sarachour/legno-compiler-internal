import gpkit
import itertools

import lab_bench.lib.chipcmd.data as chipcmd

from chip.config import Labels
import chip.cont as cont
import chip.props as props
from chip.conc import ConcCirc

from compiler.common import infer
from compiler.jaunt_pass.jenv import JauntInferEnv, JauntVarType
from compiler.jaunt_pass.expr_visitor import ExprVisitor, SCFPropExprVisitor
from compiler.jaunt_pass.objective.obj_mgr import JauntObjectiveFunctionManager

import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jaunt_common as jaunt_common

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
                jaunt_util.cstr_in_interval(jenv,jop.JVar(jvar),
                                        interval.Interval.type_infer(1.0,1.0),
                                        ival)

        visitor = ScaleModelExprVisitor(jenv,circ,block,loc)
        for lhs,rhs in scale_model.eqs():
            j_lhs = visitor.visit_expr(lhs)
            j_rhs = visitor.visit_expr(rhs)
            jenv.eq(j_lhs,j_rhs)

def sc_build_jaunt_env(prog,circ):
    jenv = JauntInferEnv()
    # declare scaling factors
    infer.clear(circ)
    infer.infer_intervals(prog,circ)
    infer.infer_bandwidths(prog,circ)
    jaunt_common.decl_scale_variables(jenv,circ)
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

def sc_alog_bandwidth_constraint(jenv,circ,mbw,hwbw):
    tau = jop.JVar(jenv.TAU)
    if hwbw.unbounded_lower() and hwbw.unbounded_upper():
        return

    if mbw.is_infinite():
        return

    physbw = bputil_to_phys_bandwidth(circ,mbw.bandwidth)
    jenv.use_tau()
    if hwbw.upper > 0:
        jenv.lte(jop.JMult(tau,jop.JConst(physbw)), \
                 jop.JConst(hwbw.upper))
    else:
        jenv.fail()

    if hwbw.lower > 0:
        jenv.gte(jop.JMult(tau,jop.JConst(physbw)), \
                 jop.JConst(hwbw.lower))

def sc_alog_oprange_constraint(jenv,prop,scale_expr,mrng,hwrng):
    jaunt_util.cstr_upper_bound(jenv, scale_expr, mrng.upper, hwrng.upper)
    jaunt_util.cstr_lower_bound(jenv, scale_expr, mrng.lower, hwrng.lower)
    if mrng.spread == 0.0:
        return

    if isinstance(prop, props.AnalogProperties):
        if abs(mrng.lower) > 0:
            jaunt_util.cstr_lower_bound(jenv,scale_expr,abs(mrng.lower), \
                                    prop.min_signal())
        if abs(mrng.upper) > 0:
            jaunt_util.cstr_lower_bound(jenv,scale_expr,abs(mrng.upper), \
                                           prop.min_signal())


def sc_interval_constraint(jenv,circ,block,loc,port,handle=None):
    config = circ.config(block.name,loc)
    mrng = config.interval(port)
    mbw = config.bandwidth(port)
    # expression for scaling math range
    scfvar = jop.JVar(jenv.get_scvar(block.name,loc,port,handle))
    oprngvar = jop.JVar(jenv.get_op_range_var(block.name,loc,port,handle), \
                        exponent=-1.0)
    scale_expr = jop.JMult(scfvar,oprngvar)

    scale_model = block.scale_model(config.comp_mode)
    baseline = scale_model.baseline
    print(block.name)
    prop = block.props(config.comp_mode,baseline,port,handle=handle)
    hwrng,hwbw = prop.interval(), prop.bandwidth()
    if isinstance(prop, props.AnalogProperties):
        sc_alog_oprange_constraint(jenv,prop,scale_expr,mrng,hwrng)
        sc_alog_bandwidth_constraint(jenv,circ,mbw,hwbw)

    elif isinstance(prop, props.DigitalProperties):
        sc_alog_oprange_constraint(jenv,prop,scale_expr,mrng,hwrng)
        sc_dig_quantize_constraint(jenv,scfvar, \
                                   mrng,\
                                   prop)
        sc_dig_bandwidth_constraint(jenv,prob,circ, \
                                    mbw,
                                    prop)
    else:
        raise Exception("unknown")

def sc_generate_problem(jenv,prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out in block.outputs:
            # ensure we can propagate the dynamics
            sc_traverse_dynamics(jenv,circ,block,loc,out)

        for port in block.outputs + block.inputs:
            for handle in block.handles(config.comp_mode,port):
                sc_interval_constraint(jenv,circ,block,loc,out,handle=handle)

            sc_interval_constraint(jenv,circ,block,loc,out)

    if not jenv.uses_tau():
        jenv.eq(jop.JVar(jenv.TAU), jop.JConst(1.0))
    else:
        jenv.lte(jop.JVar(jenv.TAU), jop.JConst(1e10))
        jenv.gte(jop.JVar(jenv.TAU), jop.JConst(1e-10))


def infer_scale_config(prog,circ):
  assert(isinstance(circ,ConcCirc))
  jenv = sc_build_jaunt_env(prog,circ)
  jopt = JauntObjectiveFunctionManager(jenv)
  for optcls in JauntObjectiveFunctionManager.basic_methods():
    jopt.method = optcls.name()
    print("===== %s =====" % optcls.name())
    for idx,(gpprob,obj) in \
        enumerate(build_gpkit_problem(circ,jenv,jopt)):
      print("-> %s" % optcls.name())
      if gpprob is None:
        continue

