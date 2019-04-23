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
                 uint8_t rng,
                 uint8_t* buf)
  {
    uint8_t idx = 0;
    Fabric::Chip::Tile::Slice::Fanout * fanout = common::get_fanout(fab,port.idxloc);
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface* iface;
    switch(blk){
    case circ::block_type_t::FANOUT:
      iface = common::get_output_port(fab,blk,port);
      add_to_buf(buf,idx,circ::code_type_t::CODE_PMOS, fanout->getAnaIrefPmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_NMOS, fanout->getAnaIrefNmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_OFFSET, get_offset_code(iface,rng));
      finish_buf(buf,idx);
      break;

    case circ::block_type_t::MULT:
      // TODO: indicate if input or output.
      add_to_buf(buf,idx,circ::code_type_t::CODE_PMOS, fanout->getAnaIrefPmos());
      add_to_buf(buf,idx,circ::code_type_t::CODE_NMOS, fanout->getAnaIrefNmos());
      finish_buf(buf,idx);
      break;

    default:
      comm::error("get_offset_code: unexpected block");

    }

  }

}
