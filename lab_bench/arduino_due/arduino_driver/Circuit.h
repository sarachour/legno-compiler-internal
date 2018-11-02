#ifndef CIRCUIT_H
#define CIRCUIT_H
#define _DUE
#include <HCDC_DEMO_API.h>

namespace circ {
typedef enum block_type {
  DAC,
  CHIP_INPUT,
  CHIP_OUTPUT,
  TILE,
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
    SET_N_ADC_SAMPLES,
    /*disable components*/
    DISABLE_DAC,
    DISABLE_MULT,
    DISABLE_INTEG,
    DISABLE_FANOUT,
    DISABLE_LUT,
    /*connection*/
    CONNECT,
    BREAK,
    CALIBRATE
} cmd_type_t;

typedef struct circ_loc {
  byte chip;
  byte tile;
  byte slice;
} circ_loc_t;

typedef struct circ_loc_idx1 {
   circ_loc_t loc;
   byte idx;
} circ_loc_idx1_t;

typedef struct circ_loc_idx2 {
  circ_loc_idx1_t idxloc;
  byte idx2;
} circ_loc_idx2_t;

typedef struct use_integ {
   circ_loc_t loc;
   byte value;
   bool inv;
} cmd_use_integ_t;


typedef struct use_dac {
   circ_loc_t loc;
   byte value;
   bool inv;
} cmd_use_dac_t;

typedef struct use_mult {
  circ_loc_idx1_t loc;
  bool use_coeff;
  byte coeff;
  bool inv;
} cmd_use_mult_t;

typedef struct use_fanout {
  circ_loc_idx1_t loc;
  bool inv[3];
} cmd_use_fanout_t;

typedef struct connection {
   block_type_t src_blk;
   circ_loc_idx2_t src_loc;
   block_type_t dst_blk;
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
  cmd_data_t data;
  cmd_type_t type;
} cmd_t;

void commit_config(Fabric * fab);
Fabric* setup_board();
void finalize_config(Fabric * fab);
void execute(Fabric * fab);
void finish(Fabric * fab);

void print_command(cmd_t& cmd);
void exec_command(Fabric * fab, cmd_t cmd);

}
#endif CIRCUIT_H
