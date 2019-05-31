#include "AnalogLib.h"
#include "assert.h"
#include "fu.h"
#include "calib_util.h"
#include "profile.h"


bool helper_check_steady(Fabric * fab,
                         Fabric::Chip::Tile::Slice::ChipAdc* adc,
                         Fabric::Chip::Tile::Slice::Dac* dac,
                         dac_code_t& dac_code
                         ){
  dac_code_t codes_dac = dac->m_codes;
  dac->update(dac_code);
	fab->cfgCommit();
  bool success=true;
  // get the adc code at that value
	unsigned char adcPrev = adc->getData();
	for (unsigned char rep=0; success&&(rep<16); rep++){
    // determine if adc code is the same value as the previous value.
		success &= adcPrev==adc->getData();
  }
  dac->update(codes_dac);
	return success;
}


bool helper_find_bias_and_nmos(Fabric * fab,
                               Fabric::Chip::Tile::Slice::ChipAdc* adc,
                               Fabric::Chip::Tile::Slice::Dac* dac,
                               dac_code_t& dac_code_0,
                               dac_code_t& dac_code_1,
                               dac_code_t& dac_code_neg_1,
                               adc_code_t& best_code
                         ){
  dac_code_t codes_dac = dac->m_codes;
  adc->m_codes.nmos = 0;
  adc->setAnaIrefNmos();
  bool found_code = false;
  float max_error = 0.5;
  while(adc->m_codes.nmos <= 7 && !found_code){
    bool succ = true;
    float error;
    bool calib_failed;
    float target = 128.0;
    dac->update(dac_code_0);
    binsearch::find_bias(adc,
                         128.0,
                         adc->m_codes.i2v_cal,
                         error,
                         MEAS_ADC);
    binsearch::test_stab(adc->m_codes.i2v_cal, error,
                         max_error, calib_failed);
    succ &= !calib_failed;
    sprintf(FMTBUF,"nmos=%d i2v_cal=%d target=%f meas=%f succ=%s",
            adc->m_codes.nmos, adc->m_codes.i2v_cal, 128.0, 128.0+error,
            calib_failed ? "false" : "true");
    print_log(FMTBUF);

    if(succ){
      dac->update(dac_code_1);
      target = 255.0;
      error = binsearch::get_bias(adc, target, MEAS_ADC);

    }
    if(succ){
      dac->update(dac_code_neg_1);
      target = 0.0;
      error = binsearch::get_bias(adc, target, MEAS_ADC);
    }
    if(succ){
      found_code = true;
      best_code = adc->m_codes;
    }
    adc->m_codes.nmos += 1;
    if(adc->m_codes.nmos <= 7){
      adc->setAnaIrefNmos();
    }
  }
  return found_code;
}


bool Fabric::Chip::Tile::Slice::ChipAdc::calibrate (profile_t& result,
                                                    const float max_error) {

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


  dac_code_t dac_code_0;
  dac_code_t dac_code_1;
  dac_code_t dac_code_neg1;
  prof::init_profile(prof::TEMP);
  dac_code_0 = cutil::make_val_dac(calib, val_dac,
                                   0.0,
                                   prof::TEMP);

  prof::init_profile(prof::TEMP);
  dac_code_1 = cutil::make_val_dac(calib, val_dac,
                                   1.0*coeff,
                                   prof::TEMP);

  prof::init_profile(prof::TEMP);
  dac_code_neg1 = cutil::make_val_dac(calib, val_dac,
                                      -1.0*coeff,
                                      prof::TEMP);


	Connection conn0 = Connection ( val_dac->out0, in0 );
	conn0.setConn();
	setEnable (true);

  bool found_code=false;
  adc_code_t best_code = m_codes;
  adc_code_t tmp_code = m_codes;
  unsigned char opts[] = {nA100,nA200,nA300,nA400};
  int signs[] = {-1,1};
  print_info("calibrating adc..");
  for(unsigned char fs=0; fs < 4; fs += 1){
    m_codes.lower_fs = opts[fs];
    m_codes.upper_fs = opts[fs];
    for(unsigned char spread=0; spread < 32 && !found_code; spread++){
      for(unsigned char lsign=0; lsign < 2 && !found_code; lsign +=1){
        for(unsigned char usign=0; usign < 2 && !found_code; usign +=1){
          m_codes.lower = 31+spread*signs[lsign];
          m_codes.upper = 31+spread*signs[usign];
          update(m_codes);
          // is this successful
          bool succ = true;
          succ = helper_check_steady(fab,this,val_dac,dac_code_0);
          if(succ)
            succ &= helper_check_steady(fab,this,val_dac,dac_code_1);
          if(succ)
            succ &= helper_check_steady(fab,this,val_dac,dac_code_neg1);

          if(succ){
            sprintf(FMTBUF, "-> fs=%d lower=%d upper=%d",
                    m_codes.lower_fs,m_codes.lower,m_codes.upper);
            print_log(FMTBUF);
            succ &= helper_find_bias_and_nmos(fab,this,val_dac,
                                              dac_code_0,
                                              dac_code_1,
                                              dac_code_neg1,
                                              tmp_code);
          }
          if(succ){
            found_code = true;
            best_code = tmp_code;
          }
        }
      }
    }
  }

	conn0.brkConn();
	val_dac->setEnable(false);


  cutil::restore_conns(calib);
  val_dac->update(codes_dac);

  codes_self.i2v_cal = best_code.i2v_cal;
  codes_self.nmos = best_code.nmos;
  codes_self.lower = best_code.lower;
  codes_self.lower_fs = best_code.lower_fs;
  codes_self.upper = best_code.upper;
  codes_self.upper_fs = best_code.upper_fs;
  update(codes_self);

	// Serial.println("offset settings found");
	return found_code;
}

