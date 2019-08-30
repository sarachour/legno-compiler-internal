from bmark.bmarks.biology import \
        bont,epor,repri,compinh, \
        smmrxn,gentoggle,rxn

def get_benchmarks():
  return [
    bont.model(),
    epor.model(),
    repri.model(),
    repri.model(closed_form=False),
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
