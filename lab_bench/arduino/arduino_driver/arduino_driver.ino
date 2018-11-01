#include <DueTimer.h>
#include "Experiment.h"

const float DELAY_TIME_US= 10.0;

volatile int idx = 0;
const int N = 10000;
int WF1[N];
int WF2[N];

experiment_t experiment;


void setup() {
  Serial.begin(115200);
  // put your setup code here, to run once:
  analogWriteResolution(12);  // set the analog output resolution to 12 bit (4096 levels)
  Serial.println("> initialized");
  Serial.print("external trigger: ");
  Serial.println(SDA);
  pinMode(SDA, OUTPUT);
  
}
void get_input(byte* buf, int n_bytes){
  int idx = 0;

  while(true){ 
    Serial.println("need_bytes:");
    Serial.println(n_bytes);
    while(Serial.available() == 0) {
        delay(300);
   }
   while(Serial.available() > 0) {
        byte b = Serial.read(); 
        buf[idx] = b;
        idx += 1;
        Serial.print("  ->");
        Serial.print(idx);
        Serial.print("/");
        Serial.println(n_bytes);
        if(idx == n_bytes){
          return;
        }
    }
  }
}

// commands
// 0 <dac_id> 0 <ampl>: dc signal.
// 0 <dac_id> 1 <ampl> <freq> <phase> : sin wave
// 1 <circ_id>: set circuit config
// 2 <arg_id> <arg_value> : set circuit argument 
// 3: start_experiment
// 4: clear_experiment
// 5: quit

void dac_subcommand_handler(){
  byte args[2];
  get_input(args,2);
  int dac_id = args[0];
  byte shape = args[1];
  switch(shape){
    case 0:
      Serial.println("dc");
      break;
    case 1:
      Serial.println("sin");
      break;
    default:
      Serial.println("unknown");
      exit(1);
  }
  
}
void circ_subcommand_handler(){
  byte arg;
  get_input(&arg,1);
  
}
void arg_subcommand_handler(){
  byte arg_id;
  int value;
  get_input(&arg_id,1);
  get_input((byte*) &value,4);
  
}


void _update_wave_1() {
  if(idx == N)  {
     analogWrite(DAC0, 0);  // write the selected waveform on DAC0
     return;
  }
  analogWrite(DAC0, WF1[idx]);  // write the selected waveform on DAC0
 
  idx++;
  if(idx == N) {
     digitalWrite(SDA,LOW);
  }
  else if(idx > N/2){
     digitalWrite(SDA,HIGH);
  }
}
void _update_wave_2() {
  if(idx == N)  {
     analogWrite(DAC0, 0); 
     analogWrite(DAC1, 0); 
     return;
  }
  // 0.825 volts
  analogWrite(DAC0, WF1[idx]);  // write the selected waveform on DAC0
  analogWrite(DAC1, WF2[idx]);  // write the selected waveform on DAC1
 
  idx++;
  if(idx == N) {
     digitalWrite(SDA,LOW);
  }
  else if(idx > N/2){
     digitalWrite(SDA,HIGH);
  }
  
}

void _setup_experiment(){
  idx = 0;
  compile_experiment(&experiment);
  if(experiment.num_signals == 0){
     return;
  }
  else if(experiment.num_signals == 1){
     write_signal(WF1,N,experiment.sig1,NUM_SUBSIGS);
     Timer3.attachInterrupt(_update_wave_1);
  }
  else if(experiment.num_signals == 2){
     write_signal(WF1,N,experiment.sig1,NUM_SUBSIGS);
     write_signal(WF2,N,experiment.sig2,NUM_SUBSIGS);
     Timer3.attachInterrupt(_update_wave_2);
  }
  else {
     Serial.print("unknown number of signals:");
     Serial.println(experiment.num_signals);
     exit(1);
  } 
}
void clear_experiment(){
  init_experiment(&experiment);
}
void run_experiment(){
  _setup_experiment();
  // trigger the start of the experiment
  digitalWrite(SDA,LOW);
  Timer3.start(DELAY_TIME_US);
  while(idx < N){
      delayMicroseconds(1000);
  }
  Timer3.detachInterrupt();
}
void command_interp(){
  byte cmd;
  get_input(&cmd, 1);
  switch(cmd){
    case 0:
      Serial.println("dac cmd");
      dac_subcommand_handler();
      break;
    case 1:
      Serial.println("circ cmd");
      circ_subcommand_handler();
      break;
    case 2:
      Serial.println("arg cmd");
      arg_subcommand_handler();
      break;
    case 3:
      Serial.println("run cmd");
      run_experiment();
      break;
    case 4:
      Serial.println("clear cmd");
      clear_experiment();
      break;
    case 5:
      Serial.println("quit cmd");
      exit(0);
      break;
    case 6:
      Serial.println("read cmd");
      break;
      
    default:
      Serial.println("unknown command. exiting.");
      exit(1);
  }
  
}





void loop() {
  while(true){
      command_interp();
  }
}


