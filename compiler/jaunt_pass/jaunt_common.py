from enum import Enum
import numpy as np
import ops.jop as jop
import ops.nop as nop
import ops.op as ops
import chip.props as props
from chip.model import ModelDB, PortModel, OutputModel
import chip.hcdc.globals as glb
import util.util as util
import util.config as CONFIG
import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jenv as jenvlib
import math

db = ModelDB()

def get_parameters(jenv,circ,block,loc,port,handle=None):
    config = circ.config(block.name,loc)
    scale_model = block.scale_model(config.comp_mode)
    baseline = scale_model.baseline
    pars = {}
    if isinstance(jenv, jenvlib.JauntInferEnv):
        scale_mode = baseline
        hwscvar = jop.JVar(jenv.get_op_range_var(block.name,loc,port,handle))
        physgain,physunc = 1.0,0.0
    else:
        scale_mode = config.scale_mode
        hwscvar = jop.JConst(1.0)
        model = PortModel(block.name,loc,port, \
                          config.comp_mode,scale_mode)
        if jenv.physical and \
           db.has(block.name,loc,port,config.comp_mode,scale_mode,handle):
            model = db.get(block.name,loc,port,config.comp_mode,scale_mode,handle)

        if isinstance(model,OutputModel):
            physgain = model.gain
            print("%s[%s].%s (%s)= %f" % (block.name,loc,port,handle,physgain))
        else:
            physgain = 1.0

        unc = math.sqrt(model.noise**2.0 + model.bias_uncertainty**2.0)
        physunc = unc+abs(model.bias)

    mrng = config.interval(port)
    mbw = config.bandwidth(port)
    mathscvar = jop.JVar(jenv.get_scvar(block.name,loc,port,handle))
    prop = block.props(config.comp_mode,scale_mode,port,handle=handle)
    hwrng,hwbw,snr = prop.interval(), prop.bandwidth(), config.snr(port)
    exclude = None
    if isinstance(prop,props.DigitalProperties):
        exclude = prop.exclude()

    return {
        'math_range':mrng,
        'math_bandwidth':mbw,
        'math_scale':mathscvar,
        'hw_scale':hwscvar,
        'prop':prop,
        'hw_range':hwrng,
        'hw_bandwidth':hwbw,
        'hw_snr':snr,
        'hw_exclude':exclude,
        'phys_gain': physgain,
        'phys_unc': physunc,
        'min_snr': 1.0
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
        jenv.lte(jop.JMult(tau,jop.JConst(physbw)), \
                 jop.JConst(hwbw.upper),
                 'jcom-analog-bw-%s' % annot
        )
    else:
        jenv.fail()

    if hwbw.lower > 0:
        jenv.gte(jop.JMult(tau,jop.JConst(physbw)), \
                 jop.JConst(hwbw.lower),
                 'jcom-analog-bw-%s' % annot
        )

def digital_op_range_constraint(jenv,circ,block,loc,port,handle,annot=""):
    pars = get_parameters(jenv,circ,block,loc,port,handle)
    mrng = pars['math_range']
    hwrng = pars['hw_range']
    hwexc = pars['hw_exclude']
    prop = pars['prop']
    mscale = pars['math_scale']
    hscale = pars['hw_scale']
    #for k,v in pars.items():
    #    print("%s=%s" % (k,v))
    assert(isinstance(prop, props.DigitalProperties))
    jaunt_util.upper_bound_constraint(jenv,
                                      jop.JMult(mscale,
                                                jop.expo(hscale,-1.0)),
                                      mrng.upper, hwrng.upper,
                                      'jcom-digital-oprange-%s' % annot)
    if abs(mrng.upper) > 0:
        if mrng.upper >= 0:
            jaunt_util.lower_bound_constraint(jenv,
                                            jop.JMult(mscale,
                                                    jop.expo(hscale,-1.0)),
                                            mrng.upper, hwexc.upper,
                                            'jcom-digital-upos-opexc-%s' % annot)
        else:
            jaunt_util.upper_bound_constraint(jenv,
                                            jop.JMult(mscale,
                                                    jop.expo(hscale,-1.0)),
                                            mrng.upper, hwexc.upper,
                                            'jcom-digital-uneg-opexc-%s' % annot)

    jaunt_util.lower_bound_constraint(jenv,
                                      jop.JMult(mscale,
                                                jop.expo(hscale,-1.0)),
                                      mrng.lower, hwrng.lower,
                                      'jcom-digital-oprange-%s' % annot)
    if abs(mrng.lower) > 0:
        if mrng.lower >= 0:
            jaunt_util.lower_bound_constraint(jenv,
                                            jop.JMult(mscale,
                                                        jop.expo(hscale,-1.0)),
                                            mrng.lower, hwexc.lower,
                                            'jcom-digital-lpos-opexc-%s' % annot)
        else:
            jaunt_util.upper_bound_constraint(jenv,
                                            jop.JMult(mscale,
                                                        jop.expo(hscale,-1.0)),
                                            mrng.lower, hwexc.lower,
                                            'jcom-digital-lneg-opexc-%s' % annot)



def analog_op_range_constraint(jenv,circ,block,loc,port,handle,annot=""):
    pars = get_parameters(jenv,circ,block,loc,port,handle)
    mrng = pars['math_range']
    hwrng = pars['hw_range']
    min_snr = pars['min_snr']
    phys_gain = pars['phys_gain']
    prop = pars['prop']
    assert(isinstance(prop, props.AnalogProperties))
    ratio = jop.JMult(jop.JConst(1.0/phys_gain), \
                      jop.JMult(pars['math_scale'],jop.expo(pars['hw_scale'],-1.0)))
    jaunt_util.upper_bound_constraint(jenv,
                                      ratio,
                                      mrng.upper, hwrng.upper,
                                      'jcom-analog-oprange-%s' % annot)
    jaunt_util.lower_bound_constraint(jenv,
                                      ratio,
                                      mrng.lower, hwrng.lower,
                                      'jcom-analog-oprange-%s' % annot)
    # if this makes the system a system that processes a physical signal.
    if prop.is_physical:
        jenv.eq(mscale, jop.JConst(1.0),'jcom-analog-physical-rng')

    phys_unc = pars['phys_unc']
    if phys_unc > 0.0 and mrng.bound > 0.0:
        signal_expr = jop.JMult(pars['math_scale'],jop.JConst(mrng.bound))
        noise_expr = jop.JConst(1.0/phys_unc)
        snr_expr = jop.JMult(signal_expr,noise_expr)
        jenv.gte(snr_expr,jop.JConst(min_snr), \
                 annot='jcom-analog-minsig')


def digital_quantize_constraint(jenv,circ,block,loc,port,handle,annot=""):
    if jenv.no_quality:
        return
    pars = get_parameters(jenv,circ,block,loc,port,handle)
    prop = pars['prop']
    mrng = pars['math_range']
    min_snr = pars['min_snr']
    delta_h = np.mean(np.diff(prop.values()))

    if delta_h > 0.0 and mrng.bound > 0.0:
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

            print("max_samples=%s n_samples=%s" % \
                  (hw_max_samples, sim_max_samples))

            if sim_max_samples > hw_max_samples:
                raise Exception("[error] not enough storage in arduino to record data")

    elif prop.kind == props.DigitalProperties.ClockType.CONTINUOUS:
        hwbw = prop.bandwidth()
        analog_bandwidth_constraint(jenv,circ,block,loc,port,handle,
                                    "digcont-bw-%s[%s].%s" % (block,loc,port))
    else:
        raise Exception("unknown not permitted")
