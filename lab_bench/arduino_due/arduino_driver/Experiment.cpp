#include "math.h"
#include "Experiment.h"
#include "Arduino.h"
#include "Circuit.h"
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
// maximum number of samples per acquire.
#define OSC_SAMPLES 1000


inline void save_adc0_value(experiment_t * expr, int idx){
  short value = ADC->ADC_CDR[6] - ADC->ADC_CDR[7];
  expr->databuf[expr->adc_offsets[0]+idx] = value;
}
inline void save_adc1_value(experiment_t * expr, int idx){
  short value = ADC->ADC_CDR[4] - ADC->ADC_CDR[5];
  expr->databuf[expr->adc_offsets[1]+idx] = value;
}
inline void save_adc2_value(experiment_t * expr, int idx){
  short value = ADC->ADC_CDR[2] - ADC->ADC_CDR[3];
  expr->databuf[expr->adc_offsets[2]+idx] = value;
}
inline void save_adc3_value(experiment_t * expr, int idx){
  short value = ADC->ADC_CDR[0] - ADC->ADC_CDR[1];
  expr->databuf[expr->adc_offsets[3]+idx] = value;
}

inline void write_dac0_value(experiment_t * expr, int idx){
  analogWrite(DAC0, expr->databuf[expr->dac_offsets[0] + idx]); 
}
inline void write_dac1_value(experiment_t * expr, int idx){
  analogWrite(DAC1, expr->databuf[expr->dac_offsets[1] + idx]); 
}
inline void _toggle_SDA(){
  SDA_VAL = SDA_VAL == HIGH ? LOW : HIGH;
  digitalWrite(SDA,SDA_VAL);
}
inline void drive_sda_clock(int idx){
   if(idx % N_OSC == 0 or idx >= N){
      _toggle_SDA();
  }
}
void _update_wave(){
  int idx = IDX;
  if(EXPERIMENT->use_adc[0])
    save_adc0_value(EXPERIMENT,idx);
  
  if(EXPERIMENT->use_adc[1])
    save_adc1_value(EXPERIMENT,idx);
  
  if(EXPERIMENT->use_adc[2])
    save_adc2_value(EXPERIMENT,idx);
  
  if(EXPERIMENT->use_adc[3])
    save_adc3_value(EXPERIMENT,idx);
    
  if(EXPERIMENT->use_dac[0])
    write_dac0_value(EXPERIMENT,idx);  
    
  if(EXPERIMENT->use_dac[1])
    write_dac1_value(EXPERIMENT,idx);
    
  drive_sda_clock(idx);
  IDX = idx+1;
  // increment index
}


void setup_experiment() {
  pinMode(SDA, OUTPUT);
  // put your setup code here, to run once:
  analogWriteResolution(12);  // set the analog output resolution to 12 bit (4096 levels)
  //Serial.print("external trigger: ");
  //Serial.println(SDA);
  
}



void enable_adc(experiment_t * expr, byte adc_id){
  expr->use_adc[adc_id] = true;
}
void enable_oscilloscope(experiment_t * expr){
  expr->use_osc = true;
}
void enable_analog_chip(experiment_t * expr){
  expr->use_analog_chip = true;
}
void enable_dac(experiment_t * expr, byte dac_id){
  expr->use_dac[dac_id] = true;
}

void print_adc_values(experiment_t * expr, int adc_id, int nels, int offset){
  int n = nels ? nels + offset < expr->n_samples : expr->n_samples - (nels+offset);
  Serial.print(n);
  int adc_offset = expr->adc_offsets[adc_id];
  if(adc_offset >= 0 and expr->compute_offsets){
    for(int idx=offset; idx<offset+n; idx+=1){
      Serial.print(expr->databuf[adc_offset+idx]);
    }
  }
  Serial.println("");
}

void compute_offsets(experiment_t * expr){
  int n_segs = 0;
  for(int i=0; i < MAX_ADCS; i+= 1){
    n_segs += expr->use_adc[i] ? 1 : 0;
  }
  for(int i=0; i < MAX_DACS; i+= 1){
    n_segs += expr->use_dac[i] ? 1 : 0;
  }
  expr->max_samples = MAX_SIZE / n_segs;
  int seg_idx = 0;
  for(int i=0; i < MAX_ADCS; i += 1){
    expr->adc_offsets[i] = seg_idx*expr->max_samples;
    seg_idx += 1;
  }
  for(int i=0; i < MAX_DACS; i += 1){
    expr->adc_offsets[i] = seg_idx*expr->max_samples;
    seg_idx += 1;
  }
  if(expr->n_samples > expr->max_samples){
    expr->n_samples = expr->max_samples;
  }
  expr->compute_offsets = true;
}
void reset_experiment(experiment_t * expr){
  expr->use_analog_chip = true;
  expr->compute_offsets = false;
  expr->n_samples = 0;
  expr->max_samples = 0;
  for(int idx = 0; idx < MAX_DACS; idx+=1 ){
    expr->use_dac[idx] = false;
    expr->dac_offsets[idx] = -1;
  }
  for(int idx = 0; idx < MAX_ADCS; idx+=1 ){
    expr->use_adc[idx] = false;
    expr->adc_offsets[idx] = -1;
  }
  expr->use_osc = false;
  memset(expr->databuf,0,MAX_SIZE);
}
void run_experiment(experiment_t * expr, Fabric * fab){
  if(not expr->compute_offsets){
      Serial.println("[error] must compute offsets beforehand");
      return;
  }
  IDX = 0;
  N = expr->n_samples;
  N_OSC = OSC_SAMPLES/DELAY_TIME_US;
  FABRIC = fab;
  EXPERIMENT = expr;
  Serial.print(N_OSC);
  Serial.print("/");
  Serial.println(N);
  // trigger the start of the experiment
  //Timer3.detachInterrupt();
  //attach_interrupts(expr,fab);
  if(expr->use_analog_chip){
    //circ::commit_config(fab);
    //circ::finalize_config(fab);
    //circ::execute(fab);
  }
  else{
  }
  //Timer3.attachInterrupt(_update_wave);
  //Timer3.start(DELAY_TIME_US);
  _toggle_SDA();
  while(IDX < N){
    _update_wave();
    delay(2);
  }
  _toggle_SDA();
  //Timer3.detachInterrupt();
  if(EXPERIMENT->use_analog_chip){
        //circ::finish(FABRIC);
  }
  analogWrite(DAC0, 0); 
  analogWrite(DAC1, 0); 
  Serial.println("::done::");
}

void set_n_samples(experiment_t * expr, int n){
  if(expr->compute_offsets){
      expr->n_samples = n <= expr->max_samples ? n : expr->max_samples;
  }
  else{
      expr->n_samples = n;
  }
}

void set_dac_values(experiment_t* expr, float * inbuf, int dac_id, int n, int offset){
  if(not expr->compute_offsets){
    Serial.print("[ERROR] must compute offsets before setting dac values.");
    return;
  }
  int buf_idx = offset + expr->dac_offsets[dac_id];
  for(int idx = 0; idx < n; idx+=1){
      unsigned short value = (short) (inbuf[idx]*2048+2048);
      expr->databuf[buf_idx + idx] = value;
  }
}
void exec_command(experiment_t* expr, Fabric* fab, cmd_t& cmd, float * inbuf){
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
      set_n_samples(expr,cmd.args[0]);
      break;

    case cmd_type_t::COMPUTE_OFFSETS:
      compute_offsets(expr);
      break;
    case cmd_type_t::SET_DAC_VALUES:
      set_dac_values(expr,inbuf,cmd.args[0],cmd.args[1],cmd.args[2]);
      break;

    case cmd_type_t::GET_ADC_VALUES:
      print_adc_values(expr,cmd.args[0],cmd.args[1],cmd.args[2]);
      break;
  }
}


void print_command(cmd_t& cmd, float* inbuf){
  switch(cmd.type){
    case cmd_type_t::SET_N_ADC_SAMPLES:
      Serial.print("set_samples ");
      Serial.println(cmd.args[0]);
      break;
      
    case cmd_type_t::USE_OSC:
      Serial.println("use_osc");
      break;

    case cmd_type_t::USE_DAC:
      Serial.print("use_dac ");
      Serial.println(cmd.args[0]);
      break;

    case cmd_type_t::USE_ADC:
      Serial.print("use_adc ");
      Serial.println(cmd.args[0]);
      break;

    case cmd_type_t::USE_ANALOG_CHIP:
      Serial.println("use_analog_chip");
      break;

    case cmd_type_t::COMPUTE_OFFSETS:
      Serial.println("compute_offsets");
      break;
      
    case cmd_type_t::GET_ADC_VALUES:
      Serial.print("get_adc_values adc_id=");
      Serial.print(cmd.args[0]);
      Serial.print(" nels=");
      Serial.print(cmd.args[1]);
      Serial.print(" offset=");
      Serial.println(cmd.args[2]);
      break;
       
    case cmd_type_t::SET_DAC_VALUES:
      Serial.print("set_dac_values dac_id=");
      Serial.print(cmd.args[0]);
      Serial.print(" nels=");
      Serial.print(cmd.args[1]);
      Serial.print(" offset=");
      Serial.print(cmd.args[2]);
      Serial.print(" [");
      for(int i=0; i < cmd.args[1]; i++){
        Serial.print(inbuf[i]);
        Serial.print(" ");
      }
      Serial.println("]");
      break;

    case cmd_type_t::RESET:
      Serial.println("reset");
      break;
      
    case cmd_type_t::RUN:
      Serial.println("run");
      break;
      
    default:
      Serial.print(cmd.type);
      Serial.print(" ");
      Serial.print(cmd.args[0]);
      Serial.print(" ");
      Serial.print(cmd.args[1]);
      Serial.print(" ");
      Serial.print(cmd.args[2]);
      Serial.println(" <unimpl experiment>");
      break;
  }
}

}


