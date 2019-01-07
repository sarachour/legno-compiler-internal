import chip.props as props
from chip.conc import ConcCirc
import ops.op as ops
import gpkit
import itertools
import compiler.jaunt_gen_noise_circ as jnoise
import ops.jop as jop
import ops.op as op
from ops.interval import Interval, IRange, IValue
import signal
import random
import time

#TODO: what is low range, high range and med range?
#TODO: setRange: integ.in, integ.out and mult have setRange functions.
#TODO: how do you set wc in the integrator? Is it through the setRange function?

class JauntProb:

    TAU = "tau"

    def __init__(self):
        # scaling factor name to port
        self._to_scf = {}
        self._from_scf ={}

        # location to index
        self._from_loc = {}
        self._to_loc = {}

        self._to_hw_range = {}
        self._to_math_range = {}
        self._to_coefficient = {}
        self._visited = {}
        self._priority = {}

        self._eqs = []
        self._ltes = []

        # metavar
        self._meta = {}
        self._metavar = 0
        self._failed = False
        self._use_tau = False

    def use_tau(self):
        self._use_tau = True

    def uses_tau(self):
        return self._use_tau

    def fail(self):
        self._failed = True

    def failed(self):
        return self._failed

    def priority(self):
        for (block_name,port,idx,handle), weight \
            in self._priority.items():
            loc = self._to_loc[block_name][idx]
            yield block_name,port,loc,handle,weight

    def variables(self):
        yield JauntProb.TAU

        for scf in self._from_scf.keys():
            yield scf

    def eqs(self):
        for lhs,rhs in self._eqs:
            yield (lhs,rhs)

    def ltes(self):
        for lhs,rhs in self._ltes:
            yield (lhs,rhs)

    def _loc_to_index(self,block_name,loc,create=False):
        loc_key = str(loc)
        if not create:
            assert(block_name in self._from_loc)
            if not loc_key in self._from_loc[block_name]:
                print(self._from_loc[block_name].keys())
                raise Exception("not in <%s>: <%s>" % (block_name,loc_key))

            return self._from_loc[block_name][loc_key]

        # create a new location collection for block
        if not block_name in self._from_loc:
            self._from_loc[block_name] = {}
            self._to_loc[block_name] = {}

        # create a mapping from a location to an index
        if not loc_key in self._from_loc[block_name]:
            n = int(len(self._from_loc[block_name].keys()))
            self._from_loc[block_name][loc_key] = n
            self._to_loc[block_name][n] = loc

        return self._from_loc[block_name][loc_key]

    def _index_to_loc(self,block_name,index):
        return self._to_loc[block_name][index]

    def visited(self,block_name,loc,port,handle=None):
        index = self._loc_to_index(block_name,loc)
        if not (block_name,port,index,handle) in self._visited:
            return False
        else:
            return self._visited[(block_name,port,index,handle)]

    def visit(self,block_name,loc,port,handle=None):
        index = self._loc_to_index(block_name,loc,create=True)
        self._visited[(block_name,port,index,handle)] = True


    def coefficient(self,block_name,loc,port,handle=None):
        index = self._loc_to_index(block_name,loc)
        if not (block_name,port,index,handle) in self._to_coefficient:
            return 1.0
        else:
            return self._to_coefficient[(block_name,port,index,handle)]

    def set_coefficient(self,block_name,loc,port,value,handle=None):
        index = self._loc_to_index(block_name,loc,create=True)
        self._to_coefficient[(block_name,port,index,handle)] = value

    def set_hardware_range(self,block_name,loc,port,ival,handle=None):
        index = self._loc_to_index(block_name,loc,create=True)
        if not (isinstance(ival,Interval)):
            raise Exception("not ival <%s>.T<%s>" % \
                            (ival,ival.__class__.__name__))

        assert(not (block_name,port,index,handle) in self._to_hw_range)
        self._to_hw_range[(block_name,port,index,handle)] = ival

    def set_math_range(self,block_name,loc,port,interval,handle=None):
        index = self._loc_to_index(block_name,loc)
        if not (isinstance(interval,Interval)):
            raise Exception("not interval <%s>.T<%s>" % \
                            (interval,interval.__class__.__name__))

        assert(not (block_name,port,index,handle) in self._to_math_range)
        self._to_math_range[(block_name,port,index,handle)] = interval


    def has_hardware_range(self,block_name,loc,port,handle=None):
        index = self._loc_to_index(block_name,loc)
        return (block_name,port,index,handle) in self._to_hw_range


    def has_math_range(self,block_name,loc,port,handle=None):
        index = self._loc_to_index(block_name,loc)
        return (block_name,port,index,handle) in self._to_math_range

    def set_priority(self,block_name,loc,port,handle=None):
        index = self._loc_to_index(block_name,loc)
        self._priority[(block_name,port,index,handle)] = 1.0

    def get_scf_info(self,scf_var):
        if not scf_var in self._from_scf:
            print(self._from_scf.keys())
            raise Exception("not scaling factor table in <%s>" % scf_var)

        block_name,port,index,handle = self._from_scf[scf_var]
        loc = self._index_to_loc(block_name,index)
        return block_name,loc,port,handle

    def get_scf(self,block_name,loc,port,handle=None):
        index = self._loc_to_index(block_name,loc)
        return self._to_scf[(block_name,port,index,handle)]

    def decl_scf(self,block_name,loc,port,handle=None):
        # create a scaling factor from the variable name
        index = self._loc_to_index(block_name,loc,create=True)
        var_name = "SCF_%s_%d_%s_%s" % (block_name,index,port,handle)
        if var_name in self._from_scf:
            return var_name

        self._from_scf[var_name] = (block_name,port,index,handle)
        self._to_scf[(block_name,port,index,handle)] = var_name
        return var_name

    def eq(self,v1,v2):
        # TODO: equality
        self._eqs.append((v1,v2))


    def lte(self,v1,v2):
        # TODO: equality
        self._ltes.append((v1,v2))


    def gte(self,v1,v2):
        # TODO: equality
        self._ltes.append((v2,v1))


    def hardware_range(self,block_name,loc,port,handle=None):
        index = self._loc_to_index(block_name,loc)
        key = (block_name,port,index,handle)
        if not key in self._to_hw_range:
            return None
        else:
            return self._to_hw_range[key]

    def math_range(self,block_name,loc,port,handle=None):
        index = self._loc_to_index(block_name,loc,port)
        key = (block_name,port,index,handle)
        if not key in self._to_math_range:
            return None
        else:
            return self._to_math_range[key]

    def math_ranges(self,block_name,loc,ports,handle=None):
        index = self._loc_to_index(block_name,loc)
        missing = False
        bindings = []
        for port in ports:
            key = (block_name,port,index,handle)
            if key in self._to_math_range:
                interval = self._to_math_range[key]
            else:
                interval = None
                missing = True

            bindings.append((port,interval))

        return not missing, bindings



def bp_ival_port_to_range(block,config,port,handle=None):
    port_props = block.info(config.comp_mode,\
                            config.scale_mode,\
                            port,\
                            handle=handle)
    if isinstance(port_props,props.AnalogProperties):
        lb,ub,units = port_props.interval()
        return IRange(lb,ub)

    elif isinstance(port_props,props.DigitalProperties):
        lb = min(port_props.values())
        ub = max(port_props.values())
        return IRange(lb,ub)

    else:
        raise Exception("unhandled <%s>" % port_props)

def bp_ival_hw_port_op_ranges(prob,circ):

    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        mode = config.comp_mode
        for port in block.inputs + block.outputs:
            hwrng = bp_ival_port_to_range(block,config,port)
            prob.set_hardware_range(block_name,loc,port,hwrng)
            for handle in block.handles(mode,port):
                hwrng = bp_ival_port_to_range(block,config,port, \
                                              handle=handle)
                prob.set_hardware_range(block_name,loc,port,hwrng,\
                                        handle=handle)

def bp_ival_math_dac_ranges(prob,circ):
     for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.inputs + block.outputs:
            if config.has_dac(port):
                value = config.dac(port)
                mrng = IValue(value)
                print("val: %s[%s].%s := %s" % (block_name,loc,port,mrng))
                prob.set_math_range(block_name,loc,port,mrng)

def bp_ival_math_label_ranges(prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.outputs + block.inputs:
            if config.has_label(port):
                label = config.label(port)
                if port in block.outputs:
                    handle = block.get_dynamics(config.comp_mode,port).toplevel()
                else:
                    handle = None
                lb,ub = circ.interval(label)
                mrng = IRange(lb,ub)
                print("lbl: %s[%s].%s := %s" % (block_name,loc,port,mrng))
                prob.set_math_range(block_name,loc,port,mrng,\
                                    handle=handle)
                prob.set_priority(block_name,loc,port, \
                                  handle=handle)

def bp_ival_hardware_classify_ports(prob,variables):
    bound,free = [],[]
    for var in variables:
        block_name,loc,port = var
        if prob.has_hardware_range(block_name,loc,port):
            bound.append(var)
        else:
            free.append(var)

    return free,bound


def bp_ival_math_classify_ports(prob,variables):
    bound,free = [],[]
    for var in variables:
        block_name,loc,port = var
        if prob.has_math_range(block_name,loc,port):
            bound.append(var)
        else:
            free.append(var)

    return free,bound

def bpder_derive_output_port(prob,circ,block,config,loc,port):
    coeff = prob.coefficient(block.name,loc,port)
    dyn = block.get_dynamics(config.comp_mode,port)
    expr = op.Mult(dyn,op.Const(coeff))


    handles = expr.handles()
    # test to see if we have computed the interval
    visited = True
    if not prob.visited(block.name,loc,port):
        visited = False
    for handle in handles:
        if not prob.visited(block.name,loc,port,handle=handle):
            visited = False

    if visited:
        print("[visit] skipping %s[%s].%s" \
              % (block.name,loc,port))
        return True

    prob.visit(block.name,loc,port)
    # find intervals for free variables
    variables = list(map(lambda v: (block.name,loc,v), expr.vars()))
    free,bound = bp_ival_hardware_classify_ports(prob, variables)
    assert(len(free) == 0)
    free,bound = bp_ival_math_classify_ports(prob, variables)
    for free_block_name,free_loc,free_port in free:
        free_block = circ.board.block(free_block_name)
        bp_derive_intervals(prob,circ,free_block,\
                            circ.config(free_block.name,free_loc),\
                            free_loc,free_port)

    # compute intervals
    varmap = {}
    for var_block_name,var_loc,var_port in free+bound:
        ival = prob.math_range(var_block_name,var_loc,var_port)
        varmap[var_port] = ival
        print("  v:%s=%s" % (var_port,ival))

    for handle in handles:
        ival = prob.math_range(block.name, loc, port,
                               handle=handle)
        varmap[handle] = ival
        print("  h:%s=%s" % (handle,ival))

    intervals = expr.interval(varmap)

    if prob.math_range(block.name,loc,port) is None:
        prob.set_math_range(block.name,loc,port,intervals.interval)
        print("out %s[%s].%s => %s [c=%s]" % \
              (block.name,loc,port,intervals.interval,coeff))

    for handle,interval in intervals.bindings():
        if not prob.math_range(block.name,loc,port,handle=handle):
            prob.set_math_range(block.name,loc,port, \
                                interval,handle=handle)
            print("out %s[%s].%s:%s => %s" % \
                (block.name,loc,port,handle,interval))





def bpder_derive_input_port(prob,circ,block,config,loc,port):
    sources = list(circ.get_conns_by_dest(block.name,loc,port))
    free,bound = bp_ival_math_classify_ports(prob,sources)
    print("input %s[%s].%s #srcs=%d" % (block.name,loc,port,len(sources)))
    assert(len(sources) > 0)
    for free_block_name,free_loc,free_port in free:
        free_block = circ.board.block(free_block_name)
        bp_derive_intervals(prob,circ,free_block,
                            circ.config(free_block.name,free_loc),\
                            free_loc,free_port)

    expr_ival = None
    for src_block_name,src_loc,src_port in free+bound:
        src_ival = prob.math_range(src_block_name,src_loc,src_port)
        expr_ival = src_ival if expr_ival is None else \
                    expr_ival.add(src_ival)

    prob.set_math_range(block.name,loc,port,expr_ival)
    print("in %s[%s].%s => %s" % (block.name,loc,port,expr_ival))



def bp_derive_intervals(prob,circ,block,config,loc,port):
    if block.is_input(port):
        bpder_derive_input_port(prob,circ,block,config,loc,port)

    elif block.is_output(port):
        bpder_derive_output_port(prob,circ,block,config,loc,port)

    else:
        raise Exception("what the fuck...")


def bp_bind_intervals(prob,circ):
    # bind operating ranges for ports
    print("-> bind port operating ranges")
    bp_ival_hw_port_op_ranges(prob,circ)
    # bind math ranges of dacs
    print("-> bind math ranges of dac values")
    bp_ival_math_dac_ranges(prob,circ)
    # bind math ranges of labels
    print("-> bind math ranges of labels")
    bp_ival_math_label_ranges(prob,circ)
    print("-> derive intervals")
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out_port in block.outputs:
            bp_derive_intervals(prob,circ,block,config,loc,out_port)

    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.outputs + block.inputs:
            assert(prob.has_hardware_range(block_name,loc,port))

def bp_bind_coefficients(prob,circ):

    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out,expr in block.dynamics(config.comp_mode):
            scf = block.scale_factor(config.comp_mode,config.scale_mode,out)

            if scf != 1.0:
                prob.set_coefficient(block_name,loc,out,scf)

def bp_decl_scaling_factors(prob,circ):
    # define scaling factors
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            prob.decl_scf(block_name,loc,output)
            for handle in block.handles(config.comp_mode,output):
                prob.decl_scf(block_name,loc,output,handle=handle)

        for inp in block.inputs:
            prob.decl_scf(block_name,loc,inp)

        for output in block.outputs:
            for orig in block.copies(config.comp_mode,output):
                copy_scf = prob.get_scf(block_name,loc,output)
                orig_scf = prob.get_scf(block_name,loc,orig)
                prob.eq(jop.JVar(orig_scf),jop.JVar(copy_scf))

    # set scaling factors connected by a wire equal
    for sblk,sloc,sport,dblk,dloc,dport in circ.conns():
        s_scf = prob.get_scf(sblk,sloc,sport)
        d_scf = prob.get_scf(dblk,dloc,dport)
        prob.eq(jop.JVar(s_scf),jop.JVar(d_scf))


def is_zero(v):
    return abs(v) < 1e-14


def same_sign(v1,v2):
    if v1 < 0 and v2 < 0:
        return True
    elif v1 > 0 and v2 > 0:
        return True
    else:
        return False

def bpgen_build_lower_bound(prob,expr,math_lower,hw_lower):
    if is_zero(math_lower) and hw_lower <= 0:
        return
    elif is_zero(math_lower) and hw_lower > 0:
        return prob.fail()
    elif is_zero(hw_lower) and math_lower >= 0:
        return
    elif is_zero(hw_lower) and math_lower < 0:
        return prob.fail()

    assert(not is_zero(math_lower))
    assert(not is_zero(hw_lower))

    if same_sign(math_lower,hw_lower) and \
       math_lower > 0 and hw_lower > 0:
        prob.gte(jop.JMult(expr,jop.JConst(math_lower)),
                 jop.JConst(hw_lower))

    elif same_sign(math_lower,hw_lower) and \
         math_lower < 0 and hw_lower < 0:
        prob.lte(jop.JMult(expr,jop.JConst(-math_lower)),
                 jop.JConst(-hw_lower))

    elif not same_sign(math_lower,hw_lower) and \
         hw_lower < 0 and math_lower > 0:
        pass

    elif not same_sign(math_lower,hw_lower) and \
         hw_lower > 0 and math_lower < 0:
        print("[[fail]] dne A st: %s < A*%s" % (hw_lower,math_lower))
        prob.fail()
    else:
        raise Exception("uncovered lb: %s %s" % (math_lower,hw_lower))


def bpgen_build_upper_bound(prob,expr,math_upper,hw_upper):
    if is_zero(math_upper) and hw_upper >= 0:
        return

    elif is_zero(math_upper) and hw_upper < 0:
        return

    elif is_zero(hw_upper) and math_upper <= 0:
        return

    elif is_zero(hw_upper) and math_upper > 0:
        return prob.fail()

    assert(not is_zero(math_upper))
    assert(not is_zero(hw_upper))

    if same_sign(math_upper,hw_upper) and \
       math_upper > 0 and hw_upper > 0:
        prob.lte(jop.JMult(expr,jop.JConst(math_upper)),
                 jop.JConst(hw_upper))

    elif same_sign(math_upper,hw_upper) and \
         math_upper < 0 and hw_upper < 0:
        prob.lte(jop.JMult(expr,jop.JConst(-math_upper)),
                 jop.JConst(-hw_upper))

    elif not same_sign(math_upper,hw_upper) and \
         hw_upper > 0 and math_upper < 0:
        pass

    elif not same_sign(math_upper,hw_upper) and \
         hw_upper < 0 and math_upper > 0:
        print("[[fail]] dne A st: %s > A*%s" % (hw_upper,math_upper))
        prob.fail()
    else:
        raise Exception("uncovered lb: %s %s" % (math_lower,hw_lower))


def bpgen_scaled_interval_constraint(prob,scale_expr,math_rng,hw_rng):
    bpgen_build_upper_bound(prob,scale_expr, \
                            math_rng.upper,hw_rng.upper)
    bpgen_build_lower_bound(prob,scale_expr, \
                            math_rng.lower,hw_rng.lower)


def bpgen_compute_interval(prob,block,loc,expr):
    bindings = {}
    for var in expr.vars():
        bindings[var] = prob.math_range(block,loc,var)

    return expr.interval(bindings).interval

def bpgen_traverse_expr(prob,block,loc,port,expr):
    inv_tau_scfvar = jop.JVar(prob.TAU,exponent=-1)
    if expr.op == ops.Op.CONST:
        return jop.JConst(1.0)

    elif expr.op == ops.Op.VAR:
        port = expr.name
        scf = prob.get_scf(block.name,loc,port)
        return jop.JVar(scf)

    elif expr.op == ops.Op.MULT:
        expr1 = bpgen_traverse_expr(prob,block,loc,port,expr.arg1)
        expr2 = bpgen_traverse_expr(prob,block,loc,port,expr.arg2)
        return jop.JMult(expr1,expr2)

    elif expr.op == ops.Op.INTEG:
        # derivative and ic are scaled simialrly
        ic_expr = bpgen_traverse_expr(prob,block,loc,port,expr.init_cond)
        deriv_expr = bpgen_traverse_expr(prob,block,loc,port,expr.deriv)
        var_deriv = jop.JVar(prob.get_scf(block.name,loc,port, \
                                          handle=expr.deriv_handle))
        var_stvar = jop.JVar(prob.get_scf(block.name,loc,port, \
                                          handle=expr.handle))
        integ_expr = jop.JMult(inv_tau_scfvar,var_deriv)

        # ranges are contained
        deriv_mrng = prob.math_range(block.name,loc,port,expr.deriv_handle)
        st_mrng = prob.math_range(block.name,loc,port,expr.handle)
        ic_mrng = bpgen_compute_interval(prob,block.name,loc,expr.init_cond)
        deriv_hwrng = prob.hardware_range(block.name,loc,port,expr.deriv_handle)
        st_hwrng = prob.hardware_range(block.name,loc,port,expr.handle)
        assert(not deriv_mrng is None)
        assert(not ic_mrng is None)
        assert(not deriv_hwrng is None)
        assert(not st_hwrng is None)
        bpgen_scaled_interval_constraint(prob, \
                                         deriv_expr,deriv_mrng,deriv_hwrng)
        bpgen_scaled_interval_constraint(prob,integ_expr,\
                                         st_mrng,st_hwrng)
        bpgen_scaled_interval_constraint(prob,ic_expr, \
                                         ic_mrng,st_hwrng)
        # the handles for deriv and stvar are the same
        prob.eq(integ_expr,var_stvar)
        prob.eq(ic_expr,var_stvar)
        prob.eq(deriv_expr,var_deriv)
        prob.use_tau()
        return var_stvar

    else:
        raise Exception("unhandled <%s>" % expr)


def bpgen_traverse_dynamics(prob,block,loc,out,expr):
  expr_scf = bpgen_traverse_expr(prob,block,loc,out,expr)
  var_scfvar = jop.JVar(prob.get_scf(block.name,loc,out))
  coeff = prob.coefficient(block.name,loc,out)
  prob.eq(var_scfvar,jop.JMult(jop.JConst(coeff), expr_scf))

def bp_generate_problem(prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out,expr in block.dynamics(config.comp_mode):
            bpgen_traverse_dynamics(prob,block,loc,out,expr)

        for port in block.outputs + block.inputs:
            mrng = prob.math_range(block_name,loc,port)
            if mrng is None:
                print("[skip] not in use <%s[%s].%s>" % \
                      (block_name,loc,port))
                continue

            hwrng = prob.hardware_range(block_name,loc,port)
            scfvar = jop.JVar(prob.get_scf(block_name,loc,port))
            bpgen_scaled_interval_constraint(prob,scfvar,mrng,hwrng)


    if not prob.uses_tau():
        prob.eq(jop.JVar(prob.TAU), jop.JConst(1.0))

    else:
        TAU_MAX = 1e6
        TAU_MIN = 1e-6
        prob.lte(jop.JVar(prob.TAU),jop.JConst(TAU_MAX))
        prob.gte(jop.JVar(prob.TAU),jop.JConst(TAU_MIN))

def build_data_structures(circ):
    prob = JauntProb()

    # declare scaling factors
    print("-> Decl Scaling Factors")
    bp_decl_scaling_factors(prob,circ)

    # pass1: fill intervals
    print("-> Derive + Bind Intervals")
    bp_bind_intervals(prob,circ)

    # pass2: fill in hardware coefficients
    print("-> Fill Coefficients")
    bp_bind_coefficients(prob,circ)

    # pass3: generate problem
    print("-> Generate Problem")
    bp_generate_problem(prob,circ)

    return prob

def gpkit_expr(variables,expr):
    if expr.op == jop.JOp.VAR:
        return variables[expr.name]**expr.exponent

    elif expr.op == jop.JOp.MULT:
        e1 = gpkit_expr(variables,expr.arg(0))
        e2 = gpkit_expr(variables,expr.arg(1))
        return e1*e2

    elif expr.op == jop.JOp.CONST:
        return expr.value

    else:
        raise Exception("unsupported <%s>" % expr)



def cancel_signs(orig_lhs,orig_rhs):
    const1,expr1 = orig_lhs.factor_const()
    const2,expr2 = orig_rhs.factor_const()
    if const1 >= 0 and const2 >= 0:
        pass
    elif const1 <= 0 and const1 <= 0:
        const1 *= -1
        const2 *= -1
    else:
        print("[sign mismatch] %s OP %s" % (orig_lhs,orig_rhs))
        return False,orig_lhs,orig_rhs

    new_expr1 = jop.JMult(jop.JConst(const1),expr1)
    new_expr2 = jop.JMult(jop.JConst(const2),expr2)
    return True,new_expr1,new_expr2

def build_problem(circ,prob):
    TAU_MIN = 1e-6
    failed = prob.failed()
    if failed:
        return None


    variables = {}
    for scf in prob.variables():
        print(scf)
        variables[scf] = gpkit.Variable(scf)

    constraints = []
    for orig_lhs,orig_rhs in prob.eqs():
        succ,lhs,rhs = cancel_signs(orig_lhs,orig_rhs)
        if not succ:
            failed = True
            continue

        gp_lhs = gpkit_expr(variables,lhs)
        gp_rhs = gpkit_expr(variables,rhs)
        if isinstance(gp_lhs == gp_rhs,bool):
            #print("assert(%s == %s)" % (gp_lhs,gp_rhs))
            if not gp_lhs == gp_rhs:
                print("[[false]]: %s != %s" % (lhs,rhs))
                failed = True

            continue


        print("%s == %s" % (gp_lhs,gp_rhs))
        constraints.append(gp_lhs == gp_rhs)

    for lhs,rhs in prob.ltes():
        gp_lhs = gpkit_expr(variables,lhs)
        gp_rhs = gpkit_expr(variables,rhs)
        if isinstance(gp_lhs <= gp_rhs,bool):
            #print("assert(%s <= %s)" % (gp_lhs,gp_rhs))
            if not gp_lhs <= gp_rhs:
                print("[[false]]: %s <= %s" % (lhs,rhs))
                failed = True
            continue

        print("%s <= %s" % (gp_lhs,gp_rhs))
        constraints.append(gp_lhs <= gp_rhs)

    constraints.append(TAU_MIN <= variables[prob.TAU])
    #constraints.append(1.0 == variables[prob.TAU])

    if failed:
        print("<< failed >>")
        time.sleep(0.2)
        return None

    objective = 1.0/variables["tau"]
    for block_name,port,loc,handle,weight in prob.priority():
        scf = prob.get_scf(block_name,loc,port,handle=handle)
        objective += 1.0/variables[scf]

    model = gpkit.Model(objective,constraints)
    return model

def solve_problem(gpmodel,timeout=10):
    def handle_timeout(signum,frame):
        raise TimeoutError("solver timed out")
    try:
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(timeout)
        sln = gpmodel.solve(verbosity=2)
        signal.alarm(0)
    except RuntimeWarning:
        return None
    except TimeoutError as te:
        print("Timeout: cvxopt timed out or hung")
        return None

    return sln


def sp_update_circuit(prob,circ,assigns):
    bindings = {}
    tau = None
    for variable,value in assigns.items():
        print("SCF %s = %s" % (variable,value))
        if variable.name == prob.TAU:
            tau = value
        else:
            block_name,loc,port,handle = prob.get_scf_info(variable.name)
            bindings[(block_name,loc,port,handle)] = value


    intervals = {}
    circ.set_tau(tau)
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.outputs + block.inputs:
            propobj= block.info(config.comp_mode,config.scale_mode,port)
            if config.has_dac(port):
                scale_factor = bindings[(block_name,loc,port,None)]
                value = config.dac(port)
                scaled_value = scale_factor*value
                assert(isinstance(propobj,props.DigitalProperties))
                closest_scaled_value = propobj.value(scaled_value)
                print("dac %s[%s].%s: %s -> %s" %\
                      (block.name,loc,port,value, \
                       closest_scaled_value))
                config.set_dac(port,closest_scaled_value)
                intervals[(block_name,loc,port)] = \
                          [closest_scaled_value, \
                           closest_scaled_value,scale_factor]

            elif (block_name,loc,port,None) in bindings:
                scale_factor = bindings[(block_name,loc,port,None)]
                # add scale factor, if there's a label
                if config.has_label(port):
                    label = config.label(port)
                    config.set_scf(port,scale_factor)

                #compute ranges
                low,high = prob.math_range(block_name,loc,port)
                intervals[(block.name,loc,port)] = [
                    low*scale_factor,
                    high*scale_factor,
                    scale_factor
                ]


    return circ,(tau,intervals)


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


    for choice in itertools.product(*choices):
        circ = ConcCirc.from_json(circ.board,circ_json)
        for (block_name,loc),scale_mode in zip(labels,choice):
            print("%s.%s = %s" % (block_name,loc,scale_mode))
            circ.config(block_name,loc) \
                .set_scale_mode(scale_mode)

        #input()
        yield circ

def scale(circ,noise_analysis=False):
    for orig_circ in iter_scaled_circuits(circ):
        if not noise_analysis:
            data_structs = build_data_structures(orig_circ)
        else:
            raise Exception("unimplemented: noise analysis")

        prob = build_problem(orig_circ,data_structs)
        if prob is None:
            continue

        #input()
        sln = solve_problem(prob)
        if sln is None:
            print("[[FAILURE]]")
            continue

        if not 'freevariables' in sln:
            print("[[FAILURE]]")
            succ,result = sln
            assert(result is None)
            assert(succ == False)
            continue

        upd_circ,(tau,intervals) = sp_update_circuit(data_structs,orig_circ,
                                                     sln['freevariables'])
        yield upd_circ,tau,intervals
