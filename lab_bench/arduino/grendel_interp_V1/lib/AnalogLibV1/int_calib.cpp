#include "AnalogLib.h"
#include <float.h>
#include "calib_util.h"
#include "fu.h"
/*
this function performs linear regressions on the two datasets to estimate
the time constant. A known input k_value is applied to the integrator, which has an unknown
bias.
 */
time_constant_stats estimate_time_constant(float k_value,
                             int n,
                             float * nom_times,float * nom_vals,
                             float * k_times, float * k_vals){
  float nom_alpha,nom_beta,nom_Rsq;
  float k_alpha,k_beta,k_Rsq;
  time_constant_stats stats;

  util::linear_regression(nom_times,nom_vals,n,
                          nom_alpha,nom_beta,nom_Rsq);
  util::linear_regression(k_times,k_vals,n,
                          k_alpha,k_beta,k_Rsq);
  float alpha_k = k_alpha - nom_alpha;
  stats.k = k_value;
  stats.tc = alpha_k/k_value;
  stats.eps = nom_alpha/stats.tc;
  stats.R2_eps = nom_Rsq;
  stats.R2_k = k_Rsq;
  /*
    sprintf(FMTBUF,"  nominal alpha=%f beta=%f R2=%f",
    nom_alpha,nom_beta,nom_Rsq);
    print_info(FMTBUF);
    sprintf(FMTBUF,"  const alpha=%f beta=%f R2=%f",
    k_alpha,k_beta,k_Rsq);
    print_info(FMTBUF);
  */
  return stats;
}

float compute_score(calib_objective_t obj,
                    float target_tc,
                    time_constant_stats stats){
  float time_scale = stats.tc/target_tc;
  sprintf(FMTBUF,"time-const=%f eps=%f confidence=(%f,%f)",
          time_scale,
          stats.eps,
          stats.R2_k,
          stats.R2_eps);
  print_info(FMTBUF);
  switch(obj){
  case CALIB_MINIMIZE_ERROR:
    // try to minimize the error between the expected and observed
    // time constant
    return fabs(time_scale- 1.0);
    break;
  case CALIB_MAXIMIZE_DELTA_FIT:
    // try and choose time constants that produce good fits.
    return fabs(stats.eps);
    break;
  }
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

      time_constant_stats tc_stats = estimate_time_constant(input,
                                                            n_samples,
                                                            nom_times,nom_values,
                                                            k_times,k_values);
      scores_gain[gain_cal] = compute_score(obj,target_tc,tc_stats);
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
      /*
      sprintf(FMTBUF," codes=(%d,%d,32) target=%f mean=%f score=%f",
              nmos,in0_cal,target,mean,score_in[in0_cal]);
      print_info(FMTBUF);
      */
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
      /*
      sprintf(FMTBUF," codes=(%d,%d,%d) target=%f mean=%f score=%f",
              nmos,codes[nmos][0],out0_cal,target,mean,score_out[out0_cal]);
      print_info(FMTBUF);
      */
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
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * val_dac = parentSlice->dac;
  Fabric::Chip::Tile::Slice::Fanout * fan = &this->parentSlice->fans[0];

  fanout_code_t codes_fanout = fan->m_codes;
  dac_code_t codes_val_dac = val_dac->m_codes;
  integ_code_t codes_integ = this->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
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
  for(int i=0; i < MAX_NMOS; i += 1){
    scores[i] = cl_scores[i]*ol_scores[i];
    /*
    sprintf(FMTBUF,"nmos=%d closed=%f open=%e final=%e",
            cl_scores[i],ol_scores[i],scores[i]);
    print_info(FMTBUF);
    */
  }

  int best_nmos = util::find_minimum(scores,MAX_NMOS);
  int best_gain_cal = ol_codes[best_nmos];
  int best_port_cal_in0 = cl_codes[best_nmos][0];
  int best_port_cal_out0 = cl_codes[best_nmos][1];
  sprintf(FMTBUF,"BEST nmos=%d gain_cal=%d port_cals=(%d,%d)",
          best_nmos,best_gain_cal,best_port_cal_in0,best_port_cal_out0);
  print_info(FMTBUF);
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

