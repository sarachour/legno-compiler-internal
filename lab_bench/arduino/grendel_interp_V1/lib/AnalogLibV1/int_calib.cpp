#include "AnalogLib.h"
#include <float.h>
#include "calib_util.h"
#include "fu.h"
/*
this function performs linear regressions on the two datasets to estimate
the time constant. A known input k_value is applied to the integrator, which has an unknown
bias.
 */
float estimate_time_constant(calib_objective_t obj,
                             float k_value, float target_tc,
                             int n,
                             float * nom_times,float * nom_vals,
                             float * k_times, float * k_vals,
                             float& score){
  float nom_alpha,nom_beta,nom_Rsq;
  float k_alpha,k_beta,k_Rsq;
  util::linear_regression(nom_times,nom_vals,n,
                          nom_alpha,nom_beta,nom_Rsq);
  util::linear_regression(k_times,k_vals,n,
                          k_alpha,k_beta,k_Rsq);
  float alpha_k = k_alpha - nom_alpha;
  float meas_tc = alpha_k/k_value;
  float time_scale = meas_tc/target_tc;
  sprintf(FMTBUF,"time-const=%f confidence=(%f,%f)",
          time_scale,
          k_Rsq,nom_Rsq);
  print_info(FMTBUF);
  /*
  sprintf(FMTBUF,"  nominal alpha=%f beta=%f R2=%f",
          nom_alpha,nom_beta,nom_Rsq);
  print_info(FMTBUF);
  sprintf(FMTBUF,"  const alpha=%f beta=%f R2=%f",
          k_alpha,k_beta,k_Rsq);
  print_info(FMTBUF);
  */
  switch(obj){
  case CALIB_MINIMIZE_ERROR:
    // try to minimize the error between the expected and observed
    // time constant
    score = fabs(time_scale- 1.0);
    break;
  case CALIB_MAXIMIZE_DELTA_FIT:
    // try and choose time constants that produce good fits.
    score = 1.0-max(k_Rsq, nom_Rsq);
    break;
  }
  return time_scale;
}

void Fabric::Chip::Tile::Slice::Integrator::calibrateOpenLoopCircuit(calib_objective_t obj,
                                                                     Dac* val_dac,
                                                                     float (&scores)[MAX_NMOS],
                                                                     int (&codes)[MAX_NMOS],
                                                                     int (&closed_loop_calib_table) [MAX_NMOS][2]){

  dac_code_t backup_codes = val_dac->m_codes;
  // configure value DAC
  val_dac->setEnable(true);
  val_dac->setRange(RANGE_MED);
  val_dac->setInv(false);
  val_dac->setConstantCode(129);
  val_dac->update(val_dac->m_codes);

  // determine the rate of change of the open loop system.
  float dummy;
  float input = val_dac->fastMeasureValue(dummy);
  sprintf(FMTBUF,"open-loop input=%f",input);
  print_info(FMTBUF);

  // set the initial condition of the system
  this->setInitial(0.0);
  float target_tc = Fabric::Chip::Tile::Slice::Integrator::computeTimeConstant(this->m_codes);

  // set the relevant connections
  Connection conn_out_to_tile = Connection (this->out0,parentSlice->tileOuts[3].in0);
  Connection conn_dac_to_in = Connection (val_dac->out0, this->in0);
  Connection tileout_to_chipout = Connection (parentSlice->tileOuts[3].out0,
                                              parentSlice->parentTile->parentChip
                                              ->tiles[3].slices[2].chipOutput->in0);
  conn_out_to_tile.setConn();
  tileout_to_chipout.setConn();

  const int n_samples = 25;
  float nom_times[25],k_times[25];
  float nom_values[25],k_values[25];
  for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
    this->m_codes.nmos = nmos;
    this->m_codes.port_cal[in0Id] = closed_loop_calib_table[nmos][0];
    this->m_codes.port_cal[out0Id] = closed_loop_calib_table[nmos][1];

    float scores_gain[MAX_GAIN_CAL];
    for(int gain_cal=0; gain_cal < MAX_GAIN_CAL; gain_cal += 1){
      this->m_codes.gain_cal = gain_cal;
      this->update(this->m_codes);

      // with input provided via dac
      conn_dac_to_in.setConn();
      util::meas_transient_chip_out(this,
                                    k_times, k_values,
                                    n_samples);
      // with ground.
      conn_dac_to_in.brkConn();
      util::meas_transient_chip_out(this,
                                    nom_times, nom_values,
                                    n_samples);

      estimate_time_constant(obj,input,target_tc,
                             n_samples,
                             nom_times,nom_values,
                             k_times,k_values,
                             scores_gain[gain_cal]);
    }

    codes[nmos] = util::find_minimum(scores_gain, MAX_GAIN_CAL);
    scores[nmos] = scores_gain[codes[nmos]];
    sprintf(FMTBUF,"nmos=%d BEST code=%d score=%f",nmos,codes[nmos],scores[nmos]);
    print_info(FMTBUF);
  }

  conn_out_to_tile.brkConn();
  tileout_to_chipout.brkConn();
  val_dac->update(backup_codes);
  return;
}

/*
  Calibration routine for idiomatic closed-loop circuit that implements the following:

  z' = -z

  note that with the fanout biases accounted the diffeq is actually solving

  z' = -z + out0bias

  the steady state for this equation is out0bias with a measurement error of out1bias

  so the expected measured signal at steady state is

  out0bias + out1bias


 */
void Fabric::Chip::Tile::Slice::Integrator::calibrateClosedLoopCircuit(calib_objective_t obj,
                                                                       Fanout* fan,
                                                                       float (&scores)[MAX_NMOS],
                                                                       int (&codes)[MAX_NMOS][2]){

  // configure fanout and record biases for each port
  fanout_code_t backup_codes = fan->m_codes;
  float out0bias, out1bias, out2bias;
  fan->setRange(RANGE_MED);
  fan->setInv(out0Id,true);
  fan->setInv(out1Id,false);
  fan->setInv(out2Id,false);
  fan->measureZero(out0bias,out1bias,out2bias);
  float target = 0.0 + out0bias + out1bias;

  sprintf(FMTBUF,"fan bias0=%f bias1=%f bias2=%f", out0bias,out1bias,out2bias);
  print_info(FMTBUF);
  // configure init cond
  setInitial(0.0);

  // set the relevant connections
  Connection conn_out_to_fan = Connection (this->out0,fan->in0);
  Connection conn_fan0_to_in = Connection (fan->out0, this->in0);
  Connection conn_fan1_to_tileout = Connection (fan->out1,
                                                parentSlice->tileOuts[3].in0);
  Connection tileout_to_chipout = Connection (parentSlice->tileOuts[3].out0,
                                              parentSlice->parentTile->parentChip
                                              ->tiles[3].slices[2].chipOutput->in0);


  conn_out_to_fan.setConn();
  conn_fan0_to_in.setConn();
  conn_fan1_to_tileout.setConn();

  /*
    algorithm:
    for each nmos, choose in0_cal that minimizes error where
       out0_cal = 32 and gain_cal = 32

    for each nmos,chosen in0_cal, choose out0_cal that minimizes error
       where gain_cal = 32
   */
  for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
    float score_in[MAX_BIAS_CAL];
    this->m_codes.nmos = nmos;
    this->m_codes.gain_cal = 32;
    this->m_codes.port_cal[out0Id] = 32;
    for(int in0_cal=0; in0_cal < MAX_BIAS_CAL; in0_cal += 1){
      this->m_codes.port_cal[in0Id] = in0_cal;
      this->update(this->m_codes);
      float mean, variance;
      util::meas_steady_chip_out(this,mean,variance);
      score_in[in0_cal] = fabs(mean-target);
      sprintf(FMTBUF," codes=(%d,%d,32) target=%f mean=%f score=%f",
              nmos,in0_cal,target,mean,score_in[in0_cal]);
      print_info(FMTBUF);
    }
    codes[nmos][0] = util::find_minimum(score_in, MAX_BIAS_CAL);
    scores[nmos] = score_in[codes[nmos][0]];
    sprintf(FMTBUF,"nmos=%f BEST in0_code=%d score=%f",
            nmos, codes[nmos][0], scores[nmos]);
    print_info(FMTBUF);
  }
  for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
    float score_out[MAX_BIAS_CAL];
    this->m_codes.nmos = nmos;
    this->m_codes.gain_cal = 32;
    this->m_codes.port_cal[in0Id] = codes[nmos][0];
    for(int out0_cal=0; out0_cal < MAX_BIAS_CAL; out0_cal += 1){
      this->m_codes.port_cal[out0Id] = out0_cal;
      this->update(this->m_codes);
      float mean, variance;
      util::meas_steady_chip_out(this,mean,variance);
      score_out[out0_cal] = fabs(mean-target);
      sprintf(FMTBUF," codes=(%d,%d,%d) target=%f mean=%f score=%f",
              nmos,codes[nmos][0],out0_cal,target,mean,score_out[out0_cal]);
      print_info(FMTBUF);
    }
    codes[nmos][1] = util::find_minimum(score_out, MAX_BIAS_CAL);
    scores[nmos] = score_out[codes[nmos][1]];
    sprintf(FMTBUF,"nmos=%f BEST codes=(%d,%d) score=%f",
            nmos, codes[nmos][0],codes[nmos][1], scores[nmos]);
    print_info(FMTBUF);
  }
  conn_out_to_fan.brkConn();
  conn_fan0_to_in.brkConn();
  conn_fan1_to_tileout.brkConn();
  fan->update(backup_codes);
}
void Fabric::Chip::Tile::Slice::Integrator::calibrate(calib_objective_t obj){
  cutil::calibrate_t calib;
  cutil::initialize(calib);

  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * val_dac = parentSlice->dac;
  Fabric::Chip::Tile::Slice::Fanout * fan = &this->parentSlice->fans[0];

  fanout_code_t codes_fanout = fan->m_codes;
  dac_code_t codes_val_dac = val_dac->m_codes;
  integ_code_t codes_integ = this->m_codes;

  cutil::buffer_fanout_conns(calib,fan);
  cutil::buffer_dac_conns(calib,val_dac);
  cutil::buffer_integ_conns(calib,this);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,
                              parentSlice->parentTile->parentChip
                              ->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  Connection tileout_to_chipout = Connection (parentSlice->tileOuts[3].out0,
                                              parentSlice->parentTile->parentChip
                                              ->tiles[3].slices[2].chipOutput->in0);
  // set configuration
  tileout_to_chipout.setConn();

  float ol_scores[MAX_NMOS];
  float cl_scores[MAX_NMOS];
  int ol_codes[MAX_NMOS];
  int cl_codes[MAX_NMOS][2];


  this->calibrateClosedLoopCircuit(obj,fan,cl_scores,cl_codes);
  /*
  for(int i=0; i < MAX_NMOS; i+=1){
    cl_codes[i][0] = cl_codes[i][1] = 32;
  }
  */
  this->calibrateOpenLoopCircuit(obj,val_dac,ol_scores,ol_codes,cl_codes);
  float scores[MAX_NMOS];
  print_info("==== FINAL SCORES ====");
  for(int i=0; i < MAX_NMOS; i += 1){
    scores[i] = cl_scores[i]*ol_scores[i];
    sprintf(FMTBUF,"nmos=%d closed=%f open=%f final=%f",
            cl_scores[i],ol_scores[i],scores[i]);
    print_info(FMTBUF);
  }

  int best_nmos = util::find_minimum(scores,MAX_NMOS);
  int best_gain_cal = ol_codes[best_nmos];
  int best_port_cal_in0 = cl_codes[best_nmos][0];
  int best_port_cal_out0 = cl_codes[best_nmos][1];

  val_dac->update(codes_val_dac);
  fan->update(codes_fanout);
	tileout_to_chipout.brkConn();
  cutil::restore_conns(calib);
  this->m_codes = codes_integ;
  this->m_codes.nmos = best_nmos;
  this->m_codes.gain_cal = best_gain_cal;
  this->m_codes.port_cal[in0Id] = best_port_cal_in0;
  this->m_codes.port_cal[out0Id] = best_port_cal_out0;

}


/*
bool helper_find_cal_out0(Fabric::Chip::Tile::Slice::Integrator * integ,
                          float target,
                          float max_error){
  float error;
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
  float ic_val = Fabric::Chip::Tile::Slice::Integrator::compute_init_cond(integ->m_codes);
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



void find_zero(Fabric::Chip::Tile::Slice::Integrator* integ, float max_error,
               int* buf_in,int * buf_out){
  Fabric::Chip::Tile::Slice::Fanout * fanout = &integ->parentSlice->fans[0];
  fanout_code_t fan_codes = fanout->m_codes;
  integ_code_t integ_codes = integ->m_codes;

  fanout->m_codes.range[in0Id] = RANGE_MED;
  fanout->m_codes.range[out0Id] = RANGE_MED;
  fanout->m_codes.range[out1Id] = RANGE_MED;
  fanout->m_codes.range[out2Id] = RANGE_MED;
  fanout->m_codes.inv[out0Id] = false;
  fanout->m_codes.inv[out1Id] = true;
  fanout->update(fanout->m_codes);

  // do not invert the signal
  cutil::calibrate_t calib;
  cutil::initialize(calib);

  print_info("===== CALIBRATE FANOUT =====");
  fanout->calibrate(CALIB_MINIMIZE_ERROR);
  print_info("===== FIND ZERO =====");

  integ->setInitial(0.0);
  cutil::buffer_fanout_conns(calib,fanout);
  cutil::buffer_integ_conns(calib,integ);
  cutil::buffer_tileout_conns(calib,&integ->parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,
                              integ->parentSlice->parentTile->parentChip
                              ->tiles[3].slices[2].chipOutput);

  cutil::break_conns(calib);

  Fabric::Chip::Connection integ_to_fan = Fabric::Chip::Connection ( integ->out0, fanout->in0 );
  Fabric::Chip::Connection fan_to_tile = Fabric::Chip::Connection ( fanout->out0,
                                                      integ->parentSlice->tileOuts[3].out0);
  Fabric::Chip::Connection fan_to_integ = Fabric::Chip::Connection(fanout->out1, integ->in0);
  Fabric::Chip::Connection tile_to_chip = Fabric::Chip::Connection ( integ->parentSlice->tileOuts[3].out0,
                                         integ->parentSlice->parentTile        \
                                         ->parentChip->tiles[3].slices[2].chipOutput->in0 );

  integ_to_fan.setConn();
  fan_to_tile.setConn();
  fan_to_integ.setConn();
  tile_to_chip.setConn();

  // DO NOT NEGATE THE INTEGRATORS SIGNAL.
  // this makes it impossible to find steady state.
  integ->m_codes.inv[out0Id] = false;
  bool found_code = false;
  integ_code_t best_code = integ->m_codes;
  for(int nmos=0; nmos < 8; nmos += 1) {
    float bias_neg = -1;
    float bias_pos = -1;
    int code[2];

    buf_in[nmos] = -1;
    buf_out[nmos] = -1;
    code[0] = code[1] = -1;
    for(unsigned int bias_in=0; bias_in < 64; bias_in += 1){
      float mean, variance;
      integ->m_codes.nmos = nmos;
      integ->m_codes.port_cal[in0Id] = bias_in;
      integ->m_codes.port_cal[out0Id] = 32;
      integ->update(integ->m_codes);
      util::meas_steady_chip_out(integ,mean,variance);
      if(mean < 0.0 &&
         (bias_neg == -1 || fabs(mean) < bias_neg)){
        code[0]= bias_in;
        bias_neg = fabs(mean);
      }
      else if(mean >= 0.0 &&
              (bias_pos == -1 || fabs(mean) < bias_pos)){
        code[1]= bias_in;
        bias_pos = fabs(mean);
      }
    }
    sprintf(FMTBUF, "  - nmos=%d in_bias=%d error=%f",
            nmos,code[0],bias_neg);
    print_info(FMTBUF);
    sprintf(FMTBUF, "  + nmos=%d in_bias=%d error=%f",
            nmos,code[1],bias_pos);
    print_info(FMTBUF);

    float bias_best = max_error;
    int out_code = -1;
    int in_code = -1;
    for(int bias_out=0; bias_out < 64; bias_out += 1){
      for(int i = 0; i < 2; i +=1 ){
        float mean, variance;
        if(code[i] < 0){
          continue;
        }
        integ->m_codes.nmos = nmos;
        integ->m_codes.port_cal[in0Id] = code[i];
        integ->m_codes.port_cal[out0Id] = bias_out;
        integ->update(integ->m_codes);
        util::meas_steady_chip_out(integ,mean,variance);
        if(fabs(mean) <= bias_best){
          bias_best = fabs(mean);
          out_code = bias_out;
          in_code = code[i];
        }
      }
    }
    buf_in[nmos] = in_code;
    buf_out[nmos] = out_code;
    sprintf(FMTBUF, "nmos=%d in_bias=%d out_bias=%d error=%f",
            nmos, buf_in[nmos],buf_out[nmos],bias_best);
    print_info(FMTBUF);
  }

  integ_to_fan.brkConn();
  fan_to_tile.brkConn();
  fan_to_integ.brkConn();
  tile_to_chip.brkConn();
  cutil::restore_conns(calib);
  fanout->update(fan_codes);
  integ->update(integ_codes);
}
bool Fabric::Chip::Tile::Slice::Integrator::calibrateTargetHelper (profile_t& result,
                                                                   const float max_error,
                                                                   bool change_code) {
  if(!m_codes.enable){
    return true;
  }

  int bias_ins[8];
  int bias_outs[8];
  find_zero(this,0.03,bias_ins,bias_outs);

  print_info("===== CALIBRATE COMPONENT =====");
  Dac * ref_dac = parentSlice->dac;

  integ_code_t codes_self = m_codes;
  dac_code_t ref_codes = ref_dac->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);

  cutil::buffer_integ_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,
                              parentSlice->parentTile->parentChip
                              ->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

	// output side
  //conn1
  Connection ref_to_tile = Connection ( ref_dac->out0,
                                        parentSlice->tileOuts[3].in0 );
  //conn2
	Connection integ_to_tile= Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile \
                                         ->parentChip->tiles[3].slices[2].chipOutput->in0 );

  dac_code_t dac_ref;
  float ic_val = compute_init_cond(m_codes);
  float ref_val=0.0;

  print_info("making ref dac");
  dac_ref = cutil::make_ref_dac(calib,ref_dac,
                                -ic_val,
                                ref_val);
  ref_dac->update(dac_ref);
  integ_to_tile.setConn();
	tile_to_chip.setConn();
  ref_to_tile.setConn();

  bool found_code = false;
  integ_code_t best_code = m_codes;

  print_info("=== calibrate integrator ===");
  m_codes.nmos = 0;
	setAnaIrefNmos ();
  unsigned int code = m_codes.ic_code;
  // the higher the nmos code, the better the dynamic range
  while (m_codes.nmos <= 7 && calib.success) {
    bool succ = true;
    sprintf(FMTBUF, "nmos=%d", m_codes.nmos);
    print_info(FMTBUF);
    if(bias_ins[m_codes.nmos] < 0 or
       bias_outs[m_codes.nmos] < 0){
      print_info("  -> no bias that moves to zero");
      m_codes.nmos += 1;
      if(m_codes.nmos <= 7){
        setAnaIrefNmos ();
      }
      continue;
    }
    this->m_codes.port_cal[in0Id] = bias_ins[m_codes.nmos];
    this->m_codes.port_cal[out0Id] = bias_outs[m_codes.nmos];
    update(m_codes);
    //if(succ)
    //  succ &= helper_find_cal_in0(this,0.01);

    //m_codes.range[in0Id] = codes_self.range[in0Id];
    //m_codes.range[out0Id] = codes_self.range[out0Id];
    //update(m_codes);
    if(succ){
      ref_to_tile.setConn();
      succ &= helper_find_cal_gain(this,
                                   ref_dac,
                                   max_error,
                                   code,
                                   ref_val,
                                   dac_ref,
                                   change_code);
      ref_to_tile.brkConn();
    }
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
  ref_dac->update(ref_codes);
  ref_to_tile.brkConn();
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
  //setInitial(0.93);
  setInitial(0.0);
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
*/
