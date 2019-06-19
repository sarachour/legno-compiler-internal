
import os
from enum import Enum

import util.config as config
import util.util as util

class PathHandler:
    def __init__(self,name,bmark,make_dirs=True):
        self.set_root_dir(name,bmark)
        for path in [
            self.ROOT_DIR,
            self.BMARK_DIR,
            self.ABS_CIRC_DIR,
            self.CONC_CIRC_DIR,
            self.CONC_GRAPH_DIR,
            self.ABS_GRAPH_DIR,
            self.REF_WAVEFORM_FILE_DIR,
            self.MEAS_WAVEFORM_FILE_DIR,
            self.GRENDEL_FILE_DIR,
            self.PLOT_DIR
        ]:
          if make_dirs:
              util.mkdir_if_dne(path)

        self._name = name
        self._bmark = bmark

    def set_root_dir(self,name,bmark):
        self.ROOT_DIR = "%s/legno/%s" % (config.OUTPUT_PATH,name)
        self.BMARK_DIR = self.ROOT_DIR + ("/%s" % bmark)
        self.ABS_CIRC_DIR = self.BMARK_DIR + "/abs-circ"
        self.ABS_GRAPH_DIR = self.BMARK_DIR + "/abs-graph"
        self.CONC_CIRC_DIR = self.BMARK_DIR + "/conc-circ"
        self.CONC_GRAPH_DIR = self.BMARK_DIR + "/conc-graph"
        self.GRENDEL_FILE_DIR = self.BMARK_DIR + "/grendel"
        self.PLOT_DIR = self.BMARK_DIR + "/plots"
        self.MEAS_WAVEFORM_FILE_DIR = self.BMARK_DIR + "/out-waveform"
        self.REF_WAVEFORM_FILE_DIR = self.BMARK_DIR + "/ref-waveform"


    def conc_circ_file(self,bmark,indices,scale_index,model,opt):
      index_str = "_".join(map(lambda ind : str(ind),indices))
      return self.CONC_CIRC_DIR+ "/%s_%s_s%s_%s_%s.circ" % \
        (self._bmark,index_str,scale_index,model,opt)


    def conc_graph_file(self,bmark,indices,scale_index,model,opt,tag="notag"):
      index_str = "_".join(map(lambda ind : str(ind),indices))
      return self.CONC_GRAPH_DIR+ "/%s_%s_s%s_%s_%s_%s.dot" % \
        (self._bmark,index_str,scale_index,model,opt,tag)


    def plot(self,bmark,indices,scale_index,model,opt, \
             menv_name,henv_name,tag):
      index_str = "_".join(map(lambda ind : str(ind),indices))
      return self.PLOT_DIR+ "/%s_%s_s%s_%s_%s_%s_%s_%s.png" % \
        (self._bmark,index_str,scale_index,model,opt, \
         menv_name,henv_name,\
         tag)


    def grendel_file(self,bmark,indices,scale_index,model,opt, \
                     menv_name,henv_name):
      index_str = "_".join(map(lambda ind : str(ind),indices))
      return self.GRENDEL_FILE_DIR+ "/%s_%s_s%s_%s_%s_%s_%s.grendel" % \
        (self._bmark,index_str,scale_index,model,opt,menv_name,henv_name)


    def reference_waveform_file(self,bmark,menv_name):
      return self.REF_WAVEFORM_FILE_DIR+ "/%s_%s.json" % \
        (self._bmark,menv_name)

    def measured_waveform_dir(self):
      return self.MEAS_WAVEFORM_FILE_DIR


    def measured_waveform_file(self,bmark,indices,scale_index, \
                               model,opt,\
                               menv_name,hwenv_name,variable,trial):
      index_str = "_".join(map(lambda ind : str(ind),indices))
      return self.MEAS_WAVEFORM_FILE_DIR+ "/%s_%s_s%s_%s_%s_%s_%s_%s_%d.json" % \
        (self._bmark,index_str,scale_index,model,opt, \
         menv_name,hwenv_name,variable,trial)


    def measured_waveform_files(self,bmark,indices,scale_index,\
                               menv_name,hwenv_name,variable):
      index_str = "_".join(map(lambda ind : str(ind),indices))
      prefix = "%s_%s_s%s_%s_%s_" % \
        (self._bmark,index_str,scale_index,menv_name,hwenv_name)

      raise Exception("TODO: this is not the correct prefix.")
      for dirname, subdirlist, filelist in \
          os.walk(self.MEAS_WAVEFORM_FILE_DIR):
        for fname in filelist:
          if fname.endswith('.json') and fname.startswith(prefix):
            yield "%s/%s" % (self.MEAS_WAVEFORM_FILE_DIR,fname)


    def measured_waveform_file_to_args(self,name):
      basename = name.split(".json")[0]
      args = basename.split("_")
      bmark = args[0]
      print(name)
      indices = list(map(lambda token: int(token), args[1:-7]))
      scale_index = int(args[-7].split('s')[1])
      model = args[-6]
      opt = args[-5]
      menv_name = args[-4]
      hwenv_name = args[-3]
      var_name = args[-2]
      trial = int(args[-1])

      return bmark,indices,scale_index,model,opt, \
          menv_name,hwenv_name,var_name,trial


    @staticmethod
    def grendel_file_to_args(name):
      basename = name.split(".grendel")[0]
      args = basename.split("_")
      bmark = args[0]
      indices = list(map(lambda token: int(token), args[1:-5]))
      scale_index = int(args[-5].split('s')[1])
      model = args[-4]
      opt = args[-3]
      menv_name = args[-2]
      hwenv_name = args[-1]
      return bmark,indices,scale_index,model,opt,menv_name,hwenv_name


    @staticmethod
    def conc_circ_to_args(name):
      basename = name.split(".circ")[0]
      args = basename.split("_")
      bmark = args[0]
      indices = list(map(lambda token: int(token), args[1:-3]))
      scale_index = int(args[-3].split('s')[1])
      model = args[-2]
      opt = args[-1]
      return bmark,indices,scale_index,model,opt


    @staticmethod
    def abs_circ_to_args(name):
      basename = name.split(".circ")[0]
      args = basename.split("_")
      bmark = args[0]
      indices = list(map(lambda token: int(token), args[1:]))
      return bmark,indices

    def abs_graph_file(self,indices):
        index_str = "_".join(map(lambda ind : str(ind),indices))
        return self.ABS_GRAPH_DIR+ "/%s_%s.dot" % \
          (self._bmark,index_str)


    def abs_circ_file(self,indices):
        index_str = "_".join(map(lambda ind : str(ind),indices))
        return self.ABS_CIRC_DIR+ "/%s_%s.circ" % \
          (self._bmark,index_str)

    def grendel_file_dir(self):
        return self.GRENDEL_FILE_DIR


    def skelt_circ_dir(self):
        return self.SKELT_CIRC_DIR


    def conc_circ_dir(self):
        return self.CONC_CIRC_DIR


    def abs_circ_dir(self):
        return self.ABS_CIRC_DIR

    def has_file(self,filepath):
        if not os.path.exists(filepath):
          return False

        directory,filename = os.path.split(filepath)
        return filename in os.listdir(directory)
