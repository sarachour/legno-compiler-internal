#include "HCDC_DEMO_API.h"
#include <float.h>

void Fabric::Chip::Tile::Slice::Dac::setEnable (
	bool enable
) {
	this->enable = enable;
	setParam0 ();
	setParam1 ();
}

void Fabric::Chip::Tile::Slice::Dac::DacOut::setInv (
	bool inverse // whether output is negated
) {
	this->inverse = inverse;
	parentFu->setParam0 ();
}

void Fabric::Chip::Tile::Slice::Dac::setHiRange (
	// default is 2uA mode
	bool hiRange // 20 uA mode
) {
	out0->hiRange = hiRange;
	setEnable (
		enable
	);
}

void Fabric::Chip::Tile::Slice::Dac::setSource (
	bool memory,
	bool external, // digital to analog converter takes input from chip parallel input
	bool lut0, // digital to analog converter takes input from first lookup table
	bool lut1 // digital to analog converter takes input from second lookup table
	// only one of these should be true
) {
	/*record*/
	this->memory = memory;
	switch (parentSlice->sliceId) {
		case slice0: parentSlice->parentTile->slice0DacOverride = memory; break;
		case slice1: parentSlice->parentTile->slice1DacOverride = memory; break;
		case slice2: parentSlice->parentTile->slice2DacOverride = memory; break;
		case slice3: parentSlice->parentTile->slice3DacOverride = memory; break;
	}
	this->external = external;
	if (external) {
		parentSlice->parentTile->setParallelIn ( external );
	}
	this->lut0 = lut0;
	this->lut1 = lut1;

	unsigned char cfgTile = 0b00000000;
	cfgTile += parentSlice->parentTile->slice0DacOverride ? 1<<7 : 0;
	cfgTile += parentSlice->parentTile->slice1DacOverride ? 1<<6 : 0;
	cfgTile += parentSlice->parentTile->slice2DacOverride ? 1<<5 : 0;
	cfgTile += parentSlice->parentTile->slice3DacOverride ? 1<<4 : 0;
	parentSlice->parentTile->controllerHelperTile ( 11, cfgTile );

	setEnable (
		enable
	);
}

void Fabric::Chip::Tile::Slice::Dac::setConstantCode (
	unsigned char constantCode // fixed point representation of desired constant
	// 0 to 255 are valid
) {
	this->constantCode = constantCode;
	setSource ( true, false, false, false );
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

bool Fabric::Chip::Tile::Slice::Dac::setConstant (
	float constant // floating point representation of desired constant
	// -10.0 to 10.0 are valid
) {
	// Serial.print("setConstant ");
	// Serial.println(constant);
	// Serial.flush();

	out0->setInv ( false );
	if (-1.0000001<constant && constant<127./128.) {
		setHiRange ( false );
		setConstantCode ( round(constant*128.0+128.0) );
		return calibrateTarget ( false, constant );
	} else if (-10.0000001<constant && constant<127./12.8) {
		setHiRange ( true );
		setConstantCode ( round((constant/10.0)*128.0+128.0) );
		return calibrateTarget ( true, constant );
	} else {
		error ("DAC constant bias generation must be between -10.0 and 10.0");
		return false;
	}
}

Fabric::Chip::Tile::Slice::Dac::Dac (
	Chip::Tile::Slice * parentSlice
) :
	FunctionUnit(parentSlice, unitDac)
{
	out0 = new DacOut (this);
	tally_dyn_mem <DacOut> ("DacOut");
	setAnaIrefDacNmos ( false, false );
}

/*Set enable, invert, range, clock select*/
void Fabric::Chip::Tile::Slice::Dac::setParam0 () const {
	unsigned char cfgTile = 0;
	cfgTile += enable ? 1<<7 : 0;
	cfgTile += (out0->inverse) ? 1<<6 : 0;
	cfgTile += (out0->hiRange ? dacHi : dacMid) ? 1<<5 : 0;
	cfgTile += (external||memory) ? extDac : ( lut0 ? lutL : lutR )<<0;
	setParamHelper (0, cfgTile);
}

/*Set calDac, input select*/
void Fabric::Chip::Tile::Slice::Dac::setParam1 () const {
	unsigned char calDac = /*out0->hiRange ? hiNegGainCalCode :*/ negGainCalCode; /*gain calibration code*/
	if (calDac<0||63<calDac) error ("calDac out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += calDac<<2;
	cfgTile += (external||memory) ? extDac : ( lut0 ? lutL : lutR )<<0;
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
) {
	return true;
}

bool Fabric::Chip::Tile::Slice::Dac::calibrateTarget (
	bool hiRange, // 20 uA mode
	float constant // floating point representation of desired constant
) {

	// preserve mul state because we will clobber it
	unsigned char userMulPmos = parentSlice->muls[1].anaIrefPmos;
	unsigned char userVgaNmos = parentSlice->muls[1].anaIrefDacNmos;
	unsigned char userVgaCalCode = parentSlice->muls[1].negGainCalCode;
	bool userVga = parentSlice->muls[1].vga;
	unsigned char userVgaGain = parentSlice->muls[1].gainCode;

	bool userOutLo = parentSlice->muls[1].out0->loRange;
	bool userOutHi = parentSlice->muls[1].out0->hiRange;
	unsigned char userOutLoOffsetCode = parentSlice->muls[1].out0->loOffsetCode;
	unsigned char userOutMidOffsetCode = parentSlice->muls[1].out0->midOffsetCode;
	unsigned char userOutHiOffsetCode = parentSlice->muls[1].out0->hiOffsetCode;

	bool userIn0Lo = parentSlice->muls[1].in0->loRange;
	bool userIn0Hi = parentSlice->muls[1].in0->hiRange;
	unsigned char userIn0LoOffsetCode = parentSlice->muls[1].in0->loOffsetCode;
	unsigned char userIn0MidOffsetCode = parentSlice->muls[1].in0->midOffsetCode;
	unsigned char userIn0HiOffsetCode = parentSlice->muls[1].in0->hiOffsetCode;

	bool userIn1Lo = parentSlice->muls[1].in1->loRange;
	bool userIn1Hi = parentSlice->muls[1].in1->hiRange;
	unsigned char userIn1LoOffsetCode = parentSlice->muls[1].in1->loOffsetCode;
	unsigned char userIn1MidOffsetCode = parentSlice->muls[1].in1->midOffsetCode;
	unsigned char userIn1HiOffsetCode = parentSlice->muls[1].in1->hiOffsetCode;

	Connection userConn00 = Connection ( out0, out0->userSourceDest );
	Connection userConn01 = Connection ( parentSlice->muls[1].in0->userSourceDest, parentSlice->muls[1].in0 );
	Connection conn0 = Connection ( out0, parentSlice->muls[1].in0 );

	Connection userConn10 = Connection ( parentSlice->muls[1].out0, parentSlice->muls[1].out0->userSourceDest );
	Connection userConn11 = Connection ( parentSlice->tileOuts[3].in0->userSourceDest, parentSlice->tileOuts[3].in0 );
	Connection conn1 = Connection ( parentSlice->muls[1].out0, parentSlice->tileOuts[3].in0 );

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

	anaIrefDacNmos = 0;
	setAnaIrefDacNmos ( false, false );
	bool biasStable = false;
	while (!biasStable) {
		biasStable = findBiasHelper (
			hiRange ? -constant/10.0 : constant,
			negGainCalCode
		);
	}

	if (hiRange) {
		conn0.brkConn();
		if (userConn00.destIfc) userConn00.setConn();
		if (userConn01.sourceIfc) userConn01.setConn();

		parentSlice->muls[1].anaIrefPmos = userMulPmos;
		parentSlice->muls[1].setAnaIrefPmos();
		parentSlice->muls[1].anaIrefDacNmos = userVgaNmos;
		parentSlice->muls[1].setAnaIrefDacNmos( false, false );
		parentSlice->muls[1].negGainCalCode = userVgaCalCode;
		parentSlice->muls[1].setGainCode( userVgaGain );
		parentSlice->muls[1].setVga( userVga );

		parentSlice->muls[1].out0->loOffsetCode = userOutLoOffsetCode;
		parentSlice->muls[1].out0->midOffsetCode = userOutMidOffsetCode;
		parentSlice->muls[1].out0->hiOffsetCode = userOutHiOffsetCode;
		parentSlice->muls[1].out0->setRange( userOutLo, userOutHi );

		parentSlice->muls[1].in0->loOffsetCode = userIn0LoOffsetCode;
		parentSlice->muls[1].in0->midOffsetCode = userIn0MidOffsetCode;
		parentSlice->muls[1].in0->hiOffsetCode = userIn0HiOffsetCode;
		parentSlice->muls[1].in0->setRange( userIn0Lo, userIn0Hi );

		parentSlice->muls[1].in1->loOffsetCode = userIn1LoOffsetCode;
		parentSlice->muls[1].in1->midOffsetCode = userIn1MidOffsetCode;
		parentSlice->muls[1].in1->hiOffsetCode = userIn1HiOffsetCode;
		parentSlice->muls[1].in1->setRange( userIn1Lo, userIn1Hi );

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

	return biasStable;
}

bool Fabric::Chip::Tile::Slice::Dac::setAnaIrefDacNmos (
	bool decrement,
	bool increment
) {
	if (!setAnaIrefDacNmosHelper (decrement, increment)) return false;

	unsigned char selRow;
	unsigned char selCol=2;
	unsigned char selLine;
	switch (parentSlice->sliceId) {
		case slice0: selRow=0; selLine=3; break;
		case slice1: selRow=1; selLine=0; break;
		case slice2: selRow=0; selLine=2; break;
		case slice3: selRow=1; selLine=1; break;
		default: error ("DAC invalid slice"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111);

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

	return true;
}

// binary search so dac scale matches adc scale
bool Fabric::Chip::Tile::Slice::Dac::findBiasAdc (
	unsigned char & gainCalCode
) {
	// Serial.println("Dac gain calibration");

	setHiRange(true);
	setConstantCode(2);
	ChipAdc * adc;
	switch (parentSlice->sliceId) {
		case slice0: adc=parentSlice->adc; break;
		case slice1: adc=parentSlice->parentTile->slices[0].adc; break;
		case slice2: adc=parentSlice->adc; break;
		case slice3: adc=parentSlice->parentTile->slices[2].adc; break;
	}
	Connection conn = Connection ( out0, adc->in0 );
	conn.setConn();

	bool biasStable = false;
	while (!biasStable) {
		biasStable = findBiasHelperAdc (gainCalCode);
	}

	setEnable (false);
	conn.brkConn();
	adc->setEnable (false);

	// switch to finding full scale
	setConstantCode(0);
	Connection conn0 = Connection ( out0, parentSlice->tileOuts[3].in0 );
	conn0.setConn();
	Connection conn1 = Connection ( parentSlice->tileOuts[3].out0, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
	conn1.setConn();
	parentSlice->parentTile->parentChip->parentFabric->cfgCommit();

	float midNegTarget = binarySearchMeas();
	Serial.print("midNegTarget = ");
	Serial.println(midNegTarget);

	conn0.brkConn();
	conn1.brkConn();
	setEnable(false);

	return biasStable;
}

bool Fabric::Chip::Tile::Slice::Dac::findBiasHelperAdc (
	unsigned char & code
) {
	binarySearchAdc ( 0, FLT_MAX, 63, FLT_MAX, code );

	// Serial.print("\ntile row ");
	// Serial.print(parentSlice->parentTile->tileRowId);
	// Serial.print(" tile col ");
	// Serial.print(parentSlice->parentTile->tileColId);
	// Serial.print(" slice ");
	// Serial.print(parentSlice->sliceId);
	// Serial.print(" unit ");
	// Serial.print(unitId);
	// Serial.print(" code ");
	// Serial.println(code);

	if (code==0 || code==1) {
		setAnaIrefDacNmos(true, false);
		return false;
	} else if (code==63 || code==62) {
		setAnaIrefDacNmos(false, true);
		return false;
	} else {
		return true;
	}
}

// binary search so dac scale matches adc scale
void Fabric::Chip::Tile::Slice::Dac::binarySearchAdc (
	unsigned char minGainCalCode,
	float minBest,
	unsigned char maxGainCalCode,
	float maxBest,
	unsigned char & finalGainCalCode
) {
	if (binarySearchAvg (minGainCalCode, minBest, maxGainCalCode, maxBest, finalGainCalCode)) return;

	setParam1 ();
	parentSlice->parentTile->parentChip->parentFabric->cfgCommit();

	ChipAdc * adc;
	switch (parentSlice->sliceId) {
		case slice0: adc=parentSlice->adc; break;
		case slice1: adc=parentSlice->parentTile->slices[0].adc; break;
		case slice2: adc=parentSlice->adc; break;
		case slice3: adc=parentSlice->parentTile->slices[2].adc; break;
	}

	unsigned char adcRead = adc->getData();
	Serial.print("adcRead = ");
	Serial.println(adcRead);

	float target = 2.0;
	if ( adcRead < target ) {
		return binarySearchAdc (minGainCalCode, minBest, finalGainCalCode, fabs(adcRead-target), finalGainCalCode);
	} else {
		return binarySearchAdc (finalGainCalCode, fabs(adcRead-target), maxGainCalCode, maxBest, finalGainCalCode);
	}

}
