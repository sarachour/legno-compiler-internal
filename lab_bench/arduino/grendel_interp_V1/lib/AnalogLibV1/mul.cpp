#include "AnalogLib.h"
#include "fu.h"
#include "calib_util.h"
#include <float.h>

void Fabric::Chip::Tile::Slice::Multiplier::update(mult_code_t codes){
  m_codes = codes;
  updateFu();
}

void Fabric::Chip::Tile::Slice::Multiplier::setEnable (
	bool enable
) {
	m_codes.enable = enable;
	setParam0 ();
	/*establish calibration codes*/
	setParam1 ();
	setParam3 ();
	setParam4 ();
	setParam5 ();
}

void Fabric::Chip::Tile::Slice::Multiplier::setVga (
	bool vga // constant coefficient multiplier mode
) {
	m_codes.vga = vga;
	setParam1 ();
}

void Fabric::Chip::Tile::Slice::Multiplier::setGainCode (
	unsigned char gainCode // fixed point representation of desired gain
) {
	// Serial.println("setGainCode");
	// Serial.println(gainCode);
	setVga (true);
	m_codes.gain_code = gainCode;
  m_codes.gain_val = (gainCode-128)/128.0;
	setParam2 ();
}

bool Fabric::Chip::Tile::Slice::Multiplier::setGain(float gain){
  if(-1.0000001 < gain && gain < 127.0/128.0){
    setGainCode(gain*128.0+128.0);
    m_codes.gain_val= gain;
    return true;
  }
  else{
    return false;
  }
}


void Fabric::Chip::Tile::Slice::Multiplier::MultiplierInterface::setRange (range_t range) {
  parentMultiplier->m_codes.range[ifcId] = range;
	parentFu->setParam0 ();
	parentFu->setParam3 ();
	parentFu->setParam4 ();
	parentFu->setParam5 ();
}

void Fabric::Chip::Tile::Slice::Multiplier::defaults () {
  m_codes.pmos = 3;
  m_codes.nmos = 0;
  m_codes.vga = false;
  m_codes.gain_code = 128;
  m_codes.gain_val = 0.0;
  m_codes.gain_cal = 0;
  m_codes.inv[in0Id] = false;
  m_codes.inv[in1Id] = false;
  m_codes.inv[out0Id] = false;
  m_codes.range[in0Id] = RANGE_MED;
  m_codes.range[in1Id] = RANGE_MED;
  m_codes.range[out0Id] = RANGE_MED;
  m_codes.port_cal[in0Id] = 31;
  m_codes.port_cal[in1Id] = 31;
  m_codes.port_cal[out0Id] = 31;
  m_codes.enable = false;
  setAnaIrefNmos();
	setAnaIrefPmos();
}


Fabric::Chip::Tile::Slice::Multiplier::Multiplier (
	Slice * parentSlice,
	unit unitId
) :
	FunctionUnit(parentSlice, unitId)
{
	out0 = new MultiplierInterface (this, out0Id);
	tally_dyn_mem <MultiplierInterface> ("MultiplierInterface");
	in0 = new MultiplierInterface (this, in0Id);
	tally_dyn_mem <MultiplierInterface> ("MultiplierInterface");
	in1 = new MultiplierInterface (this, in1Id);
	tally_dyn_mem <MultiplierInterface> ("MultiplierInterface");
  defaults();
}

mulRange range_to_mulRange(range_t rng){
  switch(rng){
  case RANGE_HIGH: return mulHi;
  case RANGE_LOW: return mulLo;
  case RANGE_MED: return mulMid;
  default: error("unknown range");
  }
  return mulMid;
}
/*Set enable, input 1 range, input 2 range, output range*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam0 () const {
	unsigned char cfgTile = 0;
	cfgTile += m_codes.enable ? 1<<7 : 0;
	cfgTile += (range_to_mulRange(m_codes.range[in0Id]))<<4;
	cfgTile += (range_to_mulRange(m_codes.range[in1Id]))<<2;
	cfgTile += (range_to_mulRange(m_codes.range[out0Id]))<<0;
	setParamHelper (0, cfgTile);
}

/*Set calDac, enable variable gain amplifer mode*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam1 () const {
  unsigned char negGainCalCode = m_codes.gain_cal;
	if (negGainCalCode<0||63<negGainCalCode) error ("midNegGainCode out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += negGainCalCode<<2;
	cfgTile += m_codes.vga ? 1<<1 : 0;
	setParamHelper (1, cfgTile);
}

/*Set gain if VGA mode*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam2 () const {
  unsigned char gainCode = m_codes.gain_code;
	if (gainCode<0||255<gainCode) error ("gain out of bounds");
	setParamHelper (2, gainCode);
}

/*Set calOutOs*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam3 () const {
  unsigned char calOutOs = m_codes.port_cal[out0Id];
	if (calOutOs<0||63<calOutOs) error ("calOutOs out of bounds");
	unsigned char cfgTile = calOutOs<<2;
	setParamHelper (3, cfgTile);
}

/*Set calInOs1*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam4 () const {
  unsigned char calInOs1 = m_codes.port_cal[in0Id];
	if (calInOs1<0||63<calInOs1) error ("calInOs1 out of bounds");
	unsigned char cfgTile = calInOs1<<2;
	setParamHelper (4, cfgTile);
}

/*Set calInOs2*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam5 () const {
  unsigned char calInOs2 = m_codes.port_cal[in1Id];
	if (calInOs2<0||63<calInOs2) error ("calInOs2 out of bounds");
	unsigned char cfgTile = calInOs2<<2;
	setParamHelper (5, cfgTile);
}

void Fabric::Chip::Tile::Slice::Multiplier::setParamHelper (
	unsigned char selLine,
	unsigned char cfgTile
) const {
	if (selLine<0||5<selLine) error ("selLine out of bounds");

	/*DETERMINE SEL_ROW*/
	unsigned char selRow;
	switch (parentSlice->sliceId) {
		case slice0: selRow = 2; break;
		case slice1: selRow = 3; break;
		case slice2: selRow = 4; break;
		case slice3: selRow = 5; break;
		default: error ("invalid slice. Only slices 0 through 3 have MULs"); break;
	}

	/*DETERMINE SEL_COL*/
	unsigned char selCol;
	switch (unitId) {
		case unitMulL: selCol = 3; break;
		case unitMulR: selCol = 4; break;
		default: error ("invalid unit. Only unitMulL and unitMulR are MULs"); break;
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

bool Fabric::Chip::Tile::Slice::Multiplier::calibrate (float max_error) {
  mult_code_t codes_self = m_codes;
	setGain(-1.0);
  bool succ = calibrateTarget(max_error);
  codes_self.nmos = m_codes.nmos;
  codes_self.pmos = m_codes.pmos;
  codes_self.port_cal[in0Id] = m_codes.port_cal[in0Id];
  codes_self.port_cal[in1Id] = m_codes.port_cal[in1Id];
  codes_self.port_cal[out0Id] = m_codes.port_cal[out0Id];
  codes_self.gain_cal = m_codes.gain_cal;
  update(codes_self);
	return succ;
}

bool helper_find_port_cal_out0(Fabric::Chip::Tile::Slice::Dac* dac,
                               Fabric::Chip::Tile::Slice::Multiplier* mult,
                               float max_error){
  float delta;
  bool calib_failed;
  //out0Id
  mult->setGain(0.0);
  mult->setVga(true);
  dac->setEnable(false);
  binsearch::find_bias(mult, 0.0,
                       mult->m_codes.port_cal[out0Id],
                       delta,
                       MEAS_CHIP_OUTPUT);
  // update nmos code
  binsearch::test_stab(mult->m_codes.port_cal[out0Id],fabs(delta),
                       max_error,calib_failed);


  return !calib_failed;

}

bool helper_find_port_cal_in0(Fabric::Chip::Tile::Slice::Dac* dac,
                              Fabric::Chip::Tile::Slice::Multiplier* mult,
                              float max_error){
  float delta;
  bool calib_failed;
  mult->setGain(1.0);
  mult->setVga(true);
  dac->setEnable(false);
  binsearch::find_bias(mult, 0.0,
                       mult->m_codes.port_cal[in0Id],
                       delta,
                       MEAS_CHIP_OUTPUT);
  // update nmos code
  binsearch::test_stab(mult->m_codes.port_cal[in0Id],fabs(delta),
                       max_error,calib_failed);

  return !calib_failed;
}

bool helper_find_port_cal_in1(Fabric::Chip::Tile::Slice::Dac* dac,
                              Fabric::Chip::Tile::Slice::Multiplier* mult,
                              dac_code_t& dac_code_0,
                              float max_error){
  //in1id
  /* find bias by minimizing error of 0*0 */
  float delta;
  bool calib_failed;
  Fabric::Chip::Connection conn_in1 = Fabric::Chip::Connection (
                                                                dac->out0, mult->in0);
  mult->setVga(false);
  dac->update(dac_code_0);
  dac->setEnable(true);
  conn_in1.setConn();
  binsearch::find_bias(mult, 0.0,
                       mult->m_codes.port_cal[in1Id],
                       delta,
                       MEAS_CHIP_OUTPUT);
  // update nmos code
  binsearch::test_stab(mult->m_codes.port_cal[in1Id],fabs(delta),
                       max_error,calib_failed);

  conn_in1.brkConn();
  dac->setEnable(false);
  return !calib_failed;

}

bool helper_find_pmos(Fabric::Chip::Tile::Slice::Dac* dac,
                      Fabric::Chip::Tile::Slice::Fanout* fan,
                      Fabric::Chip::Tile::Slice::Multiplier* mult,
                      dac_code_t& dac_code_1,
                      float max_error){
  print_debug("pmos calibrate");
  range_t outrng = mult->m_codes.range[out0Id];
  range_t in0rng = mult->m_codes.range[in0Id];
  range_t in1rng = mult->m_codes.range[in1Id];
  Fabric::Chip::Connection dac_to_fan = Fabric::Chip::Connection ( dac->out0,
                                       fan->in0 );
  Fabric::Chip::Connection fan_to_mult_in0 = Fabric::Chip::Connection ( fan->out0, mult->in0 );
  //conn6
  Fabric::Chip::Connection fan_to_mult_in1 = Fabric::Chip::Connection ( fan->out1, mult->in1 );

  /* find the pmos value by minimizing the error
     of the computation -1*-1 */
  dac->update(dac_code_1);
  dac->setEnable(true);
  // conn4 : dac_to_fan
  // conn5 : fan_to_mult_in0
  // conn6: fan_to_mult_in1

  dac_to_fan.setConn();
  fan_to_mult_in0.setConn();
  fan_to_mult_in1.setConn();

  mult->out0->setRange(RANGE_MED);
  mult->in0->setRange(RANGE_MED);
  mult->in1->setRange(RANGE_MED);
  mult->setVga(false);
  // find best effort pmos
  float error;
  binsearch::find_pmos(mult,1.0,
                       mult->m_codes.pmos,
                       error,
                       MEAS_CHIP_OUTPUT);
  // update nmos code
  //binsearch::test_stab(mult->m_codes.gain_cal,fabs(delta),
  //                    max_error,calib_failed);
  sprintf(FMTBUF, "calibrate pmos target=%f meas=%f",1.0,1.0+error);
  print_log(FMTBUF);

  mult->out0->setRange(outrng);
  mult->in0->setRange(in0rng);
  mult->in1->setRange(in1rng);

  dac_to_fan.brkConn();
  fan_to_mult_in0.brkConn();
  fan_to_mult_in1.brkConn();
  return true;
}

bool helper_find_gain_cal(float gain,
                          Fabric::Chip::Tile::Slice::Multiplier* mult,
                          Fabric::Chip::Tile::Slice::Dac* val_dac,
                          Fabric::Chip::Tile::Slice::Dac* ref_dac,
                          Fabric::Chip::Tile::Slice::TileInOut* tileout,
                          bool hiRange,
                          float target,
                          dac_code_t& dac_ref_target,
                          dac_code_t& dac_code_0_1,
                          dac_code_t& dac_code_1,
                          float max_error){

	Fabric::Chip::Connection ref_to_tileout = Fabric::Chip::Connection ( ref_dac->out0, tileout->in0 );
  Fabric::Chip::Connection dac_to_mult_in0 = Fabric::Chip::Connection ( val_dac->out0, mult->in0 );
  bool calib_failed;
  val_dac->setEnable(true);
  if(mult->m_codes.range[in0Id] == RANGE_LOW){
    val_dac->update(dac_code_0_1);
  }
  else{
    val_dac->update(dac_code_1);
  }
  if(hiRange){
    ref_dac->update(dac_ref_target);
    ref_to_tileout.setConn();
  }
  // set multiplier to vga, set routes
  mult->setVga(true);
  mult->setGain(gain);
  dac_to_mult_in0.setConn();
  float error;
  binsearch::find_bias(mult,
                       target,
                       mult->m_codes.gain_cal,
                       error,
                       MEAS_CHIP_OUTPUT
                       );
  sprintf(FMTBUF, "calibrate gain=%f target=%f meas=%f",gain,target,target+error);
  print_log(FMTBUF);
  // update nmos code
  binsearch::test_stab(mult->m_codes.gain_cal,fabs(error),
                       max_error,calib_failed);

  //teardown
  if (hiRange) {
    ref_to_tileout.brkConn();
  }
  dac_to_mult_in0.brkConn();
  return !calib_failed;
}
bool Fabric::Chip::Tile::Slice::Multiplier::calibrateTarget (float max_error) {
  float gain = m_codes.gain_val;
  int sign = m_codes.inv[out0Id] ? -1.0 : 1.0;
  bool hiRange = m_codes.range[out0Id] == RANGE_HIGH;
  bool loRange = m_codes.range[in0Id] == RANGE_LOW;
  float in0val = m_codes.range[in0Id] == RANGE_LOW ? 0.1 : 1.0;
  float in1val = m_codes.range[in1Id] == RANGE_LOW ? 0.1 : 1.0;
  float coeff_vga = util::range_to_coeff(m_codes.range[out0Id])/util::range_to_coeff(m_codes.range[in0Id]);
  float coeff_mult = coeff_vga/util::range_to_coeff(m_codes.range[in1Id]);

  float target_vga =  sign*gain*coeff_vga*in0val;
  float target_mult =  sign*coeff_vga*in0val*in1val;
	// preserve dac state because we will clobber it
  // can only calibrate target for vga.
  if(!m_codes.enable){
    print_log("not enabled");
    return true;
  }
  if(!m_codes.vga){
    print_log("not in vga mode");
    return true;
  }
  int cFanId = unitId==unitMulL?0:1;

  int next_slice = (slice_to_int(parentSlice->sliceId) + 1) % 4;
  Dac * ref_dac = parentSlice->parentTile->slices[next_slice].dac;
  Dac * val_dac = parentSlice->dac;
  cutil::calibrate_t calib;
  cutil::initialize(calib);
  // backup state of each component that will be clobbered
  mult_code_t codes_self = m_codes;
  dac_code_t codes_dac = val_dac->m_codes;
  dac_code_t codes_ref = ref_dac->m_codes;
  fanout_code_t codes_fan = parentSlice->fans[cFanId].m_codes;

  // backup connections
  cutil::buffer_mult_conns(calib,this);
  cutil::buffer_fanout_conns(calib,&parentSlice->fans[cFanId]);
  cutil::buffer_dac_conns(calib,ref_dac);
  cutil::buffer_dac_conns(calib,val_dac);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::break_conns(calib);
  
	Connection mult_to_tileout = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection tileout_to_chipout = Connection ( parentSlice->tileOuts[3].out0,
                                               parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );


  mult_to_tileout.setConn();
	tileout_to_chipout.setConn();


  dac_code_t dac_code_0;
  dac_code_t dac_code_1;
  dac_code_t dac_code_0_1;
  dac_code_t dac_ref_targ_vga;
  dac_code_t dac_ref_targ_mult;
  dac_code_1 = cutil::make_one_dac(calib,val_dac);
  dac_code_0 = cutil::make_zero_dac(calib, val_dac);
  if(hiRange){
    dac_ref_targ_vga = cutil::make_val_dac(calib,
                                       ref_dac,
                                       -target_vga);
    //dac_ref_targ_mult = cutil::make_val_dac(calib,
    //                                        ref_dac,
    //                                        target_mult);

  }
  // done computing preset codes
  if(loRange){
    dac_code_0_1 = cutil::make_low_dac(calib, parentSlice->dac);
  }

  bool found_code = false;
  mult_code_t best_code = m_codes;
	m_codes.nmos = 0;
	setAnaIrefNmos ();
  sprintf(FMTBUF, "=== calibrate multiplier ===", m_codes.nmos);
  print_info(FMTBUF);

	do {
    if(found_code){
      break;
    }
    bool succ = true;
    //calibrate bias, no external input
    sprintf(FMTBUF, "nmos=%d", m_codes.nmos);
    print_info(FMTBUF);
    succ &= helper_find_port_cal_out0(val_dac, this,max_error);
    if(succ)
      succ &= helper_find_port_cal_in0(val_dac, this,max_error);
    if(succ)
      succ &= helper_find_port_cal_in1(val_dac, this,dac_code_0,max_error);
    if(succ)
      succ &= helper_find_pmos(val_dac,
                               &parentSlice->fans[cFanId],
                               this,
                               dac_code_1,
                               max_error);
    if(succ)
      succ &= helper_find_gain_cal(gain,
                                   this,
                                   val_dac,
                                   ref_dac,
                                   &parentSlice->tileOuts[3],
                                   hiRange,
                                   hiRange ? 0.0 : target_vga,
                                   dac_ref_targ_vga,
                                   dac_code_0_1,
                                   dac_code_1,
                                   max_error);
    if(succ){
      best_code = m_codes;
      found_code = true;
    }
		parentSlice->fans[cFanId].setEnable(false);
    parentSlice->dac->setEnable(false);

    m_codes.nmos += 1;
    if(m_codes.nmos <= 7){
      setAnaIrefNmos ();
    }
	} while (m_codes.nmos <= 7 && !found_code);
  m_codes = best_code;
  update(m_codes);
	/*teardown*/
	tileout_to_chipout.brkConn();
	mult_to_tileout.brkConn();
  cutil::restore_conns(calib);

  codes_self.nmos = m_codes.nmos;
  codes_self.pmos = m_codes.pmos;
  codes_self.port_cal[in0Id] = m_codes.port_cal[in0Id];
  codes_self.port_cal[in1Id] = m_codes.port_cal[in1Id];
  codes_self.port_cal[out0Id] = m_codes.port_cal[out0Id];
  codes_self.gain_cal = m_codes.gain_cal;

  val_dac->update(codes_dac);
  ref_dac->update(codes_ref);
  parentSlice->fans[unitId==unitMulL?0:1].update(codes_fan);
  update(codes_self);

	return found_code && calib.success;
}

/*
bool Fabric::Chip::Tile::Slice::Multiplier::MultiplierInterface::calibrate () {

  mult_code_t user_self = parentMultiplier->m_codes;
  dac_code_t user_dac = parentFu->parentSlice->dac->m_codes;
	if (ifcId==out0Id || ifcId==in0Id) {
		parentMultiplier->setGainCode((ifcId==in0Id) ? 255 : 128);
	}
	Connection conn = Connection ( parentFu->parentSlice->dac->out0, parentFu->in0 );
	//unsigned char userConstantCode = parentFu->parentSlice->dac->constantCode;
	//bool userInverse = parentFu->parentSlice->dac->out0->inverse;
	if (ifcId==in1Id) {
		parentFu->parentSlice->dac->setConstantCode (0);
		parentFu->parentSlice->dac->out0->setInv (true);
		conn.setConn();
		parentMultiplier->setVga(false);
	}

  float delta = FLT_MAX;
  unsigned char code = 0;
  bool calib_failed;
	//setRange(true, false);
	binarySearch ( 0, FLT_MAX, 63, FLT_MAX,
                 code,
                 delta);
	if ( code <1 || code >62 ) error ("MUL offset failure");
  parentFu->testStab(code,parentMultiplier->m_codes.nmos,delta,calib_failed);
  user_self.port_cal[ifcId] = code;
  parentMultiplier->update(user_self);
  parentFu->parentSlice->dac->update(user_dac);
  return not calib_failed;
}
*/
void Fabric::Chip::Tile::Slice::Multiplier::setAnaIrefNmos () const {
	unsigned char selRow;
	unsigned char selCol;
	unsigned char selLine;
  binsearch::test_iref(m_codes.nmos);
	switch (unitId) {
		case unitMulL: switch (parentSlice->sliceId) {
			case slice0: selRow=1; selCol=2; selLine=1; break;
			case slice1: selRow=0; selCol=3; selLine=0; break;
			case slice2: selRow=1; selCol=2; selLine=0; break;
			case slice3: selRow=0; selCol=3; selLine=1; break;
			default: error ("MUL invalid slice"); break;
		} break;
		case unitMulR: switch (parentSlice->sliceId) {
			case slice0: selRow=1; selCol=2; selLine=3; break;
			case slice1: selRow=0; selCol=3; selLine=2; break;
			case slice2: selRow=1; selCol=2; selLine=2; break;
			case slice3: selRow=0; selCol=3; selLine=3; break;
			default: error ("MUL invalid slice"); break;
		} break;
		default: error ("MUL invalid unitId"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	switch (unitId) {
		case unitMulL: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00000111) + ((m_codes.nmos<<3) & 0b00111000); break;
			case slice1: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			case slice2: cfgTile = (cfgTile & 0b00000111) + ((m_codes.nmos<<3) & 0b00111000); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			default: error ("MUL invalid slice"); break;
		} break;
		case unitMulR: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			case slice1: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			default: error ("MUL invalid slice"); break;
		} break;
		default: error ("MUL invalid unitId"); break;
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

void Fabric::Chip::Tile::Slice::Multiplier::setAnaIrefPmos () const {

	unsigned char setting=7-m_codes.pmos; // because pmos setting has opposite effect on gain
	unsigned char selRow=0;
	unsigned char selCol=4;
	unsigned char selLine;
  binsearch::test_iref(m_codes.pmos);
	switch (unitId) {
		case unitMulL: switch (parentSlice->sliceId) {
			case slice0: selLine=2; break;
			case slice1: selLine=5; break;
			case slice2: selLine=1; break;
			case slice3: selLine=0; break;
			default: error ("MUL invalid slice"); break;
		} break;
		case unitMulR: switch (parentSlice->sliceId) {
			case slice0: selLine=0; break;
			case slice1: selLine=1; break;
			case slice2: selLine=2; break;
			case slice3: selLine=3; break;
			default: error ("MUL invalid slice"); break;
		} break;
		default: error ("MUL invalid unitId"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	switch (unitId) {
		case unitMulL: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00111000) + (setting & 0b00000111); break;
			case slice1: cfgTile = (cfgTile & 0b00111000) + (setting & 0b00000111); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (setting & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00000111) + ((setting<<3) & 0b00111000); break;
			default: error ("MUL invalid slice"); break;
		} break;
		case unitMulR: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00111000) + (setting & 0b00000111); break;
			case slice1: cfgTile = (cfgTile & 0b00000111) + ((setting<<3) & 0b00111000); break;
			case slice2: cfgTile = (cfgTile & 0b00000111) + ((setting<<3) & 0b00111000); break;
			case slice3: cfgTile = (cfgTile & 0b00000111) + ((setting<<3) & 0b00111000); break;
			default: error ("MUL invalid slice"); break;
		} break;
		default: error ("MUL invalid unitId"); break;
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
