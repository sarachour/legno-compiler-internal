from chip.phys import PhysicalModel
from chip.block import Block
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chip_command as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import ops.nop as nops
import chip.units as units

def black_box_model_tile(blk):
  print("[TODO] crossbar[tile].blackbox")
  phys = blk.physical("*","*","out")
  phys.set_to(PhysicalModel.read(util.datapath('tile_xbar.bb')))

def black_box_model_chip(blk):
  print("[TODO] crossbar[tile].blackbox")
  phys = blk.physical("*","*","out")
  phys.set_to(PhysicalModel.read(util.datapath('global_xbar.bb')))


def black_box_model_cc(blk):
  black_box_model_tile(blk)



tile_out = Block('tile_out',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out","in"], \
          util.make_ana_props(chipcmd.RangeType.HIGH,\
                         glb.ANALOG_MIN,
                         glb.ANALOG_MAX)) \
.set_scale_factor("*","*","out",1.0) \
.check()
black_box_model_tile(tile_out)

tile_in = Block('tile_in',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out","in"], \
          util.make_ana_props(chipcmd.RangeType.HIGH,\
                         glb.ANALOG_MIN,
                         glb.ANALOG_MAX)) \
.set_scale_factor("*","*","out",1.0) \
.check()
black_box_model_tile(tile_in)


inv_conn = Block('conn_inv',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out","in"], \
          util.make_ana_props(chipcmd.RangeType.HIGH,\
                         glb.ANALOG_MIN,
                         glb.ANALOG_MAX)) \
.set_scale_factor("*","*","out",-1.0) \
.check()
black_box_model_cc(inv_conn)


chip_out = Block('chip_out',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out"], \
          util.make_ana_props(chipcmd.RangeType.HIGH,\
                         glb.ANALOG_MIN,
                         glb.ANALOG_MAX)) \
.set_info("*","*",["in"], \
          util.make_ana_props(chipcmd.RangeType.HIGH,\
                         glb.ANALOG_MIN,
                         glb.ANALOG_MAX)) \
.set_scale_factor("*","*","out",1.0) \
.check()
black_box_model_chip(chip_out)

chip_in = Block('chip_in',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["in"], \
          util.make_ana_props(chipcmd.RangeType.MED,\
                         glb.ANALOG_MIN,
                         glb.ANALOG_MAX)) \
.set_info("*","*",["out"], \
          util.make_ana_props(chipcmd.RangeType.MED,\
                         glb.ANALOG_MIN,
                         glb.ANALOG_MAX)) \
.set_scale_factor("*","*","out",1.0) \
.check()
black_box_model_chip(chip_in)
