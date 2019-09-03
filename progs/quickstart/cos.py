from dslang.dsprog import DSProg

def dsname():
  return "cos"

def dsprog():
  params = {
    'P0': 0.1,
    'V0' :0.0
  }
  prob = DSProg("cos")
  prob.decl_stvar("V","(-P)","{P0}",params)
  prob.decl_stvar("P","V","{V0}",params)
  prob.emit("P","Position")
  prob.interval("P",-1.0,1.0)
  prob.interval("V",-1.0,1.0)
  prob.check()
  return prob

def dssim():
  exp = DSSim('t20')
  exp.set_sim_time(20)
  return exp
