from scripts.common import read_only_properties, ExecutionStatus
import os

@read_only_properties('bmark', 'subset', 'arco_indices','jaunt_index', \
                      'objective_fun','model','math_env','hw_env','grendel_file',\
                      'jaunt_circ_file')
class ExperimentEntry:

  def __init__(self,db,status,modif,subset,bmark, \
               arco_indices,jaunt_index, \
               grendel_file,
               jaunt_circ_file, \
               model,objective_fun, \
               math_env,hw_env, \
               energy,runtime,quality):
    self.bmark = bmark
    self.subset = subset
    self.arco_indices = arco_indices
    self.jaunt_index = jaunt_index
    self.objective_fun = objective_fun
    self.model = model
    self.math_env = math_env
    self.hw_env = hw_env
    self.grendel_file = grendel_file
    self.jaunt_circ_file = jaunt_circ_file

    self._status = status
    self._modif = modif
    self._energy= energy
    self._runtime= runtime
    self._quality= quality
    self._db = db

  @property
  def modif(self):
    return self._modif

  @modif.setter
  def modif(self,new_modif):
    assert(isinstance(new_modif,ExecutionStatus))
    self.update_db({'modif':new_status.value})
    self._modif = new_status

  @property
  def status(self):
    return self._status

  @status.setter
  def status(self,new_status):
    assert(isinstance(new_status,ExecutionStatus))
    self.update_db({'status':new_status.value})
    self._status = new_status

  @property
  def runtime(self):
    return self._runtime

  @runtime.setter
  def runtime(self,new_runtime):
    assert(new_runtime >= 0)
    self.update_db({'runtime':new_runtime})
    self._runtime = new_runtime

  @property
  def energy(self):
    return self._energy

  @energy.setter
  def energy(self,new_energy):
    self.update_db({'energy':new_energy})
    self._energy = new_energy


  @property
  def quality(self):
    return self._quality

  @quality.setter
  def quality(self,new_quality):
    self.update_db({'quality':new_quality})
    self._quality = new_quality



  def outputs(self):
    for outp in self._db.output_tbl.get(self.subset,
                                          self.bmark, \
                                          self.arco_indices, \
                                          self.jaunt_index, \
                                          self.model, \
                                          self.objective_fun, \
                                          self.math_env, \
                                          self.hw_env):
      yield outp

  def synchronize(self):
    # delete if we're missing relevent files
    if not os.path.isfile(self.grendel_file) or \
       not os.path.isfile(self.jaunt_circ_file):
      self.delete()
      return

    clear_computed = False
    not_done = False
    for output in self.outputs():
      if os.path.isfile(output.out_file):
        if output.status == ExecutionStatus.PENDING:
          output.status = ExecutionStatus.RAN
      else:
        if output.status == ExecutionStatus.RAN:
          output.status = ExecutionStatus.PENDING

      not_done = not_done or \
                 (output.status == ExecutionStatus.PENDING)

    if not not_done:
      self.status = ExecutionStatus.RAN
    else:
      self.status = ExecutionStatus.PENDING

  def update_db(self,args):
    self._db.experiment_tbl.update(self.subset,
                    self.bmark,
                    self.arco_indices,
                    self.jaunt_index,
                    self.model,
                    self.objective_fun,
                    self.math_env,
                    self.hw_env,
                    args)

  def set_status(self,new_status):
    assert(isinstance(new_status,ExecutionStatus))
    self.update_db({'status':new_status.value})
    self._status = new_status

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

    self._db.experiment_table.delete(self.subset,
                               self.bmark,
                               self.arco_indices,
                               self.jaunt_index,
                               self.model,
                               self.objective_fun,
                               self.math_env,
                               self.hw_env)

  def get_outputs(self):
    return self._db.output_table.get(self.subset,
                                self.bmark, \
                                self.arco_indices,
                                self.jaunt_index,
                                self.model,
                                self.objective_fun,
                                self.math_env, \
                                self.hw_env)

  @staticmethod
  def from_db_row(db,args):
    entry = ExperimentEntry(
      db=db,
      status=ExecutionStatus(args['status']),
      modif=args['modif'],
      subset=args['subset'],
      bmark=args['bmark'],
      arco_indices=[args['arco0'],args['arco1'], \
                  args['arco2'], args['arco3']],
      model=args['model'],
      grendel_file=args['grendel_file'],
      jaunt_circ_file=args['jaunt_circ_file'],
      objective_fun=args['opt'],
      jaunt_index=args['jaunt'],
      math_env=args['menv'],
      hw_env=args['hwenv'],
      energy=args['energy'],
      runtime=args['runtime'],
      quality=args['quality'],
    )
    return entry

  @property
  def circ_ident(self):
    return "%s::%s(%s,%s)" % (self.subset,
                          self.bmark,
                          self.arco_indices,
                          self.jaunt_index)

  @property
  def ident(self):
    return "%s[%s,%s](%s,%s)" % (self.circ_ident, \
                                 self.objective_fun, \
                                 self.model, \
                                 self.math_env, \
                                 self.hw_env)

  def __repr__(self):
    s = "{\n"
    s += "bmark=%s\n" % (self.bmark)
    s += "ident=%s\n" % (self.ident)
    s += "status=%s\n" % (self.status.value)
    s += "grendel_file=%s\n" % (self.grendel_file)
    s += "jaunt_circ=%s\n" % (self.jaunt_circ_file)
    s += "energy=%s\n" % (self.energy)
    s += "runtime=%s\n" % (self.runtime)
    s += "quality=%s\n" % (self.quality)
    s += "}\n"
    return s

