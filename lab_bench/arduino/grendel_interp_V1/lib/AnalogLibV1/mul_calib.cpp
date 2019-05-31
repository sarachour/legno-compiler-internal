#include "AnalogLib.h"
#include "fu.h"
#include "calib_util.h"
#include <float.h>


bool Fabric::Chip::Tile::Slice::Multiplier::calibrate (profile_t& result, float max_error) {
  mult_code_t codes_self = m_codes;
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



bool helper_find_gain_cal(float gain,
                          Fabric::Chip::Tile::Slice::Multiplier* mult,
                          Fabric::Chip::Tile::Slice::Dac* val_dac,
                          Fabric::Chip::Tile::Slice::Dac* ref_dac,
                          Fabric::Chip::Tile::Slice::TileInOut* tileout,
                          bool hiRange,
                          float target,
                          dac_code_t& dac_ref_target,
                          dac_code_t& dac_ref_target_half,
                          dac_code_t& dac_code_0_1,
                          dac_code_t& dac_code_0_05,
                          dac_code_t& dac_code_1,
                          dac_code_t& dac_code_0_5,
                          float max_error){

	Fabric::Chip::Connection ref_to_tileout = Fabric::Chip::Connection ( ref_dac->out0, tileout->in0 );
  Fabric::Chip::Connection dac_to_mult_in0 = Fabric::Chip::Connection ( val_dac->out0, mult->in0 );
  bool calib_failed;
  val_dac->setEnable(true);
  if(mult->m_codes.range[in0Id] == RANGE_LOW){
    val_dac->update(dac_code_0_1);
  }
  else{
    val_dac->update(dac_code_1);
  }
  if(hiRange){
    ref_dac->update(dac_ref_target);
    ref_to_tileout.setConn();
  }
  // set multiplier to vga, set routes
  mult->setVga(true);
  mult->setGain(gain);
  dac_to_mult_in0.setConn();
  float error;
  bool succ = true;
  binsearch::find_bias(mult,
                       target,
                       mult->m_codes.gain_cal,
                       error,
                       MEAS_CHIP_OUTPUT
                       );
  // update nmos code
  binsearch::test_stab(mult->m_codes.gain_cal,
                       fabs(error),
                       max_error,
                       calib_failed);
  succ &= !calib_failed;
  sprintf(FMTBUF, "calibrate full gain=%f target=%f meas=%f max=%f succ=%s",
          gain,
          target,
          target+error,
          max_error,
          calib_failed ? "no" : "yes");
  print_log(FMTBUF);

  // compute fidelity at midpoint. If this is truly an appropriate gain,
  // it should be able to compute the gain at another value.
  if(mult->m_codes.range[in0Id] == RANGE_LOW){
    val_dac->update(dac_code_0_05);
  }
  else{
    val_dac->update(dac_code_0_5);
  }
  if(hiRange){
    ref_dac->update(dac_ref_target_half);
  }
  error = util::meas_chip_out(mult) - target*0.5;
  binsearch::test_stab(mult->m_codes.gain_cal,
                       fabs(error),
                       max_error,
                       calib_failed);
  succ &= !calib_failed;
  sprintf(FMTBUF, "calibrate half gain=%f target=%f meas=%f max=%f succ=%s",
          gain,
          target*0.5,
          target*0.5+error,
          max_error,
          calib_failed ? "no" : "yes");

  print_log(FMTBUF);
  print_log("---");
  //teardown
  if (hiRange) {
    ref_to_tileout.brkConn();
  }
  dac_to_mult_in0.brkConn();
  return succ;
}


bool Fabric::Chip::Tile::Slice::Multiplier::calibrateTarget (profile_t& result, float max_error) {
  float gain = m_codes.gain_val;
  int sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  bool hiRange = m_codes.range[out0Id] == RANGE_HIGH;
  bool loRange = m_codes.range[in0Id] == RANGE_LOW;
  float in0val = m_codes.range[in0Id] == RANGE_LOW ? 0.1 : 1.0;
  float in1val = m_codes.range[in1Id] == RANGE_LOW ? 0.1 : 1.0;
  float coeff_vga = util::range_to_coeff(m_codes.range[out0Id])/util::range_to_coeff(m_codes.range[in0Id]);
  float coeff_mult = coeff_vga/util::range_to_coeff(m_codes.range[in1Id]);

  float target_vga =  sign*gain*coeff_vga*in0val;
  float target_mult =  sign*coeff_vga*in0val*in1val;
	// preserve dac state because we will clobber it
  // can only calibrate target for vga.
  if(!m_codes.enable){
    print_log("not enabled");
    return true;
  }
  if(!m_codes.vga){
    print_log("not in vga mode");
    return true;
  }
  int cFanId = unitId==unitMulL?0:1;

  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;
  Dac * val_dac = parentSlice->dac;
  cutil::calibrate_t calib;
  cutil::initialize(calib);
  // backup state of each component that will be clobbered
  mult_code_t codes_self = m_codes;
  dac_code_t codes_dac = val_dac->m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;

  // backup connections
  cutil::buffer_mult_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_dac_conns(calib,val_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  Connection mult_to_tileout = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection tileout_to_chipout = Connection ( parentSlice->tileOuts[3].out0,
                                               parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );


  mult_to_tileout.setConn();
	tileout_to_chipout.setConn();

  dac_code_t dac_code_0;
  dac_code_t dac_code_1; // the entire range
  dac_code_t dac_code_0_1; // half the entire range, for the hiRange signal
  dac_code_t dac_code_0_5; // half the range
  dac_code_t dac_code_0_05; // half the range, for loRange signal
  dac_code_t dac_ref_targ_vga; // reference signal, for full range
  dac_code_t dac_ref_targ_vga_half; // reference signal, for half range


  if(hiRange){
    prof::init_profile(prof::TEMP);
    dac_ref_targ_vga = cutil::make_val_dac(calib,
                                       ref_dac,
                                           -target_vga,
                                           prof::TEMP);
    prof::init_profile(prof::TEMP);
    dac_ref_targ_vga_half = cutil::make_val_dac(calib,
                                           ref_dac,
                                           -target_vga*0.5,
                                           prof::TEMP);

  }

  // done computing preset codes
  if(loRange){
    prof::init_profile(prof::TEMP);
    dac_code_0_1 = cutil::make_val_dac(calib,
                                       val_dac,0.1,
                                       prof::TEMP);
    prof::init_profile(prof::TEMP);
    dac_code_0_05 = cutil::make_val_dac(calib,
                                        val_dac,0.05,
                                        prof::TEMP);

  }
  prof::init_profile(prof::TEMP);
  dac_code_1 = cutil::make_one_dac(calib,val_dac,
                                   prof::TEMP);
  prof::init_profile(prof::TEMP);
  dac_code_0_5 = cutil::make_val_dac(calib,val_dac,0.5,
                                     prof::TEMP);
  prof::init_profile(prof::TEMP);
  dac_code_0 = cutil::make_zero_dac(calib, val_dac,
                                    prof::TEMP);

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
    sprintf(FMTBUF, "target=%f max_error=%f nmos=%d", target_vga,max_error,m_codes.nmos);
    print_info(FMTBUF);
    succ &= helper_find_port_cal_out0(val_dac, this,max_error);
    if(succ)
      succ &= helper_find_port_cal_in0(val_dac, this,max_error);
    if(succ)
      succ &= helper_find_port_cal_in1(val_dac, this,dac_code_0,max_error);

    if(succ){
      bool pmos_succ = false;
      for(int pmos=0; pmos<=7; pmos+=1){
        m_codes.pmos = pmos;
        setAnaIrefPmos();
        pmos_succ = helper_find_gain_cal(gain,
                                         this,
                                         val_dac,
                                         ref_dac,
                                         &parentSlice->tileOuts[3],
                                         hiRange,
                                         hiRange ? 0.0 : target_vga,
                                         dac_ref_targ_vga,
                                         dac_ref_targ_vga_half,
                                         dac_code_0_1,
                                         dac_code_0_05,
                                         dac_code_1,
                                         dac_code_0_5,
                                         max_error);
        if(pmos_succ){
          break;
        }
      }
      succ &= pmos_succ;
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

  val_dac->update(codes_dac);
  ref_dac->update(codes_ref);
  update(codes_self);

	return found_code && calib.success;
}
