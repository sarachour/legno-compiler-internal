import ops.jop as jop
import ops.op as ops
import chip.props as props
from enum import Enum
import compiler.jaunt_pass.jaunt_util as jaunt_util
import util.util as util
import numpy as np

def decl_scale_variables(jenv,circ):
    # define scaling factors
    MIN_SC = 1e-6
    MAX_SC = 1e6
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            v = jenv.decl_scvar(block_name,loc,output)
            for handle in block.handles(config.comp_mode,output):
                v = jenv.decl_scvar(block_name,loc,output,handle=handle)

            if block.name == "lut":
                v=jenv.decl_inject_var(block_name,loc,output)

        for inp in block.inputs:
            v=jenv.decl_scvar(block_name,loc,inp)
            if block.name == "lut":
                v=jenv.decl_inject_var(block_name,loc,inp)

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
    tau = jop.JVar(jenv.tau())
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

def analog_op_range_constraint(jenv,prop,mscale,hscale,mrng,hwrng):
    jaunt_util.upper_bound_constraint(jenv,
                                      jop.JMult(mscale,
                                                jop.expo(hscale,-1.0)),
                                      mrng.upper, hwrng.upper)
    jaunt_util.lower_bound_constraint(jenv,
                                      jop.JMult(mscale,
                                                jop.expo(hscale,-1.0)),
                                      mrng.lower, hwrng.lower)

    if isinstance(prop, props.AnalogProperties):
        if mrng.spread == 0 and abs(mrng.lower) > 0:
            jaunt_util.lower_bound_constraint(jenv,mscale,abs(mrng.lower), \
                                              prop.min_signal(prop.SignalType.CONSTANT))

        elif mrng.spread > 0:
            jaunt_util.lower_bound_constraint(jenv,mscale,mrng.spread, \
                                    prop.min_signal(prop.SignalType.DYNAMIC))



def digital_quantize_constant(jenv,mscale,math_val,props):
    delta_h = np.mean(np.diff(props.values()))
    min_quants = props.min_quantize(props.SignalType.CONSTANT)
    if abs(math_val) > 0:
        jaunt_util.lower_bound_constraint(jenv,mscale,\
                                        abs(math_val)/delta_h,
                                        min_quants)

def digital_quantize_signal(jenv,mscale,math_ival,props):
    delta_h = np.mean(np.diff(props.values()))
    min_quants = props.min_quantize(props.SignalType.DYNAMIC)
    lb = delta_h*min_quants
    jaunt_util.lower_bound_constraint(jenv,mscale,\
                                      math_ival.spread/delta_h,
                                      min_quants)


def digital_quantize_constraint(jenv,mscale,math_rng,props):
    if math_rng.lower < math_rng.upper:
        digital_quantize_signal(jenv,mscale,math_rng,props)
    else:
        digital_quantize_constant(jenv,mscale,math_rng.value,props)

def digital_bandwidth_constraint(jenv,prob,circ,mbw,prop):
    tau = jop.JVar(jenv.tau())
    tau_inv = jop.JVar(jenv.tau(),exponent=-1.0)
    if mbw.is_infinite():
        return

    physbw = _to_phys_bandwidth(circ,mbw.bandwidth)
    if prop.kind == props.DigitalProperties.ClockType.CONSTANT:
        assert(mbw.bandwidth == 0)

    elif prop.kind == props.DigitalProperties.ClockType.CLOCKED:
        jenv.use_tau()
        # time between samples
        hw_sample_rate = prop.sample_rate
        # maximum number of samples
        hw_max_samples = prop.max_samples
        # maximum simulation time
        m_exptime = prob.max_sim_time
        assert(not m_exptime is None)
        # sample frequency required
        sample_freq = 2.0*physbw
        sample_ival = 1.0/sample_freq
        jenv.gte(jop.JMult(tau_inv,jop.JConst(sample_ival)), \
                           jop.JConst(hw_sample_rate))

        if not hw_max_samples is None:
            print(hw_max_samples, m_exptime)
            input()
            jenv.lte(jop.JMult(tau_inv,jop.JConst(m_exptime)),  \
                     jop.JConst(hw_max_samples))

    elif prop.kind == props.DigitalProperties.ClockType.CONTINUOUS:
        hwbw = prop.bandwidth()
        analog_bandwidth_constraint(jenv,circ, \
                                    mbw,hwbw)
    else:
        raise Exception("unknown not permitted")
