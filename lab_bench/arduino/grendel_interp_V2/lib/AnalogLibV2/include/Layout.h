#ifndef LAYOUT_H
#define LAYOUT_H

#include "include/Enums.h"

typedef struct LAYOUT_LOC_T {
  unsigned char tile;
  unsigned char row;
  unsigned char col;
  unsigned char line;
  unsigned char offset;
  unsigned char size;
  bool flip_endian;
} loc_t;

namespace layout {

 loc_t mkloc(unsigned char row, unsigned char col,
             unsigned char line, unsigned char offset,
             unsigned char size, bool endian);

 loc_t connection(block_loc_t& src,PORT_NAME srcp,
                  block_loc_t& dest,PORT_NAME destp);

 loc_t FANOUT_enable(block_loc_t& blk);
 loc_t FANOUT_range(block_loc_t& blk);
 loc_t FANOUT_inv(block_loc_t& blk, unsigned char idx);
 loc_t FANOUT_en3(block_loc_t& blk);
 loc_t FANOUT_nmos(block_loc_t& blk);
 loc_t FANOUT_pmos(block_loc_t& blk);


 loc_t MULT_enable(block_loc_t& blk);
 loc_t MULT_vga(block_loc_t& blk);
 loc_t MULT_range(block_loc_t& blk, PORT_NAME port);
 loc_t MULT_gain_code(block_loc_t& blk);
 loc_t MULT_offset_code(block_loc_t& blk, PORT_NAME port);
 loc_t MULT_pmos(block_loc_t& blk);
 loc_t MULT_nmos(block_loc_t& blk);


 loc_t INTEG_enable(block_loc_t& blk);
 loc_t INTEG_inv(block_loc_t& blk);
 loc_t INTEG_gain(block_loc_t& blk);
 loc_t INTEG_range(block_loc_t& blk);
 loc_t INTEG_offset_enable(block_loc_t& blk,PORT_NAME port);
 loc_t INTEG_exception(block_loc_t& blk);
 loc_t INTEG_init_cond(block_loc_t & blk);
 loc_t INTEG_nmos(block_loc_t& blk);
 loc_t INTEG_pmos(block_loc_t& blk);

 loc_t ADC_enable(block_loc_t& blk);
 loc_t ADC_offset_i2v(block_loc_t& blk);
 loc_t ADC_offset_upper(block_loc_t& blk);
 loc_t ADC_offset_upper_fullscale(block_loc_t& blk);
 loc_t ADC_offset_lower(block_loc_t& blk);
 loc_t ADC_offset_lower_fullscale(block_loc_t& blk);
 loc_t ADC_test_enable(block_loc_t& blk);
 loc_t ADC_test_adc(block_loc_t& blk);
 loc_t ADC_test_i2v(block_loc_t& blk);
 loc_t ADC_test_rstring(block_loc_t& blk);
 loc_t ADC_test_rstring_incr(block_loc_t & blk);
 loc_t ADC_pmos(block_loc_t& blk);
 loc_t ADC_nmos(block_loc_t& blk);

 loc_t DAC_enable(block_loc_t& blk);
 loc_t DAC_range(block_loc_t& blk);
 loc_t DAC_use_mem(block_loc_t& blk);
 loc_t DAC_value(block_loc_t& blk);
 loc_t DAC_clk_sel(block_loc_t& blk);
 loc_t DAC_input_sel(block_loc_t& blk);
 loc_t DAC_offset(block_loc_t& blk);
 loc_t DAC_pmos(block_loc_t& blk);
 loc_t DAC_nmos(block_loc_t& blk);

 loc_t LUT_trigger_delay(block_loc_t& blk);
 loc_t LUT_write_delay(block_loc_t& blk);
 loc_t LUT_read_delay(block_loc_t& blk);
 loc_t LUT_clk_sel(block_loc_t& blk);
 loc_t LUT_input_sel(block_loc_t& blk);
 loc_t LUT_value(block_loc_t& blk, unsigned char addr);


}


#endif
