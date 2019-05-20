#include "AnalogLib.h"
#include "fu.h"
#include <float.h>
#include "assert.h"

namespace util {

  bool is_valid_iref(unsigned char code){
    return (code <= 7 && code >= 0);
  }

  void test_iref(unsigned char code){
    assert(is_valid_iref(code));
  }

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


  void distribution(float* values, int samples,
                     float& mean, float & variance){
    mean = 0.0;
    for(unsigned int index = 0; index < samples; index++){
      mean += values[index];
    }
    mean /= (float) samples;
    variance = 0.0;
    for(unsigned int index=0; index < samples; index++){
      variance += pow((values[index] - mean),2.0);
    }
    variance /= (float) (samples-1);
  }

  void meas_dist_adc(Fabric::Chip::Tile::Slice::ChipAdc* fu,
                      float& mean, float& variance){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    float meas[SAMPLES];
    for(unsigned int i=0; i < SAMPLES; i += 1){
      meas[i] = (float) fu->getData();
    }
    distribution(meas, SAMPLES, mean, variance);
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
