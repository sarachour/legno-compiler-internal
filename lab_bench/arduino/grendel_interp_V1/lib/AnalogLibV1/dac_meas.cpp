#include "AnalogLib.h"
#include <float.h>
#include "assert.h"
#include "calib_util.h"
#include "slice.h"
#include "dac.h"



profile_t Fabric::Chip::Tile::Slice::Dac::measure(float in)
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
  dac_code_t codes_dac = m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;

  m_codes.source = DSRC_MEM;
  setConstant(in);
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
  float target = m_codes.const_val*scf;
	if (hiRange) {
    // feed dac output into scaling down multiplier input
		ref_to_tile.setConn();
    target = make_reference_dac(calib,
                       base_code, this,ref_dac);
	}
  dac_to_tile.setConn();
	tile_to_chip.setConn();

  float mean=0.0,variance=0.0;
  util::meas_dist_chip_out(this,mean,variance);
  profile_t result = prof::make_profile(out0Id,
                                        0,
                                        m_codes.const_val*scf,
                                        m_codes.const_val,
                                        0.0,
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
  update(codes_dac);
  return result;
}


