#include "AnalogLib.h"
#include "fu.h"
#include <float.h>

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

mulRange range_to_mulRange(range_t rng){
  switch(rng){
  case RANGE_HIGH: return mulHi;
  case RANGE_LOW: return mulLo;
  case RANGE_MED: return mulMid;
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

bool Fabric::Chip::Tile::Slice::Multiplier::calibrate () {
	setGain(-1.0);
  calibrateTarget();
	setVga(false);
	return true;
}

bool Fabric::Chip::Tile::Slice::Multiplier::calibrateTarget () {
  float gain = m_codes.gain_val;
  bool hiRange = m_codes.range[out0Id] == RANGE_HIGH;
	// preserve dac state because we will clobber it
  // can only calibrate target for vga.
  if(!m_codes.vga or !m_codes.enable){
    return true;
  }
  dac_code_t codes_dac = parentSlice->dac->m_codes;
  mult_code_t codes_mul = parentSlice->muls[unitId==unitMulL?1:0].m_codes;
  mult_code_t codes_self = m_codes;
  fanout_code_t codes_fan = parentSlice->fans[unitId==unitMulL?0:1].m_codes;

  parentSlice->dac->setConstant(-1.0);
	if (hiRange) parentSlice->muls[unitId==unitMulL?1:0].setGain(-0.1);

	Connection userConn40 = Connection ( parentSlice->dac->out0, parentSlice->dac->out0->userSourceDest );
	Connection userConn41 = Connection ( parentSlice->fans[unitId==unitMulL?0:1].in0->userSourceDest, parentSlice->fans[unitId==unitMulL?0:1].in0 );
	if (userConn41.sourceIfc) userConn41.brkConn();
	Connection conn4 = Connection ( parentSlice->dac->out0, parentSlice->fans[unitId==unitMulL?0:1].in0 );

	Connection userConn50 = Connection ( parentSlice->fans[unitId==unitMulL?0:1].out0, parentSlice->fans[unitId==unitMulL?0:1].out0->userSourceDest );
	Connection userConn51 = Connection ( in0->userSourceDest, in0 );
	if (userConn51.sourceIfc) userConn51.brkConn();
	Connection conn5 = Connection ( parentSlice->fans[unitId==unitMulL?0:1].out0, in0 );

	Connection userConn60 = Connection ( parentSlice->fans[unitId==unitMulL?0:1].out1, parentSlice->fans[unitId==unitMulL?0:1].out1->userSourceDest );
	Connection userConn61 = Connection ( in1->userSourceDest, in1 );
	if (userConn61.sourceIfc) userConn61.brkConn();
	Connection conn6 = Connection ( parentSlice->fans[unitId==unitMulL?0:1].out1, in1 );

	// output side
	Connection userConn00 = Connection ( out0, out0->userSourceDest );
	Connection userConn01 = Connection ( parentSlice->muls[unitId==unitMulL?1:0].in0->userSourceDest, parentSlice->muls[unitId==unitMulL?1:0].in0 );
	if (hiRange && userConn01.sourceIfc) userConn01.brkConn();
	Connection conn0 = Connection ( out0, parentSlice->muls[unitId==unitMulL?1:0].in0 );

	Connection userConn10 = Connection ( parentSlice->muls[unitId==unitMulL?1:0].out0, parentSlice->muls[unitId==unitMulL?1:0].out0->userSourceDest );
	Connection userConn11 = Connection ( parentSlice->tileOuts[3].in0->userSourceDest, parentSlice->tileOuts[3].in0 );
	// if (hiRange && userConn11.sourceIfc) userConn11.brkConn();
	Connection conn1 = Connection ( parentSlice->muls[unitId==unitMulL?1:0].out0, parentSlice->tileOuts[3].in0 );

	Connection conn2 = Connection ( out0, parentSlice->tileOuts[3].in0 );
	if (userConn11.sourceIfc) userConn11.brkConn();
	conn2.setConn();

	Connection userConn30 = Connection ( parentSlice->tileOuts[3].out0, parentSlice->tileOuts[3].out0->userSourceDest );
	Connection userConn31 = Connection ( parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0->userSourceDest, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
	if (userConn31.sourceIfc) userConn31.brkConn();
	Connection conn3 = Connection ( parentSlice->tileOuts[3].out0, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
	conn3.setConn();

	unsigned char ttl = 64;
  bool new_search = true;
  bool calib_failed = true;

	m_codes.nmos = 0;
	setAnaIrefNmos ();
	do {
    float errors[4];
    unsigned char codes[4];
    float dummy;
    //in0Id
    setGainCode(255);
    setVga(true);
    binsearch::find_bias(this, 0.0,
                         m_codes.port_cal[in0Id],
                         errors[0],
                         MEAS_CHIP_OUTPUT,
                         false);
    codes[0] = m_codes.port_cal[in0Id];

    //out0Id
    setGainCode(128);
    setVga(true);
    binsearch::find_bias(this, 0.0,
                         m_codes.port_cal[out0Id],
                         errors[1],
                         MEAS_CHIP_OUTPUT,
                         false);
    codes[1] = m_codes.port_cal[out0Id];
    //in1id
    Connection conn_in1 = Connection ( parentSlice->dac->out0, in0);
    setVga(false);
    parentSlice->dac->setConstantCode(0);
    parentSlice->dac->out0->setInv(true);
    conn_in1.setConn();
    binsearch::find_bias(this, 0.0,
                         m_codes.port_cal[in1Id],
                         errors[2],
                         MEAS_CHIP_OUTPUT,
                         false);
    codes[2] = m_codes.port_cal[in1Id];
    conn_in1.brkConn();

    // Serial.println("\nMultiplier gain calibration");
    range_t outrng = m_codes.range[out0Id];
    range_t in0rng = m_codes.range[in0Id];
    range_t in1rng = m_codes.range[in1Id];

		conn4.setConn();
		conn5.setConn();
		conn6.setConn();

    out0->setRange(RANGE_MED);
    in0->setRange(RANGE_MED);
    in0->setRange(RANGE_MED);
    setVga(false);
    binsearch::find_pmos(this,1.0,
                         m_codes.pmos,
                         dummy,
                         MEAS_CHIP_OUTPUT,
                         false);
    // Serial.print("anaIrefPmos = ");
    // Serial.println(anaIrefPmos);
    out0->setRange(outrng);
    in0->setRange(in0rng);
    in1->setRange(in1rng);

    if (hiRange) {
      conn0.setConn();
      conn1.setConn();
      // parentSlice->dac->setConstant(-0.1);
    }

    /*calibrate VGA gain to negative full scale*/
    // Serial.print("\nVGA gain calibration ");
    // Serial.println(gain);
    setVga(true);
    binsearch::find_bias(this,
                         hiRange ? gain : -gain,
                         m_codes.gain_cal,
                         errors[3],
                         MEAS_CHIP_OUTPUT,
                         false);
    codes[3] = m_codes.gain_cal;

    binsearch::multi_test_stab_and_update_nmos(this,
                                               codes,errors,4,
                                               m_codes.nmos,
                                               new_search,
                                               calib_failed);
    if (hiRange) {
      conn2.setConn();
    }

		conn4.brkConn();
		conn5.brkConn();
		conn6.brkConn();
		parentSlice->fans[unitId==unitMulL?0:1].setEnable(false);

		ttl--;

	} while (new_search && ttl);

  codes_self.nmos = m_codes.nmos;
  codes_self.pmos = m_codes.pmos;
  codes_self.port_cal[in0Id] = m_codes.port_cal[in0Id];
  codes_self.port_cal[in1Id] = m_codes.port_cal[in1Id];
  codes_self.port_cal[out0Id] = m_codes.port_cal[out0Id];
  codes_self.gain_cal = m_codes.gain_cal;

	/*teardown*/
	if (hiRange) {
		conn0.brkConn();
		if (userConn00.destIfc) userConn00.setConn();
		if (userConn01.sourceIfc) userConn01.setConn();

		parentSlice->muls[unitId==unitMulL?1:0].update(codes_mul);

		conn1.brkConn();
		if (userConn10.destIfc) userConn10.setConn();
		if (userConn11.sourceIfc) userConn11.setConn();
	}

	conn3.brkConn();
	if (userConn31.sourceIfc) userConn31.setConn();
	if (userConn30.destIfc) userConn30.setConn();
	conn2.brkConn();
	if (userConn11.sourceIfc) userConn11.setConn();
	if (userConn00.destIfc) userConn00.setConn();

	if (userConn61.sourceIfc) userConn61.setConn();
	if (userConn60.destIfc) userConn60.setConn();
	if (userConn51.sourceIfc) userConn51.setConn();
	if (userConn50.destIfc) userConn50.setConn();
	if (userConn41.sourceIfc) userConn41.setConn();
	if (userConn40.destIfc) userConn40.setConn();

  parentSlice->dac->update(codes_dac);
  parentSlice->fans[unitId==unitMulL?0:1].update(codes_fan);
  parentSlice->muls[unitId==unitMulL?1:0].update(codes_mul);
  update(codes_self);

	return !calib_failed;
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
