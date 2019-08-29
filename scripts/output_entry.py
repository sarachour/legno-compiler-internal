from scripts.common import read_only_properties, ExecutionStatus
import json
import util.util as util

class OutputTransform:

  def __init__(self,varname):
    self.variable = varname
    self.handle = None
    self.time_constant = 1.0
    self.legno_time_scale = 1.0
    self.legno_ampl_scale = 1.0
    self.expd_time_scale = 1.0
    self.expd_time_offset = 0.0

  def to_json(self):
    return self.__dict__

  @staticmethod
  def from_json(varname,obj):
    xform = OutputTransform(varname)
    if not obj is None:
      print(obj)
      xform.__dict__ = obj
    return xform

  def __repr__(self):
    s = "{\n"
    for k,v in self.__dict__.items():
      s += " %s=%s\n" % (k,v)
    s += "}"
    return s

@read_only_properties('subset','arco_indices','jaunt_index', \
                      'objective_fun', 'model', 'math_env', \
                      'hw_env', 'out_file',  \
                      'trial','varname')
class OutputEntry:

  def __init__(self,db,status,modif,subset,bmark,
               arco_indices,
               jaunt_index,
               out_file,
               model,
               objective_fun,math_env,hw_env,
               varname,trial,transform,quality,runtime):
    self._db = db
    self.subset = subset
    self.bmark = bmark
    self.arco_indices = arco_indices
    self.jaunt_index = jaunt_index
    self.objective_fun = objective_fun
    self.model = model
    self.math_env = math_env
    self.hw_env = hw_env
    self.varname = varname
    self.trial = trial
    self.out_file = out_file

    self._modif =modif
    self._status = status
    self._quality =quality
    self._transform = transform
    self._runtime =runtime

  @staticmethod
  def from_db_row(db,args):
    if not args['transform'] is  None:
      args['transform'] = OutputTransform.from_json(args['varname'], \
                                          util \
                                          .decompress_json(args['transform']))
    entry = OutputEntry(
      db=db,
      status=ExecutionStatus(args['status']),
      modif=args['modif'],
      subset=args['subset'],
      bmark=args['bmark'],
      arco_indices=[args['arco0'],args['arco1'], \
                  args['arco2'], args['arco3']],
      out_file=args['out_file'],
      model=args['model'],
      objective_fun=args['opt'],
      jaunt_index=args['jaunt'],
      math_env=args['menv'],
      hw_env=args['hwenv'],
      varname=args['varname'],
      trial=args['trial'],
      quality=args['quality'],
      runtime=args['runtime'],
      transform=args['transform']
    )
    return entry

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
  def quality(self):
    return self._quality

  @quality.setter
  def quality(self,new_quality):
    self.update_db({'quality':new_quality})
    self._quality = new_quality

  @property
  def transform(self):
    if self._transform is None:
      obj = None
    else:
      obj = self._transform.__dict__

    xform = OutputTransform \
            .from_json(self.varname, \
                       obj)
    return xform

  @transform.setter
  def transform(self,new_xform):
    assert(isinstance(new_xform,OutputTransform))
    self.update_db({'transform':util.compress_json(new_xform.to_json())})
    self._transform = new_xform


  def delete(self):
     self._db.output_tbl.delete(self.subset,
                            self.bmark,
                            self.arco_indices,
                            self.jaunt_index,
                            self.model,
                            self.objective_fun,
                            self.math_env,
                            self.hw_env,
                            self.varname,
                            self.trial)

  def update_db(self,args):
    self._db.output_tbl.update(self.subset,
                               self.bmark,
                               self.arco_indices,
                               self.jaunt_index,
                               self.model,
                               self.objective_fun,
                               self.math_env,
                               self.hw_env,
                               self.varname,
                               self.trial,
                               args)




  @property
  def circ_ident(self):
    return "%s(%s,%s)" % (self.bmark,
                          self.arco_indices,
                          self.jaunt_index)
  @property
  def port_ident(self):
    return "%s.%s" % (self.circ_ident,self.varname)



  @property
  def ident(self):
    return "%s::%s[%s,%s](%s,%s)" % (self.subset, \
                                     self.port_ident, \
                                     self.objective_fun, \
                                     self.model, \
                                     self.math_env, \
                                     self.hw_env)

  def __repr__(self):
    s = "{\n"
    s += "ident=%s\n" % self.ident
    s += "status=%s\n" % (self._status.value)
    s += "varname=<%s>\n" % (self._varname)
    s += "trial=%d\n" % (self._trial)
    s += "out_file=%s\n" % (self._out_file)
    s += "rank=%s\n" % (self._rank)
    s += "tau=%s\n" % (self._tau)
    s += "scf=%s\n" % (self._scf)
    s += "fmax=%s\n" % (self._fmax)
    s += "quality=%s\n" % (self._quality)
    s += "transform=%s\n" % (self._transform)
    s += "}\n"
    return s

