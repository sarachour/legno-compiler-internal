#include "AnalogLib.h"
#include "fu.h"
#include <float.h>
#include "assert.h"

namespace util {

  /* validity testing */
  bool is_valid_iref(unsigned char code){
    return (code <= 7 && code >= 0);
  }

  void test_iref(unsigned char code){
    assert(is_valid_iref(code));
  }

  const char * ifc_to_string(ifc id){
    return "?";
  }

  /* helper functions for building block functions */
  float sign_to_coeff(bool inv){
    return inv ? -1.0 : 1.0;
  }
  range_t range_to_dac_range(range_t rng){
    switch(rng){
    case RANGE_LOW:
      return RANGE_MED;
    case RANGE_MED:
      return RANGE_MED;
    case RANGE_HIGH:
      return RANGE_HIGH;
    }
    error("unknown range");
    return RANGE_UNKNOWN;
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


  void linear_regression(float* times, float * values, int n,
                         float& alpha, float& beta ,float& Rsquare,
                         float& max_error,float& avg_error){
    float avg_time,avg_value,dummy;
    distribution(times,n,avg_time,dummy);
    distribution(values,n,avg_value,dummy);
    float slope_numer=0.0;
    float slope_denom=0.0;
    for(int i=0; i < n; i += 1){
      slope_numer += (times[i]-avg_time)*(values[i]-avg_value);
      slope_denom += (times[i]-avg_time)*(times[i]-avg_time);
    }
    alpha = slope_numer/slope_denom;
    beta = avg_value - alpha*avg_time;

    float SSRES = 0.0;
    float SSTOT = 0.0;
    avg_error = 0.0;
    max_error = 0.0;
    for(int i=0; i < n; i += 1){
      float pred = alpha*times[i]+beta;
      SSRES += pow(values[i]-pred,2);
      SSTOT += pow(values[i]-avg_value,2);
      float this_error = fabs(pred-values[i]);
      avg_error += this_error;
      max_error = max(max_error,this_error);
    }
    avg_error = avg_error/((float) n);
    Rsquare = 1.0 - SSRES/SSTOT;
  }
  int find_maximum(float* values, int n){
    int best_index=0;
    assert(n >= 1);
    for(int i=0; i < n; i+=1){
      if(values[i] > values[best_index]){
        best_index = i;
      }
    }
    return best_index;
  }
  int find_minimum(float* values, int n){
    int best_index=0;
    assert(n >= 1);
    for(int i=0; i < n; i+=1){
      if(values[i] < values[best_index]){
        best_index = i;
      }
    }
    return best_index;
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


  float meas_max_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu,int n){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    float value = fu->getChip()->tiles[3].slices[2].chipOutput
      ->analogMax(n);
    return value;
  }


  float meas_fast_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    float value = fu->getChip()->tiles[3].slices[2].chipOutput
      ->fastAnalogAvg();
    return value;
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

  int meas_transient_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                               float * times, float* values,
                               int samples){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    int n = fu->getChip()->tiles[3].slices[2].chipOutput
      ->analogSeq(times,values,samples);
    for(int i=0; i < n; i += 1){
      sprintf(FMTBUF," t=%f v=%f", times[i], values[i]);
      print_info(FMTBUF);
    }
    return n;
  }
  void meas_steady_chip_out(Fabric::Chip::Tile::Slice::FunctionUnit* fu,
                            float& mean, float& variance){
    Fabric* fab = fu->getFabric();
    fu->updateFu();
    fab->cfgCommit();
    fab->execStart();
    //wait for one millisecond.
    delay(3);
    fu->getChip()->tiles[3].slices[2].chipOutput
      ->analogDist(mean,variance);
    fab->execStop();
  }
}
