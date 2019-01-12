import chip.props as props
from chip.conc import ConcCirc
import chip.conc_infer as conc_infer
from chip.config import Labels
import ops.op as ops
import gpkit
import itertools
import compiler.jaunt_gen_noise_circ as jnoise
import ops.jop as jop
import ops.op as op
import signal
import random
import time
import numpy as np

#TODO: what is low range, high range and med range?
#TODO: setRange: integ.in, integ.out and mult have setRange functions.
#TODO: how do you set wc in the integrator? Is it through the setRange function?
class JauntObjectiveFunction():

    @staticmethod
    def methods():
        #return ['fast','slow','max']
        return ['fast','slow']

    def __init__(self,jenv):
        self.method = 'fast'
        self.jenv = jenv

    def objective(self,varmap):
        if self.method == 'fast':
            return self.fast(varmap)
        elif self.method == 'slow':
            return self.slow(varmap)
        elif self.method == 'max':
            return self.max_dynamic_range(varmap)

    def slow(self,varmap):
        objective = varmap[self.jenv.TAU]
        print(objective)
        return objective

    def fast(self,varmap):
        objective = 1.0/varmap[self.jenv.TAU]
        print(objective)
        return objective

    def max_dynamic_range(self,varmap):
        objective = 1.0/varmap[self.jenv.TAU]
        for scvar in self.jenv.scvars():
            objective += 1.0/varmap[scvar]
        return objective


class JauntEnv:

    TAU = "tau"

    def __init__(self):
        # scaling factor name to port
        self._to_scvar = {}
        self._from_scvar ={}
        self._to_tauvar = {}
        self._from_tauvar ={}


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
        yield JauntEnv.TAU

        for tauvar in self._from_tauvar.keys():
            yield tauvar

        for scvar in self._from_scvar.keys():
            yield scvar

    def eqs(self):
        for lhs,rhs in self._eqs:
            yield (lhs,rhs)

    def ltes(self):
        for lhs,rhs in self._ltes:
            yield (lhs,rhs)


    def get_tauvar_info(self,tauvar_var):
        if not tauvar_var in self._from_tauvar:
            print(self._from_tauvar.keys())
            raise Exception("not scaling factor table in <%s>" % tauvar_var)

        block_name,loc,port,handle = self._from_tauvar[tauvar_var]
        return block_name,loc,port,handle

    def get_tauvar(self,block_name,loc,port,handle=None):
        return self._to_tauvar[(block_name,loc,port,handle)]

    def decl_tauvar(self,block_name,loc,port,handle=None):
        # create a scaling factor from the variable name
        var_name = "TV_%s_%s_%s_%s" % (block_name,loc,port,handle)
        if var_name in self._from_tauvar:
            return var_name

        self._from_tauvar[var_name] = (block_name,loc,port,handle)
        self._to_tauvar[(block_name,loc,port,handle)] = var_name
        return var_name


    def get_scvar_info(self,scvar_var):
        if not scvar_var in self._from_scvar:
            print(self._from_scvar.keys())
            raise Exception("not scaling factor table in <%s>" % scvar_var)

        block_name,loc,port,handle = self._from_scvar[scvar_var]
        return block_name,loc,port,handle

    def tauvars(self):
        return self._from_tauvar.keys()

    def scvars(self):
        return self._from_scvar.keys()

    def get_scvar(self,block_name,loc,port,handle=None):
        return self._to_scvar[(block_name,loc,port,handle)]

    def is_scvar(self,var):
        return var in self._from_scvar

    def decl_scvar(self,block_name,loc,port,handle=None):
        # create a scaling factor from the variable name
        var_name = "SCV_%s_%s_%s_%s" % (block_name,loc,port,handle)
        if var_name in self._from_scvar:
            return var_name

        self._from_scvar[var_name] = (block_name,loc,port,handle)
        self._to_scvar[(block_name,loc,port,handle)] = var_name
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



def bp_decl_time_variables(jenv,circ):
    # define scaling factors
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            jenv.decl_tauvar(block_name,loc,output)
            for handle in block.handles(config.comp_mode,output):
                jenv.decl_tauvar(block_name,loc,output,handle=handle)

        for inp in block.inputs:
            jenv.decl_tauvar(block_name,loc,inp)

        for output in block.outputs:
            for orig in block.copies(config.comp_mode,output):
                copy_scf = jenv.get_tauvar(block_name,loc,output)
                orig_scf = jenv.get_tauvar(block_name,loc,orig)
                jenv.eq(jop.JVar(orig_scf),jop.JVar(copy_scf))

    # set scaling factors connected by a wire equal
    for sblk,sloc,sport,dblk,dloc,dport in circ.conns():
        s_scf = jenv.get_tauvar(sblk,sloc,sport)
        d_scf = jenv.get_tauvar(dblk,dloc,dport)
        jenv.eq(jop.JVar(s_scf),jop.JVar(d_scf))


def bp_decl_scale_variables(jenv,circ):
    # define scaling factors
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            jenv.decl_scvar(block_name,loc,output)
            for handle in block.handles(config.comp_mode,output):
                jenv.decl_scvar(block_name,loc,output,handle=handle)

        for inp in block.inputs:
            jenv.decl_scvar(block_name,loc,inp)

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


def is_zero(v):
    return abs(v) < 1e-14


def same_sign(v1,v2):
    if v1 < 0 and v2 < 0:
        return True
    elif v1 > 0 and v2 > 0:
        return True
    else:
        return False

def bpgen_build_lower_bound(jenv,expr,math_lower,hw_lower):
    if is_zero(math_lower) and hw_lower <= 0:
        return
    elif is_zero(math_lower) and hw_lower > 0:
        return jenv.fail()
    elif is_zero(hw_lower) and math_lower >= 0:
        return
    elif is_zero(hw_lower) and math_lower < 0:
        return jenv.fail()

    assert(not is_zero(math_lower))
    assert(not is_zero(hw_lower))

    if same_sign(math_lower,hw_lower) and \
       math_lower > 0 and hw_lower > 0:
        jenv.gte(jop.JMult(expr,jop.JConst(math_lower)),
                 jop.JConst(hw_lower))

    elif same_sign(math_lower,hw_lower) and \
         math_lower < 0 and hw_lower < 0:
        jenv.lte(jop.JMult(expr,jop.JConst(-math_lower)),
                 jop.JConst(-hw_lower))

    elif not same_sign(math_lower,hw_lower) and \
         hw_lower < 0 and math_lower > 0:
        pass

    elif not same_sign(math_lower,hw_lower) and \
         hw_lower > 0 and math_lower < 0:
        print("[[fail]] dne A st: %s < A*%s" % (hw_lower,math_lower))
        jenv.fail()
    else:
        raise Exception("uncovered lb: %s %s" % (math_lower,hw_lower))


def bpgen_build_upper_bound(jenv,expr,math_upper,hw_upper):
    if is_zero(math_upper) and hw_upper >= 0:
        return

    elif is_zero(math_upper) and hw_upper < 0:
        return

    elif is_zero(hw_upper) and math_upper <= 0:
        return

    elif is_zero(hw_upper) and math_upper > 0:
        return jenv.fail()

    assert(not is_zero(math_upper))
    assert(not is_zero(hw_upper))

    if same_sign(math_upper,hw_upper) and \
       math_upper > 0 and hw_upper > 0:
        jenv.lte(jop.JMult(expr,jop.JConst(math_upper)),
                 jop.JConst(hw_upper))

    elif same_sign(math_upper,hw_upper) and \
         math_upper < 0 and hw_upper < 0:
        jenv.lte(jop.JMult(expr,jop.JConst(-math_upper)),
                 jop.JConst(-hw_upper))

    elif not same_sign(math_upper,hw_upper) and \
         hw_upper > 0 and math_upper < 0:
        pass

    elif not same_sign(math_upper,hw_upper) and \
         hw_upper < 0 and math_upper > 0:
        print("[[fail]] dne A st: %s > A*%s" % (hw_upper,math_upper))
        jenv.fail()
    else:
        raise Exception("uncovered lb: %s %s" % (math_lower,hw_lower))


def bpgen_scaled_interval_constraint(jenv,scale_expr,math_rng,hw_rng):
    bpgen_build_upper_bound(jenv,scale_expr, \
                            math_rng.upper,hw_rng.upper)
    bpgen_build_lower_bound(jenv,scale_expr, \
                            math_rng.lower,hw_rng.lower)


def bpgen_tauvar_traverse_expr(jenv,circ,block,loc,port,expr):
    if expr.op == ops.OpType.VAR:
        return jop.JVar(jenv.get_tauvar(block.name,loc,expr.name))


    elif expr.op == ops.OpType.MULT:
        texpr1 = bpgen_tauvar_traverse_expr(jenv,circ,block,loc,port,expr.arg1)
        texpr2 = bpgen_tauvar_traverse_expr(jenv,circ,block,loc,port,expr.arg2)
        jenv.eq(texpr1,texpr2)
        return texpr1

    elif expr.op == ops.OpType.INTEG:
        # derivative and ic are scaled simialrly
        texpr_ic = bpgen_tauvar_traverse_expr(jenv,circ,block,loc,port,expr.init_cond)
        texpr_deriv = bpgen_tauvar_traverse_expr(jenv,circ,block,loc,port,expr.deriv)

        tvar_deriv = jop.JVar(jenv.get_tauvar(block.name,loc,port, \
                                              handle=expr.deriv_handle))
        tvar_stvar = jop.JVar(jenv.get_tauvar(block.name,loc,port, \
                                              handle=expr.handle))

        jenv.eq(tvar_stvar, \
                jop.JMult(jop.JVar(jenv.TAU,exponent=-1), tvar_deriv))

        jenv.eq(tvar_stvar,texpr_ic)
        return tvar_stvar

    else:
        raise Exception("unimplemented: %s" % expr)

def bpgen_scaled_digital_constraint(jenv,scale_expr,math_rng,values,quantize=1):
    lb,ub = math_rng.lower/quantize,math_rng.upper/quantize
    lb_val = min(filter(lambda v: same_sign(v,lb), values), \
              key=lambda v: abs(v))
    print(lb,lb_val)
    ub_val = min(filter(lambda v: same_sign(v,ub), values), \
              key=lambda v: abs(v))

    bpgen_build_lower_bound(jenv,scale_expr,\
                            abs(lb),abs(lb_val))
    bpgen_build_lower_bound(jenv,scale_expr,\
                            abs(ub),abs(ub_val))


def bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr):
    config = circ.config(block.name,loc)
    if expr.op == ops.OpType.CONST:
        return jop.JConst(1.0)

    elif expr.op == ops.OpType.VAR:
        scvar = jenv.get_scvar(block.name,loc,expr.name)
        return jop.JVar(scvar)

    elif expr.op == ops.OpType.MULT:
        expr1 = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.arg1)
        expr2 = bpgen_scvar_traverse_expr(jenv,circ,block,loc,port,expr.arg2)
        return jop.JMult(expr1,expr2)

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
        bpgen_scaled_interval_constraint(jenv, \
                                         scvar_deriv,
                                         deriv_mrng,
                                         deriv_hwrng)

        st_mrng = config.interval(port,expr.handle)
        st_hwrng = config.op_range(port,expr.handle)
        bpgen_scaled_interval_constraint(jenv,scvar_state,\
                                         st_mrng,st_hwrng)

        ic_mrng = config.interval(port,expr.ic_handle)
        bpgen_scaled_interval_constraint(jenv,scvar_state, \
                                         ic_mrng,st_hwrng)
        # the handles for deriv and stvar are the same
        jenv.use_tau()
        return scvar_state

    else:
        raise Exception("unhandled <%s>" % expr)


def bpgen_traverse_dynamics(jenv,circ,block,loc,out,expr):
  scexpr = bpgen_scvar_traverse_expr(jenv,circ,block,loc,out,expr)
  tauexpr = bpgen_tauvar_traverse_expr(jenv,circ,block,loc,out,expr)
  scfvar = jop.JVar(jenv.get_scvar(block.name,loc,out))
  tauvar = jop.JVar(jenv.get_tauvar(block.name,loc,out))
  # coefficient
  coeff = circ.config(block.name,loc).coeff(block,out)
  jenv.eq(scfvar,jop.JMult(jop.JConst(coeff), scexpr))
  jenv.eq(tauvar,tauexpr)

def bp_generate_problem(jenv,circ,quantize_signals=5):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out,expr in block.dynamics(config.comp_mode):
            bpgen_traverse_dynamics(jenv,circ,block,loc,out,expr)

        for port in block.outputs + block.inputs:
            mrng = circ.config(block_name,loc).interval(port)
            if mrng is None:
                print("[skip] not in use <%s[%s].%s>" % \
                      (block_name,loc,port))
                continue

            hwrng = config.op_range(port)
            scfvar = jop.JVar(jenv.get_scvar(block_name,loc,port))
            bpgen_scaled_interval_constraint(jenv,scfvar,mrng,hwrng)

            # make sure digital values are large enough to register.
            properties = config.props(block,port)
            if config.has_label(port):
                typ = config.label_type(port)
                if typ == Labels.OUTPUT or typ == Labels.DYNAMIC_INPUT:
                    quantize = quantize_signals
                else:
                    quantize = 1
            else:
                quantize = 1

            if isinstance(properties,props.DigitalProperties):
                bpgen_scaled_digital_constraint(jenv,scfvar,mrng,\
                                                properties.values(),
                                                quantize=quantize)

    if not jenv.uses_tau():
        jenv.eq(jop.JVar(jenv.TAU), jop.JConst(1.0))

    else:
        TAU_MAX = 1e6
        TAU_MIN = 1e-6
        jenv.lte(jop.JVar(jenv.TAU),jop.JConst(TAU_MAX))
        jenv.gte(jop.JVar(jenv.TAU),jop.JConst(TAU_MIN))

def build_jaunt_env(circ):
    conc_infer.infer(circ)
    jenv = JauntEnv()
    # declare scaling factors
    bp_decl_scale_variables(jenv,circ)
    bp_decl_time_variables(jenv,circ)
    bp_generate_problem(jenv,circ)

    return jenv

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

def build_gpkit_problem(circ,jenv,jopt):
    failed = jenv.failed()
    if failed:
        return None


    variables = {}
    for scf in jenv.variables():
        print(scf)
        variables[scf] = gpkit.Variable(scf)

    constraints = []
    for orig_lhs,orig_rhs in jenv.eqs():
        succ,lhs,rhs = cancel_signs(orig_lhs,orig_rhs)
        if not succ:
            failed = True
            continue

        gp_lhs = gpkit_expr(variables,lhs)
        gp_rhs = gpkit_expr(variables,rhs)
        result = gp_lhs == gp_rhs
        msg="%s == %s" % (lhs,rhs)
        constraints.append((gp_lhs == gp_rhs,msg))

    for lhs,rhs in jenv.ltes():
        gp_lhs = gpkit_expr(variables,lhs)
        gp_rhs = gpkit_expr(variables,rhs)
        msg="%s <= %s" % (lhs,rhs)
        constraints.append((gp_lhs <= gp_rhs,msg))


    gpkit_cstrs = []
    for cstr,msg in constraints:
        if isinstance(cstr,bool) or isinstance(cstr,np.bool_):
            if not cstr:
                print("[[false]]: %s" % (msg))
                failed = True
            else:
                print("[[true]]: %s" % (msg))
        else:
            gpkit_cstrs.append(cstr)
            print("[q] %s" % msg)

    if failed:
        print("<< failed >>")
        time.sleep(0.2)
        return None

    print("==== Objective Fxn [%s] ====" % jopt.method)
    objective = jopt.objective(variables)
    print(objective)
    model = gpkit.Model(objective,gpkit_cstrs)
    return model

def solve_gpkit_problem(gpmodel,timeout=10):
    def handle_timeout(signum,frame):
        raise TimeoutError("solver timed out")
    try:
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(timeout)
        sln = gpmodel.solve(verbosity=2)
        signal.alarm(0)
    except RuntimeWarning:
        signal.alarm(0)
        return None
    except TimeoutError as te:
        print("Timeout: cvxopt timed out or hung")
        signal.alarm(0)
        return None

    return sln


def sp_update_circuit(jenv,circ,assigns):
    bindings = {}
    tau = None
    for variable,value in assigns.items():
        print("SCF %s = %s" % (variable,value))
        if variable.name == jenv.TAU:
            circ.set_tau(tau)
        else:
            if jenv.is_scvar(variable.name):
                block_name,loc,port,handle = jenv.get_scvar_info(variable.name)
                circ.config(block_name,loc).set_scf(port,handle,value)
            else:
                block_name,loc,port,handle = jenv.get_tauvar_info(variable.name)
                circ.config(block_name,loc).set_tau(port,handle,value)


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
            jenv = build_jaunt_env(orig_circ)
        else:
            raise Exception("unimplemented: noise analysis")
        if jenv is None:
            continue

        skip_opts = False
        jopt = JauntObjectiveFunction(jenv)
        gpprob = build_gpkit_problem(orig_circ,jenv,jopt)
        if gpprob is None:
            continue

        for opt in JauntObjectiveFunction.methods():
            if skip_opts:
                continue
            jopt.method = opt
            sln = solve_gpkit_problem(gpprob)
            if sln is None:
                print("[[FAILURE]]")
                skip_opts = True

            elif not 'freevariables' in sln:
                print("[[FAILURE]]")
                succ,result = sln
                assert(result is None)
                assert(succ == False)
                skip_opts = True

            else:
                upd_circ = sp_update_circuit(jenv,orig_circ,
                                         sln['freevariables'])
                yield upd_circ
