#include "AnalogLib.h"
#include "fu.h"
#include "connection.h"
#include "calib_util.h"
#include <float.h>


namespace cutil {

  void initialize(calibrate_t& cal){
    cal.success = true;
    cal.nconns = 0;
  }

  dac_code_t make_low_dac(calibrate_t& calib,
                          Fabric::Chip::Tile::Slice::Dac* dac){
    dac_code_t backup = dac->m_codes;
    dac_code_t result = dac->m_codes;
    dac->setEnable(true);
    if(!dac->setConstant(0.1)){
      print_log("MULT: cannot set DAC=0.1");
      calib.success = false;
    }
    dac->setRange(RANGE_MED);
    dac->out0->setInv(false);
    if(!dac->calibrateTarget(0.001)){
      print_log("MULT: cannot calibrate DAC=-0.1");
      calib.success = false;
    }
    else{
      print_debug("MULT: CALIBRATED DAC=0.1");
    }
    result = dac->m_codes;
    dac->update(backup);
    return result;

  }
  float h2m_coeff_norec(){
    return 0.9;
  }
  float h2m_coeff(){
    return h2m_coeff_norec();
  }
  mult_code_t make_h2m_mult_norecurse(calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Multiplier * mult){
    mult_code_t backup = mult->m_codes;
    mult_code_t result = mult->m_codes;
    // scale down.
    mult->setEnable(true);
    mult->m_codes.range[in0Id] = RANGE_HIGH;
    mult->m_codes.range[in1Id] = RANGE_MED;
    mult->m_codes.range[out0Id] = RANGE_MED;
    mult->setVga(true);
    mult->setGain(h2m_coeff());
    if(!mult->calibrateTarget(0.01)){
      // formerly was 0.1
      print_log("norecurse: cannot calibrate GAIN=0.1");
      calib.success = false;

    }
    else{
      print_debug("norecurse: CALIBRATED GAIN=0.1");
    }
    result = mult->m_codes;
    mult->update(backup);
    return result;
  }

  mult_code_t make_h2m_mult(calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Multiplier * mult){
    // the recursive one has issues converging, so we have to use the one
    // with less dynamic range
    return make_h2m_mult_norecurse(calib,mult);
  }

  mult_code_t make_h2m_mult_recurse(calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Multiplier * mult){
    mult_code_t backup = mult->m_codes;
    mult_code_t result = mult->m_codes;
    // scale down.
    mult->setEnable(true);
    mult->m_codes.range[in0Id] = RANGE_HIGH;
    mult->m_codes.range[in1Id] = RANGE_MED;
    mult->m_codes.range[out0Id] = RANGE_HIGH;
    mult->setVga(true);
    mult->setGain(0.1);
    if(!mult->calibrateTarget(0.01)){
      // formerly was 0.1
      print_log("recurse: cannot calibrate GAIN=0.1");
      calib.success = false;

    }
    else{
      print_debug("recurse: CALIBRATED GAIN=0.1");
    }
    result = mult->m_codes;
    mult->update(backup);
    return result;
  }
  mult_code_t make_one_mult(calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Multiplier * mult){
    error("unimplemented: one mult");
  }
  dac_code_t make_one_dac(calibrate_t& calib,
                          Fabric::Chip::Tile::Slice::Dac * dac){
    dac_code_t backup = dac->m_codes;
    dac_code_t result = dac->m_codes;
    dac->setEnable(true);
    dac->setRange(RANGE_MED);
    dac->m_codes.const_val = 1.0;
    dac->setConstantCode(255);
    dac->setSource(DSRC_MEM);
    dac->out0->setInv(false);
    if(!dac->calibrateTarget(0.01)){
      print_log("MULT: cannot calibrate DAC=-1");
      calib.success = false;
    }
    else{
      print_debug("MULT: CALIBRATED DAC=1");
    }
    result = dac->m_codes;
    dac->update(backup);
    return result;

  }
  dac_code_t make_zero_dac(calibrate_t& calib,
                           Fabric::Chip::Tile::Slice::Dac * dac){
    dac_code_t backup = dac->m_codes;
    dac_code_t result = dac->m_codes;
    dac->setEnable(true);
    dac->setConstant(0);
    dac->setRange(RANGE_MED);
    dac->out0->setInv(true);
    if(!dac->calibrateTarget(0.01)){
      print_log("MULT: cannot calibrate DAC=0");
      calib.success = false;
    }
    else{
      print_debug("MULT: CALIBRATED DAC=0");
    }
    result = dac->m_codes;
    dac->update(backup);
    return result;
  }
  void buffer_conn(calibrate_t& calib, Fabric::Chip::Connection& conn){
    if(calib.nconns < MAX_CONNS){
      int i = calib.nconns;
      calib.conn_buf[i][0] = conn.sourceIfc;
      calib.conn_buf[i][1] = conn.destIfc;
      calib.nconns += 1;
    }
    else{
      error("ran out of connections.");
    }
  }
  void buffer_conns(calibrate_t& calib,
                    Fabric::Chip::Tile::Slice::FunctionUnit * fo,
                    int n_ins,
                    int n_outs){

    if(n_ins >= 1){
      Fabric::Chip::Connection c_in0 = Fabric::Chip::Connection (fo->in0->userSourceDest,
                                                                 fo->in0);
      if(c_in0.sourceIfc && c_in0.destIfc){
        buffer_conn(calib,c_in0);
      }
    }
    if(n_ins >= 2){
      Fabric::Chip::Connection c_in1 = Fabric::Chip::Connection (fo->in1->userSourceDest,
                                                                 fo->in1);
      if(c_in1.sourceIfc){
        buffer_conn(calib,c_in1);
      }
    }
    if(n_outs >= 1){
      Fabric::Chip::Connection c_out0 = Fabric::Chip::Connection (fo->out0,
                                                                  fo->out0->userSourceDest);
      if(c_out0.destIfc){
        buffer_conn(calib,c_out0);
      }
    }
    if(n_outs >= 2){
      Fabric::Chip::Connection c_out1 = Fabric::Chip::Connection (fo->out1,
                                                                  fo->out1->userSourceDest);
      if(c_out1.destIfc){
        buffer_conn(calib,c_out1);
      }
    }
    if(n_outs >= 3){
      Fabric::Chip::Connection c_out2 = Fabric::Chip::Connection (fo->out2,
                                                                  fo->out2->userSourceDest);
      if(c_out2.destIfc){
        buffer_conn(calib,c_out2);
      }
    }
  }
  void buffer_fanout_conns( calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Fanout* fu){
    buffer_conns(calib,fu,1,3);
  }
  void buffer_mult_conns( calibrate_t& calib,
                          Fabric::Chip::Tile::Slice::Multiplier* fu){
    buffer_conns(calib,fu,2,1);
  }
  void buffer_dac_conns( calibrate_t& calib,
                         Fabric::Chip::Tile::Slice::Dac* fu){
    buffer_conns(calib,fu,0,1);
  }
  void buffer_tileout_conns( calibrate_t& calib,
                             Fabric::Chip::Tile::Slice::TileInOut* fu){
    buffer_conns(calib,fu,1,1);
  }
  void buffer_integ_conns( calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Integrator * fu){
    buffer_conns(calib,fu,1,1);
  }
  void buffer_chipin_conns( calibrate_t& calib,
                             Fabric::Chip::Tile::Slice::ChipInput * fu){
    buffer_conns(calib,fu,1,1);
  }
  void buffer_chipout_conns( calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::ChipOutput * fu){
    buffer_conns(calib,fu,1,0);
  }
  void break_conns(calibrate_t& calib){
    sprintf(FMTBUF, "nconns %d", calib.nconns);
    for(int i=0; i < calib.nconns; i+=1){
      Fabric::Chip::Connection c = Fabric::Chip::Connection(calib.conn_buf[i][0],
                                                            calib.conn_buf[i][1]);
      sprintf(FMTBUF, "break %d", i);
      print_debug(FMTBUF);
      c.brkConn();
    }
  }
  void restore_conns(calibrate_t& calib){
    for(int i=0; i < calib.nconns; i+=1){
      Fabric::Chip::Connection c = Fabric::Chip::Connection(calib.conn_buf[i][0],
                                                            calib.conn_buf[i][1]);
      sprintf(FMTBUF, "restore %d", i);
      print_debug(FMTBUF);
      c.setConn();
    }
  }

}
