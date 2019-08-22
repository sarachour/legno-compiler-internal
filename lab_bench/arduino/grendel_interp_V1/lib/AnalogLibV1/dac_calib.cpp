#include "AnalogLib.h"
#include <float.h>
#include "assert.h"
#include "calib_util.h"
#include "slice.h"
#include "dac.h"


void Fabric::Chip::Tile::Slice::Dac::calibrate (calib_objective_t obj)
{
  // backup state
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  dac_code_t codes_dac = m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);

  cutil::buffer_dac_conns(calib,this);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  //setup
	Connection dac_to_tile = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
  this->m_codes.source = DSRC_MEM;
  dac_to_tile.setConn();
	tile_to_chip.setConn();

  //populate calibration table
  float calib_table[MAX_NMOS][MAX_GAIN_CAL];
  for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
    this->m_codes.nmos = nmos;
    for(int gain_cal=0; gain_cal < MAX_GAIN_CAL; gain_cal += 1){
      this->m_codes.gain_cal=gain_cal;
      //compute score for combo
      float score = 0;
      switch(obj){
      case CALIB_MINIMIZE_ERROR:
        score = calibrateMinError();
        break;
      case CALIB_MAXIMIZE_DELTA_FIT:
        score = calibrateMaxDeltaFit();
        break;
      }
      calib_table[nmos][gain_cal] = score;
      sprintf(FMTBUF,"nmos=%d\tgain_cal=%d\tscore=%f",nmos,gain_cal,score);
      print_info(FMTBUF);
    }
  }

  //chose best_codes
  int best_nmos = 0;
  int best_gain_cal = 0;
  float best_score = calib_table[best_nmos][best_gain_cal];
  for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
    for(int gain_cal=0; gain_cal < MAX_GAIN_CAL; gain_cal += 1){
      if(calib_table[nmos][gain_cal] < best_score){
        best_nmos = nmos;
        best_gain_cal = gain_cal;
        best_score = calib_table[best_nmos][best_gain_cal];
      }
    }
  }
  best_score = calib_table[best_nmos][best_gain_cal];
  print_info("======");
  sprintf(FMTBUF,"BEST nmos=%d\tgain_cal=%d\tscore=%f",
          best_nmos,best_gain_cal,best_score);
  print_info(FMTBUF);

  // teardown
  update(codes_dac);
  tile_to_chip.brkConn();
  dac_to_tile.brkConn();
  cutil::restore_conns(calib);
  //set hidden codes to best codes
  this->m_codes = codes_dac;
  this->m_codes.nmos = best_nmos;
  this->m_codes.gain_cal = best_gain_cal;
  update(this->m_codes);
  return;
}

float Fabric::Chip::Tile::Slice::Dac::calibrateMaxDeltaFit(){
  const int NPTS = 5;
  float test_points[5] = {0,1,-1,0.5,-0.5};
  float gains[5];
  float bias;
  for(int i=0; i < NPTS; i += 1){
    float const_val = test_points[i];
    this->setConstant(const_val);
    float target = Fabric::Chip::Tile::Slice::Dac::computeOutput(this->m_codes);
    float mean,variance;
    mean = this->fastMeasureValue(variance);
    if(fabs(target) > 0.0){
      gains[i] = mean/target;
    }
    else{
      bias = mean;
    }
  }
  float score_total = 0;
  float gain_mean,gain_variance;
  util::distribution(gains,NPTS,
                     gain_mean,
                     gain_variance);
  float score = gain_variance/gain_mean;
  return score;

}
float Fabric::Chip::Tile::Slice::Dac::calibrateMinError(){
  const int NPTS = 5;
  float test_points[5] = {0,1,-1,0.5,-0.5};
  float score_total = 0;
  for(int i=0; i < NPTS; i += 1){
    float const_val = test_points[i];
    this->setConstant(const_val);
    float target = Fabric::Chip::Tile::Slice::Dac::computeOutput(this->m_codes);
    float mean,variance;
    mean = this->fastMeasureValue(variance);
    score_total += fabs(target-mean);
  }
  return score_total/NPTS;
}
