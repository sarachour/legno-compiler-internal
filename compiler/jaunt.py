
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
import compiler.jaunt_pass.jaunt_physlog as jaunt_physlog


import ops.jop as jop
import ops.op as ops
import chip.props as props
import ops.interval as interval



def sc_interval_constraint(jenv,circ,prob,block,loc,port,handle=None):
    config = circ.config(block.name,loc)
    prop = block.props(config.comp_mode,config.scale_mode,port,handle=handle)
    annot = "%s.%s.%s" % (block.name,loc,port)
    if isinstance(prop, props.AnalogProperties):
        jaunt_common.analog_op_range_constraint(jenv,circ,block,loc,port, handle,\
                                                annot=annot)
        jaunt_common.analog_bandwidth_constraint(jenv,circ,block,loc,port,handle,\
                                                 annot)

    elif isinstance(prop, props.DigitalProperties):
        hwexc = prop.exclude()
        jaunt_common.digital_op_range_constraint(jenv,circ,block,loc,port,handle, \
                                                 annot)
        # phys,prop,scfvar,jop.JConst(1.0),mrng
        jaunt_common.digital_quantize_constraint(jenv,circ,block,loc,port,handle, \
                                                 "")
        jaunt_common.digital_bandwidth_constraint(jenv,prob,circ,block,loc,port,handle,
                                                  annot)
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


    if not jenv.uses_tau() or not jenv.time_scaling:
        print("uses tau: %s" % jenv.uses_tau())
        print("time scale: %s" % jenv.time_scaling)
        jenv.eq(jop.JVar(jenv.tau()), jop.JConst(1.0),'tau_fixed')
        input()
    else:
        jenv.lte(jop.JVar(jenv.tau()), jop.JConst(1e6),'tau_min')
        jenv.gte(jop.JVar(jenv.tau()), jop.JConst(1e-6),'tau_max')
        jaunt_common.max_sim_time_constraint(jenv,prob,circ)


def sc_build_jaunt_env(jenv,prog,circ):
    # declare scaling factors
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

def compute_scale(jenv,prog,circ,objfun):
    assert(isinstance(circ,ConcCirc))
    jenv = sc_build_jaunt_env(jenv,prog,circ)
    jopt = JauntObjectiveFunctionManager(jenv)
    jopt.method = objfun.name()
    blacklist = []
    smtenv = jsmt.build_smt_prob(circ,jenv,blacklist=blacklist)
    if smtenv is None:
        print("failed to build inference problem")
        return

    results = list(jsmt.solve_smt_prob(smtenv,nslns=10))
    if len(results) == 0:
        return

    print("objective: %s" % objfun.name())
    for gpprob,thisobj in \
        jgpkit.build_gpkit_problem(circ,jenv,jopt):
        if gpprob is None:
            print("<< could not build geometric problem>>")
            continue

        sln = jgpkit.solve_gpkit_problem(gpprob)
        if sln == None:
            print("<< solution is none >>")
            jgpkit.debug_gpkit_problem(gpprob)
            input()
            continue

        jopt.add_result(thisobj.tag(),sln)
        new_circ = apply_result(jenv,circ,sln)
        yield thisobj,new_circ


def scale(prog,circ,nslns, \
          model='physical', \
          digital_error=0.05, \
          analog_error=0.05):
    infer.clear(circ)
    infer.infer_intervals(prog,circ)
    infer.infer_bandwidths(prog,circ)
    infer.infer_snrs(prog,circ)
    objs = JauntObjectiveFunctionManager.basic_methods()
    for idx,infer_circ in enumerate(jaunt_infer.infer_scale_config(prog, \
                                                                   circ, \
                                                                   nslns, \
                                                                   model=model,
                                                                   digital_error=digital_error,
                                                                   analog_error=analog_error)):
        for obj in objs:
            jenv = jenvlib.JauntEnv(model=model, \
                                    digital_error=digital_error, \
                                    analog_error=analog_error)
            for final_obj,final_circ in compute_scale(jenv,prog,infer_circ,obj):
                yield idx,final_obj.tag(),jenv.params.tag(),final_circ

    jaunt_physlog.save()
    if not jaunt_physlog.is_empty():
        raise Exception("must calibrate components")
