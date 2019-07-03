from chip.model import ModelDB
import chip.model as model
import chip.props as proplib
import ops.op as oplib
from scipy.integrate import ode
import ops.interval as intervallib


def get_params(db,conc_circ, \
               block_name,loc,port, \
               handle=None, \
               mode='naive'):
  block = conc_circ.board.block(block_name)
  config = conc_circ.config(block_name,loc)

  coeff = block.coeff(config.comp_mode, \
                      config.scale_mode, \
                      port, handle)
  oprange = None
  sample_rate = None
  quantize = None
  if block.has_prop(config.comp_mode, \
                    config.scale_mode, \
                    port,handle):
    prop = block.props(config.comp_mode, \
                      config.scale_mode, \
                      port,handle)
    oprange = prop.interval()
    if isinstance(prop,proplib.DigitalProperties):
      quantize = prop.values()
      sample_rate = prop.sample_rate


  gain = model.get_gain(db,conc_circ, \
                        block_name, \
                        loc, port, \
                        handle, \
                        mode=mode)
  opsc_l,opsc_u = model.get_oprange_scale(db, \
                                          conc_circ, \
                                          block_name, \
                                          loc, port, \
                                          handle, \
                                          mode=mode)
  unc = model.get_variance(db, \
                           conc_circ, \
                           block_name, \
                           loc, port, \
                           handle=handle,
                           mode=mode)

  if not oprange is None:
    lb = opsc_l*oprange.lower
    ub = opsc_u*oprange.upper
    ival = intervallib.Interval(lb,ub)
  else:
    ival = None
  return {
    'interval': ival,
    'gain':coeff*gain,
    'unc':unc
  }

def build_output(db,conc_circ,block_name,loc,port,expr,
                 mode='naive'):
  def phys_expr(expr,handle):
    pars = get_params(db,conc_circ,block_name,loc,port,\
                      handle=handle,
                      mode=mode)
    e = oplib.Mult(oplib.Const(pars['gain']),expr)
    if not pars['interval'] is None:
      e = oplib.Clamp(e,pars['interval'])
    #e = oplib.Add(e,
    #              oplib.RandomVar(pars['unc']))
    return e

  if block_name == "integrator":
    assert(isinstance(expr,oplib.Integ))

    init_cond = phys_expr(expr.init_cond, \
                          expr.ic_handle)
    deriv = phys_expr(expr.deriv, \
                      expr.deriv_handle)

    return init_cond,deriv

  else:
    return phys_expr(expr, None)

def build_input(db,conc_circ,block_name,loc,port,expr,
                 mode='naive'):
  pars = get_params(db,conc_circ,block_name,loc,port,\
                    handle=None,
                    mode=mode)
  e2 = oplib.Clamp(expr,pars['interval'])
  return e2

def build_expr(db,conc_circ, \
               block_name,loc,port, \
               mode='naive',
               stvars=[],
               depth=0):
  block = conc_circ.board.block(block_name)
  config = conc_circ.config(block_name,loc)

  if (block_name,loc,port) in stvars and \
     depth > 0:
    lbl = config.label(port)
    print("stub %s[%s].%s -> %s" % (block_name,loc,port,lbl))
    return oplib.Var(lbl)

  if port in block.outputs:
    expr = block.get_dynamics(config.comp_mode, port)
    in_exprs = {}
    for v in expr.vars():
      in_e = build_expr(db,conc_circ, \
                        block_name,loc,v, \
                        mode=mode,
                        stvars=stvars,
                        depth=depth+1)
      in_exprs[v] = in_e

    out_expr = expr.substitute(in_exprs)
    print("out %s[%s].%s -> %s" % \
      (block_name,loc,port,out_expr))
    return build_output(db,conc_circ, \
                        block_name,loc,v, \
                        out_expr, \
                        mode=mode)

  elif port in block.inputs:
    inputs = []
    if config.has_dac(port):
      dac_val = config.dac(port)
      scf = config.scf(port)
      inputs.append(oplib.Const(dac_val*scf))

    for sblk,sloc,sport in \
        conc_circ.get_conns_by_dest(block_name,loc,port):
      src_expr= build_expr(db,conc_circ, \
                           sblk,sloc,sport,
                           mode=mode,
                           stvars=stvars,
                           depth=depth+1)
      inputs.append(src_expr)

    print(inputs)
    in_expr = oplib.mkadd(inputs)
    print("in %s[%s].%s val=%s" % \
      (block_name,loc,port,in_expr))
    return build_input(db,conc_circ, \
                       block_name,loc,port, \
                       in_expr, \
                       mode=mode)

def build_diffeqs(conc_circ):
  db = ModelDB()
  stvars = []
  for loc,_ in  \
      conc_circ.instances_of_block("integrator"):
    stvars.append(('integrator',loc,'out'))


  initials = {}
  var_initials = {}
  derivs = {}
  var_derivs = {}
  for block,loc,port in stvars:
    init_cond,deriv = build_expr(db,conc_circ, \
                                 block,loc,port, \
                                 stvars=stvars)
    config = conc_circ.config(block,loc)
    label = config.label(port)
    assert(not label in initials)
    var_initials[label],initials[label]  \
      = oplib.to_python(init_cond)
    var_derivs[label],derivs[label] \
      = oplib.to_python(deriv)

  return initials,derivs

def build_simulation(board,conc_circ):
  init_conds,derivs = build_diffeqs(conc_circ)
  return init_conds,derivs
