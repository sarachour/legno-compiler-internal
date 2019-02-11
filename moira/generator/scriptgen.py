from enum import Enum
import numpy as np
import itertools
import generator.scriptdb as scriptdb

class MoiraPragmaType(Enum):
  INPUT = 'in'
  OUTPUT = 'out'
  CONSTANT = 'const'
  TIME = 'time'
  START = 'start'
  END = 'end'
  MAP = 'map'
  PTR = 'ptr'
  REF = 'ref'

class MoiraShapeType(Enum):
  SIN = 'sin'

class MoiraParametricInput:
  class InputType(Enum):
    CONST = 'const'
    SIN = 'sin'

  class InterpType(Enum):
    LOG10 = 'log10'
    LINEAR = 'linear'

  def __init__(self,name):
    self._type = type
    self._params = {}

  @property
  def parameters(self):
    return list(self._params.keys())

  def interpolate(self,param,n):
    minval,maxval,scaletype = self._params[param]
    if scaletype == MoiraParametricInput.InterpType.LOG10:
      return np.logspace(minval,maxval,n,base=10.0)
    else:
      return np.linspace(minval,maxval,n)

  def add_param(self,inp_name,minval,maxval,scaletype):
    assert(isinstance(scaletype, MoiraParametricInput.InterpType))
    assert(minval <= maxval)
    self._params[inp_name] = (minval,maxval,scaletype)

  def build(self,pardict):
    raise NotImplementedError

  def generate(self,n):
    raise NotImplementedError

  @staticmethod
  def parse(args):
    ityp = MoiraParametricInput.InputType(args[0])
    if ityp == MoiraParametricInput.InputType.SIN:
      return MoiraSinInput.parse(args[1:])
    elif ityp == MoiraParametricInput.InputType.CONST:
      return MoiraConstInput.InputType.parse(args[1:])

class MoiraSinInput(MoiraParametricInput):

  def __init__(self,amin,amax,ascale, \
               fmin,fmax,fscale):
    MoiraParametricInput.__init__(self, \
                                  MoiraParametricInput.InputType.SIN)
    self.add_param('ampl', amin, amax, ascale)
    self.add_param('freq', fmin,fmax, fscale)

  def construct(self,pars):
    return '{ampl}*sin({freq}*t_)'.format(**pars)

  @staticmethod
  def parse(args):
    assert(args[0] == 'ampl')
    amin = float(args[1])
    amax = float(args[2])
    astep = MoiraParametricInput.InterpType(args[3])

    assert(args[4] == 'freq')
    fmin = float(args[5])
    fmax = float(args[6])
    fstep = MoiraParametricInput.InterpType(args[7])
    return MoiraSinInput(amin,amax,astep,fmin,fmax,fstep)

class MoiraConstInput(MoiraParametricInput):

  def __init__(self,amin,amax,ascale):
    MoiraParametricInput.__init__(self, \
                                  MoiraParametricInput.InputType.SIN)
    self.add_param('value', amin, amax, ascale)

  def construct(self,pars):
    return '{value}'.format(**pars)

  @staticmethod
  def parse(args):
    vmin = float(args[0])
    vmax = float(args[1])
    vstep = MoiraParametricInput.InterpType(args[2])
    return MoiraConstInput(vmin,vmax,vstep)

class MoiraDataPointer:

  def __init__(self,name,ptr_name):
    self._output = None
    self._inputs = {}
    self._consts = {}
    self._name = name
    self._ptr_name = ptr_name

  def add_const(self,inp,param,this_const,this_param):
    if not inp in self._consts:
      self._consts[inp] = {}
    self._consts[inp][param] = (this_const,this_param)


  def add_input(self,inp,param,this_inp,this_param):
    if not inp in self._inputs:
      self._inputs[inp] = {}
    self._inputs[inp][param] = (this_inp,this_param)

  def set_output(self,out,this_out):
    self._output = this_out

  def entry(self,inps,consts):
    ptr_inputs = {}
    ptr_consts = {}
    for idx in self._inputs:
      ptr_inputs[idx] = {}
      for par,(this_inp,this_param) \
          in self._inputs[idx].items():
        value = inps[this_inp][this_param]
        ptr_inputs[idx][par] = value

    for idx in self._consts:
      ptr_inputs[idx] = {}
      for par,(this_const,this_param) \
          in self._consts[idx].items():
        value = inps[this_const][this_param]
        ptr_consts[idx][par] = value

    entry = scriptdb.MoiraScriptEntry(self._name,ptr_inputs,ptr_consts,self._output)
    return entry

class MoiraOutput:

  class Reference:
    class Type(Enum):
      PTR = "ptr"
      CONST = "const"
      EXPR = 'expr'

    def __init__(self):
      self._consts = []
      self._ptrs = []
      self._expr = None

    def concretize(self,consts):
      return self._expr.format(**consts)

    def pointers(self):
      return self._ptrs

    def add_pointer(self,var):
      self._ptrs.append(var)

    def add_const(self,var):
      self._consts.append(var)

    def set_expr(self,expr):
      self._expr = expr

    @staticmethod
    def parse(args):
      idx = 0
      ref = MoiraOutput.Reference()
      while idx < len(args):
        typ = MoiraOutput.Reference.Type(args[idx])
        name = args[idx+1]
        if typ == MoiraOutput.Reference.Type.PTR:
          ref.add_pointer(name)
        elif typ == MoiraOutput.Reference.Type.CONST:
          ref.add_const(name)
        elif typ == MoiraOutput.Reference.Type.EXPR:
          ref.set_expr(name)

        idx += 2;

      assert(not ref._expr is None)
      return ref

  def __init__(self,name):
    self._reference = None
    self._name = name

  @property
  def name(self):
    return self._name

  @property
  def reference(self):
    return self._reference

  def set_reference(self,r):
    assert(isinstance(r,MoiraOutput.Reference))
    self._reference = r

class MoiraGrendelExperimentGenerator:

  def __init__(self,name):
    self._prog = []
    self._inputs = {}
    self._outputs = {}
    self._consts = {}
    self._ptrs = {}
    self._sim_time = 0
    self._name = name

  def add_pointer(self,varname,experiment_name):
    self._ptrs[varname] = MoiraDataPointer(varname,
                                           experiment_name)

  def pointer(self,varname):
    return self._ptrs[varname]

  def add_stmt(self,stmt):
    self._prog.append(stmt)

  def set_input(self,idx,inp):
    assert(isinstance(inp,MoiraParametricInput))
    assert(isinstance(idx,int))
    assert(not idx in self._inputs)
    self._inputs[idx] = inp

  def add_output(self,idx,name):
    self._outputs[idx] = MoiraOutput(name)

  def output(self,idx):
    return self._outputs[idx]

  def set_const(self,name,inp):
    assert(isinstance(inp,MoiraParametricInput))
    assert(not name in self._consts)
    self._consts[name] = inp

  def set_sim_time(self,time):
    self._sim_time = time


  def generate_script(self,path_handler,inps,consts):
    prog = []
    prog.append('reset')

    for idx in self._inputs.keys():
      prog.append('micro_use_due_dac %d' % idx)

    for stmt in [
        'micro_use_osc',
        'osc_set_volt_range 0 -1.5 2.5',
        'osc_set_volt_range 1 -1.5 2.5',
        'osc_set_sim_time %f' % self._sim_time,
        'micro_set_sim_time %f %f' % (self._sim_time,self._sim_time),
        'micro_compute_offsets',
        'micro_get_num_adc_samples',
        'micro_get_num_dac_samples',
        'micro_get_time_delta',
        'micro_use_chip',
    ]:
      prog.append(stmt)


    for idx,inp in self._inputs.items():
      expr = inp.construct(inps[idx])
      prog.append("set_due_dac_values %d %s" % (idx,expr))

    for stmt in self._prog:
      prog.append(stmt.format(**consts))

    for stmt in [
        'osc_setup_trigger',
        'micro_setup_chip',
        'micro_get_status',
        'osc_setup_trigger',
        'micro_run',
        'micro_get_status',
        'micro_teardown_chip'
    ]:
      prog.append(stmt)

    for out_idx,out in self._outputs.items():
      this_prog = list(prog)
      entry = scriptdb.MoiraScriptEntry(self._name,inps,consts,out_idx)
      filename = path_handler.database_file(entry.identifier())
      this_prog.append('get_osc_values differential 0 1 %s %s' % \
                       (out.name,filename))

      if not out.reference is None:
        ref = out.reference
        entry.set_reference(ref.concretize(consts))
        for ptr in out.reference.pointers():
          ptr_entry = self._ptrs[ptr].entry(inps,consts)
          entry.add_pointer(ptr,ptr_entry)

      yield entry,this_prog


  def generate(self,path_handler,n):
    def set_value(d,k1,k2,v):
      if not k1 in d:
        d[k1] = {}
      d[k1][k2] = v

    inputs = list(self._inputs.keys())
    terms = []
    options = []
    for inpname,inp in self._inputs.items():
      for par in inp.parameters:
        terms.append(('in',inpname,par))
        values = inp.interpolate(par,n)
        options.append(values)

    for constname,const in self._consts.items():
      for par in const.parameters:
        terms.append(('const',constname,par))
        values = const.interpolate(par,n)
        options.append(values)

    for opt in itertools.product(*options):
      pars = dict(zip(terms,opt))
      consts = {}
      inps = {}
      for (kind,var,param),value in pars.items():
        if kind == 'in':
          set_value(inps,var,param,value)
        elif kind == 'const':
          consts[var] = value

      for entry,prog in self.generate_script(path_handler,inps,consts):
        yield entry,prog

class MoiraGrendelEnv:

  def __init__(self):
    self._experiments = []

  def add(self,e):
    self._experiments.append(e)

  def experiments(self):
    return self._experiments


def parse_pragma(menv,mexp,_args):
  cmd = MoiraPragmaType(_args[0])
  args = _args[1:]
  if cmd == MoiraPragmaType.START:
    name = args[0]
    return MoiraGrendelExperimentGenerator(name)

  elif cmd == MoiraPragmaType.TIME:
    runtime = float(args[0])
    mexp.set_sim_time(runtime)
    return mexp

  elif cmd == MoiraPragmaType.END:
    menv.add(mexp)
    return None

  elif cmd == MoiraPragmaType.INPUT:
    in_idx = int(args[0])
    inp = MoiraParametricInput.parse(args[1:])
    mexp.set_input(in_idx,inp)
    return mexp

  elif cmd == MoiraPragmaType.PTR:
    name = args[0]
    exper = args[1]
    mexp.add_pointer(name, exper)
    return mexp

  elif cmd == MoiraPragmaType.MAP:
    name = args[0]
    data_ptr = mexp.pointer(name)
    if args[1] == 'in':
      this_idx,this_param = int(args[2]),args[3]
      ptr_idx,ptr_param = int(args[4]),args[5]
      data_ptr.add_input(this_idx,this_param,\
                         ptr_idx,ptr_param)
      return mexp

    elif args[1] == 'out':
      ptr_idx = int(args[2])
      this_idx = int(args[3])
      data_ptr.set_output(this_idx,ptr_idx)
      return mexp

    else:
      raise Exception("unknown")

  elif cmd == MoiraPragmaType.OUTPUT:
    out_idx = int(args[0])
    mexp.add_output(out_idx,args[1])
    return mexp

  elif cmd == MoiraPragmaType.REF:
    out_idx = int(args[0])
    out = mexp.output(out_idx)
    ref = MoiraOutput.Reference.parse(args[1:])
    out.set_reference(ref)
    return mexp

  elif cmd == MoiraPragmaType.CONSTANT:
    ident = args[0]
    inp = MoiraConstInput.parse(args[1:])
    mexp.set_const(ident,inp)
    return mexp

  else:
    raise Exception("%s: %s" % (cmd,args))

def read(filename):
  menv = MoiraGrendelEnv()
  experiment = None
  with open(filename) as fh:
    stub = []
    for line in fh:
      args = line.strip().split()
      if len(args) == 0:
        continue

      if args[0] == '@pragma':
        experiment = parse_pragma(menv,experiment,args[1:])
      else:
        experiment.add_stmt(line.strip())

  return menv
