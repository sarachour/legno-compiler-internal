#ifndef UTIL_H
#define UTIL_H

unsigned char endian (unsigned char input);
unsigned char copy_bits(unsigned char cfg, unsigned char buf,
                        unsigned char offset, unsigned char nbits);
unsigned char set_bit(unsigned char bitno);

#endif

