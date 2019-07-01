#include "AnalogLib.h"
#include <float.h>
#include "calib_util.h"
#include "fu.h"


void Fabric::Chip::Tile::Slice::Integrator::characterize(profile_t& result){
  integ_code_t backup = m_codes;
  prof::init_profile(result);
  float vals[SIZE1D];
  int n = prof::data_1d(vals,SIZE1D);
  measure(result,0.2,false);
  measure(result,0.0,false);
  for(int i=0; i < n; i += 1){
    setInitial(vals[i]);
    measure(result,0.0,true);
  }
  update(backup);
}


void Fabric::Chip::Tile::Slice::Integrator::characterizeTarget(profile_t& result){
  float vals[SIZE1D];
  int n = prof::data_1d(vals,SIZE1D);
  prof::init_profile(result);
  measure(result,0.0,true);
  for(int i=0; i < n; i += 2){
    measure(result,vals[i],false);
  }
}


void helper_get_cal_in0(Fabric::Chip::Tile::Slice::Integrator * integ,
                        profile_t& result)
{

  integ->m_codes.cal_enable[out0Id] = false;
  integ->m_codes.cal_enable[in0Id] = true;
  integ->update(integ->m_codes);

  float mean,variance;
  util::meas_dist_chip_out(integ,mean,variance);
  prof::add_prop(result,
                 in0Id,
                 0.0,
                 0.0,
                 0.0,
                 mean,
                 variance);
  //print_info("INPUT TREND");
  //util::meas_trend_chip_out(integ);
  integ->m_codes.cal_enable[in0Id] = false;
}


void helper_get_cal_out0(Fabric::Chip::Tile::Slice::Integrator * integ,
                         profile_t& result)
{
  integ->m_codes.cal_enable[in0Id] = false;
  integ->m_codes.cal_enable[out0Id] = true;
  integ->update(integ->m_codes);

  float mean,variance;
  util::meas_dist_chip_out(integ,mean,variance);
  prof::add_prop(result,
                 out0Id,
                 0.0,
                 0.0,
                 0.0,
                 mean,
                 variance);

  //print_info("OUTPUT TREND");
  //util::meas_trend_chip_out(integ);


  integ->m_codes.cal_enable[out0Id] = false;
}
void helper_get_cal_trend(Fabric::Chip::Tile::Slice::Integrator * integ,
                          Fabric::Chip::Tile::Slice::Dac * val_dac,
                          dac_code_t& val_dac_codes,
                          float val,
                          profile_t& result)
{
  integ->update(integ->m_codes);
  val_dac->update(val_dac_codes);
  sprintf(FMTBUF, "BIAS TREND %f", val);
  print_info(FMTBUF);
  util::meas_trend_chip_out(integ);
}
bool helper_get_cal_gain(Fabric::Chip::Tile::Slice::Integrator * integ,
                         Fabric::Chip::Tile::Slice::Dac * ref_dac,
                         dac_code_t& ref_dac_codes,
                         float ref,
                         profile_t& result
                         )
{
  print_info("---- test initial cond ---");
  float target = compute_init_cond(integ->m_codes);
  ref_dac->update(ref_dac_codes);
  integ->update(integ->m_codes);
  float mean,variance;
  util::meas_dist_chip_out(integ,mean,variance);
  sprintf(FMTBUF,"mean=%f variance=%f target=%f ref=%f",
          mean,variance,target,ref);
  print_info(FMTBUF);
  prof::add_prop(result,
                 in1Id,
                 target,
                 0.0,
                 integ->m_codes.ic_val,
                 mean-(target+ref),
                 variance);
}



void Fabric::Chip::Tile::Slice::Integrator::measure(profile_t& result, float input, \
                                                    bool test_init_cond)
{
  Dac * aux_dac = parentSlice->dac;
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  //back up codes
  integ_code_t codes_self = m_codes;
  dac_code_t aux_codes = aux_dac->m_codes;

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

  dac_code_t dac_ref;
  float ref_target,ref;
  dac_code_t dac_val;
  float val;
  if(test_init_cond){
    ref_target = compute_init_cond(m_codes);
    dac_ref = cutil::make_ref_dac(calib,aux_dac,-ref_target,ref);
    aux_dac->update(dac_ref);
    aux_to_tile.setConn();
  }
  else{
    prof::init_profile(prof::TEMP);
    dac_val = cutil::make_val_dac(calib,aux_dac,input,
                                  prof::TEMP);
    aux_dac->update(dac_val);
    aux_to_input.setConn();
  }
  integ_to_tile.setConn();
	tile_to_chip.setConn();

  if(!test_init_cond){
    helper_get_cal_out0(this,
                        result);
    helper_get_cal_in0(this,
                       result);
    /*
    helper_get_cal_trend(this,
                         aux_dac,
                         dac_val,
                         input,
                         result);
    */
  }
  else{
    helper_get_cal_gain(this,
                        aux_dac,
                        dac_ref,
                        ref,
                        result);
  }

  if(test_init_cond){
    aux_to_tile.brkConn();
  }
  else{
    aux_to_input.brkConn();
  }
  integ_to_tile.brkConn();
	tile_to_chip.brkConn();
  aux_dac->update(aux_codes);
  cutil::restore_conns(calib);
  update(codes_self);

}
