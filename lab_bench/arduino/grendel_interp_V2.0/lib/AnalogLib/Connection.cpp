#include "include/Block.h"
#include "include/Util.h"
#include "include/Vector.h"
#include "include/Connection.h"
#include "include/Logger.h"

namespace conn {

vector_t build_connection_vector(block_t src, PORT_NAME sport,
                                 block_t dst, PORT_NAME dport, bool & cross_tile);
vector_t null_neighbor_row1(vector_t& v, unsigned char row){
  v = mkvector(v.tile,row,v.col,v.line,0);
  return v;
}
vector_t null_neighbor_row2(vector_t& v, unsigned char tile_row, unsigned char row){
  const unsigned char TILE_MAP[2][4] = {
    {0,1,0,1},
    {2,3,2,3}
  };
  const unsigned char new_tile = TILE_MAP[tile_row][v.tile];
  return mkvector(new_tile,row,v.col,v.line,0);
}

void brkconn(block_t src,PORT_NAME sport, block_t dst, PORT_NAME dport){
  if(src.chip != dst.chip){
    logger::error("cannot connect different chips");
  }
  bool cross_tile = false;
  vector_t v = build_connection_vector(src,sport,dst,dport,cross_tile);
  block::set_enable(src,false);
  block::set_enable(dst,false);
  if(src.type == BLOCK_TYPE::FANOUT && sport == PORT_NAME::OUT2){
    fanout::set_out3(src,false);
  }
  if(dst.type == BLOCK_TYPE::INTEG){
    integ::set_exception(dst,false);
  }
  // sets the bits to zero
  src.iface->enqueue(clear_vector(v));

}
void mkconn(block_t& src,PORT_NAME sport, block_t& dst, PORT_NAME dport)
{
  if(src.chip != dst.chip){
    logger::error("cannot connect different chips");
  }

  bool cross_tile = false;
  vector_t v = build_connection_vector(src,sport,dst,dport,cross_tile);
  if(cross_tile){
    for(unsigned char row=0; row < 5; row++){
      src.iface->enqueue(null_neighbor_row2(v,0,row));
      src.iface->enqueue(null_neighbor_row2(v,1,row));
    }
  }
  else{
    for(unsigned char row=0; row < 6; row++){
      src.iface->enqueue(null_neighbor_row1(v,row));
    }
  }
  logger::assert(block::has_port(src.type,sport), "does not have source port");
  logger::assert(block::output_port(sport), "port is not output port");
  logger::assert(block::has_port(dst.type,dport), "does not have dest port");
  logger::assert(block::input_port(dport), "port is not input port");
  block::set_enable(src,true);
  block::set_enable(dst,true);
  if(src.type == BLOCK_TYPE::FANOUT && sport == PORT_NAME::OUT2){
    fanout::set_out3(src,true);
  }
  if(dst.type == BLOCK_TYPE::INTEG){
    integ::set_exception(dst,true);
  }
  src.iface->enqueue(v);
}


/*
THESE ARE ALL PRIVATE METHODS FOR CONSTRUCTING THE VECTOR
*/

unsigned char findGlobalSelCol(block_t& blk){
  switch(blk.type){
  case BLOCK_TYPE::CHIP_IN:
    return 15;
  case BLOCK_TYPE::TILE_OUT:
    switch(blk.tile){
    case 0:
    case 2:
      return 13;
    case 1:
    case 3:
      return 14;
    default:
      logger::error("unknown tile");
      break;
    }
    break;
  default:
    logger::error("unknown block");
    break;
  }
  logger::error("logic logger::error");
  return 0;
}
unsigned char findGlobalSelRow(block_t& blk){
  const unsigned char TILE_ROWS[4][4] = {
    {0,2,0,2},
    {0,2,0,2},
    {1,3,1,3},
    {1,3,1,3}
  };
  switch(blk.type){
  case CHIP_OUT:
    return 4;

  case TILE_IN:
    return TILE_ROWS[blk.slice][blk.tile];
    break;

  default:
    logger::error("cannot have arbitrary block bridging tiles.");
  }
  logger::error("logic logger::error");
  return 0;

}

unsigned char findLocalSelBit(block_t& blk, PORT_NAME port){
  //left=0; right=1
  const unsigned char MULT_BITS[2][2] = {
    {3,4},{5,6}
  };
  const unsigned char FANOUT_BITS[2] = {0,1};
  const unsigned char TILEOUT_BITS[4][4] = {
    {7,3,7,3},
    {6,2,6,2},
    {5,1,5,1},
    {4,0,4,0}
  };
  switch(blk.type){
  case BLOCK_TYPE::MULT:
    return MULT_BITS[blk.index][block::port_to_index(port)];
  case BLOCK_TYPE::INTEG:
    return 2;
  case BLOCK_TYPE::FANOUT:
    return FANOUT_BITS[blk.index];
  case BLOCK_TYPE::TILE_ADC:
    return 7;
  case BLOCK_TYPE::TILE_OUT:
    return TILEOUT_BITS[blk.index][blk.slice];
  case BLOCK_TYPE::TILE_LUT:
  case BLOCK_TYPE::TILE_DAC:
  case BLOCK_TYPE::CHIP_IN:
  case BLOCK_TYPE::TILE_IN:
    logger::error("unsupported");
    break;
  default:
    logger::error("unsupported");
    break;
  }
  logger::error("logic logger::error");
  return 0;
}
unsigned char findLocalSelLine(block_t& blk,PORT_NAME port){
  logger::assert(block::has_port(blk.type,port), "does not have port");
  logger::assert(block::output_port(port), "not output port");

  const unsigned char TILE_LINES[4][4] = {
    {10,2,6,10},
    {11,3,7,11},
    {10,4,8,12},
    {11,5,0,13}
  };
  const unsigned char MULT_LINES[4] = {11,5,9,13};
  const unsigned char DAC_LINES[4] = {9,10,14,15};
  const unsigned char FANOUT_LINES[4][3] = {
    {4,5,6},{7,8,9},{10,11,12},{13,14,15}
  };
  const unsigned char INTEG_LINES[4] = {5,6,7,8};
  switch(blk.type){
  case BLOCK_TYPE::TILE_IN:
    return TILE_LINES[blk.index][blk.slice];

  case BLOCK_TYPE::MULT:
    return MULT_LINES[blk.slice];

  case BLOCK_TYPE::TILE_DAC:
    return DAC_LINES[blk.slice];

  case BLOCK_TYPE::INTEG:
    return INTEG_LINES[blk.slice];

  case BLOCK_TYPE::FANOUT:
    return FANOUT_LINES[blk.slice][block::port_to_index(port)];

  case BLOCK_TYPE::CHIP_IN:
  case BLOCK_TYPE::TILE_ADC:
  case BLOCK_TYPE::TILE_LUT:
  case BLOCK_TYPE::TILE_OUT:
  case BLOCK_TYPE::CHIP_OUT:
    logger::error("cannot use as destination"); break;
  default:
    logger::error("cannot get line"); break;
  }
  logger::error("global logic logger::error");
  return 0;
}
unsigned char findLocalSelCol(block_t& blk){
  const unsigned char TILE_COLS[4][4] = {
    {3,5,5,5},
    {3,5,5,5},
    {4,5,5,5},
    {4,5,5,5}
  };
  const unsigned char DAC_COLS[4] = {3,3,5,5};
  const unsigned char FANOUT_COLS[2] = {0,1};
  const unsigned char MULT_COLS[2] = {3,4};
  switch(blk.type){
  case BLOCK_TYPE::TILE_IN:
    return TILE_COLS[blk.index][blk.slice];
    break;
  case BLOCK_TYPE::MULT:
    return MULT_COLS[blk.index];

  case BLOCK_TYPE::TILE_DAC:
    return DAC_COLS[blk.slice];
    break;

  case BLOCK_TYPE::INTEG:
    return 2;

  case BLOCK_TYPE::FANOUT:
    return FANOUT_COLS[blk.index];
    break;
  case BLOCK_TYPE::CHIP_IN:
  case TILE_ADC:
  case TILE_LUT:
  case TILE_OUT:
  case CHIP_OUT:
    logger::error("invalid unit");
    break;
  default:
    logger::error("unknown unit");
    break;
  }
  logger::error("could not find block");
  return 0;
}
unsigned char findLocalSelRow(block_t& blk){
  switch(blk.type) {
  case TILE_DAC:
    logger::error("cannot connect dac");
  case TILE_ADC:
    switch(blk.slice){
    case 0: return 4;
    case 1: logger::error("ADC only on [0,2]");
    case 2: return 5;
    case 3: logger::error("ADC only on [0,2]");
    }
    break;
  case TILE_LUT:
    logger::error("LUT cannot be destination");
  case TILE_OUT:
    switch(blk.slice){
    case 0:
    case 1: return 1;
    case 2:
    case 3: return 0;
    }
    break;
  case CHIP_OUT:
    logger::error("chip_out cannot be destination");
  default:
    switch(blk.slice){
    case 0: return 2;
    case 1: return 3;
    case 2: return 4;
    case 3: return 5;
    }
    break;
  }
  logger::error("logic logger::error");
  return 0;
}

 vector_t build_connection_vector(block_t src, PORT_NAME sport, block_t dst, PORT_NAME dport, bool & cross_tile){
  cross_tile = (src.type == CHIP_IN or src.type == TILE_OUT) or \
    (dst.type == CHIP_OUT or dst.type == TILE_IN);

  if(not cross_tile && src.tile != dst.tile){
    logger::error("cannot connect functional units on different tiles");
  }
  const unsigned char CONN_TILE[4][4] = {
    {0,1,0,1},
    {0,1,0,1},
    {2,3,2,3},
    {2,3,2,3}
  };
  unsigned char selTile = CONN_TILE[dst.tile][src.tile];
  unsigned char selRow;
  unsigned char selCol;
  unsigned char selLine;
  unsigned char selBit;
  if(not cross_tile){
    selRow = findLocalSelRow(dst);
    selCol = findLocalSelCol(src);
    selBit = findLocalSelBit(dst,dport);
    selLine = findLocalSelLine(src,sport);
  }
  else{
    selRow = findGlobalSelRow(dst);
    selCol = findGlobalSelCol(src);
    selBit = findLocalSelBit(dst,dport);
    selLine = findLocalSelLine(src,sport);
  }
  vector_t v = mkvector(selTile, selRow, selCol, selLine, selBit);
  return v;
}

}
