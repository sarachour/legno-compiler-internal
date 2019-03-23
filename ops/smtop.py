from enum import Enum
import z3

class Z3Ctx:
  def __init__(self,env):
    self._solver = z3.Solver()
    self._z3vars = {}
    self._smtvars = {}
    self._smtenv = env
    self._sat = None
    self._model = None

  def sat(self):
    return self._sat

  def model(self):
    if self._sat:
      return self.translate(self._model)
    else:
      raise Exception("unsat: no model")

  def decl(self,typ,var):
    if typ == SMTEnv.Type.REAL:
      v = z3.Real(var)
    elif typ == SMTEnv.Type.BOOL:
      v = z3.Bool(var)
    self._z3vars[var] = v
    self._smtvars[v] = var

  def cstr(self,cstr):
    self._solver.add(cstr)

  def z3var(self,name):
    return self._z3vars[name]

  def translate(self,model):
    assigns = {}
    for v in self._z3vars.values():
      smtvar = self._smtvars[v]
      jvar = self._smtenv.from_smtvar(smtvar)
      assigns[jvar] = model[v]

    return assigns

  def solve(self):
    rmap = {
      'unsat': False,
      'unknown': False,
      'sat': True
    }
    result = self._solver.check()
    print("result: %s" % result)
    self._sat = rmap[str(result)]
    print("sat: %s" % self._sat)
    if self.sat():
      m = self._solver.model()
      self._model = m
      return self.translate(m)

  def negate_model(self,model):
    clauses = []
    for v in self._z3vars.values():
      if z3.is_bool(v):
        value = model[v]
        clauses.append(value != v)

    self.cstr(z3.Or(clauses))

  def next_solution(self):
    assert(self._sat)
    self.negate_model(self._model)
    return self.solve()

class SMTEnv:
  class Type(Enum):
    REAL = "Real"
    BOOL = "Bool"

  def __init__(self):
    self._decls = []
    self._cstrs = []
    self._index = 0
    self._to_smtvar = {}
    self._from_smtvar = {}

  def decl(self,name,typ):
    if name in self._to_smtvar:
      return self._to_smtvar[name]

    assert(isinstance(typ, SMTEnv.Type))
    vname = "v%d" % self._index
    self._index += 1
    self._decls.append(SMTDecl(vname,typ))
    self._to_smtvar[name] = vname
    self._from_smtvar[vname] = name

  def from_smtvar(self,name):
    return self._from_smtvar[name]

  def get_smtvar(self,name):
    return self._to_smtvar[name]

  def eq(self,e1,e2):
    self._cstrs.append(SMTAssert(SMTEq(e1,e2)))

  def lt(self,e1,e2):
    self._cstrs.append(SMTAssert(SMTLT(e1,e2)))

  def lte(self,e1,e2):
    self._cstrs.append(SMTAssert(SMTLTE(e1,e2)))

  def cstr(self,c):
    self._cstrs.append(SMTAssert(c))

  def to_z3(self):
    ctx = Z3Ctx(self)
    for decl in self._decls:
      decl.to_z3(ctx)

    for cstr in self._cstrs:
      cstr.to_z3(ctx)

    return ctx

  def to_smtlib2(self):
    prog = ""
    for decl in self._decls:
      prog += ("%s\n" % decl.to_smtlib2())

    for cstr in self._cstrs:
      prog += ("%s\n" % cstr.to_smtlib2())

    prog += "(check-sat)\n"
    prog += "(get-model)\n"
    prog += "(exit)\n"
    return prog

class SMTVar:

  def __init__(self,name):
    self._name = name

  def to_smtlib2(self):
    return "%s" % self._name

  def to_z3(self,ctx):
    return ctx.z3var(self._name)

class SMTConst:

  def __init__(self,value):
    self._value = value

  def to_z3(self,ctx):
    return self._value

  def to_smtlib2(self):
    return "%f" % self._value

class SMTMult:

  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_z3(self,ctx):
    return self._arg1.to_z3(ctx)*self._arg2.to_z3(ctx)

  def to_smtlib2(self):
    return "(* %s %s)" % \
      (self._arg1.to_smtlib2(),
       self._arg2.to_smtlib2())


class SMTAdd:
  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_z3(self,ctx):
    return self._arg1.to_z3(ctx)+self._arg2.to_z3(ctx)


  def to_smtlib2(self):
    return "(+ %s %s)" % \
      (self._arg1.to_smtlib2(),
       self._arg2.to_smtlib2())

class SMTDecl:

  def __init__(self,name,t):
    self._name = name
    self._type = t

  def to_z3(self,ctx):
    ctx.decl(self._type,self._name)

  def to_smtlib2(self):
    return "(declare-const %s %s)"  \
      % (self._name,self._type.value)

class SMTEq:

  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_z3(self,ctx):
    return self._arg1.to_z3(ctx) == self._arg2.to_z3(ctx)


  def to_smtlib2(self):
    return "(= %s %s)"  \
      % (self._arg1.to_smtlib2(),
         self._arg2.to_smtlib2())


class SMTLT:

  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_z3(self,ctx):
    return self._arg1.to_z3(ctx) < self._arg2.to_z3(ctx)

  def to_smtlib2(self):
    return "(< %s %s)"  \
      % (self._arg1.to_smtlib2(),
         self._arg2.to_smtlib2())


class SMTExactlyN:

  def __init__(self,vs,n):
    self._vars = vs
    self._n = n

  def to_z3(self,ctx):
    args = list(map(lambda v: (ctx.z3var(v),1), self._vars))
    return z3.PbEq(args,self._n)

  def to_smtlib2(self):
    args = self._vars
    argstr = " ".join(args)
    typstr = " ".join(map(lambda i: '1', \
                          range(1,len(args)+1)))
    return "((_ pbeq %s %d) %s)"  \
      % (typstr,self._n,argstr)


class SMTAssert:

  def __init__(self,cstr):
    self._cstr = cstr

  def to_z3(self,ctx):
    ctx.cstr(self._cstr.to_z3(ctx))

  def to_smtlib2(self):
    return "(assert %s)"  \
      % (self._cstr.to_smtlib2())


class SMTImplies:

  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_z3(self,ctx):
    return z3.Implies(self._arg1.to_z3(ctx),
                      self._arg2.to_z3(ctx))

  def to_smtlib2(self):
    return "(implies %s %s)"  \
      % (self._arg1.to_smtlib2(),
         self._arg2.to_smtlib2())


class SMTLTE:

  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_z3(self,ctx):
    return self._arg1.to_z3(ctx) <= self._arg2.to_z3(ctx)

  def to_smtlib2(self):
    return "(<= %s %s)"  \
      % (self._arg1.to_smtlib2(),
         self._arg2.to_smtlib2())

