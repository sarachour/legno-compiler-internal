#include "AnalogLib.h"
#include <float.h>
#include "assert.h"

void Fabric::Chip::Tile::Slice::Dac::setEnable (
	bool enable
)
{
	m_codes.enable = enable;
	setParam0 ();
	setParam1 ();
}

void Fabric::Chip::Tile::Slice::Dac::DacOut::setInv (
	bool inverse // whether output is negated
) {
	Fabric::Chip::Tile::Slice::Dac* dac = this->parentFu;
  dac->m_codes.inv = inverse;
	parentFu->setParam0();
}

void Fabric::Chip::Tile::Slice::Dac::setRange (
	// default is 2uA mode
	range_t range // 20 uA mode
) {
  assert(range != RANGE_LOW);
  m_codes.range = range;
	setEnable (m_codes.enable);
}

void Fabric::Chip::Tile::Slice::Dac::setSource (dac_source_t src) {
	/*record*/
  m_codes.source = src;
  bool memory = (src == DSRC_MEM);
  bool external = (src == DSRC_EXTERN);
	switch (parentSlice->sliceId) {
		case slice0: parentSlice->parentTile->slice0DacOverride = memory; break;
		case slice1: parentSlice->parentTile->slice1DacOverride = memory; break;
		case slice2: parentSlice->parentTile->slice2DacOverride = memory; break;
		case slice3: parentSlice->parentTile->slice3DacOverride = memory; break;
	}
	if (external) {
		parentSlice->parentTile->setParallelIn ( external );
	}

	unsigned char cfgTile = 0b00000000;
	cfgTile += parentSlice->parentTile->slice0DacOverride ? 1<<7 : 0;
	cfgTile += parentSlice->parentTile->slice1DacOverride ? 1<<6 : 0;
	cfgTile += parentSlice->parentTile->slice2DacOverride ? 1<<5 : 0;
	cfgTile += parentSlice->parentTile->slice3DacOverride ? 1<<4 : 0;
	parentSlice->parentTile->controllerHelperTile ( 11, cfgTile );

	setEnable (
		m_codes.enable
	);
}

void Fabric::Chip::Tile::Slice::Dac::setConstantCode (
	unsigned char constantCode // fixed point representation of desired constant
	// 0 to 255 are valid
) {
  m_codes.const_code = constantCode;
  m_codes.const_val = (constantCode - 128)/128.0;
  setSource(DSRC_MEM);
	parentSlice->parentTile->parentChip->parentFabric->cfgCommit();
	unsigned char selLine = 0;
	switch (parentSlice->sliceId) {
		case slice0: selLine = 7; break;
		case slice1: selLine = 8; break;
		case slice2: selLine = 9; break;
		case slice3: selLine = 10; break;
	}
	unsigned char cfgTile = endian (constantCode);
	parentSlice->parentTile->controllerHelperTile ( selLine, cfgTile );
}

bool Fabric::Chip::Tile::Slice::Dac::setConstant(float constant){
  if(-1.0000001 < constant && constant< 127.0/128.0){
    setConstantCode(round(constant*128.0+128.0));
    m_codes.const_val = constant;
    return true;
  }
  else{
    return false;
  }
}

Fabric::Chip::Tile::Slice::Dac::Dac (
	Chip::Tile::Slice * parentSlice
) :
	FunctionUnit(parentSlice, unitDac)
{
  m_codes.inv = false;
  m_codes.range = RANGE_MED;
  m_codes.pmos = 0;
  m_codes.nmos = 0;
  m_codes.gain_cal = 0;
  m_codes.const_code = 128;
  m_codes.const_val = 0.0;
  m_codes.enable = false;
	out0 = new DacOut (this);
	tally_dyn_mem <DacOut> ("DacOut");
	setAnaIrefNmos ();
}

/*Set enable, invert, range, clock select*/
void Fabric::Chip::Tile::Slice::Dac::setParam0 () const {
	unsigned char cfgTile = 0;
  bool external = (m_codes.source == DSRC_EXTERN or m_codes.source == DSRC_MEM);
  bool lut0 = (m_codes.source == DSRC_LUT0);
  bool is_hiRange = (m_codes.range == RANGE_HIGH);
  bool is_inverse = (m_codes.inv);
	cfgTile += m_codes.enable ? 1<<7 : 0;
	cfgTile += (is_inverse) ? 1<<6 : 0;
	cfgTile += (is_hiRange ? dacHi : dacMid) ? 1<<5 : 0;
	cfgTile += (external) ? extDac : ( lut0 ? lutL : lutR )<<0;
	setParamHelper (0, cfgTile);
}

/*Set calDac, input select*/
void Fabric::Chip::Tile::Slice::Dac::setParam1 () const {
	unsigned char calDac =  m_codes.gain_cal;
	if (calDac<0||63<calDac) error ("calDac out of bounds");
	unsigned char cfgTile = 0;
  bool external = (m_codes.source == DSRC_EXTERN or m_codes.source == DSRC_MEM);
  bool lut0 = (m_codes.source == DSRC_LUT0);
	cfgTile += calDac<<2;
  cfgTile += (external) ? extDac : ( lut0 ? lutL : lutR )<<0;
	setParamHelper (1, cfgTile);
}

/*Helper function*/
void Fabric::Chip::Tile::Slice::Dac::setParamHelper (
	unsigned char selLine,
	unsigned char cfgTile
) const {
	if (selLine<0||1<selLine) error ("selLine out of bounds");

	/*DETERMINE SEL_COL*/
	unsigned char selCol;
	switch (parentSlice->sliceId) {
		case slice0: selCol = 6; break;
		case slice1: selCol = 3; break;
		case slice2: selCol = 7; break;
		case slice3: selCol = 4; break;
		default: error ("DAC invalid slice"); break;
	}

	Chip::Vector vec = Vector (
		*this,
		6,
		selCol,
		selLine,
		endian (cfgTile)
	);

	parentSlice->parentTile->parentChip->cacheVec (
		vec
	);
}

bool Fabric::Chip::Tile::Slice::Dac::calibrate (
)
{
	return true;
}

bool Fabric::Chip::Tile::Slice::Dac::calibrateTarget ()
{
  //setConstantCode(round(constant*128.0+128.0));
  if(!m_codes.enable){
    Serial.println("AC:>[msg] DAC not enabled");
    return true;
  }
  float constant = m_codes.const_val;
  bool hiRange = (m_codes.range == RANGE_HIGH);
  Serial.print("AC:>[msg] DAC ");
  Serial.print(m_codes.const_val);
  Serial.print(" ");
  Serial.print(m_codes.const_code);
  Serial.print(" ");
  Serial.println(hiRange);

  mult_code_t user_mul1 = parentSlice->muls[1].m_codes;
	// preserve mul state because we will clobber it
	//unsigned char userMulPmos = parentSlice->muls[1].anaIrefPmos;
	//unsigned char userVgaNmos = parentSlice->muls[1].anaIrefDacNmos;
	//unsigned char userVgaCalCode = parentSlice->muls[1].negGainCalCode;
	//bool userVga = parentSlice->muls[1].vga;
	//unsigned char userVgaGain = parentSlice->muls[1].gainCode;

	//bool userOutLo = parentSlice->muls[1].out0->loRange;
	//bool userOutHi = parentSlice->muls[1].out0->hiRange;
	//unsigned char userOutLoOffsetCode = parentSlice->muls[1].out0->loOffetCode;
	//unsigned char userOutMidOffsetCode = parentSlice->muls[1].out0->midOffsetCode;
	//unsigned char userOutHiOffsetCode = parentSlice->muls[1].out0->hiOffsetCode;

	//bool userIn0Lo = parentSlice->muls[1].in0->loRange;
	//bool userIn0Hi = parentSlice->muls[1].in0->hiRange;
	//unsigned char userIn0LoOffsetCode = parentSlice->muls[1].in0->loOffsetCode;
	//unsigned char userIn0MidOffsetCode = parentSlice->muls[1].in0->midOffsetCode;
	//unsigned char userIn0HiOffsetCode = parentSlice->muls[1].in0->hiOffsetCode;

	//bool userIn1Lo = parentSlice->muls[1].in1->loRange;
	//bool userIn1Hi = parentSlice->muls[1].in1->hiRange;
	//unsigned char userIn1LoOffsetCode = parentSlice->muls[1].in1->loOffsetCode;
	//unsigned char userIn1MidOffsetCode = parentSlice->muls[1].in1->midOffsetCode;
	//unsigned char userIn1HiOffsetCode = parentSlice->muls[1].in1->hiOffsetCode;

	Connection userConn00 = Connection ( out0, out0->userSourceDest );
	Connection userConn01 = Connection ( parentSlice->muls[1].in0->userSourceDest,
                                       parentSlice->muls[1].in0 );
	Connection conn0 = Connection ( out0, parentSlice->muls[1].in0 );

	Connection userConn10 = Connection ( parentSlice->muls[1].out0,
                                       parentSlice->muls[1].out0->userSourceDest );
	Connection userConn11 = Connection ( parentSlice->tileOuts[3].in0->userSourceDest,
                                       parentSlice->tileOuts[3].in0 );
	Connection conn1 = Connection ( parentSlice->muls[1].out0,
                                  parentSlice->tileOuts[3].in0 );

	Connection conn2 = Connection ( out0, parentSlice->tileOuts[3].in0 );

	if (hiRange) {
		if (userConn01.sourceIfc) userConn01.brkConn();
		conn0.setConn();
		parentSlice->muls[1].setGain(-0.1);
		if (userConn11.sourceIfc) userConn11.brkConn();
		conn1.setConn();
	} else {
		if (userConn11.sourceIfc) userConn11.brkConn();
		conn2.setConn();
	}

	Connection userConn30 = Connection ( parentSlice->tileOuts[3].out0, parentSlice->tileOuts[3].out0->userSourceDest );
	Connection userConn31 = Connection ( parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0->userSourceDest, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
	if (userConn31.sourceIfc) userConn31.brkConn();
	Connection conn3 = Connection ( parentSlice->tileOuts[3].out0, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
	conn3.setConn();

	// Serial.println("Dac gain calibration");
	// Serial.flush();

	m_codes.nmos = 0;
	setAnaIrefNmos ();
  bool succ = binsearch::find_bias_and_nmos(
                       this,
                       hiRange ? -constant : constant,
                       m_codes.gain_cal,
                       m_codes.nmos,
                       MEAS_CHIP_OUTPUT,
                       false);
	if (hiRange) {
		conn0.brkConn();
		if (userConn00.destIfc) userConn00.setConn();
		if (userConn01.sourceIfc) userConn01.setConn();

    parentSlice->muls[1].update(user_mul1);
		//parentSlice->muls[1].anaIrefPmos = userMulPmos;
		//parentSlice->muls[1].setAnaIrefPmos();
		//parentSlice->muls[1].anaIrefDacNmos = userVgaNmos;
		//parentSlice->muls[1].setAnaIrefDacNmos();
		//parentSlice->muls[1].negGainCalCode = userVgaCalCode;
		//parentSlice->muls[1].setGainCode( userVgaGain );
		//parentSlice->muls[1].setVga( userVga );

		//parentSlice->muls[1].out0->loOffsetCode = userOutLoOffsetCode;
		//parentSlice->muls[1].out0->midOffsetCode = userOutMidOffsetCode;
		//parentSlice->muls[1].out0->hiOffsetCode = userOutHiOffsetCode;
		//parentSlice->muls[1].out0->setRange( userOutLo, userOutHi );

		//parentSlice->muls[1].in0->loOffsetCode = userIn0LoOffsetCode;
		//parentSlice->muls[1].in0->midOffsetCode = userIn0MidOffsetCode;
		//parentSlice->muls[1].in0->hiOffsetCode = userIn0HiOffsetCode;
		//parentSlice->muls[1].in0->setRange( userIn0Lo, userIn0Hi );

		//parentSlice->muls[1].in1->loOffsetCode = userIn1LoOffsetCode;
		//parentSlice->muls[1].in1->midOffsetCode = userIn1MidOffsetCode;
		//parentSlice->muls[1].in1->hiOffsetCode = userIn1HiOffsetCode;
		//parentSlice->muls[1].in1->setRange( userIn1Lo, userIn1Hi );

		conn1.brkConn();
		if (userConn10.destIfc) userConn10.setConn();
		if (userConn11.sourceIfc) userConn11.setConn();
	} else {
		conn2.brkConn();
		if (userConn00.destIfc) userConn00.setConn();
		if (userConn11.sourceIfc) userConn11.setConn();
	}

	conn3.brkConn();
	if (userConn30.destIfc) userConn30.setConn();
	if (userConn31.sourceIfc) userConn31.setConn();

	return succ;
}

void Fabric::Chip::Tile::Slice::Dac::setAnaIrefNmos () const {
	unsigned char selRow;
	unsigned char selCol=2;
	unsigned char selLine;
  binsearch::test_iref(m_codes.nmos);
	switch (parentSlice->sliceId) {
		case slice0: selRow=0; selLine=3; break;
		case slice1: selRow=1; selLine=0; break;
		case slice2: selRow=0; selLine=2; break;
		case slice3: selRow=1; selLine=1; break;
		default: error ("DAC invalid slice"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111);

	Chip::Vector vec = Vector (
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
