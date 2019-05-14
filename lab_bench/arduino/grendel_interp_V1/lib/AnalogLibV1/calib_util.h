#ifndef CUTIL_H
#define CUTIL_H
#include "AnalogLib.h"
#include "fu.h"
#include "connection.h"
#include <float.h>


namespace cutil{

  #define MAX_CONNS 10

  typedef struct _CALIBRATE_T {
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface* conn_buf[MAX_CONNS][2];
    int nconns;
    bool success;
  } calibrate_t;

  void initialize(calibrate_t& cal);
  float h2m_coeff();
  float h2m_coeff_norec();

  // this is a special high-to-medium converter specifically for
  // the multiplier, since we want to be able to scale down signals
  //
  mult_code_t make_h2m_mult_norecurse(calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Multiplier* mult);

  mult_code_t make_h2m_mult(calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Multiplier* mult);
  mult_code_t make_one_mult(calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Multiplier* mult);
  dac_code_t make_zero_dac(calibrate_t& calib,
                           Fabric::Chip::Tile::Slice::Dac* dac);
  dac_code_t make_low_dac(calibrate_t& calib,
                          Fabric::Chip::Tile::Slice::Dac* dac);
  dac_code_t make_one_dac(calibrate_t& calib,
                           Fabric::Chip::Tile::Slice::Dac * dac);

  void buffer_fanout_conns( calibrate_t& calib,
                            Fabric::Chip::Tile::Slice::Fanout* fu);
  void buffer_mult_conns( calibrate_t& calib,
                          Fabric::Chip::Tile::Slice::Multiplier* fu);
  void buffer_dac_conns( calibrate_t& calib,
                         Fabric::Chip::Tile::Slice::Dac* fu);
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
