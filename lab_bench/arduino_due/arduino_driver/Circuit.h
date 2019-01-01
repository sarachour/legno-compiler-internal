#ifndef CIRCUIT_H
#define CIRCUIT_H
#define _DUE
#include <HCDC_DEMO_API.h>

namespace circ {
typedef enum block_type {
  DAC,
  CHIP_INPUT,
  CHIP_OUTPUT,
  TILE_INPUT,
  TILE_OUTPUT,
  MULT,
  INTEG,
  FANOUT,
  LUT
} block_type_t;

// TODO interpreter for commands
typedef enum cmd_type {
    /*use components*/
    USE_DAC,
    USE_MULT,
    USE_FANOUT,
    USE_INTEG,
    USE_LUT,
    /*disable components*/
    DISABLE_DAC,
    DISABLE_MULT,
    DISABLE_INTEG,
    DISABLE_FANOUT,
    DISABLE_LUT,
    /*connection*/
    CONNECT,
    BREAK,
    CALIBRATE,
    /*debug*/
    GET_INTEG_STATUS
} cmd_type_t;

typedef struct circ_loc {
  uint8_t chip;
  uint8_t tile;
  uint8_t slice;
} circ_loc_t;

typedef struct circ_loc_idx1 {
   circ_loc_t loc;
   uint8_t idx;
} circ_loc_idx1_t;

typedef struct circ_loc_idx2 {
  circ_loc_idx1_t idxloc;
  uint8_t idx2;
} circ_loc_idx2_t;

typedef struct use_integ {
   circ_loc_t loc;
   uint8_t inv;
   uint8_t in_range;
   uint8_t out_range;
   uint8_t debug;
   float value;
} cmd_use_integ_t;


typedef struct use_dac {
   circ_loc_t loc;
   uint8_t inv;
   uint8_t out_range;
   float value;
} cmd_use_dac_t;

typedef struct use_mult {
  circ_loc_idx1_t loc;
  uint8_t use_coeff;
  uint8_t in0_range;
  uint8_t in1_range;
  uint8_t out_range;
  float coeff;
} cmd_use_mult_t;

typedef struct use_fanout {
  circ_loc_idx1_t loc;
  uint8_t inv[3];
  uint8_t in_range;
} cmd_use_fanout_t;

typedef struct connection {
   uint16_t src_blk;
   circ_loc_idx2_t src_loc;
   uint16_t dst_blk;
   circ_loc_idx2_t dst_loc;
} cmd_connection_t;

typedef union cmddata {
  cmd_use_fanout_t fanout;
  cmd_use_integ_t integ;
  cmd_use_mult_t mult;
  cmd_use_dac_t dac;
  cmd_connection_t conn;
  circ_loc_t circ_loc;
  circ_loc_idx1_t circ_loc_idx1;
  circ_loc_idx2_t circ_loc_idx2;
} cmd_data_t;

typedef struct cmd {
  uint16_t type;
  cmd_data_t data;
} cmd_t;

void commit_config(Fabric * fab);
Fabric* setup_board();
void finalize_config(Fabric * fab);
void execute(Fabric * fab);
void finish(Fabric * fab);

void print_command(cmd_t& cmd);
void exec_command(Fabric * fab, cmd_t& cmd);

}
#endif CIRCUIT_H
