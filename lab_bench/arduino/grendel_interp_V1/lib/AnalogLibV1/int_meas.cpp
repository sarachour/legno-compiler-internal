#include "AnalogLib.h"
#include <float.h>
#include "calib_util.h"
#include "fu.h"


profile_t Fabric::Chip::Tile::Slice::Integrator::measure(char mode, float input){
  if(mode == 0){
    return measure_ic(input);
  }
  else{
    return measure_ss(input);
  }
}


profile_t Fabric::Chip::Tile::Slice::Integrator::measure_ss(float input){
  Fanout * fanout = &this->parentSlice->fans[0];
  Dac* val_dac = this->parentSlice->dac;
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;

  fanout_code_t fan_codes = fanout->m_codes;
  dac_code_t val_dac_codes = val_dac->m_codes;
  dac_code_t ref_dac_codes = ref_dac->m_codes;
  integ_code_t integ_codes = this->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_fanout_conns(calib,fanout);
  cutil::buffer_integ_conns(calib,this);
  cutil::buffer_dac_conns(calib,val_dac);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_tileout_conns(calib,&this->parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,
                              this->parentSlice->parentTile->parentChip
                              ->tiles[3].slices[2].chipOutput);

  cutil::break_conns(calib);

  range_t out_range = integ_codes.range[out0Id];
  fanout->m_codes.range[in0Id] = out_range;
  fanout->m_codes.range[out0Id] = out_range;
  fanout->m_codes.range[out1Id] = out_range;
  fanout->m_codes.range[out2Id] = out_range;
  fanout->m_codes.inv[out0Id] = false;
  fanout->m_codes.inv[out1Id] = true;
  fanout->update(fanout->m_codes);

  float target_input = compute_steady_state_input(m_codes,input);
  float ref;
  dac_code_t dac_code_value;
  dac_code_t dac_code_ref;
  dac_code_value = cutil::make_val_dac(calib,val_dac,target_input);
  val_dac->update(dac_code_value);


  float target_output = compute_steady_state_output(m_codes,input);
  dac_code_ref = cutil::make_ref_dac(calib,
                                     ref_dac,
                                     -target_output,
                                     ref);
  ref_dac->update(dac_code_ref);
  setInitial(0.0);
  update(m_codes);


  Connection integ_to_fan = Fabric::Chip::Connection ( out0, fanout->in0 );
  Connection fan_to_tile = Fabric::Chip::Connection ( fanout->out0,
                                                      parentSlice->tileOuts[3].out0);
  Connection refdac_to_tile = Fabric::Chip::Connection ( ref_dac->out0,
                                                                    parentSlice->tileOuts[3].out0);
  Connection fan_to_integ = Fabric::Chip::Connection(fanout->out1, in0);
  Connection valdac_to_integ = Fabric::Chip::Connection(val_dac->out0, in0);
  Connection tile_to_chip = Fabric::Chip::Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile        \
                                         ->parentChip->tiles[3].slices[2].chipOutput->in0 );

  integ_to_fan.setConn();
  fan_to_tile.setConn();
  refdac_to_tile.setConn();
  fan_to_integ.setConn();
  valdac_to_integ.setConn();
  tile_to_chip.setConn();
  float mean, variance;
  util::meas_steady_chip_out(this,mean,variance);
  profile_t prof = prof::make_profile(out0Id,
                                      calib.success ? 1 : 255,
                                      target_output,
                                      target_input,
                                      0.0,
                                      mean-(target_output+ref),
                                      variance);

  integ_to_fan.brkConn();
  fan_to_tile.brkConn();
  refdac_to_tile.brkConn();
  fan_to_integ.brkConn();
  valdac_to_integ.brkConn();
  tile_to_chip.brkConn();
  cutil::restore_conns(calib);
  fanout->update(fan_codes);
  val_dac->update(val_dac_codes);
  ref_dac->update(ref_dac_codes);
  this->update(integ_codes);
  return prof;
}

profile_t Fabric::Chip::Tile::Slice::Integrator::measure_ic(float input)
{
  Dac * aux_dac = parentSlice->dac;
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  //back up codes
  integ_code_t codes_integ = m_codes;
  dac_code_t aux_codes = aux_dac->m_codes;

  setInitial(input);

  cutil::calibrate_t calib;
  cutil::initialize(calib);

  cutil::buffer_integ_conns(calib,this);
  cutil::buffer_dac_conns(calib,aux_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile
                              ->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

	// output side
  //conn1
  Connection aux_to_tile = Connection ( aux_dac->out0,
                                        parentSlice->tileOuts[3].in0 );
  Connection aux_to_input = Connection ( aux_dac->out0,
                                        in0 );

  //conn2
	Connection integ_to_tile= Connection ( out0, parentSlice->tileOuts[3].in0 );

	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile
                                         ->parentChip->tiles[3].slices[2].chipOutput->in0 );

  float target,ref;
  dac_code_t dac_ref_codes;
  target = compute_init_cond(m_codes);
  dac_ref_codes = cutil::make_ref_dac(calib,aux_dac,-target,ref);
  aux_dac->update(dac_ref_codes);
  aux_to_tile.setConn();
  integ_to_tile.setConn();
	tile_to_chip.setConn();
  update(m_codes);
  float mean,variance;
  util::meas_dist_chip_out(this,mean,variance);
  profile_t prof = prof::make_profile(out0Id,
                                      calib.success ? 0 : 255,
                                      target,
                                      m_codes.ic_val,
                                      0.0,
                                      mean-(target+ref),
                                      variance);
  aux_to_tile.brkConn();
  integ_to_tile.brkConn();
	tile_to_chip.brkConn();
  aux_dac->update(aux_codes);
  cutil::restore_conns(calib);
  update(codes_integ);
  return prof;
}
