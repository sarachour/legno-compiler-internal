#include "AnalogLib.h"
#include "assert.h"
#include "calib_util.h"

void fmeas_make_ref_dac(Fabric::Chip::Tile::Slice::Dac * aux_dac,float target){
  aux_dac->setEnable(true);
  aux_dac->setRange(RANGE_HIGH);
  aux_dac->setSource(DSRC_MEM);
  aux_dac->setInv(false);
  aux_dac->setConstant(-target/10.0);
}


profile_t Fabric::Chip::Tile::Slice::Fanout::measure(char mode, float input) {

  Fabric::Chip::Tile::Slice::Dac * val_dac = parentSlice->dac;
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;

  fanout_code_t codes_fan = m_codes;
  dac_code_t codes_dac = val_dac->m_codes;
  dac_code_t codes_ref_dac = ref_dac->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_fanout_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_dac_conns(calib,val_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,
                              parentSlice->parentTile->parentChip
                              ->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  dac_code_t dac_code_value;
  dac_code_t dac_code_ref;

  float in_target = input*util::range_to_coeff(m_codes.range[in0Id]);
  in_target = val_dac->fastMakeValue(in_target);

  Connection dac_to_fan = Connection ( val_dac->out0, in0 );
  Connection tile_to_chip = Connection (parentSlice->tileOuts[3].out0,
                                parentSlice->parentTile->parentChip \
                                ->tiles[3].slices[2].chipOutput->in0);
  Connection ref_to_tile = Connection ( ref_dac->out0,
                                        parentSlice->tileOuts[3].in0 );

  unsigned char port = 0;
  float out_target;
  switch(mode){
  case 0:
    Connection (out0, this->parentSlice->tileOuts[3].in0).setConn();
    port = out0Id;
    out_target = in_target*util::sign_to_coeff(m_codes.inv[out0Id]);
    break;
  case 1:
    Connection(out1, this->parentSlice->tileOuts[3].in0).setConn();
    port = out1Id;
    out_target = in_target*util::sign_to_coeff(m_codes.inv[out1Id]);
    break;
  case 2:
    setThird(true);
    Connection(out2, this->parentSlice->tileOuts[3].in0).setConn();
    out_target = in_target*util::sign_to_coeff(m_codes.inv[out2Id]);
    port = out2Id;
    break;
  default:
    error("unknown mode");
  }

  dac_to_fan.setConn();
	tile_to_chip.setConn();

  cutil::fast_make_dac(ref_dac, -out_target);
  ref_to_tile.setConn();

  float mean,variance,dummy;
  calib.success &= cutil::measure_signal_robust(this,
                                                ref_dac,
                                                out_target,
                                                false,
                                                mean,
                                                variance);
  float ref = ref_dac->fastMeasureValue(dummy);
  sprintf(FMTBUF,"PARS target=%f ref=%f mean=%f",
          out_target,ref,mean);
  print_info(FMTBUF);

  float bias = (mean-(out_target+ref));
  profile_t prof = prof::make_profile(port,
                                      mode,
                                      out_target,
                                      in_target,
                                      0.0,
                                      bias,
                                      variance);
  if(!calib.success){
    prof.mode = 255;
  }
  dac_to_fan.brkConn();
  tile_to_chip.brkConn();
  ref_to_tile.brkConn();
  switch(mode){
  case 0:
    Connection (out0, this->parentSlice->tileOuts[3].in0).brkConn();
    break;
  case 1:
    Connection(out2, this->parentSlice->tileOuts[3].in0).brkConn();
    break;
  case 2:
    setThird(false);
    Connection(out2, this->parentSlice->tileOuts[3].in0).brkConn();
    break;
  }
	setEnable ( false );
  cutil::restore_conns(calib);
  this->update(codes_fan);
  return prof;
}
