#ifndef VECTOR_T
#define VECTOR_T

#include "Layout.h"

/*Crossbar switch cell specifies which switch to set*/
typedef struct VECTOR {
  unsigned char tile;
  loc_t loc;
  unsigned char cfg;
} vector_t;
/*Auxiliary function for converting between endian formats for 8 bit values*/

vector_t mkvector(unsigned char tile,
                  loc_t loc,
                  unsigned char cfg);


vector_t clear_vector(vector_t & v);
#endif
