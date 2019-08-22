#include "AnalogLib.h"
#include "assert.h"
#include "calib_util.h"

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

  ref_dac->setEnable(true);
  val_dac->setEnable(true);
  ref_to_tileout.setConn();
  val_to_fanout.setConn();
  tileout_to_chipout.setConn();

  float calib_table[MAX_NMOS];
  int calib_table_codes[MAX_NMOS][3];

  for(int nmos = 0; nmos < MAX_NMOS; nmos += 1){
    float scores[MAX_BIAS_CAL];
    float best_scores[3];
    // bind best bias code for out0
    conn_out0.setConn();
    for(int bias_cal=0; bias_cal < MAX_BIAS_CAL; bias_cal+=1){
      this->m_codes.port_cal[out0Id] = bias_cal;
      update(this->m_codes);
      switch(obj){
      case CALIB_MINIMIZE_ERROR:
        scores[bias_cal] = calibrateMinError(val_dac,ref_dac,out0Id);
        break;
      case CALIB_MAXIMIZE_DELTA_FIT:
        scores[bias_cal] = calibrateMaxDeltaFit(val_dac,ref_dac,out0Id);
        break;
      }
      sprintf(FMTBUF," %d nmos=%d bias_cal=%d score=%f",0,nmos,bias_cal,
              scores[bias_cal]);
      print_info(FMTBUF);
    }
    this->m_codes.port_cal[out0Id] = 32;
    calib_table_codes[nmos][0] = util::find_minimum(scores,MAX_BIAS_CAL);
    best_scores[0] = scores[calib_table_codes[nmos][0]];
    conn_out0.brkConn();

    // find the best code for out1
    conn_out1.setConn();
    for(int bias_cal=0; bias_cal < MAX_BIAS_CAL; bias_cal+=1){
      this->m_codes.port_cal[out1Id] = bias_cal;
      update(this->m_codes);
      switch(obj){
      case CALIB_MINIMIZE_ERROR:
        scores[bias_cal] = calibrateMinError(val_dac,ref_dac,out1Id);
        break;
      case CALIB_MAXIMIZE_DELTA_FIT:
        scores[bias_cal] = calibrateMaxDeltaFit(val_dac,ref_dac,out1Id);
        break;
      }
      sprintf(FMTBUF," %d nmos=%d bias_cal=%d score=%f",1,nmos,bias_cal,
              scores[bias_cal]);
      print_info(FMTBUF);
    }
    this->m_codes.port_cal[out1Id] = 32;
    calib_table_codes[nmos][1] = util::find_minimum(scores,MAX_BIAS_CAL);
    best_scores[1] = scores[calib_table_codes[nmos][1]];
    conn_out1.brkConn();

    // find the best code for out2
    conn_out2.setConn();
    for(int bias_cal=0; bias_cal < MAX_BIAS_CAL; bias_cal+=1){
      this->m_codes.port_cal[out2Id] = bias_cal;
      update(this->m_codes);
      switch(obj){
      case CALIB_MINIMIZE_ERROR:
        scores[bias_cal] = calibrateMinError(val_dac,ref_dac,out2Id);
        break;
      case CALIB_MAXIMIZE_DELTA_FIT:
        scores[bias_cal] = calibrateMaxDeltaFit(val_dac,ref_dac,out2Id);
        break;
      }
      sprintf(FMTBUF," %d nmos=%d bias_cal=%d score=%f",2,nmos,bias_cal,
              scores[bias_cal]);
      print_info(FMTBUF);
    }
    this->m_codes.port_cal[out2Id] = 32;
    calib_table_codes[nmos][2] = util::find_minimum(scores,MAX_BIAS_CAL);
    best_scores[2] = scores[calib_table_codes[nmos][2]];
    conn_out2.brkConn();

    calib_table[nmos] = util::find_maximum(best_scores,3);
    sprintf(FMTBUF,"nmos=%d bias_codes=[%d,%d,%d] score=%f", nmos,
            calib_table_codes[nmos][0],
            calib_table_codes[nmos][1],
            calib_table_codes[nmos][2],
            calib_table[nmos]);
    print_info(FMTBUF);
  }

  int best_nmos=0;
  int best_score=0;
  best_nmos = util::find_maximum(calib_table,MAX_NMOS);
  best_score = calib_table[best_nmos];
  ref_to_tileout.brkConn();
  val_to_fanout.brkConn();
  tileout_to_chipout.brkConn();
  cutil::restore_conns(calib);
  ref_dac->m_codes = codes_ref_dac;
  val_dac->m_codes = codes_val_dac;
  this->m_codes = codes_fanout;
  //set best hidden codes
  this->m_codes.port_cal[out0Id] = calib_table_codes[best_nmos][0];
  this->m_codes.port_cal[out1Id] = calib_table_codes[best_nmos][1];
  this->m_codes.port_cal[out2Id] = calib_table_codes[best_nmos][2];
  this->m_codes.nmos = best_nmos;
  update(this->m_codes);
  return;
}
float Fabric::Chip::Tile::Slice::Fanout::calibrateMaxDeltaFit(Fabric::Chip::Tile::Slice::Dac * val_dac,
                                                              Fabric::Chip::Tile::Slice::Dac * ref_dac,
                                                              ifc out_id) {

  return 0.0;
}
float Fabric::Chip::Tile::Slice::Fanout::calibrateMinError(Fabric::Chip::Tile::Slice::Dac * val_dac,
                                                           Fabric::Chip::Tile::Slice::Dac * ref_dac,
                                                           ifc out_id) {
  const int NPTS = 3;
  float test_points[3] = {0,-0.5,1};
  float score_total = 0;
  int total = 0;
  for(int i=0; i < NPTS; i += 1){
    float mean,dummy;
    bool measure_steady_state = false;
    val_dac->setConstant(test_points[i]);
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
