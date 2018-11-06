#include <DueTimer.h>
#include "Experiment.h"
#include "Comm.h"
#include "Circuit.h"

experiment::experiment_t this_experiment;
Fabric * fabric;

typedef enum cmd_type {
    CIRC_CMD,
    EXPERIMENT_CMD
} cmd_type_t;


typedef union cmd_data {
  experiment::cmd_t exp_cmd;
  circ::cmd_t circ_cmd;
} cmd_data_t;

typedef struct cmd_{
  cmd_type_t type;
  cmd_data_t data;
} cmd_t;

void setup() {
  Serial.begin(115200);
  Serial.flush();
  experiment::setup_experiment();
  
}

void loop() {
  if(read_mode()){
    Serial.println("::process::");
    cmd_t cmd;
    read_bytes((byte *) &cmd,sizeof(cmd_t));
  
    switch(cmd.type){
      case cmd_type_t::CIRC_CMD:
        circ::print_command(cmd.data.circ_cmd);
        break;
      case cmd_type_t::EXPERIMENT_CMD:
        experiment::print_command(cmd.data.exp_cmd);
        break;
      default:
        Serial.println("unknown...");
        break;
    }
    reset();
  }
  else{
    Serial.print(write_pos());
    Serial.println("::listen::");
    listen();
    delay(300);
  }
  
  
  
}


