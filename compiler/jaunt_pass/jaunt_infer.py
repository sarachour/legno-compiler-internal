import gpkit
import itertools

import lab_bench.lib.chipcmd.data as chipcmd

from chip.config import Labels
import chip.cont as cont
from chip.conc import ConcCirc

from compiler.common import infer
import compiler.jaunt_pass.jenv as jenvlib
import compiler.jaunt_pass.expr_visitor as exprvisitor
from compiler.jaunt_pass.objective.obj_mgr import JauntObjectiveFunctionManager

import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jaunt_common as jaunt_common

import ops.jop as jop
import ops.op as ops
import chip.props as props
import ops.interval as interval

import signal
import random
import time
import numpy as np
import util.util as util
import util.config as CONFIG
import tqdm

def sc_get_cont_var(jtype,block_name,loc,port,handle):
    if jtype == jenvlib.JauntVarType.OP_RANGE_VAR:
        return cont.CSMOpVar(port,handle)
    elif jtype == jenvlib.JauntVarType.COEFF_VAR:
        return cont.CSMCoeffVar(port,handle)
    else:
        return None

def sc_get_scm_var(jenv,block_name,loc,v):
    if v.type == cont.CSMVar.Type.OPVAR:
        jvar = jenv.get_op_range_var(block_name,loc,v.port,v.handle)
    elif v.type == cont.CSMVar.Type.COEFFVAR:
        jvar = jenv.get_coeff_var(block_name,loc,v.port,v.handle)
    else:
        raise Exception("unknown var type")
    return jvar


class ScaleModelExprVisitor(exprvisitor.ExprVisitor):

    def __init__(self,jenv,circ,block,loc):
        exprvisitor.ExprVisitor.__init__(self,jenv,circ,block,loc,None)

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

class SCFInferExprVisitor(exprvisitor.SCFPropExprVisitor):

    def __init__(self,jenv,circ,block,loc,port):
        exprvisitor.SCFPropExprVisitor.__init__(self,jenv,circ,block,loc,port)

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
                jaunt_util.in_interval_constraint(jenv,jop.JVar(jvar),
                                        interval.Interval.type_infer(1.0,1.0),
                                        ival)

        visitor = ScaleModelExprVisitor(jenv,circ,block,loc)
        for lhs,rhs in scale_model.eqs():
            j_lhs = visitor.visit_expr(lhs)
            j_rhs = visitor.visit_expr(rhs)
            jenv.eq(j_lhs,j_rhs)

def sc_build_jaunt_env(prog,circ):
    jenv = jenvlib.JauntInferEnv()
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


def sc_interval_constraint(jenv,circ,prob,block,loc,port,handle=None):
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
    prop = block.props(config.comp_mode,baseline,port,handle=handle)
    hwrng,hwbw = prop.interval(), prop.bandwidth()
    if isinstance(prop, props.AnalogProperties):
        jaunt_common.analog_op_range_constraint(jenv,prop,scale_expr,mrng,hwrng)
        jaunt_common.analog_bandwidth_constraint(jenv,circ,mbw,hwbw)

    elif isinstance(prop, props.DigitalProperties):
        jaunt_common.analog_op_range_constraint(jenv,prop,scale_expr,mrng,hwrng)
        jaunt_common.digital_quantize_constraint(jenv,scfvar, \
                                   mrng, prop)
        jaunt_common.digital_bandwidth_constraint(jenv,prob,circ, \
                                                  mbw, prop)
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
                sc_interval_constraint(jenv,circ,prob,block,loc,out,handle=handle)

            sc_interval_constraint(jenv,circ,prob,block,loc,out)

    if not jenv.uses_tau():
        jenv.eq(jop.JVar(jenv.TAU), jop.JConst(1.0))
    else:
        jenv.lte(jop.JVar(jenv.TAU), jop.JConst(1e10))
        jenv.gte(jop.JVar(jenv.TAU), jop.JConst(1e-10))


def apply_result(jenv,circ,sln):
    ctxs = {}
    for variable,value in sln['freevariables'].items():
        if variable.name == jenv.TAU:
            continue
        else:
            block_name,loc,port,handle,tag = jenv.get_jaunt_var_info(variable.name)
            if not (block_name,loc) in ctxs:
                config = circ.config(block_name,loc)
                model = circ.board.block(block_name).scale_model(config.comp_mode)
                ctxs[(block_name,loc)] = cont.ContinuousScaleContext(model)


            contvar = sc_get_cont_var(tag,block_name,loc,port,handle)
            if not contvar is None:
                ctxs[(block_name,loc)].assign(contvar,value)

    for (block_name,loc),ctx in ctxs.items():
        print("=== %s[%s] ===" % (block_name,loc))
        scale_mode = ctx.model.scale_mode(ctx)
        circ.config(block_name,loc).set_scale_mode(scale_mode)

    return circ

def infer_scale_config(prog,circ):
    assert(isinstance(circ,ConcCirc))
    jenv = sc_build_jaunt_env(prog,circ)
    jopt = JauntObjectiveFunctionManager(jenv)
    for optcls in JauntObjectiveFunctionManager.basic_methods():
        jopt.method = optcls.name()
        print("===== %s =====" % optcls.name())
        for idx,(gpprob,obj) in \
            enumerate(jenvlib.build_gpkit_problem(circ,jenv,jopt)):
            if gpprob is None:
                continue

            print("-> %s" % optcls.name())
            sln = jenvlib.solve_gpkit_problem(gpprob)
            if sln is None:
                print("[[FAILURE - NO SLN]]")
                jenv.set_solved(False)
                jenvlib.debug_gpkit_problem(gpprob)
                return
            else:
                jenv.set_solved(True)

            apply_result(jenv,circ,sln)
            yield circ
            jopt.add_result(obj.tag(),sln)
            yield obj,sln
