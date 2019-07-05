#include "AnalogLib.h"
#include "Circuit.h"
#include "Common.h"
#include "Comm.h"
#include "fu.h"
#include "profile.h"

namespace calibrate {

  profile_t measure(Fabric* fab,
                         uint16_t blk,
                         circ::circ_loc_idx1_t loc,
                         uint8_t mode,
                         float in0,
                         float in1)
  {
    Fabric::Chip::Tile::Slice::Fanout * fanout;
    Fabric::Chip::Tile::Slice::Multiplier * mult;
    Fabric::Chip::Tile::Slice::ChipAdc * adc;
    Fabric::Chip::Tile::Slice::Dac * dac;
    Fabric::Chip::Tile::Slice::Integrator * integ;
    Fabric::Chip::Tile::Slice::LookupTable * lut;

    switch(blk){
    case circ::block_type_t::FANOUT:
      fanout = common::get_fanout(fab,loc);
      fanout->measure(mode,in0);
      break;

    case circ::block_type_t::MULT:
      // TODO: indicate if input or output.
      mult = common::get_mult(fab,loc);
      return mult->measure(in0,in1);
      break;

    case circ::block_type_t::TILE_ADC:
      adc = common::get_slice(fab,loc.loc)->adc;
      return adc->measure(in0);
      break;

    case circ::block_type_t::TILE_DAC:
      dac = common::get_slice(fab,loc.loc)->dac;
      return dac->measure(in0);
      break;

    case circ::block_type_t::INTEG:
      integ = common::get_slice(fab,loc.loc)->integrator;
      return integ->measure(mode,in0);
      break;

    case circ::block_type_t::LUT:
      break;
    default:
      comm::error("get_offset_code: unexpected block");
    }
  }


  bool calibrate(Fabric* fab,
                 profile_t& result,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc,
                 const float max_error,
                 bool targeted)
  {
    Fabric::Chip::Tile::Slice::Fanout * fanout;
    Fabric::Chip::Tile::Slice::Multiplier * mult;
    Fabric::Chip::Tile::Slice::ChipAdc * adc;
    Fabric::Chip::Tile::Slice::Dac * dac;
    Fabric::Chip::Tile::Slice::Integrator * integ;
    Fabric::Chip::Tile::Slice::LookupTable * lut;
    switch(blk){
    case circ::block_type_t::FANOUT:
      fanout = common::get_fanout(fab,loc);
      return fanout->calibrate(result,max_error);
      break;

    case circ::block_type_t::MULT:
      // TODO: indicate if input or output.
      mult = common::get_mult(fab,loc);
      if(mult->m_codes.vga and targeted){
        return mult->calibrateTarget(result,max_error);
      }
      else{
        return mult->calibrate(result,max_error);
      }
      break;

    case circ::block_type_t::TILE_ADC:
      adc = common::get_slice(fab,loc.loc)->adc;
      return adc->calibrate(result,max_error);
      break;

    case circ::block_type_t::TILE_DAC:
      dac = common::get_slice(fab,loc.loc)->dac;
      if(dac->m_codes.source == dac_source_t::DSRC_MEM and targeted){
        return dac->calibrateTarget(result,max_error);
      }
      else{
        return dac->calibrate(result,max_error);
      }
      break;

    case circ::block_type_t::LUT:
      lut = common::get_slice(fab,loc.loc)->lut;
      return true;

    case circ::block_type_t::INTEG:
      integ = common::get_slice(fab,loc.loc)->integrator;
      if(targeted){
        return integ->calibrateTarget(result,max_error);
      }
      else{
        return integ->calibrate(result,max_error);
      }
      break;

    default:
      comm::error("get_offset_code: unexpected block");

    }
    return false;
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
    Fabric::Chip::Tile::Slice::LookupTable * lut;

    switch(blk)
      {
      case circ::block_type_t::FANOUT:
        fanout = common::get_fanout(fab,loc);
        fanout->update(state.fanout);
        break;
      case circ::block_type_t::TILE_ADC:
        adc = common::get_slice(fab,loc.loc)->adc;
        adc->update(state.adc);
        break;

      case circ::block_type_t::TILE_DAC:
        dac = common::get_slice(fab,loc.loc)->dac;
        dac->update(state.dac);
        break;
      case circ::block_type_t::LUT:
        lut = common::get_slice(fab,loc.loc)->lut;
        lut->update(state.lut);
        break;

      case circ::block_type_t::MULT:
        mult = common::get_mult(fab,loc);
        mult->update(state.mult);
        break;
      case circ::block_type_t::INTEG:
        integ = common::get_slice(fab,loc.loc)->integrator;
        integ->update(state.integ);
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
    Fabric::Chip::Tile::Slice::LookupTable * lut;

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
      case circ::block_type_t::LUT:
        lut = common::get_slice(fab,loc.loc)->lut;
        state.lut = lut->m_codes;
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
