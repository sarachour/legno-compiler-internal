#include "HCDC_DEMO_API.h"
#include <float.h>

void Fabric::Chip::Tile::Slice::Multiplier::setEnable (
	bool enable
) {
	this->enable = enable;
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
	this->vga = vga;
	setParam1 ();
}

void Fabric::Chip::Tile::Slice::Multiplier::setGainCode (
	unsigned char gainCode // fixed point representation of desired gain
) {
	// Serial.println("setGainCode");
	// Serial.println(gainCode);
	setVga (true);
	this->gainCode = gainCode;
	setParam2 ();
}

bool Fabric::Chip::Tile::Slice::Multiplier::setGainDirect(float gain, bool hiRange,bool setBias){
  if(-1.0000001 < gain && gain < 127.0/128.0){
    setGainCode(gain*128.0+128.0);
    if(setBias){
      return calibrateTarget(hiRange, gain);
    }
  }
  else{
    return false;
  }
}

bool Fabric::Chip::Tile::Slice::Multiplier::setGain (
	float gain // floating point representation of desired gain
	// -100.0 to 100.0 are valid
) {
	// Serial.print("setGain ");
	// Serial.println(gain);
	// Serial.flush();

	if (-.010000001<gain && gain<1.27/128.) { // enable x0.01 gain using input & output attenuation
		out0->setRange (
			true, // 0.2uA mode
			false // 20 uA mode
		);
		in0->setRange (
			false, // 0.2uA mode
			true // 20 uA mode
		);
		setGainCode ( (gain*100.0)*128.0 + 128.0 );
		return calibrateTarget (false, gain);
	} else if (-.10000001<gain && gain<12.7/128.) { // enable x0.1 gain using input attenuation
		out0->setRange (
			false, // 0.2uA mode
			false // 20 uA mode
		);
		in0->setRange (
			false, // 0.2uA mode
			true // 20 uA mode
		);
		setGainCode ( round((gain*10.0)*128.0 + 128.0) );
		return calibrateTarget (false, gain);
	} else if (-1.0000001<gain && gain<127./128.) { // regular mode
		out0->setRange (
			false, // 0.2uA mode
			false // 20 uA mode
		);
		in0->setRange (
			false, // 0.2uA mode
			false // 20 uA mode
		);
		setGainCode ( round(gain*128.0 + 128.0) );
		return calibrateTarget (false, gain);
	} else if (-10.0000001<gain && gain<127./12.8) { // enable x10 gain using output gain
		out0->setRange (
			false, // 0.2uA mode
			true // 20 uA mode
		);
		in0->setRange (
			false, // 0.2uA mode
			false // 20 uA mode
		);
		setGainCode ( round((gain/10.0)*128.0 + 128.0) );
		return calibrateTarget (true, gain);
	} else if (-100.0000001<gain && gain<127./1.28) { // enable x100 gain using both input & output gain
		out0->setRange (
			false, // 0.2uA mode
			true // 20 uA mode
		);
		in0->setRange ( // least reliable
			true, // 0.2uA mode
			false // 20 uA mode
		);
		setGainCode ( (gain/100.0)*128.0 + 128.0 );
		return calibrateTarget (true, gain);
	} else {
		error ("VGA gain must be between -100.0 and 100.0");
		return false;
	};
}

void Fabric::Chip::Tile::Slice::Multiplier::MultiplierInterface::setRange (
	bool loRange, // 0.2uA mode
	bool hiRange // 20 uA mode
	// default is 2uA mode
	// this setting should match the unit that gives the input to the multiplier
) {
	if (loRange&&hiRange) error ("MUL low and high range cannot be selected at the same time");
	this->loRange = loRange;
	this->hiRange = hiRange;
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
	setAnaIrefDacNmos( false, false );
	setAnaIrefPmos();
}

/*Set enable, input 1 range, input 2 range, output range*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam0 () const {
	unsigned char cfgTile = 0;
	cfgTile += enable ? 1<<7 : 0;
	cfgTile += (in0->loRange ? mulLo : (in0->hiRange ? mulHi : mulMid))<<4;
	cfgTile += (in1->loRange ? mulLo : (in1->hiRange ? mulHi : mulMid))<<2;
	cfgTile += (out0->loRange ? mulLo : (out0->hiRange ? mulHi : mulMid))<<0;
	setParamHelper (0, cfgTile);
}

/*Set calDac, enable variable gain amplifer mode*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam1 () const {
	if (negGainCalCode<0||63<negGainCalCode) error ("midNegGainCode out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += negGainCalCode<<2;
	cfgTile += vga ? 1<<1 : 0;
	setParamHelper (1, cfgTile);
}

/*Set gain if VGA mode*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam2 () const {
	if (gainCode<0||255<gainCode) error ("gain out of bounds");
	setParamHelper (2, gainCode);
}

/*Set calOutOs*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam3 () const {
	unsigned char calOutOs = out0->loRange ? out0->loOffsetCode : (out0->hiRange ? out0->hiOffsetCode : out0->midOffsetCode);
	if (calOutOs<0||63<calOutOs) error ("calOutOs out of bounds");
	unsigned char cfgTile = calOutOs<<2;
	setParamHelper (3, cfgTile);
}

/*Set calInOs1*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam4 () const {
	unsigned char calInOs1 = in0->loRange ? in0->loOffsetCode : (in0->hiRange ? in0->hiOffsetCode : in0->midOffsetCode);
	if (calInOs1<0||63<calInOs1) error ("calInOs1 out of bounds");
	unsigned char cfgTile = calInOs1<<2;
	setParamHelper (4, cfgTile);
}

/*Set calInOs2*/
void Fabric::Chip::Tile::Slice::Multiplier::setParam5 () const {
	unsigned char calInOs2 = in1->loRange ? in1->loOffsetCode : (in1->hiRange ? in1->hiOffsetCode : in1->midOffsetCode);
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
	setVga(false);
	return true;
}

bool Fabric::Chip::Tile::Slice::Multiplier::calibrateTarget (
	bool hiRange,
	float gain
) {

	// preserve dac state because we will clobber it
	unsigned char userDacNmos = parentSlice->dac->anaIrefDacNmos;
	unsigned char userDacCalCode = parentSlice->dac->negGainCalCode;
	unsigned char userDacConst = parentSlice->dac->constantCode;
	bool userDacInv = parentSlice->dac->out0->inverse;
	bool userDacHi = parentSlice->dac->out0->hiRange;
	parentSlice->dac->setConstant(-1.0);

	// preserve mul state because we will clobber it
	unsigned char userMulPmos = parentSlice->muls[unitId==unitMulL?1:0].anaIrefPmos;
	unsigned char userVgaNmos = parentSlice->muls[unitId==unitMulL?1:0].anaIrefDacNmos;
	unsigned char userVgaCalCode = parentSlice->muls[unitId==unitMulL?1:0].negGainCalCode;
	bool userVga = parentSlice->muls[unitId==unitMulL?1:0].vga;
	unsigned char userVgaGain = parentSlice->muls[unitId==unitMulL?1:0].gainCode;

	bool userOutLo = parentSlice->muls[unitId==unitMulL?1:0].out0->loRange;
	bool userOutHi = parentSlice->muls[unitId==unitMulL?1:0].out0->hiRange;
	unsigned char userOutLoOffsetCode = parentSlice->muls[unitId==unitMulL?1:0].out0->loOffsetCode;
	unsigned char userOutMidOffsetCode = parentSlice->muls[unitId==unitMulL?1:0].out0->midOffsetCode;
	unsigned char userOutHiOffsetCode = parentSlice->muls[unitId==unitMulL?1:0].out0->hiOffsetCode;

	bool userIn0Lo = parentSlice->muls[unitId==unitMulL?1:0].in0->loRange;
	bool userIn0Hi = parentSlice->muls[unitId==unitMulL?1:0].in0->hiRange;
	unsigned char userIn0LoOffsetCode = parentSlice->muls[unitId==unitMulL?1:0].in0->loOffsetCode;
	unsigned char userIn0MidOffsetCode = parentSlice->muls[unitId==unitMulL?1:0].in0->midOffsetCode;
	unsigned char userIn0HiOffsetCode = parentSlice->muls[unitId==unitMulL?1:0].in0->hiOffsetCode;

	bool userIn1Lo = parentSlice->muls[unitId==unitMulL?1:0].in1->loRange;
	bool userIn1Hi = parentSlice->muls[unitId==unitMulL?1:0].in1->hiRange;
	unsigned char userIn1LoOffsetCode = parentSlice->muls[unitId==unitMulL?1:0].in1->loOffsetCode;
	unsigned char userIn1MidOffsetCode = parentSlice->muls[unitId==unitMulL?1:0].in1->midOffsetCode;
	unsigned char userIn1HiOffsetCode = parentSlice->muls[unitId==unitMulL?1:0].in1->hiOffsetCode;
	if (hiRange) parentSlice->muls[unitId==unitMulL?1:0].setGain(-0.1);

	// preserve dac and fanout connections because we will clobber them
	// input side
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

	anaIrefDacNmos = 0;
	setAnaIrefDacNmos ( false, false );
	bool biasStable;
	unsigned char ttl = 64;

	do {

		// multiplier offset codes are mildly sensitive to bias code changes
		// Serial.println("\nCalibrate output");
		out0->calibrate();
		// Serial.println("\nCalibrate input 0");
		in0->calibrate();
		// Serial.println("\nCalibrate input 1");
		in1->calibrate();

		conn4.setConn();
		conn5.setConn();
		conn6.setConn();

			// Serial.println("\nMultiplier gain calibration");
			bool multOutLo = out0->loRange;
			bool multOutHi = out0->hiRange;
			out0->setRange(false,false);
			bool multIn0Lo = in0->loRange;
			bool multIn0Hi = in0->hiRange;
			in0->setRange(false,false);
			bool multIn1Lo = in1->loRange;
			bool multIn1Hi = in1->hiRange;
			in1->setRange(false,false);

				setVga(false);
				binarySearchTarget ( 1.0, 0, FLT_MAX, 7, FLT_MAX, anaIrefPmos );
				// Serial.print("anaIrefPmos = ");
				// Serial.println(anaIrefPmos);

			out0->setRange(multOutLo,multOutHi);
			in0->setRange(multIn0Lo,multIn0Hi);
			in1->setRange(multIn1Lo,multIn1Hi);

			if (hiRange) {
				conn0.setConn();
				conn1.setConn();
				// parentSlice->dac->setConstant(-0.1);
			}

				/*calibrate VGA gain to negative full scale*/
				// Serial.print("\nVGA gain calibration ");
				// Serial.println(gain);
				setVga(true);

				biasStable = findBiasHelper (
					hiRange ? gain/10.0 : -gain,
					negGainCalCode
				);

			if (hiRange) {
				conn2.setConn();
			}

		conn4.brkConn();
		conn5.brkConn();
		conn6.brkConn();
		parentSlice->fans[unitId==unitMulL?0:1].setEnable(false);

		ttl--;

	} while (!biasStable && ttl);

	/*teardown*/
	if (hiRange) {
		conn0.brkConn();
		if (userConn00.destIfc) userConn00.setConn();
		if (userConn01.sourceIfc) userConn01.setConn();

		parentSlice->muls[unitId==unitMulL?1:0].anaIrefPmos = userMulPmos;
		parentSlice->muls[unitId==unitMulL?1:0].setAnaIrefPmos();
		parentSlice->muls[unitId==unitMulL?1:0].anaIrefDacNmos = userVgaNmos;
		parentSlice->muls[unitId==unitMulL?1:0].setAnaIrefDacNmos( false, false );
		parentSlice->muls[unitId==unitMulL?1:0].negGainCalCode = userVgaCalCode;
		parentSlice->muls[unitId==unitMulL?1:0].setGainCode( userVgaGain );
		parentSlice->muls[unitId==unitMulL?1:0].setVga( userVga );

		parentSlice->muls[unitId==unitMulL?1:0].out0->loOffsetCode = userOutLoOffsetCode;
		parentSlice->muls[unitId==unitMulL?1:0].out0->midOffsetCode = userOutMidOffsetCode;
		parentSlice->muls[unitId==unitMulL?1:0].out0->hiOffsetCode = userOutHiOffsetCode;
		parentSlice->muls[unitId==unitMulL?1:0].out0->setRange( userOutLo, userOutHi );

		parentSlice->muls[unitId==unitMulL?1:0].in0->loOffsetCode = userIn0LoOffsetCode;
		parentSlice->muls[unitId==unitMulL?1:0].in0->midOffsetCode = userIn0MidOffsetCode;
		parentSlice->muls[unitId==unitMulL?1:0].in0->hiOffsetCode = userIn0HiOffsetCode;
		parentSlice->muls[unitId==unitMulL?1:0].in0->setRange( userIn0Lo, userIn0Hi );

		parentSlice->muls[unitId==unitMulL?1:0].in1->loOffsetCode = userIn1LoOffsetCode;
		parentSlice->muls[unitId==unitMulL?1:0].in1->midOffsetCode = userIn1MidOffsetCode;
		parentSlice->muls[unitId==unitMulL?1:0].in1->hiOffsetCode = userIn1HiOffsetCode;
		parentSlice->muls[unitId==unitMulL?1:0].in1->setRange( userIn1Lo, userIn1Hi );

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

	parentSlice->dac->anaIrefDacNmos = userDacNmos;
	parentSlice->dac->setAnaIrefDacNmos( false, false );
	parentSlice->dac->negGainCalCode = userDacCalCode;
	parentSlice->dac->setHiRange(userDacHi);
	parentSlice->dac->out0->setInv(userDacInv);
	parentSlice->dac->setConstantCode(userDacConst);

	return true;
}

void Fabric::Chip::Tile::Slice::Multiplier::MultiplierInterface::calibrate () {

	/*setup*/
	/*the multiplier is used as a VGA during calibration of the output and the first input*/
	/*Set calDac, enable variable gain amplifer mode*/
	/*when calibrating the output offset, the zero value of the VGA, which has a very small offset, is used to provide a reference zero*/
	/*the VGA has to be some large value when calibrating the first input, which is calibrated by tuning the first input to zero*/
	/*Set gain if VGA mode*/
	unsigned char userGainCode = parentMultiplier->gainCode;
	if (ifcId==out0Id || ifcId==in0Id) {
		parentMultiplier->setGainCode((ifcId==in0Id) ? 255 : 128);
	}
	/*if calibrating the input offset of second input, feed an input to the MUL first input*/
	Connection conn = Connection ( parentFu->parentSlice->dac->out0, parentFu->in0 );
	unsigned char userConstantCode = parentFu->parentSlice->dac->constantCode;
	bool userInverse = parentFu->parentSlice->dac->out0->inverse;
	if (ifcId==in1Id) {
		parentFu->parentSlice->dac->setConstantCode (0);
		parentFu->parentSlice->dac->out0->setInv (true);
		conn.setConn();
		parentMultiplier->setVga(false);
	}

	bool userLoRange = loRange;
	bool userHiRange = hiRange;
	setRange(true, false);
	binarySearch ( 0, FLT_MAX, 63, FLT_MAX, loOffsetCode );
	if ( loOffsetCode<1 || loOffsetCode>62 ) error ("MUL offset failure");
	setRange(false, false);
	binarySearch ( 0, FLT_MAX, 63, FLT_MAX, midOffsetCode );
	if ( midOffsetCode<1 || midOffsetCode>62 ) error ("MUL offset failure");
	setRange(false, true);
	binarySearch ( 0, FLT_MAX, 63, FLT_MAX, hiOffsetCode );
	if ( hiOffsetCode<1 || hiOffsetCode>62 ) error ("MUL offset failure");

	/*teardown*/
	setRange( userLoRange, userHiRange );
	if (ifcId==in1Id) {
		parentFu->parentSlice->dac->setConstantCode (userConstantCode);
		parentFu->parentSlice->dac->out0->setInv (userInverse);
		conn.brkConn();
	}
	if (ifcId==out0Id || ifcId==in0Id) {
		parentMultiplier->setGainCode( userGainCode );
	}
}

bool Fabric::Chip::Tile::Slice::Multiplier::setAnaIrefDacNmos (
	bool decrement,
	bool increment
) {
	if (!setAnaIrefDacNmosHelper (decrement, increment)) return false;

	unsigned char selRow;
	unsigned char selCol;
	unsigned char selLine;
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
			case slice0: cfgTile = (cfgTile & 0b00000111) + ((anaIrefDacNmos<<3) & 0b00111000); break;
			case slice1: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
			case slice2: cfgTile = (cfgTile & 0b00000111) + ((anaIrefDacNmos<<3) & 0b00111000); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
			default: error ("MUL invalid slice"); break;
		} break;
		case unitMulR: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
			case slice1: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
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

	return true;
}

void Fabric::Chip::Tile::Slice::Multiplier::setAnaIrefPmos () const {

	unsigned char setting=7-anaIrefPmos; // because pmos setting has opposite effect on gain
	unsigned char selRow=0;
	unsigned char selCol=4;
	unsigned char selLine;
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
