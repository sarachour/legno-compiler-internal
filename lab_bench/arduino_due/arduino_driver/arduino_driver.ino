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


void setup() {
  Serial.begin(115200);
  Serial.flush();
  experiment::setup_experiment();
  
}

void loop() {
  cmd_type_t cmd_type = (cmd_type_t) read_byte();
  circ::cmd_t circ_cmd;
  experiment::cmd_t exp_cmd;
  
  switch(cmd_type){
    case cmd_type_t::CIRC_CMD:
      Serial.println("circuit command");
      read_bytes((byte*) &circ_cmd, sizeof(circ::cmd_t));
      circ::print_command(circ_cmd);
      break;
    case cmd_type_t::EXPERIMENT_CMD:
      Serial.println("experiment command");
      read_bytes((byte*) &exp_cmd, sizeof(experiment::cmd_t));
      experiment::print_command(exp_cmd);
      break;
  }
  
}


