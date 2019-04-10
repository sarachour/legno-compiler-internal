#include "include/Layout.h"
#include "include/Enums.h"
#include "include/Block.h"
#include "include/Logger.h"

namespace layout {

  loc_t mkloc(unsigned char row,
              unsigned char col,
              unsigned char offset,
              unsigned char size,
              bool flip_endian){
    loc_t loc;
    loc.row = row;
    loc.col = col;
    loc.offset = offset;
    loc.size = size;
    loc.flip_endian = flip_endian;
    return loc;
  }

  loc_t connection(block_loc_t& src,PORT_NAME srcp, \
                  block_loc_t& dest,PORT_NAME destp){
    loc_t loc;
    loc.size = 1;
    // row layout
    const char ROW_TILEOUT[4] = {1,1,0,0};
    const char ROW_ADC[4] = {4,0,5,0};
    const char ROW_TILEIN[4][4] = {{0,2,0,2},{0,2,0,2}, {1,3,1,3},{1,3,1,3}};
    const char ROW_DEFAULT[4] = {2,3,4,5};
    // bit layout
    const char BIT_MULT[2][2] = {{3,4},{5,6}};
    const char BIT_FANOUT[2] = {0,1};
    const char BIT_TILEOUT[4][4] = {
      {7,3,7,3},{6,2,6,2},{5,1,5,1},{4,0,4,0}
    };
    const char BIT_TILEIN[4][4] = {
      {0,4,0,4},{1,5,1,5},{2,6,2,6},{3,7,3,7}
    };
    const char BIT_CHIPOUT[4][4] = {
      {7,3,7,3},{6,2,6,2},{5,1,5,1},{4,0,4,0}
    };
    switch(dest.type){
    case BLOCK_TYPE::TILE_ADC:
      logger::assert(dest.slice == 0 && dest.slice == 2,
                     "adc must be on even slice");
      loc.row = ROW_ADC[dest.slice];
      loc.offset = 7;
      break;

    case BLOCK_TYPE::FANOUT:
      loc.row = ROW_DEFAULT[dest.slice];
      loc.offset = BIT_FANOUT[dest.index];
      break;


    case BLOCK_TYPE::INTEG:
      loc.row = ROW_DEFAULT[dest.slice];
      loc.offset = 2;
      break;

    case BLOCK_TYPE::TILE_OUT:
      loc.row = ROW_TILEOUT[dest.slice];
      loc.offset = BIT_TILEOUT[dest.index][dest.slice];
      break;
    case BLOCK_TYPE::MULT:
      loc.row = ROW_DEFAULT[dest.slice];
      loc.offset = BIT_MULT[dest.index][block::port_to_index(destp)];
      break;

    case BLOCK_TYPE::TILE_IN:
      loc.row = ROW_TILEIN[dest.slice][dest.tile];
      loc.offset = BIT_TILEIN[dest.index][dest.tile];
      break;

    case BLOCK_TYPE::CHIP_OUT:
      loc.row = 4;
      loc.offset = BIT_CHIPOUT[dest.slice][dest.tile];
      break;

    default:
      logger::error("invalid dest");
    }
    // col layout
    const char COL_TILEIN[4][4] = {
      {3,5,5,5},{3,5,5,5},
      {4,5,5,5},{4,5,5,5}
    };
    const char COL_DAC[4] = {2,2,5,5};
    const char COL_FANOUT[2] = {0,1};
    const char COL_MULT[2] = {3,4};
    const char COL_TILEOUT[4] = {13,13,14,14};
    //line layout
    const char LINE_TILEIN[4][4] = {
      {10,2,6,10}, {11,3,7,11}, {10,4,9,12}, {11,5,9,13}
    };
    const char LINE_TILEOUT[4][4] = {
      {0,4,8,12}, {1,5,9,13}, {2,6,10,14}, {3,7,11,15}
    };
    const char LINE_MULT[4] = {6,7,8,9};
    const char LINE_DAC[4] = {9,10,14,15};
    const char LINE_INTEG[4] = {5,6,7,8};
    const char LINE_FANOUT[4][3] = {
      {4,5,6},{7,8,9},{10,11,12},{13,14,15}
    };
    const char LINE_CHIPIN[4][4] = {
      {0,0,4,4},{1,1,5,5},{2,2,6,6},{3,3,7,7}
    };
    switch(src.type){
    case BLOCK_TYPE::TILE_IN:
      loc.col = COL_TILEIN[src.index][src.slice];
      loc.line = LINE_TILEIN[src.index][src.slice];
      break;
    case BLOCK_TYPE::TILE_OUT:
      loc.col = COL_TILEOUT[src.tile];
      loc.line = LINE_TILEOUT[src.index][src.slice];
      break;

    case BLOCK_TYPE::TILE_DAC:
      loc.col = COL_DAC[src.slice];
      loc.line = LINE_DAC[src.slice];
      break;

    case BLOCK_TYPE::INTEG:
      loc.col = 2;
      loc.line = LINE_INTEG[src.slice];
      break;
    case BLOCK_TYPE::FANOUT:
      loc.col = COL_FANOUT[src.index];
      loc.line = LINE_FANOUT[src.slice][block::port_to_index(srcp)];
      break;
    case BLOCK_TYPE::MULT:
      loc.col = COL_MULT[src.index];
      loc.line = LINE_MULT[src.slice];
      break;

    case BLOCK_TYPE::CHIP_IN:
      loc.col = 15;
      loc.line = LINE_CHIPIN[src.slice][src.tile];
      break;

    default:
      logger::error("invalid src");
    }

    return loc;
  }

  loc_t FANOUT_PARAM(block_loc_t& blk){
    const char ROW[4] = {2,3,4,5};
    const char COL[2] = {0,1};
    loc_t loc;
    loc.row = ROW[blk.slice];
    loc.col = COL[blk.index];
    loc.offset = loc.size = loc.line = 0;
    loc.flip_endian = true;
    return loc;
  }
  loc_t FANOUT_enable(block_loc_t& blk){
    loc_t l = FANOUT_PARAM(blk);
    l.line = 0;
    l.offset = 7;
    l.size = 1;
    return l;
  }
  loc_t FANOUT_range(block_loc_t& blk){
    loc_t l = FANOUT_PARAM(blk);
    l.line = 0;
    l.offset = 0;
    l.size = 1;
    return l;
  }
  loc_t FANOUT_inv(block_loc_t& blk, unsigned char idx){
    loc_t l = FANOUT_PARAM(blk);
    l.line = idx;
    l.offset = 1;
    l.size = 1;
    return l;
  }
  loc_t FANOUT_en3(block_loc_t& blk){
    loc_t l = FANOUT_PARAM(blk);
    l.line = 3;
    l.offset = 0;
    l.size = 1;
    return l;
  }
  loc_t FANOUT_nmos(block_loc_t& blk){
    const char COL[2][4] = {{0,0,1,1}, {1,1,2,2}};
    const char LINE[2][4] = {{0,1,0,1},{2,3,0,1}};
    const char OFFSET[4] = {3,3,0,0};
    loc_t loc;
    loc.row = 0;
    loc.col = COL[blk.index][blk.slice];
    loc.line = LINE[blk.index][blk.slice];
    loc.offset = OFFSET[blk.slice];
    loc.size = 3;
    loc.flip_endian = true;
    return loc;
  }

  loc_t FANOUT_pmos(block_loc_t& blk){
    const char LINE[2][4] = {{3,2,1,0}, {1,0,3,2}};
    const char COL[2] = {0,1};
    loc_t loc;
    loc.row = 0;
    loc.col = COL[blk.index];
    loc.line = LINE[blk.index][blk.slice];
    loc.size = 3;
    loc.flip_endian = true;
    return loc;
  }
  loc_t MULT_PARAM(block_loc_t& blk){
    const char ROW[4] = {2,3,4,5};
    const char COL[2] = {3,4};
    loc_t loc;
    loc.row = ROW[blk.slice];
    loc.col = COL[blk.index];
    loc.offset = loc.size = loc.line = 0;
    loc.flip_endian = true;
    return loc;
  }
  loc_t MULT_enable(block_loc_t& blk){
    loc_t loc = MULT_PARAM(blk);
    loc.line = 0;
    loc.offset = 7;
    loc.size = 1;
    return loc;
  }

  loc_t MULT_vga(block_loc_t& blk){
    loc_t loc = MULT_PARAM(blk);
    loc.line = 1;
    loc.offset = 1;
    loc.size = 1;
    return loc;
  }
  loc_t MULT_range(block_loc_t& blk, PORT_NAME port){
    loc_t loc = MULT_PARAM(blk);
    loc.line = 0;
    loc.size = 2;
    switch(port){
    case PORT_NAME::IN0: loc.offset = 4; break;
    case PORT_NAME::IN1: loc.offset = 2; break;
    case PORT_NAME::OUT0: loc.offset = 0; break;
    default: logger::error("unsupported port"); break;
    }
    return loc;
  }

  loc_t MULT_gain_code(block_loc_t& blk){
    loc_t loc = MULT_PARAM(blk);
    loc.line = 2;
    loc.offset = 0;
    loc.size = 8;
    return loc;
  }
  loc_t MULT_offset_code(block_loc_t& blk, PORT_NAME port){
    loc_t loc = MULT_PARAM(blk);
    loc.size = 6;
    switch(port){
    case PORT_NAME::COEFF:
      loc.line = 1; loc.offset = 2; break;
    case PORT_NAME::OUT0:
      loc.line = 3; loc.offset = 2; break;
    case PORT_NAME::IN0:
      loc.line = 4; loc.offset = 2; break;
    case PORT_NAME::IN1:
      loc.line = 5; loc.offset = 2; break;
    default: logger::error("unsupported port"); break;
    }
    return loc;
  }

  loc_t DAC_PARAM(block_loc_t& blk){
    loc_t loc;
    const unsigned char COL[4] = {6,3,7,4};
    loc.row = 6;
    loc.col = COL[blk.slice];
    loc.flip_endian = true;
    loc.line = loc.offset = loc.size = 0;
    return loc;
  }

  loc_t DAC_enable(block_loc_t& blk){
    loc_t loc = DAC_PARAM(blk);
    loc.line = 0;
    loc.offset=7;
    loc.size = 1;
    return loc;
  }

  loc_t DAC_value(block_loc_t& blk){
    loc_t loc;
    const char LINE[4] = {7,8,9,10};
    loc.row = 8;
    loc.col = 0;
    loc.line = LINE[blk.slice];
    loc.offset = 0;
    loc.size = 8;
    loc.flip_endian = true;
    return loc;
  }

}
