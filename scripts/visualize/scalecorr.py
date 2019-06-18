import scripts.visualize.common as common
from scripts.db import MismatchStatus

from chip.conc import ConcCirc
from chip.hcdc.hcdcv2_4 import make_board
import bmark.diffeqs as diffeqs
import compiler.jaunt as jaunt
import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jenv as jenvlib

import numpy as np
import matplotlib.pyplot as plt

board = make_board("standard")

def compute_varset(circ,bmark):
  prog = diffeqs.get_prog(bmark)
  jenv = jaunt.sc_build_jaunt_env(prog,circ)
  varmap = {}
  for idx,v in enumerate(jenv.variables(in_use=True)):
    typ,args = jenv.get_jaunt_var_info(v)
    if typ == jenvlib.JauntVarType.SCALE_VAR or \
        typ == jenvlib.JauntVarType.INJECT_VAR:
      blk,loc,port,handle = args
      varmap[idx] = (typ,(blk,loc,port))

    elif typ == jenvlib.JauntVarType.TAU:
      varmap[idx] = (typ,())

  return varmap

def to_label(varset,i):
  tag,info = varset[i]
  if tag == jenvlib.JauntVarType.TAU:
    label = "tau"
  else:
    blk,loc,port = info
    label = "%s[%s].%s" % (blk,loc,port)

  return label

def visualize():
  data = common.get_data(series_type='bmark')

  fields = ['jaunt_circ_file', 'circ_ident', 'quality']
  mismatches = [MismatchStatus.UNKNOWN, \
                MismatchStatus.IDEAL]
  for series in data.series():
    skelt_circs,circ_idents,quality = data.get_data(series, \
                                        fields,
                                        mismatches)

    varset = None
    Ys = []
    for circ_file,quality in zip(skelt_circs,quality):
      circ = ConcCirc.read(board,circ_file)
      if varset is None:
        varset = compute_varset(circ,series)
        Xs = list(map(lambda _: [], range(0,len(varset))))

      values = [0]*len(varset.keys())
      for idx,(tag,info) in varset.items():
        if tag == jenvlib.JauntVarType.TAU:
          scf = circ.tau
        elif tag == jenvlib.JauntVarType.SCALE_VAR:
          blk,loc,port = info
          scf = circ.config(blk,loc).scf(port)
        elif tag == jenvlib.JauntVarType.INJECT_VAR:
          blk,loc,port = info
          scf = circ.config(blk,loc).inject_var(port)

        Xs[idx].append(scf)

      Ys.append(quality)

    print("=== %s [%d] ===" % (series,len(varset)))
    for i in range(0,len(varset)):
      for j in range(0,len(varset)):
        X = list(map(lambda k: Xs[i][k]*Xs[j][k], range(0,len(circ_idents))))
        corr = np.corrcoef(X,Ys)
        correl = corr[0][1]
        xcorr = np.corrcoef(Xs[i],Xs[j])
        if abs(correl) > 0.65 and abs(xcorr[0][1]) < 0.33:
          print("%s,%s = %s" % (to_label(varset,i), \
                                to_label(varset,j), \
                                correl))


    print("=========\n\n")
