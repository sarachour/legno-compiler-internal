#include "AnalogLib.h"
#include "assert.h"
#include "fu.h"
#include "calib_util.h"
#include "profile.h"

bool helper_check_steady(Fabric * fab,
                         Fabric::Chip::Tile::Slice::ChipAdc* adc,
                         Fabric::Chip::Tile::Slice::Dac* dac
                         ){
  dac->update(dac->m_codes);
	fab->cfgCommit();
  bool success=true;
  // get the adc code at that value
	unsigned char adcPrev = adc->getData();
	for (unsigned char rep=0; success&&(rep<16); rep++){
    // determine if adc code is the same value as the previous value.
		success &= adcPrev==adc->getData();
  }
	return success;
}

bool Fabric::Chip::Tile::Slice::ChipAdc::testValidity(Fabric::Chip::Tile::Slice::Dac * val_dac){
  Fabric* fab = parentSlice->parentTile->parentChip->parentFabric;
  const float VALID_TEST_POINTS[3] = {0,1,-1};
  for(int i = 0; i < 3; i += 1){
    val_dac->setConstant(VALID_TEST_POINTS[i]);
    if(!helper_check_steady(fab,this,val_dac)){
      return false;
    }
  }
  return true;
}


#define CALIB_NPTS 3
const float TEST_POINTS[CALIB_NPTS] = {0,0.5,-0.5};

float Fabric::Chip::Tile::Slice::ChipAdc::calibrateFast(Fabric::Chip::Tile::Slice::Dac * val_dac){

  float in_val,target,meas,dummy;
  val_dac->setConstant(0.0);
  in_val = val_dac->fastMeasureValue(dummy);
  target =Fabric::Chip::Tile::Slice::ChipAdc::computeOutput(this->m_codes,
                                                            in_val);
  meas = util::meas_adc(this);
  return fabs(target-meas);
}

float Fabric::Chip::Tile::Slice::ChipAdc::calibrateMinError(Fabric::Chip::Tile::Slice::Dac * val_dac){

  float dummy;
  float score_total=0.0;
  for(int i=0; i < CALIB_NPTS; i += 1){
    val_dac->setConstant(TEST_POINTS[i]);
    float in_val = val_dac->fastMeasureValue(dummy);
    float target =Fabric::Chip::Tile::Slice::ChipAdc::computeOutput(this->m_codes,
                                                                   in_val);

    float meas = util::meas_adc(this);
    score_total += fabs(target-meas);
  }
  return score_total/CALIB_NPTS;
}
float Fabric::Chip::Tile::Slice::ChipAdc::calibrateMaxDeltaFit(Fabric::Chip::Tile::Slice::Dac * val_dac){
  return 0.0;
}

void Fabric::Chip::Tile::Slice::ChipAdc::calibrate (calib_objective_t obj) {

  Fabric::Chip::Tile::Slice::Dac * val_dac = parentSlice->dac;
  //backup
  adc_code_t codes_adc = m_codes;
  dac_code_t codes_dac = val_dac->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_dac_conns(calib,val_dac);
  cutil::buffer_adc_conns(calib,this);
  cutil::break_conns(calib);

  val_dac->setEnable(true);
	Connection conn0 = Connection ( val_dac->out0, in0 );
	conn0.setConn();

  print_info("calibrating adc...");
  cutil::calib_table_t calib_table = cutil::make_calib_table();
  unsigned char opts[] = {nA100,nA200,nA300,nA400};
  int signs[] = {-1,1};
  bool perfect_score = false;
  for(unsigned char fs=0; fs < 4 && !perfect_score; fs += 1){
    m_codes.lower_fs = opts[fs];
    m_codes.upper_fs = opts[fs];
    for(unsigned char spread=0; spread < 32 && !perfect_score; spread++){
      for(unsigned char lsign=0; lsign < 2 && !perfect_score; lsign +=1){
        for(unsigned char usign=0; usign < 2 && !perfect_score; usign +=1){
          m_codes.lower = 31+spread*signs[lsign];
          m_codes.upper = 31+spread*signs[usign];
          m_codes.nmos = 0;
          update(m_codes);
          for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
            m_codes.nmos = nmos;
            update(m_codes);
            if(!testValidity(val_dac)){
              continue;
            }
            for(int i2v_cal=0; i2v_cal < MAX_GAIN_CAL; i2v_cal += 16){
              m_codes.i2v_cal = i2v_cal;
              update(m_codes);
              float score;
              switch(obj){
              case CALIB_MINIMIZE_ERROR:
                score = calibrateMinError(val_dac);
                break;
              case CALIB_MAXIMIZE_DELTA_FIT:
                score = calibrateMaxDeltaFit(val_dac);
                break;
              case CALIB_FAST:
                score = calibrateFast(val_dac);
                break;
              default:
                error("unimplemented adc");
                break;
              }
              // TODO
              sprintf(FMTBUF,"fs=(%d,%d) def=(%d,%d) nmos=%d i2v=%d score=%f",
                      m_codes.lower_fs,
                      m_codes.upper_fs,
                      m_codes.lower,
                      m_codes.upper,
                      nmos,
                      i2v_cal,
                      score);
              print_info(FMTBUF);
              cutil::update_calib_table(calib_table,score,6,
                                        m_codes.lower_fs,
                                        m_codes.upper_fs,
                                        m_codes.lower,
                                        m_codes.upper,
                                        nmos,i2v_cal);
              if(cutil::perfect_score(calib_table)){
                perfect_score = true;
                break;
              }
            }
          }
        }
      }
    }
  }
  // find the actual best i2v_cal code.
  this->m_codes.lower_fs = calib_table.state[0];
  this->m_codes.upper_fs = calib_table.state[1];
  this->m_codes.lower = calib_table.state[2];
  this->m_codes.upper = calib_table.state[3];
  this->m_codes.nmos = calib_table.state[4];
  for(int i2v_cal=0; i2v_cal < MAX_GAIN_CAL; i2v_cal += 1){
    this->m_codes.i2v_cal = i2v_cal;
    update(m_codes);
    float score;
    switch(obj){
    case CALIB_MINIMIZE_ERROR:
      score = calibrateMinError(val_dac);
      break;
    case CALIB_MAXIMIZE_DELTA_FIT:
      score = calibrateMaxDeltaFit(val_dac);
      break;
    case CALIB_FAST:
      score = calibrateFast(val_dac);
      break;
    default:
      error("unimplemented adc");
      break;
    }
    cutil::update_calib_table(calib_table,score,6,
                              m_codes.lower_fs,
                              m_codes.upper_fs,
                              m_codes.lower,
                              m_codes.upper,
                              m_codes.nmos,i2v_cal);
  }

  conn0.brkConn();
  val_dac->update(codes_dac);
  this->update(codes_adc);

  this->m_codes.lower_fs = calib_table.state[0];
  this->m_codes.upper_fs = calib_table.state[1];
  this->m_codes.lower = calib_table.state[2];
  this->m_codes.upper = calib_table.state[3];
  this->m_codes.nmos = calib_table.state[4];
  this->m_codes.i2v_cal = calib_table.state[5];

  sprintf(FMTBUF,"BEST fs=(%d,%d) def=(%d,%d) nmos=%d i2v=%d score=%f",
          m_codes.lower_fs,
          m_codes.upper_fs,
          m_codes.lower,
          m_codes.upper,
          m_codes.nmos,
          m_codes.i2v_cal,
          calib_table.score);
  print_info(FMTBUF);
}

/*
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
  dac_code_0 = cutil::make_val_dac(calib, val_dac,
                                   0.0);

  dac_code_1 = cutil::make_val_dac(calib, val_dac,
                                   1.0*coeff);

  dac_code_neg1 = cutil::make_val_dac(calib, val_dac,
                                      -1.0*coeff);


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

*/
