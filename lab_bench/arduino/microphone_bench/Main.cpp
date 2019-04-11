#include "Arduino.h"
/****************************************
Example Sound Level Sketch for the 
Adafruit Microphone Amplifier
****************************************/

void setup()
{
   Serial.begin(9600);
   analogWriteResolution(12);
}

void loop()
{
  analogWrite(DAC0, 2037);
}
