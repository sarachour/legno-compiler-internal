import compiler.jaunt_pass.basic_opt as boptlib
import compiler.jaunt_pass.phys_opt as physoptlib
import ops.jop as jop


#TODO: what is low range, high range and med range?
#TODO: setRange: integ.in, integ.out and mult have setRange functions.
#TODO: how do you set wc in the integrator? Is it through the setRange function?
class JauntObjectiveFunctionManager():

    @staticmethod
    def basic_methods():
        #return ['fast','slow','max']
        return [
            boptlib.SlowObjFunc,
            boptlib.FastObjFunc,
            boptlib.MaxSignalObjFunc,
            boptlib.MaxSignalAndSpeedObjFunc,
            boptlib.MaxSignalAndStabilityObjFunc,

        ]

    @staticmethod
    def physical_methods():
        #return ['lo-noise', 'lo-bias', 'lo-delay']
        return [boptlib.MaxSignalAtSpeedObjFunc, \
                physoptlib.LowNoiseObjFunc]

    def __init__(self,jenv):
        self.method = None
        self.jenv = jenv
        self._results = {}

    def result(self,objective):
        return self._results[objective]

    def add_result(self,objective,sln):
        assert(not objective in self._results)
        self._results[objective] = sln


    def objective(self,circuit,varmap):
        assert(not self.method is None)
        gen = None
        for obj in self.basic_methods() + self.physical_methods():
            if obj.name() == self.method:
                gen = obj.make(circuit,self,varmap)

        for obj in gen:
            yield obj


class JauntEnv:
    LUT_SCF_IN = "LUTSCFIN"
    LUT_SCF_OUT = "LUTSCFOUT"
    TAU = "tau"

    def __init__(self):
        # scaling factor name to port
        self._to_scvar = {}
        self._from_scvar ={}
        self._in_use = {}

        self._eqs = []
        self._ltes = []
        # metavar
        self._meta = {}
        self._metavar = 0
        self._failed = False
        self._use_tau = False
        self._solved = False

    def set_solved(self,solved_problem):
        self._solved = solved_problem

    def solved(self):
        return self._solved

    def use_tau(self):
        self._use_tau = True

    def uses_tau(self):
        return self._use_tau

    def fail(self):
        self._failed = True

    def failed(self):
        return self._failed

    def in_use(self,scvar):
        return (scvar) in self._in_use

    def variables(self):
        yield JauntEnv.TAU

        #for tauvar in self._from_tauvar.keys():
        #    yield tauvar

        for scvar in self._from_scvar.keys():
            yield scvar

    def eqs(self):
        for lhs,rhs in self._eqs:
            yield (lhs,rhs)

    def ltes(self):
        for lhs,rhs in self._ltes:
            yield (lhs,rhs)


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
        scvar = self._to_scvar[(block_name,loc,port,handle)]
        self._in_use[scvar] = True
        return scvar


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
        self.lte(v2,v1)


def decl_scale_variables(jenv,circ):
    # define scaling factors
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for output in block.outputs:
            jenv.decl_scvar(block_name,loc,output)
            for handle in block.handles(config.comp_mode,output):
                jenv.decl_scvar(block_name,loc,output,handle=handle)

            if block.name == "lut":
                jenv.decl_scvar(block_name,loc,output, \
                                handle=jenv.LUT_SCF_OUT)
                pass

        for inp in block.inputs:
            jenv.decl_scvar(block_name,loc,inp)
            if block.name == "lut":
                jenv.decl_scvar(block_name,loc,inp, \
                                handle=jenv.LUT_SCF_IN)
                pass

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


def build_lower_bound(jenv,expr,math_lower,hw_lower):
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


def build_upper_bound(jenv,expr,math_upper,hw_upper):
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
        raise Exception("uncovered ub: %s %s" % (math_upper,hw_upper))

