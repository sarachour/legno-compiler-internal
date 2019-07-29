#include "include/Vector.h"

vector_t clear_vector(vector_t& v){
  v = mkvector(v.tile, v.loc, 0);
  return v;
}

vector_t mkvector(unsigned char tile, loc_t loc, unsigned char cfg){

  vector_t vect;
  vect.loc = loc;
  vect.cfg = cfg;
  vect.tile = tile;
  return vect;
}
