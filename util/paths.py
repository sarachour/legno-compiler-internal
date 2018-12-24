
import os
from enum import Enum

class PathHandler:
    def __init__(self,name,bmark):
        self.set_root_dir(name,bmark)
        for path in [
            self.ROOT_DIR,
            self.BMARK_DIR,
            self.ABS_CIRC_DIR,
            self.ABS_GRAPH_DIR
        ]:
          if not os.path.exists(path):
            os.makedirs(path)

        self._name = name
        self._bmark = bmark

    def set_root_dir(self,name,bmark):
        self.ROOT_DIR = "outputs/legno/%s" % name
        self.BMARK_DIR = self.ROOT_DIR + ("/%s" % bmark)
        self.ABS_CIRC_DIR = self.BMARK_DIR + "/abs-circ"
        self.ABS_GRAPH_DIR = self.BMARK_DIR + "/abs-graph"

    def abs_graph_file(self,indices):
        index_str = "_".join(map(lambda ind : str(ind),indices))
        return self.ABS_GRAPH_DIR+ "/%s_%s.dot" % \
          (self._bmark,index_str)


    def abs_circ_file(self,indices):
        index_str = "_".join(map(lambda ind : str(ind),indices))
        return self.ABS_CIRC_DIR+ "/%s_%s.circ" % \
          (self._bmark,index_str)

    def abs_circ_dir(self):
        return self.ABS_CIRC_DIR

    def has_file(self,filepath):
        return os.path.exists(filepath)
