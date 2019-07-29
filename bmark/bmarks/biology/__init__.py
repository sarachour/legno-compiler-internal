import bmark.bmarks.biology.bont as bont
import bmark.bmarks.biology.epor as epor
import bmark.bmarks.biology.repri as repri
import bmark.bmarks.biology.compinh as compinh
import bmark.bmarks.biology.smmrxn as smmrxn
import bmark.bmarks.biology.gentoggle as gentoggle
import bmark.bmarks.biology.rxn as rxn

def get_benchmarks():
  return [
    bont.model(),
    epor.model(),
    repri.model(),
    compinh.model(),
    smmrxn.model(True),
    smmrxn.model(False),
    gentoggle.model(),
    rxn.model_bimolec(),
    rxn.model_dissoc(),
    rxn.model_dimer_mult(),
    #rxn.model_dimer_lut(),
    rxn.model_bidir()
  ]
