#include "AnalogLib.h"
#include "assert.h"
#include "fu.h"
#include "calib_util.h"
#include "profile.h"


bool Fabric::Chip::Tile::Slice::ChipAdc::testValidity(Fabric::Chip::Tile::Slice::Dac * val_dac){
  Fabric* fab = parentSlice->parentTile->parentChip->parentFabric;
  const float VALID_TEST_POINTS[3] = {0,1,-1};
  const float STD_THRESH = 2.0;
  const float ZERO_THRESH = 0.7;
  float mean,variance;
  for(int i = 0; i < 3; i += 1){
    val_dac->setConstant(VALID_TEST_POINTS[i]);
    util::meas_dist_adc(this,mean,variance);
    float std = sqrt(variance);
    if(std >= STD_THRESH ||
       (VALID_TEST_POINTS[i] == 0.0
        && fabs(mean-128) >= ZERO_THRESH)){
      return false;
    }
  }
  return true;
}


#define CALIB_NPTS 3
const float TEST_POINTS[CALIB_NPTS] = {0,0.5,-0.5};

float Fabric::Chip::Tile::Slice::ChipAdc::calibrateFast(Fabric::Chip::Tile::Slice::Dac * val_dac){

  float mean,variance,dummy;
  float in_val = val_dac->fastMakeValue(0.0);
  float target =Fabric::Chip::Tile::Slice::ChipAdc::computeOutput(this->m_codes,
                                                                  in_val);

  util::meas_dist_adc(this,mean,variance);
  return fabs(target-mean);
}

float Fabric::Chip::Tile::Slice::ChipAdc::calibrateMinError(Fabric::Chip::Tile::Slice::Dac * val_dac){

  float mean,variance;
  float loss_total=0.0;
  for(int i=0; i < CALIB_NPTS; i += 1){
    float test_pt = TEST_POINTS[i]*util::range_to_coeff(this->m_codes.range);
    float in_val = val_dac->fastMakeValue(test_pt);
    float target =Fabric::Chip::Tile::Slice::ChipAdc::computeOutput(this->m_codes,
                                                                   in_val);

    util::meas_dist_adc(this,mean,variance);
    loss_total += fabs(target-mean);
  }
  return loss_total/CALIB_NPTS;
}
float Fabric::Chip::Tile::Slice::ChipAdc::calibrateMaxDeltaFit(Fabric::Chip::Tile::Slice::Dac * val_dac){
  error("unimplemented: integ max_delta_fit");
  return 0.0;
}

void Fabric::Chip::Tile::Slice::ChipAdc::calibrate (calib_objective_t obj) {

  Fabric::Chip::Tile::Slice::Dac * val_dac = parentSlice->dac;
  //backup
  adc_code_t codes_adc = m_codes;
  dac_code_t codes_dac = val_dac->m_codes;
  const float EPS = 1e-4;

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
  for(unsigned char fs=0; fs < 4; fs += 1){
    m_codes.lower_fs = opts[fs];
    m_codes.upper_fs = opts[fs];

    for(unsigned char spread=0; spread < 32; spread++){
      sprintf(FMTBUF,"fs=%d spread=%d",
              fs, spread);
      print_info(FMTBUF);
      for(unsigned char lsign=0; lsign < 2; lsign +=1){
        for(unsigned char usign=0; usign < 2; usign +=1){
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
              float loss;
              switch(obj){
              case CALIB_MINIMIZE_ERROR:
                loss = calibrateMinError(val_dac);
                break;
              case CALIB_MAXIMIZE_DELTA_FIT:
                loss = calibrateMaxDeltaFit(val_dac);
                break;
              case CALIB_FAST:
                loss = calibrateFast(val_dac);
                break;
              default:
                error("unimplemented adc");
                break;
              }
              // TODO
              sprintf(FMTBUF,"fs=(%d,%d) def=(%d,%d) nmos=%d i2v=%d loss=%f",
                      m_codes.lower_fs,
                      m_codes.upper_fs,
                      m_codes.lower,
                      m_codes.upper,
                      nmos,
                      i2v_cal,
                      loss);
              print_info(FMTBUF);
              cutil::update_calib_table(calib_table,loss,6,
                                        m_codes.lower_fs,
                                        m_codes.upper_fs,
                                        m_codes.lower,
                                        m_codes.upper,
                                        nmos,i2v_cal);

              if(fabs(calib_table.loss) < EPS)
                break;
            }
            if(fabs(calib_table.loss) < EPS && calib_table.set)
              break;
          }
          if(fabs(calib_table.loss) < EPS && calib_table.set)
            break;
        }
        if(fabs(calib_table.loss) < EPS && calib_table.set)
          break;
      }
      if(fabs(calib_table.loss) < EPS && calib_table.set)
        break;
    }
    if(fabs(calib_table.loss) < EPS && calib_table.set)
      break;
  }
  if(!calib_table.set){
    error("could not calibrate adc..");
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
    float loss;
    switch(obj){
    case CALIB_MINIMIZE_ERROR:
      loss = calibrateMinError(val_dac);
      break;
    case CALIB_MAXIMIZE_DELTA_FIT:
      loss = calibrateMaxDeltaFit(val_dac);
      break;
    case CALIB_FAST:
      loss = calibrateFast(val_dac);
      break;
    default:
      error("unimplemented adc");
      break;
    }
    cutil::update_calib_table(calib_table,loss,6,
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

  sprintf(FMTBUF,"BEST fs=(%d,%d) def=(%d,%d) nmos=%d i2v=%d loss=%f",
          m_codes.lower_fs,
          m_codes.upper_fs,
          m_codes.lower,
          m_codes.upper,
          m_codes.nmos,
          m_codes.i2v_cal,
          calib_table.loss);
  print_info(FMTBUF);
}
