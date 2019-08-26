#include "AnalogLib.h"
#include "fu.h"
#include "mul.h"
#include "calib_util.h"
#include <float.h>

#define CALIB_NPTS 3
const float TEST_POINTS[CALIB_NPTS] = {-1.0,1.0,0.5};


float Fabric::Chip::Tile::Slice::Multiplier::calibrateMinError(Dac * val0_dac,
                                                               Dac * val1_dac,
                                                               Dac * ref_dac){
  if(this->m_codes.vga){
    return calibrateMinErrorVga(val0_dac, ref_dac);
  }
  else{
    return calibrateMinErrorMult(val0_dac, val1_dac, ref_dac);
  }
}
float Fabric::Chip::Tile::Slice::Multiplier::calibrateMinErrorVga(Dac * val_dac,
                                                                  Dac * ref_dac){
  int npts = 0;
  float total_score = 0.0;
  for(int i=0; i < CALIB_NPTS; i += 1){
    for(int j=0; j < CALIB_NPTS; j += 1){
      float in0 = TEST_POINTS[i];
      float in1 = TEST_POINTS[j];
      float dummy,mean;
      val_dac->setConstant(in0);
      this->setGain(in1);
      float target_in0 = val_dac->fastMeasureValue(dummy);
      float target_out = this->computeOutput(this->m_codes,
                                             Dac::computeInput(val_dac->m_codes,
                                                               target_in0),
                                             0.0);
      const bool meas_steady = false;
      bool succ = cutil::measure_signal_robust(this,
                                               ref_dac,
                                               target_out,
                                               meas_steady,
                                               mean,
                                               dummy);
      if(succ){
        total_score += fabs(mean-target_out);
        npts += 1;
      }
    }
  }
  return total_score/npts;
}
float Fabric::Chip::Tile::Slice::Multiplier::calibrateMinErrorMult(Dac * val0_dac,
                                                                   Dac * val1_dac,
                                                                   Dac * ref_dac){
  int npts = 0;
  float total_score = 0.0;
  for(int i=0; i < CALIB_NPTS; i += 1){
    for(int j=0; j < CALIB_NPTS; j += 1){
      float in0 = TEST_POINTS[i];
      float in1 = TEST_POINTS[j];
      float dummy,mean;
      val0_dac->setConstant(in0);
      val1_dac->setConstant(in1);
      float target_in0 = val0_dac->fastMeasureValue(dummy);
      float target_in1 = val1_dac->fastMeasureValue(dummy);
      float target_out = this->computeOutput(this->m_codes,
                                             Dac::computeInput(val0_dac->m_codes,
                                                               target_in0),
                                             Dac::computeInput(val1_dac->m_codes,
                                                               target_in1)
                                             );

      const bool meas_steady = false;
      bool succ = cutil::measure_signal_robust(this,
                                               ref_dac,
                                               target_out,
                                               meas_steady,
                                               mean,
                                               dummy);
      if(succ){
        total_score += fabs(mean-target_out);
        npts += 1;
      }
    }
  }
  return total_score/npts;
}
void Fabric::Chip::Tile::Slice::Multiplier::calibrate (calib_objective_t obj) {
  mult_code_t codes_self = m_codes;

  int next_slice1 = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  int next_slice2 = (slice_to_int(parentSlice->sliceId) + 2) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice2].dac;
  Dac * val0_dac = parentSlice->dac;
  Dac * val1_dac = parentSlice->parentTile->slices[next_slice1].dac;

  mult_code_t codes_mult = m_codes;
  dac_code_t codes_dac_val0 = val0_dac->m_codes;
  dac_code_t codes_dac_val1 = val1_dac->m_codes;
  dac_code_t codes_dac_ref = ref_dac->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_mult_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_dac_conns(calib,val0_dac);
  cutil::buffer_dac_conns(calib,val1_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile
                              ->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  Connection dac0_to_in0 = Connection (val0_dac->out0, this->in0);
  Connection dac1_to_in1 = Connection (val1_dac->out0, this->in1);
  Connection mult_to_tileout = Connection (this->out0, parentSlice->tileOuts[3].in0);
	Connection tileout_to_chipout = Connection ( parentSlice->tileOuts[3].out0,
                                               parentSlice->parentTile
                                               ->parentChip->tiles[3].slices[2].chipOutput->in0 );
  Fabric::Chip::Connection ref_to_tileout =
    Fabric::Chip::Connection ( ref_dac->out0, parentSlice->tileOuts[3].in0);

  val0_dac->setRange(this->m_codes.range[in0Id]);
  val1_dac->setRange(this->m_codes.range[in1Id]);
  ref_dac->setRange(this->m_codes.range[out0Id]);
  fast_calibrate_dac(val0_dac);
  fast_calibrate_dac(val1_dac);

  mult_to_tileout.setConn();
  ref_to_tileout.setConn();
	tileout_to_chipout.setConn();
  dac0_to_in0.setConn();
  dac1_to_in1.setConn();
  float min_gain_code=32,n_gain_codes=1;
  if(this->m_codes.vga){
    min_gain_code=0;
    n_gain_codes=MAX_GAIN_CAL;
  }

  cutil::calib_table_t calib_table = cutil::make_calib_table();
  /*nmos, gain_cal, port_cal in0,in1,out*/
  for(int nmos=0; nmos < MAX_NMOS; nmos += 1){
    cutil::calib_table_t table_out = cutil::make_calib_table();
    cutil::calib_table_t table_in0 = cutil::make_calib_table();
    cutil::calib_table_t table_in1 = cutil::make_calib_table();
    this->m_codes.nmos = nmos;
    this->m_codes.port_cal[in0Id] = 32;
    this->m_codes.port_cal[in1Id] = 32;
    this->m_codes.port_cal[out0Id] = 32;
    this->m_codes.gain_cal = 32;
    this->setGain(0.0);
    this->setVga(true);
    dac0_to_in0.brkConn();
    dac1_to_in1.brkConn();
    ref_to_tileout.brkConn();
    for(int bias_out=0; bias_out < MAX_BIAS_CAL; bias_out+=1){
      this->m_codes.port_cal[out0Id] = bias_out;
      this->update(this->m_codes);
      float bias = util::meas_chip_out(this);
      cutil::update_calib_table(table_out,fabs(bias),1,bias_out);
    }
    this->m_codes.port_cal[out0Id] = table_out.state[0];

    this->setGain(1.0);
    for(int bias_in0=0; bias_in0 < MAX_BIAS_CAL; bias_in0+=1){
      this->m_codes.port_cal[in0Id] = bias_in0;
      this->update(this->m_codes);
      float bias = util::meas_chip_out(this);
      cutil::update_calib_table(table_in0,fabs(bias),1,bias_in0);
    }
    this->m_codes.port_cal[in0Id] = table_in0.state[0];

    this->setVga(false);
    for(int bias_in1=0; bias_in1 < MAX_BIAS_CAL; bias_in1+=1){
      this->m_codes.port_cal[in1Id] = bias_in1;
      this->update(this->m_codes);
      float bias = util::meas_chip_out(this);
      cutil::update_calib_table(table_in1,fabs(bias),1,bias_in1);
    }
    this->m_codes.port_cal[in1Id] = table_in1.state[0];


    this->m_codes.vga = codes_mult.vga;
    dac0_to_in0.setConn();
    dac1_to_in1.setConn();
    ref_to_tileout.setConn();
    for(int gain_cal=min_gain_code;
        gain_cal < min_gain_code+n_gain_codes;
        gain_cal+=16){
      this->m_codes.gain_cal = gain_cal;
      this->update(this->m_codes);
      float score;
      switch(obj){
      case CALIB_MINIMIZE_ERROR:
        score = calibrateMinError(val0_dac,val1_dac,ref_dac);
        break;
      default:
        error("mult calib : unimplemented");
      }
      cutil::update_calib_table(calib_table,score,5,
                                nmos,
                                this->m_codes.port_cal[in0Id],
                                this->m_codes.port_cal[in1Id],
                                this->m_codes.port_cal[out0Id],
                                gain_cal
                                );
      sprintf(FMTBUF,"nmos=%d port_cal=(%d,%d,%d) gain_cal=%d score=%f",
              this->m_codes.nmos,
              this->m_codes.port_cal[in0Id],
              this->m_codes.port_cal[in1Id],
              this->m_codes.port_cal[out0Id],
              this->m_codes.gain_cal,
              score);
      print_info(FMTBUF);
    }
  }

  this->m_codes.nmos = calib_table.state[0];
  this->m_codes.port_cal[in0Id] = calib_table.state[1];
  this->m_codes.port_cal[in1Id] = calib_table.state[2];
  this->m_codes.port_cal[out0Id] = calib_table.state[3];
  // do a thorough search for best nmos code.
  for(int gain_cal=min_gain_code; gain_cal < min_gain_code+n_gain_codes; gain_cal+=1){
    this->m_codes.gain_cal = gain_cal;
    this->update(this->m_codes);
    float score;
    switch(obj){
    case CALIB_MINIMIZE_ERROR:
      score = calibrateMinError(val0_dac,val1_dac,ref_dac);
      break;
    default:
      error("mult calib : unimplemented");
    }
    cutil::update_calib_table(calib_table,score,5,
                              this->m_codes.nmos,
                              this->m_codes.port_cal[in0Id],
                              this->m_codes.port_cal[in1Id],
                              this->m_codes.port_cal[out0Id],
                              gain_cal
                              );
    sprintf(FMTBUF,"nmos=%d port_cal=(%d,%d,%d) gain_cal=%d score=%f",
            this->m_codes.nmos,
            this->m_codes.port_cal[in0Id],
            this->m_codes.port_cal[in1Id],
            this->m_codes.port_cal[out0Id],
            this->m_codes.gain_cal,
            score);
  }
  val0_dac->update(codes_dac_val0);
  val1_dac->update(codes_dac_val1);
  ref_dac->update(codes_dac_ref);
  this->update(codes_mult);
	tileout_to_chipout.brkConn();
	mult_to_tileout.brkConn();
  cutil::restore_conns(calib);

  this->m_codes.nmos = calib_table.state[0];
  this->m_codes.port_cal[in0Id] = calib_table.state[1];
  this->m_codes.port_cal[in1Id] = calib_table.state[2];
  this->m_codes.port_cal[out0Id] = calib_table.state[3];
  this->m_codes.gain_cal = calib_table.state[4];

  sprintf(FMTBUF,"BEST nmos=%d port_cal=(%d,%d,%d) gain_cal=%d score=%f",
          this->m_codes.nmos,
          this->m_codes.port_cal[in0Id],
          this->m_codes.port_cal[in1Id],
          this->m_codes.port_cal[out0Id],
          this->m_codes.gain_cal,
          calib_table.score);
  print_info(FMTBUF);
}
