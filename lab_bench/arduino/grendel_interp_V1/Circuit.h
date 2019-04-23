#ifndef CIRCUIT_H
#define CIRCUIT_H

#define _DUE
#include "AnalogLib.h"
namespace circ {

typedef enum block_type {
  TILE_DAC,
  CHIP_INPUT,
  CHIP_OUTPUT,
  TILE_INPUT,
  TILE_OUTPUT,
  MULT,
  INTEG,
  FANOUT,
  LUT,
  TILE_ADC
} block_type_t;

// TODO interpreter for commands
typedef enum cmd_type {
    /*use components 0-5 */
    USE_DAC,
    USE_MULT,
    USE_FANOUT,
    USE_INTEG,
    USE_LUT,
    USE_ADC,
    /*disable components 6-12 */
    DISABLE_DAC,
    DISABLE_MULT,
    DISABLE_INTEG,
    DISABLE_FANOUT,
    DISABLE_LUT,
    DISABLE_ADC,
    /*connection 12-15 */
    CONNECT,
    BREAK,
    CALIBRATE,
    /*debug 15-17 */
    GET_INTEG_STATUS,
    GET_ADC_STATUS,
    /*set values 17-21 */
    CONFIG_DAC,
    CONFIG_MULT,
    CONFIG_INTEG,
    WRITE_LUT,
    /*code setting*/
    GET_CODES,
    SET_CODES,
    MEASURE
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

 typedef enum code_type {
   CODE_PMOS,
   CODE_NMOS,
   CODE_OFFSET,
   CODE_COMP_LOWER_FS,
   CODE_COMP_UPPER_FS
 } code_type_t;


typedef enum dac_source {
  DS_MEM,
  DS_EXT,
  DS_LUT0,
  DS_LUT1
} dac_source_t;

typedef struct use_dac {
   circ_loc_t loc;
   uint8_t source;
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

typedef enum lut_source {
  LS_EXT,
  LS_ADC0,
  LS_ADC1
} lut_source_t;

typedef struct use_lut {
  circ_loc_t loc;
  uint8_t source;
} cmd_use_lut_t;


typedef struct write_lut {
  circ_loc_t loc;
  uint8_t offset;
  uint8_t n;
} cmd_write_lut_t;

typedef struct use_adc {
  circ_loc_t loc;
  uint8_t in_range;
} cmd_use_adc_t;

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

 typedef struct acc_code {
   uint16_t src_blk;
   circ_loc_idx2_t port;
   uint8_t keyvals[10];
 } cmd_acc_code_t;

typedef union cmddata {
  cmd_use_fanout_t fanout;
  cmd_use_integ_t integ;
  cmd_use_mult_t mult;
  cmd_use_dac_t dac;
  cmd_use_lut_t lut;
  cmd_write_lut_t write_lut;
  cmd_use_adc_t adc;
  cmd_connection_t conn;
  circ_loc_t circ_loc;
  circ_loc_idx1_t circ_loc_idx1;
  circ_loc_idx2_t circ_loc_idx2;
  cmd_acc_code_t codes;
} cmd_data_t;

typedef struct cmd {
  uint16_t type;
  cmd_data_t data;
} cmd_t;

//Fabric* setup_board();
//void init_calibrations();
void timeout(Fabric * fab, unsigned int timeout);
void print_command(cmd_t& cmd);
void exec_command(Fabric * fab, cmd_t& cmd, float* inbuf);
void debug_command(Fabric * fab, cmd_t& cmd, float* inbuf);

}
#endif CIRCUIT_H
