import chip.props as props
from chip.conc import ConcCirc
import lab_bench.lib.chipcmd.data as chipcmd
from compiler.common import infer
from chip.config import Labels
import ops.op as ops
import gpkit
import itertools
import compiler.jaunt_pass.phys_opt as physoptlib
import compiler.jaunt_pass.basic_opt as boptlib
import compiler.jaunt_pass.scalecfg_opt as scalelib
from compiler.jaunt_pass.common import JauntEnv, JauntObjectiveFunctionManager
import compiler.jaunt_pass.common as jcomlib
import ops.jop as jop
import ops.op as op
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


def sc_decl_scale_model_variables(circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        scale_model = block.scale_model(config.comp_mode)
        input()

def sc_build_jaunt_env(prog,circ):
    jenv = JauntScaleModelEnv()
    # declare scaling factors
    infer.clear(circ)
    infer.infer_intervals(prog,circ)
    infer.infer_bandwidths(prog,circ)
    jcomlib.decl_scale_variables(jenv,circ)
    #custom
    sc_decl_scale_model_variables(circ)
    sc_generate_problem(jenv,prog,circ)
    return jenv


def sc_generate_problem(jenv,prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out in block.outputs:
            bpgen_traverse_dynamics(jenv,circ,block,loc,out)

        for port in block.outputs + block.inputs:
            properties = config.props(block,port)
            mrng = config.interval(port)
            hwrng = config.op_range(port)
            if mrng is None:
                #print("[skip] not in use <%s[%s].%s>" % \
                #      (block_name,loc,port))
                continue

            scfvar = jop.JVar(jenv.get_scvar(block_name,loc,port))
            mbw = config.bandwidth(port)
            bpgen_scaled_analog_interval_constraint(jenv,scfvar, \
                                                    mrng,hwrng,
                                                    properties)
            # make sure digital values are large enough to register.
            if isinstance(properties,props.DigitalProperties):
                bpgen_scaled_digital_quantize_constraint(jenv,scfvar, \
                                                         mrng,\
                                                         properties)
                bpgen_scaled_digital_bandwidth_constraint(jenv,prob,circ, \
                                                          mbw,
                                                          properties)
            else:
                hwbw = properties.bandwidth()
                bpgen_scaled_analog_bandwidth_constraint(jenv,\
                                                         circ, \
                                                         mbw,hwbw)

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

