#include "AnalogLib.h"
#include "assert.h"
#include "calib_util.h"

void Fabric::Chip::Tile::Slice::Fanout::measureZero(float &out0bias,
                                                    float &out1bias,
                                                    float &out2bias){
  // backup and clobber state.
  cutil::calibrate_t calib;
  fanout_code_t codes_fan = this->m_codes;
  cutil::initialize(calib);
  cutil::buffer_fanout_conns(calib,this);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,
                              parentSlice->parentTile->parentChip
                              ->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);
  Connection tileout_to_chipout = Connection (parentSlice->tileOuts[3].out0,
                                              parentSlice->parentTile->parentChip
                                              ->tiles[3].slices[2].chipOutput->in0);
  Connection conn_out0 = Connection (this->out0,parentSlice->tileOuts[3].in0);
  Connection conn_out1 = Connection (this->out1,parentSlice->tileOuts[3].in0);
  Connection conn_out2 = Connection (this->out2,parentSlice->tileOuts[3].in0);
  tileout_to_chipout.setConn();

  conn_out0.setConn();
  out0bias = util::meas_chip_out(this);
  conn_out0.brkConn();
  conn_out1.setConn();
  out1bias = util::meas_chip_out(this);
  conn_out1.brkConn();
  conn_out2.setConn();
  out2bias = util::meas_chip_out(this);
  conn_out2.brkConn();
  tileout_to_chipout.brkConn();

  this->update(codes_fan);
  cutil::restore_conns(calib);
}
float Fabric::Chip::Tile::Slice::Fanout::getScore(calib_objective_t obj,
                Fabric::Chip::Tile::Slice::Dac * val_dac,
                Fabric::Chip::Tile::Slice::Dac * ref_dac,
                ifc outId
                )
{
  switch(obj){
  case CALIB_MINIMIZE_ERROR:
    return calibrateMinError(val_dac,ref_dac,outId);
    break;
  case CALIB_MAXIMIZE_DELTA_FIT:
    return calibrateMaxDeltaFit(val_dac,ref_dac,outId);
    break;
  case CALIB_FAST:
    return calibrateFast(val_dac,ref_dac,outId);
    break;
  default:
    error("unknown obj function");
  }
}


void Fabric::Chip::Tile::Slice::Fanout::calibrate(calib_objective_t obj){
  //backup state
  cutil::calibrate_t calib;
  cutil::initialize(calib);

  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;
  Dac * val_dac = parentSlice->dac;
  fanout_code_t codes_fanout = m_codes;
  dac_code_t codes_ref_dac = ref_dac->m_codes;
  dac_code_t codes_val_dac = val_dac->m_codes;
  cutil::buffer_fanout_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_dac_conns(calib,val_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,
                              parentSlice->parentTile->parentChip
                              ->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  //setup circuit
  Connection tileout_to_chipout = Connection (parentSlice->tileOuts[3].out0,
                                          parentSlice->parentTile->parentChip
                                          ->tiles[3].slices[2].chipOutput->in0);
  Connection conn_out0 = Connection (this->out0,parentSlice->tileOuts[3].in0);
  Connection conn_out1 = Connection (this->out1,parentSlice->tileOuts[3].in0);
  Connection conn_out2 = Connection (this->out2,parentSlice->tileOuts[3].in0);
  Fabric::Chip::Connection ref_to_tileout =
    Fabric::Chip::Connection ( ref_dac->out0, parentSlice->tileOuts[3].in0);
  Fabric::Chip::Connection val_to_fanout =
    Fabric::Chip::Connection ( val_dac->out0, this->in0);

  // always enable third output so all of them can be calibrated
  this->setThird(true);
  //enable dacs
  ref_dac->setEnable(true);
  val_dac->setEnable(true);
  ref_to_tileout.setConn();
  val_to_fanout.setConn();
  tileout_to_chipout.setConn();

  cutil::calib_table_t calib_table[MAX_NMOS];;
  for(int nmos = 0; nmos < MAX_NMOS; nmos += 1){
    // bind best bias code for out0
    float tmp_score = 0.0;
    calib_table[nmos] = cutil::make_calib_table();

    this->m_codes.port_cal[out0Id] = 32;
    this->m_codes.port_cal[out1Id] = 32;
    this->m_codes.port_cal[out2Id] = 32;
    conn_out0.setConn();
    for(int bias_cal=0; bias_cal < MAX_BIAS_CAL; bias_cal+=1){
      this->m_codes.port_cal[out0Id] = bias_cal;
      update(this->m_codes);
      float score = getScore(obj,val_dac,ref_dac,out0Id);
      cutil::update_calib_table(calib_table[nmos],score,3,bias_cal,32,32);
    }
    this->m_codes.port_cal[out0Id] = calib_table[nmos].state[0];
    conn_out0.brkConn();
    sprintf(FMTBUF,"nmos=%d bias_codes=(%d,%d,%d) score=%f",
            nmos,
            calib_table[nmos].state[0],
            calib_table[nmos].state[1],
            calib_table[nmos].state[2],
            calib_table[nmos].score);
    print_info(FMTBUF);
    // find the best code for out1
    conn_out1.setConn();
    tmp_score = calib_table[nmos].score;
    for(int bias_cal=0; bias_cal < MAX_BIAS_CAL; bias_cal+=1){
      this->m_codes.port_cal[out1Id] = bias_cal;
      update(this->m_codes);
      float score = getScore(obj,val_dac,ref_dac,out1Id);
      cutil::update_calib_table(calib_table[nmos],
                                max(score,tmp_score),
                                3,
                                calib_table[nmos].state[0],
                                bias_cal,
                                32);
    }
    this->m_codes.port_cal[out1Id] = calib_table[nmos].state[1];
    conn_out1.brkConn();
    sprintf(FMTBUF,"nmos=%d bias_codes=(%d,%d,%d) score=%f",
            nmos,
            calib_table[nmos].state[0],
            calib_table[nmos].state[1],
            calib_table[nmos].state[2],
            calib_table[nmos].score);
    print_info(FMTBUF);
    // find the best code for out2
    conn_out2.setConn();
    tmp_score = calib_table[nmos].score;
    for(int bias_cal=0; bias_cal < MAX_BIAS_CAL; bias_cal+=1){
      this->m_codes.port_cal[out2Id] = bias_cal;
      update(this->m_codes);
      float score = getScore(obj,val_dac,ref_dac,out2Id);
      cutil::update_calib_table(calib_table[nmos],
                                max(score,tmp_score),
                                3,
                                calib_table[nmos].state[0],
                                calib_table[nmos].state[1],
                                bias_cal);
    }
    this->m_codes.port_cal[out2Id] = calib_table[nmos].state[2];
    conn_out2.brkConn();

    sprintf(FMTBUF,"nmos=%d bias_codes=(%d,%d,%d) score=%f",
            nmos,
            calib_table[nmos].state[0],
            calib_table[nmos].state[1],
            calib_table[nmos].state[2],
            calib_table[nmos].score);
    print_info(FMTBUF);
  }

  float scores[MAX_NMOS];
  for(int i=0; i < MAX_NMOS; i+=1){
    scores[i] = calib_table[i].score;
  }
  ref_to_tileout.brkConn();
  val_to_fanout.brkConn();
  tileout_to_chipout.brkConn();
  cutil::restore_conns(calib);
  ref_dac->m_codes = codes_ref_dac;
  val_dac->m_codes = codes_val_dac;
  this->m_codes = codes_fanout;
  //set best hidden codes
  int best_nmos=0;
  int best_score=0;
  best_nmos = util::find_minimum(scores,MAX_NMOS);
  best_score = calib_table[best_nmos].score;
  this->m_codes.port_cal[out0Id] = calib_table[best_nmos].state[0];
  this->m_codes.port_cal[out1Id] = calib_table[best_nmos].state[1];
  this->m_codes.port_cal[out2Id] = calib_table[best_nmos].state[2];
  this->m_codes.nmos = best_nmos;
  update(this->m_codes);
  return;
}

#define CALIB_NPTS 3
const float TEST_POINTS[CALIB_NPTS] = {0,-0.5,1};


float Fabric::Chip::Tile::Slice::Fanout::calibrateMaxDeltaFit(Fabric::Chip::Tile::Slice::Dac * val_dac,
                                                              Fabric::Chip::Tile::Slice::Dac * ref_dac,
                                                              ifc out_id) {

  return 0.0;
}
float Fabric::Chip::Tile::Slice::Fanout::calibrateMinError(Fabric::Chip::Tile::Slice::Dac * val_dac,
                                                           Fabric::Chip::Tile::Slice::Dac * ref_dac,
                                                           ifc out_id) {
  float score_total = 0;
  int total = 0;
  for(int i=0; i < CALIB_NPTS; i += 1){
    float mean,dummy;
    bool measure_steady_state = false;
    val_dac->setConstant(TEST_POINTS[i]);
    float in_val = val_dac->fastMeasureValue(dummy);
    float target =Fabric::Chip::Tile::Slice::Fanout::computeOutput(this->m_codes,
                                                                   out_id,
                                                                   in_val);
    bool succ = cutil::measure_signal_robust(this, ref_dac, target,
                                             measure_steady_state,
                                             mean,
                                             dummy);
    if(succ){
      score_total = fabs(target-mean);
      total += 1;
    }
  }
  if(total > 0)
    return score_total/total;
  else
    error("no valid points");
}

float Fabric::Chip::Tile::Slice::Fanout::calibrateFast(Fabric::Chip::Tile::Slice::Dac * val_dac,
                    Fabric::Chip::Tile::Slice::Dac * ref_dac,
                    ifc out_id){
  Fabric::Chip::Connection val_to_fanout =
    Fabric::Chip::Connection ( val_dac->out0, this->in0);
  Fabric::Chip::Connection ref_to_tileout =
    Fabric::Chip::Connection ( ref_dac->out0, parentSlice->tileOuts[3].in0);
  val_to_fanout.brkConn();
  ref_to_tileout.brkConn();
  float meas = util::meas_chip_out(this);
  val_to_fanout.setConn();
  ref_to_tileout.setConn();
  return fabs(meas);
}
