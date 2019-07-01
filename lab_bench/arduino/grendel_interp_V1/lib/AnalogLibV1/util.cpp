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
    variance /= (float) (samples);
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

  void meas_trend_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    fab->execStart();
    fu->getChip()->tiles[3].slices[2].chipOutput
      ->analogTrend();
    fab->execStop();
  }
}
