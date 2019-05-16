//#define _DUE
#include "AnalogLib.h"
#include "Circuit.h"
#include "Calibrate.h"
#include "Comm.h"
#include "Common.h"
#include "calib_util.h"
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
  block_code_t state;
  util::ser_calib_result_t result;
  uint8_t byteval;
  char buf[32];
  bool succ;
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
  case cmd_type_t::USE_ADC:
    adcd = cmd.data.adc;
    adc = common::get_slice(fab,adcd.loc)->adc;
    adc->setEnable(true);
    adc->setRange((range_t) adcd.in_range);
    comm::response("enabled adc",0);
    break;
  case cmd_type_t::USE_DAC:
    dacd = cmd.data.dac;
    dac = common::get_slice(fab,dacd.loc)->dac;
    dac->setEnable(true);
    dac->out0->setInv(dacd.inv);
    dac->setRange((range_t) dacd.out_range);
    dac->setSource((dac_source_t) dacd.source);
    if(dacd.source == DSRC_MEM){
      comm::test(dac->setConstant(dacd.value),
                 "failed to set dac value");
    }
    comm::response("enabled dac",0);
    break;

  case cmd_type_t::USE_MULT:
    // multiplier doesn't actually support inversion
    // multiplier uses dac from same row.
    multd = cmd.data.mult;
    mult = common::get_mult(fab,multd.loc);
    mult->setEnable(true);
    mult->setVga(multd.use_coeff);
    mult->in0->setRange((range_t) multd.in0_range);
    mult->out0->setRange((range_t) multd.out_range);
    if(not multd.use_coeff){
      mult->in1->setRange((range_t) multd.in1_range);
    }
    else{
      comm::test(mult->setGain(multd.coeff),
                 "failed to set gain");
    }
    comm::response("enabled mult",0);
    break;
  case cmd_type_t::USE_FANOUT:
    fod = cmd.data.fanout;
    fanout = common::get_fanout(fab,fod.loc);
    fanout->setEnable(true);
    fanout->setRange((range_t) fod.in_range);
    fanout->out0->setInv(fod.inv[0]);
    fanout->out1->setInv(fod.inv[1]);
    fanout->out2->setInv(fod.inv[2]);
    fanout->setThird(fod.third);
    comm::response("enabled fanout",0);
    break;

  case cmd_type_t::USE_INTEG:
    integd = cmd.data.integ;
    integ = common::get_slice(fab,integd.loc)->integrator;
    integ->setEnable(true);
    integ->setException( integd.debug == 1 ? true : false);
    integ->out0->setInv(integd.inv);
    integ->in0->setRange((range_t) integd.in_range);
    integ->out0->setRange((range_t) integd.out_range);
    comm::test(integ->setInitial(integd.value),
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
    lut->setSource((lut_source_t) lutd.source);
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

  case cmd_type_t::CHARACTERIZE:
    util::init_result(result.result);
    //calibrate::characterize(fab,
    //                            result.result,
    //                           cmd.data.calib.blk,
    //                          cmd.data.calib.loc);
    calibrate::get_codes(fab,
                         cmd.data.state.blk,
                         cmd.data.state.loc,
                         state);
    comm::response("characterization terminated",1);
    sprintf(FMTBUF,"result=%d state=%d",sizeof(result.result), sizeof(state));
    print_log(FMTBUF);
    sprintf(FMTBUF,"%d",sizeof(state)+sizeof(result.result)+2);
    comm::data(FMTBUF,"I");
    comm::payload();
    Serial.print(sizeof(state));
    Serial.print(" ");
    Serial.print(sizeof(result.result));
    for(int i=0; i < sizeof(state); i+=1){
      Serial.print(" ");
      Serial.print(state.charbuf[i]);
    }
    for(int i=0; i < sizeof(result.result); i+=1){
      Serial.print(" ");
      Serial.print(result.charbuf[i]);
    }
    Serial.println("");
    break;


  case cmd_type_t::CALIBRATE:
    succ = calibrate::calibrate(fab,
                                result.result,
                                cmd.data.calib.blk,
                                cmd.data.calib.loc,
                                cmd.data.calib.max_error);
    calibrate::get_codes(fab,
                         cmd.data.state.blk,
                         cmd.data.state.loc,
                         state);
    comm::response("calibration terminated",1);
    sprintf(FMTBUF,"%d",sizeof(state)+2);
    comm::data(FMTBUF,"I");
    comm::payload();
    Serial.print(sizeof(state));
    Serial.print(" ");
    Serial.print(succ ? 1 : 0);
    for(int i=0; i < sizeof(state); i+=1){
      Serial.print(" ");
      Serial.print(state.charbuf[i]);
    }
    Serial.println("");
    break;

  case cmd_type_t::GET_STATE:
    calibrate::get_codes(fab,
                         cmd.data.state.blk,
                         cmd.data.state.loc,
                         state);
    comm::response("returning codes",1);
    sprintf(FMTBUF,"%d",sizeof(state)+1);
    comm::data(FMTBUF,"I");
    comm::payload();
    Serial.print(sizeof(state));
    for(int i=0; i < sizeof(state); i+=1){
      Serial.print(" ");
      Serial.print(state.charbuf[i]);
    }
    Serial.println("");
    break;
  case cmd_type_t::SET_STATE:
    memcpy(state.charbuf,
           cmd.data.state.data,
           sizeof(block_code_t));
    calibrate::set_codes(fab,
                         cmd.data.state.blk,
                         cmd.data.state.loc,
                         state);
    comm::response("set codes",0);
    break;

  case cmd_type_t::DEFAULTS:
    comm::print_header();
    Serial.println("setting to default");
    fab->defaults();
    comm::response("set defaults",0);
    break;

  default:
    comm::error("unknown command");
    break;
  }
}




}


