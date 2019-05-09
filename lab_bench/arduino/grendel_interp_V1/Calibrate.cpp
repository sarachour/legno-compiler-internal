#include "AnalogLib.h"
#include "Circuit.h"
#include "Common.h"
#include "Comm.h"

namespace calibrate {

  bool calibrate(Fabric* fab,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc)
  {
    Fabric::Chip::Tile::Slice::Fanout * fanout;
    Fabric::Chip::Tile::Slice::Multiplier * mult;
    Fabric::Chip::Tile::Slice::ChipAdc * adc;
    Fabric::Chip::Tile::Slice::Dac * dac;
    Fabric::Chip::Tile::Slice::Integrator * integ;

    switch(blk){
    case circ::block_type_t::FANOUT:
      fanout = common::get_fanout(fab,loc);
      fanout->calibrate();
      break;

    case circ::block_type_t::MULT:
      // TODO: indicate if input or output.
      mult = common::get_mult(fab,loc);
      if(mult->m_codes.vga){
        return mult->calibrateTarget();
      }
      else{
        return mult->calibrate();
      }
      break;

    case circ::block_type_t::TILE_ADC:
      adc = common::get_slice(fab,loc.loc)->adc;
      adc->calibrate();
      break;

    case circ::block_type_t::TILE_DAC:
      dac = common::get_slice(fab,loc.loc)->dac;
      if(dac->m_codes.source == dac_source_t::DSRC_MEM){
        return dac->calibrateTarget();
      }
      else{
        return dac->calibrate();
      }
      break;

    case circ::block_type_t::INTEG:
      integ = common::get_slice(fab,loc.loc)->integrator;
      integ->calibrate();
      integ->calibrateTarget();
      break;

    default:
      comm::error("get_offset_code: unexpected block");

    }

  }

  void set_codes(Fabric* fab,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc,
                 block_code_t& state)
  {
    Fabric::Chip::Tile::Slice::Fanout * fanout;
    Fabric::Chip::Tile::Slice::Multiplier * mult;
    Fabric::Chip::Tile::Slice::ChipAdc * adc;
    Fabric::Chip::Tile::Slice::Dac * dac;
    Fabric::Chip::Tile::Slice::Integrator * integ;

    switch(blk)
      {
      case circ::block_type_t::TILE_DAC:
        dac = common::get_slice(fab,loc.loc)->dac;
        dac->update(state.dac);
        break;
      default:
        comm::error("set_codes: unimplemented block");
      }
  }
  void get_codes(Fabric* fab,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc,
                 block_code_t& state)
  {
    uint8_t idx = 0;
    Fabric::Chip::Tile::Slice::Fanout * fanout;
    Fabric::Chip::Tile::Slice::Multiplier * mult;
    Fabric::Chip::Tile::Slice::ChipAdc * adc;
    Fabric::Chip::Tile::Slice::Dac * dac;
    Fabric::Chip::Tile::Slice::Integrator * integ;

    switch(blk)
      {
      case circ::block_type_t::FANOUT:
        fanout = common::get_fanout(fab,loc);
        state.fanout = fanout->m_codes;
        break;
      case circ::block_type_t::MULT:
        // TODO: indicate if input or output.
        mult = common::get_mult(fab,loc);
        state.mult = mult->m_codes;
        break;
      case circ::block_type_t::TILE_ADC:
        adc = common::get_slice(fab,loc.loc)->adc;
        state.adc = adc->m_codes;
        break;
      case circ::block_type_t::TILE_DAC:
        dac = common::get_slice(fab,loc.loc)->dac;
        state.dac = dac->m_codes;
        break;
      case circ::block_type_t::INTEG:
        integ = common::get_slice(fab,loc.loc)->integrator;
        state.integ = integ->m_codes;
        break;
      default:
        comm::error("get_offset_code: unexpected block");
      }
  }
}
