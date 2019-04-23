#include "AnalogLib.h"

#ifndef CALIBRATE_H
#define CALIBRATE_H

namespace calibrate {

  void get_codes(Fabric* fab,
                 uint16_t blk,
                 circ::circ_loc_idx2_t port,
                 uint8_t rng,
                 uint8_t* buf);

}

#endif
