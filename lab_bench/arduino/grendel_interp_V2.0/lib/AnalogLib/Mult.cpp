#include "include/Block.h"
#include "include/Util.h"
#include "include/Logger.h"

namespace mult {


  vector_t _pmos_vect(block_t& blk,unsigned char data,
                      unsigned char & offset,
                      unsigned char & size){
    const unsigned char PMOS_LINE[2][4] = {
      {2,5,1,0},
      {0,1,2,3}
    };
    const unsigned char selrow = 0;
    const unsigned char selcol = 4;
    const unsigned char line = PMOS_LINE[blk.index ][blk.slice];
    vector_t vec = mkvector(blk.tile, selrow, selcol, line,
                            endian(data));
    offset = 0;
    size = 3;
    if((blk.slice != 3) && blk.index == LEFT){
      offset = 3;
    }
    if((blk.slice == 0) && blk.index == RIGHT){
      offset = 3;
    }
    return vec;
  }

  vector_t _nmos_vect(block_t& blk,unsigned char data,
                      unsigned char & offset,
                      unsigned char & size){
    const unsigned char NMOS_ROW[4] = {1,0,1,0};
    const unsigned char NMOS_COL[4] = {2,3,2,3};
    const unsigned char NMOS_LINE[2][4] = {
      {1,0,0,1},
      {3,2,2,3}
    };
    unsigned char selrow = NMOS_ROW[blk.slice];
    unsigned char selcol = NMOS_COL[blk.slice];
    unsigned char line = NMOS_LINE[blk.index][blk.slice];
    vector_t vec = mkvector(blk.tile, selrow, selcol, line,
                            endian(data));
    offset = 0;
    size = 3;
    if((blk.slice == 0 || blk.slice == 2) && blk.index == 0){
      offset = 3;
    }
    return vec;
  }


  vector_t set_iref_pmos(block_t& blk, unsigned char data){
    logger::assert(data < 8 && data >= 0, "iref has to be in [0,7]");
    unsigned char offset;
    unsigned char size;
    vector_t vect = _pmos_vect(blk,0,offset,size);
    unsigned char cfg = endian(blk.iface->get(vect));
    cfg = copy_bits(cfg,0b111 & data,offset,size);
    // create vector
    vect = _pmos_vect(blk,cfg,offset,size);
    blk.iface->enqueue(vect);
  }

  vector_t set_iref_nmos(block_t& blk, unsigned char data){
    logger::assert(data < 8 && data >= 0, "iref has to be in [0,7]");
    unsigned char offset;
    unsigned char size;
    vector_t vect = _nmos_vect(blk,0,offset,size);
    unsigned char cfg = endian(blk.iface->get(vect));
    cfg = copy_bits(cfg,0b111 & data,offset,size);
    // create vector
    vect = _nmos_vect(blk,cfg,offset,size);
    blk.iface->enqueue(vect);
  }

  vector_t _param_vect(block_t& blk, unsigned char line, unsigned char data){
    const unsigned char to_sel_row[4] = {2,3,4,5};
    const unsigned char to_sel_col[2] = {3,4};

    unsigned char selrow = to_sel_row[blk.slice];
    unsigned char selcol = to_sel_col[blk.index];
    vector_t vec = mkvector(blk.tile, selrow, selcol, line, data);
    return vec;
  }

  void set_params(block_t& blk, unsigned char line, unsigned char data){
    blk.iface->enqueue(_param_vect(blk,line,endian(data)));
  }
  unsigned char get_params(block_t& blk, unsigned char line){
    return endian(blk.iface->get(_param_vect(blk,line,0)));

  }

  bool has_port(PORT_NAME port){
    return port == PORT_NAME::IN0 or
      port == PORT_NAME::IN1 or
      port == PORT_NAME::COEFF or
      port == PORT_NAME::OUT0;
  }

  void set_enable(block_t& blk, bool enabled){
    unsigned char cfg;

    cfg = get_params(blk,0);
    if(enabled){
      cfg = copy_bits(cfg,0b1,7,1);
    }
    else{
      cfg = copy_bits(cfg,0b0,7,1);
    }
    set_params(blk,1,cfg);

  }


  void set_vga(block_t& blk, bool enabled){
    unsigned char cfg;

    cfg = get_params(blk,1);
    if(enabled){
      cfg = copy_bits(cfg,0b10,0,2);
    }
    else{
      cfg = copy_bits(cfg,0b0,0,2);
    }
    set_params(blk,1,cfg);

  }

  void set_gain_code(block_t& blk, unsigned char gain){
    set_params(blk,2,gain);
  }

  void set_gain(block_t& blk, float value){
    logger::warn("todo: set_gain");
  }

  void set_range(block_t& blk, PORT_NAME port, RANGE_TYPE range){
    unsigned char cfg = get_params(blk,0);
    unsigned char range_code = to_range_code(blk.type,range);
    switch(port){
    case PORT_NAME::IN0:
      cfg = copy_bits(cfg,range_code,4,2);
      break;
    case PORT_NAME::IN1:
      cfg = copy_bits(cfg,range_code,2,2);
      break;
    case PORT_NAME::OUT0:
      cfg = copy_bits(cfg,range_code,0,2);
      break;
    default:
      logger::error("unexpected port for mult.");
    }
    set_params(blk,0,cfg);

  }

  void set_offset_code(block_t& blk, PORT_NAME port, unsigned char offset_code){
    logger::assert(port == PORT_NAME::IN0 ||
                   port == PORT_NAME::IN1 ||
                   port == PORT_NAME::OUT0 ||
                   port == PORT_NAME::COEFF, "not valid mult port");
    logger::assert(offset_code <= 63, "offset code oob");
    unsigned char cfg;
    switch(port){
    case PORT_NAME::IN1:
      cfg = offset_code << 2;
      set_params(blk,5,cfg);
      break;
    case PORT_NAME::IN0:
      cfg = offset_code << 2;
      set_params(blk,4,cfg);
      break;
    case PORT_NAME::OUT0:
      cfg = offset_code << 2;
      set_params(blk,3,cfg);
      break;
    case PORT_NAME::COEFF:
      cfg = get_params(blk,1);
      cfg = copy_bits(cfg,offset_code,2,6);
      set_params(blk,1,cfg);
      break;
    default:
      logger::assert(false, "unknown port");
    }
  }


}
