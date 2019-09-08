from dslang.dsprog import DSProgDB
import importlib.util
import os

def dynamic_load(filepath):
  spec = importlib.util.spec_from_file_location("module.name",
                                                filepath)
  module = importlib.util.module_from_spec(spec)
  obj = spec.loader.exec_module(module)
  if module.dssim != None and \
     module.dsprog != None and \
     module.dsname != None:
    DSProgDB.register(module.dsname(), \
                            module.dsprog, \
                            module.dssim)

root_dir = os.path.dirname(os.path.abspath(__file__))
for root, dirs, files in os.walk(root_dir):
   for filename in files:
     if filename.endswith(".py") and \
        filename != "__init__.py":
       dynamic_load("%s/%s" % (root,filename))

