#include "include/Vector.h"

vector_t clear_vector(vector_t& v){
  v = mkvector(v.tile, v.row, v.col, v.line, 0);
  return v;
}
