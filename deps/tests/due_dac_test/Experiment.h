#ifndef EXPERIMENT_H
#define EXPERIMENT_H


#include "math.h"

typedef enum wftype {
  LINEAR = 3,
  CONST = 1,
  SIN = 2,
  NONE = 0
} wftype_t;

typedef struct wfsin {
  float freq;
  float phase;
  float ampl;  
} wfsin_t;

typedef struct wflinear {
  float slope;
  float offset;  
} wflinear_t;

typedef struct wfconst {
  float value;
} wfconst_t;

typedef union wfdata {
   wfconst_t constd;
   wfsin_t sind;
   wflinear_t lind;
} wfdata_t;

typedef struct wfspec {
  wftype_t type;
  wfdata_t data;
} wfspec_t;

# define NUM_SUBSIGS 10
typedef struct experiment {
  int num_signals; 
  wfspec_t sig1[NUM_SUBSIGS];
  wfspec_t sig2[NUM_SUBSIGS];
} experiment_t;

void clear_data(int * WF, int N);
void build_sin(int * WF, int N, float freq,float phase,float ampl);
void build_const(int * WF, int N, float ampl);
void build_linear(int * WF, int N, float M, float B);
wfspec_t* sig_get_unused(wfspec_t * subsigs, int n_sigs);
void sig_add_sin(wfspec_t * subsigs, int n_sigs, float freq, float phase, float ampl);
void sig_add_const(wfspec_t * subsigs, int n_sigs, float value);
void sig_add_linear(wfspec_t * subsigs, int n_sigs, float slope, float offset);
void write_signal(int * WF, int N, wfspec_t * subsigs, int n_sigs);
void init_experiment(experiment_t * exp);



#endif
