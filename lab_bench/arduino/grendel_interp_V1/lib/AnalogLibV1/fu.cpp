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

  void init_result(util::calib_result_t& result){
    result.size = 0;
    for(int i=0; i < MAX_KEYS; i += 1){
      result.port[i] = 0;
      result.noise[i] = 0.0;
      result.bias[i] = 0.0;
      result.target[i] = 0.0;
    }
  }

  void print_result(util::calib_result_t& result, int level){
    for(int i=0; i < result.size; i+= 1){
      sprintf("port=%s target=%f bias=%f noise=%f", result.port[i],
              result.target[i],result.bias[i],result.noise[i]);
      print_level(FMTBUF,level);
    }

  }
  void add_prop(util::calib_result_t& result,
                ifc prop, float target, float bias, float noise){
    if(result.size >= MAX_KEYS){
      sprintf(FMTBUF,
              "cutil::add_prop: no more space left for prop: %d/%d",
              result.size, MAX_KEYS);
      error(FMTBUF);
    }
    result.port[result.size] = prop;
    result.bias[result.size] = bias;
    result.noise[result.size] = noise;
    result.target[result.size] = target;
    sprintf(FMTBUF, "add-prop prop=%d bias=%f noise=%f target=%f",
            prop,bias,noise,target);
    print_log(FMTBUF);
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


  float meas_adc(Fabric::Chip::Tile::Slice::ChipAdc* fu){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    return fu->getData();
  }


  float meas_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    float value = fu->getChip()->tiles[3].slices[2].chipOutput
      ->analogAvg();
    return value;
  }


  void meas_dist_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                     float& mean, float& variance){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    fu->getChip()->tiles[3].slices[2].chipOutput
      ->analogDist(mean,variance);
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
                 const float max_error,
                 bool& calib_failed){
    //const float MIN_ERROR = 1e-2;
    sprintf(FMTBUF,
            "result: bias=%d error=%f max-error=%f",
            code, error, max_error);
    print_debug(FMTBUF);
    if(fabs(error) <= max_error){
      calib_failed = false;
    }
    else{
      calib_failed = true;
    }
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


  float bin_search_meas(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                        meas_method_t method)
  {
    switch(method)
      {
      case MEAS_CHIP_OUTPUT:
        return util::meas_chip_out(fu);

      case MEAS_ADC:
        return util::meas_adc(fu);

      default:
        error("unknown measurement method");
      }
    return FLT_MAX;
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

  float get_bias(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                 float target,
                 meas_method_t method)
  {
    // find code.
    return bin_search_meas(fu,method)-target;
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
      deltas[code-min_code] = bin_search_meas(fu,method)-target;

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
