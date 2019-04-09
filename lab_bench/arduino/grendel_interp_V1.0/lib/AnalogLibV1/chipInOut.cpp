#include "HCDC_DEMO_API.h"
#include "assert.h"
// y = -0.001592x + 3.267596
// R^2 = 0.999464
#define ALPHA -0.001592251629
#define BETA 3.267596063219
#ifdef _DUE


void Fabric::Chip::Tile::Slice::ChipOutput::analogDist (
                                                        unsigned int n,
                                                        float scale,
                                                        float& mean,
                                                        float& variance
                                                        ) const {


  unsigned long long lsumsq = 0;
  unsigned long lsum = 0;
  unsigned int value;
  for (unsigned int index = 0; index < n; index++) {
    value = ADC->ADC_CDR[ardAnaDiffChan];
    lsum += value;
    lsumsq += value*value;
  }

  float sum = (ALPHA*lsum + BETA*((float) n))/scale;
  float sumsq = (ALPHA*ALPHA*lsumsq + 2.0*ALPHA*BETA*lsum + BETA*BETA*((float) n))/(scale*scale);
  mean = sum/n;
  variance = (sumsq - 2.0*sum*mean +  mean*mean*n)/(n-1);
  assert(variance > 0);
}

/*Measure the reading of an ADC from multiple samples*/
float Fabric::Chip::Tile::Slice::ChipOutput::analogAvg (
                                                        unsigned int samples,
                                                        float scale
                                                        ) const
{

    unsigned long adcSum = 0;
    for (unsigned int index = 0; index < samples; index++) {
        // while ((ADC->ADC_ISR & 0x1000000) == 0);
        adcSum += ADC->ADC_CDR[ardAnaDiffChan];
    }

    float mean = (ALPHA * ((float)adcSum/(float)samples) +  BETA);
    mean = mean / scale;
    return mean;

}
#endif
