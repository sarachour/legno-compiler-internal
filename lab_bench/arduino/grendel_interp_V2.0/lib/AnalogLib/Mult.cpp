#include "include/Block.h"
#include "include/Util.h"
#include "include/Logger.h"

namespace mult {


  void set_iref_pmos(block_t& blk, unsigned char data){
    logger::assert(data < 8 && data >= 0, "iref has to be in [0,7]");

  }

  void set_iref_nmos(block_t& blk, unsigned char data){
    logger::assert(data < 8 && data >= 0, "iref has to be in [0,7]");
  }


  bool has_port(PORT_NAME port){
    return port == PORT_NAME::IN0 or
      port == PORT_NAME::IN1 or
      port == PORT_NAME::COEFF or
      port == PORT_NAME::OUT0;
  }

  void set_enable(block_t& blk, bool enabled){

  }


  void set_vga(block_t& blk, bool enabled){

  }

  void set_gain_code(block_t& blk, unsigned char gain){
  }

  void set_gain(block_t& blk, float value){
    unsigned char gain = value*127 + 128;
    set_gain_code(blk,gain);
  }

  void set_range(block_t& blk, PORT_NAME port, RANGE_TYPE range){
  }

  void set_offset_code(block_t& blk, PORT_NAME port, unsigned char offset_code){
    logger::assert(port == PORT_NAME::IN0 ||
                   port == PORT_NAME::IN1 ||
                   port == PORT_NAME::OUT0 ||
                   port == PORT_NAME::COEFF, "not valid mult port");
    logger::assert(offset_code <= 63, "offset code oob");
  }


}
