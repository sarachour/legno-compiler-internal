#include <DueTimer.h>
#include "Experiment.h"
#include "Comm.h"
#include "Circuit.h"

experiment::experiment_t this_experiment;
Fabric * fabric;

typedef enum cmd_type {
    CIRC_CMD,
    EXPERIMENT_CMD,
    FLUSH_CMD
} cmd_type_t;


typedef union cmd_data {
  experiment::cmd_t exp_cmd;
  circ::cmd_t circ_cmd;
  char flush_cmd;
} cmd_data_t;

typedef struct cmd_{
  uint8_t type;
  cmd_data_t data;
} cmd_t;

void setup() {
  Serial.begin(115200);
  Serial.flush();
  experiment::setup_experiment();
  
}

void loop() {
  if(read_mode()){
    cmd_t cmd;
    int nbytes = read_bytes((byte *) &cmd,sizeof(cmd_t));
    float * inbuf = NULL;
    Serial.print(nbytes);
    Serial.print("/");
    Serial.print(sizeof(cmd_t));
    Serial.print("  ");
    for(int idx=0; idx < nbytes; idx += 1){
      Serial.print(((byte*) &cmd)[idx]);
      Serial.print(",");
    }
    Serial.println("::process::");
    switch(cmd.type){
      case cmd_type_t::CIRC_CMD:
        circ::print_command(cmd.data.circ_cmd);
        break;
      case cmd_type_t::EXPERIMENT_CMD:
        inbuf = (float*) get_data_ptr(nbytes);
        experiment::print_command(cmd.data.exp_cmd,inbuf);
        break;
      case cmd_type_t::FLUSH_CMD:
        Serial.println("::flush::");
        break;
      default:
        Serial.print(cmd.type);
        Serial.println(" <unknown>");
        break;
    }
    reset();
  }
  else{
    Serial.print(write_pos());
    Serial.println("::listen::");
    listen();
    delay(30);
  }
  
  
  
}


