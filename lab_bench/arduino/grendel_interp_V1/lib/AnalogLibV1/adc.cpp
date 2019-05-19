#include "AnalogLib.h"
#include "assert.h"
#include "fu.h"
#include "calib_util.h"

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
  m_codes.padding=20;
  m_codes.nmos = 0;
  m_codes.i2v_cal = 31;
  m_codes.enable = false;
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

bool helper_check_steady(Fabric * fab,
                         Fabric::Chip::Tile::Slice::ChipAdc* adc,
                         Fabric::Chip::Tile::Slice::Dac* dac,
                         dac_code_t& dac_code
                         ){
  dac_code_t codes_dac = dac->m_codes;
  dac->update(dac_code);
	fab->cfgCommit();
  bool success=true;
  // get the adc code at that value
	unsigned char adcPrev = adc->getData();
	for (unsigned char rep=0; success&&(rep<16); rep++){
    // determine if adc code is the same value as the previous value.
		success &= adcPrev==adc->getData();
  }
  dac->update(codes_dac);
	return success;
}


bool helper_find_bias_and_nmos(Fabric * fab,
                               Fabric::Chip::Tile::Slice::ChipAdc* adc,
                               Fabric::Chip::Tile::Slice::Dac* dac,
                               dac_code_t& dac_code_0,
                               dac_code_t& dac_code_1,
                               dac_code_t& dac_code_neg_1,
                               adc_code_t& best_code
                         ){
  dac_code_t codes_dac = dac->m_codes;
  adc->m_codes.nmos = 0;
  adc->setAnaIrefNmos();
  bool found_code = false;
  float max_error = 0.5;
  int padding = adc->m_codes.padding;
  while(adc->m_codes.nmos <= 7 && !found_code){
    bool succ = true;
    float error;
    bool calib_failed;
    float target = 128.0;
    dac->update(dac_code_0);
    binsearch::find_bias(adc,
                         128.0,
                         adc->m_codes.i2v_cal,
                         error,
                         MEAS_ADC);
    binsearch::test_stab(adc->m_codes.i2v_cal, error,
                         max_error, calib_failed);
    succ &= !calib_failed;
    sprintf(FMTBUF,"nmos=%d i2v_cal=%d target=%f meas=%f succ=%s",
            adc->m_codes.nmos, adc->m_codes.i2v_cal, 128.0, 128.0+error,
            calib_failed ? "false" : "true");
    print_log(FMTBUF);

    if(succ){
      dac->update(dac_code_1);
      target = 255.0-padding;
      error = binsearch::get_bias(adc, target, MEAS_ADC);
      binsearch::test_stab(adc->m_codes.i2v_cal, error,
                           max_error, calib_failed);
      succ &= !calib_failed;
      sprintf(FMTBUF,"nmos=%d i2v_cal=%d target=%f meas=%f succ=%s",
              adc->m_codes.nmos, adc->m_codes.i2v_cal,target,target+error,
              calib_failed ? "false" : "true");
      print_log(FMTBUF);

    }
    if(succ){
      dac->update(dac_code_neg_1);
      target = 0.0+padding;
      error = binsearch::get_bias(adc, target, MEAS_ADC);
      binsearch::test_stab(adc->m_codes.i2v_cal, error,
                           max_error, calib_failed);
      succ &= !calib_failed;
      sprintf(FMTBUF,"nmos=%d i2v_cal=%d target=%f meas=%f succ=%s",
              adc->m_codes.nmos, adc->m_codes.i2v_cal, target, target+error,
              calib_failed ? "false" : "true");
      print_log(FMTBUF);
    }
    if(succ){
      found_code = true;
      best_code = adc->m_codes;
    }
    adc->m_codes.nmos += 1;
    if(adc->m_codes.nmos <= 7){
      adc->setAnaIrefNmos();
    }
  }
  return found_code;
}
bool Fabric::Chip::Tile::Slice::ChipAdc::calibrate (util::calib_result_t& result,
                                                    const float max_error) {

  float coeff = util::range_to_coeff(m_codes.range);
  update(m_codes);

  Fabric::Chip::Tile::Slice::Dac * val_dac = parentSlice->dac;
  Fabric* fab = parentSlice->parentTile->parentChip->parentFabric;
  adc_code_t codes_self= m_codes;
  dac_code_t codes_dac = val_dac->m_codes;

  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_dac_conns(calib,val_dac);
  cutil::buffer_adc_conns(calib,this);
  cutil::break_conns(calib);
  print_log("backed up connections");

  val_dac->setEnable(true);


  dac_code_t dac_code_0;
  dac_code_t dac_code_1;
  dac_code_t dac_code_neg1;
  util::calib_result_t interim_result;
  util::init_result(interim_result);
  dac_code_0 = cutil::make_val_dac(calib, val_dac,
                                     0.0,
                                     interim_result);

  util::init_result(interim_result);
  dac_code_1 = cutil::make_val_dac(calib, val_dac,
                                   1.0*coeff,
                                   interim_result);

  util::init_result(interim_result);
  dac_code_neg1 = cutil::make_val_dac(calib, val_dac,
                                      -1.0*coeff,
                                      interim_result);


	Connection conn0 = Connection ( parentSlice->dac->out0, in0 );
	conn0.setConn();
	setEnable (true);

  bool found_code=false;
  adc_code_t best_code = m_codes;
  adc_code_t tmp_code = m_codes;
  unsigned char opts[] = {nA100,nA200,nA300,nA400};
  int signs[] = {-1,1};
  print_info("calibrating adc..");
  for(unsigned char fs=0; fs < 4; fs += 1){
    m_codes.lower_fs = opts[fs];
    m_codes.upper_fs = opts[fs];
    for(unsigned char spread=0; spread < 32 && !found_code; spread++){
      for(unsigned char lsign=0; lsign < 2 && !found_code; lsign +=1){
        for(unsigned char usign=0; usign < 2 && !found_code; usign +=1){
          m_codes.lower = 31+spread*signs[lsign];
          m_codes.upper = 31+spread*signs[usign];
          update(m_codes);
          // is this successful
          bool succ = true;
          succ = helper_check_steady(fab,this,val_dac,dac_code_0);
          if(succ)
            succ &= helper_check_steady(fab,this,val_dac,dac_code_1);
          if(succ)
            succ &= helper_check_steady(fab,this,val_dac,dac_code_neg1);

          if(succ){
            sprintf(FMTBUF, "-> fs=%d lower=%d upper=%d",
                    m_codes.lower_fs,m_codes.lower,m_codes.upper);
            print_log(FMTBUF);
            succ &= helper_find_bias_and_nmos(fab,this,val_dac,
                                              dac_code_0,
                                              dac_code_1,
                                              dac_code_neg1,
                                              tmp_code);
          }
          if(succ){
            found_code = true;
            best_code = tmp_code;
          }
        }
      }
    }
  }

	conn0.brkConn();
	val_dac->setEnable(false);


  cutil::restore_conns(calib);
  val_dac->update(codes_dac);

  codes_self.i2v_cal = best_code.i2v_cal;
  codes_self.nmos = best_code.nmos;
  codes_self.lower = best_code.lower;
  codes_self.lower_fs = best_code.lower_fs;
  codes_self.upper = best_code.upper;
  codes_self.upper_fs = best_code.upper_fs;
  update(codes_self);

	// Serial.println("offset settings found");
	return found_code;
}


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
