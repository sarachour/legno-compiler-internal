#include "AnalogLib.h"
#include "fu.h"
#include <float.h>
#include "assert.h"


char FMTBUF[64];

void Fabric::Chip::Tile::Slice::FunctionUnit::updateFu(){
  setAnaIrefNmos();
  setAnaIrefPmos();
  setParam0();
  setParam1();
  setParam2();
  setParam3();
  setParam4();
  setParam5();
}

namespace util{
  float range_to_coeff(range_t rng){
    switch(rng){
    case RANGE_LOW:
      return 0.1;
    case RANGE_MED:
      return 1.0;
    case RANGE_HIGH:
      return 10.0;
    }
    error("unknown range");
    return -1.0;
  }
}
namespace binsearch {
  void bin_search(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                  float target,
                  unsigned char min_code,
                  unsigned char max_code,
                  unsigned char& curr_code, float& curr_error,
                  meas_method_t method);
  float bin_search_get_delta(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                             float target,
                             meas_method_t method,
                             float& delta);

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

  bool is_valid_iref(unsigned char code){
    return (code <= 7 && code >= 0);
  }



  void test_iref(unsigned char code){
    assert(is_valid_iref(code));
  }

  void test_stab(unsigned char code,
                float error,
                bool& calib_failed){
    const float MIN_ERROR = 1e-2;
    sprintf(FMTBUF,
            "result: bias=%d error=%f max-error=%f",
            code, error, MIN_ERROR);
    print_debug(FMTBUF);
    if(fabs(error) < MIN_ERROR){
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
    if(!new_search){
      calib_failed = true;
      }
    fu->setAnaIrefNmos();
  }

  void multi_test_stab(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                                       unsigned char* codes,
                                       float* errors,
                                       int n_vals,
                                       bool& calib_failed)
  {
    calib_failed = false;
    for(int i = 0; i < n_vals; i+= 1){
      bool this_failed;
      test_stab(codes[i], errors[i], this_failed);
      calib_failed |= this_failed;
    }
  }

  int get_nmos_delta(unsigned char code){
    if(code == 0 || code == 1){
      return -1;
    }
    else if(code == 63 || code == 62){
      return 1;
    }
    return 0;
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
      if(!new_search){
        calib_failed = true;
      }
      fu->setAnaIrefNmos();
  }

  bool find_bias_and_nmos(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                          float target,
                          unsigned char & code,
                          unsigned char & nmos,
                          meas_method_t method)
  {
    bool calib_failed=true;
    float deltas[8];
    unsigned char codes[8];
    nmos = 0;
    for(nmos=0; nmos < 8; nmos += 1){
      float delta;
      sprintf(FMTBUF, "find nmos=%d",nmos);
      print_debug(FMTBUF);
      //compute bias
      fu->setAnaIrefNmos();
      find_bias(fu,target,code,delta,method);
      codes[nmos] = code;
      deltas[nmos] = delta;

      test_stab(codes[nmos],deltas[nmos],calib_failed);
      if(!calib_failed){
        return true;
      }
    }
    unsigned char best_nmos = 0;
    float best_delta = deltas[0];
    for(int i=1; i < 8; i += 1){
      if(fabs(deltas[i]) < fabs(best_delta)){
        best_nmos = i;
      }
    }
    code = codes[best_nmos];
    nmos = best_nmos;
    fu->setAnaIrefNmos();
    fu->updateFu();
    fu->getFabric()->cfgCommit();
    return !calib_failed;

  }
  void find_pmos(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                 float target,
                 unsigned char & code,
                 float & error,
                 meas_method_t method)
  {
    // find code.
    error = FLT_MAX;
    bin_search(fu, target,0,7,code,error,method);
  }
  void find_bias(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                 float target,
                 unsigned char & code,
                 float & error,
                 meas_method_t method)
  {
    // find code.
    error = FLT_MAX;
    bin_search(fu,target,0,63,code,error,method);
  }

  float bin_search_meas(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                        meas_method_t method)
  {
    Fabric::Chip::Tile::Slice::ChipAdc* adc;
    float value;
    switch(method)
      {
      case MEAS_CHIP_OUTPUT:
        value = fu->getChip()->tiles[3].slices[2].chipOutput
          ->analogAvg(CAL_REPS,1.0);
        //value /= FULL_SCALE;
        return value;

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

  float bin_search_get_delta(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                           float target,
                           meas_method_t method,
                           float& delta)
  {
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    float meas = bin_search_meas(fu,method);
    delta = meas-target;
  }

  void bin_search(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                   float target,
                   unsigned char min_code, unsigned char max_code,
                   unsigned char& curr_code, float& curr_delta,
                   meas_method_t method)
  {
    //local minima finding array.
    float deltas[64];
    for(unsigned char code=min_code; code <= max_code; code+=1){
      float delta;
      curr_code = code;
      bin_search_get_delta(fu,target,method,delta);
      deltas[code-min_code] = delta;
    }

    unsigned char best_code = min_code;
    float best_delta = deltas[0];
    for(int code=min_code+1; code <= max_code; code+=1){
      float delta = deltas[code-min_code];
      if(fabs(delta) < fabs(best_delta)){
        best_code = code;
        best_delta = delta;
      }
    }
    curr_code = best_code;
    curr_delta = best_delta;
    sprintf(FMTBUF, "BEST code=%d delta=%f",curr_code,curr_delta);
    print_debug(FMTBUF);


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
