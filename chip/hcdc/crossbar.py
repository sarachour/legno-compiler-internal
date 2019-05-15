from chip.phys import PhysicalModel
from chip.block import Block,BlockType
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
from chip.hcdc.globals import CTX, GLProp
from chip.cont import *
import ops.op as ops
import ops.nop as nops
import chip.units as units

def black_box_model_tile(blk):
  phys = blk.physical("*","*","out")
  phys.set_to(PhysicalModel.read(util.datapath('tile_xbar.bb')))

def black_box_model_chip(blk):
  phys = blk.physical("*","*","out")
  phys.set_to(PhysicalModel.read(util.datapath('global_xbar.bb')))


def black_box_model_cc(blk):
  black_box_model_tile(blk)


def xbar_continuous_model(xbar):
  csm = ContinuousScaleModel()
  csm.set_baseline("*")
  out = csm.decl_var(CSMOpVar("out"))
  inp = csm.decl_var(CSMOpVar("in"))
  coeff = csm.decl_var(CSMCoeffVar("out"))
  csm.eq(ops.Mult(ops.Var(inp.varname),
                  ops.Var(coeff.varname)), \
         ops.Var(out.varname))
  csm.discrete.add_mode("*")
  csm.discrete.add_cstr("*",out,1.0)
  csm.discrete.add_cstr("*",inp,1.0)
  xbar.set_scale_model("*", csm)

ana_props = util.make_ana_props(chipcmd.RangeType.HIGH,\
                                CTX.get(GLProp.CURRENT_INTERVAL,
                                        'tile_out', \
                                        "*","*",None))

tile_out = Block('tile_out',type=BlockType.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["out","in"], ana_props) \
.set_coeff("*","*","out",1.0) \
.check()
black_box_model_tile(tile_out)
xbar_continuous_model(tile_out)

ana_props = util.make_ana_props(chipcmd.RangeType.HIGH,\
                                CTX.get(GLProp.CURRENT_INTERVAL,
                                        'tile_in', \
                                        "*","*",None))

tile_in = Block('tile_in',type=BlockType.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["out","in"], ana_props) \
.set_coeff("*","*","out",1.0) \
.check()
black_box_model_tile(tile_in)
xbar_continuous_model(tile_in)


ana_props = util.make_ana_props(chipcmd.RangeType.HIGH,\
                                CTX.get(GLProp.CURRENT_INTERVAL,
                                        'conn_inv', \
                                        "*","*",None))

inv_conn = Block('conn_inv') \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["out","in"], \
           ana_props) \
.set_coeff("*","*","out",-1.0) \
.check()
black_box_model_cc(inv_conn)
xbar_continuous_model(inv_conn)


ana_props = util.make_ana_props(chipcmd.RangeType.HIGH,\
                                CTX.get(GLProp.CURRENT_INTERVAL,
                                        'chip_out', \
                                        "*","*",None))

chip_out = Block('chip_out',type=BlockType.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["out"], ana_props) \
.set_props("*","*",["in"], ana_props) \
.set_coeff("*","*","out",1.0) \
.check()
black_box_model_chip(chip_out)
xbar_continuous_model(chip_out)

ana_props = util.make_ana_props(chipcmd.RangeType.HIGH,\
                                CTX.get(GLProp.CURRENT_INTERVAL,
                                        'chip_in', \
                                        "*","*",None))

chip_in = Block('chip_in',type=BlockType.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["in"], ana_props) \
.set_props("*","*",["out"], ana_props) \
.set_coeff("*","*","out",1.0) \
.check()
black_box_model_chip(chip_in)
xbar_continuous_model(chip_in)
