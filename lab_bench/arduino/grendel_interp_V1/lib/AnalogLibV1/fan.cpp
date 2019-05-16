#include "AnalogLib.h"
#include "assert.h"
#include "calib_util.h"
void Fabric::Chip::Tile::Slice::Fanout::setEnable (
	bool enable
) {
	/*record*/
	m_codes.enable = enable;
	/*set*/
	setParam0();
	setParam1();
	setParam2();
	setParam3();
}

void Fabric::Chip::Tile::Slice::Fanout::setRange (
	range_t range// 20uA mode
	// 20uA mode results in more ideal behavior in terms of phase shift but consumes more power
	// this setting should match the unit that gives the input to the fanout
) {
  assert(range != RANGE_LOW);
  m_codes.range[in0Id] = range;
  m_codes.range[out0Id] = range;
  m_codes.range[out1Id] = range;
  m_codes.range[out2Id] = range;
	setParam0();
	setParam1();
	setParam2();
	setParam3();
}

void Fabric::Chip::Tile::Slice::Fanout::FanoutOut::setInv (
	bool inverse // whether output is negated
) {
  Fabric::Chip::Tile::Slice::Fanout* fan = this->parentFu;
	fan->m_codes.inv[ifcId] = inverse;
	parentFu->setParam1 ();
	parentFu->setParam2 ();
	parentFu->setParam3 ();
}

void Fabric::Chip::Tile::Slice::Fanout::setThird (
	bool third // whether third output is on
) {
	m_codes.third = third;
	setParam3();
}

void Fabric::Chip::Tile::Slice::Fanout::defaults (){
  m_codes.range[in0Id] = RANGE_MED;
  m_codes.range[in1Id] = RANGE_UNKNOWN;
  m_codes.range[out0Id] = RANGE_MED;
  m_codes.range[out1Id] = RANGE_MED;
  m_codes.range[out2Id] = RANGE_MED;
  m_codes.inv[in0Id] = false;
  m_codes.inv[in1Id] = false;
  m_codes.inv[out0Id] = false;
  m_codes.inv[out1Id] = false;
  m_codes.inv[out2Id] = false;
  m_codes.port_cal[in0Id] = 0;
  m_codes.port_cal[in1Id] = 0;
  m_codes.port_cal[out0Id] = 31;
  m_codes.port_cal[out1Id] = 31;
  m_codes.port_cal[out2Id] = 31;
  m_codes.enable = false;
  m_codes.third = false;
  m_codes.nmos = 0;
  m_codes.pmos = 3;
	setAnaIrefNmos();
	setAnaIrefPmos();
}

Fabric::Chip::Tile::Slice::Fanout::Fanout (
	Chip::Tile::Slice * parentSlice,
	unit unitId
) :
	FunctionUnit(parentSlice, unitId)
{
	in0 = new GenericInterface (this, in0Id);
	tally_dyn_mem <GenericInterface> ("GenericInterface");
	out0 = new FanoutOut (this, out0Id);
	tally_dyn_mem <FanoutOut> ("FanoutOut");
	out1 = new FanoutOut (this, out1Id);
	tally_dyn_mem <FanoutOut> ("FanoutOut");
	out2 = new FanoutOut (this, out2Id);
	tally_dyn_mem <FanoutOut> ("FanoutOut");
  defaults();
}

/*Set enable, range*/
void Fabric::Chip::Tile::Slice::Fanout::setParam0 () const {
	unsigned char cfgTile = 0;
  bool is_hi = (m_codes.range[in0Id] == RANGE_HIGH);
	cfgTile += m_codes.enable ? 1<<7 : 0;
	cfgTile += is_hi ? 1<<5 : 0;
	setParamHelper (0, cfgTile);
}

/*Set calDac1, invert output 1*/
void Fabric::Chip::Tile::Slice::Fanout::setParam1 () const {
	unsigned char calDac1 = m_codes.port_cal[out0Id];
	if (calDac1<0||63<calDac1) error ("calDac1 out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += calDac1<<2;
	cfgTile += m_codes.inv[out0Id] ? 1<<1 : 0;
	setParamHelper (1, cfgTile);
}

/*Set calDac2, invert output 2*/
void Fabric::Chip::Tile::Slice::Fanout::setParam2 () const {
	unsigned char calDac2 = m_codes.port_cal[out1Id];
	if (calDac2<0||63<calDac2) error ("calDac2 out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += calDac2<<2;
	cfgTile += m_codes.inv[out1Id] ? 1<<1 : 0;
	setParamHelper (2, cfgTile);
}

/*Set calDac3, invert output 3, enable output 3*/
void Fabric::Chip::Tile::Slice::Fanout::setParam3 () const {
	unsigned char calDac3 = m_codes.port_cal[out2Id];
	if (calDac3<0||63<calDac3) error ("calDac3 out of bounds");
	unsigned char cfgTile = 0;
	cfgTile += calDac3<<2;
	cfgTile += m_codes.inv[out2Id] ? 1<<1 : 0;
	cfgTile += m_codes.third ? 1<<0 : 0;
	setParamHelper (3, cfgTile);
}

/*Helper function*/
void Fabric::Chip::Tile::Slice::Fanout::setParamHelper (
	unsigned char selLine,
	unsigned char cfgTile
) const {
	if (selLine<0||3<selLine) error ("selLine out of bounds");

	/*DETERMINE SEL_ROW*/
	unsigned char selRow;
	switch (parentSlice->sliceId) {
		case slice0: selRow = 2; break;
		case slice1: selRow = 3; break;
		case slice2: selRow = 4; break;
		case slice3: selRow = 5; break;
		default: error ("invalid slice. Only slices 0 through 3 have FANs"); break;
	}

	/*DETERMINE SEL_COL*/
	unsigned char selCol;
	switch (unitId) {
		case unitFanL: selCol = 0; break;
		case unitFanR: selCol = 1; break;
		default: error ("invalid unit. Only unitFanL and unitFanR are FANs"); break;
	}

	Vector vec = Vector (
		*this,
		selRow,
		selCol,
		selLine,
		endian (cfgTile)
	);

	parentSlice->parentTile->parentChip->cacheVec (
		vec
	);
}


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

	Connection conn = Connection (parentSlice->tileOuts[3].out0,
                                parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0);
	conn.setConn();

	// Serial.print("\nFanout interface calibration");
  Connection conn0 = Connection (out0, this->parentSlice->tileOuts[3].in0);
  conn0.setConn();
  float value = util::measure_chip_out(this);
  conn0.brkConn();
  util::add_prop(result,out0Id, 0.0, value);

  Connection conn1 = Connection (out1, this->parentSlice->tileOuts[3].in0);
  conn1.setConn();
  value = util::measure_chip_out(this);
  conn1.brkConn();
  util::add_prop(result,out1Id,0.0,value);

  Connection conn2 = Connection (out2, this->parentSlice->tileOuts[3].in0);
  conn1.setConn();
  setThird(true);
  value = util::measure_chip_out(this);
  setThird(false);
  conn2.brkConn();
  util::add_prop(result,out2Id,0.0,value);

	conn.brkConn();
	setEnable ( false );
  cutil::restore_conns(calib);
  this->update(codes_self);
}
bool Fabric::Chip::Tile::Slice::Fanout::calibrate (util::calib_result_t& result,
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

  bool new_search = true;
  bool calib_failed = true;
	while (new_search) {
    float errors[3];
    unsigned char codes[3];
    Connection conn0 = Connection (out0, this->parentSlice->tileOuts[3].in0);
    conn0.setConn();
    binsearch::find_bias(this,0.0,
                         m_codes.port_cal[out0Id],
                         errors[0],
                         MEAS_CHIP_OUTPUT);
    codes[0] = m_codes.port_cal[out0Id];
    conn0.brkConn();

    Connection conn1 = Connection (out1, this->parentSlice->tileOuts[3].in0);
    conn1.setConn();
    binsearch::find_bias(this,0.0,
                         m_codes.port_cal[out1Id],
                         errors[1],
                         MEAS_CHIP_OUTPUT);
    codes[1] = m_codes.port_cal[out1Id];
    conn1.brkConn();

    Connection conn2 = Connection (out2, this->parentSlice->tileOuts[3].in0);
    conn1.setConn();
    setThird(true);
    binsearch::find_bias(this,0.0,
                         m_codes.port_cal[out2Id],
                         errors[2],
                         MEAS_CHIP_OUTPUT);
    codes[2] = m_codes.port_cal[out2Id];
    setThird(false);
    conn2.brkConn();
    // update nmos for multiple stability statements
    binsearch::multi_test_stab_and_update_nmos(this,
                                               codes,
                                               errors,
                                               max_error,
                                               3,
                                               m_codes.nmos,
                                               new_search,
                                               calib_failed);
	}
	conn.brkConn();
	setEnable ( false );
  cutil::restore_conns(calib);
  codes_self.port_cal[out0Id] = m_codes.port_cal[out0Id];
  codes_self.port_cal[out1Id] = m_codes.port_cal[out1Id];
  codes_self.port_cal[out2Id] = m_codes.port_cal[out2Id];
  this->update(codes_self);
	return !calib_failed;
}
/*
void Fabric::Chip::Tile::Slice::Fanout::FanoutOut::findBias (
                                                             unsigned char & offsetCode,
                                                             bool& new_search,
                                                             bool& calib_failed
) {
	if (ifcId==out2Id) parentFanout->setThird(true);
	Connection conn = Connection ( this, parentFu->parentSlice->tileOuts[3].in0 );
	conn.setConn();

	findBiasHelper (offsetCode,parentFanout->m_codes.nmos,new_search,calib_failed);

	conn.brkConn();
	if (ifcId==out2Id) parentFanout->setThird(false);

}
*/

void Fabric::Chip::Tile::Slice::Fanout::setAnaIrefNmos () const {
	unsigned char selRow=0;
	unsigned char selCol;
	unsigned char selLine;
  binsearch::test_iref(m_codes.nmos);
	switch (unitId) {
		case unitFanL: switch (parentSlice->sliceId) {
			case slice0: selCol=0; selLine=0; break;
			case slice1: selCol=0; selLine=1; break;
			case slice2: selCol=1; selLine=0; break;
			case slice3: selCol=1; selLine=1; break;
			default: error ("FAN invalid slice"); break;
		} break;
		case unitFanR: switch (parentSlice->sliceId) {
			case slice0: selCol=1; selLine=2; break;
			case slice1: selCol=1; selLine=3; break;
			case slice2: selCol=2; selLine=0; break;
			case slice3: selCol=2; selLine=1; break;
			default: error ("FAN invalid slice"); break;
		} break;
		default: error ("FAN invalid unitId"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	switch (unitId) {
		case unitFanL: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00000111) + ((m_codes.nmos<<3) & 0b00111000); break;
			case slice1: cfgTile = (cfgTile & 0b00000111) + ((m_codes.nmos<<3) & 0b00111000); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			default: error ("FAN invalid slice"); break;
		} break;
		case unitFanR: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00000111) + ((m_codes.nmos<<3) & 0b00111000); break;
			case slice1: cfgTile = (cfgTile & 0b00000111) + ((m_codes.nmos<<3) & 0b00111000); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111); break;
			default: error ("FAN invalid slice"); break;
		} break;
		default: error ("FAN invalid unitId"); break;
	}

	Vector vec = Vector (
		*this,
		selRow,
		selCol,
		selLine,
		endian (cfgTile)
	);

	parentSlice->parentTile->parentChip->cacheVec (
		vec
	);
}

void Fabric::Chip::Tile::Slice::Fanout::setAnaIrefPmos () const {

	unsigned char selRow=0;
	unsigned char selCol;
	unsigned char selLine;
  binsearch::test_iref(m_codes.pmos);
	switch (unitId) {
		case unitFanL: switch (parentSlice->sliceId) {
			case slice0: selLine=3; break;
			case slice1: selLine=2; break;
			case slice2: selLine=1; break;
			case slice3: selLine=0; break;
			default: error ("FAN invalid slice"); break;
		} selCol=0; break;
		case unitFanR: switch (parentSlice->sliceId) {
			case slice0: selLine=1; break;
			case slice1: selLine=0; break;
			case slice2: selLine=3; break;
			case slice3: selLine=2; break;
			default: error ("FAN invalid slice"); break;
		} selCol=1; break;
		default: error ("FAN invalid unitId"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	switch (unitId) {
		case unitFanL: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos & 0b00000111); break;
			case slice1: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos & 0b00000111); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos & 0b00000111); break;
			default: error ("FAN invalid slice"); break;
		} break;
		case unitFanR: switch (parentSlice->sliceId) {
			case slice0: cfgTile = (cfgTile & 0b00000111) + ((m_codes.pmos<<3) & 0b00111000); break;
			case slice1: cfgTile = (cfgTile & 0b00000111) + ((m_codes.pmos<<3) & 0b00111000); break;
			case slice2: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos & 0b00000111); break;
			case slice3: cfgTile = (cfgTile & 0b00111000) + (m_codes.pmos & 0b00000111); break;
			default: error ("FAN invalid slice"); break;
		} break;
		default: error ("FAN invalid unitId"); break;
	}

	Vector vec = Vector (
		*this,
		selRow,
		selCol,
		selLine,
		endian (cfgTile)
	);

	parentSlice->parentTile->parentChip->cacheVec (
		vec
	);
}
