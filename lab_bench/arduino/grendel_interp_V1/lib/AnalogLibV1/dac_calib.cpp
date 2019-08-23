#include "AnalogLib.h"
#include <float.h>
#include "assert.h"
#include "calib_util.h"
#include "slice.h"
#include "dac.h"
#include "Arduino.h"

#define MAX_HIDDEN_STATE 5
typedef struct {
  unsigned char state[MAX_HIDDEN_STATE];
  float score;
  bool set;
} calib_table_t;

calib_table_t make_calib_table(){
  calib_table_t st;
  st.set = false;
  for(int i=0; i < MAX_HIDDEN_STATE; i+=1){
    st.state[i]=0;
  }
  return st;
}

void update_calib_table(calib_table_t& table, float new_score, int n, ...){
  va_list valist;
  va_start(valist, n);
  if(not table.set || table.score > new_score){
    table.set = true;
    table.score = new_score;
    assert(n < MAX_HIDDEN_STATE);
    for(int i=0; i < n; i += 1){
      table.state[i] = va_arg(valist, int);
    }
  }
  va_end(valist);
}

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
  calib_table_t calib_table = make_calib_table();
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
      update_calib_table(calib_table,score,2,nmos,gain_cal);
      sprintf(FMTBUF,"nmos=%d\tgain_cal=%d\tscore=%f",nmos,gain_cal,score);
      print_info(FMTBUF);
    }
  }
  int best_nmos = calib_table.state[0];
  int best_gain_cal = calib_table.state[1];
  print_info("======");
  sprintf(FMTBUF,"BEST nmos=%d\tgain_cal=%d\tscore=%f",
          best_nmos,best_gain_cal,calib_table.score);
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
}

#define CALIB_NPTS 2
const float TEST_POINTS[CALIB_NPTS] = {0,0.8};

float Fabric::Chip::Tile::Slice::Dac::calibrateMaxDeltaFit(){
  float gains[CALIB_NPTS];
  float bias;
  int m=0;
  for(int i=0; i < CALIB_NPTS; i += 1){
    float const_val = TEST_POINTS[i];
    this->setConstant(const_val);
    float target = Fabric::Chip::Tile::Slice::Dac::computeOutput(this->m_codes);
    float mean,variance;
    mean = this->fastMeasureValue(variance);
    if(fabs(target) > 0.0){
      gains[m] = mean/target;
      m+=1;
    }
    else{
      bias = mean;
    }
  }
  float score_total = 0;
  float gain_mean,gain_variance;
  util::distribution(gains,m,
                     gain_mean,
                     gain_variance);
  float score = gain_variance/gain_mean;
  return score;

}
float Fabric::Chip::Tile::Slice::Dac::calibrateMinError(){
  float score_total = 0;
  for(int i=0; i < CALIB_NPTS; i += 1){
    float const_val = TEST_POINTS[i];
    this->setConstant(const_val);
    float target = Fabric::Chip::Tile::Slice::Dac::computeOutput(this->m_codes);
    float mean,variance;
    mean = this->fastMeasureValue(variance);
    score_total += fabs(target-mean);
  }
  return score_total/CALIB_NPTS;
}
