import util.config as CONFIG
import sqlite3
from scripts.experiment_table import ExperimentTable
from scripts.output_table import OutputTable
from scripts.common import get_output_files
import util.paths as paths
import os

class ExpDriverDB:


  def __init__(self):
    path = CONFIG.EXPERIMENT_DB
    self.conn = sqlite3.connect(path)
    self.curs = self.conn.cursor()
    self.experiment_tbl = ExperimentTable(self)
    self.output_tbl = OutputTable(self)


  def close(self):
    self.conn.close()


  def add(self,path_handler,subset,bmark,arco_inds, \
          jaunt_inds, \
          model,opt, \
          menv_name,hwenv_name):
    entry=  self.experiment_tbl.add(path_handler, \
                                    subset,bmark,arco_inds, \
                                    jaunt_inds, \
                                    model,opt, \
                                    menv_name,hwenv_name)

    print(entry)
    for out_file in get_output_files(entry.grendel_file):
      _,_,_,_,_,_,_,var_name,trial = path_handler \
                               .measured_waveform_file_to_args(out_file)
      self.output_tbl.add(path_handler, \
                          subset,bmark,arco_inds,jaunt_inds, \
                          model,opt, \
                          menv_name,hwenv_name,var_name,trial)

    entry.synchronize()

  def scan(self):
    for dirname, subdirlist, filelist in os.walk(CONFIG.OUTPUT_PATH):
      for fname in filelist:
        if fname.endswith('.grendel'):
          subset,bmark = paths.PathHandler.path_to_args(dirname)
          ph = paths.PathHandler(subset,bmark,make_dirs=False)
          args= \
                ph.grendel_file_to_args(fname)
          bmark,arco_inds,jaunt_inds,model,opt,menv_name,hwenv_name = args
          exp = self.add(ph,subset,bmark,arco_inds,jaunt_inds, \
                         model,opt,menv_name,hwenv_name)
          if not exp is None:
            yield exp
