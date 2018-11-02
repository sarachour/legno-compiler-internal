#ifndef EXPERIMENT_H
#define EXPERIMENT_H
#include <DueTimer.h>
#include "Circuit.h"
#include "math.h"

# define MAX_SIZE 10000

namespace experiment {
  
typedef struct experiment_data {
  int n_dac_samples[2];
  int n_adc_samples;
  bool use_osc;
  bool use_adc[4];
  bool use_dac[2];
  bool use_analog_chip;
  // input data
  short dac[2][MAX_SIZE];
  // adc output data
  short adc_pos[4][MAX_SIZE];
  short adc_neg[4][MAX_SIZE];

} experiment_t;

typedef enum cmd_type {
  RESET,
  SET_DAC_VALUES,
  GET_ADC_VALUES,
  USE_ANALOG_CHIP,
  SET_N_ADC_SAMPLES,
  USE_DAC,
  USE_ADC,
  USE_OSC,
  RUN
} cmd_type_t;


typedef struct cmd {
  cmd_type_t type;
  int args[3];
} cmd_t;

void setup_experiment();
void set_dac_value(experiment_t * expr, byte dac_id,int sample,float data);
void enable_adc(experiment_t * expr, byte adc_id);
void enable_oscilloscope(experiment_t * expr);
void enable_analog_chip(experiment_t * expr);
void reset_experiment(experiment_t * expr);
void enable_dac(experiment_t * expr, byte dac_id);
short* get_adc_values(experiment_t * expr, byte adc_id, int& num_samples);
void exec_command(experiment_t * expr, cmd_t cmd);
void print_command(cmd_t& cmd);
}
#endif
