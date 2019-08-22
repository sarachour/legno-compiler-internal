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
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;
  dac_code_t codes_ref = ref_dac->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);

  cutil::buffer_dac_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  //setup
	Connection dac_to_tile = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
  Connection ref_to_tile = Connection ( ref_dac->out0,
                                        parentSlice->tileOuts[3].in0 );

  dac_to_tile.setConn();
	tile_to_chip.setConn();
	ref_to_tile.setConn();
  m_codes.source = DSRC_MEM;

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
        score = calibrateMinError(ref_dac);
        break;
      case CALIB_MAXIMIZE_DELTA_FIT:
        score = calibrateMaxDeltaFit(ref_dac);
        break;
      }
      calib_table[nmos][gain_cal] = score;
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

  // teardown
  update(codes_dac);
  ref_to_tile.brkConn();
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

float Fabric::Chip::Tile::Slice::Dac::calibrateMaxDeltaFit(Fabric::Chip::Tile::Slice::Dac * ref_dac){
  return 0.0;
}
float Fabric::Chip::Tile::Slice::Dac::calibrateMinError(Fabric::Chip::Tile::Slice::Dac * ref_dac){
  const int NPTS = 5;
  float test_points[5] = {0,1,-1,0.5,-0.5};
  float score_total = 0;
  for(int i=0; i < NPTS; i += 1){
    float const_val = test_points[i];
    this->setConstant(const_val);
    float target = Fabric::Chip::Tile::Slice::Dac::compute_output(this->m_codes);
    bool steady = false;
    float mean, variance;
    bool success = cutil::measure_signal_robust(this,
                                                 ref_dac,
                                                 target,
                                                 steady,
                                                 mean,
                                                 variance);
    if(success){
      score_total += fabs(target-mean);
    }
  }
  return score_total/NPTS;
}
/*
bool Fabric::Chip::Tile::Slice::Dac::calibrateTarget (profile_t& result,
                                                      const float max_error)
{
  if(!m_codes.enable){
    print_log("DAC not enabled");
    return true;
  }
  if(m_codes.source != DSRC_MEM){
    print_log("DAC must have memory as source.");
    return false;
  }
  bool hiRange = (m_codes.range == RANGE_HIGH);
  int ic_sign = m_codes.inv ? -1.0 : 1.0;
  float const_val = m_codes.const_val*util::range_to_coeff(m_codes.range)*ic_sign;
  cutil::calibrate_t calib;
  cutil::initialize(calib);

  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;
  dac_code_t codes_self = m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;

  update(m_codes);

  cutil::buffer_dac_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);
  // conn0
	Connection ref_to_tile = Connection ( ref_dac->out0,
                                        parentSlice->tileOuts[3].in0 );

  // conn2
	Connection dac_to_tile = Connection ( out0, parentSlice->tileOuts[3].in0 );
  // conn3
	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );

  dac_code_t base_code;
  float target = m_codes.const_val;
	if (hiRange) {
    // feed dac output into scaling down multiplier input
		ref_to_tile.setConn();
    target = make_reference_dac(calib,base_code, this,ref_dac);
	}
  dac_to_tile.setConn();
	tile_to_chip.setConn();

  sprintf(FMTBUF, "dac-value: %f %d %d", m_codes.const_val,
          m_codes.const_code,
          m_codes.range);
  print_log(FMTBUF);
  bool succ = false;
  int code = m_codes.const_code;
  float target_sign = target >= 0 ? 1.0 : -1.0;
  int delta = 0;
  while(!succ){
    float error = 0.0;
    if(!calib.success){
      print_info("failed to calibrate dependency");
      break;
    }
    if(code + delta > 255
       || code + delta < 0){
      print_info("outside acceptable code range");
      delta = 0;
      break;
    }
    setConstantCode(code + delta);
    succ = binsearch::find_bias_and_nmos(
                                         this,
                                         target,
                                         max_error,
                                         m_codes.gain_cal,
                                         m_codes.nmos,
                                         error,
                                         MEAS_CHIP_OUTPUT);
    sprintf(FMTBUF,"const code=%d target=%f meas=%f",
            code+delta,
            target,
            target+error);
    print_info(FMTBUF);
    if(!succ){
      if(error*target_sign <= 0){
        delta += target_sign;
      }
      else{
        delta += target_sign*(-1.0);
      }
    }
  }
  if (hiRange) {
    // feed dac output into scaling down multiplier input
		ref_to_tile.brkConn();
    ref_dac->update(codes_ref);
    // feed output of scaledown multiplier to tile output.
	}
	tile_to_chip.brkConn();
  dac_to_tile.brkConn();
  cutil::restore_conns(calib);
  codes_self.nmos = m_codes.nmos;
  codes_self.gain_cal = m_codes.gain_cal;
  codes_self.const_code = code+delta;
  update(codes_self);
	return succ && calib.success;
}
*/
