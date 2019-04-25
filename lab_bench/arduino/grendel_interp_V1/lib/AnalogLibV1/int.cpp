#include "AnalogLib.h"
#include <float.h>

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
  if(-1.0000001 < initial && initial < 127.0/128.0){
    setInitialCode(initial*128.0+128.0);
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

Fabric::Chip::Tile::Slice::Integrator::Integrator (
	Chip::Tile::Slice * parentSlice
) :
	FunctionUnit(parentSlice, unitInt)
{
	in0 = new IntegratorIn (this);
	tally_dyn_mem <IntegratorIn> ("IntegratorIn");
	out0 = new IntegratorOut (this);
	tally_dyn_mem <IntegratorOut> ("IntegratorOut");
  m_codes.pmos = 5;
  m_codes.nmos = 0;
  m_codes.ic_code = 128;
  m_codes.ic_val = 0.0;
  m_codes.inv[in0Id] = false;
  m_codes.inv[out0Id] = false;
  m_codes.range[in0Id] = RANGE_MED;
  m_codes.range[out0Id] = RANGE_MED;
  m_codes.cal_enable[in0Id] = false;
  m_codes.cal_enable[in1Id] = false;
  m_codes.port_cal[in0Id] = 31;
  m_codes.port_cal[out0Id] = 31;
  m_codes.exception = false;
  m_codes.gain_cal = 32;
	setAnaIrefNmos();
	setAnaIrefPmos();
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

bool Fabric::Chip::Tile::Slice::Integrator::calibrate (
) {
  return true;
  /*
	setEnable(true);
	Connection conn2 = Connection ( out0, parentSlice->tileOuts[3].in0 );
	Connection conn3 = Connection ( parentSlice->tileOuts[3].out0, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
	conn2.setConn();
	conn3.setConn();

	bool succ = true;
    //    SerialUSB.println("\nCalibrate output");
	succ = succ && in0->calibrate();
  succ = succ && out0->calibrate();
  //    SerialUSB.println("\nCalibrate input");
	conn2.brkConn();
	conn3.brkConn();
	setEnable(false); // commits inteface calibration settings
  // ignore our success calibrating.
	return true;
  */
}

bool Fabric::Chip::Tile::Slice::Integrator::calibrateTarget () {
    //    SerialUSB.print("\nIntegrator calibrateTarget hiRange ");
    //    SerialUSB.print(hiRange);
    //    SerialUSB.print(" initial ");
    //    SerialUSB.println(initial);

  if(!m_codes.enable){
    return true;
  }
	// preserve mul state because we will clobber it
  bool hiRange = (m_codes.range[out0Id] == RANGE_HIGH);
  float initial = m_codes.ic_val;
  mult_code_t user_mul0 = parentSlice->muls[0].m_codes;
	//unsigned char userMulPmos = parentSlice->muls[0].anaIrefPmos;
	//unsigned char userVgaNmos = parentSlice->muls[0].anaIrefDacNmos;
	//unsigned char userVgaCalCode = parentSlice->muls[0].negGainCalCode;
	//bool userVga = parentSlice->muls[0].vga;
	//unsigned char userVgaGain = parentSlice->muls[0].gainCode;

	//bool userOutLo = parentSlice->muls[0].out0->loRange;
	//bool userOutHi = parentSlice->muls[0].out0->hiRange;
	//unsigned char userOutLoOffsetCode = parentSlice->muls[0].out0->loOffsetCode;
	//unsigned char userOutMidOffsetCode = parentSlice->muls[0].out0->midOffsetCode;
	//unsigned char userOutHiOffsetCode = parentSlice->muls[0].out0->hiOffsetCode;

	//bool userIn0Lo = parentSlice->muls[0].in0->loRange;
	//bool userIn0Hi = parentSlice->muls[0].in0->hiRange;
	//unsigned char userIn0LoOffsetCode = parentSlice->muls[0].in0->loOffsetCode;
	//unsigned char userIn0MidOffsetCode = parentSlice->muls[0].in0->midOffsetCode;
	//unsigned char userIn0HiOffsetCode = parentSlice->muls[0].in0->hiOffsetCode;

	//bool userIn1Lo = parentSlice->muls[0].in1->loRange;
	//bool userIn1Hi = parentSlice->muls[0].in1->hiRange;
	//unsigned char userIn1LoOffsetCode = parentSlice->muls[0].in1->loOffsetCode;
	//unsigned char userIn1MidOffsetCode = parentSlice->muls[0].in1->midOffsetCode;
	//unsigned char userIn1HiOffsetCode = parentSlice->muls[0].in1->hiOffsetCode;
	if (hiRange) parentSlice->muls[0].setGain(-0.1);

	// output side
	Connection userConn00 = Connection ( out0, out0->userSourceDest );
	Connection userConn01 = Connection ( parentSlice->muls[0].in0->userSourceDest, parentSlice->muls[0].in0 );
	if (hiRange && userConn01.sourceIfc) userConn01.brkConn();
	Connection conn0 = Connection ( out0, parentSlice->muls[0].in0 );

	Connection userConn10 = Connection ( parentSlice->muls[0].out0, parentSlice->muls[0].out0->userSourceDest );
	Connection userConn11 = Connection ( parentSlice->tileOuts[3].in0->userSourceDest, parentSlice->tileOuts[3].in0 );
	// if (hiRange && userConn11.sourceIfc) userConn11.brkConn();
	Connection conn1 = Connection ( parentSlice->muls[0].out0, parentSlice->tileOuts[3].in0 );

	Connection conn2 = Connection ( out0, parentSlice->tileOuts[3].in0 );
	if (userConn11.sourceIfc) userConn11.brkConn();
	conn2.setConn();

	Connection userConn30 = Connection ( parentSlice->tileOuts[3].out0, parentSlice->tileOuts[3].out0->userSourceDest );
	Connection userConn31 = Connection ( parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0->userSourceDest, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
	if (userConn31.sourceIfc) userConn31.brkConn();
	Connection conn3 = Connection ( parentSlice->tileOuts[3].out0, parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );
	conn3.setConn();

  /*
	bool userIntOutLo=out0->loRange; bool userIntOutHi=out0->hiRange;
	bool userIntInLo=in0->loRange; bool userIntInHi=in0->hiRange;
	in0->setRange(false,false);
    //     SerialUSB.println("\nCalibrate output");
	out0->calibrate();
    //     SerialUSB.println("\nCalibrate input");
	in0->calibrate();
	out0->setRange(userIntOutLo,userIntOutHi);
	in0->setRange(userIntInLo,userIntInHi);
	anaIrefDacNmos = 0;
  */
		/*calibrate integrator gain to target scale*/
        //         SerialUSB.print("\nIntegrator gain calibration ");
        //         SerialUSB.print(initial);
        //         SerialUSB.print(" initialCode ");
        //         SerialUSB.println(initialCode);

    m_codes.nmos = 0;
    setAnaIrefNmos();
    if (hiRange) {
      conn0.setConn();
      conn1.setConn();
    }
    bool new_search = true;
    bool calib_failed = true;
		while (new_search) {
      bool succ = out0->calibrate();
      succ &= in0->calibrate();
			findBiasHelper (
				hiRange ? -initial : initial,
				m_codes.gain_cal,
        m_codes.nmos,
        new_search,
        calib_failed
			);
      calib_failed |= !succ;
		}

	if (hiRange) {
		conn0.brkConn();
		if (userConn00.destIfc) userConn00.setConn();
		if (userConn01.sourceIfc) userConn01.setConn();

    parentSlice->muls[0].update(user_mul0);
		//parentSlice->muls[0].anaIrefPmos = userMulPmos;
		//parentSlice->muls[0].setAnaIrefPmos();
		//parentSlice->muls[0].anaIrefDacNmos = userVgaNmos;
		//parentSlice->muls[0].setAnaIrefDacNmos( false, false );
		//parentSlice->muls[0].negGainCalCode = userVgaCalCode;
		//parentSlice->muls[0].setGainCode( userVgaGain );
		//parentSlice->muls[0].setVga( userVga );

		//parentSlice->muls[0].out0->loOffsetCode = userOutLoOffsetCode;
		//parentSlice->muls[0].out0->midOffsetCode = userOutMidOffsetCode;
		//parentSlice->muls[0].out0->hiOffsetCode = userOutHiOffsetCode;
		//parentSlice->muls[0].out0->setRange( userOutLo, userOutHi );

		//parentSlice->muls[0].in0->loOffsetCode = userIn0LoOffsetCode;
		//parentSlice->muls[0].in0->midOffsetCode = userIn0MidOffsetCode;
		//parentSlice->muls[0].in0->hiOffsetCode = userIn0HiOffsetCode;
		//parentSlice->muls[0].in0->setRange( userIn0Lo, userIn0Hi );

		//parentSlice->muls[0].in1->loOffsetCode = userIn1LoOffsetCode;
		//parentSlice->muls[0].in1->midOffsetCode = userIn1MidOffsetCode;
		//parentSlice->muls[0].in1->hiOffsetCode = userIn1HiOffsetCode;
		//parentSlice->muls[0].in1->setRange( userIn1Lo, userIn1Hi );

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

	return calib_failed;
}

bool Fabric::Chip::Tile::Slice::Integrator::IntegratorInterface::calibrate () {
    //    SerialUSB.print("\nIntegrator interface calibration");
	parentIntegrator->m_codes.cal_enable[ifcId] = true;
  float delta = FLT_MAX;
  bool failed = false;
  unsigned char code;
	binarySearch ( 0, FLT_MAX, 63, FLT_MAX, code, delta);
	if ( code<1 || code>62 ) error ("INT offset failure");
  parentFu->testStab(code,parentIntegrator->m_codes.nmos,delta,failed);
  parentIntegrator->m_codes.port_cal[ifcId] = code;
  return !failed;
}

void Fabric::Chip::Tile::Slice::Integrator::setAnaIrefNmos () const {
	unsigned char selRow=0;
	unsigned char selCol=2;
	unsigned char selLine;
  testIref(m_codes.nmos);
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
  testIref(m_codes.pmos);
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
