#include "include/Block.h"
#include "include/Layout.h"

namespace tile_dac {

  void initialize(block_t& blk){

  }
  void set_enable(block_t& blk, bool value){
    loc_t loc = layout::DAC_enable(blk);
    unsigned char data = value ? 0b1 : 0b0;
    blk.iface->set(loc,data);
  }
  void set_source(block_t& blk, dac_source_t value){
    loc_t use_mem= layout::DAC_use_mem(blk);
    switch(value){
    case DSRC_MEM:
      break;
    case DSRC_PARA:
      break;
    case DSRC_LUT0:
      break;
    case DSRC_LUT1:
      break;
    }
  }

  void set_value(block_t& blk, unsigned char value){
    loc_t loc = layout::DAC_value(blk);
    blk.iface->set(loc,value);
  }
  void set_offset_code(block_t& blk, const char value){
  }

  void set_iref_pmos_code(block_t& blk, unsigned char pmos){
  }

  void set_iref_nmos_code(block_t& blk, unsigned char nmos){
  }

}
