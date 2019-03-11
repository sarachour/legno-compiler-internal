import ops.jop as jop
import ops.op as ops
import chip.props as props
from enum import Enum
import compiler.jaunt_pass.jaunt_util as jaunt_util
import util.util as util
import numpy as np

def decl_scale_variables(jenv,circ):
    # define scaling factors
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            jenv.decl_scvar(block_name,loc,output)
            for handle in block.handles(config.comp_mode,output):
                jenv.decl_scvar(block_name,loc,output,handle=handle)

            if block.name == "lut":
                jenv.decl_scvar(block_name,loc,output, \
                                handle=jenv.LUT_SCF_OUT)
                pass

        for inp in block.inputs:
            jenv.decl_scvar(block_name,loc,inp)
            if block.name == "lut":
                jenv.decl_scvar(block_name,loc,inp, \
                                handle=jenv.LUT_SCF_IN)
                pass

        for output in block.outputs:
            for orig in block.copies(config.comp_mode,output):
                copy_scf = jenv.get_scvar(block_name,loc,output)
                orig_scf = jenv.get_scvar(block_name,loc,orig)
                jenv.eq(jop.JVar(orig_scf),jop.JVar(copy_scf))

    # set scaling factors connected by a wire equal
    for sblk,sloc,sport,dblk,dloc,dport in circ.conns():
        s_scf = jenv.get_scvar(sblk,sloc,sport)
        d_scf = jenv.get_scvar(dblk,dloc,dport)
        jenv.eq(jop.JVar(s_scf),jop.JVar(d_scf))

def _to_phys_bandwidth(circ,bw):
    return bw*circ.board.time_constant

def analog_bandwidth_constraint(jenv,circ,mbw,hwbw):
    tau = jop.JVar(jenv.TAU)
    if hwbw.unbounded_lower() and hwbw.unbounded_upper():
        return

    if mbw.is_infinite():
        return

    physbw = _to_phys_bandwidth(circ,mbw.bandwidth)
    jenv.use_tau()
    if hwbw.upper > 0:
        jenv.lte(jop.JMult(tau,jop.JConst(physbw)), \
                 jop.JConst(hwbw.upper))
    else:
        jenv.fail()

    if hwbw.lower > 0:
        jenv.gte(jop.JMult(tau,jop.JConst(physbw)), \
                 jop.JConst(hwbw.lower))

def analog_op_range_constraint(jenv,prop,scale_expr,mrng,hwrng):
    jaunt_util.upper_bound_constraint(jenv, scale_expr, mrng.upper, hwrng.upper)
    jaunt_util.lower_bound_constraint(jenv, scale_expr, mrng.lower, hwrng.lower)
    if mrng.spread == 0.0:
        return

    if isinstance(prop, props.AnalogProperties):
        if abs(mrng.lower) > 0:
            jaunt_util.lower_bound_constraint(jenv,scale_expr,abs(mrng.lower), \
                                    prop.min_signal())
        if abs(mrng.upper) > 0:
            jaunt_util.lower_bound_constraint(jenv,scale_expr,abs(mrng.upper), \
                                           prop.min_signal())





def digital_quantize_constraint(jenv,scale_expr,math_rng,props):
    def compute_bnds(math_val):
        all_values = props.values()
        max_error = props.max_error
        values = list(filter(lambda v: jaunt_util.same_sign(v,math_val), \
                             all_values))
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
            jaunt_util.lower_bound_constraint(jenv,scale_expr_inv,\
                                    abs(lb_nom),abs(lb_min))
            jaunt_util.upper_bound_constraint(jenv,scale_expr_inv,\
                                    abs(lb_nom),abs(lb_max))

        if not util.equals(ub,0):
            ub_min,ub_max,ub_nom = compute_bnds(ub)
            jaunt_util.lower_bound_constraint(jenv,scale_expr_inv,\
                                    abs(ub_nom),abs(ub_min))
            jaunt_util.upper_bound_constraint(jenv,scale_expr_inv,\
                                    abs(ub_nom),abs(ub_max))

    else:
        if not util.equals(lb,0):
            val_min,val_max,val_nom = compute_bnds(lb)
            jaunt_util.lower_bound_constraint(jenv,scale_expr_inv,\
                                    abs(val_nom),abs(val_min))
            jaunt_util.upper_bound_constraint(jenv,scale_expr_inv,\
                                    abs(val_nom),abs(val_max))

def digital_bandwidth_constraint(jenv,prob,circ,mbw,prop):
    tau = jop.JVar(jenv.TAU)
    tau_inv = jop.JVar(jenv.TAU,exponent=-1.0)
    if mbw.is_infinite():
        return

    physbw = _to_phys_bandwidth(circ,mbw.bandwidth)
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
        analog_bandwidth_constraint(jenv,circ, \
                                    mbw,hwbw)
    else:
        raise Exception("unknown not permitted")
