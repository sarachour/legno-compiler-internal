#include "AnalogLib.h"
#include "Circuit.h"
#include "Common.h"
#include "Comm.h"
#include "fu.h"

namespace calibrate {

  void characterize(Fabric* fab,
                 util::calib_result_t& result,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc)
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
      fanout->characterize(result);
      break;

    case circ::block_type_t::MULT:
      // TODO: indicate if input or output.
      mult = common::get_mult(fab,loc);
      mult->characterize(result);
      break;

    case circ::block_type_t::TILE_ADC:
      adc = common::get_slice(fab,loc.loc)->adc;
      break;

    case circ::block_type_t::TILE_DAC:
      dac = common::get_slice(fab,loc.loc)->dac;
      dac->characterize(result);
      break;

    case circ::block_type_t::INTEG:
      integ = common::get_slice(fab,loc.loc)->integrator;
      integ->characterize(result);
      break;

    case circ::block_type_t::LUT:
      break;
    default:
      comm::error("get_offset_code: unexpected block");
    }
  }


  bool calibrate(Fabric* fab,
                 util::calib_result_t& result,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc,
                 const float max_error)
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
      if(mult->m_codes.vga){
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
      if(dac->m_codes.source == dac_source_t::DSRC_MEM){
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
      integ->calibrate(result,max_error);
      return integ->calibrateTarget(result,max_error);
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
        comm::print_header();
        circ::print_state(blk,state);
        Serial.println();
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
