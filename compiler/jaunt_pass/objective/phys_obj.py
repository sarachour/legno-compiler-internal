import itertools
import ops.nop as nop
import util.util as util
import compiler.common.evaluator_heuristic as evalheur
import compiler.jaunt_pass.objective.obj as optlib
import compiler.jaunt_pass.objective.basic_obj as boptlib
import compiler.jaunt_pass.objective.sweep_obj as swoptlib
import math

class FastHeuristicObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return 'fast-heur'

  @staticmethod
  def make(circuit,jobj,varmap):
    jenv = jobj.jenv
    ports = evalheur.get_iface_ports(circuit,False,1.0)
    obj = 0
    for _,block_name,loc,port in ports:
      scf = jenv.get_scvar(block_name,loc,port)
      obj += varmap[jenv.tau()]/varmap[scf]

    obj *= varmap[jenv.tau()]**(-1)
    yield FastHeuristicObjFunc(obj)



class HeuristicObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return 'heur'

  @staticmethod
  def make(circuit,jobj,varmap):
    jenv = jobj.jenv
    ports = evalheur.get_iface_ports(circuit,False,1.0)
    obj = 0
    for _,block_name,loc,port in ports:
      scf = jenv.get_scvar(block_name,loc,port)
      obj += varmap[jenv.tau()]/varmap[scf]

    yield HeuristicObjFunc(obj)



class TauSweepSNRObjFunc(swoptlib.MultSpeedObjFunc):

  def __init__(self,obj,idx,cstrs):
    swoptlib.MultSpeedObjFunc.__init__(self,obj,idx,cstrs)

  def mktag(self,idx):
    return "lnz-tau%d" % idx


  @staticmethod
  def name():
    return "nz-sweep-tau"


  @staticmethod
  def mkobj(circ,jobj,varmap,idx,tau,cstrs):
    obj = list(LowNoiseObjFunc.make(circ,jobj,varmap))[0].objective()
    return TauSweepSNRObjFunc(obj,
                              idx=idx,
                              cstrs=cstrs)

  @staticmethod
  def make(circ,jobj,varmap,n=7):
    return swoptlib.MultSpeedObjFunc.make(
      TauSweepSNRObjFunc,circ, jobj,varmap,n=n)

