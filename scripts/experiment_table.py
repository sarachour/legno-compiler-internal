import scripts.common as common
import datetime
from scripts.experiment_entry import ExperimentEntry

class ExperimentTable:


  def __init__(self,db):
    self.db = db
    cmd = '''CREATE TABLE IF NOT EXISTS experiments
             (subset text NOT NULL,
              bmark text NOT NULL,
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
              quality real,
              energy real,
              runtime real,
              PRIMARY KEY (subset,bmark,arco0,arco1,
                           arco2,arco3,jaunt,
                           model,opt,menv,hwenv)
             );
    '''
    self._order = ['subset',
                   'bmark','status','modif','arco0', \
                   'arco1','arco2', \
                   'arco3','jaunt',
                   'model','opt','menv','hwenv',
                   'grendel_file', \
                   'jaunt_circ_file',
                   'quality', \
                   'energy', \
                   'runtime']

    self._modifiable =  \
                        ['status','modif','quality', \
                         'energy','runtime']
    self.db.curs.execute(cmd)

  def _get_rows(self,where_clause):
    cmd = '''SELECT * FROM experiments {where_clause}'''
    conc_cmd = cmd.format(where_clause=where_clause)
    for values in list(self.db.curs.execute(conc_cmd)):
      assert(len(values) == len(self._order))
      args = dict(zip(self._order,values))
      yield ExperimentEntry.from_db_row(self.db,args)

  def get_all(self):
    for entry in self._get_rows(""):
      yield entry


  def get_by_status(self,status):
    assert(isinstance(status,common.ExecutionStatus))
    where_clause = "WHERE status=\"%s\"" % status.value
    for entry in self._get_rows(where_clause):
      yield entry

  def get_by_bmark(self,bmark):
    where_clause = "WHERE bmark=\"%s\"" % bmark
    for entry in self._get_rows(where_clause):
      yield entry

  def to_where_clause(self,subset,bmark,arco_inds,jaunt_inds,model,opt, \
                      menv_name,hwenv_name):
    cmd = '''WHERE
      subset = "{subset}"
      AND bmark = "{bmark}"
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
    args = common.make_args(subset,bmark,arco_inds, \
                            jaunt_inds,model,opt, \
                     menv_name,hwenv_name)

    conc_cmd = cmd.format(**args)
    return conc_cmd

  def filter(self,filt):
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
      itertr= self.filter({'bmark':bmark,'opt':objfun})
    elif not objfun is None:
      itertr= self.filter({'opt':objfun})
    elif not bmark is None:
      itertr= self.filter({'bmark':bmark})
    else:
      raise Exception("???")

    for entry in itertr:
      entry.delete()
      yield entry



  def get(self,subset,bmark,arco_inds,jaunt_inds,model,opt,menv_name,hwenv_name):
    where_clause = self.to_where_clause(subset,bmark,\
                                        arco_inds,jaunt_inds,model,opt, \
                                        menv_name,hwenv_name)
    result = list(self._get_rows(where_clause))
    if len(result) == 0:
      return None
    elif len(result) == 1:
      return result[0]
    else:
      raise Exception("nonunique experiment")

  def delete(self,subset,bmark,arco_inds,jaunt_inds, \
                        model,opt,menv_name,hwenv_name):
    cmd = '''
    DELETE FROM experiments {where_clause};
    '''
    where_clause = self.to_where_clause(subset,bmark,\
                                        arco_inds,jaunt_inds,
                                        model,opt, \
                                        menv_name,hwenv_name)
    conc_cmd = cmd.format(where_clause=where_clause)
    self.db.curs.execute(conc_cmd)
    self.db.conn.commit()



  def add(self,path_handler,
          subset,bmark,arco_inds, \
          jaunt_inds, \
          model,opt, \
          menv_name,hwenv_name):
    entry = self.get(subset, \
                     bmark,arco_inds,jaunt_inds, \
                     model,opt,menv_name,hwenv_name)
    if entry is None:
      cmd = '''
      INSERT INTO experiments (
         subset,bmark,arco0,arco1,arco2,arco3,jaunt,
         model,opt,menv,hwenv,
         jaunt_circ_file,
         grendel_file,status,modif
      ) VALUES
      (
         "{subset}","{bmark}",{arco0},{arco1},{arco2},{arco3},{jaunt},
         "{model}","{opt}","{menv}","{hwenv}",
         "{conc_circ}",
         "{grendel_file}",
         "{status}",
         "{modif}"
      )
      '''
      args = common.make_args(subset,
                       bmark,arco_inds,jaunt_inds,model,opt, \
                       menv_name,hwenv_name)
      args['modif'] = datetime.datetime.now()
      args['status'] = common.ExecutionStatus.PENDING.value
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

      conc_cmd = cmd.format(**args)
      self.db.curs.execute(conc_cmd)
      self.db.conn.commit()
      entry = self.get(subset,bmark,arco_inds,jaunt_inds, \
                       model,opt,menv_name,hwenv_name)

    return entry



  def update(self,subset,bmark,arco_inds,jaunt_inds,model, \
             opt,menv_name,hwenv_name,new_fields):
    cmd = '''
    UPDATE experiments
    SET {assign_clause} {where_clause};
    '''
    where_clause = self.to_where_clause(subset,bmark,\
                                        arco_inds,jaunt_inds,model,opt, \
                                        menv_name,hwenv_name)
    new_fields['modif'] = datetime.datetime.now()
    assign_subclauses = []
    for field,value in new_fields.items():
      assert(field in self._modifiable)
      if field == 'modif' or field == 'status':
        subcmd = "%s=\"%s\"" % (field,value)
      else:
        subcmd = "%s=%s" % (field,value)
      assign_subclauses.append(subcmd)

    assign_clause = ",".join(assign_subclauses)
    conc_cmd = cmd.format(where_clause=where_clause, \
                          assign_clause=assign_clause)
    self.db.curs.execute(conc_cmd)
    if self.db.curs.rowcount == 0:
      raise Exception("Query Failed:\n%s" % conc_cmd)

    self.db.conn.commit()

