#include "include/Block.h"
#include "include/Util.h"
#include "include/Layout.h"
#include "include/Vector.h"
#include "include/Connection.h"
#include "include/Logger.h"

namespace conn {

  vector_t build_connection_vector(block_t src, PORT_NAME sport,
                                   block_t dst, PORT_NAME dport,
                                   bool & cross_tile);

  vector_t null_neighbor_row1(vector_t& v, unsigned char row){
    loc_t loc = layout::mkloc(row,v.loc.col,v.loc.line,0,8,false);
    v = mkvector(v.tile,loc,0);
    return v;
  }


  vector_t null_neighbor_row2(vector_t& v,
                              unsigned char tile_row,
                              unsigned char row){
    const unsigned char TILE_MAP[2][4] = {
      {0,1,0,1},
      {2,3,2,3}
    };
    const unsigned char new_tile = TILE_MAP[tile_row][v.tile];

    loc_t loc = layout::mkloc(row,v.loc.col,v.loc.line,0,8,false);
    return mkvector(new_tile,loc,0);
  }

  void brkconn(block_t src,PORT_NAME sport,
               block_t dst, PORT_NAME dport){
    if(src.place.chip != dst.place.chip){
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
  void mkconn(block_t& src,PORT_NAME sport,
              block_t& dst, PORT_NAME dport)
  {
    if(src.place.chip != dst.place.chip){
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



  vector_t build_connection_vector(block_t src, PORT_NAME sport,
                                    block_t dst, PORT_NAME dport,
                                    bool & cross_tile){
    cross_tile = (src.type == CHIP_IN or src.type == TILE_OUT) or \
      (dst.type == CHIP_OUT or dst.type == TILE_IN);

    if(not cross_tile && src.place.tile != dst.place.tile){
      logger::error("cannot connect functional units on different tiles");
    }
    loc_t loc = layout::connection(src.place,sport,dst.place,dport);
    const unsigned char CONN_TILE[4][4] = {
      {0,1,0,1},
      {0,1,0,1},
      {2,3,2,3},
      {2,3,2,3}
    };
    unsigned char tile = CONN_TILE[dst.place.tile][src.place.tile];
    vector_t v = mkvector(tile, loc, 0b1);
    return v;
  }

}
