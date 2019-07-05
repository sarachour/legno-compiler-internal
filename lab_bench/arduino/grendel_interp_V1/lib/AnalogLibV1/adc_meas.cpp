#include "AnalogLib.h"
#include "assert.h"
#include "fu.h"
#include "calib_util.h"


profile_t Fabric::Chip::Tile::Slice::ChipAdc::measure(float input){
  float coeff = util::range_to_coeff(m_codes.range);
  update(m_codes);

  Fabric::Chip::Tile::Slice::Dac * val_dac = parentSlice->dac;
  Fabric* fab = parentSlice->parentTile->parentChip->parentFabric;
  adc_code_t codes_self= m_codes;
  dac_code_t codes_dac = val_dac->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_dac_conns(calib,val_dac);
  cutil::buffer_adc_conns(calib,this);
  cutil::break_conns(calib);

  val_dac->setEnable(true);
  dac_code_t dac_code_value;
  dac_code_value = cutil::make_val_dac(calib,val_dac,
                                       coeff*input);
  val_dac->update(dac_code_value);

  Connection conn0 = Connection ( val_dac->out0, in0 );
	conn0.setConn();
	setEnable (true);

  float target = (input+1.0)*0.5*255;

  float mean,variance;
  util::meas_dist_adc(this,mean,variance);
  profile_t prof = prof::make_profile(out0Id,
                                      0,
                                      target,
                                      input,
                                      0.0,
                                      mean-target,
                                      variance);

  sprintf(FMTBUF, "MEAS target=%f input=%f / mean=%f var=%f",
          target, input, mean, variance);
  print_log(FMTBUF);
	conn0.brkConn();
	val_dac->setEnable(false);

  cutil::restore_conns(calib);
  val_dac->update(codes_dac);
  return prof;
}
