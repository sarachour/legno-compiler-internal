import chip.props as props
from chip.conc import ConcCirc
import chip.conc_infer as conc_infer
import ops.op as ops
import gpkit
import itertools
import compiler.jaunt_gen_noise_circ as jnoise
import ops.jop as jop
import ops.op as op
import signal
import random
import time

#TODO: what is low range, high range and med range?
#TODO: setRange: integ.in, integ.out and mult have setRange functions.
#TODO: how do you set wc in the integrator? Is it through the setRange function?

class JauntProb:

    TAU = "tau"

    def __init__(self,circ):
        self.env = conc_infer.infer(circ)
        # scaling factor name to port
        self._to_scvar = {}
        self._from_scvar ={}

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


    def get_scvar_info(self,scf_var):
        if not scf_var in self._from_scf:
            print(self._from_scf.keys())
            raise Exception("not scaling factor table in <%s>" % scf_var)

        block_name,loc,port,handle = self._from_scf[scf_var]
        return block_name,loc,port,handle

    def get_scvar(self,block_name,loc,port,handle=None):
        return self._to_scf[(block_name,loc,port,handle)]

    def decl_scvar(self,block_name,loc,port,handle=None):
        # create a scaling factor from the variable name
        var_name = "SCV_%s_%d_%s_%s" % (block_name,loc,port,handle)
        if var_name in self._from_scf:
            return var_name

        self._from_scf[var_name] = (block_name,loc,port,handle)
        self._to_scf[(block_name,loc,port,handle)] = var_name
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



def bp_decl_scaling_variables(prob,circ):
    # define scaling factors
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            prob.decl_scf(block_name,loc,output)
            for handle in block.handles(config.comp_mode,output):
                prob.decl_scvar(block_name,loc,output,handle=handle)

        for inp in block.inputs:
            prob.decl_scvar(block_name,loc,inp)

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
    if expr.op == ops.OpType.CONST:
        return jop.JConst(1.0)

    elif expr.op == ops.OpType.VAR:
        port = expr.name
        scf = prob.get_scf(block.name,loc,port)
        return jop.JVar(scf)

    elif expr.op == ops.OpType.MULT:
        expr1 = bpgen_traverse_expr(prob,block,loc,port,expr.arg1)
        expr2 = bpgen_traverse_expr(prob,block,loc,port,expr.arg2)
        return jop.JMult(expr1,expr2)

    elif expr.op == ops.OpType.INTEG:
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
    prob = JauntProb(circ)
    # declare scaling factors
    print("-> Decl Scaling Variables")
    bp_decl_scale_variables(prob,circ)

    # pass3: generate problem
    print("-> Generate Problem")
    bp_generate_problem(prob,circ)

    return prob

def gpkit_expr(variables,expr):
    if expr.op == jop.JOpType.VAR:
        return variables[expr.name]**expr.exponent

    elif expr.op == jop.JOpType.MULT:
        e1 = gpkit_expr(variables,expr.arg(0))
        e2 = gpkit_expr(variables,expr.arg(1))
        return e1*e2

    elif expr.op == jop.JOpType.CONST:
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
