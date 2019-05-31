#include "AnalogLib.h"
#include <float.h>
#include "assert.h"
#include "calib_util.h"
#include "slice.h"
#include "dac.h"

void Fabric::Chip::Tile::Slice::Dac::characterize(profile_t& result){
  if(m_codes.source == DSRC_MEM){
    dac_code_t backup = m_codes;
    // spoof source.
    m_codes.source = DSRC_LUT0;
    characterizeTarget(result);
    update(backup);
  }
  else{
    characterizeTarget(result);
  }
}

void Fabric::Chip::Tile::Slice::Dac::characterizeTarget(profile_t& result)
{
  if(m_codes.source == DSRC_MEM){
    prof::init_profile(result);
    measure(result);
  }
  else{
    dac_code_t backup = m_codes;
    m_codes.source = DSRC_MEM;
    float vals[SIZE1D];
    int n = prof::data_1d(vals,SIZE1D);
    // measure how good the dac is at writing certain values.
    prof::init_profile(result);
    for(int i=0; i < n; i+=1){
      setConstant(vals[i]);
      measure(result);
    }
    update(backup);
  }

}


void Fabric::Chip::Tile::Slice::Dac::measure(profile_t& result)
{
  if(!m_codes.enable){
    print_log("DAC not enabled");
    return;
  }
  bool hiRange = (m_codes.range == RANGE_HIGH);
  float scf = util::range_to_coeff(m_codes.range);
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
  float target = m_codes.const_val*scf;
  prof::init_profile(base_code_result);
	if (hiRange) {
    // feed dac output into scaling down multiplier input
		ref_to_tile.setConn();
    target = make_reference_dac(calib,
                       base_code_result,
                       base_code, this,ref_dac);
	}
  dac_to_tile.setConn();
	tile_to_chip.setConn();

  float mean=0.0,variance=0.0;
  util::meas_dist_chip_out(this,mean,variance);
  prof::add_prop(result, out0Id,
                 m_codes.const_val*scf,
                 mean-target,
                 variance);

  if (hiRange) {
    // feed dac output into scaling down multiplier input
		ref_to_tile.brkConn();
    ref_dac->update(codes_ref);
    // feed output of scaledown multiplier to tile output.
	}
	tile_to_chip.brkConn();
  dac_to_tile.brkConn();

  cutil::restore_conns(calib);
  update(codes_self);
}


