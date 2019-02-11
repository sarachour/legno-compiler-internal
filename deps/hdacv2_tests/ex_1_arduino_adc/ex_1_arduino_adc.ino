#include <DueTimer.h>
/*
 * adc 0,2 : chip 0, positive adc0, adc1
 * adc 1,3 : chip 0, negative adc0, adc1
 * adc 4,6 : chip 1, positive adc0, adc1
 * adc 5,7 : chip 1, negative adc0, adc1
 */
// counter for how many samples that have been tajen
volatile unsigned short timeIndex = 0;

//maximum number of samples
const unsigned short timeSize = 256

//buffer to store the samples
volatile unsigned short adcCode[timeSize];

//timer delay between ADC samples
const float delayTimeMicroseconds = 1;

void setup() {
  // put your setup code here, to run once:
  Timer3.attachInterrupt(write_adc_outputs);  
}

void configure() {
  // put your configuration here.
  
}
void loop() {
  // put your main code here, to run repeatedly:
  configure()
  fabric->cfgStop();
  Timer3.start(delayTimeMicroseconds);

  //start integration routine
  fabric->execStart();
  while (timeIndex != timeSize) {};
  // stop integration routine
  fabric->execStop();
  for(int i=0; i < timeSize; i++){
     float value = adcCodeToVal(adcCode[i]);
     SerialUSB.println(value)
  }
}

void write_adc_outputs(){
  adcCode[timeIndex] = ADC=>ADC_CDR[6];
  timeIndex  ++;
  if (timeIndex == timeSize){
     Timer3.stop()
  }
}


