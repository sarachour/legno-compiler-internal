#include "AnalogLib.h"
#include "assert.h"
#include "fu.h"
#include "calib_util.h"


void Fabric::Chip::Tile::Slice::ChipAdc::characterize(util::calib_result_t& result){
  util::init_result(result);
  int n = 20;
  for(int i=0; i < n; i += 1){
    float in0 = (i/n)*1.0;
    sprintf(FMTBUF, "COMPUTE %f", in0);
    measure(result,in0);
  }
}


void Fabric::Chip::Tile::Slice::ChipAdc::measure(util::calib_result_t& result, float input){
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
  util::calib_result_t interim_result;
  dac_code_value = cutil::make_val_dac(calib,val_dac,
                                       coeff*input,
                                       interim_result);
  val_dac->update(dac_code_value);

  Connection conn0 = Connection ( val_dac->out0, in0 );
	conn0.setConn();
	setEnable (true);

  float spread = 255 - (m_codes.pad_left + m_codes.pad_right);
  float offset = m_codes.pad_left;
  float target = input*spread + offset;

  float mean,variance;
  util::meas_dist_adc(this,mean,variance);
  util::add_prop(result,out0Id,
                 target,
                 mean-target,
                 variance);


	conn0.brkConn();
	val_dac->setEnable(false);

  cutil::restore_conns(calib);
  val_dac->update(codes_dac);
}
