#define _DUE
#include "AnalogLib.h"
#include "Circuit.h"
#include "Comm.h"
#include <assert.h>

//char HCDC_DEMO_BOARD = 6;
char HCDC_DEMO_BOARD = 4;


namespace circ {

  RANGE_TYPE to_range(unsigned char code){
    switch(code){
    case 0: return RANGE_TYPE::RNG_LOW;
    case 1: return RANGE_TYPE::RNG_MED;
    case 2: return RANGE_TYPE::RNG_HIGH;
    default:
      comm::error("unknown range");
    }
    return RANGE_TYPE::RNG_MED;
  }

  PORT_NAME to_out_port(unsigned char index){
    switch(index){
    case 0: return PORT_NAME::OUT0;
    case 1: return PORT_NAME::OUT1;
    case 2: return PORT_NAME::OUT2;
    default:
      comm::error("unknown");
    }
    return PORT_NAME::UNKNOWN_PORT;
  }
  PORT_NAME to_in_port(unsigned char index){
    switch(index){
    case 0: return PORT_NAME::IN0;
    case 1: return PORT_NAME::IN1;
    default:
      comm::error("unknown");
    }
    return PORT_NAME::UNKNOWN_PORT;

  }

  BLOCK_TYPE to_blk(unsigned char btype){
    switch(btype){
    case block_type_t::TILE_DAC: return BLOCK_TYPE::TILE_DAC;
    case block_type_t::TILE_INPUT: return BLOCK_TYPE::TILE_IN;
    case block_type_t::TILE_OUTPUT: return BLOCK_TYPE::TILE_OUT;
    case block_type_t::CHIP_INPUT: return BLOCK_TYPE::CHIP_IN;
    case block_type_t::CHIP_OUTPUT: return BLOCK_TYPE::CHIP_OUT;
    case block_type_t::MULT: return BLOCK_TYPE::MULT;
    case block_type_t::FANOUT: return BLOCK_TYPE::FANOUT;
    case block_type_t::INTEG: return BLOCK_TYPE::INTEG;
    case block_type_t::LUT: return BLOCK_TYPE::TILE_LUT;
    case block_type_t::TILE_ADC: return BLOCK_TYPE::TILE_ADC;
    default:
      comm::error("unknown block.");
    }
    comm::error("error");
    return BLOCK_TYPE::UNKNOWN_BLOCK;
  }
  void debug_command(Fabric * fab, cmd_t& cmd, float* inbuf){
    cmd_write_lut_t wrlutd;
    switch(cmd.type){
    case cmd_type_t::CONFIG_DAC:
      comm::response("[dbg] configured dac (direct)",0);
      break;
    case cmd_type_t::USE_ADC:
      comm::response("[dbg] enabled adc",0);
      break;
    case cmd_type_t::USE_DAC:
      comm::response("[dbg] enabled dac",0);
      break;
    case cmd_type_t::CONFIG_MULT:
      comm::response("[dbg] configured mult [direct]",0);
      break;
    case cmd_type_t::USE_MULT:
      comm::response("[dbg] enabled mult",0);
      break;
    case cmd_type_t::USE_FANOUT:
      comm::response("[dbg] enabled fanout",0);
      break;
    case cmd_type_t::CONFIG_INTEG:
      comm::response("[dbg] configured integ [direct]",0);
      break;
    case cmd_type_t::USE_INTEG:
      comm::response("[dbg] enabled integ",0);
      break;
    case cmd_type_t::GET_INTEG_STATUS:
      comm::response("[dbg] retrieved integ exception",1);
      comm::data("0", "i");
      break;
    case cmd_type_t::GET_ADC_STATUS:
      comm::response("[dbg] retrieved  lut exception",1);
      comm::data("0", "i");
      break;
    case cmd_type_t::USE_LUT:
      comm::response("[dbg] use lut",0);
      break;
    case cmd_type_t::WRITE_LUT:
      wrlutd = cmd.data.write_lut;
      comm::print_header();
      Serial.print(wrlutd.n);
      Serial.print(" offset=");
      Serial.println(wrlutd.offset);
      for(int data_idx=0; data_idx < wrlutd.n; data_idx+=1){
        comm::print_header();
        Serial.print(data_idx+wrlutd.offset);
        Serial.print("=");
        Serial.print(inbuf[data_idx]);
      }
      comm::response("[dbg] write lut",0);
      break;
    case cmd_type_t::DISABLE_DAC:
      comm::response("[dbg] disabled dac",0);
      break;
    case cmd_type_t::DISABLE_ADC:
      comm::response("[dbg] disabled adc",0);
      break;
    case cmd_type_t::DISABLE_LUT:
      comm::response("[dbg] disabled lut",0);
      break;
    case cmd_type_t::DISABLE_MULT:
      comm::response("[dbg] disabled mult",0);
      break;
    case cmd_type_t::DISABLE_FANOUT:
      comm::response("[dbg] disabled fanout",0);
      break;
    case cmd_type_t::DISABLE_INTEG:
      comm::response("[dbg] disabled integ",0);
      break;
    case cmd_type_t::CONNECT:
      comm::response("[dbg] connected",0);
      break;
    case cmd_type_t::BREAK:
      comm::response("[dbg] disconnected",0);
      break;
    case cmd_type_t::CALIBRATE:
      comm::response("[dbg] calibrated",0);
      break;
    default:
      comm::error("unknown command");
      break;
    }
  }


  void exec_command(Fabric * fab, cmd_t& cmd, float* inbuf){
    block_t blk;
    block_t blk2;
    PORT_NAME port;
    PORT_NAME port2;
    switch(cmd.type){
    case cmd_type_t::USE_MULT:
      // multiplier doesn't actually support inversion
      // multiplier uses dac from same row.
      blk = fab->block(BLOCK_TYPE::MULT,
                      cmd.data.mult.loc.loc.chip,
                      cmd.data.mult.loc.loc.tile,
                      cmd.data.mult.loc.loc.slice,
                      cmd.data.mult.loc.idx
                      );
      mult::set_enable(blk,true);
      mult::set_vga(blk,cmd.data.mult.use_coeff);
      mult::set_range(blk, PORT_NAME::OUT0,
                      to_range(cmd.data.mult.in0_range));
      mult::set_range(blk, PORT_NAME::IN1,
                      to_range(cmd.data.mult.out_range));
      if(not cmd.data.mult.use_coeff){
        mult::set_range(blk, PORT_NAME::IN1,
                        to_range(cmd.data.mult.in1_range));
      }
      else{
        mult::set_gain(blk,
                       cmd.data.mult.coeff);
      }
      comm::response("enabled mult",0);
      break;
    case cmd_type_t::CONNECT:
      blk = fab->block(to_blk(cmd.data.conn.src_blk),
                      cmd.data.conn.src_loc.idxloc.loc.chip,
                      cmd.data.conn.src_loc.idxloc.loc.tile,
                      cmd.data.conn.src_loc.idxloc.loc.slice,
                      cmd.data.conn.src_loc.idxloc.idx);
      blk2 = fab->block(to_blk(cmd.data.conn.dst_blk),
                        cmd.data.conn.dst_loc.idxloc.loc.chip,
                        cmd.data.conn.dst_loc.idxloc.loc.tile,
                        cmd.data.conn.dst_loc.idxloc.loc.slice,
                        cmd.data.conn.dst_loc.idxloc.idx);

      port = to_out_port(cmd.data.conn.src_loc.idx2);
      port2 = to_in_port(cmd.data.conn.dst_loc.idx2);
      conn::mkconn(blk,port,blk2,port2);
      comm::response("connected",0);
      break;
    default:
        comm::error("unknown command");
        break;
    }
  }


  void print_loc(circ_loc_t& loc){
    Serial.print(loc.chip);
    Serial.print(":");
    Serial.print(loc.tile);
    Serial.print(":");
    Serial.print(loc.slice);
  }

  void print_idx_loc(circ_loc_idx1_t& loc){
    print_loc(loc.loc);
    Serial.print(":");
    Serial.print(loc.idx);
  }


  void print_port_loc(circ_loc_idx2_t& loc){
    print_idx_loc(loc.idxloc);
    Serial.print("[");
    Serial.print(loc.idx2);
    Serial.print("]");
  }

  void print_block(uint8_t type){
    switch(type){
    case block_type::TILE_DAC:
      Serial.print("dac");
      break;
    case block_type::CHIP_INPUT:
      Serial.print("chip_in");
      break;
    case block_type::CHIP_OUTPUT:
      Serial.print("chip_out");
      break;
    case block_type::TILE_INPUT:
      Serial.print("tile_in");
      break;
    case block_type::TILE_OUTPUT:
      Serial.print("tile_out");
      break;
    case block_type::MULT:
      Serial.print("mult");
      break;
    case block_type::INTEG:
      Serial.print("integ");
      break;
    case block_type::FANOUT:
      Serial.print("fanout");
      break;
    case block_type::LUT:
      Serial.print("lut");
      break;
    case block_type::TILE_ADC:
      Serial.print("adc");
      break;
    default:
      Serial.print("unknown<");
      Serial.print(type);
      Serial.print(">");
      break;
    }
  }
  #define range_to_str(code) (code == 2 ? "h" : (code == 1 ? "m" : (code == 0 ? "l" : "?")))

  void print_command(cmd_t& cmd){
    comm::print_header();
    switch(cmd.type){
    case cmd_type_t::USE_FANOUT:
      Serial.print("use fanout ");
      print_idx_loc(cmd.data.fanout.loc);
      Serial.print(" inv0=");
      Serial.print(cmd.data.fanout.inv[0] ? "yes" : "no");
      Serial.print(" inv1=");
      Serial.print(cmd.data.fanout.inv[1] ? "yes" : "no");
      Serial.print(" inv2=");
      Serial.print(cmd.data.fanout.inv[2] ? "yes" : "no");
      Serial.print(" rng=");
      Serial.print(range_to_str(cmd.data.fanout.in_range));
      break;

    case cmd_type_t::CONFIG_MULT:
      Serial.print("config mult ");
      print_idx_loc(cmd.data.mult.loc);
      if(cmd.data.mult.use_coeff){
        Serial.print(" gain coeff=");
        Serial.print(cmd.data.mult.coeff);
      }
      else{
        Serial.print(" prod");
      }
      Serial.print(" in0_rng=");
      Serial.print(range_to_str(cmd.data.mult.in0_range));
      Serial.print(" in1_rng=");
      Serial.print(range_to_str(cmd.data.mult.in1_range));
      Serial.print(" out_rng=");
      Serial.print(range_to_str(cmd.data.mult.out_range));
      break;
    case cmd_type_t::USE_MULT:
      Serial.print("use mult ");
      print_idx_loc(cmd.data.mult.loc);
      if(cmd.data.mult.use_coeff){
        Serial.print(" gain coeff=");
        Serial.print(cmd.data.mult.coeff);
      }
      else{
        Serial.print(" prod");
      }
      Serial.print(" in0_rng=");
      Serial.print(range_to_str(cmd.data.mult.in0_range));
      Serial.print(" in1_rng=");
      Serial.print(range_to_str(cmd.data.mult.in1_range));
      Serial.print(" out_rng=");
      Serial.print(range_to_str(cmd.data.mult.out_range));
      break;
    case cmd_type_t::CONFIG_DAC:
      Serial.print("config dac ");
      print_loc(cmd.data.dac.loc);
      Serial.print(" val=");
      Serial.print(cmd.data.dac.value);
      break;
    case cmd_type_t::USE_ADC:
      Serial.print("use adc ");
      print_loc(cmd.data.adc.loc);
      Serial.print(" rng=");
      Serial.print(range_to_str(cmd.data.adc.in_range));
      break;
    case cmd_type_t::USE_DAC:
      Serial.print("use dac ");
      print_loc(cmd.data.dac.loc);
      Serial.print(" src=");
      Serial.print(cmd.data.dac.source);
      Serial.print(" inv=");
      Serial.print(cmd.data.dac.inv ? "yes" : "no");
      Serial.print(" rng=");
      Serial.print(range_to_str(cmd.data.dac.out_range));
      Serial.print(" val=");
      Serial.print(cmd.data.dac.value);
      break;
    case cmd_type_t::GET_ADC_STATUS:
      Serial.print("get adc status ");
      print_loc(cmd.data.adc.loc);
      break;
    case cmd_type_t::GET_INTEG_STATUS:
      Serial.print("get integ status ");
      print_loc(cmd.data.integ.loc);
      break;
    case cmd_type_t::CONFIG_INTEG:
      Serial.print("config integ ");
      print_loc(cmd.data.integ.loc);
      Serial.print(" ic=");
      Serial.print(cmd.data.integ.value);
      Serial.print(" in_range=");
      Serial.print(range_to_str(cmd.data.integ.in_range));
      Serial.print(" out_range=");
      Serial.print(range_to_str(cmd.data.integ.out_range));
      break;
    case cmd_type_t::USE_INTEG:
      Serial.print("use integ ");
      print_loc(cmd.data.integ.loc);
      Serial.print(" inv=");
      Serial.print(cmd.data.integ.inv ? "yes" : "no");
      Serial.print(" in_range=");
      Serial.print(range_to_str(cmd.data.integ.in_range));
      Serial.print(" out_range=");
      Serial.print(range_to_str(cmd.data.integ.out_range));
      Serial.print(" debug=");
      Serial.print(cmd.data.integ.debug == 1 ? "yes" : "no");
      break;
    case cmd_type_t::USE_LUT:
      Serial.print("use lut ");
      print_loc(cmd.data.lut.loc);
      Serial.print(" src=");
      Serial.print(cmd.data.lut.source);
      break;
    case cmd_type_t::WRITE_LUT:
      Serial.print("write lut ");
      print_loc(cmd.data.circ_loc);
      break;
    case cmd_type_t::DISABLE_ADC:
      Serial.print("disable adc ");
      print_loc(cmd.data.circ_loc);
      break;
    case cmd_type_t::DISABLE_DAC:
      Serial.print("disable dac ");
      print_loc(cmd.data.circ_loc);
      break;
    case cmd_type_t::DISABLE_MULT:
      Serial.print("disable mult ");
      print_loc(cmd.data.circ_loc);
      break;
    case cmd_type_t::DISABLE_INTEG:
      Serial.print("disable integ ");
      print_loc(cmd.data.circ_loc);
      break;
    case cmd_type_t::DISABLE_FANOUT:
      Serial.print("disable fanout ");
      print_idx_loc(cmd.data.circ_loc_idx1);
      break;
    case cmd_type_t::DISABLE_LUT:
      Serial.print("disable lut ");
      print_loc(cmd.data.circ_loc);
      break;
    case cmd_type_t::CONNECT:
      Serial.print("conn ");
      print_block(cmd.data.conn.src_blk);
      Serial.print(" ");
      print_port_loc(cmd.data.conn.src_loc);
      Serial.print("<->");
      print_block(cmd.data.conn.dst_blk);
      Serial.print(" ");
      print_port_loc(cmd.data.conn.dst_loc);
      break;
    case cmd_type_t::BREAK:
      Serial.print("break ");
      print_block(cmd.data.conn.src_blk);
      Serial.print(" ");
      print_port_loc(cmd.data.conn.src_loc);
      Serial.print("<->");
      print_block(cmd.data.conn.dst_blk);
      Serial.print(" ");
      print_port_loc(cmd.data.conn.dst_loc);
      break;
    case cmd_type_t::CALIBRATE:
      Serial.print("calibrate ");
      print_loc(cmd.data.circ_loc);
      break;
    default:
      Serial.print(cmd.type);
      Serial.print(" <unimpl circuit>");
      break;
    }
    Serial.println("");
  }

}


