#include "Comm.h"
#include <Arduino.h>

namespace comm {
  
#define BUFSIZ 1024

byte INBUF[BUFSIZ];
int WPOS=0;
int RPOS=0;
int MSGNO = 0;
int TRYNO = 0;
bool DONE=false;


bool read_mode(){
  return DONE;
}
void header(){
  Serial.print("\nAC:>");
}
void print_header(){
  header();
  Serial.print("[msg]");
}
void listen_command(){
  header();
  Serial.print("[listen]");
  Serial.print(" pos=");
  Serial.print(write_pos());
  Serial.print(" msg#=");
  Serial.println(MSGNO);
}
void process_command(){
  header();
  Serial.println("[process]");
}
void done_command(){
  header();
  Serial.println("[done]");
}

void payload(){
  header();
  Serial.print("[array]");
}
void data(const char * msg,const char * type_sig){
  header();
  Serial.print("[data][");
  Serial.print(type_sig);
  Serial.print("] ");  
  Serial.println(msg);
}
void response(const char * msg,int args){
  header();
  Serial.print("[resp][");
  Serial.print(args);
  Serial.print("]");
  Serial.println(msg);
}
void error(const char * msg){
  while(1){
     header();
     Serial.print("[error]");
     Serial.println(msg);
     delay(100);
  }
}
void reset(){
  DONE = false;
  WPOS = 0;
  RPOS = 0;
}
int write_pos(){
  return WPOS;
}
#define MAX_TRIES 10000
void listen(){
  if(DONE){
    print_header();
    Serial.println("<found endline>");
    return;
  }

  if(TRYNO % MAX_TRIES == 0){ 
     comm::listen_command();
  }
  TRYNO += 1;
  while(Serial.available() > 0){
    char recv = Serial.read();
    INBUF[WPOS] = recv;
    WPOS += 1;
    if(recv == '\n' and INBUF[WPOS-2] == '\r'){
      DONE = true;
      RPOS = 0;
      WPOS -= 2;
      MSGNO += 1;
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

}
