#include <DueTimer.h>
#include "Experiment.h"
#include "Comm.h"
#include "Circuit.h"
#include "assert.h"

experiment::experiment_t this_experiment;
Fabric * this_fabric;

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
  uint8_t test;
  uint8_t type;
  cmd_data_t data;
} cmd_t;

void setup() {
  this_fabric = circ::setup_board();
  Serial.begin(115200);
  Serial.flush();
  experiment::setup_experiment();
  
}

void loop() {
  if(read_mode()){
    cmd_t cmd;
    int nbytes = read_bytes((byte *) &cmd,sizeof(cmd_t));
    float * inbuf = NULL;
    bool debug = cmd.test == 0 ? false : true;
    Serial.println("::process::");
    switch(cmd.type){
      case cmd_type_t::CIRC_CMD:
        assert(this_fabric != NULL);
        if(!debug){
          circ::print_command(cmd.data.circ_cmd);
          circ::exec_command(this_fabric,cmd.data.circ_cmd);
        }
        else{
          Serial.print("DEBUG:");
          circ::print_command(cmd.data.circ_cmd);
          Serial.println(0);
        }
        break;
      case cmd_type_t::EXPERIMENT_CMD:
        inbuf = (float*) get_data_ptr(nbytes);
        if(!debug){
          experiment::print_command(cmd.data.exp_cmd,inbuf);
          experiment::exec_command(&this_experiment,this_fabric,cmd.data.exp_cmd,inbuf);
        }
        else{
          Serial.print("DEBUG:");
          experiment::print_command(cmd.data.exp_cmd,inbuf);
          Serial.println(0);
        }
        // in the event the fabric has not been initialized, initialize it
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


