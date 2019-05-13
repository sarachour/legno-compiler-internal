#include "AnalogLib.h"
#include "assert.h"
// y = -0.001592x + 3.267596
// R^2 = 0.999464
#ifdef _DUE

// for differential channels
#define ALPHA -0.001592251629
#define BETA 3.267596063219

// for single-ended channels
#define ADC_RESOLUTION (3300.0/4096.0)
#define ADC_FULLSCALE (1208.0)
#define ADC_MIN 50

void Fabric::Chip::Tile::Slice::ChipOutput::analogDist (
                                                        unsigned int n,
                                                        float& mean,
                                                        float& variance
                                                        ) const {


  unsigned long long neg_sumsq,pos_sumsq = 0;
  unsigned long neg_sum,pos_sum = 0;
  unsigned int neg_val,pos_val;
  for (unsigned int index = 0; index < n; index++) {
    pos_val = ADC->ADC_CDR[ardAnaDiffChan];
    neg_val = ADC->ADC_CDR[ardAnaDiffChan+1];
    pos_sum += pos_val;
    pos_sumsq += pos_val*pos_val;
    neg_sum += neg_val;
    neg_sumsq += neg_val*neg_val;
  }

  /*
  float scale = ADC_FULLSCALE;
  float sum = (ALPHA*lsum + BETA*((float) n))/scale;
  float sumsq = (ALPHA*ALPHA*lsumsq + 2.0*ALPHA*BETA*lsum + BETA*BETA*((float) n))/(scale*scale);
  mean = sum/n;
  variance = (sumsq - 2.0*sum*mean +  mean*mean*n)/(n-1);
  assert(variance > 0);
  */
  error("FIXME: reimplement");
}

float single_ended(int ardAnaDiffChan, unsigned int samples){
  unsigned long adcPos = 0;
  unsigned long adcNeg = 0;
  for (unsigned int index = 0; index < samples; index++) {
    // while ((ADC->ADC_ISR & 0x1000000) == 0);

    // ADC_CDR[7] = A0
    // ADC_CDR[6] = A1
    adcPos += ADC->ADC_CDR[ardAnaDiffChan+1];
    adcNeg += ADC->ADC_CDR[ardAnaDiffChan];
  }
  float pos_mv = ADC_RESOLUTION * ((float)adcPos/(float)samples);
  float neg_mv = ADC_RESOLUTION * ((float)adcNeg/(float)samples);
  float value = (pos_mv-neg_mv)/ADC_FULLSCALE;
  //sprintf(FMTBUF,"chan=%d pos=%f neg=%f diff=%f", ardAnaDiffChan,
  //        pos_mv, neg_mv,value);
  //print_debug(FMTBUF);
  if(neg_mv < ADC_MIN){
    sprintf(FMTBUF, "broken negative channel [%d,%d]",
            ardAnaDiffChan,
            ardAnaDiffChan+1);
    error(FMTBUF);
  }
  if(pos_mv < ADC_MIN){
    sprintf(FMTBUF, "broken positive channel [%d,%d]",
            ardAnaDiffChan,
            ardAnaDiffChan+1);
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
