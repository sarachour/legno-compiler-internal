#include "AnalogLib.h"
#include <float.h>
#include "assert.h"
#include "calib_util.h"
#include "slice.h"
#include "dac.h"

void fast_calibrate_dac(Fabric::Chip::Tile::Slice::Dac * aux_dac){
  if(!aux_dac->calibrated){
    // do a naive calibration to make sure we have enough range.
    dac_code_t codes = aux_dac->m_codes;
    aux_dac->setEnable(true);
    aux_dac->setRange(RANGE_MED);
    aux_dac->setInv(false);
    aux_dac->calibrate(prof::TEMP,0.02);
    aux_dac->calibrated = true;
    aux_dac->calib_codes = aux_dac->m_codes;
    aux_dac->m_codes = codes;
  }
  aux_dac->m_codes.pmos = aux_dac->calib_codes.pmos;
  aux_dac->m_codes.nmos = aux_dac->calib_codes.nmos;
  aux_dac->m_codes.gain_cal = aux_dac->calib_codes.gain_cal;
  aux_dac->update(aux_dac->m_codes);
}

float Fabric::Chip::Tile::Slice::Dac::fastMakeValue(float target){
  if(fabs(target) < 0.9){
    return fastMakeMedValue(target, 0.02);
  }
  else{
    return fastMakeHighValue(target,0.2);
  }
}
float Fabric::Chip::Tile::Slice::Dac::fastMakeMedValue(float target,
                                                       float max_error){

  dac_code_t codes_dac = m_codes;
  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_dac_conns(calib,this);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice
                              ->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

	Connection this_dac_to_tile = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile
                                         ->parentChip->tiles[3].slices[2].chipOutput->in0 );
  this->setEnable(true);
  this->setRange(RANGE_MED);
  this->setInv(false);
  this->setSource(DSRC_MEM);

  fast_calibrate_dac(this);

  this_dac_to_tile.setConn();
  tile_to_chip.setConn();

  print_debug(FMTBUF);
  // start at what the value would be if the gain was one.
  this->setConstant(target);
  // start out with no code offset
  int delta = 0;
  // store the base code
  int base_code = this->m_codes.const_code;
  // start off with a terrible measured difference
  float mean = 1e6;
  // adjust the code until we fall within some bound of our
  // target difference
  while(fabs(mean - target) > max_error){
    int next_code = base_code + delta;
    if(next_code < 0 || next_code > 255){
      break;
    }
    this->m_codes.const_code = next_code;
    update(this->m_codes);
    mean = util::meas_chip_out(this);
    sprintf(FMTBUF,"DIFF delta=%d targ=%f meas=%f err=%f max_err=%f suc=%s",
            next_code,target,mean,fabs(mean-target),max_error,
            fabs(mean-target) > max_error ? "n" : "y");
    print_debug(FMTBUF);
    delta += target < mean ? -1 : +1;
  }
  this_dac_to_tile.brkConn();
  tile_to_chip.brkConn();
  cutil::restore_conns(calib);
  return mean;


}
// this method makes an approximate current value.
float Fabric::Chip::Tile::Slice::Dac::fastMakeHighValue(float target,
                                                        float max_error){
  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;
  dac_code_t codes_dac = m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;
  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_dac_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice
                              ->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

	Connection this_dac_to_tile = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection ref_dac_to_tile = Connection ( ref_dac->out0, parentSlice->tileOuts[3].in0 );
  // conn3
	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );


  ref_dac->setEnable(true);
  ref_dac->setRange(RANGE_HIGH);
  ref_dac->setInv(false);
  ref_dac->setSource(DSRC_MEM);
  fast_calibrate_dac(ref_dac);

  this->setEnable(true);
  this->setRange(RANGE_HIGH);
  this->setInv(false);
  this->setSource(DSRC_MEM);
  fast_calibrate_dac(this);

  this_dac_to_tile.setConn();
  ref_dac_to_tile.setConn();
  tile_to_chip.setConn();

  // make sure the reference values are always
  // the opposite sign of the target signal.
  float value = target < 0 ? -1e-6 : 1e-6;
  float step = 0.5;

  // determine zero for the reference dac
  this_dac_to_tile.brkConn();
  ref_dac_to_tile.setConn();
  ref_dac->setConstant(0.0);
  float ref_value = util::meas_chip_out(this);

  // determine zero for this dac
  ref_dac_to_tile.brkConn();
  this_dac_to_tile.setConn();
  this->setConstant(0.0);
  float dac_value = util::meas_chip_out(this);

  // add these dacs togeth
  this_dac_to_tile.setConn();
  ref_dac_to_tile.setConn();
  bool update_ref = true;
  // connect reference dac.
  // telescope the dacs outward until we find
  // a value for the reference dac that is within
  // one step of the target
  while(fabs(ref_value) < fabs(target)
        && fabs(value) <= 10.0){
    float old_value = value;
    // telescope outward
    value = -(value < 0 ? value - step : value + step);
    float mean = -99.0;
    if(update_ref){
      ref_dac->setConstant((value)*0.1);
      mean = util::meas_chip_out(this);
      ref_value = -dac_value + mean;
    }
    else{
      this->setConstant((value)*0.1);
      mean = util::meas_chip_out(this);
      dac_value = -ref_value + mean;
    }
    // emit information
    sprintf(FMTBUF, "%s dac_val=%f ref_val=%f mean=%f dac=%f ref=%f",
            update_ref ? "R" : "D",
            this->m_codes.const_val,
            ref_dac->m_codes.const_val,
            mean,
            dac_value,
            ref_value);
    print_debug(FMTBUF);
    update_ref = !update_ref;
  }
  // compute the expected difference, with respect to this
  // reference dac
  float target_diff = target + ref_value;
  sprintf(FMTBUF,"C target=%f ref=%f diff=%f",
          target,ref_dac->m_codes.const_val,
          target_diff);
  print_debug(FMTBUF);
  // start at what the value would be if the gain was one.
  this->setConstant(target*0.1);
  // start out with no code offset
  int delta = 0;
  // store the base code
  int base_code = this->m_codes.const_code;
  // start off with a terrible measured difference
  float mean = 1e6;
  // adjust the code until we fall within some bound of our
  // target difference
  while(fabs(mean - target_diff) > max_error){
    int next_code = base_code + delta;
    if(next_code < 0 || next_code > 255){
      break;
    }
    this->m_codes.const_code = next_code;
    update(this->m_codes);
    mean = util::meas_chip_out(this);
    sprintf(FMTBUF,"DIFF delta=%d targ=%f meas=%f err=%f max_err=%f suc=%s",
            next_code,target_diff,mean,fabs(mean-target_diff),max_error,
            fabs(mean-target_diff) > max_error ? "n" : "y");
    print_debug(FMTBUF);
    delta += target_diff < mean ? -1 : +1;
  }

  this_dac_to_tile.brkConn();
  ref_dac_to_tile.brkConn();
  tile_to_chip.brkConn();
  cutil::restore_conns(calib);
  ref_dac->update(codes_ref);

  return mean - ref_value;
}

float Fabric::Chip::Tile::Slice::Dac::fastMeasureValue(){
  if(this->m_codes.range == RANGE_HIGH){
    return fastMeasureHighValue();
  }
  else {
    return fastMeasureMedValue();
  }
}

float Fabric::Chip::Tile::Slice::Dac::fastMeasureMedValue(){
  dac_code_t codes_dac = m_codes;
  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_dac_conns(calib,this);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice
                              ->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);
	Connection this_dac_to_tile = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );


  this_dac_to_tile.setConn();
  tile_to_chip.setConn();
  float mean = util::meas_chip_out(this);
  this_dac_to_tile.brkConn();
  tile_to_chip.brkConn();
  cutil::restore_conns(calib);
  update(codes_dac);
  return mean;


}
// very quickly measures a value using uncalibrated dacs.
float Fabric::Chip::Tile::Slice::Dac::fastMeasureHighValue(){

  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;
  dac_code_t codes_dac = m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;
  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_dac_conns(calib,this);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,parentSlice
                              ->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

	Connection this_dac_to_tile = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection ref_dac_to_tile = Connection ( ref_dac->out0, parentSlice->tileOuts[3].in0 );
  // conn3
	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );


  this->setEnable(true);
  this->setRange(RANGE_HIGH);
  this->setSource(DSRC_MEM);

  ref_dac->setEnable(true);
  ref_dac->setRange(RANGE_HIGH);
  ref_dac->setSource(DSRC_MEM);
  fast_calibrate_dac(ref_dac);

  this_dac_to_tile.setConn();
  ref_dac_to_tile.setConn();
  tile_to_chip.setConn();
  //compute the floating point value from the dac code.
  float value = ((this->m_codes.const_code-128.0)/128.0)*10.0;
  float step = 1.0;
  float total = 0.0;
  bool update_ref = true;
  while(fabs(value) >= step){
    float old_value = value;
    value= -(value< 0 ? value+ step : value-step);
    //telescope the value
    //alternate between updating the reference.
    if(update_ref){
      ref_dac->setConstant(value/10.0);
    }
    else{
      this->setConstant(value/10.0);
    }
    float mean = util::meas_chip_out(this);
    /*
      if we can't measure the difference, adjust
      the value of the dac we're tuning until we're
      in a measurable range.
    */
    while(fabs(mean) > 1.2 &&
          fabs(value) < 10.0){
      // this value is too negative
      value += mean < -1.2 ? step*0.1 : -step*0.1;
      if(update_ref){
        ref_dac->setConstant(value/10.0);
      }
      else{
        this->setConstant(value/10.0);
      }
      mean = util::meas_chip_out(this);
    }
    total += fabs(mean);
    sprintf(FMTBUF, "%s old=%f new=%f mean=%f total=%f",
            update_ref ? "R" : "D",
            old_value,
            value,
            mean,
            total);
    print_debug(FMTBUF);
    update_ref = !update_ref;
  }
  if(update_ref){
    ref_dac_to_tile.brkConn();
  }
  else{
    this_dac_to_tile.brkConn();
  }
  float mean = util::meas_chip_out(this);
  total += fabs(mean);
  sprintf(FMTBUF, "B old=%f new=%f mean=%f total=%f",
          value,
          0.0,
          mean,
          total);
  print_debug(FMTBUF);
  total = this->m_codes.const_val > 0 ? total : -total;
  ref_dac_to_tile.brkConn();
  this_dac_to_tile.brkConn();
  tile_to_chip.brkConn();
  cutil::restore_conns(calib);
  update(codes_dac);
  ref_dac->update(codes_ref);
  return total;
}
