#include "AnalogLib.h"
#include "assert.h"
#include "calib_util.h"

bool Fabric::Chip::Tile::Slice::Fanout::calibrate (profile_t& result,
                                                   float max_error) {

  fanout_code_t codes_self = m_codes;
  cutil::calibrate_t calib;
  cutil::initialize(calib);
  cutil::buffer_fanout_conns(calib,this);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_chipout_conns(calib,
                              parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);

  m_codes.nmos = 0;
	setEnable ( true );
	Connection conn = Connection (parentSlice->tileOuts[3].out0,
                                parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0);
	conn.setConn();

	// Serial.print("\nFanout interface calibration");

  bool found_code = false;
  m_codes.nmos = 0;
  setAnaIrefNmos();
  fanout_code_t best_code = m_codes;
	while (m_codes.nmos <=7 && !found_code) {
    bool calib_failed = true;
    float error;
    bool succ = true;
    Connection conn0 = Connection (out0,
                                   this->parentSlice->tileOuts[3].in0);
    conn0.setConn();
    binsearch::find_bias(this,0.0,
                         m_codes.port_cal[out0Id],
                         error,
                         MEAS_CHIP_OUTPUT);
    binsearch::test_stab(m_codes.port_cal[out0Id],
                        error, max_error,
                        calib_failed);
    succ &= !calib_failed;
    conn0.brkConn();

    Connection conn1 = Connection (out1,
                                   this->parentSlice->tileOuts[3].in0);
    conn1.setConn();
    binsearch::find_bias(this,0.0,
                         m_codes.port_cal[out1Id],
                         error,
                         MEAS_CHIP_OUTPUT);
    binsearch::test_stab(m_codes.port_cal[out1Id],
                         error, max_error,
                         calib_failed);
    succ &= !calib_failed;
    conn1.brkConn();

    Connection conn2 = Connection (out2,
                                   this->parentSlice->tileOuts[3].in0);
    conn2.setConn();
    setThird(true);
    binsearch::find_bias(this,0.0,
                         m_codes.port_cal[out2Id],
                         error,
                         MEAS_CHIP_OUTPUT);
    binsearch::test_stab(m_codes.port_cal[out2Id],
                         error, max_error,
                         calib_failed);
    succ &= !calib_failed;
    setThird(false);
    conn2.brkConn();
    // update nmos for multiple stability statements
    if(succ){
      found_code = true;
      best_code = m_codes;
    }
    m_codes.nmos += 1;
    if(m_codes.nmos <= 7){
      setAnaIrefNmos();
    }
	}
	conn.brkConn();
  cutil::restore_conns(calib);
	setEnable ( false );
  codes_self.nmos = best_code.nmos;
  codes_self.port_cal[out0Id] = best_code.port_cal[out0Id];
  codes_self.port_cal[out1Id] = best_code.port_cal[out1Id];
  codes_self.port_cal[out2Id] = best_code.port_cal[out2Id];
  this->update(codes_self);
	return found_code && calib.success;
}
