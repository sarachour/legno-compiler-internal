#include "include/Pin.h"
#include "include/Logger.h"

namespace pin {

void setup_pins(){
  pinMode(PIN_ctrRst, OUTPUT);
	pinMode(PIN_spiClk, OUTPUT);
	pinMode(PIN_spiMosi, OUTPUT);
	pinMode(PIN_moMiEn, OUTPUT);

	digitalWrite(PIN_moMiEn, LOW);

  for(int i=0; i < 2; i+=1){
    pinMode(PIN_chipSel[i], OUTPUT);
    pinMode(PIN_rowSel[i], OUTPUT);
    pinMode(PIN_colSel[i], OUTPUT);
  }
  /*ANALOG INPUT CHANNEL ENABLE PINS*/
  for(int i=0; i < 4; i+=1){
    pinMode(PIN_anaEn[i], OUTPUT);
    digitalWrite(PIN_anaEn[i], LOW);
  }
  pinMode(PIN_tdiClk, OUTPUT);
  for(int i=0; i < 8; i+=1){
    pinMode(PIN_tdi[i], OUTPUT);
  }
  pinMode(PIN_tdoClk, INPUT);
  for(int i=0; i < 8; i+=1){
    pinMode(PIN_tdo[i], INPUT);
  }
}

void setup_io(){
#ifdef _DUE
  analogReadResolution(12);
  analogWriteResolution(12);
#else
  analogReference(DEFAULT);
#endif
	randomSeed(analogRead(0));
	// Set up ADC
	ADC->ADC_MR |= 0x80; // set free running mode on ADC
	ADC->ADC_MR &= 0xFFFF00FF; // set prescaler to fastest
	ADC->ADC_COR = 0x10000; // enable differential ADC for all channels
	ADC->ADC_CHER = 0x55; // enable four pairs of differential ADC
	adc_enable_interrupt(ADC, ADC_IER_DRDY);
	ADC->ADC_IER |= 0x55; // enable ADC interrupt on pin A0
	while ((ADC->ADC_ISR & 0x1000000) == 0);
}

  void setup(){
    setup_pins();
    setup_io();
  }

int get_due_adc_index(unsigned char chip,unsigned char tile,unsigned char slice){
  for(int i=0; i < 4; i+=1){
     if(chip == PIN_anaLoc[i][0] &&
        tile == PIN_anaLoc[i][1] &&
        slice == PIN_anaLoc[i][2])
     {
        return i;
     }
  }
  return -1;
}

void enable_due_adc_pin(unsigned char chip,unsigned char tile,unsigned char slice){
   int idx= get_due_adc_index(chip,tile,slice);
   if(idx < 0){
      return;
   }
   digitalWrite(PIN_anaEn[idx], HIGH);
}

float read_extern(unsigned char chip,
                  unsigned char tile,
                  unsigned char slice,
                  unsigned int samples,
                  float scale){

  int idx= get_due_adc_index(chip,tile,slice);
  if(idx < 0){
    return -1.0;
  }
  int pin = PIN_anaOut[idx];
  unsigned long adcSum = 0;
  for (unsigned int index = 0; index < samples; index++) {
    // while ((ADC->ADC_ISR & 0x1000000) == 0);
    adcSum += ADC->ADC_CDR[pin];
  }

  float mean = (ALPHA * ((float)adcSum/(float)samples) +  BETA);
  mean = mean / scale;
  return mean;
}

void read_extern2(unsigned char chip,
                  unsigned char tile,
                  unsigned char slice,
                  unsigned int n,
                  float scale,
                  float& mean,
                  float& variance
                  ) {
  int idx= get_due_adc_index(chip,tile,slice);
  if(idx < 0){
    return;
  }
  int pin = PIN_anaOut[idx];

  unsigned long long lsumsq = 0;
  unsigned long lsum = 0;
  unsigned int value;
  for (unsigned int index = 0; index < n; index++) {
    value = ADC->ADC_CDR[pin];
    lsum += value;
    lsumsq += value*value;
  }

  float sum = (ALPHA*lsum + BETA*((float) n))/scale;
  float sumsq = (ALPHA*ALPHA*lsumsq + 2.0*ALPHA*BETA*lsum + BETA*BETA*((float) n))/(scale*scale);
  mean = sum/n;
  variance = (sumsq - 2.0*sum*mean +  mean*mean*n)/(n-1);
  logger::assert(variance > 0, "variance must be positive");
}

void reset(){
  DigitalWriteP(PIN_ctrRst, HIGH);
  DigitalWriteP(PIN_ctrRst, LOW);
}

}
