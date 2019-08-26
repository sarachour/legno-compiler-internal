#include "AnalogLib.h"
#include <float.h>
#include "calib_util.h"
#include "fu.h"

#define CALIB_NPTS 5
const float TEST_POINTS[CALIB_NPTS] = {0,-0.9,0.9,0.5,-0.5};



float Fabric::Chip::Tile::Slice::Integrator::calibrateInitCondMinError(Fabric::Chip::Tile::Slice::Dac * ref_dac){
  float score_total = 0;
  int total = 0;
  for(int i=0; i < CALIB_NPTS; i += 1){
    float ic_val = TEST_POINTS[i];
    this->setInitial(ic_val);
    float target = Fabric::Chip::Tile::Slice::Integrator::computeInitCond(this->m_codes);
    bool measure_steady_state = false;
    float mean,dummy;
    bool succ = cutil::measure_signal_robust(this,
                                             ref_dac,
                                             target,
                                             measure_steady_state,
                                             mean,
                                             dummy);
    if(succ){
      sprintf(FMTBUF,"  test=%f meas=%f",target,mean);
      print_info(FMTBUF);
      score_total += fabs(target-mean);
      total += 1;
    }
  }
  return score_total/total;
}
float Fabric::Chip::Tile::Slice::Integrator::calibrateInitCondMaxDeltaFit(Dac * ref_dac){
  error("unimplemented: integ max_delta_fit");
  float gains[CALIB_NPTS];
  float bias = 0;
  int m = 0;
  for(int i=0; i < CALIB_NPTS; i += 1){
    float ic_val = TEST_POINTS[i];
    this->setInitial(ic_val);
    float target = Fabric::Chip::Tile::Slice::Integrator::computeInitCond(this->m_codes);
    bool measure_steady_state = false;
    float mean,dummy;
    bool succ = cutil::measure_signal_robust(this,
                                             ref_dac,
                                             target,
                                             measure_steady_state,
                                             mean,
                                             dummy);
    if(succ && target != 0.0){
      gains[m] = mean/target;
      m += 1;
    }
    else{
      bias = mean;
    }
  }
  float avg_gain, gain_variance;
  util::distribution(gains,m,avg_gain,gain_variance);
  sprintf(FMTBUF," gain=N(%f,%f) bias=%f", avg_gain,gain_variance,bias);
  return gain_variance;
}

void Fabric::Chip::Tile::Slice::Integrator::calibrateInitCond(calib_objective_t obj,
                                                              Dac* ref_dac,
                                                              cutil::calib_table_t (&calib_table)[MAX_NMOS],
                                                              cutil::calib_table_t (&closed_loop_calib_table) [MAX_NMOS]){

  dac_code_t backup_codes = ref_dac->m_codes;

  ref_dac->setRange(this->m_codes.range[out0Id]);
  fast_calibrate_dac(ref_dac);
  // set the relevant connections
  Connection ref_to_tile = Connection ( ref_dac->out0,
                                        parentSlice->tileOuts[3].in0 );
  //conn2
	Connection integ_to_tile= Connection ( out0,
                                         parentSlice->tileOuts[3].in0 );
  integ_to_tile.setConn();
  ref_to_tile.setConn();

  print_info("calibrate init cond");
  for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
    calib_table[nmos] = cutil::make_calib_table();
    this->m_codes.port_cal[in0Id] = closed_loop_calib_table[nmos].state[0];
    this->m_codes.port_cal[out0Id] = closed_loop_calib_table[nmos].state[1];
    this->m_codes.nmos = nmos;
    for(int gain_cal=0; gain_cal < MAX_GAIN_CAL; gain_cal += 1){
      this->m_codes.gain_cal = gain_cal;
      update(this->m_codes);
      //TODO
      float score = 0.0;
      switch(obj){
      case CALIB_MINIMIZE_ERROR:
        // try to minimize the error between the expected and observed
        // time constant
        score = calibrateInitCondMinError(ref_dac);
        break;
      case CALIB_MAXIMIZE_DELTA_FIT:
        // try and choose time constants that produce good fits.
        score = calibrateInitCondMaxDeltaFit(ref_dac);
        break;
      default:
        error("unimplemented");
      }
      sprintf(FMTBUF,"nmos=%d gain_cal=%d score=%f",nmos,gain_cal,score);
      print_info(FMTBUF);
      cutil::update_calib_table(calib_table[nmos],score,1,gain_cal);
    }
  }
  integ_to_tile.brkConn();
  ref_to_tile.brkConn();

}
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

float tc_compute_score(calib_objective_t obj,
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
                                                                     cutil::calib_table_t (&calib_table)[MAX_NMOS],
                                                                     cutil::calib_table_t (&closed_loop_calib_table) [MAX_NMOS]){

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

  conn_out_to_tile.setConn();

  const int n_samples = 25;
  float nom_times[25],k_times[25];
  float nom_values[25],k_values[25];
  for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
    this->m_codes.nmos = nmos;
    this->m_codes.port_cal[in0Id] = closed_loop_calib_table[nmos].state[0];
    this->m_codes.port_cal[out0Id] = closed_loop_calib_table[nmos].state[1];
    calib_table[nmos] = cutil::make_calib_table();

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
      float score = tc_compute_score(obj,target_tc,tc_stats);
      cutil::update_calib_table(calib_table[nmos],score,1,gain_cal);
    }

    sprintf(FMTBUF,"BEST nmos=%d code=%d score=%f",
            nmos,
            calib_table[nmos].state[0],
            calib_table[nmos].score);
    print_info(FMTBUF);
  }

  conn_out_to_tile.brkConn();
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
                                                                       cutil::calib_table_t (&calib_table)[MAX_NMOS]){

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
    this->m_codes.nmos = nmos;
    this->m_codes.gain_cal = 32;
    this->m_codes.port_cal[out0Id] = 32;
    calib_table[nmos] = cutil::make_calib_table();
    for(int in0_cal=0; in0_cal < MAX_BIAS_CAL; in0_cal += 1){
      this->m_codes.port_cal[in0Id] = in0_cal;
      this->update(this->m_codes);
      float mean, variance;
      util::meas_steady_chip_out(this,mean,variance);
      float score = fabs(mean-target);
      cutil::update_calib_table(calib_table[nmos],score,2,in0_cal,32);
      /*
      sprintf(FMTBUF," codes=(%d,%d,32) target=%f mean=%f score=%f",
              nmos,in0_cal,target,mean,score_in[in0_cal]);
      print_info(FMTBUF);
      */
    }
    sprintf(FMTBUF,"nmos=%d BEST in0_code=%d score=%f",
            nmos, calib_table[nmos].state[0], calib_table[nmos].score);
    print_info(FMTBUF);
  }
  for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
    this->m_codes.nmos = nmos;
    this->m_codes.gain_cal = 32;
    this->m_codes.port_cal[in0Id] = calib_table[nmos].state[0];
    for(int out0_cal=0; out0_cal < MAX_BIAS_CAL; out0_cal += 1){
      this->m_codes.port_cal[out0Id] = out0_cal;
      this->update(this->m_codes);
      float mean, variance;
      util::meas_steady_chip_out(this,mean,variance);
      float score = fabs(mean-target);
      cutil::update_calib_table(calib_table[nmos],score,2,
                                calib_table[nmos].state[0],
                                out0_cal);
      /*
      sprintf(FMTBUF," codes=(%d,%d,%d) target=%f mean=%f score=%f",
              nmos,codes[nmos][0],out0_cal,target,mean,score_out[out0_cal]);
      print_info(FMTBUF);
      */
    }
    sprintf(FMTBUF,"nmos=%d BEST codes=(%d,%d) score=%f",
            nmos,
            calib_table[nmos].state[0],
            calib_table[nmos].state[1],
            calib_table[nmos].score);
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

  cutil::calib_table_t ol_calib_table[MAX_NMOS];
  cutil::calib_table_t cl_calib_table[MAX_NMOS];

  this->calibrateClosedLoopCircuit(obj,fan,cl_calib_table);

  // calibrating the initial condition
  //this->setRange(out0Id, RANGE_MED);
  this->calibrateInitCond(obj,val_dac,ol_calib_table,cl_calib_table);
  // gain cal does not control time constant, but it does change it
  //this->calibrateOpenLoopCircuit(obj,val_dac,ol_calib_table,cl_calib_table);
  float scores[MAX_NMOS];
  for(int i=0; i < MAX_NMOS; i += 1){
    scores[i] = cl_calib_table[i].score + ol_calib_table[i].score;
  }

  int best_nmos = util::find_minimum(scores,MAX_NMOS);
  int best_gain_cal = ol_calib_table[best_nmos].state[0];
  int best_port_cal_in0 = cl_calib_table[best_nmos].state[0];
  int best_port_cal_out0 = cl_calib_table[best_nmos].state[1];
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
