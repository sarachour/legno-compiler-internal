import util.config as cfg
import util.paths as paths
import bmark.diffeqs as diffeqs
import sqlite3
from enum import Enum
import os
import datetime
import lab_bench.lib.command as cmd
import lab_bench.lib.expcmd.micro_getter as microget
import lab_bench.lib.expcmd.osc as osc
import json

def get_output_files(grendel_script):
  with open(grendel_script,'r') as fh:
    for line in fh:
      instr = cmd.parse(line)
      if isinstance(instr,osc.OscGetValuesCmd):
        yield instr.filename
      elif isinstance(instr,microget.MicroGetADCValuesCmd):
        yield instr.filename

def make_args(bmark,arco_inds,jaunt_indx,model,opt,menv_name,hwenv_name):
  return  {
    'bmark':bmark,
    'arco0':arco_inds[0],
    'arco1':arco_inds[1],
    'arco2':arco_inds[2],
    'arco3':arco_inds[3],
    'jaunt':jaunt_indx,
    'model': model,
    'opt': opt,
    'menv':menv_name,
    'hwenv': hwenv_name
  }

class OutputStatus(Enum):
  PENDING = "pending"
  RAN = "ran"
  ANALYZED = "analyzed"

class MismatchStatus(Enum):
  UNKNOWN = "unknown"
  BAD = "bad"
  NONIDEAL = "nonideal"
  IDEAL = "ideal"

  def to_code(self):
    if self == MismatchStatus.UNKNOWN:
      return 0
    elif self == MismatchStatus.BAD:
      return 1
    elif self == MismatchStatus.NONIDEAL:
      return 2
    elif self == MismatchStatus.IDEAL:
      return 3

  def to_score(self):
    if self == MismatchStatus.IDEAL:
      return 1.0
    elif self == MismatchStatus.NONIDEAL:
      return 0.5
    elif self == MismatchStatus.BAD:
      return 0.0
    elif self == MismatchStatus.UNKNOWN:
      return 1.0

  @staticmethod
  def from_code(i):
    if i == 0:
      return MismatchStatus.UNKNOWN
    elif i == 1:
      return MismatchStatus.BAD
    elif i == 2:
      return MismatchStatus.NONIDEAL
    elif i == 3:
      return MismatchStatus.IDEAL
    else:
      raise Exception("unknown <%s>" % x)

  @staticmethod
  def options():
    yield MismatchStatus.UNKNOWN
    yield MismatchStatus.BAD
    yield MismatchStatus.NONIDEAL
    yield MismatchStatus.IDEAL

  @staticmethod
  def abbrevs():
    return list(map(lambda o: o.to_abbrev(), \
                    MismatchStatus.options()))

  def to_abbrev(self):
    if self == MismatchStatus.BAD:
      return "b"
    elif self == MismatchStatus.UNKNOWN:
      return "?"
    elif self == MismatchStatus.IDEAL:
      return "g"
    elif self == MismatchStatus.NONIDEAL:
      return "m"

  @staticmethod
  def from_abbrev(x):
    if x == 'b':
      return MismatchStatus.BAD
    elif x == '?':
      return MismatchStatus.UNKNOWN
    elif x == 'g':
      return MismatchStatus.IDEAL
    elif x == 'm':
      return MismatchStatus.NONIDEAL
    else:
      raise Exception("unknown <%s>" % x)

class ExperimentStatus(Enum):
  PENDING = "pending"
  RAN = "ran"
  ANALYZED = "analyzed"

class OutputEntry:

  def __init__(self,db,bmark,arco_indices,jaunt_index,
               model,
               objective_fun,math_env,hw_env,varname,trial):
    self._db = db
    self._bmark = bmark
    self._arco_indices = arco_indices
    self._jaunt_index = jaunt_index
    self._objective_fun = objective_fun
    self._model = model
    self._math_env = math_env
    self._hw_env = hw_env
    self._varname = varname
    self._trial = trial
    self._transform = None
    self._status = None
    self._out_file = None
    self._quality = None
    self._rank = None
    self._tau = None
    self._scf = None
    self._runtime = None
    self._modif = None
    self._columns = None

  @property
  def transform(self):
    return self._transform


  @property
  def trial(self):
    return self._trial


  @property
  def tau(self):
    return self._tau


  @property
  def fmax(self):
    return self._fmax

  @property
  def scf(self):
    return self._scf


  @property
  def transform(self):
    return self._transform

  @property
  def rank(self):
    return self._rank


  @property
  def quality(self):
    return self._quality

  @property
  def model(self):
    return self._model

  @property
  def bmark(self):
    return self._bmark

  @property
  def objective_fun(self):
    return self._objective_fun

  @property
  def arco_indices(self):
    return self._arco_indices

  @property
  def jaunt_index(self):
    return self._jaunt_index

  @property
  def hw_env(self):
    return self._hw_env

  @property
  def math_env(self):
    return self._math_env

  @property
  def columns(self):
    return self._columns

  @property
  def varname(self):
    return self._varname

  @property
  def status(self):
    return self._status

  @property
  def out_file(self):
    return self._out_file

  @staticmethod
  def from_db_row(db,args):
    entry = OutputEntry(
      db=db,
      bmark=args['bmark'],
      arco_indices=[args['arco0'],args['arco1'], \
                  args['arco2'], args['arco3']],
      model=args['model'],
      objective_fun=args['opt'],
      jaunt_index=args['jaunt'],
      math_env=args['menv'],
      hw_env=args['hwenv'],
      varname=args['varname'],
      trial=args['trial']
    )
    entry._columns = args
    entry._out_file=args['out_file']
    entry._trial=args['trial']
    entry._quality=args['quality']
    entry._rank=args['rank']
    entry._fmax=args['fmax']
    if not args['transform'] is None:
      entry._transform = json.loads(args['transform'])
    else:
      entry._transform = None
    entry._scf=args['scf']
    entry._tau=args['tau']
    entry._status=OutputStatus(args['status'])
    entry._modif=args['modif']
    entry._columns = args
    return entry

  def delete(self):
     self._db.delete_output(self._bmark,
                            self._arco_indices,
                            self._jaunt_index,
                            self._model,
                            self._objective_fun,
                            self._math_env,
                            self._hw_env,
                            self._varname,
                            self._trial)

  def update_db(self,args):
    self._db.update_output(self._bmark,
                           self._arco_indices,
                           self._jaunt_index,
                           self._model,
                           self._objective_fun,
                           self._math_env,
                           self._hw_env,
                           self._varname,
                           self._trial,
                           args)


  def set_status(self,new_status):
    assert(isinstance(new_status,OutputStatus))
    self.update_db({'status':new_status.value})
    self._status = new_status


  def set_rank(self,new_rank):
    if new_rank == float('inf'):
      new_rank = 1e9
    if new_rank == float('-inf'):
      new_rank = -1e9

    self.update_db({'rank':new_rank})
    self._rank = new_rank


  def set_scf(self,new_scf):
    self.update_db({'scf':new_scf})
    self._scf = new_scf

  def set_tau(self,new_tau):
    self.update_db({'tau':new_tau})
    self._tau = new_tau

  def set_fmax(self,new_fmax):
    self.update_db({'fmax':new_fmax})
    self._fmax = new_fmax

  def set_transform(self,new_transform):
    self.update_db({'transform': \
                    json.dumps(new_transform)})
    self._transform = new_transform

  def set_quality(self,new_quality):
    self.update_db({'quality':new_quality})
    self._quality = new_quality


  @property
  def circ_ident(self):
    return "%s(%s,%s)" % (self._bmark,
                          self._arco_indices,
                          self._jaunt_index)
  @property
  def port_ident(self):
    return "%s.%s" % (self.circ_ident,self._varname)



  @property
  def ident(self):
    return "%s[%s,%s](%s,%s)" % (self.port_ident,
                              self._objective_fun,
                              self._model,
                              self._math_env,
                              self._hw_env)

  def __repr__(self):
    s = "{\n"
    s += "ident=%s\n" % self.ident
    s += "status=%s\n" % (self._status.value)
    s += "out_file=%s\n" % (self._out_file)
    s += "rank=%s\n" % (self._rank)
    s += "tau=%s\n" % (self._tau)
    s += "fmax=%s\n" % (self._fmax)
    s += "quality=%s\n" % (self._quality)
    s += "transform=%s\n" % (self._transform)
    s += "}\n"
    return s



class ExperimentEntry:

  def __init__(self,db,bmark,arco_indices,jaunt_index,
               model,objective_fun,math_env,hw_env):
    self._bmark = bmark
    self._arco_indices = arco_indices
    self._jaunt_index = jaunt_index
    self._objective_fun = objective_fun
    self._model = model
    self._math_env = math_env
    self._hw_env = hw_env
    self._grendel_file = None
    self._jaunt_circ_file = None
    self._rank= None
    self._energy= None
    self._runtime= None
    self._quality= None
    self._mismatch = None
    self._db = db
    self._columns = None

  @property
  def rank(self):
    return self._rank


  @property
  def runtime(self):
    return self._runtime

  @property
  def energy(self):
    return self._energy


  @property
  def quality(self):
    return self._quality

  @property
  def columns(self):
    return self._columns


  @property
  def status(self):
    return self._status


  @property
  def bmark(self):
    return self._bmark


  @property
  def objective_fun(self):
    return self._objective_fun


  @property
  def math_env(self):
    return self._math_env



  @property
  def jaunt_circ_file(self):
    return self._jaunt_circ_file

  @property
  def mismatch(self):
    return self._mismatch


  @property
  def grendel_file(self):
    return self._grendel_file

  def outputs(self):
    for outp in self._db.get_outputs(self._bmark, \
                                     self._arco_indices, \
                                     self._jaunt_index, \
                                     self._model, \
                                     self._objective_fun, \
                                     self._math_env, \
                                     self._hw_env):
      yield outp

  def synchronize(self):
    # delete if we're missing relevent files
    if not os.path.isfile(self.grendel_file) or \
       not os.path.isfile(self.jaunt_circ_file):
      self.delete()
      return

    clear_computed = False
    for output in self.outputs():
      if os.path.isfile(output.out_file):
        if output.status == OutputStatus.PENDING:
          output.set_status(OutputStatus.RAN)
      else:
        if output.status == OutputStatus.RAN:
          output.set_status(OutputStatus.PENDING)


    not_done = any(map(lambda out: out.status == OutputStatus.PENDING, \
                      self.outputs()))
    if not not_done:
      self.set_status(ExperimentStatus.RAN)
    else:
      self.set_status(ExperimentStatus.PENDING)

  def update_db(self,args):
    self._db.update_experiment(self._bmark,
                               self._arco_indices,
                               self._jaunt_index,
                               self._model,
                               self._objective_fun,
                               self._math_env,
                               self._hw_env,
                               args)

  def set_status(self,new_status):
    assert(isinstance(new_status,ExperimentStatus))
    self.update_db({'status':new_status.value})
    self._status = new_status

  def set_mismatch(self,new_mismatch):
    assert(isinstance(new_mismatch,MismatchStatus))
    if new_mismatch:
      self.update_db({'mismatch':new_mismatch.to_code()})
    else:
      self.update_db({'mismatch':new_mismatch.to_code()})
    self._mismatch = new_mismatch


  def set_rank(self,new_rank):
    if new_rank == float('inf'):
      new_rank = 1e9
    if new_rank == float('-inf'):
      new_rank = -1e9

    self.update_db({'rank':new_rank})
    self._rank = new_rank

  def set_quality(self,new_quality):
    self.update_db({'quality':new_quality})
    self._quality = new_quality

  def set_energy(self,new_energy):
    self.update_db({'energy':new_energy})
    self._energy = new_energy


  def set_runtime(self,new_runtime):
    self.update_db({'runtime':new_runtime})
    self._runtime = new_runtime

  def delete(self):
    for outp in self.get_outputs():
      outp.delete()

    self._db.delete_experiment(self._bmark,
                               self._arco_indices,
                               self._jaunt_index,
                               self._model,
                               self._objective_fun,
                               self._math_env,
                               self._hw_env)

  def get_outputs(self):
    return self._db.get_outputs(self._bmark, \
                                self._arco_indices,
                                self._jaunt_index,
                                self._model,
                                self._objective_fun,
                                self._math_env, self._hw_env)

  @staticmethod
  def from_db_row(db,args):
    entry = ExperimentEntry(
      db=db,
      bmark=args['bmark'],
      arco_indices=[args['arco0'],args['arco1'], \
                  args['arco2'], args['arco3']],
      model=args['model'],
      objective_fun=args['opt'],
      jaunt_index=args['jaunt'],
      math_env=args['menv'],
      hw_env=args['hwenv']
    )

    entry._grendel_file,=args['grendel_file'],
    entry._jaunt_circ_file,=args['jaunt_circ_file'],
    entry._rank=args['rank']
    entry._quality=args['quality']
    entry._energy=args['energy']
    entry._runtime=args['runtime']
    entry._status=ExperimentStatus(args['status'])
    entry._modif = args['modif']
    entry._mismatch = MismatchStatus.from_code(args['mismatch'])
    entry._columns = args
    return entry

  @property
  def circ_ident(self):
    return "%s(%s,%s)" % (self._bmark,
                          self._arco_indices,
                          self._jaunt_index)

  @property
  def ident(self):
    return "%s[%s](%s,%s)" % (self.circ_ident,
                              self._objective_fun,
                              self._math_env,
                              self._hw_env)

  def __repr__(self):
    s = "{\n"
    s += "bmark=%s\n" % (self.bmark)
    s += "ident=%s\n" % (self.ident)
    s += "status=%s\n" % (self._status.value)
    s += "grendel_file=%s\n" % (self._grendel_file)
    s += "jaunt_circ=%s\n" % (self._jaunt_circ_file)
    s += "rank=%s\n" % (self._rank)
    s += "energy=%s\n" % (self._energy)
    s += "runtime=%s\n" % (self._runtime)
    s += "quality=%s\n" % (self._quality)
    s += "}\n"
    return s



class ExperimentDB:

  def __init__(self):
    path = cfg.EXPERIMENT_DB
    self._conn = sqlite3.connect(path)
    self._curs = self._conn.cursor()
    cmd = '''CREATE TABLE IF NOT EXISTS experiments
             (bmark text NOT NULL,
              status text NOT NULL,
              modif timestamp,
              arco0 int NOT NULL,
              arco1 int NOT NULL,
              arco2 int NOT NULL,
              arco3 int NOT NULL,
              jaunt int NOT NULL,
              model text NOT NULL,
              opt text NOT NULL,
              menv text NOT NULL,
              hwenv text NOT NULL,
              grendel_file text,
              jaunt_circ_file text,
              rank real,
              mismatch int,
              quality real,
              energy real,
              runtime real,
              PRIMARY KEY (bmark,arco0,arco1,
                           arco2,arco3,jaunt,
                           model,opt,menv,hwenv)
             );
    '''
    self._experiment_order = ['bmark','status','modif','arco0', \
                              'arco1','arco2', \
                              'arco3','jaunt',
                              'model','opt','menv','hwenv',
                              'grendel_file', \
                              'jaunt_circ_file',
                              'rank','mismatch',
                              'quality', \
                              'energy','runtime']

    self._experiment_modifiable =  \
                                   ['rank','status','modif','quality', \
                                    'energy','runtime','mismatch']
    self._curs.execute(cmd)

    cmd = '''CREATE TABLE IF NOT EXISTS outputs( bmark text NULL,
    status text NOT NULL,
    arco0 int NOT NULL,
    arco1 int NOT NULL,
    arco2 int NOT NULL,
    arco3 int NOT NULL,
    jaunt int NOT NULL,
    model text NOT NULL,
    opt text NOT NULL,
    menv text NOT NULL,
    hwenv text NOT NULL,
    varname text NOT NULL,
    trial int NOT NULL,
    out_file text,
    rank real,
    quality real,
    transform text,
    fmax real,
    tau real,
    scf real,
    modif timestamp,
    PRIMARY KEY (bmark,arco0,arco1,arco2,arco3,jaunt,
                 model,opt,menv,hwenv,varname,trial)
    FOREIGN KEY (bmark,arco0,arco1,arco2,arco3,jaunt,
                 model,opt,menv,hwenv)
    REFERENCES experiments(bmark,arco0,arco1,arco2,arco3,jaunt,
                           model,opt,menv,hwenv)
    )
    '''
    self._output_order = ['bmark','status','arco0', \
                          'arco1','arco2', \
                          'arco3','jaunt','model','opt','menv','hwenv',
                          'varname','trial','out_file', \
                          'rank','quality','transform', \
                          'fmax','tau','scf','modif']

    self._output_modifiable = ['quality','modif','status','rank','transform', \
                               'tau','scf','fmax']
    self._curs.execute(cmd)
    self._conn.commit()

  def close(self):
    self._conn.close()

  def _get_output_rows(self,where_clause):
    cmd = '''SELECT * FROM outputs {where_clause}'''
    conc_cmd = cmd.format(where_clause=where_clause)
    for values in list(self._curs.execute(conc_cmd)):
      assert(len(values) == len(self._output_order))
      args = dict(zip(self._output_order,values))
      yield OutputEntry.from_db_row(self,args)


  def _get_experiment_rows(self,where_clause):
    cmd = '''SELECT * FROM experiments {where_clause}'''
    conc_cmd = cmd.format(where_clause=where_clause)
    for values in list(self._curs.execute(conc_cmd)):
      assert(len(values) == len(self._experiment_order))
      args = dict(zip(self._experiment_order,values))
      yield ExperimentEntry.from_db_row(self,args)


  def get_all(self):
    for entry in self._get_experiment_rows(""):
      yield entry

  def get_by_status(self,status):
    assert(isinstance(status,ExperimentStatus))
    where_clause = "WHERE status=\"%s\"" % status.value
    for entry in self._get_experiment_rows(where_clause):
      yield entry

  def to_where_clause(self,bmark,arco_inds,jaunt_inds,model,opt, \
                      menv_name,hwenv_name,varname=None,trial=None):
    cmd = '''WHERE bmark = "{bmark}"
    AND arco0 = {arco0}
    AND arco1 = {arco1}
    AND arco2 = {arco2}
    AND arco3 = {arco3}
    AND jaunt = {jaunt}
    AND model = "{model}"
    AND opt = "{opt}"
    AND menv = "{menv}"
    AND hwenv = "{hwenv}"
    '''
    args = make_args(bmark,arco_inds,jaunt_inds,model,opt, \
                     menv_name,hwenv_name)
    if not varname is None:
      cmd += "AND varname = \"{varname}\""
      args['varname'] = varname
    if not trial is None:
      cmd += "AND trial = {trial}"
      args['trial'] = trial


    conc_cmd = cmd.format(**args)
    return conc_cmd

  def update_output(self,bmark,arco_inds,jaunt_inds,model,opt, \
                    menv_name,hwenv_name,varname,trial,new_fields):
    cmd = '''
    UPDATE outputs
    SET {assign_clause} {where_clause};
    '''
    where_clause = self.to_where_clause(bmark,\
                                        arco_inds,jaunt_inds,
                                        model,
                                        opt, \
                                        menv_name,hwenv_name,
                                        varname=varname,
                                        trial=trial)
    new_fields['modif'] = datetime.datetime.now()
    assign_subclauses = []
    for field,value in new_fields.items():
      assert(field in self._output_modifiable)
      if field == 'modif' or field == 'status' or field == 'transform':
        subcmd = "%s=\"%s\"" % (field,value)
      else:
        subcmd = "%s=%s" % (field,value)
      assign_subclauses.append(subcmd)

    assign_clause = ",".join(assign_subclauses)
    conc_cmd = cmd.format(where_clause=where_clause, \
                          assign_clause=assign_clause)
    self._curs.execute(conc_cmd)
    self._conn.commit()


  def update_experiment(self,bmark,arco_inds,jaunt_inds,model, \
                        opt,menv_name,hwenv_name,new_fields):
    cmd = '''
    UPDATE experiments
    SET {assign_clause} {where_clause};
    '''
    where_clause = self.to_where_clause(bmark,\
                                        arco_inds,jaunt_inds,model,opt, \
                                        menv_name,hwenv_name)
    new_fields['modif'] = datetime.datetime.now()
    assign_subclauses = []
    for field,value in new_fields.items():
      assert(field in self._experiment_modifiable)
      if field == 'modif' or field == 'status':
        subcmd = "%s=\"%s\"" % (field,value)
      else:
        subcmd = "%s=%s" % (field,value)
      assign_subclauses.append(subcmd)

    assign_clause = ",".join(assign_subclauses)
    conc_cmd = cmd.format(where_clause=where_clause, \
                          assign_clause=assign_clause)
    self._curs.execute(conc_cmd)
    self._conn.commit()


  def get_outputs(self,bmark,arco_inds,jaunt_inds,model,opt,menv_name,hwenv_name):
    cmd = '''
     SELECT *
     FROM outputs
     {where_clause};
    '''
    where_clause = self.to_where_clause(bmark,\
                                        arco_inds,jaunt_inds,
                                        model,opt, \
                                        menv_name,hwenv_name)
    for entry in self._get_output_rows(where_clause):
      yield entry

  def filter_experiments(self,filt):
    for entry in self.get_all():
      args = entry.columns
      skip = False
      for k,v in args.items():
        if k in filt and v != filt[k]:
          skip = True
      if skip:
        continue
      yield entry



  def delete(self,bmark=None,objfun=None):
    assert(not bmark is None or not objfun is None)
    if not bmark is None and not objfun is None:
      itertr= self.filter_experiments({'bmark':bmark,'opt':objfun})
    elif not objfun is None:
      itertr= self.filter_experiments({'opt':objfun})
    elif not bmark is None:
      itertr= self.filter_experiments({'bmark':bmark})
    else:
      raise Exception("???")

    for entry in itertr:
      entry.delete()
      yield entry

  def get_experiment(self,bmark,arco_inds,jaunt_inds,model,opt,menv_name,hwenv_name):
    where_clause = self.to_where_clause(bmark,\
                                        arco_inds,jaunt_inds,model,opt, \
                                        menv_name,hwenv_name)
    result = list(self._get_experiment_rows(where_clause))
    if len(result) == 0:
      return None
    elif len(result) == 1:
      return result[0]
    else:
      raise Exception("nonunique experiment")

  def delete_output(self,bmark,arco_inds,jaunt_inds, \
                    model,opt,menv_name,hwenv_name,output,trial):
    cmd = '''
    DELETE FROM outputs {where_clause};
    '''
    where_clause = self.to_where_clause(bmark,\
                                        arco_inds,jaunt_inds,
                                        model, \
                                        opt, \
                                        menv_name,hwenv_name,
                                        varname=output,
                                        trial=trial)
    conc_cmd = cmd.format(where_clause=where_clause)
    self._curs.execute(conc_cmd)
    self._conn.commit()


  def delete_experiment(self,bmark,arco_inds,jaunt_inds, \
                        model,opt,menv_name,hwenv_name):
    cmd = '''
    DELETE FROM experiments {where_clause};
    '''
    where_clause = self.to_where_clause(bmark,\
                                        arco_inds,jaunt_inds,
                                        model,opt, \
                                        menv_name,hwenv_name)
    conc_cmd = cmd.format(where_clause=where_clause)
    self._curs.execute(conc_cmd)
    self._conn.commit()




  def add_output(self,path_handler,bmark,arco_inds, \
                 jaunt_inds, model, opt,\
                 menv_name,hwenv_name,output,trial):
    cmd = '''
      INSERT INTO outputs (
         bmark,arco0,arco1,arco2,arco3,jaunt,
         model,opt,menv,hwenv,out_file,status,modif,varname,trial
      ) VALUES
      (
         "{bmark}",{arco0},{arco1},{arco2},{arco3},{jaunt},
         "{model}","{opt}","{menv}","{hwenv}",
         "{out_file}",
         "{status}",
         "{modif}",
         "{varname}",
         {trial}
      )
      '''
    args = make_args(bmark,arco_inds,jaunt_inds,model,opt, \
                     menv_name,hwenv_name)
    args['modif'] = datetime.datetime.now()
    args['status'] = OutputStatus.PENDING.value
    args['varname'] = output
    args['trial'] = trial
    args['out_file'] = path_handler.measured_waveform_file(bmark,arco_inds, \
                                                           jaunt_inds, \
                                                           model,
                                                           opt,menv_name, \
                                                           hwenv_name, \
                                                           output, \
                                                           trial)
    conc_cmd = cmd.format(**args)
    self._curs.execute(conc_cmd)
    self._conn.commit()

  def add_experiment(self,path_handler,bmark,arco_inds, \
                     jaunt_inds, \
                     model,opt, \
                     menv_name,hwenv_name):
    entry = self.get_experiment(bmark,arco_inds,jaunt_inds, \
                                model,opt,menv_name,hwenv_name)
    if entry is None:
      cmd = '''
      INSERT INTO experiments (
         bmark,arco0,arco1,arco2,arco3,jaunt,
         model,opt,menv,hwenv,
         jaunt_circ_file,
         grendel_file,status,modif,mismatch
      ) VALUES
      (
         "{bmark}",{arco0},{arco1},{arco2},{arco3},{jaunt},
         "{model}","{opt}","{menv}","{hwenv}",
         "{conc_circ}",
         "{grendel_file}",
         "{status}",
         "{modif}",{mismatch}
      )
      '''
      args = make_args(bmark,arco_inds,jaunt_inds,model,opt, \
                       menv_name,hwenv_name)
      args['modif'] = datetime.datetime.now()
      args['status'] = ExperimentStatus.PENDING.value
      args['grendel_file'] = path_handler.grendel_file(bmark,arco_inds, \
                                                       jaunt_inds,
                                                       model,
                                                       opt,
                                                       menv_name,
                                                       hwenv_name)
      args['conc_circ'] = path_handler.conc_circ_file(bmark,arco_inds, \
                                                      jaunt_inds, \
                                                      model,
                                                      opt)

      # not mismatched
      args['mismatch'] = 0
      conc_cmd = cmd.format(**args)
      self._curs.execute(conc_cmd)
      self._conn.commit()
      entry = self.get_experiment(bmark,arco_inds,jaunt_inds, \
                                  model,opt,menv_name,hwenv_name)
      for out_file in get_output_files(args['grendel_file']):
        _,_,_,_,_,_,_,var_name,trial = path_handler \
                               .measured_waveform_file_to_args(out_file)
        self.add_output(path_handler,bmark,arco_inds,jaunt_inds, \
                        model,opt, \
                        menv_name,hwenv_name,var_name,trial)

      entry.synchronize()
      return entry

  def scan(self):
    for name in diffeqs.get_names():
      ph = paths.PathHandler('standard',name,make_dirs=False)
      grendel_dir = ph.grendel_file_dir()
      for dirname, subdirlist, filelist in os.walk(grendel_dir):
        for fname in filelist:
          if fname.endswith('.grendel'):
            bmark,arco_inds,jaunt_inds,model,opt,menv_name,hwenv_name = \
                                    ph.grendel_file_to_args(fname)
            exp = self.add_experiment(ph,bmark,arco_inds,jaunt_inds, \
                                      model,opt,menv_name,hwenv_name)
            if not exp is None:
              yield exp
