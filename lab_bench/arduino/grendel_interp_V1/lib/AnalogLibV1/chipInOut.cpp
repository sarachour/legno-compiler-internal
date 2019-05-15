#include "AnalogLib.h"
#include "assert.h"
// y = -0.001592x + 3.267596
// R^2 = 0.999464
#ifdef _DUE

// for differential channels
#define ALPHA -0.001592251629
#define BETA 3.267596063219

// for single-ended channels
#define ADC_CONVERSION (3300.0/4096.0)
//#define ADC_FULLSCALE (1208.0)

//should be 1208, but it isn't for some reason.
#define ADC_FULLSCALE (1000.0)
#define ADC_MIN 0

void Fabric::Chip::Tile::Slice::ChipOutput::analogDist (
                                                        unsigned int n,
                                                        float& mean,
                                                        float& variance
                                                        ) const {


  error("FIXME: reimplement");
}

float single_ended(int ardAnaDiffChan, unsigned int samples){
  unsigned long adcPos = 0;
  unsigned long adcNeg = 0;
  unsigned int pinmap[] = {7,6,5,4,3,2,1,0};
  //                      {n,p,n,p,n,p,n,p}
  /*
    A0 A1 A2 A3 A4 A5 A6 A7
    N  P  N  P  N  P  N  P
    7  6  5  4  3  2  1  0
   */
  /*
  for (unsigned int index = 0; index < samples; index++) {
    while ((ADC->ADC_ISR & 0x1000000) == 0);

    // ADC_CDR[7] = A0
    // ADC_CDR[6] = A1
    adcPos += ADC->ADC_CDR[ardAnaDiffChan+1];
    adcNeg += ADC->ADC_CDR[ardAnaDiffChan];
  }
  */
  samples = 10;
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
  if(neg_mv < ADC_MIN){
    sprintf(FMTBUF, "broken negative channel [%d,%d] %f",
            ardAnaDiffChan,
            ardAnaDiffChan+1,
            neg_mv);
    error(FMTBUF);
  }
  if(pos_mv < ADC_MIN){
    sprintf(FMTBUF, "broken positive channel [%d,%d] %f",
            ardAnaDiffChan,
            ardAnaDiffChan+1,
            pos_mv);
    error(FMTBUF);
  }
  return value;
}
float differential(int ardAnaDiffChan, unsigned int samples){
  unsigned long adcDiff = 0;
  for (unsigned int index = 0; index < samples; index++) {
    // while ((ADC->ADC_ISR & 0x1000000) == 0);
    adcDiff += ADC->ADC_CDR[ardAnaDiffChan];
  }
  float value = ALPHA*((float)adcDiff/(float)samples)+BETA;
  return value;
}
/*Measure the reading of an ADC from multiple samples*/
float Fabric::Chip::Tile::Slice::ChipOutput::analogAvg (unsigned int samples) const
{
  //return differential(ardAnaDiffChan, samples);
  return single_ended(ardAnaDiffChan, samples);
}
#endif
