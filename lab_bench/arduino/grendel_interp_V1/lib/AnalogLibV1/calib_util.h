#ifndef CUTIL_H
#define CUTIL_H
#include "fu.h"
#include "connection.h"
#include "profile.h"
#include <float.h>

namespace cutil {

  #define MAX_CONNS 10
  #define MAX_HIDDEN_STATE 7
  #define DAC_CACHE_SIZE 7

  typedef struct {
    unsigned char state[MAX_HIDDEN_STATE];
    float score;
    bool set;
  } calib_table_t;

  typedef struct _CALIBRATE_T {
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface* conn_buf[MAX_CONNS][2];
    int nconns;
    bool success;
  } calibrate_t;

  calib_table_t make_calib_table();
  void update_calib_table(calib_table_t& table, float new_score, int n, ...);
  bool perfect_score(calib_table_t& table);



  bool measure_signal_robust(Fabric::Chip::Tile::Slice::FunctionUnit * fu,
                             Fabric::Chip::Tile::Slice::Dac * ref_dac,
                             float target,
                             bool measure_steady_state,
                             float& mean,
                             float& variance);


  void initialize(calibrate_t& cal);
  // this is a special high-to-medium converter specifically for
  // the multiplier, since we want to be able to scale down signals
  //
  /* DEPRECATED START*/
  float fast_make_dac(Fabric::Chip::Tile::Slice::Dac* dac,
                        float value);

  dac_code_t make_ref_dac(calibrate_t& calib,
                           Fabric::Chip::Tile::Slice::Dac* dac,
                          float value,
                          float& ref);

  dac_code_t make_zero_dac(calibrate_t& calib,
                           Fabric::Chip::Tile::Slice::Dac* dac);
  dac_code_t make_one_dac(calibrate_t& calib,
                          Fabric::Chip::Tile::Slice::Dac * dac);
  dac_code_t make_val_dac(calibrate_t& calib,
                          Fabric::Chip::Tile::Slice::Dac * dac,
                          float value);
  /* DEPRECATED START*/

  void buffer_fanout_conns( calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Fanout* fu);
  void buffer_mult_conns( calibrate_t& calib,
                          Fabric::Chip::Tile::Slice::Multiplier* fu);
  void buffer_dac_conns( calibrate_t& calib,
                         Fabric::Chip::Tile::Slice::Dac* fu);
  void buffer_adc_conns( calibrate_t& calib,
                         Fabric::Chip::Tile::Slice::ChipAdc* fu);

  void buffer_integ_conns( calibrate_t& calib,
                         Fabric::Chip::Tile::Slice::Integrator* fu);

  void buffer_chipin_conns( calibrate_t& calib,
                             Fabric::Chip::Tile::Slice::ChipInput* fu);
  void buffer_chipout_conns( calibrate_t& calib,
                             Fabric::Chip::Tile::Slice::ChipOutput* fu);

  void buffer_tileout_conns( calibrate_t& calib,
                             Fabric::Chip::Tile::Slice::TileInOut* fu);
  void break_conns(calibrate_t& calib);
  void restore_conns(calibrate_t& calib);

}

#endif
