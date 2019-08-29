from enum import Enum

class ExecutionStatus(Enum):
  PENDING = "pending"
  RAN = "ran"
  ANALYZED = "analyzed"



def get_output_files(grendel_script):
  import lab_bench.lib.command as cmdparse
  import lab_bench.lib.expcmd.micro_getter as microget
  import lab_bench.lib.expcmd.osc as osc

  with open(grendel_script,'r') as fh:
    for line in fh:
      instr = cmdparse.parse(line)
      if isinstance(instr,osc.OscGetValuesCmd):
        yield instr.filename
      elif isinstance(instr,microget.MicroGetADCValuesCmd):
        yield instr.filename

def make_args(subset,bmark,arco_inds,jaunt_indx,model,opt,menv_name,hwenv_name):
  return  {
    'subset':subset,
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

def read_only_properties(*attrs):

    def class_rebuilder(cls):
        "The class decorator"

        class NewClass(cls):
            "This is the overwritten class"
            def __setattr__(self, name, value):
                if name not in attrs:
                    pass
                elif name not in self.__dict__:
                    pass
                else:
                    raise AttributeError("Can't modify {}".format(name))

                super().__setattr__(name, value)
        return NewClass
    return class_rebuilder
