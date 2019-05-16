#include "AnalogLib.h"
#include <float.h>
#include "calib_util.h"
#include "fu.h"

void Fabric::Chip::Tile::Slice::Integrator::update(integ_code_t codes){
  m_codes = codes;
  updateFu();
}
void Fabric::Chip::Tile::Slice::Integrator::setEnable (
	bool enable
) {
	m_codes.enable = enable;
	setParam0 ();
	setParam1 ();
	setParam3 ();
	setParam4 ();
}

void Fabric::Chip::Tile::Slice::Integrator::IntegratorOut::setInv (
	bool inverse // whether output is negated
) {
	parentIntegrator->m_codes.inv[ifcId] = inverse;
	parentFu->setEnable (
		parentIntegrator->m_codes.enable
	);
}

void Fabric::Chip::Tile::Slice::Integrator::IntegratorOut::setRange (range_t range) {
	/*check*/
  parentIntegrator->m_codes.range[ifcId] = range;
	parentFu->setEnable (parentIntegrator->m_codes.enable);
}

void Fabric::Chip::Tile::Slice::Integrator::IntegratorIn::setRange (range_t range) {
	/*check*/
  parentIntegrator->m_codes.range[ifcId] = range;
	parentFu->setEnable (parentIntegrator->m_codes.enable);
}

void Fabric::Chip::Tile::Slice::Integrator::setInitialCode (
	unsigned char initialCode // fixed point representation of initial condition
) {
  m_codes.ic_code = initialCode;
  m_codes.ic_val = (initialCode-128)/128.0;
	setParam2 ();
}

bool Fabric::Chip::Tile::Slice::Integrator::setInitial(float initial)
{
  if(-1.0000001 < initial && initial < 1.000001){
    setInitialCode(min(initial*128.0+128.0,255));
    m_codes.ic_val = initial;
    return true;
  }
  else{
    return false;
  }
}


void Fabric::Chip::Tile::Slice::Integrator::setException (
	bool exception // turn on overflow detection
	// turning false overflow detection saves power if it is known to be unnecessary
) {
	m_codes.exception = exception;
	setParam1 ();
}

bool Fabric::Chip::Tile::Slice::Integrator::getException () const {
	unsigned char exceptionVector;
	parentSlice->parentTile->readExp ( exceptionVector );
	// bits 0-3: Integrator overflow
	SerialUSB.print (exceptionVector);
	SerialUSB.print (" ");
	return bitRead (exceptionVector, parentSlice->sliceId);
}
void Fabric::Chip::Tile::Slice::Integrator::defaults (){
  m_codes.pmos = 5;
  m_codes.nmos = 0;
  m_codes.ic_code = 128;
  m_codes.ic_val = 0.0;
  m_codes.inv[in0Id] = false;
  m_codes.inv[in1Id] = false;
  m_codes.inv[out0Id] = false;
  m_codes.range[in0Id] = RANGE_MED;
  m_codes.range[in1Id] = RANGE_UNKNOWN;
  m_codes.range[out0Id] = RANGE_MED;
  m_codes.cal_enable[in0Id] = false;
  m_codes.cal_enable[in1Id] = false;
  m_codes.cal_enable[out0Id] = false;
  m_codes.port_cal[in0Id] = 31;
  m_codes.port_cal[in1Id] = 0;
  m_codes.port_cal[out0Id] = 31;
  m_codes.exception = false;
  m_codes.gain_cal = 32;
	setAnaIrefNmos();
	setAnaIrefPmos();
}

Fabric::Chip::Tile::Slice::Integrator::Integrator (
	Chip::Tile::Slice * parentSlice
) :
	FunctionUnit(parentSlice, unitInt)
{
	in0 = new IntegratorIn (this);
	tally_dyn_mem <IntegratorIn> ("IntegratorIn");
	out0 = new IntegratorOut (this);
	tally_dyn_mem <IntegratorOut> ("IntegratorOut");
  defaults();
}

/*Set enable, invert, range*/
void Fabric::Chip::Tile::Slice::Integrator::setParam0 () const {
	intRange intRange;
  bool out0_loRange = (m_codes.range[out0Id] == RANGE_LOW);
  bool out0_hiRange = (m_codes.range[out0Id] == RANGE_HIGH);
  bool in0_loRange = (m_codes.range[in0Id] == RANGE_LOW);
  bool in0_hiRange = (m_codes.range[in0Id] == RANGE_HIGH);

	if (out0_loRange) {
		if (in0_loRange) {
			intRange = mGainLRng;
		} else if (in0_hiRange) {
			error ("cannot set integrator output loRange when input hiRange");
		} else {
			intRange = lGainLRng;
		}
	} else if (out0_hiRange) {
		if (in0_loRange) {
			error ("cannot set integrator output hiRange when input loRange");
		} else if (in0_hiRange) {
			intRange = mGainHRng;
		} else {
			intRange = hGainHRng;
		}
	} else {
		if (in0_loRange) {
			intRange = hGainMRng;
		} else if (in0_hiRange) {
			intRange = lGainMRng;
		} else {
			intRange = mGainMRng;
		}
	}

	unsigned char cfgTile = 0;
	cfgTile += m_codes.enable ? 1<<7 : 0;
	cfgTile += (m_codes.inv[out0Id]) ? 1<<6 : 0;
	cfgTile += intRange<<3;
	setParamHelper (0, cfgTile);
}

/*Set calIc, overflow enable*/
void Fabric::Chip::Tile::Slice::Integrator::setParam1 () const {
	unsigned char cfgCalIc = m_codes.gain_cal;
	if (cfgCalIc<0||63<cfgCalIc) error ("cfgCalIc out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += cfgCalIc<<2;
	cfgTile += (m_codes.exception) ? 1<<1 : 0;
	setParamHelper (1, cfgTile);
}

/*Set initial condition*/
void Fabric::Chip::Tile::Slice::Integrator::setParam2 () const {
	setParamHelper (2, m_codes.ic_code);
}

/*Set calOutOs, calOutEn*/
void Fabric::Chip::Tile::Slice::Integrator::setParam3 () const {
	unsigned char calOutOs = m_codes.port_cal[out0Id];
	if (calOutOs<0||63<calOutOs) error ("calOutOs out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += calOutOs<<2;
	cfgTile += (m_codes.cal_enable[out0Id]) ? 1<<1 : 0;
	setParamHelper (3, cfgTile);
}

/*Set calInOs, calInEn*/
void Fabric::Chip::Tile::Slice::Integrator::setParam4 () const {
	unsigned char calInOs = m_codes.port_cal[in0Id];
	if (calInOs<0||63<calInOs) error ("calInOs out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += calInOs<<2;
	cfgTile += (m_codes.cal_enable[in0Id]) ? 1<<1 : 0;
	setParamHelper (4, cfgTile);
}

/*Helper function*/
void Fabric::Chip::Tile::Slice::Integrator::setParamHelper (
	unsigned char selLine,
	unsigned char cfgTile
) const {
	if (selLine<0||4<selLine) error ("selLine out of bounds");

	/*DETERMINE SEL_ROW*/
	unsigned char selRow;
	switch (parentSlice->sliceId) {
		case slice0: selRow = 2; break;
		case slice1: selRow = 3; break;
		case slice2: selRow = 4; break;
		case slice3: selRow = 5; break;
		default: error ("invalid slice. Only slices 0 through 3 have INTs"); break;
	}

	Vector vec = Vector (
		*this,
		selRow,
		2,
		selLine,
		endian (cfgTile)
	);

	parentSlice->parentTile->parentChip->cacheVec (
		vec
	);
}

bool Fabric::Chip::Tile::Slice::Integrator::calibrate (util::calib_result_t& result, const float max_error) {
  integ_code_t codes_self = m_codes;

	setEnable(true);
	Connection conn2 = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection conn3 = Connection ( parentSlice->tileOuts[3].out0, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
	conn2.setConn();
	conn3.setConn();

  bool new_search = true;
  bool calib_failed = true;

	m_codes.nmos = 0;
	setAnaIrefNmos ();

  while (new_search) {
    float errors[2];
    unsigned char codes[2];
    sprintf(FMTBUF, "nmos=%d", m_codes.nmos);
    print_debug(FMTBUF);
    Serial.println(m_codes.nmos);
    m_codes.cal_enable[out0Id] = true;
    binsearch::find_bias(this, 0.0,
                         m_codes.port_cal[out0Id],
                         errors[0],
                         MEAS_CHIP_OUTPUT);
    codes[0] = m_codes.port_cal[out0Id];
    m_codes.cal_enable[out0Id] = false;
    m_codes.cal_enable[in0Id] = true;
    binsearch::find_bias(this, 0.0,
                         m_codes.port_cal[in0Id],
                         errors[1],
                         MEAS_CHIP_OUTPUT);
    codes[1] = m_codes.port_cal[in0Id];
    m_codes.cal_enable[in0Id] = false;
    binsearch::multi_test_stab_and_update_nmos(this,
                                               codes, errors,
                                               max_error,
                                               2,
                                               m_codes.nmos,
                                               new_search,
                                               calib_failed);
  }
  conn2.brkConn();
	conn3.brkConn();
	setEnable(false);
  codes_self.nmos = m_codes.nmos;
  codes_self.port_cal[out0Id] = m_codes.port_cal[out0Id];
  codes_self.port_cal[in0Id] = m_codes.port_cal[in0Id];
  update(codes_self);
  return !calib_failed;

}

bool helper_find_cal_in0(Fabric::Chip::Tile::Slice::Integrator * integ,
                         float max_error){
  float error;
  bool calib_failed;
  integ->m_codes.cal_enable[out0Id] = false;
  integ->m_codes.cal_enable[in0Id] = true;
  binsearch::find_bias(integ, 0.0,
                       integ->m_codes.port_cal[in0Id],
                       error,
                       MEAS_CHIP_OUTPUT);
  int code = integ->m_codes.port_cal[in0Id];
  binsearch::test_stab(code,
                       error,
                       max_error,
                       calib_failed);
  sprintf(FMTBUF,"integ in0 target=%f measured=%f max=%f",
          0.0, error, max_error);
  print_info(FMTBUF);
  integ->m_codes.cal_enable[in0Id] = false;
  return !calib_failed;

}
bool helper_find_cal_out0(Fabric::Chip::Tile::Slice::Integrator * integ,
                          float max_error){
  float error;
  bool calib_failed;
  integ->m_codes.cal_enable[in0Id] = false;
  integ->m_codes.cal_enable[out0Id] = true;
  binsearch::find_bias(integ, 0.0,
                       integ->m_codes.port_cal[out0Id],
                       error,
                       MEAS_CHIP_OUTPUT);

  int code = integ->m_codes.port_cal[out0Id];
  binsearch::test_stab(code,
                       error,
                       max_error,
                       calib_failed);
  sprintf(FMTBUF,"integ out0 target=%f measured=%f max=%f",
          0.0, error, max_error);
  print_info(FMTBUF);
  integ->m_codes.cal_enable[out0Id] = false;
  return !calib_failed;
}
bool helper_find_cal_gain(Fabric::Chip::Tile::Slice::Integrator * integ,
                          Fabric::Chip::Tile::Slice::Dac * ref_dac,
                          float max_error,
                          int code,
                          float target,
                          dac_code_t& ref_codes,
                          int update_pos_error){

  unsigned int delta = 0;
  bool succ = false;
  float error;
  // adjust the initial condition code.
  ref_dac->update(ref_codes);
  while(!succ){
    int gain_code;
    bool calib_failed;
    if(code + delta > 255
       || code + delta < 0){
      break;
    }
    integ->setInitialCode(code+delta);
    binsearch::find_bias(integ,
                         target,
                         integ->m_codes.gain_cal,
                         error,
                         MEAS_CHIP_OUTPUT);
    gain_code = integ->m_codes.gain_cal;
    binsearch::test_stab(gain_code,
                         error,
                         max_error,
                         calib_failed);
    succ = !calib_failed;
    sprintf(FMTBUF,"init-cond code=%d target=%f measured=%f",
            code+delta, target, target+error);
    print_info(FMTBUF);
    if(!succ){
      if(error < 0){
        delta += update_pos_error*-1;
      }
      else{
        delta += update_pos_error;
      }
    }
  }
  integ->m_codes.ic_code = code+delta;
  return succ;
}
bool Fabric::Chip::Tile::Slice::Integrator::calibrateTarget (util::calib_result_t& result,
                                                             const float max_error) {
  if(!m_codes.enable){
    return true;
  }
  bool hiRange = (m_codes.range[out0Id] == RANGE_HIGH);
  int ic_sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  int update_pos = ic_sign*m_codes.ic_val >= 0 ? -1 : 1;
  Dac * ref_dac = parentSlice->dac;

  integ_code_t codes_self = m_codes;
  dac_code_t ref_codes = ref_dac->m_codes;


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
  util::calib_result_t dac_0_result;
  util::calib_result_t dac_ic_result;

  print_info("making zero dac");
  dac_0 = make_zero_dac(calib, ref_dac,dac_0_result);
  if (hiRange) {
    print_info("high range! making reference dac");
    dac_ic = make_val_dac(calib,ref_dac,
                          -10.0*m_codes.ic_val*ic_sign,
                          dac_ic_result);
    update_pos = -1;
    ref_to_tile.setConn();
  }
  integ_to_tile.setConn();
	tile_to_chip.setConn();
  ref_dac->update(dac_0);

  bool found_code = false;
  integ_code_t best_code = m_codes;

  print_info("=== calibrate integrator ===");
  m_codes.nmos = 0;
	setAnaIrefNmos ();
  unsigned int code = m_codes.ic_code;
  while (m_codes.nmos <= 7 && !found_code && calib.success) {
    bool succ = true;
    sprintf(FMTBUF, "nmos=%d", m_codes.nmos);
    print_info(FMTBUF);

    succ &= helper_find_cal_out0(this,max_error);
    if(succ)
      succ &= helper_find_cal_in0(this,max_error*2.0);
    if(succ)
      succ &= helper_find_cal_gain(this,ref_dac,max_error,code,
                                   hiRange ? 0.0: m_codes.ic_val*ic_sign,
                                   hiRange ? dac_ic : dac_0,
                                   update_pos);
    ref_dac->update(dac_0);

    if(succ){
      found_code = true;
      best_code = m_codes;
    }
    m_codes.nmos += 1;
    if(m_codes.nmos <= 7){
      setAnaIrefNmos ();
    }
  }

  update(best_code);
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
	return found_code && calib.success;
}


void Fabric::Chip::Tile::Slice::Integrator::setAnaIrefNmos () const {
	unsigned char selRow=0;
	unsigned char selCol=2;
	unsigned char selLine;
  binsearch::test_iref(m_codes.nmos);
	switch (parentSlice->sliceId) {
		case slice0: selLine=1; break;
		case slice1: selLine=2; break;
		case slice2: selLine=0; break;
		case slice3: selLine=3; break;
		default: error ("INT invalid slice"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	cfgTile = (cfgTile & 0b00000111) + ((m_codes.nmos<<3) & 0b00111000);

	Vector vec = Vector (
		*this,
		selRow,
		selCol,
		selLine,
		endian (cfgTile)
	);

	parentSlice->parentTile->parentChip->cacheVec (
		vec
	);

}

void Fabric::Chip::Tile::Slice::Integrator::setAnaIrefPmos () const {

	unsigned char selRow=0;
	unsigned char selCol;
	unsigned char selLine;
  binsearch::test_iref(m_codes.pmos);
	switch (parentSlice->sliceId) {
		case slice0: selCol=3; selLine=4; break;
		case slice1: selCol=3; selLine=5; break;
		case slice2: selCol=4; selLine=3; break;
		case slice3: selCol=4; selLine=4; break;
		default: error ("INT invalid slice"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	switch (parentSlice->sliceId) {
		case slice0: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos & 0b00000111); break;
		case slice1: cfgTile = (cfgTile & 0b00000111) + ((m_codes.pmos<<3) & 0b00111000); break;
		case slice2: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos & 0b00000111); break;
		case slice3: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos & 0b00000111); break;
		default: error ("INT invalid slice"); break;
	}

	Vector vec = Vector (
		*this,
		selRow,
		selCol,
		selLine,
		endian (cfgTile)
	);

	parentSlice->parentTile->parentChip->cacheVec (
		vec
	);
}
