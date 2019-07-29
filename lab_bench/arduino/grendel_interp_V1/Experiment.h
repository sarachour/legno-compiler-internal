#ifndef EXPERIMENT_H
#define EXPERIMENT_H
#include <DueTimer.h>
#include "Circuit.h"
#include "math.h"

# define MAX_ADCS 4
# define MAX_DACS 2
// max value is 32000
# define MAX_N_BYTES 32
//# define MAX_N_BYTES 8
#define MAX_N_SAMPLES (MAX_N_BYTES>>1)
// BOARD 5
//#define SDA_PIN SDA
#define SDA_PIN SDA1

namespace experiment {

typedef struct experiment_data {
  int dac_samples;
  int adc_samples;
  int osc_samples;
  int total_samples;
  int adc_offsets[MAX_ADCS];
  int dac_offsets[MAX_DACS];
  bool use_osc;
  bool compute_offsets;
  bool use_adc[MAX_ADCS];
  bool use_dac[MAX_DACS];
  bool periodic_dac[MAX_DACS];
  bool use_analog_chip;
  float time_between_samps_us;
  float sim_time_sec;
  // input data
  int16_t * databuf;

} experiment_t;

typedef enum cmd_type {
  RESET,
  SET_DAC_VALUES,
  GET_ADC_VALUES,
  USE_ANALOG_CHIP,
  SET_SIM_TIME,
  USE_DAC,
  USE_ADC,
  USE_OSC,
  RUN,
  COMPUTE_OFFSETS,
  GET_NUM_DAC_SAMPLES,
  GET_TIME_BETWEEN_SAMPLES,
  GET_NUM_ADC_SAMPLES
} cmd_type_t;

typedef union args {
  float floats[3];
  uint32_t ints[3];
} args_t;
typedef struct cmd {
  uint16_t type;
  args_t args;
  uint8_t flag;
} cmd_t;

void setup_experiment(experiment_t * expr);
void set_dac_value(experiment_t * expr, byte dac_id,int sample,float data);
void enable_adc(experiment_t * expr, byte adc_id);
void enable_oscilloscope(experiment_t * expr);
void enable_analog_chip(experiment_t * expr);
void reset_experiment(experiment_t * expr);
void enable_dac(experiment_t * expr, byte dac_id);
short* get_adc_values(experiment_t * expr, byte adc_id, int& num_samples);
void exec_command(experiment_t * expr, Fabric * fab, cmd_t& cmd, float* inbuf);
void debug_command(experiment_t * expr, Fabric * fab, cmd_t& cmd, float* inbuf);
void print_command(cmd_t& cmd, float* inbuf);
}
#endif
