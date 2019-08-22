#include "AnalogLib.h"
#include "assert.h"
// y = -0.001592x + 3.267596
// R^2 = 0.999464
#ifdef _DUE

// for single-ended channels
#define ADC_CONVERSION (3300.0/4096.0)
// computed regression for ARDV -> OSCV: = 0.9888*V_ard - 0.0201
// R^2 = 0.99902
// ===== FULLSCALE =====
#define ADC_FULLSCALE (1208.0)

inline float to_diff_voltage(int pos, int neg){
  float pos_mV = pos*ADC_CONVERSION;
  float neg_mV = neg*ADC_CONVERSION;
  float value = (pos_mV - neg_mV);
  float scaled_value = value/ADC_FULLSCALE;

  /*
  sprintf(FMTBUF,"pos=%d/%f neg=%d/%f diff=%f/%f",
          pos,pos_mV,
          neg,neg_mV,
          value,scaled_value);
  print_info(FMTBUF);
  */
  return scaled_value;
}
void measure_seq(int ardAnaDiffChan,float* times, float* values, int n){
  unsigned long codes[SAMPLES];
  unsigned int pos[SAMPLES];
  unsigned int neg[SAMPLES];
  const unsigned int samples = SAMPLES;
  unsigned int pinmap[] = {7,6,5,4,3,2,1,0};
  for(unsigned int index = 0; index < SAMPLES; index++){
    pos[index] = analogRead(pinmap[ardAnaDiffChan+1]);
    neg[index] = analogRead(pinmap[ardAnaDiffChan]);
    codes[index] = micros();
  }
  unsigned int base_time = codes[0];
  assert(n <= SAMPLES);
  for(unsigned int index = 0; index < n; index++){
    values[index] = to_diff_voltage(pos[index],neg[index]);
    times[index] = (codes[index]-base_time)*1e-6;
  }
}
float measure_dist(int ardAnaDiffChan, float& variance){
  unsigned int pos[SAMPLES];
  unsigned int neg[SAMPLES];
  const unsigned int samples = SAMPLES;
  unsigned int pinmap[] = {7,6,5,4,3,2,1,0};
  for(unsigned int index = 0; index < SAMPLES; index++){
    pos[index] = analogRead(pinmap[ardAnaDiffChan+1]);
    neg[index] = analogRead(pinmap[ardAnaDiffChan]);
  }

  float values[SAMPLES];
  for(unsigned int index = 0; index < SAMPLES; index++){
    values[index] = to_diff_voltage(pos[index],neg[index]);
  }
  float mean;
  util::distribution(values, SAMPLES, mean, variance);

  sprintf(FMTBUF,"chan=%d mean=%f var=%f", ardAnaDiffChan,
          mean,variance);
  print_debug(FMTBUF);
  return mean;
}



float measure(int ardAnaDiffChan){
  unsigned long adcPos = 0;
  unsigned long adcNeg = 0;
  unsigned int pinmap[] = {7,6,5,4,3,2,1,0};
  //                      {n,p,n,p,n,p,n,p}
  /*
    A0 A1 A2 A3 A4 A5 A6 A7
    P  N  P  N  P  N  P  N
    7  6  5  4  3  2  1  0
  */
  const unsigned int samples = SAMPLES;
  for(unsigned int index = 0; index < samples; index++){
    adcPos += analogRead(pinmap[ardAnaDiffChan+1]);
    adcNeg += analogRead(pinmap[ardAnaDiffChan]);
  }
  float pos = ((float)adcPos/(float)samples);
  float neg = ((float)adcNeg/(float)samples);
  float value = to_diff_voltage(pos,neg);
  return value;
}
void Fabric::Chip::Tile::Slice::ChipOutput::analogSeq(
                                                        float* times,
                                                        float* values,
                                                        int n
                                                        ) const {


  measure_seq(ardAnaDiffChan,times,values,n);
}
void Fabric::Chip::Tile::Slice::ChipOutput::analogDist (
                                                        float& mean,
                                                        float& variance
                                                        ) const {


  mean = measure_dist(ardAnaDiffChan,variance);
}


/*Measure the reading of an ADC from multiple samples*/
float Fabric::Chip::Tile::Slice::ChipOutput::analogAvg () const
{
  return measure(ardAnaDiffChan);
}
#endif
