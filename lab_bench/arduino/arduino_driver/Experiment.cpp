#include "math.h"
#include "Experiment.h"
#include "Arduino.h"

void clear_data(int * WF, int N){
  for(int t=0; t < N; t+= 1){
     WF[t] = 0;
  }
}

void _write_to_array(int * WF, int idx, int value){
    WF[idx] += (int) (value*2048 + 2048);
    if(WF[idx] > 4096){
        WF[idx] = 4096;
    }
    if(value < 0){
        WF[idx] = 0;
    }
    
}

void build_sin(int * WF, int N, float freq,float phase,float ampl){
  float scf = 1.0/((float)N)*2.0*3.14*10;
  for(int t=0; t < N; t += 1){
     float value = ampl*sin(freq*((float)t)*scf + phase);
     _write_to_array(WF,t,value);
  }
}

void build_const(int * WF, int N, float ampl){
  for(int t=0; t < N; t += 1){
     float value = ampl;
     _write_to_array(WF,t,value);
  }
}

void build_linear(int * WF, int N, float M, float B, float MIN, float MAX){
  for(int t=0; t < N; t += 1){
     float value = M*t+B;
     if(value > MAX){
        value = MAX;
     }
     if(value < MIN){
        value = MIN;
     }
     _write_to_array(WF,t,value);
  }
}

wfspec_t* sig_get_unused(wfspec_t * subsigs, int n_sigs){
  for(int idx = 0; idx < n_sigs; idx+= 1){
      if(subsigs[idx].type == wftype_t::NONE){
        return &subsigs[idx];
      }
  }
  return NULL;
}
void sig_add_sin(wfspec_t * subsigs, int n_sigs, float freq, float phase, float ampl){
  wfspec_t * sig = sig_get_unused(subsigs,n_sigs);
  sig->type = wftype_t::SIN;
  sig->data.sind.freq = freq;
  sig->data.sind.phase = phase;
  sig->data.sind.ampl = ampl;
}

void sig_add_const(wfspec_t * subsigs, int n_sigs, float value){
  wfspec_t * sig = sig_get_unused(subsigs,n_sigs);
  sig->type = wftype_t::CONST;
  sig->data.constd.value = value;
}

void sig_add_linear(wfspec_t * subsigs, int n_sigs, float slope, float offset){
  wfspec_t * sig = sig_get_unused(subsigs,n_sigs);
  sig->type = wftype_t::LINEAR;
  sig->data.lind.slope = slope;
  sig->data.lind.offset = offset;
}

void _normalize_experiment_helper(wfspec_t * spec, int n){
  float max_value = 0.0;
  for(int idx=0; idx < n; idx += 1){
     switch(spec[idx].type){
        case wftype::NONE:
          break;
        case wftype::CONST:
          max_value += spec[idx].data.constd.value;
          break;
        case wftype::SIN:
          max_value += spec[idx].data.sind.ampl;
          break;
        case wftype::LINEAR:
          max_value += max(abs(spec[idx].data.lind.min_value),
                           abs(spec[idx].data.lind.max_value));
          break;
         
     }
  }

   for(int idx=0; idx < n; idx += 1){
     switch(spec[idx].type){
        case wftype::NONE:
          break;
        case wftype::CONST:
         spec[idx].data.constd.value /= max_value;
          break;
        case wftype::SIN:
          spec[idx].data.sind.ampl /= max_value;
          break;
        case wftype::LINEAR:
          spec[idx].data.lind.min_value /= max_value;
          spec[idx].data.lind.max_value /= max_value;
          break;
         
     }
  }
}
bool _has_signal(wfspec_t * spec, int n){
  for(int idx=0; idx < n; idx += 1){
      switch(spec[idx].type){
        case wftype::NONE:
          break;
        default:
          return true;
      }
  }
  return false;
  
}
int count_signals(experiment_t * exp){
   int count = 0;
   if(_has_signal(exp->sig1,NUM_SUBSIGS)){
      count += 1;
   }
   if(_has_signal(exp->sig1,NUM_SUBSIGS)){
      count += 1;
   }
   return count;
}
void normalize_experiment(experiment_t * exp){
  float max_ampl_1 = 0.0;
  float max_ampl_2 = 0.0;
  _normalize_experiment_helper(exp->sig1, NUM_SUBSIGS);
  _normalize_experiment_helper(exp->sig2, NUM_SUBSIGS);
  
}

void compile_experiment(experiment_t * exp){
  normalize_experiment(exp);
  int n = count_signals(exp);
  exp->num_signals = n;
}
void init_experiment(experiment_t * exp){
  exp->num_signals = 0;
  for(int idx=0; idx < NUM_SUBSIGS; idx+=1){
     exp->sig1[idx].type = wftype_t::NONE;
     exp->sig2[idx].type = wftype_t::NONE;
    
  }
  
}
void write_signal(int * WF, int N, wfspec_t * subsigs, int n_sigs){
  clear_data(WF,N);
  for(int idx = 0; idx < n_sigs; idx += 1){
      wfspec_t * sig = &subsigs[idx];
      switch(sig->type){
        case wftype_t::LINEAR:
          build_linear(WF,N,sig->data.lind.slope,
                       sig->data.lind.offset);
          break;
        case wftype_t::CONST:
          build_const(WF,N,sig->data.constd.value);
          break;
        case wftype_t::SIN:
          Serial.println("sin");
          build_sin(WF,N,sig->data.sind.freq,
          sig->data.sind.phase,
          sig->data.sind.ampl);
          break;
        case wftype_t::NONE:
          break;
        default:
          Serial.print("unknown: ");
          Serial.println(sig->type);
          break;
      }
      
  }
}



