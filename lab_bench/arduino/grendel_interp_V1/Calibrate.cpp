#include "AnalogLib.h"
#include "Circuit.h"
#include "Common.h"
#include "Comm.h"

namespace calibrate {
  uint8_t get_offset_code(Fabric::Chip::Tile::Slice::FunctionUnit::Interface* iface,
                          uint8_t range){
    switch(range){
    case circ::HI_RANGE:
      return iface->hiOffsetCode;
    case circ::MED_RANGE:
      return iface->midOffsetCode;
    case circ::LOW_RANGE:
      return iface->loOffsetCode;
    }
    comm::error("get_offset_code: unexpected code");
  }

  void add_to_buf(uint8_t* buf, uint8_t& idx, circ::code_type_t key, uint8_t value){
    buf[idx] = key;
    buf[idx+1] = value;
    idx += 2;
  }
  void finish_buf(uint8_t* buf,uint8_t& idx){
    buf[idx] = circ::code_type_t::CODE_END;
  }

  void get_codes(Fabric* fab,
                 uint16_t blk,
                 circ::circ_loc_idx2_t port,
                 uint8_t port_type,
                 uint8_t rng,
                 uint8_t* buf)
  {
    uint8_t idx = 0;
    Fabric::Chip::Tile::Slice::Fanout * fanout;
    Fabric::Chip::Tile::Slice::Multiplier * mult;
    Fabric::Chip::Tile::Slice::ChipAdc * adc;
    Fabric::Chip::Tile::Slice::Dac * dac;
    Fabric::Chip::Tile::Slice::Integrator * integ;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface* iface;
    switch(port_type){
    case circ::port_type_t::PORT_INPUT:
      iface = common::get_input_port(fab,blk,port);
      break;
    case circ::port_type_t::PORT_OUTPUT:
      iface = common::get_output_port(fab,blk,port);
      break;
    }
    switch(blk){
    case circ::block_type_t::FANOUT:
      fanout = common::get_fanout(fab,port.idxloc);
      add_to_buf(buf,idx,circ::code_type_t::CODE_PMOS, fanout->getAnaIrefPmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_NMOS, fanout->getAnaIrefNmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_OFFSET, get_offset_code(iface,rng));
      finish_buf(buf,idx);
      break;

    case circ::block_type_t::MULT:
      // TODO: indicate if input or output.
      mult = common::get_mult(fab,port.idxloc);
      add_to_buf(buf,idx,circ::code_type_t::CODE_PMOS, mult->getAnaIrefPmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_NMOS, mult->getAnaIrefNmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_GAIN_OFFSET,
                 mult->getGainOffsetCode());
      add_to_buf(buf,idx,circ::code_type_t::CODE_OFFSET, get_offset_code(iface,rng));
      finish_buf(buf,idx);
      break;

    case circ::block_type_t::TILE_ADC:
      adc = common::get_slice(fab,port.idxloc.loc)->adc;
      add_to_buf(buf,idx,circ::code_type_t::CODE_PMOS, adc->getAnaIrefPmos1());
      add_to_buf(buf,idx,circ::code_type_t::CODE_PMOS2, adc->getAnaIrefPmos2());
      add_to_buf(buf,idx,circ::code_type_t::CODE_NMOS, adc->getAnaIrefNmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_COMP_LOWER, adc->getCalCompLower());
      add_to_buf(buf,idx,circ::code_type_t::CODE_COMP_LOWER_FS, adc->getCalCompLowerFS());
      add_to_buf(buf,idx,circ::code_type_t::CODE_COMP_UPPER, adc->getCalCompUpper());
      add_to_buf(buf,idx,circ::code_type_t::CODE_COMP_UPPER_FS, adc->getCalCompUpperFS());
      add_to_buf(buf,idx,circ::code_type_t::CODE_I2V_OFFSET, adc->getI2VOffset());
      add_to_buf(buf,idx,circ::code_type_t::CODE_OFFSET, get_offset_code(iface,rng));
      finish_buf(buf,idx);
      break;

    case circ::block_type_t::TILE_DAC:
      dac = common::get_slice(fab,port.idxloc.loc)->dac;
      add_to_buf(buf,idx,circ::code_type_t::CODE_NMOS, dac->getAnaIrefNmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_GAIN_OFFSET,
                 dac->getGainOffsetCode());
      add_to_buf(buf,idx,circ::code_type_t::CODE_OFFSET, get_offset_code(iface,rng));
      finish_buf(buf,idx);
      break;

    case circ::block_type_t::INTEG:
      integ = common::get_slice(fab,port.idxloc.loc)->integrator;
      add_to_buf(buf,idx,circ::code_type_t::CODE_PMOS, mult->getAnaIrefPmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_NMOS, mult->getAnaIrefNmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_OFFSET, get_offset_code(iface,rng));
      finish_buf(buf,idx);
      break;
    default:
      comm::error("get_offset_code: unexpected block");

    }

  }

}
