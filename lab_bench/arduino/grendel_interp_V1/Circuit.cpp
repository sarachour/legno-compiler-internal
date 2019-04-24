//#define _DUE
#include "AnalogLib.h"
#include "Circuit.h"
#include "Calibrate.h"
#include "Comm.h"
#include "Common.h"
#include <assert.h>

char HCDC_DEMO_BOARD = 6;
//char HCDC_DEMO_BOARD = 4;


namespace circ {

bool caltbl[2][4][4];


void init_calibrations(){
  for(int chipno=0; chipno < 2; chipno ++){
    for(int tileno = 0; tileno < 4; tileno ++){
      for(int sliceno = 0; sliceno < 4; sliceno ++){
        caltbl[chipno][tileno][sliceno] = false;
      }
    }
  }
}

bool do_calibrate(int chipno, int tileno, int sliceno){
  if(not caltbl[chipno][tileno][sliceno]){
    caltbl[chipno][tileno][sliceno] = true;
    return true;
  }
  else{
    comm::print_header();
    Serial.println("-> skipping calibration");
    return false;
  }
}



void load_range(uint8_t range, bool * lo, bool * hi){
  switch(range){
    case LOW_RANGE:
      *lo = true;
      *hi = false;
      break;
    case MED_RANGE:
      *lo = false;
      *hi = false;
      break;
    case HI_RANGE:
      *lo = false;
      *hi = true;
      break;
    default:
      comm::error("[ERROR] unknown range");
      break;
  }
  
}

void load_dac_source(uint8_t source, bool * mem, bool * ext,
                     bool * lut0, bool * lut1){
  *lut0 = false;
  *lut1 = false;
  *mem = false;
  *ext = false;
  switch(source){
    case circ::DS_MEM:
      *mem = true;
      break;
    case circ::DS_EXT:
      *ext = true;
      break;
    case circ::DS_LUT0:
      *lut0 = true;
      break;
    case circ::DS_LUT1:
      *lut1 = true;
      break;
    default:
      comm::error("[ERROR] unknown source");
  }
}

void load_lut_source(uint8_t source, bool * ext, bool * adc0, bool * adc1){
  *adc0 = false;
  *adc1 = false;
  *ext = false;
  switch(source){
    case circ::LS_EXT:
      *ext = true;
      break;
    case circ::LS_ADC0:
      *adc0 = true;
      break;
    case circ::LS_ADC1:
      *adc1 = true;
      break;
    default:
      comm::error("[ERROR] unknown source");
  }
}


Fabric* setup_board(){
  Fabric* fabric = new Fabric();
  return fabric;
}


void exec_command(Fabric * fab, cmd_t& cmd, float* inbuf){
  cmd_use_dac_t dacd;
  cmd_use_mult_t multd;
  cmd_use_fanout_t fod;
  cmd_use_integ_t integd;
  cmd_use_lut_t lutd;
  cmd_write_lut_t wrlutd;
  cmd_use_adc_t adcd;
  cmd_connection_t connd;
  bool lo1,hi1;
  bool lo2,hi2;
  bool lo3,hi3;
  bool s1,s2,s3,s4;
  uint8_t byteval;
  char buf[16];
  Fabric::Chip::Tile::Slice* slice;
  Fabric::Chip::Tile::Slice::Dac* dac;
  Fabric::Chip::Tile::Slice::Multiplier * mult;
  Fabric::Chip::Tile::Slice::Fanout * fanout;
  Fabric::Chip::Tile::Slice::Integrator* integ;
  Fabric::Chip::Tile::Slice::LookupTable* lut;
  Fabric::Chip::Tile::Slice::ChipAdc * adc;
  Fabric::Chip::Tile::Slice::FunctionUnit::Interface* src;
  Fabric::Chip::Tile::Slice::FunctionUnit::Interface* dst;
  switch(cmd.type){
  case cmd_type_t::CONFIG_DAC:
    dacd = cmd.data.dac;
    dac = common::get_slice(fab,dacd.loc)->dac;
    load_range(dacd.out_range, &lo1, &hi1);
    if(dacd.source == circ::dac_source::DS_MEM){
      comm::test(dac->setConstantDirect(dacd.value,hi1,true),
                 "failed to configure dac value");
    }
    comm::response("configured dac (direct)",0);
    break;
  case cmd_type_t::USE_ADC:
    adcd = cmd.data.adc;
    adc = common::get_slice(fab,adcd.loc)->adc;
    adc->setEnable(true);
    load_range(adcd.in_range, &lo1, &hi1);
    adc->setHiRange(hi1);
    comm::response("enabled adc",0);
    break;
  case cmd_type_t::USE_DAC:
    dacd = cmd.data.dac;
    dac = common::get_slice(fab,dacd.loc)->dac;
    dac->setEnable(true);
    dac->out0->setInv(dacd.inv);
    load_range(dacd.out_range, &lo1, &hi1);
    dac->setHiRange(hi1);
    load_dac_source(dacd.source, &s1, &s2, &s3, &s4);
    dac->setSource(s1,s2,s3,s4);
    if(dacd.source == circ::dac_source::DS_MEM){
      comm::test(dac->setConstantDirect(dacd.value,hi1,false), 
                 "failed to set dac value");
    }
    comm::response("enabled dac",0);
    break;
  case cmd_type_t::CONFIG_MULT:
    // multiplier doesn't actually support inversion
    // multiplier uses dac from same row.
    multd = cmd.data.mult;
    mult = common::get_mult(fab,multd.loc);
    if(multd.use_coeff){
      // determine if we're in the high or low output range.
      load_range(multd.out_range, &lo1, &hi1);
      comm::test(mult->setGainDirect(multd.coeff, hi1, true),
                 "failed to set gain");
    }
    comm::response("configured mult [direct]",0);
    break;
  case cmd_type_t::USE_MULT:
    // multiplier doesn't actually support inversion
    // multiplier uses dac from same row.
    multd = cmd.data.mult;
    mult = common::get_mult(fab,multd.loc);
    mult->setEnable(true);
    mult->setVga(multd.use_coeff);
    load_range(multd.in0_range, &lo1, &hi1);
    load_range(multd.in1_range, &lo2, &hi2);
    load_range(multd.out_range, &lo3, &hi3);
    mult->in0->setRange(lo1,hi1);
    mult->out0->setRange(lo3,hi3);
    if(not multd.use_coeff){
      mult->in1->setRange(lo2,hi2);
    }
    else{
      comm::test(mult->setGainDirect(multd.coeff, hi3, false),
                 "failed to set gain");
    }
    comm::response("enabled mult",0);
    break;
  case cmd_type_t::USE_FANOUT:
    fod = cmd.data.fanout;
    fanout = common::get_fanout(fab,fod.loc);
    fanout->setEnable(true);
    load_range(fod.in_range, &lo1, &hi1);
    assert(!lo1);
    fanout->setHiRange(hi1);
    fanout->out0->setInv(fod.inv[0]);
    fanout->out1->setInv(fod.inv[1]);
    fanout->out2->setInv(fod.inv[2]);
    comm::response("enabled fanout",0);
    break;
  case cmd_type_t::CONFIG_INTEG:
    integd = cmd.data.integ;
    integ = common::get_slice(fab,integd.loc)->integrator;
    load_range(integd.out_range, &lo1, &hi1);
    comm::test(integ->setInitialDirect(integd.value, hi1, true),
               "failed to set integ value");
    comm::response("configured integ [direct]",0);
    break;
  case cmd_type_t::USE_INTEG:
    integd = cmd.data.integ;
    integ = common::get_slice(fab,integd.loc)->integrator;
    integ->setEnable(true);
    integ->setException( integd.debug == 1 ? true : false);
    integ->out0->setInv(integd.inv);
    load_range(integd.in_range, &lo1, &hi1);
    load_range(integd.out_range, &lo2, &hi2);
    integ->in0->setRange(lo1,hi1);
    integ->out0->setRange(lo2,hi2);
    comm::test(integ->setInitialDirect(integd.value, hi2, false),
               "failed to set integ value");
    comm::response("enabled integ",0);
    break;
  case cmd_type_t::GET_INTEG_STATUS:
    integ = common::get_slice(fab,cmd.data.circ_loc)->integrator;
    comm::response("retrieved integ exception",1);
    comm::data(integ->getException() ? "1" : "0", "i");
    break;
  case cmd_type_t::GET_ADC_STATUS:
    adc = common::get_slice(fab,cmd.data.circ_loc)->adc;
    comm::response("retrieved  lut exception",1);
    sprintf(buf,"%d",adc->getStatusCode());
    comm::data(buf, "i");
    break;
  case cmd_type_t::USE_LUT:
    lutd = cmd.data.lut;
    lut = common::get_slice(fab,lutd.loc)->lut;
    load_lut_source(lutd.source, &s1, &s2, &s3);
    lut->setSource(s1,s2,s3);
    comm::response("use lut",0);
    break;
  case cmd_type_t::WRITE_LUT:
    wrlutd = cmd.data.write_lut;
    lut = common::get_slice(fab,wrlutd.loc)->lut;
    for(int data_idx=0; data_idx < wrlutd.n; data_idx+=1){
      byteval = round(inbuf[data_idx]*128.0 + 128.0);
      comm::print_header();
      Serial.print(data_idx+wrlutd.offset);
      Serial.print("=");
      Serial.print(inbuf[data_idx]);
      Serial.print("; ");
      Serial.println(byteval);
      if(inbuf[data_idx] < -1.0 || inbuf[data_idx] > 1.0){
        comm::error("lut value not in <-1,1>");
      }
      lut->setLut(wrlutd.offset+data_idx,byteval);
    }
    comm::response("write lut",0);
    break;
  case cmd_type_t::DISABLE_DAC:
    dac = common::get_slice(fab,cmd.data.circ_loc)->dac;
    dac->setEnable(false);
    comm::response("disabled dac",0);
    break;
  case cmd_type_t::DISABLE_ADC:
    adc = common::get_slice(fab,cmd.data.circ_loc)->adc;
    adc->setEnable(false);
    comm::response("disabled adc",0);
    break;
  case cmd_type_t::DISABLE_LUT:
    lut = common::get_slice(fab,cmd.data.circ_loc)->lut;
    //lut->setEnable(false);
    comm::response("disabled lut",0);
    break;
  case cmd_type_t::DISABLE_MULT:
    multd = cmd.data.mult;
    mult = common::get_mult(fab,multd.loc);
    mult->setEnable(false);
    comm::response("disabled mult",0);
    break;
  case cmd_type_t::DISABLE_FANOUT:
    fod = cmd.data.fanout;
    fanout = common::get_fanout(fab,fod.loc);
    fanout->setEnable(false);
    comm::response("disabled fanout",0);
    break;
  case cmd_type_t::DISABLE_INTEG:
    integd = cmd.data.integ;
    integ = common::get_slice(fab,integd.loc)->integrator;
    integ->setEnable(false);
    comm::response("disabled integ",0);
    break;
  case cmd_type_t::CONNECT:
    connd = cmd.data.conn;
    src = common::get_output_port(fab,connd.src_blk,connd.src_loc);
    dst = common::get_input_port(fab,connd.dst_blk,connd.dst_loc);
    Fabric::Chip::Connection(src,dst).setConn();
    comm::response("connected",0);
    break;
  case cmd_type_t::BREAK:
    connd = cmd.data.conn;
    src = common::get_output_port(fab,connd.src_blk,connd.src_loc);
    dst = common::get_input_port(fab,connd.dst_blk,connd.dst_loc);
    Fabric::Chip::Connection(src,dst).brkConn();
    comm::response("disconnected",0);
    break;
  case cmd_type_t::CALIBRATE:
    slice = common::get_slice(fab,cmd.data.circ_loc);
    if(do_calibrate(cmd.data.circ_loc.chip,
                    cmd.data.circ_loc.tile,
                    cmd.data.circ_loc.slice)){
      comm::test(slice->calibrate(), "calibration failed");
    }
    else{
      comm::print_header();
      Serial.println("skipping calibration.");
      Serial.flush();
    }
    comm::response("calibrated",0);
    break;
  case cmd_type_t::GET_CODES:
    calibrate::get_codes(fab,
                         cmd.data.codes.blk,
                         cmd.data.codes.loc,
                         cmd.data.codes.port_type,
                         cmd.data.codes.range,
                         buf);
    comm::response("returning codes",1);
    comm::data("16","I");
    comm::payload();
    for(int i=0; i < 16; i+=1){
      Serial.print(" ");
      Serial.print((uint8_t) buf[i]);
    }
    Serial.println("");
    break;
  default:
    comm::error("unknown command");
    break;
  }
}




}


