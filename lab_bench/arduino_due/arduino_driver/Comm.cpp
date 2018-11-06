#include "Comm.h"
#include <Arduino.h>

#define BUFSIZ 1024
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
    Serial.println("<found endline>");
    return;
  }
  while(Serial.available() > 0){
    char recv = Serial.read();
    INBUF[WPOS] = recv;
    WPOS += 1;
    if(recv == '\n' and INBUF[WPOS-2] == '\r'){
      DONE = true;
      RPOS = 0;
      WPOS -= 2;
      return;
    }
  }
}

void* get_data_ptr(int offset){
   return &INBUF[offset];
}
int get_input(uint8_t* buf, int n_bytes){
  if(not DONE){
    return -1;
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
  return siz;

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



int read_floats(float * data, int n){
  return get_input((byte *) data, n*4);
}

int read_bytes(uint8_t * data, int n){
  return get_input(data, n);
}

void discard_bytes(int n){
  discard_input(n);
}
uint8_t read_byte(){
  uint8_t value;
  get_input(&value, 1);
  return value;
}

