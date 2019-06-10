#include "AnalogLib.h"
#include "fu.h"
#include "calib_util.h"
#include <float.h>


float compute_in0(mult_code_t& m_codes,float in0){
  return in0*util::range_to_coeff(m_codes.range[in0Id]);
}
float compute_in1(mult_code_t& m_codes, float in1){
  return in1*util::range_to_coeff(m_codes.range[in1Id]);
}
float compute_out_mult(mult_code_t& m_codes, float in0, float in1){
  float sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  float rng = util::range_to_coeff(m_codes.range[out0Id]);
  rng *= 1.0/util::range_to_coeff(m_codes.range[in0Id]);
  rng *= 1.0/util::range_to_coeff(m_codes.range[in1Id]);
  sprintf(FMTBUF,"range=%f (%f,%f,out=%f)",rng,
          util::range_to_coeff(m_codes.range[in0Id]),
          util::range_to_coeff(m_codes.range[in1Id]),
          util::range_to_coeff(m_codes.range[out0Id])
          ); print_info(FMTBUF);
  sprintf(FMTBUF,"sign=%f",sign); print_info(FMTBUF);
  sprintf(FMTBUF,"in0=%f",compute_in0(m_codes,in0)); print_info(FMTBUF);
  sprintf(FMTBUF,"in1=%f",compute_in1(m_codes,in1)); print_info(FMTBUF);
  return rng*sign*compute_in0(m_codes,in0)*compute_in1(m_codes,in1);
}

float compute_out_vga(mult_code_t& m_codes, float in0){
  float gain = m_codes.gain_val;
  float sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  float rng = util::range_to_coeff(m_codes.range[out0Id]);
  rng *= 1.0/util::range_to_coeff(m_codes.range[in0Id]);
  return gain*rng*sign*compute_in0(m_codes,in0);
}

float compute_out(mult_code_t& m_codes, float in0, float in1){
  if(m_codes.vga){
    return compute_out_vga(m_codes,in0);
  }
  else{
    return compute_out_mult(m_codes,in0,in1);
  }
}
bool Fabric::Chip::Tile::Slice::Multiplier::calibrate (profile_t& result, float max_error) {
  mult_code_t codes_self = m_codes;
  if(m_codes.vga)
    setGain(1.0);
  bool succ = calibrateTarget(result,max_error);
  codes_self.nmos = m_codes.nmos;
  codes_self.pmos = m_codes.pmos;
  codes_self.port_cal[in0Id] = m_codes.port_cal[in0Id];
  codes_self.port_cal[in1Id] = m_codes.port_cal[in1Id];
  codes_self.port_cal[out0Id] = m_codes.port_cal[out0Id];
  codes_self.gain_cal = m_codes.gain_cal;
  update(codes_self);
	return succ;
}

bool helper_find_port_cal_out0(Fabric::Chip::Tile::Slice::Dac* dac,
                               Fabric::Chip::Tile::Slice::Multiplier* mult,
                               float max_error){
  float delta;
  bool calib_failed;
  //out0Id
  mult->setGain(0.0);
  mult->setVga(true);
  dac->setEnable(false);
  binsearch::find_bias(mult, 0.0,
                       mult->m_codes.port_cal[out0Id],
                       delta,
                       MEAS_CHIP_OUTPUT);
  // update nmos code
  binsearch::test_stab(mult->m_codes.port_cal[out0Id],fabs(delta),
                       max_error,calib_failed);

  sprintf(FMTBUF, "calibrate out0 target=%f meas=%f max=%f succ=%s",
          0.0,
          delta,
          max_error,
          calib_failed ? "no" : "yes");
  print_log(FMTBUF);
  return !calib_failed;

}


bool helper_find_port_cal_in0(Fabric::Chip::Tile::Slice::Dac* dac,
                              Fabric::Chip::Tile::Slice::Multiplier* mult,
                              float max_error){
  float delta;
  bool calib_failed;
  mult->setGain(1.0);
  mult->setVga(true);
  dac->setEnable(false);
  binsearch::find_bias(mult, 0.0,
                       mult->m_codes.port_cal[in0Id],
                       delta,
                       MEAS_CHIP_OUTPUT);

  // update nmos code
  binsearch::test_stab(mult->m_codes.port_cal[in0Id],fabs(delta),
                       max_error,calib_failed);

  sprintf(FMTBUF, "calibrate in0 target=%f meas=%f max=%f succ=%s",
          0.0,
          delta,
          max_error,
          calib_failed ? "no" : "yes");
  print_log(FMTBUF);

  return !calib_failed;
}

bool helper_find_port_cal_in1(Fabric::Chip::Tile::Slice::Dac* dac,
                              Fabric::Chip::Tile::Slice::Multiplier* mult,
                              dac_code_t& dac_code_0,
                              float max_error){
  //in1id
  /* find bias by minimizing error of 0*0 */
  float delta;
  bool calib_failed;
  Fabric::Chip::Connection conn_in1 = \
    Fabric::Chip::Connection (dac->out0, mult->in0);
  mult->setVga(false);
  dac->update(dac_code_0);
  dac->setEnable(true);
  conn_in1.setConn();
  binsearch::find_bias(mult, 0.0,
                       mult->m_codes.port_cal[in1Id],
                       delta,
                       MEAS_CHIP_OUTPUT);
  // update nmos code
  binsearch::test_stab(mult->m_codes.port_cal[in1Id],fabs(delta),
                       max_error,calib_failed);
  sprintf(FMTBUF, "calibrate in1 target=%f meas=%f max=%f succ=%s",
          0.0,
          delta,
          max_error,
          calib_failed ? "no" : "yes");
  print_log(FMTBUF);
  conn_in1.brkConn();
  dac->setEnable(false);
  return !calib_failed;

}

// TODO: write utility functions for calibrating input*input multiplier
bool helper_find_max_val(Fabric::Chip::Tile::Slice::Multiplier* mult,
                         Fabric::Chip::Tile::Slice::Dac* ref_dac,
                         dac_code_t& dref_targ_full,
                         dac_code_t& dref_targ_half,
                         float ref_full,
                         float ref_half,
                         Fabric::Chip::Tile::Slice::Dac* val1_dac,
                         dac_code_t& dval1_full,
                         dac_code_t& dval1_half,
                         Fabric::Chip::Tile::Slice::Dac* val2_dac,
                         dac_code_t& dval2_full,
                         dac_code_t& dval2_half,
                         float max_error){
  Fabric::Chip::Connection conn_in0 =
    Fabric::Chip::Connection(val1_dac->out0, mult->in0);
  Fabric::Chip::Connection conn_in1 =
    Fabric::Chip::Connection(val2_dac->out0, mult->in1);

  ref_dac->update(dref_targ_full);
  val1_dac->update(dval1_full);
  val2_dac->update(dval2_full);
  conn_in0.setConn();
  conn_in1.setConn();
  mult->setVga(false);
  float measurement = util::meas_chip_out(mult);
  float target = compute_out(mult->m_codes,1.0,1.0);
  float error = fabs((target+ref_full)-measurement);
  sprintf(FMTBUF, "calibrate-pmos target=%f ref=%f meas=%f error=%f",
          target,
          ref_full,
          measurement,
          error);
  print_log(FMTBUF);
  conn_in0.brkConn();
  conn_in1.brkConn();
  return error <= max_error;
}

bool helper_find_gain_cal(Fabric::Chip::Tile::Slice::Multiplier* mult,
                          Fabric::Chip::Tile::Slice::Dac* ref_dac,
                          dac_code_t& dref_targ_full,
                          dac_code_t& dref_targ_half,
                          float ref_full,
                          float ref_half,
                          Fabric::Chip::Tile::Slice::Dac* val_dac,
                          dac_code_t& dval_full,
                          dac_code_t& dval_half,
                          float max_error){

  Fabric::Chip::Connection dac_to_mult_in0 =
    Fabric::Chip::Connection ( val_dac->out0, mult->in0 );
  bool calib_failed;
  val_dac->setEnable(true);
  val_dac->update(dval_full);
  ref_dac->update(dref_targ_full);
  mult->setVga(true);
  mult->setGain(mult->m_codes.gain_val);
  dac_to_mult_in0.setConn();
  float error;
  bool succ = true;
  float target = compute_out(mult->m_codes,1.0,1.0)+ref_full;
  binsearch::find_bias(mult,target,
                       mult->m_codes.gain_cal,
                       error,
                       MEAS_CHIP_OUTPUT);
  // update nmos code
  binsearch::test_stab(mult->m_codes.gain_cal,
                       fabs(error),
                       max_error,
                       calib_failed);
  succ &= !calib_failed;
  sprintf(FMTBUF, "calibrate full gain=%f target=%f meas=%f max=%f succ=%s",
          mult->m_codes.gain_val,
          target,
          target+error,
          max_error,
          calib_failed ? "no" : "yes");
  print_log(FMTBUF);

  // compute fidelity at midpoint. If this is truly an appropriate gain,
  // it should be able to compute the gain at another value.
  val_dac->update(dval_half);
  ref_dac->update(dref_targ_half);
  target = compute_out(mult->m_codes,0.5,0.5)+ref_half;
  error = util::meas_chip_out(mult) - target;
  binsearch::test_stab(mult->m_codes.gain_cal,
                       fabs(error),
                       max_error,
                       calib_failed);
  succ &= !calib_failed;
  sprintf(FMTBUF, "calibrate half gain=%f target=%f meas=%f max=%f succ=%s",
          mult->m_codes.gain_val,
          target,
          target+error,
          max_error,
          calib_failed ? "no" : "yes");

  print_log(FMTBUF);
  print_log("---");
  dac_to_mult_in0.brkConn();
  return succ;
}

bool helper_find_pmos_mult(Fabric::Chip::Tile::Slice::Multiplier* mult,
                           Fabric::Chip::Tile::Slice::Dac* ref_dac,
                           dac_code_t& dref_targ_full,
                           dac_code_t& dref_targ_half,
                           float ref_full,
                           float ref_half,
                           Fabric::Chip::Tile::Slice::Dac* val1_dac,
                           dac_code_t& dval1_full,
                           dac_code_t& dval1_half,
                           Fabric::Chip::Tile::Slice::Dac* val2_dac,
                           dac_code_t& dval2_full,
                           dac_code_t& dval2_half,
                           float max_error){

  float error = 0.04;
  if(mult->m_codes.range[out0Id] == RANGE_HIGH){
    error *= 10.0;
  }
  for(int pmos=0; pmos<=7; pmos+=1){
    sprintf(FMTBUF,"mult pmos=%d",pmos);
    print_info(FMTBUF);
    mult->m_codes.pmos = pmos;
    mult->update(mult->m_codes);
    bool succ = helper_find_max_val(mult,
                                    ref_dac,
                                    dref_targ_full,
                                    dref_targ_half,
                                    ref_full,
                                    ref_half,
                                    val1_dac,
                                    dval1_full,
                                    dval1_half,
                                    val2_dac,
                                    dval2_full,
                                    dval2_half,
                                    error);
    if(succ)
      return true;
  }
  return false;
}


bool helper_find_pmos_vga(Fabric::Chip::Tile::Slice::Multiplier* mult,
                          Fabric::Chip::Tile::Slice::Dac* ref_dac,
                          dac_code_t& dref_targ_full,
                          dac_code_t& dref_targ_half,
                          float ref_full,
                          float ref_half,
                          Fabric::Chip::Tile::Slice::Dac* val1_dac,
                          dac_code_t& dval1_full,
                          dac_code_t& dval1_half,
                          float max_error){

  for(int pmos=0; pmos<=7; pmos+=1){
    sprintf(FMTBUF,"vga pmos=%d",pmos);
    print_info(FMTBUF);
    mult->m_codes.pmos = pmos;
    mult->update(mult->m_codes);
    bool succ = helper_find_gain_cal(mult,
                                     ref_dac,
                                     dref_targ_full,
                                     dref_targ_half,
                                     ref_full,
                                     ref_half,
                                     val1_dac,
                                     dval1_full,
                                     dval1_half,
                                     max_error);
    if(succ){
      return true;
    }
  }
  return false;
}

bool helper_find_pmos(Fabric::Chip::Tile::Slice::Multiplier* mult,
                      Fabric::Chip::Tile::Slice::Dac* ref_dac,
                      dac_code_t& dref_targ_full,
                      dac_code_t& dref_targ_half,
                      float ref_full,
                      float ref_half,
                      Fabric::Chip::Tile::Slice::Dac* val1_dac,
                      dac_code_t& dval1_full,
                      dac_code_t& dval1_half,
                      Fabric::Chip::Tile::Slice::Dac* val2_dac,
                      dac_code_t& dval2_full,
                      dac_code_t& dval2_half,
                      float max_error)
{
  if(mult->m_codes.vga){
    return helper_find_pmos_vga(mult,
                                ref_dac,
                                dref_targ_full,
                                dref_targ_half,
                                ref_full,
                                ref_half,
                                val1_dac,
                                dval1_full,
                                dval1_half,
                                max_error);
  }
  else{
    return helper_find_pmos_mult(mult,
                                 ref_dac,
                                 dref_targ_full,
                                 dref_targ_half,
                                 ref_full,
                                 ref_half,
                                 val1_dac,
                                 dval1_full,
                                 dval1_half,
                                 val2_dac,
                                 dval2_full,
                                 dval2_half,
                                 max_error);
  }

}

bool Fabric::Chip::Tile::Slice::Multiplier::calibrateTarget (profile_t& result, float max_error) {
  if(!m_codes.enable){
    print_log("not enabled");
    return true;
  }
  int cFanId = unitId==unitMulL?0:1;

  int next_slice1 = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  int next_slice2 = (slice_to_int(parentSlice->sliceId) + 2) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice1].dac;
  Dac * val1_dac = parentSlice->dac;
  Dac * val2_dac = parentSlice->parentTile->slices[next_slice2].dac;
  cutil::calibrate_t calib;
  cutil::initialize(calib);
  // backup state of each component that will be clobbered
  mult_code_t codes_self = m_codes;
  dac_code_t codes_val1 = val1_dac->m_codes;
  dac_code_t codes_val2 = val2_dac->m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;

  // backup connections
  cutil::buffer_mult_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_dac_conns(calib,val1_dac);
  cutil::buffer_dac_conns(calib,val2_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile
                              ->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  Connection mult_to_tileout = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection tileout_to_chipout = Connection ( parentSlice->tileOuts[3].out0,
                                               parentSlice->parentTile
                                               ->parentChip->tiles[3].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection ref_to_tileout =
    Fabric::Chip::Connection ( ref_dac->out0, parentSlice->tileOuts[3].in0);

  mult_to_tileout.setConn();
	tileout_to_chipout.setConn();

  dac_code_t dval1_0;
  dac_code_t dval2_0;
  dac_code_t dval1_full;
  dac_code_t dval1_half;
  dac_code_t dval2_full;
  dac_code_t dval2_half;
  dac_code_t dref_targ_full; // reference signal, for full range
  dac_code_t dref_targ_half; // reference signal, for half range
  float ref_full,ref_half;


  float target = compute_out(m_codes,1.0,1.0);
  float half = m_codes.vga ? 0.5 : 0.25;
  dref_targ_full = cutil::make_ref_dac(calib,
                                        ref_dac,
                                        -target,
                                        ref_full);
  dref_targ_half = cutil::make_ref_dac(calib,
                                        ref_dac,
                                        -target*half,
                                        ref_half);
  sprintf(FMTBUF, "target full=%f half=%f ref-full=%f ref-half=%f",
          target, target*half,ref_full,ref_half);
  print_info(FMTBUF);
  prof::init_profile(prof::TEMP);
  dval1_0 = cutil::make_zero_dac(calib,val1_dac,
                                   prof::TEMP);

  prof::init_profile(prof::TEMP);
  dval1_full = cutil::make_val_dac(calib,
                                   val1_dac,compute_in0(m_codes,1.0),
                                   prof::TEMP);
  prof::init_profile(prof::TEMP);
  dval1_half= cutil::make_val_dac(calib,
                                  val1_dac,compute_in0(m_codes,0.5),
                                  prof::TEMP);
  if(!m_codes.vga){
    prof::init_profile(prof::TEMP);
    dval2_half= cutil::make_val_dac(calib,
                                    val2_dac,compute_in1(m_codes,0.5),
                                    prof::TEMP);
    prof::init_profile(prof::TEMP);
    dval2_full = cutil::make_val_dac(calib,
                                     val2_dac,compute_in1(m_codes,1.0),
                                     prof::TEMP);
  }

  bool found_code = false;
  mult_code_t best_code = m_codes;
	m_codes.nmos = 0;
	setAnaIrefNmos ();
  print_info("=== calibrate multiplier ===");
	do {
    if(found_code){
      break;
    }
    bool succ = true;
    //calibrate bias, no external input
    sprintf(FMTBUF, "execute nmos=%d", m_codes.nmos);
    print_info(FMTBUF);
    succ &= helper_find_port_cal_out0(val1_dac, this,max_error);
    if(succ)
      succ &= helper_find_port_cal_in0(val1_dac, this,max_error);
    if(succ)
      succ &= helper_find_port_cal_in1(val1_dac, this,dval1_0,max_error);

    if(succ){
      m_codes.vga = codes_self.vga;
      ref_to_tileout.setConn();
      if(m_codes.vga){
        setGain(codes_self.gain_val);
      }
      succ &= helper_find_pmos(this,
                               ref_dac,
                               dref_targ_full,
                               dref_targ_half,
                               ref_full,
                               ref_half,
                               val1_dac,
                               dval1_full,
                               dval1_half,
                               val2_dac,
                               dval2_full,
                               dval2_half,
                               max_error);
      ref_to_tileout.brkConn();
    }
    if(succ){
      best_code = m_codes;
      found_code = true;
    }
    parentSlice->dac->setEnable(false);

    m_codes.nmos += 1;
    if(m_codes.nmos <= 7){
      setAnaIrefNmos ();
    }
	} while (m_codes.nmos <= 7 && !found_code);
  // update the result to use the best code.
  m_codes = best_code;
  update(m_codes);
	/*teardown*/
	tileout_to_chipout.brkConn();
	mult_to_tileout.brkConn();
  cutil::restore_conns(calib);

  codes_self.nmos = best_code.nmos;
  codes_self.pmos = best_code.pmos;
  codes_self.port_cal[in0Id] = best_code.port_cal[in0Id];
  codes_self.port_cal[in1Id] = best_code.port_cal[in1Id];
  codes_self.port_cal[out0Id] = best_code.port_cal[out0Id];
  codes_self.gain_cal = best_code.gain_cal;

  val1_dac->update(codes_val1);
  val2_dac->update(codes_val2);
  ref_dac->update(codes_ref);
  update(codes_self);

	return found_code && calib.success;
}
