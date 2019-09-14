#include "AnalogLib.h"


namespace oscgen {


  typedef struct {
    /*the blocks involved in making the oscillator*/
    Fabric::Chip::Tile::Slice::Integrator* integ;
    Fabric::Chip::Tile::Slice::Fanout* fan;
    Fabric::Chip::Tile::Slice::TileInOut* tile;
    Fabric::Chip::Tile::Slice::ChipOutput * chip;
    /*the two oscillators*/
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface* osc0;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface* osc1;
    integ_code_t integ_state;
    fanout_code_t fanout_state;
    bool programmed;
  } osc_env_t;

  osc_env_t select_blocks(Fabric::Chip::Tile::Slice::FunctionUnit* fu);
  void make_oscillator(osc_env_t& env);
  float measure_oscillator_amplitude(osc_env_t& env);
  void teardown_oscillator(osc_env_t& env);
}
