import chip.props as props
import ops.op as ops
import gpkit
import itertools
import compiler.jaunt_gen_noise_circ as jnoise
import ops.jop as jop
from ops.interval import Interval, IRange, IValue

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
        self._priority = {}

        self._eqs = []
        self._ltes = []

        # metavar
        self._meta = {}
        self._metavar = 0
        self._failed = False

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

    def coefficient(self,block_name,port,loc,handle=None):
        index = self._loc_to_index(block_name,loc)
        if not (block_name,port,index,handle) in self._to_coefficient:
            return 1.0
        else:
            return self._to_coefficient[(block_name,port,index,handle)]

    def set_coefficient(self,block_name,port,loc,value,handle=None):
        index = self._loc_to_index(block_name,loc)
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



def bp_ival_port_to_range(block,mode,port,handle=None):
    port_props = block.props(mode,port,handle=handle)
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
        mode = config.mode
        for port in block.inputs + block.outputs:
            hwrng = bp_ival_port_to_range(block,mode,port)
            prob.set_hardware_range(block_name,loc,port,hwrng)
            for handle in block.handles(mode,port):
                hwrng = bp_ival_port_to_range(block,mode,port, \
                                              handle=handle)
                prob.set_hardware_range(block_name,loc,port,hwrng,\
                                        handle=handle)

def bp_ival_math_dac_ranges(prob,circ):
     for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        mode = config.mode
        for port in block.inputs + block.outputs:
            port_props = block.props(mode,port)
            if config.has_dac(port):
                value = config.dac(port)
                mrng = IValue(value)
                prob.set_math_range(block_name,loc,port,mrng)

def bp_ival_math_label_ranges(prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        mode = config.mode
        for port in block.inputs + block.outputs:
            if config.has_label(port):
                label = config.label(port)
                handle = block.get_dynamics(port,mode).toplevel()
                lb,ub = circ.interval(label)
                mrng = IRange(lb,ub)
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
    comp_mode = config.mode
    expr = block.get_dynamics(port,comp_mode)
    handles = expr.handles()
    # test to see if we have computed the interval
    computed_interval = True
    if not prob.has_math_range(block.name,loc,port):
        computed_interval = False
    for handle in handles:
        if not prob.has_math_range(block.name,loc,port,handle=handle):
            computed_interval = False

    if computed_interval:
        print("skipping %s" % block.name)
        return True

    # find intervals for free variables
    variables = list(map(lambda v: (block.name,loc,v), expr.vars()))
    print("-----------------")
    print(config)
    print("variables=%s" % variables)
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

    for handle in handles:
        ival = prob.math_range(block.name, loc, port, handle=handle)
        varmap[handle] = ival

    intervals = expr.interval(varmap)
    prob.set_math_range(block.name,loc,port,intervals.interval)
    print("out %s[%s].%s => %s" % (block.name,loc,port,intervals.interval))
    for handle,interval in intervals.bindings():
        prob.set_math_range(block.name,loc,port,interval,handle=handle)
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
        for out,expr in block.dynamics(mode=config.mode):
            scf = block.scale_factor(out,mode=config.scale_mode)

            if scf != 1.0:
                prob.set_coefficient(block_name,out,loc,scf)

def bp_decl_scaling_factors(prob,circ):
    # define scaling factors
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            prob.decl_scf(block_name,loc,output)
            for handle in block.handles(config.mode,output):
                prob.decl_scf(block_name,loc,output,handle=handle)

        for inp in block.inputs:
            prob.decl_scf(block_name,loc,inp)

        for output in block.outputs:
            for orig in block.copies(config.mode,output):
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

    elif not same_sign(math_upper,hw_upper) and \
         hw_lower > 0 and math_upper < 0:
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
        prob.fail()
    else:
        raise Exception("uncovered lb: %s %s" % (math_lower,hw_lower))


def bpgen_scaled_interval_constraint(prob,scale_expr,math_rng,hw_rng):
    bpgen_build_upper_bound(prob,scale_expr, \
                            math_rng.upper,hw_rng.upper)
    bpgen_build_lower_bound(prob,scale_expr, \
                            math_rng.lower,hw_rng.lower)


def bpgen_traverse_expr(prob,block,loc,port,expr):
    inv_tau_scfvar = jop.JVar(prob.TAU,exponent=-1)
    if expr.op == ops.Op.CONST:
        return JConst(1.0)

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

        prob.eq(ic_expr,deriv_expr)
        prob.eq(ic_expr,var_deriv)
        # ranges are contained
        mrng = prob.math_range(block.name,loc,port,expr.deriv_handle)
        hwrng = prob.hardware_range(block.name,loc,port,expr.deriv_handle)
        assert(not mrng is None)
        assert(not hwrng is None)
        bpgen_scaled_interval_constraint(prob,ic_expr,mrng,hwrng)
        # the handles for deriv and stvar are the same
        integ_expr = jop.JMult(inv_tau_scfvar,var_deriv)
        prob.eq(integ_expr,var_stvar)
        return var_stvar

    else:
        raise Exception("unhandled <%s>" % expr)


def bpgen_traverse_dynamics(prob,block,loc,out,expr):
  expr_scf = bpgen_traverse_expr(prob,block,loc,out,expr)
  coeff = prob.coefficient(block.name,out,loc)
  if coeff != 1.0:
      expr_scf = jop.JMult(jop.JConst(coeff),expr_scf)

  var_scfvar = jop.JVar(prob.get_scf(block.name,loc,out))
  prob.eq(var_scfvar,expr_scf)

def bp_generate_problem(prob,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out,expr in block.dynamics(mode=config.mode):
            bpgen_traverse_dynamics(prob,block,loc,out,expr)

        for port in block.outputs + block.inputs:
            mrng = prob.math_range(block_name,loc,port)
            if mrng is None:
                print("not in use <%s[%s].%s>" % (block_name,loc,port))
                continue

            hwrng = prob.hardware_range(block_name,loc,port)
            scfvar = jop.JVar(prob.get_scf(block_name,loc,port))
            bpgen_scaled_interval_constraint(prob,scfvar,mrng,hwrng)


    TAU_MAX = 1e6
    TAU_MIN = 1e-6
    prob.lte(jop.JVar(prob.TAU),jop.JConst(TAU_MAX))
    prob.gte(jop.JVar(prob.TAU),jop.JConst(TAU_MIN))

def build_problem(circ):
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

def sp_update_circuit(prob,circ,assigns):
    bindings = {}
    tau = None
    for variable,value in assigns.items():
        print("%s = %s" % (variable,value))
        if variable.name == prob.TAU:
            tau = value
        else:
            block_name,loc,port,handle = prob.get_scf_info(variable.name)
            bindings[(block_name,loc,port,handle)] = value


    circ.set_tau(tau)
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.outputs + block.inputs:
            propobj= block.props(config.mode,port)
            if config.has_dac(port):
                scale_factor = bindings[(block_name,loc,port,None)]
                value = config.dac(port)
                scaled_value = scale_factor*value
                assert(isinstance(propobj,props.DigitalProperties))
                closest_scaled_value = propobj.value(scaled_value)
                print("dac %s: %s -> %s -> %s" %\
                      (port,value,scaled_value,closest_scaled_value))
                config.set_dac(port,closest_scaled_value)

            elif config.has_label(port):
                label = config.label(port)
                scale_factor = bindings[(block_name,loc,port,None)]
                config.set_scf(port,scale_factor)
                print("%s.%s = %s" % (port,label,scale_factor))

    return circ

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

def solve_problem(circ,prob):
    TAU_MIN = 1e-6
    failed = prob.failed()

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
            failed = failed or not (gp_lhs == gp_rhs)
            continue


        print("%s == %s" % (gp_lhs,gp_rhs))
        constraints.append(gp_lhs == gp_rhs)

    for lhs,rhs in prob.ltes():
        gp_lhs = gpkit_expr(variables,lhs)
        gp_rhs = gpkit_expr(variables,rhs)
        if isinstance(gp_lhs <= gp_rhs,bool):
            #print("assert(%s <= %s)" % (gp_lhs,gp_rhs))
            failed = failed or not (gp_lhs <= gp_rhs)
            continue

        print("%s <= %s" % (gp_lhs,gp_rhs))
        constraints.append(gp_lhs <= gp_rhs)

    constraints.append(TAU_MIN <= variables[prob.TAU])
    #constraints.append(1.0 == variables[prob.TAU])

    if failed:
        return False,None

    objective = 1.0/variables["tau"]
    for block_name,port,loc,handle,weight in prob.priority():
        scf = prob.get_scf(block_name,loc,port,handle=handle)
        objective += 1.0/variables[scf]

    model = gpkit.Model(objective,constraints)
    try:
        sln = model.solve(verbosity=2)
    except RuntimeWarning:
        return None

    return sln


def iter_scaled_circuits(circ):
    labels = []
    choices = []
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        modes = block.scale_modes
        if len(modes) > 1:
            labels.append((block_name,loc))
            choices.append(modes)

    for choice in itertools.product(*choices):
        for (block_name,loc),scale_mode in zip(labels,choice):
            print("%s.%s = %s" % (block_name,loc,scale_mode))
            circ.config(block_name,loc) \
                .set_scale_mode(scale_mode)

        yield circ

def scale(circ,noise_analysis=False):
    for orig_circ in iter_scaled_circuits(circ):
        if not noise_analysis:
            prob = build_problem(orig_circ)
        else:
            raise Exception("unimplemented: noise analysis")

        sln = solve_problem(orig_circ,prob)
        if sln is None:
            print("[[FAILURE]]")
            continue
        else:
            sp_update_circuit(prob,circ,
                              sln['freevariables'])
            yield circ
