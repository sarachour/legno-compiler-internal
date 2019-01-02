#include "math.h"
#include "Experiment.h"
#include "Arduino.h"
#include "Circuit.h"
#include "Comm.h"
#include <assert.h>

namespace experiment {

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

inline void store_value(experiment_t * expr,uint32_t offset, int short value){
  uint32_t align_offset = offset >> 1;
  uint32_t mask_offset = offset & 0x1;
  expr->databuf[align_offset].e1 = (value & BITMASK_ZERO[mask_offset]) | 
    (expr->databuf[align_offset].e1 & BITMASK_ONE[mask_offset]);
  expr->databuf[align_offset].e2 = (value & BITMASK_ONE[mask_offset]) | 
    (expr->databuf[align_offset].e2 & BITMASK_ZERO[mask_offset]);
}
short get_value(experiment_t * expr,uint32_t offset){
  uint32_t align_offset = offset >> 1;
  uint32_t mask_offset = offset & 0x1;
  short value =  (expr->databuf[align_offset].e1 & BITMASK_ZERO[mask_offset]) | 
    (expr->databuf[align_offset].e2 & BITMASK_ONE[mask_offset]);
  return value;
  
}
inline void save_adc0_value(experiment_t * expr, int idx){
  store_value(expr,expr->adc_offsets[0] + (idx % N_ADC), ADC->ADC_CDR[6] - ADC->ADC_CDR[7]);
}
inline void save_adc1_value(experiment_t * expr, int idx){
  store_value(expr,expr->adc_offsets[1] + (idx % N_ADC), ADC->ADC_CDR[4] - ADC->ADC_CDR[5]);
}
inline void save_adc2_value(experiment_t * expr, int idx){
  store_value(expr,expr->adc_offsets[2] + (idx % N_ADC), ADC->ADC_CDR[2] - ADC->ADC_CDR[3]);
}
inline void save_adc3_value(experiment_t * expr, int idx){
  store_value(expr,expr->adc_offsets[3] + (idx % N_ADC), ADC->ADC_CDR[0] - ADC->ADC_CDR[1]);
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
    
  drive_sda_clock(idx);
  if(idx >= N){
    Timer3.detachInterrupt();
    analogWrite(DAC0, 0); 
    analogWrite(DAC1, 0);
  }
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
void enable_dac(experiment_t * expr, byte dac_id,bool periodic){
  expr->use_dac[dac_id] = true;
  expr->periodic_dac[dac_id] = periodic;
}

void print_adc_values(experiment_t * expr, int adc_id, int nels, int offset){
  int n = nels ? nels + offset < expr->adc_samples : expr->adc_samples - (nels+offset);
  Serial.print(n);
  int adc_offset = expr->adc_offsets[adc_id];
  if(adc_offset >= 0 and expr->compute_offsets){
    for(int idx=offset; idx<offset+n; idx+=1){
      Serial.print(expr->databuf[adc_offset+idx].e1);
      Serial.print(expr->databuf[adc_offset+idx].e2);
    }
  }
  Serial.println("");
}

void compute_offsets(experiment_t * expr){
  int n_dac_segs = 0;
  int n_adc_segs = 0;
  // data is periodic, simulation is not.
  float sim_to_dac = ( (float) expr->total_samples)/(expr->dac_samples);
  
  for(int i=0; i < MAX_ADCS; i+= 1){
    n_adc_segs += expr->use_adc[i] ? 1 : 0;
  }
  for(int i=0; i < MAX_DACS; i+= 1){
    n_dac_segs += expr->use_dac[i] ? 1 : 0;
  }
  int n_segs = n_dac_segs + n_adc_segs;
  // cannot fit all the dac data in memory.
  int max_size = n_segs == 0 ? MAX_SIZE : MAX_SIZE/n_segs;
  if(max_size < expr->dac_samples){
     expr->dac_samples = max_size;
     expr->total_samples = max_size;
     expr->adc_samples = max_size;
  }
  //
  else{
     // expr->dac_samples unchanged
     int adc_samples = MAX_SIZE - expr->dac_samples*n_dac_segs;
     expr->dac_samples = expr->dac_samples;
     expr->adc_samples = n_adc_segs == 0 ? expr->total_samples : adc_samples/n_adc_segs;
     expr->total_samples = expr->adc_samples;
  }
  
  int seg_idx = 0;
  int offset = 0;
  for(int i=0; i < MAX_ADCS; i += 1){
    expr->adc_offsets[i] = offset;
    offset += expr->adc_samples;
  }
  for(int i=0; i < MAX_DACS; i += 1){
    expr->adc_offsets[i] = offset;
    offset += expr->dac_samples;
    seg_idx += 1;
  }
  expr->compute_offsets = true;
}
void reset_experiment(experiment_t * expr){
  expr->use_analog_chip = true;
  expr->compute_offsets = false;
  expr->dac_samples = 0;
  expr->adc_samples = 0;
  expr->total_samples = 0;
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
  memset(expr->databuf,0,MAX_SIZE);
}
void run_experiment(experiment_t * expr, Fabric * fab){
  if(not expr->compute_offsets){
      Serial.println("[error] must compute offsets beforehand");
      return;
  }
  IDX = 0;
  N = expr->total_samples;
  N_DAC = expr->dac_samples;
  N_ADC = expr->adc_samples;
  N_OSC = expr->osc_samples;
  FABRIC = fab;
  EXPERIMENT = expr;
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
    _toggle_SDA();
    circ::execute(fab);
    Timer3.start(DELAY_TIME_US);
  }
  else{
    _toggle_SDA();
    Timer3.start(DELAY_TIME_US);
  }
  while(IDX < N){
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
  Serial.println("::done::");
}

void set_sim_time(experiment_t * expr, float sim_time, float period_time, float frame_time){
  // TODO: compute number of samples and osc clock
  float time_between_samples = DELAY_TIME_US/1000.0;
  int osc_samples = frame_time/time_between_samples;
  int sim_samples = sim_time/time_between_samples;
  int dac_samples = period_time/time_between_samples;
  expr->total_samples = sim_samples;
  expr->compute_offsets = false;
  expr->dac_samples = dac_samples;
  expr->adc_samples = sim_samples;
  expr->osc_samples = osc_samples;
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
      enable_dac(expr,cmd.args.ints[0],cmd.flag);
      break;
    case cmd_type_t::USE_ADC:
      enable_adc(expr,cmd.args.ints[0]);
      break;
    case cmd_type_t::USE_OSC:
      enable_oscilloscope(expr);
      break;
    case cmd_type_t::SET_SIM_TIME:
      set_sim_time(expr,cmd.args.floats[0],cmd.args.floats[1],cmd.args.floats[2]);
      break;

    case cmd_type_t::COMPUTE_OFFSETS:
      compute_offsets(expr);
      break;
    case cmd_type_t::SET_DAC_VALUES:
      set_dac_values(expr,inbuf,cmd.args.ints[0],cmd.args.ints[1],cmd.args.ints[2]);
      break;

    case cmd_type_t::GET_ADC_VALUES:
      print_adc_values(expr,cmd.args.ints[0],cmd.args.ints[1],cmd.args.ints[2]);
      break;

    case cmd_type_t::GET_TIME_BETWEEN_SAMPLES:
      Serial.println(DELAY_TIME_US/1000.0);
      break;
      
    case cmd_type_t::GET_NUM_DAC_SAMPLES:
      Serial.println(expr->dac_samples);
      break;
    case cmd_type_t::GET_NUM_ADC_SAMPLES:
      Serial.println(expr->adc_samples);
      break;
  }
}


void print_command(cmd_t& cmd, float* inbuf){
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
      Serial.println(cmd.args.ints[0]);
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


