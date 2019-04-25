#include "AnalogLib.h"
#include "fu.h"
#include <float.h>
#include "assert.h"
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
namespace binsearch {
  void bin_search(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                  float target,
                  unsigned char lo_code, float lo_error,
                  unsigned char hi_code, float hi_error,
                  unsigned char& curr_code, float& curr_error,
                  meas_method_t method,bool reverse);

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


  void test_iref(unsigned char code){
    assert(code <= 7);
    assert(code >= 0);
  }

  void test_stab(unsigned char code,
                float error,
                bool& calib_failed){
    const float MIN_ERROR = 1e-2;
    Serial.print("AC:>[msg] result! bias_code=");
    Serial.print(code);
    Serial.print(" error=");
    Serial.println(error);
    if(error < MIN_ERROR){
      calib_failed = false;
    }
    else{
      calib_failed = true;
    }
  }

  void test_stab_and_update_nmos(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                                unsigned char code,
                                float error,
                                unsigned char& nmos,
                                bool& new_search,
                                bool& calib_failed)
  {
    new_search = false;
    test_stab(code,error,calib_failed);
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
    fu->setAnaIrefNmos();
  }

  void multi_test_stab_and_update_nmos(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                                unsigned char* codes,
                                float* errors,
                                int n_vals,
                                unsigned char& nmos,
                                bool& new_search,
                                bool& calib_failed)
    {
      new_search = false;
      calib_failed = false;
      float avg_code = 0;
      for(int i = 0; i < n_vals; i+= 1){
        bool this_failed;
        test_stab(codes[i], errors[i], this_failed);
        calib_failed |= this_failed;
        avg_code += codes[i];
      }
      if(not calib_failed){
        return;
      }
      char code = avg_code/n_vals;
      if (code==0 || code==1) {
        if(decrement_iref(nmos)) new_search=true;
        else calib_failed = true;
      }
      else if (code==63 || code==62) {
        if(increment_iref(nmos)) new_search=true;
        else calib_failed = true;
      }
      fu->setAnaIrefNmos();
  }

  bool find_bias_and_nmos(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                          float target,
                          unsigned char & code,
                          unsigned char & nmos,
                          meas_method_t method,
                          bool reverse)
  {
    bool new_search=true;
    bool calib_failed=true;
    float error;
    nmos = 0;
    fu->setAnaIrefNmos();
    while(new_search){
      Serial.print("AC:>[msg] nmos=");
      Serial.println(nmos);
      find_bias(fu,target,code,error,method, reverse);
      test_stab_and_update_nmos(fu,code,error,nmos,
                                new_search,calib_failed);
    }
    return !calib_failed;

  }
  void find_pmos(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                 float target,
                 unsigned char & code,
                 float & error,
                 meas_method_t method,
                 bool reverse)
  {
    // find code.
    error = FLT_MAX;
    bin_search(fu, target, 0, FLT_MAX, 7, FLT_MAX,
               code,error,method,reverse);
  }
  void find_bias(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                 float target,
                 unsigned char & code,
                 float & error,
                 meas_method_t method,
                 bool reverse)
  {
    // find code.
    error = FLT_MAX;
    bin_search(fu, target, 0, FLT_MAX, 63, FLT_MAX,
               code, error,method,reverse);
  }

  float bin_search_meas(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                        meas_method_t method)
  {
    Fabric::Chip::Tile::Slice::ChipAdc* adc;
    switch(method)
      {
      case MEAS_CHIP_OUTPUT:
        return fu->getChip()->tiles[3].slices[2].chipOutput
          ->analogAvg(CAL_REPS,1.0);

      case MEAS_ADC:
        adc = fu;
        return adc->getData();

      default:
        error("unknown measurement method");
      }
    return FLT_MAX;
  }

  bool bin_search_next_code (
                             unsigned char lo_code,
                             float lo_error,
                             unsigned char hi_code,
                             float hi_error,
                             unsigned char & curr_code
                             ) {
    if (lo_code+1==hi_code) {
      if (lo_error<hi_error) curr_code=lo_code;
      else curr_code=hi_code;
      return true;
    } else {
      curr_code = (lo_code + hi_code) / 2;
      return false;
    }
}
  void bin_search(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                  float target,
                  unsigned char lo_code, float lo_error,
                  unsigned char hi_code, float hi_error,
                  unsigned char& curr_code, float& curr_error,
                  meas_method_t method,
                  bool reverse)
  {
    //test if finished
    // parentSlice->parentTile->parentChip->parentFabric
    Fabric* fab = fu->getFabric();
    if (bin_search_next_code(lo_code, lo_error,
                             hi_code, hi_error, curr_code)) return;
    fu->updateFu();
    fab->cfgCommit();
    float meas = bin_search_meas(fu,method);
    float error = fabs(meas-target);
    curr_error = error;

    Serial.print("AC:>[msg] meas=");
    Serial.print(meas);
    Serial.print(" target=");
    Serial.print(target);
    Serial.print(" curr_code=");
    Serial.print(curr_code);
    Serial.print(" min_code=");
    Serial.print(lo_code);
    Serial.print(" max_code=");
    Serial.print(hi_code);
    Serial.print(" min_error=");
    Serial.print(lo_error);
    Serial.print(" max_error=");
    Serial.print(hi_error);
    Serial.print(" error=");
    Serial.println(error);
    if((meas > target && !reverse) ||
       (meas < target && reverse)) {
      return bin_search(fu,target,
                        lo_code, lo_error,
                        curr_code, curr_error,
                        curr_code, curr_error,
                        method, reverse);

    }
    else {
      return bin_search( fu, target,
                         curr_code, curr_error,
                         hi_code, hi_error,
                         curr_code, curr_error,
                         method,reverse);
    }

  }

}

/*
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
  updateFu();
  //setAnaIrefPmos ();
	//setParam1 ();
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

  finalError = error;
	//if ( (voltageDiff*target<0) || (fabs(target*FULL_SCALE)<fabs(voltageDiff)) ) {
  if(voltageDiff > target) {
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
  parentFu->updateFu();
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
bool fabric::chip::tile::slice::functionunit::binarysearchavg (
	unsigned char mincode,
	float minbest,
	unsigned char maxcode,
	float maxbest,
	unsigned char & finalcode
) const {
//        serialusb.print(" mincode ");
//        serialusb.print(mincode);
//        serialusb.print(" maxcode ");
//        serialusb.println(maxcode);
	if (mincode+1==maxcode) {
		if (minbest<maxbest) finalcode=mincode;
		else finalcode=maxcode;
		return true;
	} else {
		finalcode = (maxcode + mincode) / 2;
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



*/
