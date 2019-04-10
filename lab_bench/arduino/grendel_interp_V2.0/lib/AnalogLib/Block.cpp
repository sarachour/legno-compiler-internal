#include "include/Block.h"
#include "include/Logger.h"

namespace block {

  unsigned int port_to_index(PORT_NAME port){
    switch(port){
    case PORT_NAME::IN0:
    case PORT_NAME::OUT0:
      return 0;
    case PORT_NAME::OUT1:
    case PORT_NAME::IN1:
      return 1;
    case PORT_NAME::OUT2:
      return 2;
    default:
      logger::error("port_to_index: unknown");
    }
    logger::error("port_to_index: unknown");
    return 0;
  }
  bool digital_port(PORT_NAME port){
    switch(port){
    case PORT_NAME::COEFF:
    case PORT_NAME::IC:
      return true;
    default:
      return false;
    }
    return false;
  }
  bool output_port(PORT_NAME port){
    switch(port){
    case PORT_NAME::OUT0:
    case PORT_NAME::OUT1:
    case PORT_NAME::OUT2:
      return true;
    default:
      return false;
    }
    return false;
  }

  bool input_port(PORT_NAME port){
    switch(port){
    case PORT_NAME::IN0:
    case PORT_NAME::IN1:
      return true;
    default:
      return false;
    }
    return false;
  }
  void set_enable(block_t& blk, bool enable){
    switch(blk.type){
    case BLOCK_TYPE::MULT:
      mult::set_enable(blk,enable);
    default:
      logger::error("unimpl: set_enable");
    }
  }
  bool has_port(BLOCK_TYPE typ, PORT_NAME port){
    switch(typ){
    case BLOCK_TYPE::MULT:
      return mult::has_port(port);
    default:
      logger::error("unimpl: has_port");
    }
    return false;
  }

  block_t mkblock(BLOCK_TYPE type,
                  unsigned char chip,
                  unsigned char tile,
                  unsigned char slice,
                  unsigned char index
                  )
  {
    block_t blk;
    blk.iface = 0;
    blk.type = type;
    blk.place.chip = chip;
    blk.place.slice = slice;
    blk.place.tile = tile;
    blk.place.index = index;
    return blk;
  }


}



int to_range_code(BLOCK_TYPE blk, RANGE_TYPE t){

  if(blk == BLOCK_TYPE::FANOUT){
    switch(t){
    case RNG_LOW: return 0;
    case RNG_MED: return 0;
    case RNG_HIGH: return 1;
    }
  }
  else{
    switch(t){
    case RNG_LOW: return 1;
    case RNG_MED: return 0;
    case RNG_HIGH: return 2;
    }
  }
  logger::error("to_range_code: not handled");
  return 0;
}
