#include "HCDC_DEMO_API.h"

void Fabric::Chip::Tile::Slice::Fanout::setEnable (
	bool enable
) {
	/*record*/
	this->enable = enable;
	/*set*/
	setParam0();
	setParam1();
	setParam2();
	setParam3();
}

void Fabric::Chip::Tile::Slice::Fanout::setHiRange (
	bool hiRange // 20uA mode
	// 20uA mode results in more ideal behavior in terms of phase shift but consumes more power
	// this setting should match the unit that gives the input to the fanout
) {
	in0->hiRange = hiRange;
	setParam0();
	setParam1();
	setParam2();
	setParam3();
}

void Fabric::Chip::Tile::Slice::Fanout::FanoutOut::setInv (
	bool inverse // whether output is negated
) {
	this->inverse = inverse;
	parentFu->setParam1 ();
	parentFu->setParam2 ();
	parentFu->setParam3 ();
}

void Fabric::Chip::Tile::Slice::Fanout::setThird (
	bool third // whether third output is on
) {
	this->third = third;
	setParam3();
}

Fabric::Chip::Tile::Slice::Fanout::Fanout (
	Chip::Tile::Slice * parentSlice,
	unit unitId
) :
	FunctionUnit(parentSlice, unitId)
{
	in0 = new GenericInterface (this, in0Id);
	tally_dyn_mem <GenericInterface> ("GenericInterface");
	out0 = new FanoutOut (this, out0Id);
	tally_dyn_mem <FanoutOut> ("FanoutOut");
	out1 = new FanoutOut (this, out1Id);
	tally_dyn_mem <FanoutOut> ("FanoutOut");
	out2 = new FanoutOut (this, out2Id);
	tally_dyn_mem <FanoutOut> ("FanoutOut");
	setAnaIrefDacNmos( false, false );
	setAnaIrefPmos();
}

/*Set enable, range*/
void Fabric::Chip::Tile::Slice::Fanout::setParam0 () const {
	unsigned char cfgTile = 0;
	cfgTile += enable ? 1<<7 : 0;
	cfgTile += (in0->hiRange) ? 1<<5 : 0;
	setParamHelper (0, cfgTile);
}

/*Set calDac1, invert output 1*/
void Fabric::Chip::Tile::Slice::Fanout::setParam1 () const {
	unsigned char calDac1 = in0->hiRange ? out0->hiOffsetCode : out0->midOffsetCode;
	if (calDac1<0||63<calDac1) error ("calDac1 out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += calDac1<<2;
	cfgTile += out0->inverse ? 1<<1 : 0;
	setParamHelper (1, cfgTile);
}

/*Set calDac2, invert output 2*/
void Fabric::Chip::Tile::Slice::Fanout::setParam2 () const {
	unsigned char calDac2 = in0->hiRange ? out1->hiOffsetCode : out1->midOffsetCode;
	if (calDac2<0||63<calDac2) error ("calDac2 out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += calDac2<<2;
	cfgTile += out1->inverse ? 1<<1 : 0;
	setParamHelper (2, cfgTile);
}

/*Set calDac3, invert output 3, enable output 3*/
void Fabric::Chip::Tile::Slice::Fanout::setParam3 () const {
	unsigned char calDac3 = in0->hiRange ? out2->hiOffsetCode : out2->midOffsetCode;
	if (calDac3<0||63<calDac3) error ("calDac3 out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += calDac3<<2;
	cfgTile += out2->inverse ? 1<<1 : 0;
	cfgTile += third ? 1<<0 : 0;
	setParamHelper (3, cfgTile);
}

/*Helper function*/
void Fabric::Chip::Tile::Slice::Fanout::setParamHelper (
	unsigned char selLine,
	unsigned char cfgTile
) const {
	if (selLine<0||3<selLine) error ("selLine out of bounds");

	/*DETERMINE SEL_ROW*/
	unsigned char selRow;
	switch (parentSlice->sliceId) {
		case slice0: selRow = 2; break;
		case slice1: selRow = 3; break;
		case slice2: selRow = 4; break;
		case slice3: selRow = 5; break;
		default: error ("invalid slice. Only slices 0 through 3 have FANs"); break;
	}

	/*DETERMINE SEL_COL*/
	unsigned char selCol;
	switch (unitId) {
		case unitFanL: selCol = 0; break;
		case unitFanR: selCol = 1; break;
		default: error ("invalid unit. Only unitFanL and unitFanR are FANs"); break;
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

bool Fabric::Chip::Tile::Slice::Fanout::calibrate () {

anaIrefDacNmos = 0;

	setEnable ( true );
	Connection conn = Connection (parentSlice->tileOuts[3].out0, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0);
	conn.setConn();

	// Serial.print("\nFanout interface calibration");

	bool biasStable = false;
	while (!biasStable) {
		// Serial.println("\nfanHi");
		setHiRange ( true );
		biasStable = out0->findBias(out0->hiOffsetCode);
		if (biasStable) biasStable &= out1->findBias(out1->hiOffsetCode);
		if (biasStable) biasStable &= out2->findBias(out2->hiOffsetCode);
		// Serial.println("\nfanMid");
		setHiRange ( false );
		if (biasStable) biasStable &= out0->findBias(out0->midOffsetCode);
		if (biasStable) biasStable &= out1->findBias(out1->midOffsetCode);
		if (biasStable) biasStable &= out2->findBias(out2->midOffsetCode);
	}

	conn.brkConn();
	setEnable ( false );

	return biasStable;
}

bool Fabric::Chip::Tile::Slice::Fanout::FanoutOut::findBias (
	unsigned char & offsetCode
) {
	if (ifcId==out2Id) parentFanout->setThird(true);
	Connection conn = Connection ( this, parentFu->parentSlice->tileOuts[3].in0 );
	conn.setConn();

	bool biasStable = findBiasHelper (offsetCode);

	conn.brkConn();
	if (ifcId==out2Id) parentFanout->setThird(false);

	return biasStable;
}


bool Fabric::Chip::Tile::Slice::Fanout::setAnaIrefDacNmos (
	bool decrement,
	bool increment
) {
	if (!setAnaIrefDacNmosHelper (decrement, increment)) return false;

	unsigned char selRow=0;
	unsigned char selCol;
	unsigned char selLine;
	switch (unitId) {
		case unitFanL: switch (parentSlice->sliceId) {
			case slice0: selCol=0; selLine=0; break;
			case slice1: selCol=0; selLine=1; break;
			case slice2: selCol=1; selLine=0; break;
			case slice3: selCol=1; selLine=1; break;
			default: error ("FAN invalid slice"); break;
		} break;
		case unitFanR: switch (parentSlice->sliceId) {
			case slice0: selCol=1; selLine=2; break;
			case slice1: selCol=1; selLine=3; break;
			case slice2: selCol=2; selLine=0; break;
			case slice3: selCol=2; selLine=1; break;
			default: error ("FAN invalid slice"); break;
		} break;
		default: error ("FAN invalid unitId"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	switch (unitId) {
		case unitFanL: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00000111) + ((anaIrefDacNmos<<3) & 0b00111000); break;
			case slice1: cfgTile = (cfgTile & 0b00000111) + ((anaIrefDacNmos<<3) & 0b00111000); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
			default: error ("FAN invalid slice"); break;
		} break;
		case unitFanR: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00000111) + ((anaIrefDacNmos<<3) & 0b00111000); break;
			case slice1: cfgTile = (cfgTile & 0b00000111) + ((anaIrefDacNmos<<3) & 0b00111000); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (anaIrefDacNmos & 0b00000111); break;
			default: error ("FAN invalid slice"); break;
		} break;
		default: error ("FAN invalid unitId"); break;
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

void Fabric::Chip::Tile::Slice::Fanout::setAnaIrefPmos () const {

	unsigned char selRow=0;
	unsigned char selCol;
	unsigned char selLine;

	switch (unitId) {
		case unitFanL: switch (parentSlice->sliceId) {
			case slice0: selLine=3; break;
			case slice1: selLine=2; break;
			case slice2: selLine=1; break;
			case slice3: selLine=0; break;
			default: error ("FAN invalid slice"); break;
		} selCol=0; break;
		case unitFanR: switch (parentSlice->sliceId) {
			case slice0: selLine=1; break;
			case slice1: selLine=0; break;
			case slice2: selLine=3; break;
			case slice3: selLine=2; break;
			default: error ("FAN invalid slice"); break;
		} selCol=1; break;
		default: error ("FAN invalid unitId"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	switch (unitId) {
		case unitFanL: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00111000) + (anaIrefPmos & 0b00000111); break;
			case slice1: cfgTile = (cfgTile & 0b00111000) + (anaIrefPmos & 0b00000111); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (anaIrefPmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (anaIrefPmos & 0b00000111); break;
			default: error ("FAN invalid slice"); break;
		} break;
		case unitFanR: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00000111) + ((anaIrefPmos<<3) & 0b00111000); break;
			case slice1: cfgTile = (cfgTile & 0b00000111) + ((anaIrefPmos<<3) & 0b00111000); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (anaIrefPmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (anaIrefPmos & 0b00000111); break;
			default: error ("FAN invalid slice"); break;
		} break;
		default: error ("FAN invalid unitId"); break;
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