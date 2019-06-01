#include "AnalogLib.h"
#include "assert.h"
// y = -0.001592x + 3.267596
// R^2 = 0.999464
#ifdef _DUE

// for single-ended channels
#define ADC_CONVERSION (3300.0/4096.0)
//#define ADC_FULLSCALE (1208.0)

//should be 1208, but it isn't for some reason.
#define ADC_FULLSCALE (1000.0)
#define ADC_MIN 0

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
    int diff = pos[index] - neg[index];
    float value = ADC_CONVERSION*((float)(diff));
    value /= ADC_FULLSCALE;
    values[index] = value;
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
  float pos_mv = ADC_CONVERSION * ((float)adcPos/(float)samples);
  float neg_mv = ADC_CONVERSION * ((float)adcNeg/(float)samples);
  float value = (pos_mv-neg_mv)/ADC_FULLSCALE;
  sprintf(FMTBUF,"chan=%d pos=%f neg=%f diff=%f val=%f", ardAnaDiffChan,
          pos_mv, neg_mv,pos_mv-neg_mv,value);
  print_debug(FMTBUF);
  return value;
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
