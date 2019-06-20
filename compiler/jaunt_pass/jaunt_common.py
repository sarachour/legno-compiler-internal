from enum import Enum
import numpy as np
import ops.jop as jop
import ops.nop as nop
import ops.op as ops
import chip.props as props
from chip.model import ModelDB, PortModel,get_model
import chip.hcdc.globals as glb
import util.util as util
import util.config as CONFIG
import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jaunt_physlog as jaunt_physlog
import compiler.jaunt_pass.jenv as jenvlib
import math

db = ModelDB()

def get_phys_model(circ,block,loc,port,handle=None):
     if db.has(block.name,loc,port, \
              config.comp_mode, \
              config.scale_mode,handle):
        model = db.get(block.name,loc,port, \
                        config.comp_mode, \
                        config.scale_mode,handle)
        return model



def get_parameters(jenv,circ,block,loc,port,handle=None):
    config = circ.config(block.name,loc)
    scale_model = block.scale_model(config.comp_mode)
    baseline = scale_model.baseline
    pars = {}
    if isinstance(jenv, jenvlib.JauntInferEnv):
        scale_mode = scale_model.baseline
        hwscvar = jop.JVar(jenv.get_op_range_var(block.name,loc,port,handle))
        uncertainty = 0.0
        oprange_scale = (1.0,1.0)
    else:
        scale_mode = config.scale_mode
        hwscvar = jop.JConst(1.0)
        uncertainty = config.meta(port,'cost',handle=handle)
        phys_model = get_model(db,circ,block.name,loc,port,handle)
        oprange_scale  = phys_model.oprange_scale
        assert(not uncertainty is None)

    mrng = config.interval(port)
    mbw = config.bandwidth(port)
    mathscvar = jop.JVar(jenv.get_scvar(block.name,loc,port,handle))
    prop = block.props(config.comp_mode,scale_mode,port,handle=handle)
    hwrng,hwbw = prop.interval(), prop.bandwidth()
    return {
        'math_range':mrng,
        'math_bandwidth':mbw,
        'math_scale':mathscvar,
        'hw_scale':hwscvar,
        'prop':prop,
        'hw_range':hwrng,
        'hw_bandwidth':hwbw,
        'phys_unc': uncertainty,
        'phys_scale': oprange_scale,
        'min_digital_snr': 1.0/jenv.params.percent_digital_error,
        'min_analog_snr': 1.0/jenv.params.percent_analog_error
    }

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

    for sblk,sloc,sport,dblk,dloc,dport in circ.conns():
        s_scf = jenv.get_scvar(sblk,sloc,sport)
        d_scf = jenv.get_scvar(dblk,dloc,dport)
        jenv.eq(jop.JVar(s_scf),jop.JVar(d_scf),'jc-conn')

def _to_phys_time(circ,time):
    return time/circ.board.time_constant

def _to_phys_bandwidth(circ,bw):
    return bw*circ.board.time_constant

def analog_bandwidth_constraint(jenv,circ,block,loc,port,handle,annot):
    tau = jop.JVar(jenv.tau())
    pars = get_parameters(jenv,circ,block,loc,port,handle)
    mbw = pars['math_bandwidth']
    hwbw = pars['hw_bandwidth']
    prop = pars['prop']

    if isinstance(prop,props.AnalogProperties) and prop.is_physical:
        jenv.eq(tau,jop.JConst(1.0),'jcom-physical-bw')
        jenv.set_time_scaling(False)

    if mbw.is_infinite():
        return

    if hwbw.unbounded_lower() and hwbw.unbounded_upper():
        return

    # physical signals are not corrected by the board's time constant
    physbw = _to_phys_bandwidth(circ,mbw.bandwidth)

    jenv.use_tau()
    if hwbw.upper > 0:
        if jenv.params.bandwidth_maximum:
            jenv.lte(jop.JMult(tau,jop.JConst(physbw)), \
                    jop.JConst(hwbw.upper),
                    'jcom-analog-bw-%s' % annot
            )
    else:
        jenv.fail()

    if hwbw.lower > 0:
        if jenv.params.bandwidth_maximum:
            jenv.gte(jop.JMult(tau,jop.JConst(physbw)), \
                    jop.JConst(hwbw.lower),
                    'jcom-analog-bw-%s' % annot
            )

def digital_op_range_constraint(jenv,circ,block,loc,port,handle,annot=""):
    pars = get_parameters(jenv,circ,block,loc,port,handle)
    mrng = pars['math_range']
    hwrng = pars['hw_range']
    prop = pars['prop']
    mscale = pars['math_scale']
    hscale = pars['hw_scale']
    oprngsc_lower,oprngsc_upper = pars['phys_scale']
    #for k,v in pars.items():
    #    print("%s=%s" % (k,v))
    assert(isinstance(prop, props.DigitalProperties))
    ratio = jop.JMult(pars['math_scale'], \
                                jop.expo(pars['hw_scale'],-1.0))
    jaunt_util.upper_bound_constraint(jenv,
                                      ratio,
                                      mrng.upper,
                                      hwrng.upper*oprngsc_upper,
                                      'jcom-digital-oprange-%s' % annot)

    jaunt_util.lower_bound_constraint(jenv,
                                      ratio,
                                      mrng.lower,
                                      hwrng.lower*oprngsc_lower,
                                      'jcom-digital-oprange-%s' % annot)


    phys_unc = pars['phys_unc']
    min_snr = pars['min_analog_snr']
    if phys_unc > 0.0  \
       and mrng.bound > 0.0 \
       and jenv.params.quality_minimum:
        signal_expr = jop.JMult(pars['math_scale'],jop.JConst(mrng.bound))
        noise_expr = jop.JConst(1.0/phys_unc)
        snr_expr = jop.JMult(signal_expr,noise_expr)
        jenv.gte(snr_expr,jop.JConst(min_snr), \
                 annot='jcom-digital-minsig')


def analog_op_range_constraint(jenv,circ,block,loc,port,handle,annot=""):
    pars = get_parameters(jenv,circ,block,loc,port,handle)
    mrng = pars['math_range']
    hwrng = pars['hw_range']
    min_snr = pars['min_analog_snr']
    oprngsc_lower,oprngsc_upper = pars['phys_scale']
    prop = pars['prop']
    assert(isinstance(prop, props.AnalogProperties))
    ratio = jop.JMult(pars['math_scale'], \
                      jop.expo(pars['hw_scale'],-1.0))
    jaunt_util.upper_bound_constraint(jenv,
                                      ratio,
                                      mrng.upper,
                                      hwrng.upper*oprngsc_upper,
                                      'jcom-analog-oprange-%s' % annot)
    jaunt_util.lower_bound_constraint(jenv,
                                      ratio,
                                      mrng.lower,
                                      hwrng.lower*oprngsc_lower,
                                      'jcom-analog-oprange-%s' % annot)
    # if this makes the system a system that processes a physical signal.
    if prop.is_physical:
        jenv.eq(pars['math_scale'], jop.JConst(1.0),'jcom-analog-physical-rng')

    phys_unc = pars['phys_unc']
    if phys_unc > 0.0  \
       and mrng.bound > 0.0 \
       and jenv.params.quality_minimum:
        signal_expr = jop.JMult(pars['math_scale'],jop.JConst(mrng.bound))
        noise_expr = jop.JConst(1.0/phys_unc)
        snr_expr = jop.JMult(signal_expr,noise_expr)
        jenv.gte(snr_expr,jop.JConst(min_snr), \
                 annot='jcom-analog-minsig')


def digital_quantize_constraint(jenv,circ,block,loc,port,handle,annot=""):
    pars = get_parameters(jenv,circ,block,loc,port,handle)
    prop = pars['prop']
    mrng = pars['math_range']
    min_snr = pars['min_digital_snr']
    delta_h = np.mean(np.diff(prop.values()))

    if delta_h > 0.0  \
       and mrng.bound > 0.0 \
       and jenv.params.quantize_minimum:
        noise_expr = jop.JConst(1.0/delta_h)
        signal_expr = jop.JMult(pars['math_scale'],jop.JConst(mrng.bound))
        snr_expr = jop.JMult(signal_expr,noise_expr)
        jenv.gte(snr_expr,jop.JConst(min_snr), \
                annot='jcom-digital-minsig')

def max_sim_time_constraint(jenv,prob,circ):
    max_sim_time = _to_phys_time(circ,prob.max_sim_time)
    # 100 ms.
    max_time = 0.1
    tau_inv = jop.JVar(jenv.tau(),exponent=-1.0)
    hw_time = jop.JMult(
        jop.JConst(max_sim_time), tau_inv
    )
    jenv.lte(hw_time, jop.JConst(max_time), 'max-time')


def digital_bandwidth_constraint(jenv,prob,circ,block,loc,port,handle,annot):
    tau = jop.JVar(jenv.tau())
    tau_inv = jop.JVar(jenv.tau(),exponent=-1.0)
    pars = get_parameters(jenv,circ,block,loc,port,handle)
    mbw = pars['math_bandwidth']
    prop = pars['prop']

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
        if jenv.params.bandwidth_maximum:
            jenv.lte(jop.JMult(tau, jop.JConst(sim_sample_freq)), \
                    jop.JConst(hw_sample_freq),
                    'jcom-digital-bw-%s' % annot
            )

        if not prop.max_samples is None:
            # (max_sim_time/tau)*(sim_sample_freq*tau)
            # max_sim_time*sim_sample_freq < hw_max_samples
            max_sim_time = _to_phys_time(circ,prob.max_sim_time)
            sim_max_samples = max_sim_time*sim_sample_freq
            hw_max_samples = prop.max_samples

            #print("max_samples=%s n_samples=%s" % \
            #      (hw_max_samples, sim_max_samples))

            if sim_max_samples > hw_max_samples:
                raise Exception("[error] not enough storage in arduino to record data")

    elif prop.kind == props.DigitalProperties.ClockType.CONTINUOUS:
        hwbw = prop.bandwidth()
        analog_bandwidth_constraint(jenv,circ,block,loc,port,handle,
                                    "digcont-bw-%s[%s].%s" % (block,loc,port))
    else:
        raise Exception("unknown not permitted")
