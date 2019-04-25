#include "AnalogLib.h"
#include "fu.h"
#include <float.h>
#include "assert.h"

bool decrement_iref(uint8_t& code){
  if (code==0) return false; // error ("Bias already set to extreme value");
  else code--;
  return true;
}
bool increment_iref(uint8_t& code){
  if (code==7) return false; // error ("Bias already set to extreme value");
  else code++;
  return true;
}
void Fabric::Chip::Tile::Slice::FunctionUnit::updateFu(){
  setAnaIrefPmos();
  setAnaIrefNmos();
  setParam0();
  setParam1();
  setParam2();
  setParam3();
  setParam4();
  setParam5();
}

void Fabric::Chip::Tile::Slice::FunctionUnit::testIref(unsigned char code) const{
  assert(code <= 7);
  assert(code >= 0);
}
void Fabric::Chip::Tile::Slice::FunctionUnit::testStab(unsigned char code,
                                                       unsigned char nmos,
                                                       float error,
                                                       bool& calib_failed) const{
  const float MIN_ERROR = 1e-2;
  Serial.print("AC:>[msg] result! bias_code=");
  Serial.print(code);
  Serial.print(" nmos_code=");
  Serial.print(nmos);
  Serial.print(" error=");
  Serial.println(error);
  if(error < MIN_ERROR){
    calib_failed = false;
  }
  else{
    calib_failed = true;
  }
}
void Fabric::Chip::Tile::Slice::FunctionUnit::testStabAndUpdateNmos(
                                                                    unsigned char code,
                                                                    unsigned char& nmos,
                                                                    float error,
                                                                    bool& new_search,
                                                                    bool& calib_failed)
{
  new_search = false;
  testStab(code,nmos,error,calib_failed);
  if(not calib_failed){
    return;
  }
  if (code==0 || code==1) {
    if(decrement_iref(nmos)) new_search=true;
    else calib_failed = true;
	} else if (code==63 || code==62) {
		if(increment_iref(nmos)) new_search=true;
    else calib_failed = true;
	}
}
void Fabric::Chip::Tile::Slice::FunctionUnit::findBiasHelper (
	float target,
	unsigned char & code,
  unsigned char & nmos,
  bool& new_search,
  bool& calib_failed
) {
  float error = FLT_MAX;
	binarySearchTarget ( target, 0, FLT_MAX, 63, FLT_MAX, code, error);
  testStabAndUpdateNmos(code,nmos,error,new_search,calib_failed);
  setAnaIrefNmos();
}

void Fabric::Chip::Tile::Slice::FunctionUnit::Interface::findBiasHelper (
                                                                         unsigned char & code,
                                                                         unsigned char & nmos,
                                                                         bool& new_search,
                                                                         bool& calib_failed
) const {
  // find code.
  float error = FLT_MAX;
	binarySearch ( 0, FLT_MAX, 63, FLT_MAX, code, error);
  parentFu->testStabAndUpdateNmos(code,nmos,error,new_search,calib_failed);
  parentFu->setAnaIrefNmos();
}

void Fabric::Chip::Tile::Slice::FunctionUnit::binarySearchTarget (
	float target,
	unsigned char minGainCode,
	float minBest,
	unsigned char maxGainCode,
	float maxBest,
	unsigned char & finalGainCode,
  float& finalError
) const {
	if (binarySearchAvg (minGainCode, minBest, maxGainCode, maxBest, finalGainCode)) return;
	setAnaIrefPmos ();
	setParam1 ();
	parentSlice->parentTile->parentChip->parentFabric->cfgCommit();
	float voltageDiff = binarySearchMeas ();
  float error = fabs(voltageDiff-target);
  finalError = error;
  Serial.print("AC:>[msg] meas=");
	Serial.print(voltageDiff);
  Serial.print(" target=");
	Serial.print(target);
  Serial.print(" curr_code=");
	Serial.print(finalGainCode);
  Serial.print(" min_code=");
	Serial.print(minGainCode);
  Serial.print(" max_code=");
	Serial.print(maxGainCode);
  Serial.print(" min_error=");
	Serial.print(minBest);
  Serial.print(" max_error=");
	Serial.print(maxBest);
  Serial.print(" error=");
	Serial.println(error);

	//if ( (voltageDiff*target<0) || (fabs(target*FULL_SCALE)<fabs(voltageDiff)) ) {
  if(voltageDiff >= target) {
		return binarySearchTarget ( target,
                                minGainCode, minBest,
                                finalGainCode, error,
                                finalGainCode, finalError);
	} else {
		return binarySearchTarget ( target,
                                finalGainCode, error,
                                maxGainCode, maxBest,
                                finalGainCode, finalError);
	}
}

void Fabric::Chip::Tile::Slice::FunctionUnit::Interface::binarySearch (
	unsigned char minOffsetCode,
	float minBest,
	unsigned char maxOffsetCode,
	float maxBest,
	unsigned char & finalOffsetCode,
  float& finalError
) const {
	if (binarySearchAvg (minOffsetCode, minBest, maxOffsetCode, maxBest, finalOffsetCode)) return;
	parentFu->setParam0();
	parentFu->setParam1();
	parentFu->setParam2();
	parentFu->setParam3();
	parentFu->setParam4();
	parentFu->setParam5();
	parentFu->parentSlice->parentTile->parentChip->parentFabric->cfgCommit();
	if (ifcId==in0Id) parentFu->parentSlice->parentTile->parentChip->parentFabric->execStart();
	float voltageDiff = binarySearchMeas();
  float error = fabs(voltageDiff);
  finalError = error;
	if (ifcId==in0Id) parentFu->parentSlice->parentTile->parentChip->parentFabric->execStop();
	if (0.0<voltageDiff) {
		return binarySearch ( minOffsetCode, minBest,
                          finalOffsetCode, error,
                          finalOffsetCode, finalError);
	} else {
		return binarySearch ( finalOffsetCode, error,
                          maxOffsetCode, maxBest,
                          finalOffsetCode, finalError);
	}
}

bool Fabric::Chip::Tile::Slice::FunctionUnit::binarySearchAvg (
	unsigned char minCode,
	float minBest,
	unsigned char maxCode,
	float maxBest,
	unsigned char & finalCode
) const {
//        SerialUSB.print(" minCode ");
//        SerialUSB.print(minCode);
//        SerialUSB.print(" maxCode ");
//        SerialUSB.println(maxCode);
	if (minCode+1==maxCode) {
		if (minBest<maxBest) finalCode=minCode;
		else finalCode=maxCode;
		return true;
	} else {
		finalCode = (maxCode + minCode) / 2;
		return false;
	}
}

bool Fabric::Chip::Tile::Slice::FunctionUnit::Interface::binarySearchAvg (
	unsigned char minCode,
	float minBest,
	unsigned char maxCode,
	float maxBest,
	unsigned char & finalCode
) const {
//        SerialUSB.print(" minCode ");
//        SerialUSB.print(minCode);
//        SerialUSB.print(" maxCode ");
//        SerialUSB.println(maxCode);
	if (minCode+1==maxCode) {
		if (minBest<maxBest) finalCode=minCode;
		else finalCode=maxCode;
		return true;
	} else {
		finalCode = (maxCode + minCode) / 2;
		return false;
	}
}

float Fabric::Chip::Tile::Slice::FunctionUnit::binarySearchMeas () const {
	float voltageDiff = parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->analogAvg(CAL_REPS,1.0);
//        SerialUSB.print(" voltageDiff ");
//        SerialUSB.println(voltageDiff, 6);
	return voltageDiff;
}

float Fabric::Chip::Tile::Slice::FunctionUnit::Interface::binarySearchMeas () const {
	float voltageDiff = parentFu->parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->analogAvg(CAL_REPS,1.0);
//        SerialUSB.print(" voltageDiff ");
//        SerialUSB.println(voltageDiff, 6);
	return voltageDiff;
}

/*
bool Fabric::Chip::Tile::Slice::FunctionUnit::setAnaIrefDacNmosHelper (
	bool decrement,
	bool increment
) {
	if (decrement&&increment) {
		error ("Cannot both increment and decrement");
		return false;
	} else if (decrement) {
		if (anaIrefDacNmos==0) return false; // error ("Bias already set to extreme value");
		else anaIrefDacNmos--;
	} else if (increment) {
		if (anaIrefDacNmos==7) return false; // error ("Bias already set to extreme value");
		else anaIrefDacNmos++;
	}

//        SerialUSB.print("anaIrefDacNmos = ");
//        SerialUSB.println(anaIrefDacNmos);
	return true;
}
*/
