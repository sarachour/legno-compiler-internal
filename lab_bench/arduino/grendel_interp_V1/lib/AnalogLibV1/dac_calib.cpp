#include "AnalogLib.h"
#include <float.h>
#include "assert.h"
#include "calib_util.h"
#include "slice.h"
#include "dac.h"


bool Fabric::Chip::Tile::Slice::Dac::calibrate (profile_t& result,
                                                const float max_error)
{
  dac_code_t backup = m_codes;
  m_codes.source = DSRC_MEM;
  setConstant(1.0);
  float succ = calibrateTarget(result,max_error);
  m_codes.source = backup.source;
  m_codes.const_val = backup.const_val;
  m_codes.const_code = backup.const_code;
  update(m_codes);
  return succ;

}




bool Fabric::Chip::Tile::Slice::Dac::calibrateTarget (profile_t& result,
                                                      const float max_error)
{
  //setConstantCode(round(constant*128.0+128.0));
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
  profile_t base_code_result;
  prof::init_profile(base_code_result);
  float target = m_codes.const_val;
	if (hiRange) {
    // feed dac output into scaling down multiplier input
		ref_to_tile.setConn();
    target = make_reference_dac(calib,
                                base_code_result,
                                base_code, this,ref_dac);
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
  prof::init_profile(result);
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
