#include "AnalogLib.h"
#include "fu.h"
#include "mul.h"
#include "calib_util.h"
#include <float.h>


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

float compute_gain(float value,float bias){
  return (value+bias)/value;
}

#define N_MUL_CORNERS 4
#define N_MUL_PTS (N_MUL_CORNERS*N_MUL_CORNERS)
int helper_find_gain_cal_mult(Fabric::Chip::Tile::Slice::Multiplier* mult,
                               Fabric::Chip::Tile::Slice::Dac* ref_dac,
                               Fabric::Chip::Tile::Slice::Dac* val1_dac,
                               Fabric::Chip::Tile::Slice::Dac* val2_dac,
                               float & gain_stdev,
                               float & average_error)
{
  Fabric::Chip::Connection dac_to_mult_in0 =
    Fabric::Chip::Connection ( val1_dac->out0, mult->in0);
  Fabric::Chip::Connection dac_to_mult_in1 =
    Fabric::Chip::Connection ( val2_dac->out0, mult->in1);
  Fabric::Chip::Connection ref_to_tileout =
    Fabric::Chip::Connection ( ref_dac->out0, mult->parentSlice->tileOuts[3].in0);
  mult_code_t backup_codes = mult->m_codes;
  val1_dac->setEnable(true);
  val2_dac->setEnable(true);
  ref_dac->setEnable(true);
  mult->setVga(false);
  dac_to_mult_in0.setConn();
  dac_to_mult_in1.setConn();
  ref_to_tileout.setConn();
  float corners[N_MUL_CORNERS] = {0.9,-0.9,0.5,-0.5};
  float deltas[N_MUL_PTS];
  float values[N_MUL_PTS];
  /*
    this populates the bias table for the multiplier. Multipliers in multiply mode
    are relatively insensitive to changes in the gain_cal parameter. We will use
    this bias table to compute the standard deviation of the gain of these data points.
    we do this because it is very difficult to correct for differences in the gain
    depending on the quadrant of the inputs.
  */
  for(int i=0; i < N_MUL_CORNERS; i += 1){
    for(int j=0; j < N_MUL_CORNERS; j+=1){
      float in0_val = compute_in0(mult->m_codes,corners[i]);
      float in1_val = compute_in1(mult->m_codes,corners[j]);
      in0_val = val1_dac->fastMakeValue(in0_val);
      in1_val = val2_dac->fastMakeValue(in1_val);
      float pred_out_val = predict_out_mult(mult->m_codes,in0_val,in1_val);
      cutil::fast_make_ref_dac(ref_dac, pred_out_val);
      float ref_val = ref_dac->fastMeasureValue();
      // the bias we're actually expecting
      float targ = pred_out_val + ref_val;
      //not sensitive to gain code
      mult->m_codes.gain_cal = 32;
      float bias = binsearch::bin_search_meas(mult,MEAS_CHIP_OUTPUT);
      int idx =i*N_MUL_CORNERS+j;
      deltas[idx] = bias-targ;
      values[idx] = pred_out_val;
      float gain = compute_gain(values[idx],deltas[idx]);
      sprintf(FMTBUF,"PARS ins=(%f,%f) out=%f ref=%f offset=%f bias=%f gain=%f",
              in0_val,in1_val,pred_out_val,ref_val,targ,
              deltas[idx],gain);
      print_info(FMTBUF);
    }
  }

  int gain_code = -1;
  float avg_error=0;
  float avg_gain=0;
  float stdev=0;
  //compute average error, average gain, and standard deviation of gain.
  for(int j=0; j < N_MUL_PTS; j += 1){
    float gain = compute_gain(values[j],deltas[j]);
    avg_error += fabs(deltas[j]);
    avg_gain += gain;

  }
  avg_error /= (N_MUL_PTS);
  avg_gain /= (N_MUL_PTS);
  for(int j=0; j < N_MUL_PTS; j += 1){
    float gain = compute_gain(values[j],deltas[j]);
    stdev += pow((gain - avg_gain),2.0);
  }
  stdev /= (N_MUL_PTS-1);
  stdev = sqrt(stdev);
  sprintf(FMTBUF,"code=%d avg_err=%f avg_gain=n(%f,%f)",
          32,avg_error,avg_gain,stdev);
  print_info(FMTBUF);

  // update arguments that are passed by reference
  gain_stdev = stdev;
  average_error = avg_error;

  //reset the state
  mult->m_codes = backup_codes;
  val1_dac->setEnable(false);
  val2_dac->setEnable(false);
  dac_to_mult_in0.brkConn();
  dac_to_mult_in1.brkConn();
  ref_to_tileout.brkConn();
  return 32;
}
#define N_VGA_CORNERS 4
#define N_VGA_PTS (N_VGA_CORNERS*N_VGA_CORNERS)
int helper_find_generic_gain_cal_vga(Fabric::Chip::Tile::Slice::Multiplier* mult,
                                      Fabric::Chip::Tile::Slice::Dac* ref_dac,
                                      Fabric::Chip::Tile::Slice::Dac* val_dac,
                                      float& percent_stdev,
                                      float& average_error){
  Fabric::Chip::Connection dac_to_mult_in0 =
    Fabric::Chip::Connection ( val_dac->out0, mult->in0 );
  Fabric::Chip::Connection ref_to_tileout =
    Fabric::Chip::Connection ( ref_dac->out0, mult->parentSlice->tileOuts[3].in0);
  mult_code_t backup_codes = mult->m_codes;
  // setup input, reference signal
  val_dac->setEnable(true);
  ref_dac->setEnable(true);
  mult->setVga(true);
  dac_to_mult_in0.setConn();
  ref_to_tileout.setConn();
  float corners[N_MUL_CORNERS] = {0.9,-0.9,0.5,-0.5};
  float deltas[64][N_VGA_PTS];
  float values[N_VGA_PTS];
  /*
    the bias table is per-gain code, because the vga block is dependent on
    the gain_cal code
   */
  for(int i=0; i < N_VGA_CORNERS; i += 1){
    for(int j=0; j < N_VGA_CORNERS; j+=1){
      // measure the bias of this input output pair
      float in0_val = compute_in0(mult->m_codes,corners[i]);
      float gain_val = corners[j];
      mult->setGain(gain_val);
      in0_val = val_dac->fastMakeValue(in0_val);
      float pred_out_val = predict_out_vga(mult->m_codes,in0_val);
      cutil::fast_make_ref_dac(ref_dac, pred_out_val);
      float ref_val = ref_dac->fastMeasureValue();
      float targ = pred_out_val + ref_val;
      int idx =i*N_MUL_CORNERS+j;
      values[idx] = pred_out_val;
      sprintf(FMTBUF,"PARS ins=(%f,%f) out=%f ref=%f offset=%f",
              in0_val,gain_val,pred_out_val,ref_val,targ);
      print_info(FMTBUF);
      for(int k=0; k < 64; k++){
        mult->m_codes.gain_cal = k;
        float bias = binsearch::bin_search_meas(mult,MEAS_CHIP_OUTPUT);
        deltas[k][idx] = bias-targ;
      }
    }
  }
  int best_gain_code = -1;
  float best_error = -1;
  float best_stdev_gain = -1;
  float best_avg_gain = -1;
  /*
    choose the gain_cal code that is the closest to unity gain.
   */
  for(int i=0; i < 64; i++){
    float avg_error=0;
    float avg_gain=0;
    float stdev_gain=0;
    for(int j=0; j < N_VGA_PTS; j += 1){
      float gain = compute_gain(values[j],deltas[i][j]);
      avg_error += fabs(deltas[i][j]);
      avg_gain += gain;
    }
    avg_error /= (N_VGA_PTS);
    avg_gain /= (N_VGA_PTS);
    for(int j=0; j < N_VGA_PTS; j += 1){
      float gain = compute_gain(values[j],deltas[i][j]);
      stdev_gain += pow(gain - avg_gain,2.0);
    }
    stdev_gain = sqrt(stdev_gain/(N_VGA_PTS-1));
    sprintf(FMTBUF,"code=%d gain=n(%f,%f) error=%f",
            i,avg_gain,stdev_gain,avg_error);
    print_info(FMTBUF);
    if(best_gain_code < 0
        || avg_error < best_error){
      best_error = avg_error;
      best_stdev_gain = stdev_gain;
      best_avg_gain = avg_gain;
      best_gain_code = i;
    }
  }
  sprintf(FMTBUF,"BEST code=%d gain=n(%f,%f) error=%f",
          best_gain_code,
          best_avg_gain,
          best_stdev_gain,
          best_error);
  print_info(FMTBUF);
  //update global state
  percent_stdev = best_stdev_gain;
  average_error = best_error;
  //restore state
  mult->m_codes = backup_codes;
  val_dac->setEnable(false);
  dac_to_mult_in0.brkConn();
  ref_to_tileout.brkConn();
  return best_gain_code;
}

void helper_find_pmos_mult(Fabric::Chip::Tile::Slice::Multiplier* mult,
                           Fabric::Chip::Tile::Slice::Dac* ref_dac,
                           Fabric::Chip::Tile::Slice::Dac* val1_dac,
                           Fabric::Chip::Tile::Slice::Dac* val2_dac,
                            uint8_t& best_pmos,
                            uint8_t& best_gain_cal,
                            float& gain_stdev,
                            float& error){

  float stdevs[7];
  float errors[7];
  int gain_cals[7];
  for(int pmos=0; pmos<=7; pmos+=1){
    sprintf(FMTBUF,"mult pmos=%d",pmos);
    print_info(FMTBUF);
    mult->m_codes.pmos = pmos;
    mult->update(mult->m_codes);
    gain_cals[pmos] = helper_find_gain_cal_mult(mult,
                              ref_dac,
                              val1_dac,
                              val2_dac,
                              stdevs[pmos],
                              errors[pmos]);
  }
  // find the pmos,gain combo with the lowest error
  for(int pmos=0; pmos<=7; pmos+=1){
    if(pmos == 0 || stdevs[pmos] < stdevs[best_pmos]){
      best_pmos = pmos;
      best_gain_cal = gain_cals[pmos];
      gain_stdev = stdevs[pmos];
      error = errors[pmos];
    }
  }
  sprintf(FMTBUF,"BEST-PMOS pmos=%d gain_cal=%d stdev=%f error=%f",
          best_pmos,
          gain_cals[best_pmos],
          stdevs[best_pmos],
          errors[best_pmos]);
  print_info(FMTBUF);
}


void helper_find_pmos_vga(Fabric::Chip::Tile::Slice::Multiplier* mult,
                          Fabric::Chip::Tile::Slice::Dac* ref_dac,
                          Fabric::Chip::Tile::Slice::Dac* val1_dac,
                          uint8_t& best_pmos,
                          uint8_t& best_gain_cal,
                          float& gain_stdev,
                          float& error){
  float stdevs[7];
  float errors[7];
  int gain_cals[7];
  for(int pmos=0; pmos<=7; pmos+=1){
    sprintf(FMTBUF,"vga pmos=%d",pmos);
    print_info(FMTBUF);
    mult->m_codes.pmos = pmos;
    mult->update(mult->m_codes);
    gain_cals[pmos] = helper_find_generic_gain_cal_vga(mult,
                                                       ref_dac,
                                                       val1_dac,
                                                       stdevs[pmos],
                                                       errors[pmos]);
  }
  // find the pmos,gain combo with the lowest standard deviation of gains
  // this prevents the calibration routine for selecting parameter assignments
  // with no hot (high gain) or cold (low gain) areas
  for(int pmos=0; pmos<=7; pmos+=1){
    if(pmos == 0 || errors[pmos] < errors[best_pmos]){
      best_pmos = pmos;
      best_gain_cal = gain_cals[pmos];
      gain_stdev = stdevs[pmos];
      error = errors[pmos];
    }
  }
  sprintf(FMTBUF,"BEST-PMOS pmos=%d gain_cal=%d stdev=%f error=%f",
          best_pmos,
          gain_cals[best_pmos],
          stdevs[best_pmos],
          errors[best_pmos]);
  print_info(FMTBUF);
}

void helper_find_pmos(Fabric::Chip::Tile::Slice::Multiplier* mult,
                       Fabric::Chip::Tile::Slice::Dac* ref_dac,
                       Fabric::Chip::Tile::Slice::Dac* val1_dac,
                       Fabric::Chip::Tile::Slice::Dac* val2_dac,
                       uint8_t &pmos,
                       uint8_t &gain_cal,
                       float &gain_stdev,
                       float &error)
{
  if(mult->m_codes.vga){
    helper_find_pmos_vga(mult,
                                ref_dac,
                                val1_dac,
                                pmos,
                                gain_cal,
                                gain_stdev,
                                error);
  }
  else{
    helper_find_pmos_mult(mult,
                          ref_dac,
                          val1_dac,
                          val2_dac,
                          pmos,
                          gain_cal,
                          gain_stdev,
                          error);
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
  dval1_0 = cutil::make_zero_dac(calib,val1_dac);

  bool found_code = false;
  mult_code_t best_code = m_codes;

  print_info("=== calibrate multiplier ===");

  float errors[7];
  float stdevs[7];
  mult_code_t configs[7];
  float pmos[7];
  bool succs[7];
	for(int nmos=0; nmos < 7; nmos += 1) {
    errors[nmos] = -1;
    if(!calib.success){
      continue;
    }
    m_codes.nmos = nmos;
    setAnaIrefNmos ();
    bool succ = true;
    //calibrate bias, no external input
    sprintf(FMTBUF, "execute nmos=%d", m_codes.nmos);
    print_info(FMTBUF);
    succ &= helper_find_port_cal_out0(val1_dac, this,0.015);
    if(succ)
      succ &= helper_find_port_cal_in0(val1_dac, this,0.015);
    if(succ){
      if(codes_self.vga)
        helper_find_port_cal_in1(val1_dac, this,dval1_0,0.015);
      else
        succ &= helper_find_port_cal_in1(val1_dac, this,dval1_0,0.015);
    }
    if(succ){
      m_codes.vga = codes_self.vga;
      if(m_codes.vga){
        setGain(codes_self.gain_val);
      }
      configs[nmos] = m_codes;
      helper_find_pmos(this,
                       ref_dac,
                       val1_dac,
                       val2_dac,
                       configs[nmos].pmos,
                       configs[nmos].gain_cal,
                       stdevs[nmos],
                       errors[nmos]);
    }
    parentSlice->dac->setEnable(false);
    succs[nmos] = succ;
	}
  int best_nmos = -1;
  if(codes_self.vga)
    {
      // the best vga codes fall within the maximum error, while also reaching the minimum
      // standard deviation.
      for(int i=0; i < 7; i += 1){
        if(succs[i] && (best_nmos < 0
                        || (stdevs[i] <= stdevs[best_nmos] &&
                            errors[i] <= max_error)
                        ))
          {
            best_nmos = i;
          }
      }
    }
  else
    {
      for(int i=0; i < 7; i += 1){
        if(succs[i] && (best_nmos < 0
                        || stdevs[i] < stdevs[best_nmos])){
          best_nmos = i;
        }
      }
    }
  if(best_nmos >= 0 && errors[best_nmos] < max_error){
    best_code = configs[best_nmos];
    found_code = true;
  }
  print_info("==== BEST CODE ======");
  sprintf(FMTBUF, "nmos=%d pmos=%d gain_cal=%d error=%f gain-std=%f",
          best_code.nmos,
          best_code.pmos,
          best_code.gain_cal,
          errors[best_code.nmos],
          stdevs[best_code.nmos]);
  print_info(FMTBUF);
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
