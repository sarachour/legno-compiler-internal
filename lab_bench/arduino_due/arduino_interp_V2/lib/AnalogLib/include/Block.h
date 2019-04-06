#ifndef BLOCK_H
#define BLOCK_H
#include "include/ProgIface.h"
#include "include/Util.h"
#include "include/Logger.h"

typedef enum _RANGE_TYPE {
  RNG_LOW,
  RNG_MED,
  RNG_HIGH
} RANGE_TYPE;

typedef enum _SIGN_TYPE {
  POS,
  NEG
} SIGN_TYPE;

typedef enum _PORT {
  COEFF,
  IN0,
  IN1,
  IC,
  OUT0,
  OUT1,
  OUT2,
  UNKNOWN_PORT
} PORT_NAME;

typedef enum _BLOCK {
  MULT,
  TILE_DAC,
  TILE_ADC,
  TILE_LUT,
  INTEG,
  FANOUT,
  TILE_IN,
  TILE_OUT,
  CHIP_IN,
  CHIP_OUT,
  UNKNOWN_BLOCK
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

namespace block{
  bool has_port(BLOCK_TYPE blk, PORT_NAME port);
  unsigned int port_to_index(PORT_NAME port);
  bool digital_port(PORT_NAME port);
  bool input_port(PORT_NAME port);
  bool output_port(PORT_NAME port);
  void set_enable(block_t& blk, bool enable);
  block_t mkblock(BLOCK_TYPE blk,
                  unsigned char chip,
                  unsigned char tile,
                  unsigned char slice,
                  unsigned char index
                  );
}
namespace mult{
  bool has_port(PORT_NAME port);
  void set_offset_code(block_t& blk, PORT_NAME port, unsigned char offset_code);
  void set_gain_code(block_t& blk, unsigned char gain_code);
  void set_range(block_t& blk, PORT_NAME port, RANGE_TYPE range);
  void set_vga(block_t& blk, bool value);
  void set_enable(block_t& blk, bool value);
  void set_gain(block_t& blk, float value);
  void calibrate(block_t& blk);
}

namespace fanout{
  void set_out3(block_t& blk, bool value);
}
namespace integ {
  void set_exception(block_t& blk, bool value);
}
int to_range_code(BLOCK_TYPE blk, RANGE_TYPE t);
#endif
