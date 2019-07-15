
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
from chip.model import ModelDB
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
        print("%s = %s" % (variable,value))
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

def compute_scale(jenv,prog,infer_circ,objfun):
    assert(isinstance(infer_circ,ConcCirc))
    print("build environment")
    jenv = sc_build_jaunt_env(jenv,prog,infer_circ)
    jopt = JauntObjectiveFunctionManager(jenv)
    jopt.method = objfun.name()

    print("objective: %s" % objfun.name())
    for gpvars,gpprob,thisobj in \
        jgpkit.build_gpkit_problem(infer_circ,jenv,jopt):
        if gpprob is None:
            print("<< could not build geometric problem>>")
            continue

        print("solve")
        sln = jgpkit.solve_gpkit_problem(gpprob)
        #jgpkit.validate_gpkit_problem(jenv,gpvars,sln)
        if sln == None:
            print("<< solution is none >>")
            jgpkit.debug_gpkit_problem(gpprob)
            input()
            continue

        jopt.add_result(thisobj.tag(),sln)
        new_circ = apply_result(jenv,infer_circ,sln)
        yield thisobj,new_circ

def report_missing_models(model,circ):
    for block,loc,port,comp_mode,scale_mode in ModelDB.MISSING:
        config = circ.config(block,loc)
        jaunt_physlog.log(circ,block,loc, \
                          config,
                          comp_mode,
                          scale_mode)
        msg = "NO model: %s[%s].%s %s %s error" % \
              (block,loc,port, \
               comp_mode,scale_mode)

def scale(prog,circ,nslns, \
          model='physical', \
          digital_error=0.05, \
          analog_error=0.05, \
          max_freq=None, \
          do_log=True):
    infer.clear(circ)
    infer.infer_intervals(prog,circ)
    infer.infer_bandwidths(prog,circ)
    objs = JauntObjectiveFunctionManager.basic_methods()
    n_missing = 0
    for idx,infer_circ in enumerate(jaunt_infer.infer_scale_config(prog, \
                                                                   circ, \
                                                                   nslns, \
                                                                   model=model,
                                                                   max_freq=max_freq, \
                                                                   digital_error=digital_error,
                                                                   analog_error=analog_error)):

        for obj in objs:
            jenv = jenvlib.JauntEnv(model=model, \
                                    max_freq=max_freq, \
                                    digital_error=digital_error, \
                                    analog_error=analog_error)

            if model == jenvlib.JauntEnvParams.Model.PHYSICAL and \
               len(ModelDB.MISSING) > n_missing:
                jenv.fail(msg)

            print("missing: %d -> %d" % (n_missing, len(ModelDB.MISSING)))
            n_missing = len(ModelDB.MISSING)
            infer.infer_costs(infer_circ, \
                              propagate_cost=jenv.params.propagate_uncertainty, \
                              model=jenv.params.model)

            for final_obj,final_circ in compute_scale(jenv,prog,infer_circ,obj):
                yield idx,final_obj.tag(),jenv.params.tag(),final_circ

    print("logging: %s" % do_log)
    if do_log:
        report_missing_models(model,circ)
        jaunt_physlog.save()
        if not jaunt_physlog.is_empty() and \
        model == jenvlib.JauntEnvParams.Model.PHYSICAL:
            raise Exception("must calibrate components")

        jaunt_physlog.clear()
