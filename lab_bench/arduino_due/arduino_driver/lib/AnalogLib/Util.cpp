#include "include/Util.h"
#include "include/Vector.h"

/*Auxiliary function for converting between endian formats for 8 bit values*/
unsigned char endian (unsigned char input) {
	if (input<0||255<input) error ("endian conversion input out of bounds");
	unsigned char output = 0;
	output += (input&0x80)>>7;
	output += (input&0x40)>>5;
	output += (input&0x20)>>3;
	output += (input&0x10)>>1;
	output += (input&0x08)<<1;
	output += (input&0x04)<<3;
	output += (input&0x02)<<5;
	output += (input&0x01)<<7;
	if (output<0||255<output) error ("endian conversion output out of bounds");
	return output;
}

unsigned char set_bit(unsigned char bitno){
  if (bitno<0||7<bitno) {error("E: bitno out of bounds.\n");}
  unsigned char exponent = 7-bitno;
  unsigned char cfg = 1<<exponent;
  return cfg;
}
