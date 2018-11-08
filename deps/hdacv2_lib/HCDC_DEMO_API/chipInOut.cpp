#include "HCDC_DEMO_API.h"

/*Measure the reading of an ADC from multiple samples*/
float Fabric::Chip::Tile::Slice::ChipOutput::analogAvg (
        unsigned int samples
) const {

    // y = -0.001592x + 3.267596
    // R^2 = 0.999464

    unsigned long adcSum = 0;
    for (unsigned int index = 0; index < samples; index++) {
#ifdef _DUE
        // while ((ADC->ADC_ISR & 0x1000000) == 0);
        adcSum += ADC->ADC_CDR[ardAnaDiffChan];
#endif
    }

    return ( -0.001592251629 * ((float)adcSum/(float)samples) + 3.267596063219 );

}