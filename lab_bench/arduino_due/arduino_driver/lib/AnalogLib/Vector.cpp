#include "include/Vector.h"

vector_t clear_vector(vector_t& v){
  v = mkvector(v.tile, v.row, v.col, v.line, 0);
  return v;
}

vector_t mkvector(unsigned char tile, unsigned char row, unsigned char col,
                  unsigned char line, unsigned char cfg){

  vector_t vect;
  vect.tile = tile;
  vect.row = row;
  vect.col = col;
  vect.line = line;
  vect.cfg = cfg;
  return vect;
}
