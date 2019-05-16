#include "AnalogLib.h"
#include "calib_util.h"
#ifndef CALIBRATE_H
#define CALIBRATE_H

namespace calibrate {
  bool characterize(Fabric * fab,
                 util::calib_result_t& result,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc);


  bool calibrate(Fabric * fab,
                 util::calib_result_t& result,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc,
                 const float max_error);


  void get_codes(Fabric * fab,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc,
                 block_code_t& buf);

  void set_codes(Fabric * fab,
                 uint16_t blk,
                 circ::circ_loc_idx1_t loc,
                 block_code_t& buf);

}

#endif
