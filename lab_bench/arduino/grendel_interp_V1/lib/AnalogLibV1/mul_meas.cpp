#include "AnalogLib.h"
#include "fu.h"
#include "calib_util.h"
#include "profile.h"
#include <float.h>



profile_t Fabric::Chip::Tile::Slice::Multiplier::measure(float in0val,float in1val) {
  if(this->m_codes.vga){
    return measure_vga(in0val,in1val);
  }
  else{
    return measure_mult(in0val,in1val);
  }

}
profile_t Fabric::Chip::Tile::Slice::Multiplier::measure_vga(float in0val,float gain) {
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;
  Dac * val1_dac = parentSlice->dac;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
  // backup state of each component that will be clobbered
  mult_code_t codes_mult = m_codes;
  dac_code_t codes_val1 = val1_dac->m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;

  setGain(gain);
  float target_vga = compute_out_vga(m_codes, in0val);
  float target_in0 = compute_in0(m_codes, in0val);
  // backup connections
  cutil::buffer_mult_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_dac_conns(calib,val1_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile
                              ->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);


  dac_code_t dac_code_ref;
  dac_code_t dac_code_in0;
  dac_code_t dac_code_0;
  float ref;

  if(fabs(target_vga) > 10.0){
    sprintf(FMTBUF, "can't fit %f", target_vga);
    error(FMTBUF);
  }
  dac_code_ref = cutil::make_ref_dac(calib, ref_dac,
                                     -target_vga,
                                     ref);
  ref_dac->update(dac_code_ref);

  dac_code_in0 = cutil::make_val_dac(calib, val1_dac,
                                     target_in0);

  val1_dac->update(dac_code_in0);

  Connection dac_to_in0 = Connection(val1_dac->out0, in0);
  Connection mult_to_tileout = Connection ( out0, parentSlice->tileOuts[3].in0 );
  Connection tileout_to_chipout = Connection ( parentSlice->tileOuts[3].out0,
                                               parentSlice->parentTile
                                               ->parentChip->tiles[3].slices[2].chipOutput->in0 );
  Connection ref_to_tileout = Connection ( ref_dac->out0, parentSlice->tileOuts[3].in0 );



  dac_to_in0.setConn();
  mult_to_tileout.setConn();
  tileout_to_chipout.setConn();
  ref_to_tileout.setConn();

  float mean=0.0,variance=0.0;
  util::meas_dist_chip_out(this,mean,variance);
  profile_t prof = prof::make_profile(out0Id,0,
                                      target_vga,
                                      in0val,
                                      gain,
                                      mean-(target_vga+ref),
                                      variance);

  dac_to_in0.brkConn();
  mult_to_tileout.brkConn();
  tileout_to_chipout.brkConn();
  ref_to_tileout.brkConn();
  cutil::restore_conns(calib);
  ref_dac->update(codes_ref);
  val1_dac->update(codes_val1);
  this->update(codes_mult);
  return prof;

}


profile_t Fabric::Chip::Tile::Slice::Multiplier::measure_mult(float in0val, float in1val) {
  float target_mult = compute_out_mult(m_codes,in0val,in1val);
  float target_in0 = compute_in0(m_codes,in0val);
  float target_in1 = compute_in1(m_codes,in1val);

  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  int next2_slice = (slice_to_int(parentSlice->sliceId) + 2) % 4;
  Dac * val2_dac = parentSlice->parentTile->slices[next_slice].dac;
  Dac * val1_dac = parentSlice->dac;
  Dac * ref_dac = parentSlice->parentTile->slices[next2_slice].dac;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
  // backup state of each component that will be clobbered
  mult_code_t codes_self = m_codes;
  dac_code_t codes_val1 = val1_dac->m_codes;
  dac_code_t codes_val2 = val2_dac->m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;

  // backup connections
  cutil::buffer_mult_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_dac_conns(calib,val1_dac);
  cutil::buffer_dac_conns(calib,val2_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);


  Connection dac_to_in0 = Connection(val1_dac->out0, in0);
  Connection dac_to_in1 = Connection(val2_dac->out0, in1);
  Connection mult_to_tileout = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection tileout_to_chipout = Connection ( parentSlice->tileOuts[3].out0,
                                               parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection ref_to_tileout = \
    Fabric::Chip::Connection ( ref_dac->out0, parentSlice->tileOuts[3].in0 );


  dac_to_in0.setConn();
  dac_to_in1.setConn();
  mult_to_tileout.setConn();
  tileout_to_chipout.setConn();

  dac_code_t dac_code_ref;
  dac_code_t dac_code_in0;
  dac_code_t dac_code_in1;
  dac_code_t dac_code_0;
  float ref;

  dac_code_0 = cutil::make_zero_dac(calib, ref_dac);
  if(fabs(target_mult) > 10.0){
    sprintf(FMTBUF, "can't fit %f", target_mult);
    error(FMTBUF);
  }
  dac_code_ref = cutil::make_ref_dac(calib, ref_dac,
                                     -target_mult,
                                     ref);
  ref_dac->update(dac_code_ref);
  ref_to_tileout.setConn();
  dac_code_in0 = cutil::make_val_dac(calib, val1_dac,
                                     target_in0);
  dac_code_in1 = cutil::make_val_dac(calib, val2_dac,
                                     target_in1);

  val1_dac->update(dac_code_in0);
  val2_dac->update(dac_code_in1);
  float mean,variance;
  util::meas_dist_chip_out(this,mean,variance);
  profile_t prof = prof::make_profile(out0Id,0,
                                      target_mult,
                                      in0val,
                                      in1val,
                                      mean-(target_mult+ref),
                                      variance);

  dac_to_in0.brkConn();
  dac_to_in1.brkConn();
  mult_to_tileout.brkConn();
  tileout_to_chipout.brkConn();
  ref_to_tileout.brkConn();
  cutil::restore_conns(calib);
  ref_dac->update(codes_ref);
  val1_dac->update(codes_val1);
  val2_dac->update(codes_val2);
  this->update(codes_self);
  return prof;
}
