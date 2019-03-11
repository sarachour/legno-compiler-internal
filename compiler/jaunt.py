import chip.props as props
from chip.conc import ConcCirc
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

import compiler.jaunt_pass.jaunt_infer as jaunt_infer


def bpgen_scaled_analog_interval_constraint(jenv,scale_expr,math_rng,hw_rng,prop):
    bpgen_build_upper_bound(jenv,scale_expr, \
                            math_rng.upper,hw_rng.upper)
    bpgen_build_lower_bound(jenv,scale_expr, \
                            math_rng.lower,hw_rng.lower)

    if math_rng.spread == 0.0:
        return
    if isinstance(prop, props.AnalogProperties):
        MIN_CURRENT = prop.min_signal()
        if abs(math_rng.lower) > 0:
            bpgen_build_lower_bound(jenv,scale_expr,abs(math_rng.lower), \
                                    MIN_CURRENT)
        if abs(math_rng.upper) > 0:
            bpgen_build_lower_bound(jenv,scale_expr,abs(math_rng.upper), \
                                    MIN_CURRENT)



def bpgen_scaled_digital_quantize_constraint(jenv,scale_expr,math_rng,props):
    def compute_bnds(math_val):
        all_values = props.values()
        max_error = props.max_error
        values = list(filter(lambda v: same_sign(v,math_val), all_values))
        hw_val = max(values,key=lambda v: abs(v))
        #hardware delta
        delta_h = np.mean(np.diff(values))
        min_ratio = hw_val/(hw_val*(len(values)-1)/len(values))
        min_step =delta_h*min_ratio
        max_step = props.max_error

        ratio = hw_val / math_val
        delta_m_nom= ratio*delta_h
        return min_step,max_step,delta_m_nom

    lb,ub = math_rng.lower,math_rng.upper
    scale_expr_inv = jop.expo(scale_expr,-1.0)
    if lb < ub:
        # restrict the amount of the quantized space used to ensure reasonable
        # fidelity (quality metric), while leaving a io pair available on either \
        # end for overflow issues.
        if not util.equals(lb,0):
            lb_min,lb_max,lb_nom = compute_bnds(lb)
            bpgen_build_lower_bound(jenv,scale_expr_inv,\
                                    abs(lb_nom),abs(lb_min))
            bpgen_build_upper_bound(jenv,scale_expr_inv,\
                                    abs(lb_nom),abs(lb_max))

        if not util.equals(ub,0):
            ub_min,ub_max,ub_nom = compute_bnds(ub)
            bpgen_build_lower_bound(jenv,scale_expr_inv,\
                                    abs(ub_nom),abs(ub_min))
            bpgen_build_upper_bound(jenv,scale_expr_inv,\
                                    abs(ub_nom),abs(ub_max))

    else:
        if not util.equals(lb,0):
            val_min,val_max,val_nom = compute_bnds(lb)
            bpgen_build_lower_bound(jenv,scale_expr_inv,\
                                    abs(val_nom),abs(val_min))
            bpgen_build_upper_bound(jenv,scale_expr_inv,\
                                    abs(val_nom),abs(val_max))



def bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr):
    config = circ.config(block.name,loc)

    if expr.op == ops.OpType.CONST:
        if expr.tag == 'scf':
            return jop.JConst(expr.value)
        else:
            return jop.JConst(1.0)

    elif expr.op == ops.OpType.VAR:
        scvar = jenv.get_scvar(block.name,loc,expr.name)
        if block.name == 'lut':
            compvar = jenv.get_scvar(block.name,loc,expr.name, \
                                      handle=jenv.LUT_SCF_IN)
            prod = jop.JMult(jop.JVar(scvar),jop.JVar(compvar))
            jenv.lte(jop.JConst(0.99), prod)
            jenv.gte(jop.JConst(1.01), prod)
            return jop.JConst(1.0)
        else:
            return jop.JVar(scvar)

    elif expr.op == ops.OpType.MULT:
        expr1 = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.arg1)
        expr2 = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.arg2)
        return jop.JMult(expr1,expr2)

    elif expr.op == ops.OpType.SGN:
        bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.arg(0))
        return jop.JConst(1.0)

    elif expr.op == ops.OpType.ABS:
        expr = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.arg(0))
        return expr

    elif expr.op == ops.OpType.SQRT:
        expr = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.arg(0))
        new_expr = jop.expo(expr,0.5)
        return new_expr

    elif expr.op == ops.OpType.COS:
        expr = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.arg(0))
        jenv.eq(expr, jop.JConst(1.0))
        return jop.JConst(1.0)


    elif expr.op == ops.OpType.SIN:
        expr = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.arg(0))
        jenv.eq(expr, jop.JConst(1.0))
        return jop.JConst(1.0)

    elif expr.op == ops.OpType.INTEG:
        # derivative and ic are scaled simialrly
        scexpr_ic = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.init_cond)
        scexpr_deriv = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.deriv)
        scvar_deriv = jop.JVar(jenv.get_scvar(block.name,loc,port, \
                                              handle=expr.deriv_handle))
        scvar_state = jop.JVar(jenv.get_scvar(block.name,loc,port, \
                                              handle=expr.handle))
        jenv.eq(scexpr_ic,scvar_state)
        jenv.eq(scexpr_deriv,scvar_deriv)
        scexpr_integ = jop.JMult(jop.JVar(jenv.TAU,exponent=-1)
                                 ,scvar_deriv)

        jenv.eq(scexpr_integ,scvar_state)

        # ranges are contained
        deriv_mrng = config.interval(port,expr.deriv_handle)
        deriv_hwrng = config.op_range(port,expr.deriv_handle)
        prop = config.props(block,port,handle=expr.deriv_handle)
        bpgen_scaled_analog_interval_constraint(jenv, \
                                                scvar_deriv,
                                                deriv_mrng,
                                                deriv_hwrng,
                                                prop)

        st_mrng = config.interval(port,expr.handle)
        st_hwrng = config.op_range(port,expr.handle)
        prop = config.props(block,port,handle=expr.handle)
        bpgen_scaled_analog_interval_constraint(jenv,scvar_state,\
                                                st_mrng,\
                                                st_hwrng,
                                                prop)

        ic_mrng = config.interval(port,expr.ic_handle)
        prop = config.props(block,port,handle=expr.ic_handle)
        bpgen_scaled_analog_interval_constraint(jenv,scvar_state, \
                                                ic_mrng,
                                                st_hwrng,
                                                prop)
        # the handles for deriv and stvar are the same
        jenv.use_tau()
        return scvar_state

    else:
        raise Exception("unhandled <%s>" % expr)


def bputil_to_phys_bandwidth(circ,bw):
    return bw*circ.board.time_constant

def bpgen_traverse_dynamics(jenv,circ,block,loc,out):
    scfvar = jop.JVar(jenv.get_scvar(block.name,loc,out))
    config = circ.config(block.name,loc)
    hwrng = config.op_range(out)
    mrng = config.interval(out)
    if block.name == "lut":
        expr = config.expr(out)
        scexpr = bpgen_scvar_traverse_expr(jenv,circ,block,loc,out,expr)
        compvar = jop.JVar(jenv.get_scvar(block.name,loc,out, \
                                           handle=jenv.LUT_SCF_OUT))

        jenv.eq(scfvar, jop.JMult(compvar,scexpr))
        #jenv.eq(scfvar,scexpr)
    else:
        expr = config.dynamics(block,out)
        scexpr = bpgen_scvar_traverse_expr(jenv,circ,block,loc,out,expr)
        jenv.eq(scfvar,scexpr)


def bpgen_scaled_digital_bandwidth_constraint(jenv,prob,circ,mbw,prop):
    tau = jop.JVar(jenv.TAU)
    tau_inv = jop.JVar(jenv.TAU,exponent=-1.0)
    if mbw.is_infinite():
        return

    physbw = bputil_to_phys_bandwidth(circ,mbw.bandwidth)
    if prop.kind == props.DigitalProperties.Type.CONSTANT:
        assert(mbw.bandwidth == 0)

    elif prop.kind == props.DigitalProperties.Type.CLOCKED:
        hw_sample_rate = prop.sample_rate
        hw_max_samples = prop.max_samples
        m_exptime = prob.max_sim_time
        assert(not m_exptime is None)
        # sample frequency required
        sample_freq = 2.0*physbw
        sample_ival = 1.0/sample_freq
        jenv.gte(jop.JMult(tau_inv,jop.JConst(sample_ival)), \
                           jop.JConst(hw_sample_rate))

        if not hw_max_samples is None:
            jenv.lte(jop.JMult(tau_inv,jop.JConst(m_exptime)),  \
                     jop.JConst(hw_max_samples))

    elif prop.kind == props.DigitalProperties.Type.CONTINUOUS:
        hwbw = prop.bandwidth
        bpgen_scaled_analog_bandwidth_constraint(jenv,circ, \
                                                 mbw,hwbw)
    else:
        raise Exception("unknown not permitted")

def bpgen_scaled_analog_bandwidth_constraint(jenv,circ,mbw,hwbw):
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

def bp_generate_problem(jenv,prob,circ):
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


def build_jaunt_env(prog,circ):
    infer.clear(circ)
    infer.infer_intervals(prog,circ)
    infer.infer_op_ranges(prog,circ)
    infer.infer_bandwidths(prog,circ)
    jenv = JauntEnv()
    # declare scaling factors
    bp_decl_scale_variables(jenv,circ)
    bp_generate_problem(jenv,prog,circ)

    return jenv


def sp_update_lut_expr(expr,output,lutvars):
    repl = {}
    for name,lutvar in lutvars.items():
        repl[name] = op.Mult(op.Const(lutvar), \
                             op.Var(name))

    return op.Mult(
        expr.substitute(repl),
        op.Const(lutvars[output])
    )

def sp_update_circuit(jenv,prog,circ,assigns):
    bindings = {}
    lut_updates = {}
    tau = None
    for variable,value in assigns.items():
        if variable.name == jenv.TAU:
            print("TAU = %s" % (value))
            circ.set_tau(value)
        else:
            print("SCF %s = %s" % (variable,value))
            block_name,loc,port,handle = jenv.get_scvar_info(variable.name)
            if handle == jenv.LUT_SCF_IN or handle == jenv.LUT_SCF_OUT:
                if not (block_name,loc) in lut_updates:
                    lut_updates[(block_name,loc)] = {}
                lut_updates[(block_name,loc)][port] = value
                circ.config(block_name,loc).set_scf(port, \
                                                    handle=handle, \
                                                    scf=value)


            else:
                circ.config(block_name,loc).set_scf(port,handle=handle, \
                                                    scf=value)

    for (block_name,loc),scfs in lut_updates.items():
        cfg = circ.config(block_name,loc)
        for port,expr in cfg.exprs():
            new_expr = sp_update_lut_expr(expr,port,scfs)
            cfg.set_expr(port,new_expr)

    return circ


def iter_scaled_circuits(circ):
    labels = []
    choices = []
    circ_json = circ.to_json()
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        assert(not config.comp_mode is None)
        modes = block.scale_modes(config.comp_mode)
        labels.append((block_name,loc))
        choices.append(modes)


    n_choices = 1
    for ch in choices:
        n_choices *= len(ch)
    with tqdm.tqdm(total=n_choices) as pbar:
        for choice in itertools.product(*choices):
            circ = ConcCirc.from_json(circ.board,circ_json)
            for (block_name,loc),scale_mode in zip(labels,choice):
                #print("%s.%s = %s" % (block_name,loc,scale_mode))
                circ.config(block_name,loc) \
                    .set_scale_mode(scale_mode)

            yield circ
            pbar.update(1)


def files(scale_inds):
    for idx in scale_inds:
        for opt in JauntObjectiveFunction.methods():
            yield idx,opt



def scale_circuit_unknown(prog,circ,methods,debug=True):
    jenv = build_jaunt_env_unknown(prog,circ)
    jopt = JauntObjectiveFunctionManager(jenv)
    for optcls in methods:
        jopt.method = optcls.name()
        slns = []
        print("===== %s =====" % optcls.name())
        for idx,(gpprob,obj) in \
            enumerate(build_gpkit_problem(circ,jenv,jopt)):
            input()

def scale_circuit(prog,circ,methods,debug=True):
    assert(isinstance(circ,ConcCirc))
    jenv = build_jaunt_env(prog,circ)
    jopt = JauntObjectiveFunctionManager(jenv)
    for optcls in methods:
        jopt.method = optcls.name()
        slns = []
        print("===== %s =====" % optcls.name())
        for idx,(gpprob,obj) in \
            enumerate(build_gpkit_problem(circ,jenv,jopt)):
            print("-> %s" % optcls.name())
            if gpprob is None:
                continue

            sln = solve_gpkit_problem(gpprob)
            if sln is None:
                print("[[FAILURE - NO SLN]]")
                jenv.set_solved(False)
                #debug_gpkit_problem(gpprob)
                return

            elif not 'freevariables' in sln:
                print("[[FAILURE - NO FREEVARS]]")
                succ,result = sln
                assert(result is None)
                assert(succ == False)
                jenv.set_solved(False)
                return

            else:
                jenv.set_solved(True)
                slns.append(sln)

            jopt.add_result(obj.tag(),sln)
            upd_circ = sp_update_circuit(jenv,prog,circ.copy(),
                                        sln['freevariables'])
            yield obj.tag(),upd_circ

def physical_scale(prog,circ):
    for opt,circ in scale_circuit(prog,circ,\
                                  JauntObjectiveFunctionManager.physical_methods()):
        yield opt,circ

def scale(prog,circ):
    for result in jaunt_infer.infer_scale_config(prog,circ):
        input("TODO: run with scale variables")
        yield None,None,None

    return
