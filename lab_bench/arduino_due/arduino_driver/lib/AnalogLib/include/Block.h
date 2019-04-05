#ifndef BLOCK_H
#define BLOCK_H
#include "include/ProgIface.h"
#include "include/Util.h"

typedef enum RANGE_TYPE {
  LOW,
  MED,
  HIGH
} RANGE_TYPE;

typedef enum SIGN_TYPE {
  POS,
  NEG
} SIGN_TYPE;

typedef enum _PORT {
  COEFF,
  IN0,
  IN1,
  IC,
  OUT,
  OUT0,
  OUT1,
  OUT2
} PORT_NAME;

typedef enum _BLOCK {
  MULT,
  DAC,
  ADC,
  LUT,
  INTEG,
  FANOUT,
  TILE_IN,
  TILE_OUT,
  CHIP_IN,
  CHIP_OUT
} BLOCK_TYPE;


typedef struct _BLOCK_DATA {
  ProgIface * iface;
  BLOCK_TYPE type;
  unsigned char chip;
  unsigned char tile;
  unsigned char slice;
  unsigned char index;
} block_t;

#define LEFT 0
#define RIGHT 1

int to_range_code(BLOCK_TYPE blk, RANGE_TYPE t){

  if(blk == BLOCK_TYPE::FANOUT){
    switch(t){
    case LOW: return 0;
    case MED: return 0;
    case HIGH: return 1;
    }
  }
  else{
    switch(t){
    case LOW: return 1;
    case MED: return 0;
    case HIGH: return 2;
    }
  }
  error("to_range_code: not handled");
  return 0;
}
namespace block{
  bool has_port(BLOCK_TYPE blk, PORT_NAME port);
  unsigned int port_to_index(PORT_NAME port);
  bool input_port(PORT_NAME port);
  bool output_port(PORT_NAME port);
  void set_enable(block_t& blk, bool enable);
}
namespace mult{
  void set_offset_code(block_t& blk, PORT_NAME port, unsigned char offset_code);
  void set_gain_code(block_t& blk, unsigned char gain_code);
  void set_range(block_t& blk, PORT_NAME port, RANGE_TYPE range);
  void set_vga(block_t& blk, bool value);
  void set_enable(block_t& blk, bool value);
  void calibrate(block_t& blk);
}

namespace fanout{
  void set_out3(block_t& blk, bool value);
}
namespace integ {
  void set_exception(block_t& blk, bool value);
}
#endif
