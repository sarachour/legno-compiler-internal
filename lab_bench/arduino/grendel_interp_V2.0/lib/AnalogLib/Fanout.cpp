#include "include/Block.h"
#include "include/Logger.h"

namespace fanout {

  vector_t _param_vect(block_t&blk, unsigned char line, unsigned char cfg){
    assert(line >= 0 && line <= 3, "line in [0,3]");
    const char FANOUT_ROW[4] = {2,3,4,5};
    const char FANOUT_COL[2] = {0,1};
    const char row = FANOUT_ROW[blk.slice];
    const char col = FANOUT_COL[blk.index];
    return mkvector(row,col,line,cfg);
  }
  void set_params(block_t&blk, unsigned char line, unsigned char cfg){
    vector_t vect = _param_vect(blk,line,endian(cfg));
    blk.iface->enqueue(vect);
  }

  unsigned char get_params(block_t&blk, unsigned char line){
    return endian(blk.iface->get(_param_vect(blk,line,0)));
  }

  void set_out3(block_t& blk, bool enabled){
    logger::warn("unimpl: set_out3");
  }

  void set_inv(block_t* blk, bool invert){
    
  }

  void set_range(block_t* blk, RANGE_TYPE rng){
    
  }

  void set_enable(block_t* blk, bool enable){
    unsigned char cfg = get_params(blk,0);
  }
}
