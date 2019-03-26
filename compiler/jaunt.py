
from compiler.common import infer

import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jaunt_common as jaunt_common
import compiler.jaunt_pass.jenv as jenvlib
import compiler.jaunt_pass.jenv_smt as jsmt
import compiler.jaunt_pass.jenv_gpkit as jgpkit

from chip.conc import ConcCirc
from compiler.jaunt_pass.objective.obj_mgr import JauntObjectiveFunctionManager
import compiler.jaunt_pass.expr_visitor as exprvisitor
import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jaunt_common as jaunt_common
import compiler.jaunt_pass.jaunt_infer as jaunt_infer


import ops.jop as jop
import ops.op as ops
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
        jaunt_common.analog_op_range_constraint(jenv,prop,scfvar, \
                                                jop.JConst(1.0),mrng,hwrng, \
                                                block.name)
        jaunt_common.analog_bandwidth_constraint(jenv,circ,mbw,hwbw)

    elif isinstance(prop, props.DigitalProperties):
        jaunt_common.digital_op_range_constraint(jenv,prop,scfvar, \
                                                 jop.JConst(1.0),mrng,hwrng, \
                                                 block.name)
        jaunt_common.digital_quantize_constraint(jenv,scfvar,
                                                 jop.JConst(1.0),mrng,prop)
        jaunt_common.digital_bandwidth_constraint(jenv,prob,circ, \
                                                  mbw, prop)
    else:
        raise Exception("unknown")


# traverse dynamics, also including coefficient variable
def sc_traverse_dynamics(jenv,circ,block,loc,out):
    visitor = exprvisitor.SCFPropExprVisitor(jenv,circ,block,loc,out)
    visitor.visit()


def sc_port_used(jenv,block_name,loc,port,handle=None):
    return jenv.in_use((block_name,loc,port,handle), \
                       tag=jenvlib.JauntVarType.SCALE_VAR)

def sc_generate_problem(jenv,prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out in block.outputs:
            # ensure we can propagate the dynamics
            sc_traverse_dynamics(jenv,circ,block,loc,out)

        for port in block.outputs + block.inputs:
            if sc_port_used(jenv,block_name,loc,port):
                sc_interval_constraint(jenv,circ,prob,block,loc,port)

            for handle in block.handles(config.comp_mode,port):
                if sc_port_used(jenv,block_name,loc,port,handle=handle):
                    sc_interval_constraint(jenv,circ,prob,block, \
                                           loc,port,handle=handle)


    if not jenv.uses_tau():
        jenv.eq(jop.JVar(jenv.tau()), jop.JConst(1.0),'tau_fixed')
    else:
        jenv.lte(jop.JVar(jenv.tau()), jop.JConst(1e6),'tau_min')
        jenv.gte(jop.JVar(jenv.tau()), jop.JConst(1e-6),'tau_max')


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
    lut_updates = {}
    for variable,value in sln['freevariables'].items():
        jaunt_util.log_debug("%s = %s" % (variable,value))
        if variable.name == jenv.tau():
            new_circ.set_tau(value)
        else:
            tag,(block_name,loc,port,handle)= jenv.get_jaunt_var_info(variable.name)
            if(tag == jenvlib.JauntVarType.SCALE_VAR):
                new_circ.config(block_name,loc) \
                        .set_scf(port,value,handle=handle)
            elif(tag == jenvlib.JauntVarType.INJECT_VAR):
                new_circ.config(block_name,loc) \
                    .set_inj(port,value)
            else:
                raise Exception("unhandled: <%s>" % tag)

    return new_circ

def compute_scale(prog,circ,objfun):
    assert(isinstance(circ,ConcCirc))
    jenv = sc_build_jaunt_env(prog,circ)
    jopt = JauntObjectiveFunctionManager(jenv)
    jopt.method = objfun.name()
    blacklist = []
    smtenv = jsmt.build_smt_prob(circ,jenv,blacklist=blacklist)
    results = list(jsmt.solve_smt_prob(smtenv,nslns=1))
    if len(results) == 0:
        raise Exception("no solution exists")

    for gpprob,thisobj in \
        jgpkit.build_gpkit_problem(circ,jenv,jopt):
        if gpprob is None:
            continue

        sln = jgpkit.solve_gpkit_problem(gpprob)
        if sln == None:
            print("<< solution is none >>")
            jgpkit.debug_gpkit_problem(gpprob)
            continue

        jopt.add_result(thisobj.tag(),sln)
        new_circ = apply_result(jenv,circ,sln)
        yield thisobj,new_circ

def scale_again(prog,circ,do_physical, do_sweep):
    objs = []
    if do_physical:
        objs += JauntObjectiveFunctionManager.physical_methods()
    if do_sweep:
        objs += JauntObjectiveFunctionManager.sweep_methods()

    for obj in objs:
        for objf,new_circ in compute_scale(prog,circ,obj):
            yield objf.tag(),new_circ

def scale(prog,circ,nslns):
    objs = JauntObjectiveFunctionManager.basic_methods()
    for idx,infer_circ in enumerate(jaunt_infer.infer_scale_config(prog,circ,nslns)):
        for obj in objs:
            for final_obj,final_circ in compute_scale(prog,infer_circ,obj):
                yield idx,final_obj.tag(), final_circ
