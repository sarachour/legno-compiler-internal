#include "AnalogLib.h"
#include "assert.h"
#include "fu.h"

void Fabric::Chip::Tile::Slice::ChipAdc::setEnable (
	bool enable
) {
	m_codes.enable = enable;
	setParam0 ();
	setParam1 ();
	setParam2 ();
	setParam3 ();
}

void Fabric::Chip::Tile::Slice::ChipAdc::setRange (
	// default is 2uA mode
	range_t range
) {
  assert(range != RANGE_LOW);
  m_codes.range = range;
	setParam0();
}

unsigned char Fabric::Chip::Tile::Slice::ChipAdc::getData () const {
	unsigned char adcData0, adcData1;
	bool done;
	parentSlice->parentTile->readSerial ( adcData0, adcData1, done );
	unsigned char result = (parentSlice->sliceId==slice0) ? adcData0 : adcData1;
	// Serial.print(" ");Serial.println(result);
	return result;
}

unsigned char Fabric::Chip::Tile::Slice::ChipAdc::getStatusCode() const {
	unsigned char exceptionVector;
	parentSlice->parentTile->readExp ( exceptionVector );
	// bits 4-5: L ADC exception
	// bits 6-7: R ADC exception
	// bits 5,7: ADC underflow
	// bits 4,6: ADC overflow
	// Serial.print (exceptionVector);
	// Serial.print (" ");
  unsigned char code = 0;
  if(parentSlice->sliceId == slice0){
    code += bitRead(exceptionVector,4) == 0b1 ? 1 : 0;
    code += bitRead(exceptionVector,5) == 0b1 ? 2 : 0;
  }
  else{
    code += bitRead(exceptionVector,6) == 0b1 ? 1 : 0;
    code += bitRead(exceptionVector,7) == 0b1 ? 2 : 0;
  }
  return code;
}
bool Fabric::Chip::Tile::Slice::ChipAdc::getException () const {
	unsigned char exceptionVector;
	parentSlice->parentTile->readExp ( exceptionVector );
	// bits 4-5: L ADC exception
	// bits 6-7: R ADC exception
	// bits 5,7: ADC underflow
	// bits 4,6: ADC overflow
	// Serial.print (exceptionVector);
	// Serial.print (" ");
	bool result = (parentSlice->sliceId==slice0) ?
		bitRead (exceptionVector, 4) == 0b1 ||
		bitRead (exceptionVector, 5) == 0b1
	:
		bitRead (exceptionVector, 6) == 0b1 ||
		bitRead (exceptionVector, 7) == 0b1
	;
	return result;
}

void Fabric::Chip::Tile::Slice::ChipAdc::defaults(){
  m_codes.upper = 31;
  m_codes.upper_fs = nA100;
  m_codes.lower = 31;
  m_codes.lower_fs = nA100;
  m_codes.pmos = 4;
  m_codes.pmos2 = 4;
  m_codes.nmos = 0;
  m_codes.i2v_cal = 31;
  m_codes.enable = false;
  m_codes.inv = false;
  m_codes.range = RANGE_MED;
  m_codes.test_en = false;
  m_codes.test_adc = false;
  m_codes.test_i2v = false;
  m_codes.test_rs = false;
  m_codes.test_rsinc = false;
	setAnaIrefNmos();
	setAnaIrefPmos();
}
Fabric::Chip::Tile::Slice::ChipAdc::ChipAdc (
	Slice * parentSlice
) :
	FunctionUnit(parentSlice, unitAdc)
{
	in0 = new AdcIn (this);
	tally_dyn_mem <AdcIn> ("AdcIn");
  defaults();
}

/*Set enable, range, delay, decRst*/
void Fabric::Chip::Tile::Slice::ChipAdc::setParam0 () const {
	unsigned char cfgTile = 0;
	cfgTile += m_codes.enable ? 1<<7 : 0;
  bool is_hi = (m_codes.range == RANGE_HIGH);
	cfgTile += is_hi ? 1<<5 : 0;
	cfgTile += ns11_5<<3;
	cfgTile += false ? 1<<2 : 0;
	cfgTile += (ns3==ns6) ? 1 : 0;
	setParamHelper (0, cfgTile);
}

/*Set calibration enable, m_codes.upperEn, calI2V*/
void Fabric::Chip::Tile::Slice::ChipAdc::setParam1 () const {
	if (m_codes.i2v_cal<0||63<m_codes.i2v_cal)
    error ("m_codes.i2v_cal out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += false ? 1<<7 : 0;
	cfgTile += false ? 1<<6 : 0;
	cfgTile += m_codes.i2v_cal<<0;
	setParamHelper (1, cfgTile);
}

/*Set m_codes.lower, m_codes.lower_fs*/
void Fabric::Chip::Tile::Slice::ChipAdc::setParam2 () const {
	if (m_codes.lower<0||63<m_codes.lower)
    error ("m_codes.lower out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += m_codes.lower <<2;
	cfgTile += m_codes.lower_fs <<0;
	setParamHelper (2, cfgTile);
}

/*Set m_codes.upper, m_codes.upper_fs*/
void Fabric::Chip::Tile::Slice::ChipAdc::setParam3 () const {
	if (m_codes.upper<0||63<m_codes.upper) error ("m_codes.upper out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += m_codes.upper <<2;
	cfgTile += m_codes.upper_fs<<0;
	setParamHelper (3, cfgTile);
}
void Fabric::Chip::Tile::Slice::ChipAdc::setTestParams (
                                                        bool testEn, /*Configure the entire block in testing mode so that I2V and A/D can be tested individually*/
                                                        bool testAdc, /*Testing the ADC individually.*/
                                                        bool testIv, /*Testing the I2V individually.*/
                                                        bool testRs, /*Testing the rstring individually.*/
                                                        bool testRsInc /*Configure the counter for upward or downward increments during set up for testing R-string separately (w/ cfgCalEN=1)*/
                                                        )
{
  m_codes.test_en = testEn;
  m_codes.test_adc = testAdc;
  m_codes.test_i2v = testIv;
  m_codes.test_rs = testRs;
  m_codes.test_rsinc = testRsInc;
  setParam4();
}
/*Set testEn, testAdc, testIv, testRs, testRsInc*/
void Fabric::Chip::Tile::Slice::ChipAdc::setParam4 () const {
	unsigned char cfgTile = 0;
	cfgTile += m_codes.test_en ? 1<<7 : 0;
	cfgTile += m_codes.test_adc ? 1<<6 : 0;
	cfgTile += m_codes.test_i2v ? 1<<5 : 0;
	cfgTile += m_codes.test_rs ? 1<<4 : 0;
	cfgTile += m_codes.test_rsinc ? 1<<3 : 0;
	setParamHelper (4, cfgTile);
}

void Fabric::Chip::Tile::Slice::ChipAdc::setParamHelper (
	unsigned char selLine,
	unsigned char cfgTile
) const {
	if (selLine<0||4<selLine) error ("selLine out of bounds");

	/*DETERMINE SEL_COL*/
	unsigned char selCol;
	switch (parentSlice->sliceId) {
		case slice0: selCol = 1; break;
		case slice2: selCol = 2; break;
		default: error ("setParamHelper invalid slice. Only even slices have ADCs"); break;
	}

	Vector vec = Vector (
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

void Fabric::Chip::Tile::Slice::ChipAdc::setAnaIrefPmos () const {
	// anaIref1Pmos
	unsigned char selRow=0;
	unsigned char selCol=3;
	unsigned char selLine;
  binsearch::test_iref(m_codes.pmos);
  binsearch::test_iref(m_codes.pmos2);
	switch (parentSlice->sliceId) {
		case slice0: selLine=1; break;
		case slice2: selLine=3; break;
		default: error ("ADC invalid slice"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	cfgTile = (cfgTile & 0b00000111) + ((m_codes.pmos<<3) & 0b00111000);

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

	// anaIref2Pmos
	selRow=0;
	selCol=3;
	// selLine;
	switch (parentSlice->sliceId) {
		case slice0: selLine=2; break;
		case slice2: selLine=5; break;
		default: error ("ADC invalid slice"); break;
	}
	cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);

	switch (parentSlice->sliceId) {
		case slice0: cfgTile = (cfgTile & 0b00000111) + ((m_codes.pmos2<<3) & 0b00111000);break;
		case slice2: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos2 & 0b00000111);break;
		default: error ("ADC invalid slice"); break;
	}

	vec = Vector (
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

bool Fabric::Chip::Tile::Slice::ChipAdc::calibrate (const float max_error) {

  update(m_codes);
  adc_code_t codes_self= m_codes;
  dac_code_t codes_dac = parentSlice->dac->m_codes;
	Connection conn0 = Connection ( parentSlice->dac->out0, in0 );
	conn0.setConn();
	setEnable (true);

  print_log("-> finding posneg/fullscale settings");
  Serial.flush();
	if (!findCalCompFs()) return false;
  sprintf(FMTBUF, "lower=%d upper=%d", m_codes.lower, m_codes.upper);
  print_debug(FMTBUF);

	conn0.brkConn();
	parentSlice->dac->setEnable(false);

	// once fullscale and spread and posneg settings found
	// find I2V offset code
  print_log("-> finding i2v bias");
  float error;
  bool succ = binsearch::find_bias_and_nmos(this,
                                            128.0,
                                            max_error,
                                            m_codes.i2v_cal,
                                            m_codes.nmos,
                                            error,
                                            MEAS_ADC);
	setEnable (false);
  parentSlice->dac->update(codes_dac);
  codes_self.i2v_cal = m_codes.i2v_cal;
  codes_self.nmos = m_codes.nmos;
  codes_self.lower = m_codes.lower;
  codes_self.lower_fs = m_codes.lower_fs;
  codes_self.upper = m_codes.upper;
  codes_self.upper_fs = m_codes.upper_fs;
  update(codes_self);

	// Serial.println("offset settings found");
	return succ;
}

bool Fabric::Chip::Tile::Slice::ChipAdc::findCalCompFs () {

	// Serial.println("nA100");
	m_codes.lower_fs = nA100;
	m_codes.upper_fs = nA100;
	if (checkScale()) return true;
	// Serial.println("nA200");
	m_codes.lower_fs = nA200;
	m_codes.upper_fs = nA200;
	if (checkScale()) return true;
	// Serial.println("nA300");
	m_codes.lower_fs = nA300;
	m_codes.upper_fs = nA300;
	if (checkScale()) return true;
	// Serial.println("nA400");
	m_codes.lower_fs = nA400;
	m_codes.upper_fs = nA400;
	if (checkScale()) return true;

	return false;
}

bool Fabric::Chip::Tile::Slice::ChipAdc::checkScale () {
	for (unsigned char spread=0; spread<32; spread++) {
		// Serial.print("spread = "); Serial.println(spread);
		if ( checkSpread(spread,false,false) ) return true;
		if ( checkSpread(spread,false,true) ) return true;
		if ( checkSpread(spread,true,false) ) return true;
		if ( checkSpread(spread,true,true) ) return true;
	}
	return false;
}

bool Fabric::Chip::Tile::Slice::ChipAdc::checkSpread (
	unsigned char spread,
	bool lowerPos,
	bool upperPos
) {
	m_codes.lower = lowerPos ? 31+spread : 31-spread;
	setParam2();
	m_codes.upper = upperPos ? 31+spread : 31-spread;
	setParam3();

	bool success=true;
	// see if adc code is steady at dac=128
	success &= checkSteady(128);
	// see if adc code is steady at dac=4
	if (success) success &= checkSteady(2);
	// see if adc code is steady at dac=251
	if (success) success &= checkSteady(253);

	return success;
}

bool Fabric::Chip::Tile::Slice::ChipAdc::checkSteady (
	unsigned char dacCode
) const {
  dac_code_t codes_dac = parentSlice->dac->m_codes;
  // update dac code to specified code.
	parentSlice->dac->setConstantCode (dacCode);
	parentSlice->parentTile->parentChip->parentFabric->cfgCommit();
	bool success=true;
  // get the adc code at that value
	unsigned char adcPrev = getData();
	for (unsigned char rep=0; success&&(rep<16); rep++){
    // determine if adc code is the same value as the previous value.
		success &= adcPrev==getData();
  }
  parentSlice->dac->update(codes_dac);
	return success;
}

/*
void Fabric::Chip::Tile::Slice::ChipAdc::AdcIn::findBias (
                                                          unsigned char & offsetCode,
                                                          bool& new_search,
                                                          bool& calib_failed
) {
	// Serial.print("Adc offset calibration ");

  Fabric::Chip::Tile::Slice::ChipAdc* adc = this->parentFu;
	while (new_search) {
		findBiasHelper (offsetCode, adc->m_codes.nmos, new_search, calib_failed);
	}
}
void Fabric::Chip::Tile::Slice::ChipAdc::AdcIn::binarySearch (
	unsigned char minI2VCode,
	float minBest,
	unsigned char maxI2VCode,
	float maxBest,
	unsigned char & finalI2VCode,
  float & finalI2VError
) const {

	if (binarySearchAvg (minI2VCode, minBest, maxI2VCode, maxBest, finalI2VCode)){
    return;
  }

	parentFu->setParam1 ();
	parentFu->parentSlice->parentTile->parentChip->parentFabric->cfgCommit();

	unsigned char adcRead = parentAdc->getData();
	float target = 128.0;
  float error = fabs(adcRead-target);
	// Serial.print("finalI2VCode = ");
	// Serial.println(finalI2VCode);
	Serial.print(adcRead);
  Serial.print(" nmos=");
	Serial.print(parentAdc->m_codes.nmos);
  Serial.print(" target=");
	Serial.print(target);
  Serial.print(" curr_code=");
	Serial.print(finalI2VCode);
  Serial.print(" min_code=");
	Serial.print(minI2VCode);
  Serial.print(" max_code=");
	Serial.print(maxI2VCode);
  Serial.print(" min_error=");
	Serial.print(minBest);
  Serial.print(" max_error=");
	Serial.print(maxBest);
  Serial.print(" error=");
	Serial.println(error);

  finalI2VError = error;
  // read value less than target
	if (adcRead < target) {
		return binarySearch (minI2VCode, minBest, finalI2VCode, error,
                         finalI2VCode, finalI2VError);
	}
  // measured value more than target
  else {
		return binarySearch (finalI2VCode, error, maxI2VCode, maxBest,
                         finalI2VCode, finalI2VError);
	}

}
*/
void Fabric::Chip::Tile::Slice::ChipAdc::setAnaIrefNmos () const {
	// anaIrefI2V mapped to anaIrefDacNmos
	unsigned char selRow=0;
	unsigned char selCol=3;
	unsigned char selLine;
	switch (parentSlice->sliceId) {
		case slice0: selLine=0; break;
		case slice2: selLine=4; break;
		default: error ("ADC invalid slice"); break;
	}
	unsigned char cfgTile = endian(
		parentSlice->parentTile->parentChip->cfgBuf
		[parentSlice->parentTile->tileRowId]
		[parentSlice->parentTile->tileColId]
		[selRow]
		[selCol]
		[selLine]
	);
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
