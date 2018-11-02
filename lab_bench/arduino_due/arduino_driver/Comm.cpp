#include "Comm.h"
#include <Arduino.h>

void get_input(uint8_t* buf, int n_bytes){
  int idx = 0;

  while(true){ 
    while(Serial.available() == 0) {
         delay(300);
    }
    while(Serial.available() > 0) {
         byte b = Serial.read(); 
         buf[idx] = b;
         idx += 1;
         if(idx == n_bytes){
           return;
         }
     }
   }
}


void read_floats(float * data, int n){
  get_input((byte *) data, n/4);
}

void read_bytes(uint8_t * data, int n){
  get_input(data, n);
}

uint8_t read_byte(){
  uint8_t value;
  get_input(&value, 1);
  return value;
}

