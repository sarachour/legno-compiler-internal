#include "math.h"
#include "Experiment.h"
#include "Arduino.h"
#include "Circuit.h"
#include "Comm.h"
#include <assert.h>

namespace experiment {

int16_t DATABUF[MAX_N_BYTES/sizeof(int16_t)];

volatile int IDX;
int N;
int N_DAC;
int N_ADC;
int N_OSC;
const float DELAY_TIME_US= 10.0;
volatile int SDA_VAL = LOW;
experiment_t* EXPERIMENT;
Fabric* FABRIC;

short BITMASK_ONE[] = {0x0000,0xffff};
short BITMASK_ZERO[] = {0xffff, 0x0000};

inline void store_value(experiment_t * expr,uint32_t offset, int16_t value){
  expr->databuf[offset] = value;
}
int16_t get_value(experiment_t * expr,uint32_t offset){
  int16_t  value = expr->databuf[offset];
  return value;
}
inline void save_adc3_value(experiment_t * expr, int idx){
  store_value(expr,expr->adc_offsets[3] + (idx % N_ADC), ADC->ADC_CDR[6]);
}
inline void save_adc2_value(experiment_t * expr, int idx){
  store_value(expr,expr->adc_offsets[2] + (idx % N_ADC), ADC->ADC_CDR[4]);
}
inline void save_adc1_value(experiment_t * expr, int idx){
  store_value(expr,expr->adc_offsets[1] + (idx % N_ADC), ADC->ADC_CDR[2]);
}
inline void save_adc0_value(experiment_t * expr, int idx){
  store_value(expr,expr->adc_offsets[0] + (idx % N_ADC), ADC->ADC_CDR[0]);
}

inline void write_dac0_value(experiment_t * expr, int idx){
  int i = idx < N_DAC or expr->periodic_dac[0] ? (idx % N_DAC) : N_DAC-1;
  analogWrite(DAC0, get_value(expr,expr->dac_offsets[0] + i )); 
}
inline void write_dac1_value(experiment_t * expr, int idx){
  int i = idx < N_DAC or expr->periodic_dac[1] ? (idx % N_DAC) : N_DAC-1;
  analogWrite(DAC1, get_value(expr,expr->dac_offsets[1] + i )); 
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
  IDX += 1;
  
  if(EXPERIMENT->use_dac[0])
    write_dac0_value(EXPERIMENT,idx);  

  if(EXPERIMENT->use_dac[1])
    write_dac1_value(EXPERIMENT,idx);
    
  if(EXPERIMENT->use_adc[0])
    save_adc0_value(EXPERIMENT,idx);
  
  if(EXPERIMENT->use_adc[1])
    save_adc1_value(EXPERIMENT,idx);
  
  if(EXPERIMENT->use_adc[2])
    save_adc2_value(EXPERIMENT,idx);
  
  if(EXPERIMENT->use_adc[3])
    save_adc3_value(EXPERIMENT,idx);
    
  //drive_sda_clock(idx);
  if(idx >= N){
    Timer3.detachInterrupt();
    analogWrite(DAC0, 0); 
    analogWrite(DAC1, 0);
  }
  // increment index
}


void setup_experiment(experiment_t* expr) {
  pinMode(SDA, OUTPUT);
  // put your setup code here, to run once:
  analogWriteResolution(12);  // set the analog output resolution to 12 bit (4096 levels)
  expr->databuf = DATABUF;
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
void enable_dac(experiment_t * expr, byte dac_id,bool periodic){
  expr->use_dac[dac_id] = true;
  expr->periodic_dac[dac_id] = periodic;
}

void print_adc_values(experiment_t * expr, int adc_id, int nels, int offset){
  char buf[32];
  int n = nels + offset <= expr->adc_samples ? nels : expr->adc_samples - offset;
  sprintf(buf,"%d",n);
  comm::data(buf,"F");
  comm::payload();
  int adc_offset = expr->adc_offsets[adc_id];
  if(adc_offset >= 0 and expr->compute_offsets){
    for(int idx=offset; idx < offset+n; idx+=1){
      assert(adc_offset+idx < MAX_N_SAMPLES);
      short val = get_value(expr, adc_offset+idx);
      Serial.print(" ");
      Serial.print(float(val)/4096);
    }
  }
  Serial.println("");
}

void compute_offsets(experiment_t * expr){
  int n_dac_segs = 0;
  int n_adc_segs = 0;

  // compute the number of adc and dac segments in use.
  for(int i=0; i < MAX_ADCS; i+= 1){
    n_adc_segs += expr->use_adc[i] ? 1 : 0;
  }
  for(int i=0; i < MAX_DACS; i+= 1){
    n_dac_segs += expr->use_dac[i] ? 1 : 0;
  }
  int max_n_samples = MAX_N_SAMPLES;
  int samples_required = n_dac_segs*expr->dac_samples + n_adc_segs*expr->total_samples;
  int dac_samples = expr->dac_samples;
  int adc_samples = expr->total_samples;
  int total_samples = expr->total_samples;
  float time_between_samps = expr->time_between_samps_us;
  // if we're in over our head in terms of number of samples, readjust
  if(samples_required > max_n_samples){
    float time_scf = float(samples_required)/max_n_samples;
    dac_samples = floor(expr->dac_samples*(1.0/time_scf));
    adc_samples = floor(expr->adc_samples*(1.0/time_scf));
    total_samples = floor(expr->adc_samples*(1.0/time_scf));
    samples_required = n_dac_segs*dac_samples + n_adc_segs*adc_samples;
    time_between_samps = time_between_samps*time_scf;
    assert(samples_required <= max_n_samples);
  }
  expr->adc_samples = adc_samples;
  expr->dac_samples = dac_samples;
  expr->total_samples = dac_samples;
  expr->time_between_samps_us = time_between_samps;
  
  int offset = 0;
  for(int i=0; i < MAX_ADCS; i += 1){
    assert(offset < max_n_samples);
    if(expr->use_adc[i]){
      expr->adc_offsets[i] = offset;
      offset += expr->adc_samples;
    }
  }
  for(int i=0; i < MAX_DACS; i += 1){
    assert(offset < max_n_samples);
    if(expr->use_dac[i]){
      expr->dac_offsets[i] = offset;
      offset += expr->dac_samples;
    }
  }
  expr->compute_offsets = true;
}
void reset_experiment(experiment_t * expr){
  expr->use_analog_chip = true;
  expr->compute_offsets = false;
  expr->dac_samples = 0;
  expr->adc_samples = 0;
  expr->total_samples = 0;
  expr->time_between_samps_us = DELAY_TIME_US;;
  for(int idx = 0; idx < MAX_DACS; idx+=1 ){
    expr->use_dac[idx] = false;
    expr->periodic_dac[idx] = false;
    expr->dac_offsets[idx] = -1;
  }
  for(int idx = 0; idx < MAX_ADCS; idx+=1 ){
    expr->use_adc[idx] = false;
    expr->adc_offsets[idx] = -1;
  }
  expr->use_osc = false;
  memset(expr->databuf,0,MAX_N_BYTES);
}
void run_experiment(experiment_t * expr, Fabric * fab){
  if(not expr->compute_offsets){
      comm::error("must compute offsets beforehand");
      return;
  }
  IDX = 0;
  N = expr->total_samples;
  N_DAC = expr->dac_samples;
  N_ADC = expr->adc_samples;
  N_OSC = expr->osc_samples;
  FABRIC = fab;
  EXPERIMENT = expr;
  comm::print_header();
  Serial.print(N_OSC);
  Serial.print("/");
  Serial.println(N);
  // clear dacs
  analogWrite(DAC0, 0); 
  analogWrite(DAC1, 0); 
  delay(10);
  
  Timer3.attachInterrupt(_update_wave);
  // trigger the start of the experiment
  if(expr->use_analog_chip){
    circ::commit_config(fab);
    circ::finalize_config(fab);
    comm::print_header();
    Serial.println("wrote config");
    comm::print_header();
    Serial.println("toggle sda");
    _toggle_SDA();
    circ::execute(fab);
    Timer3.start(expr->time_between_samps_us);
  }
  else{
    comm::print_header();
    Serial.println("toggle sda");
    _toggle_SDA();
    Timer3.start(expr->time_between_samps_us);
  }
  while(IDX < N){
    comm::print_header();
    Serial.print("waiting idx=");
    Serial.println(IDX);
    delay(500);
  }
  Timer3.stop();
  if(EXPERIMENT->use_analog_chip){
        circ::finish(fab);
  }
  analogWrite(DAC0, 0); 
  analogWrite(DAC1, 0); 
  comm::done_command();
}

void set_sim_time(experiment_t * expr, float sim_time, float period_time, float frame_time){
  // TODO: compute number of samples and osc clock
  float time_between_samples = DELAY_TIME_US*1e-6;
  int osc_samples = frame_time/time_between_samples;
  int sim_samples = sim_time/time_between_samples;
  int dac_samples = period_time/time_between_samples;
  expr->time_between_samps_us = DELAY_TIME_US;
  expr->dac_samples = dac_samples;
  expr->adc_samples = sim_samples;
  expr->total_samples = sim_samples;
  expr->osc_samples = osc_samples;
  expr->compute_offsets = false;
}

void set_dac_values(experiment_t* expr, float * inbuf, int dac_id, int n, int offset){
  if(not expr->compute_offsets){
    Serial.print("[ERROR] must compute offsets before setting dac values.");
    return;
  }
  int buf_idx = offset + expr->dac_offsets[dac_id];
  for(int idx = 0; idx < n; idx+=1){
      // 4096, zero at 2047
      unsigned short value = (unsigned short) (inbuf[idx]*2047+2048) & 0xfff;
      store_value(expr,buf_idx + idx, value);
  }
}
void exec_command(experiment_t* expr, Fabric* fab, cmd_t& cmd, float * inbuf){
  char buf[128];
  switch(cmd.type){
    case cmd_type_t::RESET:
      reset_experiment(expr);
      comm::response("resetted",0);
      break;
    case cmd_type_t::RUN:
      run_experiment(expr,fab);
      comm::response("ran",0);
      break;
    case cmd_type_t::USE_ANALOG_CHIP:
      enable_analog_chip(expr);
      comm::response("use_analog_chip=true",0);
      break;
    case cmd_type_t::USE_DAC:
      enable_dac(expr,cmd.args.ints[0],cmd.flag);
      comm::response("use_dac=true",0);
      break;
    case cmd_type_t::USE_ADC:
      enable_adc(expr,cmd.args.ints[0]);
      comm::response("use_adc=true",0);
      break;
    case cmd_type_t::USE_OSC:
      enable_oscilloscope(expr);
      comm::response("enable_trigger=true",0);
      break;
    case cmd_type_t::SET_SIM_TIME:
      set_sim_time(expr,cmd.args.floats[0],cmd.args.floats[1],cmd.args.floats[2]);
      comm::response("set simulation time",0);
      break;

    case cmd_type_t::COMPUTE_OFFSETS:
      compute_offsets(expr);
      comm::response("computed offsets",0);
      break;
    case cmd_type_t::SET_DAC_VALUES:
      set_dac_values(expr,inbuf,cmd.args.ints[0],cmd.args.ints[1],cmd.args.ints[2]);
      comm::response("set dac values",0);
      break;

    case cmd_type_t::GET_ADC_VALUES:
      comm::response("get adc values",1);
      print_adc_values(expr,cmd.args.ints[0],cmd.args.ints[1],cmd.args.ints[2]);
      break;

    case cmd_type_t::GET_TIME_BETWEEN_SAMPLES:
      comm::response("get time between samples",1);
      sprintf(buf,"%g",expr->time_between_samps_us*1e-6);
      comm::data(buf,"f");
      break;
      
    case cmd_type_t::GET_NUM_DAC_SAMPLES:
      comm::response("get num dac samples",1);
      sprintf(buf,"%d",expr->dac_samples);
      comm::data(buf,"i");
      break;
      
    case cmd_type_t::GET_NUM_ADC_SAMPLES:
      comm::response("get num adc samples",1);
      sprintf(buf,"%d",expr->adc_samples);
      comm::data(buf,"i");
      break;
  }
}


void print_command(cmd_t& cmd, float* inbuf){
  comm::print_header();
  switch(cmd.type){
    case cmd_type_t::SET_SIM_TIME:
      Serial.print("set_sim_time sim=");
      Serial.print(cmd.args.floats[0]);
      Serial.print(" period=");
      Serial.println(cmd.args.floats[1]);
      Serial.print(" osc=");
      Serial.println(cmd.args.floats[2]);
      break;
      
    case cmd_type_t::USE_OSC:
      Serial.println("use_osc");
      break;

    case cmd_type_t::USE_DAC:
      Serial.print("use_dac ");
      Serial.print(cmd.args.ints[0]);
      Serial.print(" periodic=");
      Serial.println(cmd.flag ? "yes" : "no");
      break;

    case cmd_type_t::USE_ADC:
      Serial.print("use_adc ");
      Serial.println(cmd.args.ints[0]);
      break;

    case cmd_type_t::USE_ANALOG_CHIP:
      Serial.println("use_analog_chip");
      break;

    case cmd_type_t::COMPUTE_OFFSETS:
      Serial.println("compute_offsets");
      break;

    case cmd_type_t::GET_NUM_DAC_SAMPLES:
      Serial.println("get_num_dac_samples");
      break;
    
    case cmd_type_t::GET_NUM_ADC_SAMPLES:
      Serial.println("get_num_adc_samples");
      break;
    case cmd_type_t::GET_TIME_BETWEEN_SAMPLES:
      Serial.println("get_time_between_samples");
      break;
      
    case cmd_type_t::GET_ADC_VALUES:
      Serial.print("get_adc_values adc_id=");
      Serial.print(cmd.args.ints[0]);
      Serial.print(" nels=");
      Serial.print(cmd.args.ints[1]);
      Serial.print(" offset=");
      Serial.println(cmd.args.ints[2]);
      break;

    case cmd_type_t::SET_DAC_VALUES:
      Serial.print("set_dac_values dac_id=");
      Serial.print(cmd.args.ints[0]);
      Serial.print(" nels=");
      Serial.print(cmd.args.ints[1]);
      Serial.print(" offset=");
      Serial.print(cmd.args.ints[2]);
      Serial.print(" [");
      for(int i=0; i < cmd.args.ints[1]; i++){
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
      Serial.print(cmd.args.ints[0]);
      Serial.print(" ");
      Serial.print(cmd.args.ints[1]);
      Serial.print(" ");
      Serial.print(cmd.args.ints[2]);
      Serial.println(" <unimpl experiment>");
      break;
  }
}

}


