#include "include/Util.h"
#include "include/Vector.h"
#include "include/Logger.h"

/*Auxiliary function for converting between endian formats for 8 bit values*/
unsigned char endian (unsigned char input) {
	if (input<0||255<input) logger::error ("endian conversion input out of bounds");
	unsigned char output = 0;
	output += (input&0x80)>>7;
	output += (input&0x40)>>5;
	output += (input&0x20)>>3;
	output += (input&0x10)>>1;
	output += (input&0x08)<<1;
	output += (input&0x04)<<3;
	output += (input&0x02)<<5;
	output += (input&0x01)<<7;
	if (output<0||255<output) logger::error ("endian conversion output out of bounds");
	return output;
}

unsigned char set_bit(unsigned char bitno){
  if (bitno<0||7<bitno) {logger::error("E: bitno out of bounds.\n");}
  unsigned char exponent = 7-bitno;
  unsigned char cfg = 1<<exponent;
  return cfg;
}
unsigned char copy_bits(unsigned char dat, unsigned char buf,
                        unsigned char offset, unsigned char size){
  unsigned char mask = 0;
  logger::assert(offset+size-1 < 8, "out of bounds copy");
  for(int i=0; i < size; i+=1){
    mask += set_bit(i+offset);
  }
  unsigned char inv_mask = ~mask;
  unsigned char result = (buf & mask) | (dat & inv_mask);
  return result;

}


