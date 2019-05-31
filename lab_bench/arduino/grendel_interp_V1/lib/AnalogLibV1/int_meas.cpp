#include "AnalogLib.h"
#include <float.h>
#include "calib_util.h"
#include "fu.h"


void Fabric::Chip::Tile::Slice::Integrator::characterize(profile_t& result){
  integ_code_t backup = m_codes;
  prof::init_profile(result);
  float vals[SIZE1D];
  int n = prof::data_1d(vals,SIZE1D);
  for(int i=0; i < n; i += 1){
    setInitial(vals[i]);
    measure(result);
  }
  update(backup);
}


void Fabric::Chip::Tile::Slice::Integrator::characterizeTarget(profile_t& result){
  prof::init_profile(result);
  measure(result);
}


void helper_get_cal_in0(Fabric::Chip::Tile::Slice::Integrator * integ,
                        profile_t& result){
  integ->m_codes.cal_enable[out0Id] = false;
  integ->m_codes.cal_enable[in0Id] = true;
  integ->update(integ->m_codes);
  float mean,variance;
  util::meas_dist_chip_out(integ,mean,variance);
  integ->m_codes.cal_enable[in0Id] = false;
  prof::add_prop(result,in0Id, 0.0, mean,variance);
}

void helper_get_cal_out0(Fabric::Chip::Tile::Slice::Integrator * integ,
                         profile_t& result){
  integ->m_codes.cal_enable[in0Id] = false;
  integ->m_codes.cal_enable[out0Id] = true;
  integ->update(integ->m_codes);
  float mean,variance;
  util::meas_dist_chip_out(integ,mean,variance);
  integ->m_codes.cal_enable[out0Id] = false;
  prof::add_prop(result,out0Id, 0.0, mean,variance);
}

bool helper_get_cal_gain(Fabric::Chip::Tile::Slice::Integrator * integ,
                         profile_t& result,
                         Fabric::Chip::Tile::Slice::Dac * ref_dac,
                         float target,
                         dac_code_t& ref_codes){
  int ic_sign = integ->m_codes.inv[out0Id] ? -1.0 : 1.0;
  float ic_range = util::range_to_coeff(integ->m_codes.range[out0Id]);
  bool hiRange = (integ->m_codes.range[out0Id] == RANGE_HIGH);
  ref_dac->update(ref_codes);
  integ->update(integ->m_codes);
  float mean,variance;
  util::meas_dist_chip_out(integ,mean,variance);
  prof::add_prop(result,
                 out0Id,
                 integ->m_codes.ic_val*ic_range*ic_sign,
                 mean-target,
                 variance);
}


void Fabric::Chip::Tile::Slice::Integrator::measure(profile_t& result)
{
  bool hiRange = (m_codes.range[out0Id] == RANGE_HIGH);

  Dac * ref_dac = parentSlice->dac;
  integ_code_t codes_self = m_codes;
  dac_code_t ref_codes = ref_dac->m_codes;
  int ic_sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  float coeff = util::range_to_coeff(m_codes.range[out0Id]);
  float ic_val = m_codes.ic_val*ic_sign*coeff;



  cutil::calibrate_t calib;
  cutil::initialize(calib);

  cutil::buffer_integ_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

	// output side
  //conn1
  Connection ref_to_tile = Connection ( ref_dac->out0,
                                        parentSlice->tileOuts[3].in0 );
  //conn2
	Connection integ_to_tile= Connection ( out0, parentSlice->tileOuts[3].in0 );

	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );

  dac_code_t dac_0;
  dac_code_t dac_ic;

  print_info("making zero dac");
  prof::init_profile(prof::TEMP);
  dac_0 = make_zero_dac(calib, ref_dac,prof::TEMP);
  if (hiRange) {
    print_info("high range! making reference dac");
    prof::init_profile(prof::TEMP);
    dac_ic = make_val_dac(calib,ref_dac,
                          -ic_sign,
                          prof::TEMP);
    ref_to_tile.setConn();
  }
  integ_to_tile.setConn();
	tile_to_chip.setConn();
  ref_dac->update(dac_0);

  print_info("=== measure integrator ===");
  helper_get_cal_out0(this,result);
  helper_get_cal_in0(this,result);
  helper_get_cal_gain(this,result,
                      ref_dac,
                      hiRange ? 0.0: ic_val,
                      hiRange ? dac_ic : dac_0);

	if (hiRange) {
    ref_to_tile.brkConn();
    ref_dac->update(ref_codes);
	} else {
	}
  integ_to_tile.brkConn();
	tile_to_chip.brkConn();
  cutil::restore_conns(calib);

  codes_self.nmos = m_codes.nmos;
  codes_self.ic_code = m_codes.ic_code;
  codes_self.gain_cal = m_codes.gain_cal;
  codes_self.port_cal[out0Id] = m_codes.port_cal[out0Id];
  codes_self.port_cal[in0Id] = m_codes.port_cal[in0Id];
  update(codes_self);

}
