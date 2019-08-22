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

void make_feedback_fanout(Fabric::Chip::Tile::Slice::Fanout * fanout,
                          range_t out_range, bool is_positive){
  fanout->m_codes.range[in0Id] = out_range;
  fanout->m_codes.range[out0Id] = out_range;
  fanout->m_codes.range[out1Id] = out_range;
  fanout->m_codes.range[out2Id] = out_range;
  if(is_positive){
    fanout->m_codes.inv[out0Id] = false;
    fanout->m_codes.inv[out1Id] = true;
  }
  else{
    fanout->m_codes.inv[out0Id] = true;
    fanout->m_codes.inv[out1Id] = false;
  }
  fanout->m_codes.enable = true;
  fanout->update(fanout->m_codes);
  fanout->calibrate(CALIB_MINIMIZE_ERROR);
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

  error("redo everything");
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

  // calibrate the fanout for feedback control


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


  make_feedback_fanout(fanout, integ_codes.range[out0Id], !integ_codes.inv[out0Id]);

  // make an approximate input value
  /*
  float target_input = compute_steady_state_input(m_codes,input);
  target_input = val_dac->fastMakeValue(target_input);
  float target_output = predict_steady_state_output(m_codes,target_input);
  */
  float target_input, target_output;
  cutil::fast_make_dac(ref_dac,-target_output);

  setInitial(0.0);
  update(m_codes);

  refdac_to_tile.setConn();
  integ_to_fan.setConn();
  fan_to_tile.setConn();
  fan_to_integ.setConn();
  valdac_to_integ.setConn();
  tile_to_chip.setConn();
  float mean,variance,dummy;
  calib.success &= cutil::measure_signal_robust(this,
                                                ref_dac,
                                                target_output,
                                                true,
                                                mean,
                                                variance);

  float ref = ref_dac->fastMeasureValue(dummy);
  sprintf(FMTBUF,"PARS target=%f ref=%f mean=%f",
          target_output,ref,mean);
  print_info(FMTBUF);
  float bias = (mean-(target_output+ref));
  profile_t prof = prof::make_profile(out0Id,
                                      1,
                                      target_output,
                                      target_input,
                                      0.0,
                                      bias,
                                      variance);
  if(!calib.success){
    prof.mode = 255;
  }
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

  //back up codes
  integ_code_t codes_integ = m_codes;
  dac_code_t aux_dac_codes = aux_dac->m_codes;
  setInitial(input);

  cutil::calibrate_t calib;
  cutil::initialize(calib);

  cutil::buffer_integ_conns(calib,this);
  cutil::buffer_dac_conns(calib,aux_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile
                              ->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  bool high_output = (m_codes.range[out0Id] == RANGE_HIGH);
	// output side
  //conn1
  Connection aux_to_tile = Connection ( aux_dac->out0,
                                        parentSlice->tileOuts[3].in0 );


  //conn2
	Connection integ_to_tile= Connection ( out0,
                                         parentSlice->tileOuts[3].in0 );

	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile
                                         ->parentChip->tiles[3].slices[2].chipOutput->in0 );


  float target;
  mult_code_t scd_codes;
  target = this->computeInitCond(m_codes);
  cutil::fast_make_dac(aux_dac,-target);
  aux_to_tile.setConn();
  integ_to_tile.setConn();
	tile_to_chip.setConn();
  update(m_codes);
  float mean,variance,dummy;
  calib.success &= cutil::measure_signal_robust(this,
                                                aux_dac,
                                                target,
                                                false,
                                                mean,
                                                variance);

  float ref = aux_dac->fastMeasureValue(dummy);
  sprintf(FMTBUF,"PARS target=%f ref=%f mean=%f",
          target,ref,mean);
  print_info(FMTBUF);
  float bias = (mean-(target+ref));
  profile_t prof = prof::make_profile(out0Id,
                                      0,
                                      target,
                                      m_codes.ic_val,
                                      0.0,
                                      bias,
                                      variance);
  if(!calib.success){
    prof.mode = 255;
  }
  aux_dac->update(aux_dac_codes);
  aux_to_tile.brkConn();
  integ_to_tile.brkConn();
	tile_to_chip.brkConn();
  aux_dac->update(aux_dac_codes);
  cutil::restore_conns(calib);
  update(codes_integ);
  return prof;
}
