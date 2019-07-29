#include "AnalogLib.h"
#include <float.h>
#include "assert.h"
#include "calib_util.h"
#include "slice.h"
#include "dac.h"


void dmeas_make_ref_dac(Fabric::Chip::Tile::Slice::Dac * aux_dac,float target){
  aux_dac->setEnable(true);
  aux_dac->setRange(RANGE_HIGH);
  aux_dac->setSource(DSRC_MEM);
  aux_dac->setInv(false);
  aux_dac->setConstant(-target/10.0);
}

profile_t Fabric::Chip::Tile::Slice::Dac::measure(float in)
{
  if(!m_codes.enable){
    print_log("DAC not enabled");
    return;
  }
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
  ref_to_tile.setConn();
  cutil::fast_make_ref_dac(ref_dac,target);
  dac_to_tile.setConn();
	tile_to_chip.setConn();
  float mean,variance;
  calib.success &= cutil::measure_signal_robust(this,
                                                ref_dac,
                                                target,
                                                false,
                                                mean,
                                                variance);


  float ref = ref_dac->fastMeasureValue();
  sprintf(FMTBUF,"PARS target=%f ref=%f mean=%f",
          target,ref,mean);
  print_info(FMTBUF);
  float bias = (mean-(target+ref));
  profile_t result = prof::make_profile(out0Id,
                                        0,
                                        m_codes.const_val*scf,
                                        m_codes.const_val,
                                        0.0,
                                        bias,
                                        variance);
  if(!calib.success){
    result.mode = 255;
  }
  ref_to_tile.brkConn();
  ref_dac->update(codes_ref);
	tile_to_chip.brkConn();
  dac_to_tile.brkConn();

  cutil::restore_conns(calib);
  update(codes_dac);
  return result;
}


