#include "AnalogLib.h"
#include <float.h>
#include "calib_util.h"
#include "fu.h"




bool helper_find_cal_out0(Fabric::Chip::Tile::Slice::Integrator * integ,
                          float max_error){
  float error;
  float target = 0.0;
  bool calib_failed;
  integ->m_codes.cal_enable[out0Id] = true;
  binsearch::find_bias(integ, target,
                       integ->m_codes.port_cal[out0Id],
                       error,
                       MEAS_CHIP_OUTPUT);

  int code = integ->m_codes.port_cal[out0Id];
  binsearch::test_stab(code,
                       error,
                       max_error,
                       calib_failed);
  sprintf(FMTBUF,"integ out0 target=%f measured=%f error=%f max=%f",
          target, target+error, error, max_error);
  print_info(FMTBUF);
  integ->m_codes.cal_enable[out0Id] = false;
  return !calib_failed;
}

bool helper_find_cal_in0(Fabric::Chip::Tile::Slice::Integrator * integ,
                         float max_error){
  float error;
  bool calib_failed;
  float target = 0.0;
  //float target = 0.0;
  integ->m_codes.cal_enable[in0Id] = true;
  binsearch::find_bias(integ,
                       target,
                       integ->m_codes.port_cal[in0Id],
                       error,
                       MEAS_CHIP_OUTPUT);
  int code = integ->m_codes.port_cal[in0Id];
  binsearch::test_stab(code,
                       error,
                       max_error,
                       calib_failed);
  sprintf(FMTBUF,"integ in0 target=%f measured=%f error=%f max=%f",
          target, target+error,error, max_error);
  print_info(FMTBUF);
  integ->m_codes.cal_enable[in0Id] = false;
  return !calib_failed;

}


bool helper_find_cal_gain(Fabric::Chip::Tile::Slice::Integrator * integ,
                          Fabric::Chip::Tile::Slice::Dac * ref_dac,
                          float max_error,
                          int code,
                          float ref,
                          dac_code_t& ref_codes,
                          bool change_code){

  int delta = 0;
  bool succ = false;
  float ic_val = compute_init_cond(integ->m_codes);
  float target = ic_val + ref;
  float error;
  //how to identify the magnitude of the signal needs to be increased.
  //if error is negative + number is positive
  // if error is positive + number is negative
  float target_sign = target >= 0 ? 1.0 : -1.0;
  // adjust the initial condition code.
  ref_dac->update(ref_codes);
  while(!succ){
    int gain_code;
    bool calib_failed;
    if(code + delta > 255
       || code + delta < 0){
      delta = 0;
      break;
    }
    integ->setInitialCode(code+delta);
    binsearch::find_bias(integ,
                         target,
                         integ->m_codes.gain_cal,
                         error,
                         MEAS_CHIP_OUTPUT);
    gain_code = integ->m_codes.gain_cal;
    binsearch::test_stab(gain_code,
                         error,
                         max_error,
                         calib_failed);
    succ = !calib_failed;
    sprintf(FMTBUF,"init-cond code=%d target=%f measured=%f succ=%s",
            code+delta, target, target+error, succ ? "yes" : "no");
    print_info(FMTBUF);
    if(!succ){
      if(!change_code){
        return false;
      }
      if(error*target_sign <= 0){
        delta += target_sign;
      }
      else{
        delta += target_sign*-1.0;
      }
    }
  }
  integ->m_codes.ic_code = code+delta;
  return succ;
}




bool Fabric::Chip::Tile::Slice::Integrator::calibrateTargetHelper (profile_t& result,
                                                                   const float max_error,
                                                                   bool change_code) {
  if(!m_codes.enable){
    return true;
  }
  int ic_sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  bool hiRange = (m_codes.range[out0Id] == RANGE_HIGH);
  float coeff = util::range_to_coeff(m_codes.range[out0Id]);

  Dac * ref_dac = parentSlice->dac;
  integ_code_t codes_self = m_codes;
  dac_code_t ref_codes = ref_dac->m_codes;


  cutil::calibrate_t calib;
  cutil::initialize(calib);

  cutil::buffer_integ_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

	// output side
  //conn1
  Connection ref_to_tile = Connection ( ref_dac->out0,
                                        parentSlice->tileOuts[3].in0 );
  //conn2
	Connection integ_to_tile= Connection ( out0, parentSlice->tileOuts[3].in0 );

	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );

  dac_code_t dac_ref;
  float ic_val = compute_init_cond(m_codes);
  float ref_val=0.0;

  print_info("making zero dac");
  prof::init_profile(prof::TEMP);
  if (hiRange) {
    print_info("high range! making reference dac");
    prof::init_profile(prof::TEMP);
    dac_ref = cutil::make_ref_dac(calib,ref_dac,
                                 -ic_val,
                                 ref_val);
    ref_to_tile.setConn();
  }
  else{
    dac_ref = cutil::make_zero_dac(calib, ref_dac,prof::TEMP);
  }
  ref_dac->update(dac_ref);
  integ_to_tile.setConn();
	tile_to_chip.setConn();

  bool found_code = false;
  integ_code_t best_code = m_codes;

  print_info("=== calibrate integrator ===");
  m_codes.nmos = 0;
	setAnaIrefNmos ();
  unsigned int code = m_codes.ic_code;
  while (m_codes.nmos <= 7 && !found_code && calib.success) {
    bool succ = true;
    sprintf(FMTBUF, "nmos=%d", m_codes.nmos);
    print_info(FMTBUF);

    update(m_codes);
    succ &= helper_find_cal_out0(this,0.01);
    if(succ)
      succ &= helper_find_cal_in0(this,0.01);

    update(m_codes);
    if(succ)
      succ &= helper_find_cal_gain(this,
                                   ref_dac,
                                   max_error,
                                   code,
                                   ref_val,
                                   dac_ref,
                                   change_code);
    ref_dac->update(dac_ref);

    if(succ){
      found_code = true;
      best_code = m_codes;
    }
    m_codes.nmos += 1;
    if(m_codes.nmos <= 7){
      setAnaIrefNmos ();
    }
  }
  update(best_code);
	if (hiRange) {
    ref_to_tile.brkConn();
    ref_dac->update(ref_codes);
	} else {
	}
  integ_to_tile.brkConn();
	tile_to_chip.brkConn();
  cutil::restore_conns(calib);

  codes_self.nmos = m_codes.nmos;
  codes_self.ic_code = m_codes.ic_code;
  codes_self.gain_cal = m_codes.gain_cal;
  codes_self.port_cal[out0Id] = m_codes.port_cal[out0Id];
  codes_self.port_cal[in0Id] = m_codes.port_cal[in0Id];
  update(codes_self);
	return found_code && calib.success;
}




bool Fabric::Chip::Tile::Slice::Integrator::calibrateTarget (profile_t& result, const float max_error) {
  //calibrate at given initial condition, where we allow twiddling
  //the code
  return calibrateTargetHelper(result,max_error,false);
}
bool Fabric::Chip::Tile::Slice::Integrator::calibrate (profile_t& result, const float max_error) {
	//setEnable(true);
  integ_code_t codes_self = m_codes;
  setInitial(0.93);
  //calibrate at initial condition=1.0, where we don't change the
  //initial condition code
  bool success = calibrateTargetHelper(result,max_error,false);
  codes_self.nmos = m_codes.nmos;
  codes_self.gain_cal = m_codes.gain_cal;
  codes_self.port_cal[out0Id] = m_codes.port_cal[out0Id];
  codes_self.port_cal[in0Id] = m_codes.port_cal[in0Id];
  update(codes_self);
  return success;
}
