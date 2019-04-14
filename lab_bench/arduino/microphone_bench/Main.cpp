#include "Arduino.h"
/****************************************
Example Sound Level Sketch for the 
Adafruit Microphone Amplifier
****************************************/

int trigPin = 11;    // Trigger
int echoPin = 12;    // Echo
long duration;

void setup()
{
   Serial.begin(9600);
   analogWriteResolution(12);
   pinMode(trigPin, OUTPUT);
   pinMode(echoPin, INPUT);
}

void echo(){
  digitalWrite(trigPin, LOW);
  delayMicroseconds(5);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  pinMode(echoPin, INPUT);
  duration = pulseIn(echoPin, HIGH);
  Serial.println(duration);
  delay(2500);
}
void loop()
{
  analogWrite(DAC0, 2037);
  echo();
}
