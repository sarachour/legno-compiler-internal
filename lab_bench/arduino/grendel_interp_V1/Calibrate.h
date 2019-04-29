#include "AnalogLib.h"

#ifndef CALIBRATE_H
#define CALIBRATE_H

namespace calibrate {
  bool calibrate(Fabric * fab,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc);


  void get_codes(Fabric * fab,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc,
                 block_code_t& buf);

  void set_codes(Fabric * fab,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc,
                 uint8_t* buf);

}

#endif
