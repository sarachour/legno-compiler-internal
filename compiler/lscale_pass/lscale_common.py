from enum import Enum
import numpy as np
import ops.jop as jop
import ops.nop as nop
import ops.op as ops
import hwlib.props as props
from hwlib.model import ModelDB, PortModel, \
    get_oprange_scale, get_gain, get_variance
import util.util as util
import util.config as CONFIG
import compiler.lscale_pass.lscale_util as lscale_util
import compiler.lscale_pass.lscale_physlog as lscale_physlog
import compiler.lscale_pass.scenv as scenvlib
import math


def get_physics_params(scenv,circ,block,loc,port,handle=None):
    model = scenv.params.model
    config = circ.config(block.name,loc)
    oprange_lower, oprange_upper = get_oprange_scale(scenv.model_db, \
                                                     circ, \
                                                     block.name, \
                                                     loc, \
                                   port,handle=handle,
                                   mode=model)
    gain_sc = get_gain(scenv.model_db, \
                       circ, \
                       block.name,loc, \
                       port,handle=handle, \
                       mode=model)
    uncertainty_sc = get_variance(scenv.model_db, \
                                  circ,block.name,loc, \
                                  port,handle=handle, \
                                  mode=model)

    return {
        'gain':gain_sc,
        'uncertainty': uncertainty_sc,
        'oprange_lower': oprange_lower,
        'oprange_upper':oprange_upper
    }


def get_parameters(scenv,circ,block,loc,port,handle=None):
    config = circ.config(block.name,loc)
    baseline = block.baseline(config.comp_mode)
    pars = {}
    if isinstance(scenv, scenvlib.JauntInferEnv):
        scale_mode = baseline
        #physical scale variable
        hwscvar_lower = jop.JMult( \
                             jop.JVar(scenv.get_phys_op_range_scvar(block.name,loc,port, \
                                                                   handle,lower=True)), \
                             jop.JVar(scenv.get_op_range_var(block.name,loc,port,handle)) \
        );
        hwscvar_upper = jop.JMult( \
                             jop.JVar(scenv.get_phys_op_range_scvar(block.name,loc,port, \
                                                                   handle,lower=False)), \
                             jop.JVar(scenv.get_op_range_var(block.name,loc,port,handle)) \
        );
        uncertainty = jop.JVar(scenv.get_phys_uncertainty(block.name,loc,port,handle))
        hwscvar_gain = jop.JMult(
            jop.JVar(scenv.get_phys_gain_var(block.name,loc,port,handle)),
            jop.JVar(scenv.get_gain_var(block.name,loc,port,handle))
        )

    else:
        pars = get_physics_params(scenv,circ,block,loc,port,handle=handle)
        scale_mode = config.scale_mode
        hwscvar_lower = jop.JConst(pars['oprange_lower'])
        hwscvar_upper = jop.JConst(pars['oprange_upper'])
        hwscvar_gain = jop.JConst(pars['gain']*block.coeff(config.comp_mode, \
                                                            config.scale_mode, \
                                                            port,handle=handle))
        uncertainty = jop.JConst(config.meta(port,'cost',handle=handle))
        assert(not uncertainty is None)

    mrng = config.interval(port)
    mbw = config.bandwidth(port)
    mathscvar = jop.JVar(scenv.get_scvar(block.name,loc,port,handle))
    prop = block.props(config.comp_mode,scale_mode,port,handle=handle)
    hwrng= prop.interval()
    hwbw = prop.bandwidth()
    resolution = 1
    if isinstance(prop,props.DigitalProperties):
        resolution = prop.resolution

    return {
        'math_interval':mrng,
        'math_bandwidth':mbw,
        'math_scale':mathscvar,
        'prop':prop,
        'hw_oprange_scale_lower':hwscvar_lower,
        'hw_oprange_scale_upper':hwscvar_upper,
        'hw_gain':hwscvar_gain,
        'hw_oprange_base':hwrng,
        'hw_bandwidth':hwbw,
        'hw_uncertainty': uncertainty,
        'min_digital_snr': 1.0/scenv.params.percent_digital_error,
        'digital_resolution': resolution,
        'min_analog_snr': 1.0/scenv.params.percent_analog_error
    }

def decl_scale_variables(scenv,circ):
    # define scaling factors
    MIN_SC = 1e-6
    MAX_SC = 1e6
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            v = scenv.decl_scvar(block_name,loc,output)
            for handle in block.handles(config.comp_mode,output):
                v = scenv.decl_scvar(block_name,loc,output,handle=handle)
            if block.name == "lut":
                v=scenv.decl_inject_var(block_name,loc,output)

        for inp in block.inputs:
            v=scenv.decl_scvar(block_name,loc,inp)
            if block.name == "lut":
                v=scenv.decl_inject_var(block_name,loc,inp)

        for output in block.outputs:
            for orig in block.copies(config.comp_mode,output):
                copy_scf = scenv.get_scvar(block_name,loc,output)
                orig_scf = scenv.get_scvar(block_name,loc,orig)
                scenv.eq(jop.JVar(orig_scf),jop.JVar(copy_scf),'jc-copy')

    for sblk,sloc,sport,dblk,dloc,dport in circ.conns():
        s_scf = scenv.get_scvar(sblk,sloc,sport)
        d_scf = scenv.get_scvar(dblk,dloc,dport)
        scenv.eq(jop.JVar(s_scf),jop.JVar(d_scf),'jc-conn')

def _to_phys_time(circ,time):
    return time/circ.board.time_constant

def _to_phys_bandwidth(circ,bw):
    return circ.board.time_constant

def analog_bandwidth_constraint(scenv,circ,block,loc,port,handle,annot):
    tau = jop.JVar(scenv.tau())
    pars = get_parameters(scenv,circ,block,loc,port,handle)
    mbw = pars['math_bandwidth']
    hwbw = pars['hw_bandwidth']
    prop = pars['prop']

    if isinstance(prop,props.AnalogProperties) and prop.is_physical:
        scenv.eq(tau,jop.JConst(1.0),'jcom-physical-bw')
        scenv.set_time_scaling(False)

    if not scenv.params.enable_bandwidth_constraint:
        return

    # this bandwidth is constant
    if mbw.fmax == 0.0:
        return

    if mbw.is_infinite():
        return

    if hwbw.unbounded_lower() and hwbw.unbounded_upper():
        return

    # physical signals are not corrected by the board's time constant
    physbw = _to_phys_bandwidth(circ,mbw.bandwidth)
    scenv.use_tau()

    if not scenv.params.max_freq is None:
        scenv.lte(jop.JMult(tau,jop.JConst(physbw)), \
                jop.JConst(scenv.params.max_freq),
                'jcom-analog-maxbw-%s' % annot
        )

    if hwbw.upper > 0:
        scenv.lte(jop.JMult(tau,jop.JConst(physbw)), \
                jop.JConst(hwbw.upper),
                'jcom-analog-bw-%s' % annot
        )
    else:
        scenv.fail()

    if hwbw.lower > 0:
        scenv.gte(jop.JMult(tau,jop.JConst(physbw)), \
                jop.JConst(hwbw.lower),
                'jcom-analog-bw-%s' % annot
        )


def digital_op_range_constraint(scenv,circ,block,loc,port,handle,annot=""):
    pars = get_parameters(scenv,circ,block,loc,port,handle)
    mrng = pars['math_interval']
    hwrng = pars['hw_oprange_base']
    prop = pars['prop']
    hscale_lower = pars['hw_oprange_scale_lower']
    hscale_upper = pars['hw_oprange_scale_upper']

    assert(isinstance(prop, props.DigitalProperties))
    def ratio(hwexpr):
        return jop.JMult(pars['math_scale'], jop.expo(hwexpr,-1.0))

    jaunt_util.upper_bound_constraint(scenv,
                                      ratio(hscale_upper),
                                      mrng.upper,
                                      hwrng.upper,
                                      'jcom-digital-oprange-%s' % annot)

    jaunt_util.lower_bound_constraint(scenv,
                                      ratio(hscale_lower),
                                      mrng.lower,
                                      hwrng.lower,
                                      'jcom-digital-oprange-%s' % annot)


    hw_unc = pars['hw_uncertainty']
    min_snr = pars['min_analog_snr']
    hw_unc_coeff,_ = hw_unc.factor_const()
    if hw_unc_coeff > 0.0  \
       and mrng.bound > 0.0 \
       and scenv.params.enable_quality_constraint:
        signal_expr = jop.JMult(pars['math_scale'],jop.JConst(mrng.bound))
        noise_expr = jop.expo(hw_unc, -1.0)
        snr_expr = jop.JMult(signal_expr,noise_expr)
        scenv.gte(snr_expr,jop.JConst(min_snr), \
                 annot='jcom-digital-minsig')


def analog_op_range_constraint(scenv,circ,block,loc,port,handle,annot=""):

    pars = get_parameters(scenv,circ,block,loc,port,handle)
    mrng = pars['math_interval']
    hwrng = pars['hw_oprange_base']
    min_snr = pars['min_analog_snr']
    hw_unc = pars['hw_uncertainty']
    prop = pars['prop']
    assert(isinstance(prop, props.AnalogProperties))
    hw_lower = pars['hw_oprange_scale_lower']
    hw_upper = pars['hw_oprange_scale_upper']

    def ratio(hwexpr):
        return jop.JMult(pars['math_scale'], jop.expo(hwexpr,-1.0))

    jaunt_util.upper_bound_constraint(scenv,
                                      ratio(hw_upper),
                                      mrng.upper,
                                      hwrng.upper,
                                      'jcom-analog-oprange-%s' % annot)
    jaunt_util.lower_bound_constraint(scenv,
                                      ratio(hw_lower),
                                      mrng.lower,
                                      hwrng.lower,
                                      'jcom-analog-oprange-%s' % annot)

    # if this makes the system a system that processes a physical signal.
    if prop.is_physical:
        scenv.eq(pars['math_scale'], jop.JConst(1.0),'jcom-analog-physical-rng')

    hw_unc_coeff,_ = hw_unc.factor_const()
    if hw_unc_coeff > 0.0  \
       and mrng.bound > 0.0 \
       and scenv.params.enable_quality_constraint:
        signal_expr = jop.JMult(pars['math_scale'],jop.JConst(mrng.bound))
        noise_expr = jop.expo(hw_unc, -1.0)
        snr_expr = jop.JMult(signal_expr,noise_expr)
        scenv.gte(snr_expr,jop.JConst(min_snr), \
                 annot='jcom-analog-minsig')


def digital_quantize_constraint(scenv,circ,block,loc,port,handle,annot=""):
    pars = get_parameters(scenv,circ,block,loc,port,handle)
    prop = pars['prop']
    mrng = pars['math_interval']
    min_snr = pars['min_digital_snr']
    resolution = pars['digital_resolution']
    delta_h = np.mean(np.diff(prop.values()))

    if delta_h > 0.0  \
       and mrng.bound > 0.0 \
       and scenv.params.enable_quantize_constraint:
        noise_expr = jop.JConst(1.0/(resolution*delta_h))

        signal_expr = jop.JMult(pars['math_scale'],jop.JConst(mrng.bound))
        snr_expr = jop.JMult(signal_expr,noise_expr)
        scenv.gte(snr_expr,jop.JConst(min_snr), \
                annot='jcom-digital-minsig')

def max_sim_time_constraint(scenv,prob,circ):
    max_sim_time = _to_phys_time(circ,prob.max_sim_time)
    # 100 ms.
    max_time = 0.05
    tau_inv = jop.JVar(scenv.tau(),exponent=-1.0)
    hw_time = jop.JMult(
        jop.JConst(max_sim_time), tau_inv
    )
    scenv.lte(hw_time, jop.JConst(max_time), 'max-time')


def digital_bandwidth_constraint(scenv,prob,circ,block,loc,port,handle,annot):
    max_sim_time = _to_phys_time(circ,prob.max_sim_time)
    tau = jop.JVar(scenv.tau())
    tau_inv = jop.JVar(scenv.tau(),exponent=-1.0)
    pars = get_parameters(scenv,circ,block,loc,port,handle)
    mbw = pars['math_bandwidth']
    prop = pars['prop']

    if mbw.is_infinite():
        return

    physbw = _to_phys_bandwidth(circ,mbw.bandwidth)
    if prop.kind == props.DigitalProperties.ClockType.CONSTANT:
        assert(mbw.bandwidth == 0)
        return

    elif prop.kind == props.DigitalProperties.ClockType.CLOCKED:
        scenv.use_tau()
        # time between samples
        hw_sample_freq = 1.0/prop.sample_rate
        # maximum number of samples
        # sample frequency required
        sim_sample_freq = 2.0*physbw
        if scenv.params.enable_bandwidth_constraint:
            scenv.lte(jop.JMult(tau, jop.JConst(sim_sample_freq)), \
                    jop.JConst(hw_sample_freq),
                    'jcom-digital-bw-%s' % annot
            )
            if not scenv.params.max_freq is None:
                scenv.lte(jop.JMult(tau,jop.JConst(sim_sample_freq)), \
                         jop.JConst(scenv.params.max_freq),
                         'jcom-digital-maxbw-%s' % annot
                )

        # maximum runtime of 50 ms
        max_sim_time_constraint(scenv,prob,circ)

        if not prop.max_samples is None:
            sim_max_samples = max_sim_time*sim_sample_freq
            hw_max_samples = prop.max_samples

            if sim_max_samples > hw_max_samples:
                raise Exception("[error] not enough storage in arduino to record data")

    elif prop.kind == props.DigitalProperties.ClockType.CONTINUOUS:
        hwbw = prop.bandwidth()
        analog_bandwidth_constraint(scenv,circ,block,loc,port,handle,
                                    "digcont-bw-%s[%s].%s" % (block.name,loc,port))
    else:
        raise Exception("unknown not permitted")
