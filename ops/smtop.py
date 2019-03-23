from enum import Enum

class SMTEnv:
  class Type(Enum):
    REAL = "Real"

  def __init__(self):
    self._decls = []
    self._cstrs = []
    self._index = 0
    self._to_smtvar = {}

  def decl(self,name,typ):
    if name in self._to_smtvar:
      return self._to_smtvar[name]

    assert(isinstance(typ, SMTEnv.Type))
    vname = "v%d" % self._index
    self._index += 1
    self._decls.append(SMTDecl(vname,typ))
    self._to_smtvar[name] = vname

  def get_smtvar(self,name):
    return self._to_smtvar[name]

  def eq(self,e1,e2):
    self._cstrs.append(SMTEq(e1,e2))

  def lt(self,e1,e2):
    self._cstrs.append(SMTLT(e1,e2))

  def lte(self,e1,e2):
    self._cstrs.append(SMTLTE(e1,e2))

  def to_smtlib2(self):
    prog = "(set-logic QF_NRA)\n"
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


class SMTConst:

  def __init__(self,value):
    self._value = value

  def to_smtlib2(self):
    return "%f" % self._value

class SMTMult:

  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_smtlib2(self):
    return "(* %s %s)" % \
      (self._arg1.to_smtlib2(),
       self._arg2.to_smtlib2())


class SMTAdd:
  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_smtlib2(self):
    return "(+ %s %s)" % \
      (self._arg1.to_smtlib2(),
       self._arg2.to_smtlib2())

class SMTDecl:

  def __init__(self,name,t):
    self._name = name
    self._type = t

  def to_smtlib2(self):
    return "(declare-fun %s () %s)"  \
      % (self._name,self._type.value)

class SMTEq:

  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_smtlib2(self):
    return "(assert (= %s %s))"  \
      % (self._arg1.to_smtlib2(),
         self._arg2.to_smtlib2())


class SMTLT:

  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_smtlib2(self):
    return "(assert (< %s %s))"  \
      % (self._arg1.to_smtlib2(),
         self._arg2.to_smtlib2())


class SMTLTE:

  def __init__(self,e1,e2):
    self._arg1 = e1
    self._arg2 = e2

  def to_smtlib2(self):
    return "(assert (<= %s %s))"  \
      % (self._arg1.to_smtlib2(),
         self._arg2.to_smtlib2())

