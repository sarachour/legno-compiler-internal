#include "include/Block.h"
#include "include/Util.h"

namespace mult {

  vector_t mult_vect(block_t& blk, unsigned char line, unsigned char data){
    const unsigned char to_sel_row[4] = {2,3,4,5};
    const unsigned char to_sel_col[2] = {3,4};

    unsigned char selRow = to_sel_row[blk.slice];
    unsigned char selCol = to_sel_col[blk.index];
    vector_t vec = mkvector(blk.tile, selRow, selCol, line,
                        endian(data));
    return vec;
  }
  void configure(block_t& blk, unsigned char line, unsigned char data){
    blk.iface->enqueue(mult_vect(blk,line,data));
  }
  unsigned char get_config(block_t& blk, unsigned char line){
    return blk.iface->get(mult_vect(blk,line,0));

  }

  void set_enable(block_t& blk, bool enabled){
    unsigned char cfg;

    cfg = get_config(blk,0);
    if(enabled){
      cfg = copy_bits(cfg,0b1,7,1);
    }
    else{
      cfg = copy_bits(cfg,0b0,7,1);
    }
    configure(blk,1,cfg);

  }


  void set_vga(block_t& blk, bool enabled){
    unsigned char cfg;

    cfg = get_config(blk,1);
    if(enabled){
      cfg = copy_bits(cfg,0b10,0,2);
    }
    else{
      cfg = copy_bits(cfg,0b0,0,2);
    }
    configure(blk,1,cfg);

  }

  void set_gain_code(block_t& blk, unsigned char gain){
    configure(blk,2,gain);
  }

  void set_range(block_t& blk, PORT_NAME port, RANGE_TYPE range){
    unsigned char cfg = get_config(blk,0);
    unsigned char range_code = to_range_code(blk.type,range);
    switch(port){
    case PORT_NAME::IN0:
      cfg = copy_bits(cfg,range_code,4,2);
      break;
    case PORT_NAME::IN1:
      cfg = copy_bits(cfg,range_code,2,2);
      break;
    case PORT_NAME::OUT:
      cfg = copy_bits(cfg,range_code,0,2);
      break;
    default:
      error("unexpected port for mult.");
    }
    configure(blk,0,cfg);

  }
  void set_offset_code(block_t& blk, PORT_NAME port, unsigned char offset_code){
    assert(port == PORT_NAME::IN0 ||
           port == PORT_NAME::IN1 ||
           port == PORT_NAME::OUT ||
           port == PORT_NAME::COEFF);
    assert(offset_code <= 63);
    unsigned char cfg;
    switch(port){
    case PORT_NAME::IN1:
      cfg = offset_code << 2;
      configure(blk,5,cfg);
      break;
    case PORT_NAME::IN0:
      cfg = offset_code << 2;
      configure(blk,4,cfg);
      break;
    case PORT_NAME::OUT:
      cfg = offset_code << 2;
      configure(blk,3,cfg);
      break;
    case PORT_NAME::COEFF:
      cfg = get_config(blk,1);
      cfg = copy_bits(cfg,offset_code,2,6);
      configure(blk,1,cfg);
      break;
    default:
      assert(false);
    }
  }


}
