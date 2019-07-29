#ifndef BLOCK_H
#define BLOCK_H
#include "include/ProgIface.h"
#include "include/Enums.h"
#include "include/Util.h"
#include "include/Logger.h"

typedef struct _BLOCK_DATA {
  ProgIface * iface;
  BLOCK_TYPE type;
  block_loc_t place;
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
  void set_iref_pmos_code(block_t& blk, unsigned char pmos);
  void set_iref_nmos_code(block_t& blk, unsigned char nmos);
  void set_gain_code(block_t& blk, unsigned char gain_code);
  void set_gain(block_t& blk, float gain);
  void set_range(block_t& blk, PORT_NAME port, RANGE_TYPE range);
  void set_vga(block_t& blk, bool value);
  void set_inv(block_t& blk, bool value);
  void set_enable(block_t& blk, bool value);
}

namespace fanout{
  void set_out3(block_t& blk, bool value);
  void set_range(block_t& blk, PORT_NAME port, RANGE_TYPE range);
  void set_offset_code(block_t& blk, PORT_NAME port, unsigned char offset_code);
  void set_iref_pmos_code(block_t& blk, unsigned char pmos);
  void set_iref_nmos_code(block_t& blk, unsigned char nmos);

}
namespace integ {
  void set_exception(block_t& blk, bool value);
}

namespace tile_dac {
  typedef enum _DAC_SOURCE_T{
    DSRC_MEM,
    DSRC_LUT0,
    DSRC_LUT1,
    DSRC_PARA
  } dac_source_t;

  void initialize(block_t& blk);
  void set_enable(block_t& blk, bool value);
  void set_source(block_t& blk, dac_source_t value);
  void set_value(block_t& blk, const char value);
  void set_offset_code(block_t& blk, const char value);
  void set_iref_pmos_code(block_t& blk, unsigned char pmos);
  void set_iref_nmos_code(block_t& blk, unsigned char nmos);
}

int to_range_code(BLOCK_TYPE blk, RANGE_TYPE t);
#endif
