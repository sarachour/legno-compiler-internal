import ops.jop as jop
import ops.nop as nop
import ops.op as ops
import chip.props as props
from enum import Enum
import compiler.jaunt_pass.jaunt_util as jaunt_util
import chip.hcdc.globals as glb
import util.util as util
import util.config as CONFIG
import numpy as np

def noise_model(circ,block,loc,port):
    config = circ.config(block.name,loc)
    baseline = block.scale_model(config.comp_mode).baseline
    if port in block.outputs:
        phys_model = block \
                     .physical(config.comp_mode,baseline,port) \
                     .noise.copy()
        phys_model.bind_instance(block.name,loc)
        phys = [phys_model]
    else:
        phys = []
        for sb,sl,sp in circ.get_conns_by_dest(block.name,loc,port):
            phys.append(noise_model(circ,circ.board.block(sb),sl,sp)[0])

    return phys

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
                jenv.eq(jop.JVar(orig_scf),jop.JVar(copy_scf),'jc-copy')

    # set scaling factors connected by a wire equal
    for sblk,sloc,sport,dblk,dloc,dport in circ.conns():
        s_scf = jenv.get_scvar(sblk,sloc,sport)
        d_scf = jenv.get_scvar(dblk,dloc,dport)
        jenv.eq(jop.JVar(s_scf),jop.JVar(d_scf),'jc-conn')

def _to_phys_time(circ,time):
    return time/circ.board.time_constant


def _to_phys_bandwidth(circ,bw):
    return bw*circ.board.time_constant

def analog_bandwidth_constraint(jenv,circ,prop,mbw,hwbw):
    tau = jop.JVar(jenv.tau())
    if isinstance(prop,props.AnalogProperties) and prop.is_physical:
        jenv.eq(tau,jop.JConst(1.0),'jcom-physical-bw')

    if mbw.is_infinite():
        return

    if hwbw.unbounded_lower() and hwbw.unbounded_upper():
        return

    # physical signals are not corrected by the board's time constant
    physbw = _to_phys_bandwidth(circ,mbw.bandwidth)

    jenv.use_tau()
    if hwbw.upper > 0:
        jenv.lte(jop.JMult(tau,jop.JConst(physbw)), \
                 jop.JConst(hwbw.upper),
                 'jcom-analog-bw'
        )
    else:
        jenv.fail()

    if hwbw.lower > 0:
        jenv.gte(jop.JMult(tau,jop.JConst(physbw)), \
                 jop.JConst(hwbw.lower),
                 'jcom-analog-bw'
        )

def digital_op_range_constraint(jenv,phys,prop,mscale,hscale,mrng,hwrng,hwexc,annot=""):
    assert(isinstance(prop, props.DigitalProperties))
    jaunt_util.upper_bound_constraint(jenv,
                                      jop.JMult(mscale,
                                                jop.expo(hscale,-1.0)),
                                      mrng.upper, hwrng.upper,
                                      'jcom-digital-oprange-%s' % annot)
    if mrng.upper >= 0:
        jaunt_util.lower_bound_constraint(jenv,
                                          jop.JMult(mscale,
                                                  jop.expo(hscale,-1.0)),
                                          mrng.upper, hwexc.upper,
                                          'jcom-digital-u-opexc-%s' % annot)
    else:
        jaunt_util.upper_bound_constraint(jenv,
                                          jop.JMult(mscale,
                                                jop.expo(hscale,-1.0)),
                                          mrng.upper, hwexc.upper,
                                          'jcom-digital-u-opexc-%s' % annot)

    jaunt_util.lower_bound_constraint(jenv,
                                      jop.JMult(mscale,
                                                jop.expo(hscale,-1.0)),
                                      mrng.lower, hwrng.lower,
                                      'jcom-digital-oprange-%s' % annot)
    if mrng.lower >= 0:
        jaunt_util.lower_bound_constraint(jenv,
                                          jop.JMult(mscale,
                                                    jop.expo(hscale,-1.0)),
                                          mrng.lower, hwexc.lower,
                                          'jcom-digital-l-opexc-%s' % annot)
    else:
        jaunt_util.upper_bound_constraint(jenv,
                                          jop.JMult(mscale,
                                                    jop.expo(hscale,-1.0)),
                                          mrng.lower, hwexc.lower,
                                          'jcom-digital-l-opexc-%s' % annot)

def noise_model_to_noise_expr(jenv,circ,phys):
    def to_magnitude(blk,loc,port):
        cfg = circ.config(blk,loc)
        ival = cfg.interval(port)
        if ival.spread == 0:
            return ival.bound
        else:
            return ival.spread

    def to_jop(expr):
        if expr.op == nop.NOpType.CONST_RV:
            return jop.JConst(abs(expr.sigma))
        if expr.op == nop.NOpType.ADD:
            e1 = to_jop(expr.arg(0))
            e2 = to_jop(expr.arg(1))
            return jop.JAdd(e1,e2)
        if expr.op == nop.NOpType.SIG:
            blk,loc = expr.instance
            jvar = jenv.get_scvar(blk,loc,expr.port)
            jrng = to_magnitude(blk,loc,expr.port)
            return jop.JMult(
                jop.JVar(jvar),
                jop.JConst(jrng)
            )

        if expr.op == nop.NOpType.MULT:
            e1 = to_jop(expr.arg(0))
            e2 = to_jop(expr.arg(1))
            return jop.JMult(e1,e2)

        else:
            raise Exception("unimplemented: %s" % expr)

    model = nop.mkadd(phys)
    noise_expr = to_jop(model)
    return noise_expr

def compute_nsr(noise_expr,mscale,mrng):
    if mrng.spread == 0:
        if mrng.bound == 0:
            return

        signal_expr = jop.JMult(mscale,jop.JConst(mrng.bound))
        return jop.JMult(jop.expo(signal_expr,-1), noise_expr)

    else:
        if mrng.bound == 0:
            return

        signal_expr = jop.JMult(mscale,jop.JConst(mrng.bound))
        return jop.JMult(jop.expo(signal_expr,-1), noise_expr)

def compute_max_nsr(min_snr):
    if min_snr == 0:
        return None
    max_nsr = 1.0/min_snr
    return max_nsr

def analog_op_range_constraint(jenv,circ,phys,prop, \
                               mscale,hscale,mrng,hwrng,snr,annot=""):
    assert(isinstance(prop, props.AnalogProperties))
    jaunt_util.upper_bound_constraint(jenv,
                                      jop.JMult(mscale,
                                                jop.expo(hscale,-1.0)),
                                      mrng.upper, hwrng.upper,
                                      'jcom-analog-oprange-%s' % annot)
    jaunt_util.lower_bound_constraint(jenv,
                                      jop.JMult(mscale,
                                                jop.expo(hscale,-1.0)),
                                      mrng.lower, hwrng.lower,
                                      'jcom-analog-oprange-%s' % annot)
    if jenv.no_quality:
        return

    if prop.is_physical:
        jenv.eq(mscale, jop.JConst(1.0),'jcom-analog-physical-rng')

    nz_expr = noise_model_to_noise_expr(jenv,circ,phys)
    nsr_expr = compute_nsr(nz_expr,mscale,mrng)
    max_nsr = compute_max_nsr(snr)
    if max_nsr is None:
        return

    if not nsr_expr is None:
        jenv.lte(nsr_expr,jop.JConst(max_nsr), \
                 annot='jcom-analog-minsig')



def digital_quantize_constraint(jenv,phys,prop,mscale,hscale,math_rng,snr):
    if jenv.no_quality:
        return

    delta_h = np.mean(np.diff(prop.values()))
    nsr_expr = compute_nsr(jop.JConst(delta_h), mscale, math_rng)
    max_nsr = compute_max_nsr(snr)
    if max_nsr is None:
        return

    if not nsr_expr is None:
        jenv.lte(nsr_expr,jop.JConst(max_nsr), \
                 annot='jcom-digital-minsig')


def max_sim_time_constraint(jenv,prob,circ):
    max_time = 3.0
    max_sim_time = _to_phys_time(circ,prob.max_sim_time)
    tau_inv = jop.JVar(jenv.tau(),exponent=-1.0)
    hw_time = jop.JMult(
        jop.JConst(max_sim_time), tau_inv
    )
    jenv.lte(hw_time, jop.JConst(max_time), 'max-time')


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
        hw_sample_freq = 1.0/prop.sample_rate
        # maximum number of samples
        # sample frequency required
        sim_sample_freq = 2.0*physbw
        jenv.lte(jop.JMult(tau, jop.JConst(sim_sample_freq)), \
                 jop.JConst(hw_sample_freq),
                 'jcom-digital-bw'
        )
        if not prop.max_samples is None:
            # (max_sim_time/tau)*(sim_sample_freq*tau)
            # max_sim_time*sim_sample_freq < hw_max_samples
            max_sim_time = _to_phys_time(circ,prob.max_sim_time)
            sim_max_samples = max_sim_time*sim_sample_freq
            hw_max_samples = prop.max_samples

            print("max_samples=%s n_samples=%s" % \
                  (hw_max_samples, sim_max_samples))

            if sim_max_samples > hw_max_samples:
                raise Exception("[error] not enough storage in arduino to record data")

    elif prop.kind == props.DigitalProperties.ClockType.CONTINUOUS:
        hwbw = prop.bandwidth()
        analog_bandwidth_constraint(jenv,circ,prop, \
                                    mbw,hwbw)
    else:
        raise Exception("unknown not permitted")
