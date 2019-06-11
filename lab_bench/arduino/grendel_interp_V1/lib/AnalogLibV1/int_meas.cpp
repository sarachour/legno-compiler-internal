#include "AnalogLib.h"
#include <float.h>
#include "calib_util.h"
#include "fu.h"


void Fabric::Chip::Tile::Slice::Integrator::characterize(profile_t& result){
  integ_code_t backup = m_codes;
  prof::init_profile(result);
  float vals[SIZE1D];
  int n = prof::data_1d(vals,SIZE1D);
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

float compute_init_cond(integ_code_t& m_codes){
  float sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  float rng = util::range_to_coeff(m_codes.range[out0Id]);
  float ic = m_codes.ic_val;
  return rng*sign*ic;
}

float compute_output(integ_code_t& m_codes,float val){
  float sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  float rng = util::range_to_coeff(m_codes.range[out0Id])
    /util::range_to_coeff(m_codes.range[in0Id]);
  return rng*sign*val;
}

void helper_get_cal_in0(Fabric::Chip::Tile::Slice::Integrator * integ,
                        Fabric::Chip::Tile::Slice::Dac * ref_dac,
                        dac_code_t& ref_dac_codes,
                        float input,
                        float ref,
                        profile_t& result)
{

  integ->m_codes.cal_enable[out0Id] = false;
  integ->m_codes.cal_enable[in0Id] = true;
  integ->update(integ->m_codes);
  ref_dac->update(ref_dac_codes);

  float mean,variance;
  util::meas_dist_chip_out(integ,mean,variance);
  prof::add_prop(result,in0Id,
                 input,
                 input,
                 0.0,
                 mean-(ref + input),
                 variance);
  integ->m_codes.cal_enable[in0Id] = false;
}

void helper_get_cal_out0(Fabric::Chip::Tile::Slice::Integrator * integ,
                         Fabric::Chip::Tile::Slice::Dac * ref_dac,
                         dac_code_t& ref_dac_codes,
                         float input,
                         float ref,
                         profile_t& result)
{
  float target = compute_output(integ->m_codes,
                                input);
  integ->m_codes.cal_enable[in0Id] = false;
  integ->m_codes.cal_enable[out0Id] = true;
  integ->update(integ->m_codes);
  ref_dac->update(ref_dac_codes);

  float mean,variance;
  util::meas_dist_chip_out(integ,mean,variance);
  prof::add_prop(result,
                 out0Id,
                 target,
                 input,
                 0.0,
                 (mean-(ref+target)),
                 variance);



  integ->m_codes.cal_enable[out0Id] = false;
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
                 out0Id,
                 target,
                 0.0,
                 integ->m_codes.ic_val,
                 mean-(target+ref),
                 variance);
}



void Fabric::Chip::Tile::Slice::Integrator::measure(profile_t& result, float input, bool test_init_cond)
{
  Dac * ref_dac = parentSlice->dac;
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  //back up codes
  integ_code_t codes_self = m_codes;
  dac_code_t ref_codes = ref_dac->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);

  cutil::buffer_integ_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile
                              ->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

	// output side
  //conn1
  Connection ref_to_tile = Connection ( ref_dac->out0,
                                        parentSlice->tileOuts[3].in0 );
  //conn2
	Connection integ_to_tile= Connection ( out0, parentSlice->tileOuts[3].in0 );

	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile
                                         ->parentChip->tiles[3].slices[2].chipOutput->in0 );

  dac_code_t dac_ref1;
  dac_code_t dac_ref2;
  float target1,ref1;
  float target2,ref2;
  if(test_init_cond){
    target1 = compute_init_cond(m_codes);
    dac_ref1 = cutil::make_ref_dac(calib,ref_dac,-target1,ref1);
  }
  else{
    dac_ref1 = cutil::make_ref_dac(calib,ref_dac,-input,ref1);
    target2 = compute_output(m_codes, input);
    dac_ref2 = cutil::make_ref_dac(calib,ref_dac,-target2,ref2);
  }
  ref_dac->update(dac_ref1);
  ref_to_tile.setConn();
  integ_to_tile.setConn();
	tile_to_chip.setConn();

  if(!test_init_cond){
    helper_get_cal_out0(this,
                        ref_dac,dac_ref1,
                        input,
                        ref1,
                        result);
    helper_get_cal_in0(this,
                       ref_dac,dac_ref2,
                       input,
                       ref2,
                       result);
  }
  else{
    helper_get_cal_gain(this,
                        ref_dac,dac_ref1,
                        ref1,
                        result);
  }

  ref_to_tile.brkConn();
  integ_to_tile.brkConn();
	tile_to_chip.brkConn();
  ref_dac->update(ref_codes);
  cutil::restore_conns(calib);
  update(codes_self);

}
