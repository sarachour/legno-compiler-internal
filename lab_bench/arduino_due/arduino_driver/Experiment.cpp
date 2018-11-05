#include "math.h"
#include "Experiment.h"
#include "Arduino.h"
#include "Comm.h"
#include <assert.h>

namespace experiment {

volatile int IDX;
int N;
int N_OSC;
const float DELAY_TIME_US= 10.0;
volatile int SDA_VAL = LOW;
experiment_t* EXPERIMENT;
Fabric* FABRIC;


inline void save_adc_value(experiment_t * expr, byte index){
   expr->adc_pos[index][IDX] = ADC->ADC_CDR[0+(index<<1)];
   expr->adc_neg[index][IDX] = ADC->ADC_CDR[1+(index<<1)];
}
inline void write_dac0_value(experiment_t * expr){
  analogWrite(DAC0, expr->dac[0][IDX]); 
}
inline void write_dac1_value(experiment_t * expr){
  analogWrite(DAC1, expr->dac[1][IDX]); 
}
inline void _toggle_SDA(){
  SDA_VAL = SDA_VAL == HIGH ? LOW : HIGH;
  digitalWrite(SDA,SDA_VAL);
}
inline void drive_sda_clock(){
   if(IDX % N_OSC == 0 or IDX >= N){
      _toggle_SDA();
  }
}
void _update_wave(){
  for(int idx = 0; idx < 4; idx+=1){
    save_adc_value(EXPERIMENT,idx);
  }
  write_dac0_value(EXPERIMENT);  
  write_dac1_value(EXPERIMENT);
  drive_sda_clock();
  if(IDX >= N){
      Timer3.detachInterrupt();
      if(EXPERIMENT->use_analog_chip){
        circ::finish(FABRIC);
      }
      return;
  }
  // increment index
  IDX += 1;
}

void attach_interrupts(experiment_t * experiment, Fabric * fab){
  FABRIC = fab;
  EXPERIMENT = experiment;
  Timer3.attachInterrupt(_update_wave);

}

void setup_experiment() {
  pinMode(SDA, OUTPUT);
  // put your setup code here, to run once:
  analogWriteResolution(12);  // set the analog output resolution to 12 bit (4096 levels)
  Serial.print("external trigger: ");
  Serial.println(SDA);
  
}

// maximum number of samples per acquire.
#define OSC_SAMPLES 100000


void set_dac_value(experiment_t * expr, byte dac_id,int sample,float data){
   unsigned short value = (short) (value*2048 + 2048);
   expr->dac[dac_id][sample] = value;
}
void enable_adc(experiment_t * expr, byte adc_id){
  expr->use_adc[adc_id] = true;
}
void enable_oscilloscope(experiment_t * expr){
  expr->use_osc = true;
}
void enable_dac(experiment_t * expr, byte dac_id){
  expr->use_dac[dac_id] = true;
}
short* get_adc_values(experiment_t * expr, byte adc_id, int& num_samples){
  return NULL;
}
void reset_experiment(experiment_t * expr){
  expr->use_analog_chip = true;
  expr->n_adc_samples = 0;
  for(int idx = 0; idx < 2; idx+=1 ){
    expr->use_dac[idx] = false;
    expr->n_dac_samples[idx] = 0;
  }
  for(int idx = 0; idx < 4; idx+=1 ){
    expr->use_adc[idx] = false;
  }
  expr->use_osc = false;
  for(int i=0; i < MAX_SIZE; i+=1){
    for(int idx=0; idx < 4; idx +=1){
      expr->adc_pos[idx][i] = 0;
      expr->adc_neg[idx][i] = 0;
    }
    for(int idx=0; idx < 2; idx +=1){
      expr->dac[idx][i] = 0;
    }
  }
}
void run_experiment(experiment_t * expr, Fabric * fab){
  IDX = 0;
  N = expr->n_adc_samples;
  N_OSC = OSC_SAMPLES/DELAY_TIME_US;
  // trigger the start of the experiment
  attach_interrupts(expr,fab);
  if(expr->use_analog_chip){
    circ::finalize_config(fab);
    _toggle_SDA();
    circ::execute(fab);
  }
  else{
    _toggle_SDA();
  }
  Timer3.start(DELAY_TIME_US);
  while(IDX < N){
      delayMicroseconds(1000);
  }
  Timer3.detachInterrupt();
  Serial.println("::done::");
}


void exec_command(experiment_t* expr, Fabric * fab, cmd_t& cmd){
  float data[4096];
  int n;
  switch(cmd.type){
    case cmd_type_t::RESET:
      reset_experiment(expr);
      break;
    case cmd_type_t::RUN:
      run_experiment(expr,fab);
      break;
    case cmd_type_t::USE_ANALOG_CHIP:
      enable_analog_chip(expr);
      break;
    case cmd_type_t::USE_DAC:
      enable_dac(expr,cmd.args[0]);
      break;
    case cmd_type_t::USE_ADC:
      enable_adc(expr,cmd.args[0]);
      break;
    case cmd_type_t::USE_OSC:
      enable_oscilloscope(expr);
      break;
    case cmd_type_t::SET_N_ADC_SAMPLES:
      expr->n_adc_samples = cmd.args[0];
      break;
      
    case cmd_type_t::SET_DAC_VALUES:
      assert(cmd.args[1] <= 4096);
      read_floats(data,cmd.args[1]);
      for(int idx = 0; idx < cmd.args[1]; idx+=1){
        set_dac_value(expr, cmd.args[0], idx + cmd.args[2], data[idx]);
      }
      if(cmd.args[2] + cmd.args[1] > expr->n_dac_samples[cmd.args[0]]){
        expr->n_dac_samples[cmd.args[0]] = cmd.args[2] + cmd.args[1];
      }
      break;

    case cmd_type_t::GET_ADC_VALUES:
      Serial.println("> TODO: implement");
      break;
  }
}


void print_command(cmd_t& cmd){
  switch(cmd.type){
    default:
      Serial.println("<unimpl>");
  }
}

}


