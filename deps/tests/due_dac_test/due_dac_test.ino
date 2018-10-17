#include <DueTimer.h>
#include "Experiment.h"

const float DELAY_TIME_US= 10.0;

int exp_idx = 0;
volatile int idx = 0;
const int N = 10000;
int WF1[N];
int WF2[N];
experiment_t * EXPERIMENTS;
int N_EXPERIMENTS;

void setup() {
  Serial.begin(115200);
  // put your setup code here, to run once:
  analogWriteResolution(12);  // set the analog output resolution to 12 bit (4096 levels)
  Serial.println("> initialized");
  Serial.print("external trigger: ");
  Serial.println(SDA);
  pinMode(SDA, OUTPUT);
  experiments_stateless_1inp();
  
}

void experiments_stateless_1inp(){
  N_EXPERIMENTS = 1;
  EXPERIMENTS = (experiment_t*) malloc(sizeof(experiment_t)*N_EXPERIMENTS);

  for(int idx=0; idx < N_EXPERIMENTS; idx+=1){
    init_experiment(&EXPERIMENTS[idx]);
    EXPERIMENTS[idx].num_signals = 1;
  }
  
  // constant 0 signal
  idx = 0;
  experiment_t * exp;
  exp = &EXPERIMENTS[idx];
  sig_add_sin(exp->sig1, NUM_SUBSIGS, 1.0, 0.0, 1.0);

  idx += 1;
  exp = &EXPERIMENTS[idx];

  idx += 1;
  exp = &EXPERIMENTS[idx];
  sig_add_const(exp->sig1, NUM_SUBSIGS, 1.0);

  idx += 1;
  exp = &EXPERIMENTS[idx];
  sig_add_const(exp->sig1, NUM_SUBSIGS, -1.0);

  idx += 1;
  exp = &EXPERIMENTS[idx];
  sig_add_sin(exp->sig1, NUM_SUBSIGS, 1.0, 0.0, 1.0);

  idx += 1;
  exp = &EXPERIMENTS[idx];
  sig_add_sin(exp->sig1, NUM_SUBSIGS, 10.0, 0.0, 1.0);

  idx += 1;
  exp = &EXPERIMENTS[idx];
  sig_add_sin(exp->sig1, NUM_SUBSIGS, 0.1, 0.0, 1.0);

  idx += 1;
  exp = &EXPERIMENTS[idx];
  sig_add_sin(exp->sig1, NUM_SUBSIGS, 1.0, 45, 1.0);

  idx += 1;
  exp = &EXPERIMENTS[idx];
  sig_add_sin(exp->sig1, NUM_SUBSIGS, 1.0, 90, 1.0);

  idx += 1;
  exp = &EXPERIMENTS[idx];
  sig_add_sin(exp->sig1, NUM_SUBSIGS, 1.0, 120, 1.0);

  idx += 1;
  exp = &EXPERIMENTS[idx];
  sig_add_sin(exp->sig1, NUM_SUBSIGS, 1.0, 0.0, 0.5);



}
void setup_experiment(experiment_t * experiment){
  idx = 0;
  if(experiment->num_signals == 1){
     write_signal(WF1,N,experiment->sig1,NUM_SUBSIGS);
     Timer3.attachInterrupt(update_wave_1);
  }
  else if(experiment->num_signals == 2){
     write_signal(WF1,N,experiment->sig1,NUM_SUBSIGS);
     write_signal(WF2,N,experiment->sig2,NUM_SUBSIGS);
     Timer3.attachInterrupt(update_wave_2);
  }
  else {
     Serial.print("unknown number of signals:");
     Serial.println(experiment->num_signals);
  }
  
}
void loop() {
  // build sin
  setup_experiment(&EXPERIMENTS[exp_idx]);
  digitalWrite(SDA,LOW);
  while(Serial.available() == 0) {
      Serial.println("press enter to continue..");
      delay(300);
  }
  while(Serial.available() > 0) {
      Serial.read(); 
  }
  Serial.println("executing..");
  delay(300);

  Timer3.start(DELAY_TIME_US);
  while(idx < N){
      delayMicroseconds(1000);
  }
  Timer3.detachInterrupt();
  Serial.println("executed..");
  delay(300);
  exp_idx = (exp_idx+1) % N_EXPERIMENTS;
  
}

void update_wave_1() {
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
void update_wave_2() {
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

