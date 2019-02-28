#include "HCDC_DEMO_API.h"
#include <float.h>

bool Fabric::Chip::Tile::Slice::FunctionUnit::findBiasHelper (
	float target,
	unsigned char & code
) {
//        SerialUSB.print("anaIrefDacNmos = ");
//        SerialUSB.println(anaIrefDacNmos);
	binarySearchTarget ( target, 0, FLT_MAX, 63, FLT_MAX, code );

//        SerialUSB.print("\ntile row ");
//        SerialUSB.print(parentSlice->parentTile->tileRowId);
//        SerialUSB.print(" tile col ");
//        SerialUSB.print(parentSlice->parentTile->tileColId);
//        SerialUSB.print(" slice ");
//        SerialUSB.print(parentSlice->sliceId);
//        SerialUSB.print(" unit ");
//        SerialUSB.print(unitId);
//        SerialUSB.print(" code ");
//        SerialUSB.println(code);

	if (code==0 || code==1) {
		if (setAnaIrefDacNmos(true, false)) return false;
	} else if (code==63 || code==62) {
		if (setAnaIrefDacNmos(false, true)) return false;
	}
	return true;
}

bool Fabric::Chip::Tile::Slice::FunctionUnit::Interface::findBiasHelper (
	unsigned char & code
) const {
	binarySearch ( 0, FLT_MAX, 63, FLT_MAX, code );

//        SerialUSB.print("\ntile row ");
//        SerialUSB.print(parentFu->parentSlice->parentTile->tileRowId);
//        SerialUSB.print(" tile col ");
//        SerialUSB.print(parentFu->parentSlice->parentTile->tileColId);
//        SerialUSB.print(" slice ");
//        SerialUSB.print(parentFu->parentSlice->sliceId);
//        SerialUSB.print(" unit ");
//        SerialUSB.print(parentFu->unitId);
//        SerialUSB.print(" ifc ");
//        SerialUSB.print(ifcId);
//        SerialUSB.print(" code ");
//        SerialUSB.println(code);

	if (code==0 || code==1) {
		// bipolar so if running out of code also increase
		parentFu->setAnaIrefDacNmos(false, true);
		return false;
	} else if (code==63 || code==62) {
		parentFu->setAnaIrefDacNmos(false, true);
		return false;
	} else {
		return true;
	}
}

void Fabric::Chip::Tile::Slice::FunctionUnit::binarySearchTarget (
	float target,
	unsigned char minGainCode,
	float minBest,
	unsigned char maxGainCode,
	float maxBest,
	unsigned char & finalGainCode
) const {
	if (binarySearchAvg (minGainCode, minBest, maxGainCode, maxBest, finalGainCode)) return;
	setAnaIrefPmos ();
	setParam1 ();
	parentSlice->parentTile->parentChip->parentFabric->cfgCommit();
	float voltageDiff = binarySearchMeas ();
	if ( (voltageDiff*target<0) || (fabs(target*FULL_SCALE)<fabs(voltageDiff)) ) {
		return binarySearchTarget ( target, minGainCode, minBest, finalGainCode, fabs(voltageDiff-target), finalGainCode );
	} else {
		return binarySearchTarget ( target, finalGainCode, fabs(voltageDiff-target), maxGainCode, maxBest, finalGainCode );
	}
}

void Fabric::Chip::Tile::Slice::FunctionUnit::Interface::binarySearch (
	unsigned char minOffsetCode,
	float minBest,
	unsigned char maxOffsetCode,
	float maxBest,
	unsigned char & finalOffsetCode
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
	if (ifcId==in0Id) parentFu->parentSlice->parentTile->parentChip->parentFabric->execStop();
	if (0.0<voltageDiff) {
		return binarySearch ( minOffsetCode, minBest, finalOffsetCode, fabs(voltageDiff), finalOffsetCode );
	} else {
		return binarySearch ( finalOffsetCode, fabs(voltageDiff), maxOffsetCode, maxBest, finalOffsetCode );
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
