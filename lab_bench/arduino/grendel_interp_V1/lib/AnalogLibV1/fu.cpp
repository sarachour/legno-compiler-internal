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

  void init_result(util::calib_result_t& result,
                   float max_error, bool succ){
    result.success = succ;
    result.size = 0;
    result.max_error = max_error;
  }

  void print_result(util::calib_result_t& result, int level){
    sprintf(FMTBUF,"success=%s", result.success ? "y" : "n");
    print_level(FMTBUF, level);
    sprintf(FMTBUF,"max-err=%f", result.max_error);
    print_level(FMTBUF, level);
    print_level("=== props ===", level);
    for(int i=0; i < result.size; i+= 1){
      sprintf("  port=%s target=%f error=%f", result.props[i],
              result.targets[i],result.errors[i]);
      print_level(FMTBUF,level);
    }

  }
  void add_prop(util::calib_result_t& result,
                ifc prop, float target, float bias){
    if(!result.size < MAX_KEYS){
      error("cutil::add_prop: no more space left for prop");
    }
    result.props[result.size] = prop;
    result.errors[result.size] = bias;
    result.targets[result.size] = target;
    result.size += 1;
  }

  const char * ifc_to_string(ifc id){
    return "?";
  }

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


  float measure_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    float value = fu->getChip()->tiles[3].slices[2].chipOutput
      ->analogAvg(CAL_REPS);
    return value;
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
                 const float min_error,
                 bool& calib_failed){
    //const float MIN_ERROR = 1e-2;
    sprintf(FMTBUF,
            "result: bias=%d error=%f max-error=%f",
            code, error, min_error);
    print_debug(FMTBUF);
    if(fabs(error) <= min_error){
      calib_failed = false;
    }
    else{
      calib_failed = true;
    }
  }

  void test_stab_and_update_nmos(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                                 unsigned char code,
                                 float error,
                                 const float max_error,
                                 unsigned char& nmos,
                                 bool& new_search,
                                 bool& calib_failed)
  {
    new_search = false;
    test_stab(code,error,max_error,calib_failed);
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
                       const float max_error,
                       int n_vals,
                       bool& calib_failed)
  {
    calib_failed = false;
    for(int i = 0; i < n_vals; i+= 1){
      bool this_failed;
      test_stab(codes[i], errors[i], max_error, this_failed);
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
                                       const float max_error,
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
        test_stab(codes[i], errors[i], max_error, this_failed);
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
                          const float max_error,
                          unsigned char & code,
                          unsigned char & nmos,
                          float & delta,
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

      test_stab(codes[nmos],deltas[nmos],max_error,calib_failed);
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
    delta = deltas[best_nmos];
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
          ->analogAvg(CAL_REPS);
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


  }

}
