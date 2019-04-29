#include "AnalogLib.h"
#include "Circuit.h"
#include "Experiment.h"
#include "Comm.h"

namespace circ {

void debug_command(Fabric * fab, cmd_t& cmd, float* inbuf){
  cmd_write_lut_t wrlutd;
  switch(cmd.type){
      case cmd_type_t::USE_ADC:
        comm::response("[dbg] enabled adc",0);
        break;
      case cmd_type_t::USE_DAC:
        comm::response("[dbg] enabled dac",0);
        break;
      case cmd_type_t::USE_MULT:
        comm::response("[dbg] enabled mult",0);
        break;
      case cmd_type_t::USE_FANOUT:
        comm::response("[dbg] enabled fanout",0);
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
    print_block(cmd.data.calib.blk);
    Serial.print(" ");
    print_idx_loc(cmd.data.calib.loc);
    break;
  case cmd_type_t::GET_STATE:
    Serial.print("get_state ");
    print_block(cmd.data.state.blk);
    Serial.print(" ");
    print_idx_loc(cmd.data.state.loc);
    break;
  default:
    Serial.print(cmd.type);
    Serial.print(" <unimpl print circuit>");
    break;
  }
  Serial.println("");
}

}

namespace experiment {


  void debug_command(experiment_t* expr, Fabric* fab, cmd_t& cmd, float * inbuf){
    char buf[128];
    switch(cmd.type){
    case cmd_type_t::RESET:
      comm::response("[dbg] resetted",0);
      break;
    case cmd_type_t::RUN:
      comm::response("[dbg] ran",0);
      break;
    case cmd_type_t::USE_ANALOG_CHIP:
      comm::response("[dbg] use_analog_chip=true",0);
      break;
    case cmd_type_t::USE_DAC:
      comm::response("[dbg] use_dac=true",0);
      break;
    case cmd_type_t::USE_ADC:
      comm::response("[dbg] use_adc=true",0);
      break;
    case cmd_type_t::USE_OSC:
      comm::response("[dbg] enable_trigger=true",0);
      break;
    case cmd_type_t::SET_SIM_TIME:
      comm::response("[dbg] set simulation time",0);
      break;

    case cmd_type_t::COMPUTE_OFFSETS:
      comm::response("[dbg] computed offsets",0);
      break;
    case cmd_type_t::SET_DAC_VALUES:
      comm::response("[dbg] set dac values",0);
      break;

    case cmd_type_t::GET_ADC_VALUES:
      comm::response("[dbg] get adc values",1);
      comm::data("3","F");
      comm::payload();
      Serial.println(" 0.3 0.5 0.7");
      break;

    case cmd_type_t::GET_TIME_BETWEEN_SAMPLES:
      comm::response("[dbg] get time between samples",1);
      comm::data("0.1","f");
      break;
    case cmd_type_t::GET_NUM_DAC_SAMPLES:
      comm::response("get num dac samples",1);
      comm::data("10","i");
      break;
    case cmd_type_t::GET_NUM_ADC_SAMPLES:
      comm::response("get num adc samples",1);
      comm::data("15","i");
      break;
    }
  }

  void print_command(cmd_t& cmd, float* inbuf){
    comm::print_header();
    switch(cmd.type){
    case cmd_type_t::SET_SIM_TIME:
      Serial.print("set_sim_time sim=");
      Serial.print(cmd.args.floats[0]);
      Serial.print(" period=");
      Serial.println(cmd.args.floats[1]);
      Serial.print(" osc=");
      Serial.println(cmd.args.floats[2]);
      break;

    case cmd_type_t::USE_OSC:
      Serial.println("use_osc");
      break;

    case cmd_type_t::USE_DAC:
      Serial.print("use_dac ");
      Serial.print(cmd.args.ints[0]);
      Serial.print(" periodic=");
      Serial.println(cmd.flag ? "yes" : "no");
      break;

    case cmd_type_t::USE_ADC:
      Serial.print("use_adc ");
      Serial.println(cmd.args.ints[0]);
      break;

    case cmd_type_t::USE_ANALOG_CHIP:
      Serial.println("use_analog_chip");
      break;

    case cmd_type_t::COMPUTE_OFFSETS:
      Serial.println("compute_offsets");
      break;

    case cmd_type_t::GET_NUM_DAC_SAMPLES:
      Serial.println("get_num_dac_samples");
      break;

    case cmd_type_t::GET_NUM_ADC_SAMPLES:
      Serial.println("get_num_adc_samples");
      break;
    case cmd_type_t::GET_TIME_BETWEEN_SAMPLES:
      Serial.println("get_time_between_samples");
      break;

    case cmd_type_t::GET_ADC_VALUES:
      Serial.print("get_adc_values adc_id=");
      Serial.print(cmd.args.ints[0]);
      Serial.print(" nels=");
      Serial.print(cmd.args.ints[1]);
      Serial.print(" offset=");
      Serial.println(cmd.args.ints[2]);
      break;

    case cmd_type_t::SET_DAC_VALUES:
      Serial.print("set_dac_values dac_id=");
      Serial.print(cmd.args.ints[0]);
      Serial.print(" nels=");
      Serial.print(cmd.args.ints[1]);
      Serial.print(" offset=");
      Serial.print(cmd.args.ints[2]);
      Serial.print(" [");
      for(int i=0; i < cmd.args.ints[1]; i++){
        Serial.print(inbuf[i]);
        Serial.print(" ");
      }
      Serial.println("]");
      break;

    case cmd_type_t::RESET:
      Serial.println("reset");
      break;

    case cmd_type_t::RUN:
      Serial.println("run");
      break;

    default:
      Serial.print(cmd.type);
      Serial.print(" ");
      Serial.print(cmd.args.ints[0]);
      Serial.print(" ");
      Serial.print(cmd.args.ints[1]);
      Serial.print(" ");
      Serial.print(cmd.args.ints[2]);
      Serial.println(" <unimpl print experiment>");
      break;
    }
  }


}
