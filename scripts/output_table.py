import scripts.common as common
import datetime
from scripts.output_entry import OutputEntry

class OutputTable:

  def __init__(self,db):
    self.db = db
    cmd = '''CREATE TABLE IF NOT EXISTS outputs(
    subset text NOT NULL,
    bmark text NULL,
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
    variable text NOT NULL,
    trial int NOT NULL,
    out_file text,
    runtime real,
    quality real,
    transform text,
    modif timestamp,
    PRIMARY KEY (subset,bmark,arco0,arco1,arco2,arco3,jaunt,
                 model,opt,menv,hwenv,variable,trial)
    FOREIGN KEY (subset,bmark,arco0,arco1,arco2,arco3,jaunt,
                 model,opt,menv,hwenv)
    REFERENCES experiments(subset,bmark,arco0,arco1,arco2,arco3,jaunt,
                           model,opt,menv,hwenv)
    )
    '''
    self._order = ['subset',
                   'bmark','status','arco0', \
                   'arco1','arco2', \
                   'arco3','jaunt','model','opt','menv','hwenv',
                   'varname','trial','out_file', \
                   'runtime','quality','transform','modif']

    self._modifiable = ['runtime','quality','modif', \
                        'status','transform']
    self.db.curs.execute(cmd)
    self.db.conn.commit()


  def to_where_clause(self,subset,bmark,arco_inds,jaunt_inds,model,opt, \
                      menv_name,hwenv_name,varname,trial):
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
    if not varname is None and not trial is None:
      cmd += '''
      AND variable = "{varname}"
      AND trial = {trial}
      '''

    args = common.make_args(subset,bmark,arco_inds,jaunt_inds,model,opt, \
                     menv_name,hwenv_name)
    args['varname'] = varname
    args['trial'] = trial
    conc_cmd = cmd.format(**args)
    return conc_cmd

  def _get_rows(self,where_clause):
    cmd = '''SELECT * FROM outputs {where_clause}'''
    conc_cmd = cmd.format(where_clause=where_clause)
    for values in list(self.db.curs.execute(conc_cmd)):
      assert(len(values) == len(self._order))
      args = dict(zip(self._order,values))
      yield OutputEntry.from_db_row(self.db,args)


  def update(self,subset,bmark,arco_inds,jaunt_inds,model,opt, \
                    menv_name,hwenv_name,varname,trial,new_fields):
    cmd = '''
    UPDATE outputs
    SET {assign_clause} {where_clause};
    '''
    where_clause = self.to_where_clause(subset,
                                        bmark,\
                                        arco_inds,jaunt_inds,
                                        model,
                                        opt, \
                                        menv_name,hwenv_name,
                                        varname=varname,
                                        trial=trial)
    new_fields['modif'] = datetime.datetime.now()
    assign_subclauses = []
    for field,value in new_fields.items():
      assert(field in self._modifiable)
      if field == 'modif' or field == 'status' or field == 'transform':
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

  def get(self,subset,bmark,arco_inds,jaunt_inds,model,opt,menv_name,hwenv_name):
    cmd = '''
     SELECT *
     FROM outputs
     {where_clause};
    '''
    where_clause = self.to_where_clause(subset,bmark,\
                                        arco_inds,jaunt_inds,
                                        model,opt, \
                                        menv_name,hwenv_name,
                                        varname=None,
                                        trial=None)
    for entry in self._get_rows(where_clause):
      yield entry
      yield entry

  def delete(self,subset,bmark,arco_inds,jaunt_inds, \
             model,opt,menv_name,hwenv_name,output,trial):
    cmd = '''
    DELETE FROM outputs {where_clause};
    '''
    where_clause = self.to_where_clause(subset,bmark,\
                                        arco_inds,jaunt_inds,
                                        model, \
                                        opt, \
                                        menv_name,hwenv_name,
                                        varname=output,
                                        trial=trial)
    conc_cmd = cmd.format(where_clause=where_clause)
    self.db.curs.execute(conc_cmd)
    self.db.conn.commit()


  def add(self,path_handler, \
          subset,bmark,arco_inds, \
          jaunt_inds, model, opt,\
          menv_name,hwenv_name,output,trial):
    cmd = '''
      INSERT INTO outputs (
         subset,bmark,arco0,arco1,arco2,arco3,jaunt,
         model,opt,menv,hwenv,out_file,status,modif,variable,trial
      ) VALUES
      (
         "{subset}",
         "{bmark}",{arco0},{arco1},{arco2},{arco3},{jaunt},
         "{model}","{opt}","{menv}","{hwenv}",
         "{out_file}",
         "{status}",
         "{modif}",
         "{varname}",
         {trial}
      )
      '''
    args = common.make_args(subset,bmark,arco_inds,jaunt_inds,model,opt, \
                     menv_name,hwenv_name)
    args['modif'] = datetime.datetime.now()
    args['status'] = common.ExecutionStatus.PENDING.value
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
    self.db.curs.execute(conc_cmd)
    if self.db.curs.rowcount == 0:
      raise Exception("Query Failed:\n%s" % conc_cmd)

    self.db.conn.commit()

