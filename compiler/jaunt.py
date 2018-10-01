import chip.props as props
import ops.op as ops
import gpkit
import itertools

#TODO: what is low range, high range and med range?
#TODO: setRange: integ.in, integ.out and mult have setRange functions.
#TODO: how do you set wc in the integrator? Is it through the setRange function?

class Interval:

    def __init__(self,lb,ub):
        self._lower = lb
        self._upper = ub


    @property
    def lower(self):
        return self._lower

    @property
    def upper(self):
        return self._upper

    def add(self,i2):
         vals = [
            i2.lower+self.lower,
            i2.upper+self.lower,
            i2.lower+self.upper,
            i2.upper+self.upper
         ]
         lb = min(vals)
         ub = max(vals)
         if lb == ub:
             return IValue(lb)
         else:
             return IRange(lb,ub)

    def mult(self,i2):
        vals = [
            i2.lower*self.lower,
            i2.upper*self.lower,
            i2.lower*self.upper,
            i2.upper*self.upper
        ]
        lb = min(vals)
        ub = max(vals)
        if lb == ub:
            return IValue(lb)
        else:
            return IRange(lb,ub)

    def __repr__(self):
        return "[%s,%s]" % (self._lower,self._upper)

class IValue(Interval):

    def __init__(self,value):
        self._value = value
        Interval.__init__(self,value,value)

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return "[%s]" % self._value

class IRange(Interval):

    def __init__(self,min_value,max_value):
        Interval.__init__(self,min_value,max_value)


class JOp:

    MULT = 0
    CONST = 1
    VAR = 2

    STRMAP = {
        MULT: "*",
        CONST: "const",
        VAR: "var"
    }
    def __init__(self,op,args):
        self._args = args
        self._op = op


    def factor_const(self):
        raise NotImplementedError

    def arg(self,i):
        return self._args[i]

    @property
    def op(self):
        return self._op

    def __repr__(self):
        argstr = " ".join(map(lambda x : str(x),self._args))
        return "(%s %s)" % (JOp.STRMAP[self._op],argstr)

class JVar(JOp):

    def __init__(self,name):
        JOp.__init__(self,JOp.VAR,[])
        self._name = name

    def factor_const(self):
        return 1,self

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return "(var %s)" % self._name


class JConst(JOp):

    def __init__(self,value):
        JOp.__init__(self,JOp.CONST,[])
        self._value = value


    def factor_const(self):
        return self._value,JConst(1.0)

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return "(const %s)" % self._value

class JMult(JOp):

    def __init__(self,arg1,arg2):
        JOp.__init__(self,JOp.MULT,[arg1,arg2])

    def factor_const(self):
        c1,x1 = self.arg(0).factor_const()
        c2,x2 = self.arg(1).factor_const()
        return c1*c2,JMult(x1,x2)




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

    def priority(self):
        for (block_name,port,idx), weight \
            in self._priority.items():
            loc = self._to_loc[block_name][idx]
            yield block_name,port,loc,weight

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

    def coefficient(self,block_name,port,loc):
        index = self._loc_to_index(block_name,loc)
        if not (block_name,port,index) in self._to_coefficient:
            return 1.0
        else:
            return self._to_coefficient[(block_name,port,index)]

    def set_coefficient(self,block_name,port,loc,value):
        index = self._loc_to_index(block_name,loc)
        self._to_coefficient[(block_name,port,index)] = value

    def set_hardware_range(self,block_name,port,loc,interval):
        index = self._loc_to_index(block_name,loc)
        if not (isinstance(interval,Interval)):
            raise Exception("not interval <%s>" % interval)

        assert(not (block_name,port,index) in self._to_hw_range)
        self._to_hw_range[(block_name,port,index)] = interval

    def set_math_range(self,block_name,port,loc,interval):
        index = self._loc_to_index(block_name,loc)
        if not (isinstance(interval,Interval)):
            raise Exception("not interval <%s>" % interval)
        assert(not (block_name,port,index) in self._to_math_range)
        self._to_math_range[(block_name,port,index)] = interval


    def set_priority(self,block_name,port,loc):
        index = self._loc_to_index(block_name,loc)
        self._priority[(block_name,port,index)] = 1.0

    def get_scf_info(self,scf_var):
        if not scf_var in self._from_scf:
            print(self._from_scf.keys())
            raise Exception("not scaling factor table in <%s>" % scf_var)

        block_name,port,index = self._from_scf[scf_var]
        loc = self._index_to_loc(block_name,index)
        return block_name,port,loc

    def get_scf(self,block_name,port,loc):
        index = self._loc_to_index(block_name,loc)
        return self._to_scf[(block_name,port,index)]

    def decl_scf(self,block_name,port,loc):
        # create a scaling factor from the variable name
        index = self._loc_to_index(block_name,loc,create=True)
        var_name = "SCF_%s_%d_%s" % (block_name,index,port)
        if var_name in self._from_scf:
            return var_name

        self._from_scf[var_name] = (block_name,port,index)
        self._to_scf[(block_name,port,index)] = var_name
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


    def hardware_range(self,block_name,port,loc):
        index = self._loc_to_index(block_name,loc)
        key = (block_name,port,index)
        if not key in self._to_hw_range:
            return False,None
        else:
            return True,self._to_hw_range[key]

    def math_range(self,block_name,port,loc):
        index = self._loc_to_index(block_name,loc)
        key = (block_name,port,index)
        if not key in self._to_math_range:
            return False,None
        else:
            return True,self._to_math_range[key]

    def math_ranges(self,block_name,ports,loc):
        index = self._loc_to_index(block_name,loc)
        missing = False
        bindings = []
        for port in ports:
            key = (block_name,port,index)
            if key in self._to_math_range:
                interval = self._to_math_range[key]
            else:
                interval = None
                missing = True

            bindings.append((port,interval))

        return not missing, bindings

    def check_ranges(self):
        return_code = True
        for block_name,port,index in self._from_scf.values():
            if not (block_name,port,index) in self._to_math_range:
                print("math not-mapped %s.%s[%d]" % (block_name,port,index))
                return_code = False

            if not (block_name,port,index) in self._to_hw_range:
                print("hw not-mapped %s.%s[%d]" % (block_name,port,index))
                return_code = False

        return return_code


def bp_compute_expr_interval(expr,assigns):
    if expr.op == ops.Op.VAR:
        return assigns[expr.name]

    elif expr.op == ops.Op.MULT:
        i1 = bp_compute_expr_interval(expr.arg1,assigns)
        i2 = bp_compute_expr_interval(expr.arg2,assigns)
        ires = i1.mult(i2)
        return ires

    else:
        raise Exception("unhandled <%s>" % expr)

def bp_bind_intervals(prob,circ):

    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        mode = config.mode
        for port in block.inputs + block.outputs:
            port_props = block.props(mode,port)
            if isinstance(port_props,props.AnalogProperties):
                lb,ub,units = port_props.interval()
                hrng = IRange(lb,ub)
                prob.set_hardware_range(block_name,port,loc,hrng)

            elif isinstance(port_props,props.DigitalProperties):
                lb = min(port_props.values())
                ub = max(port_props.values())
                mrng = IRange(lb,ub)
                prob.set_hardware_range(block_name,port,loc,mrng)

            else:
                raise Exception("unhandled <%s>" % port_props)

            if config.has_dac(port):
                value = config.dac(port)
                mrng = IValue(value)
                prob.set_math_range(block_name,port,loc,mrng)

            elif config.has_label(port):
                label = config.label(port)
                lb,ub = circ.interval(label)
                mrng = IRange(lb,ub)
                prob.set_math_range(block_name,port,loc,mrng)
                prob.set_priority(block_name,port,loc)

            else:
                continue

    updated = True
    while updated:
        updated = False
        for (dblk,dloc),dport,srcs in circ.conns_by_dest():
            src_bounds = True
            src_interval_sum = None
            for (sblk,sloc),sport in srcs:
                src_bound,sinterval = prob.math_range(sblk,sport,sloc)
                src_bounds = src_bound and src_bounds
                if src_bound:
                    src_interval_sum = sinterval if src_interval_sum is None \
                                          else src_interval_sum.add(sinterval)


            dst_bound,_ = prob.math_range(dblk,dport,dloc)
            if src_bounds and not dst_bound:
                prob.set_math_range(dblk,dport,dloc,src_interval_sum)
                updated = True

        for block_name,loc,config in circ.instances():
            block = circ.board.block(block_name)

            for orig_out in block.outputs:
                for copy_out in block.copies(config.mode,orig_out):
                    copy_bound,_ = prob.math_range(block_name,copy_out,loc)
                    out_bound,out_interval = prob.math_range(block_name,
                                                            orig_out,loc)
                    if not copy_bound and out_bound:
                        prob.set_math_range(block_name,copy_out,
                                            loc,out_interval)
                        updated = True

            for out,expr in block.dynamics(mode=config.mode):
                ports = expr.vars()
                out_bound,_ = prob.math_range(block_name,out,loc)
                inp_bound,inp_intervals = prob.math_ranges(block_name,
                                                            ports,loc)

                if inp_bound and not out_bound:
                    updated = True
                    out_interval = bp_compute_expr_interval(expr, \
                                                        dict(inp_intervals))
                    prob.set_math_range(block_name,out,\
                                        loc,out_interval)
                    updated = True

    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)

        for inp in block.inputs:
            inp_bound,inp_intervals = prob.math_ranges(block_name,
                                                       [inp],loc)

            if not inp_bound:
                prob.set_math_range(block_name,inp,
                                    loc,IValue(0.0))

    assert(prob.check_ranges())

def bp_bind_coefficients(prob,circ):

    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out,expr in block.dynamics(mode=config.mode):
            scf = block.scale_factor(out,mode=config.scale_mode)

            if scf != 1.0:
                prob.set_coefficient(block_name,out,loc,scf)


def bp_generate_expr_constraints(prob,block,loc,expr):
    if expr.op == ops.Op.CONST:
        return JConst(1.0)

    elif expr.op == ops.Op.VAR:
        port = expr.name
        scf = prob.get_scf(block.name,port,loc)
        return JVar(scf)

    elif expr.op == ops.Op.MULT:
        expr1 = bp_generate_expr_constraints(prob,block,loc,expr.arg1)
        expr2 = bp_generate_expr_constraints(prob,block,loc,expr.arg2)
        return JMult(expr1,expr2)

    elif expr.op == ops.Op.INTEG:
        ic_expr = bp_generate_expr_constraints(prob,block,loc,expr.init_cond)
        deriv_expr = bp_generate_expr_constraints(prob,block,loc,expr.deriv)
        prob.eq(ic_expr,deriv_expr)
        return deriv_expr

    else:
        raise Exception("unhandled <%s>" % expr)


def bp_decl_scaling_factors(prob,circ):
    # define scaling factors
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            prob.decl_scf(block_name,output,loc)

        for inp in block.inputs:
            prob.decl_scf(block_name,inp,loc)

        for output in block.outputs:
            for orig in block.copies(config.mode,output):
                copy_scf = prob.get_scf(block_name,output,loc)
                orig_scf = prob.get_scf(block_name,orig,loc)
                prob.eq(JVar(orig_scf),JVar(copy_scf))

    # set scaling factors connected by a wire equal
    for (sblk,sloc),sport,(dblk,dloc),dport in circ.conns():
        s_scf = prob.get_scf(sblk,sport,sloc)
        d_scf = prob.get_scf(dblk,dport,dloc)
        prob.eq(JVar(s_scf),JVar(d_scf))



def bp_generate_problem(prob,circ):

    def same_sign(v1,v2):
        if v1 < 0 and v2 < 0:
            return True
        elif v1 >= 0 and v2 >= 0:
            return True
        else:
            return False

    uses_tau = False
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out,expr in block.dynamics(mode=config.mode):
            expr_scf = bp_generate_expr_constraints(prob,block,loc,expr)
            coeff = prob.coefficient(block_name,out,loc)

            scf_expr = expr_scf if coeff == 1.0 \
                       else JMult(JConst(coeff),expr_scf)

            out_scfvar = JVar(prob.get_scf(block_name,out,loc))
            tau_scfvar = JVar(prob.TAU)
            if not block.integrator(out):
                prob.eq(out_scfvar,scf_expr)
            else:
                prob.eq(JMult(out_scfvar,tau_scfvar),scf_expr)
                uses_tau = True

        for port in block.outputs + block.inputs:
            _,mrng = prob.math_range(block_name,port,loc)
            _,hwrng = prob.hardware_range(block_name,port,loc)
            scfvar = JVar(prob.get_scf(block_name,port,loc))
            if isinstance(mrng,IValue):
                if same_sign(mrng.value,hwrng.lower) and \
                   not same_sign(mrng.value,hwrng.upper):
                    lower,upper = None,hwrng.lower

                elif not same_sign(mrng.value,hwrng.lower) and \
                     same_sign(mrng.value,hwrng.upper):
                    lower,upper = None,hwrng.upper

                else:
                    lower,upper = hwrng.lower,hwrng.upper

                if not lower is None:
                    prob.gte(JMult(JConst(abs(mrng.value)),scfvar),\
                            JConst(abs(lower)))
                prob.lte(JMult(JConst(abs(mrng.value)),scfvar),\
                        JConst(abs(upper)))

            else:
                assert(same_sign(mrng.lower,hwrng.lower))
                assert(same_sign(mrng.upper,hwrng.upper))
                prob.lte(JMult(JConst(abs(mrng.lower)),scfvar),\
                        JConst(abs(hwrng.lower)))
                prob.lte(JMult(JConst(abs(mrng.upper)),scfvar),\
                        JConst(abs(hwrng.upper)))


        if not uses_tau:
            prob.eq(JVar(prob.TAU),JConst(1.0))

def build_problem(circ):
    prob = JauntProb()

    # declare scaling factors
    print("-> Decl Scaling Factors")
    bp_decl_scaling_factors(prob,circ)

    # pass1: fill intervals
    print("-> Fill Intervals")
    bp_bind_intervals(prob,circ)

    # pass2: fill in hardware coefficients
    print("-> Fill Coefficients")
    bp_bind_coefficients(prob,circ)

    # pass3: generate problem
    print("-> Generate Problem")
    bp_generate_problem(prob,circ)

    return prob

def gpkit_expr(variables,expr):
    if expr.op == JOp.VAR:
        return variables[expr.name]

    elif expr.op == JOp.MULT:
        e1 = gpkit_expr(variables,expr.arg(0))
        e2 = gpkit_expr(variables,expr.arg(1))
        return e1*e2

    elif expr.op == JOp.CONST:
        return expr.value

    else:
        raise Exception("unsupported <%s>" % expr)

def sp_update_circuit(prob,circ,assigns):
    bindings = {}
    tau = None
    for variable,value in assigns.items():
        #print("%s = %s" % (variable,value))
        if variable.name == prob.TAU:
            tau = value
        else:
            block_name,port,loc = prob.get_scf_info(variable.name)
            bindings[(block_name,str(loc),port)] = value


    circ.set_tau(tau)
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.outputs + block.inputs:
            propobj= block.props(config.mode,port)
            if config.has_dac(port):
                scale_factor = bindings[(block_name,str(loc),port)]
                value = config.dac(port)
                scaled_value = scale_factor*value
                assert(isinstance(propobj,props.DigitalProperties))
                closest_scaled_value = propobj.value(scaled_value)
                index = propobj.index(closest_scaled_value)
                #print("%s -> %s" %\
                #      (scaled_value,closest_scaled_value))
                config.set_dac(port,index)

            elif config.has_label(port):
                label = config.label(port)
                scale_factor = bindings[(block_name,str(loc),port)]
                config.set_scf(port,scale_factor)
                #print("%s.%s = %s" % (port,label,scale_factor))

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

    new_expr1 = JMult(JConst(const1),expr1)
    new_expr2 = JMult(JConst(const2),expr2)
    return True,new_expr1,new_expr2

def solve_problem(circ,prob):
    TAU_MIN = 1e-6
    failed = False

    variables = {}
    for scf in prob.variables():
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


        #print("%s == %s" % (gp_lhs,gp_rhs))
        constraints.append(gp_lhs == gp_rhs)

    for lhs,rhs in prob.ltes():
        gp_lhs = gpkit_expr(variables,lhs)
        gp_rhs = gpkit_expr(variables,rhs)
        if isinstance(gp_lhs <= gp_rhs,bool):
            #print("assert(%s <= %s)" % (gp_lhs,gp_rhs))
            failed = failed or not (gp_lhs <= gp_rhs)
            continue

        #print("%s <= %s" % (gp_lhs,gp_rhs))
        constraints.append(gp_lhs <= gp_rhs)

    constraints.append(TAU_MIN <= variables[prob.TAU])
    #constraints.append(1.0 == variables[prob.TAU])

    if failed:
        return False,None

    objective = 1.0/variables["tau"]
    for block_name,port,loc,weight in prob.priority():
        scf = prob.get_scf(block_name,port,loc)
        objective += 1.0/variables[scf]

    model = gpkit.Model(objective,constraints)
    try:
        sln = model.solve(verbosity=2)

    except RuntimeWarning:
        sln = None

    if not sln is None:
        upd_circ = sp_update_circuit(prob,circ,
                                     sln['freevariables'])
        return True,upd_circ
    else:
        return False,None


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
            circ.config((block_name,loc)).set_scale_mode(scale_mode)

        yield circ

def scale(circ):
    for circ in iter_scaled_circuits(circ):
        prob = build_problem(circ)
        succ,circ = solve_problem(circ,prob)
        if succ:
            print("[[SUCCESS]]")
            yield circ
        else:
            print("[[FAILURE]]")
