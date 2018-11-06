#include "Comm.h"
#include <Arduino.h>

#define BUFSIZ 5024
byte INBUF[BUFSIZ];
int WPOS=0;
int RPOS=0;
bool DONE=false;

bool read_mode(){
  return DONE;
}
void reset(){
  DONE = false;
  WPOS = 0;
  RPOS = 0;
}
int write_pos(){
  return WPOS;
}
void listen(){
  if(DONE){
    return;
  }
  while(Serial.available() > 0){
    char recv = Serial.read();
    INBUF[WPOS] = recv;
    WPOS += 1;
    if(recv == '\n' and INBUF[WPOS-2] == '\r'){
      DONE = true;
      RPOS = 0;
      return;
    }
  }
}
void get_input(uint8_t* buf, int n_bytes){
  if(not DONE){
    return;
  }
  int siz = WPOS - RPOS < n_bytes ? WPOS - RPOS : n_bytes;
  for(int idx=0; idx < siz; idx += 1){
    buf[idx] = INBUF[RPOS];
    RPOS += 1;
  }
  if(RPOS == WPOS){
    DONE = false;
    WPOS = 0;
  }

}
void discard_input(int n_bytes){
  if(not DONE){
    return;
  }
  int siz = WPOS - RPOS < n_bytes ? WPOS - RPOS : n_bytes;
  RPOS += siz;
  if(RPOS == WPOS){
    DONE = false;
    WPOS = 0;
  }
}



void read_floats(float * data, int n){
  get_input((byte *) data, n/4);
}

void read_bytes(uint8_t * data, int n){
  get_input(data, n);
}

void discard_bytes(int n){
  discard_input(n);
}
uint8_t read_byte(){
  uint8_t value;
  get_input(&value, 1);
  return value;
}

