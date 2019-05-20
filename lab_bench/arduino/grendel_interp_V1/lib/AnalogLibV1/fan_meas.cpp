#include "AnalogLib.h"
#include "assert.h"
#include "calib_util.h"

void Fabric::Chip::Tile::Slice::Fanout::characterize(util::calib_result_t& result) {
  util::init_result(result);
  measure(result);
}


void Fabric::Chip::Tile::Slice::Fanout::measure(util::calib_result_t& result) {

  fanout_code_t codes_self = m_codes;
  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_fanout_conns(calib,this);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,
                              parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  float mean,variance;
	Connection conn = Connection (parentSlice->tileOuts[3].out0,
                                parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0);
	conn.setConn();

	// Serial.print("\nFanout interface calibration");
  Connection conn0 = Connection (out0, this->parentSlice->tileOuts[3].in0);
  conn0.setConn();
  util::meas_dist_chip_out(this,mean,variance);
  conn0.brkConn();
  util::add_prop(result,out0Id, 0.0, mean,variance);

  Connection conn1 = Connection (out1, this->parentSlice->tileOuts[3].in0);
  conn1.setConn();
  util::meas_dist_chip_out(this,mean,variance);
  conn1.brkConn();
  util::add_prop(result,out1Id,0.0,mean,variance);

  Connection conn2 = Connection (out2, this->parentSlice->tileOuts[3].in0);
  conn1.setConn();
  setThird(true);
  util::meas_dist_chip_out(this,mean,variance);
  setThird(false);
  conn2.brkConn();
  util::add_prop(result,out2Id,0.0,mean,variance);

	conn.brkConn();
	setEnable ( false );
  cutil::restore_conns(calib);
  this->update(codes_self);
}
