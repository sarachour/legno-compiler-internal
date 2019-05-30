#include "AnalogLib.h"
#include "fu.h"
#include "calib_util.h"
#include <float.h>



void Fabric::Chip::Tile::Slice::Multiplier::characterize(util::calib_result_t& result){
  if(m_codes.vga){
    util::init_result(result);
    for(int i=0; i < 25; i += 1){
      float in0 = (i/25.0)*2.0-1.0;
      sprintf(FMTBUF, "COMPUTE %f*%f", in0, m_codes.gain_val);
      print_log(FMTBUF);
      measure_vga(result,in0);
    }
  }
  else{
    util::init_result(result);
    for(int i=0; i < 5; i += 1){
      float in0 = (i/5.0)*1.0;
      for(int j=0; j < 5; j += 1){
        float in1 = (j/5.0)*1.0;
        measure_mult(result,in0,in1);
      }
    }
  }
}



void Fabric::Chip::Tile::Slice::Multiplier::measure_vga(util::calib_result_t& result, float in0val) {
  int sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  float gain = m_codes.gain_val;
  bool hiRange = m_codes.range[out0Id] == RANGE_HIGH;
  bool loRange = m_codes.range[in0Id] == RANGE_LOW;
  float in0scf = util::range_to_coeff(m_codes.range[in0Id]);
  float outscf = util::range_to_coeff(m_codes.range[out0Id]);

  float coeff_vga = outscf/in0scf;

  float target_vga =  sign*gain*coeff_vga*in0scf*in0val;
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;
  Dac * val1_dac = parentSlice->dac;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
  // backup state of each component that will be clobbered
  mult_code_t codes_self = m_codes;
  dac_code_t codes_val1 = val1_dac->m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;

  // backup connections
  cutil::buffer_mult_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_dac_conns(calib,val1_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);


  Connection dac_to_in0 = Connection(val1_dac->out0, in0);
  Connection mult_to_tileout = Connection ( out0, parentSlice->tileOuts[3].in0 );
  Connection tileout_to_chipout = Connection ( parentSlice->tileOuts[3].out0,
                                               parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection ref_to_tileout = Fabric::Chip::Connection ( ref_dac->out0, parentSlice->tileOuts[3].in0 );



  dac_to_in0.setConn();
  mult_to_tileout.setConn();
  tileout_to_chipout.setConn();

  dac_code_t dac_code_ref;
  dac_code_t dac_code_in0;
  dac_code_t dac_code_0;

  util::calib_result_t interim_result;
  util::init_result(interim_result);
  dac_code_0 = cutil::make_zero_dac(calib, ref_dac,
                                    interim_result);
  if(hiRange){
    if(fabs(target_vga) > 10.0){
      sprintf(FMTBUF, "can't fit %f", target_vga);
      error(FMTBUF);
    }
    util::init_result(interim_result);
    dac_code_ref = cutil::make_val_dac(calib, ref_dac,
                                       -target_vga,
                                       interim_result);
    ref_dac->update(dac_code_ref);
    ref_to_tileout.setConn();
  }
  util::init_result(interim_result);
  dac_code_in0 = cutil::make_val_dac(calib, val1_dac,
                                     in0scf*in0val,
                                     interim_result);

  val1_dac->update(dac_code_in0);
  float mean=0.0,variance=0.0;
  util::meas_dist_chip_out(this,mean,variance);
  float target = hiRange ? 0.0 : target_vga;
  util::add_prop(result,out0Id,target_vga,
                 mean-target,
                 variance);

  dac_to_in0.brkConn();
  mult_to_tileout.brkConn();
  tileout_to_chipout.brkConn();
  if(hiRange){
    ref_to_tileout.brkConn(); ref_dac->update(codes_ref);
  }
  cutil::restore_conns(calib);
  val1_dac->update(codes_val1);
  this->update(codes_self);


}


void Fabric::Chip::Tile::Slice::Multiplier::measure_mult(util::calib_result_t& result, float in0val, float in1val) {
  int sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  bool hiRange = m_codes.range[out0Id] == RANGE_HIGH;
  bool loRange = m_codes.range[in0Id] == RANGE_LOW;
  float in0scf = util::range_to_coeff(m_codes.range[in0Id]);
  float in1scf = util::range_to_coeff(m_codes.range[in1Id]);
  float outscf = util::range_to_coeff(m_codes.range[out0Id]);

  float coeff_mult = outscf/(in0scf*in1scf);


  float target_mult =  sign*coeff_mult*in0scf*in1scf*in0val*in1val;
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

  util::calib_result_t interim_result;
  util::init_result(interim_result);
  dac_code_0 = cutil::make_zero_dac(calib, ref_dac,
                                    interim_result);
  if(hiRange){
    if(fabs(target_mult) > 10.0){
      sprintf(FMTBUF, "can't fit %f", target_mult);
      error(FMTBUF);
    }
    util::init_result(interim_result);
    dac_code_ref = cutil::make_val_dac(calib, ref_dac,
                                       -target_mult,
                                       interim_result);
    ref_dac->update(dac_code_ref);
    ref_to_tileout.setConn();
  }
  util::init_result(interim_result);
  dac_code_in0 = cutil::make_val_dac(calib, val1_dac,
                                     in0scf*in0val,
                                     interim_result);
  util::init_result(interim_result);
  dac_code_in1 = cutil::make_val_dac(calib, val2_dac,
                                     in1scf*in1val,
                                     interim_result);

  val1_dac->update(dac_code_in0);
  val2_dac->update(dac_code_in1);
  float mean,variance;
  util::meas_dist_chip_out(this,mean,variance);
  float target = hiRange ? 0 : target_mult;
  util::add_prop(result,out0Id,target_mult,
                 mean-target,variance);

  dac_to_in0.brkConn();
  dac_to_in1.brkConn();
  mult_to_tileout.brkConn();
  tileout_to_chipout.brkConn();
  if(hiRange){
    ref_to_tileout.brkConn(); ref_dac->update(codes_ref);
  }
  cutil::restore_conns(calib);
  val1_dac->update(codes_val1);
  val2_dac->update(codes_val2);
  this->update(codes_self);
}
