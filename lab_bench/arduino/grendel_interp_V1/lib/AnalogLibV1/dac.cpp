#include "AnalogLib.h"
#include <float.h>
#include "assert.h"
#include "calib_util.h"

void Fabric::Chip::Tile::Slice::Dac::update(dac_code_t codes){
  m_codes = codes;
  updateFu();
  setConstant(m_codes.const_val);
  setConstantCode(m_codes.const_code);
  setSource(m_codes.source);
  // restore exact state. The gain_val field clobbered a bit by setConstantCode
  m_codes = codes;
}

void Fabric::Chip::Tile::Slice::Dac::setEnable (
	bool enable
)
{
	m_codes.enable = enable;
	setParam0 ();
	setParam1 ();
}

void Fabric::Chip::Tile::Slice::Dac::DacOut::setInv (
	bool inverse // whether output is negated
) {
	Fabric::Chip::Tile::Slice::Dac* dac = this->parentFu;
  dac->m_codes.inv = inverse;
	parentFu->setParam0();
}

void Fabric::Chip::Tile::Slice::Dac::setRange (
	// default is 2uA mode
	range_t range // 20 uA mode
) {
  assert(range != RANGE_LOW);
  m_codes.range = range;
	setEnable (m_codes.enable);
}

void Fabric::Chip::Tile::Slice::Dac::setSource (dac_source_t src) {
	/*record*/
  m_codes.source = src;
  bool memory = (src == DSRC_MEM);
  bool external = (src == DSRC_EXTERN);
	switch (parentSlice->sliceId) {
		case slice0: parentSlice->parentTile->slice0DacOverride = memory; break;
		case slice1: parentSlice->parentTile->slice1DacOverride = memory; break;
		case slice2: parentSlice->parentTile->slice2DacOverride = memory; break;
		case slice3: parentSlice->parentTile->slice3DacOverride = memory; break;
	}
	if (external) {
		parentSlice->parentTile->setParallelIn ( external );
	}

	unsigned char cfgTile = 0b00000000;
	cfgTile += parentSlice->parentTile->slice0DacOverride ? 1<<7 : 0;
	cfgTile += parentSlice->parentTile->slice1DacOverride ? 1<<6 : 0;
	cfgTile += parentSlice->parentTile->slice2DacOverride ? 1<<5 : 0;
	cfgTile += parentSlice->parentTile->slice3DacOverride ? 1<<4 : 0;
	parentSlice->parentTile->controllerHelperTile ( 11, cfgTile );

	setEnable (
		m_codes.enable
	);
}

void Fabric::Chip::Tile::Slice::Dac::setConstantCode (
	unsigned char constantCode // fixed point representation of desired constant
	// 0 to 255 are valid
) {
  m_codes.const_code = constantCode;
  m_codes.const_val = (constantCode - 128)/128.0;
  setSource(DSRC_MEM);
	parentSlice->parentTile->parentChip->parentFabric->cfgCommit();
	unsigned char selLine = 0;
	switch (parentSlice->sliceId) {
		case slice0: selLine = 7; break;
		case slice1: selLine = 8; break;
		case slice2: selLine = 9; break;
		case slice3: selLine = 10; break;
	}
	unsigned char cfgTile = endian (constantCode);
	parentSlice->parentTile->controllerHelperTile ( selLine, cfgTile );
}

bool Fabric::Chip::Tile::Slice::Dac::setConstant(float constant){
  if(-1.0000001 < constant && constant< 127.0/128.0){
    setConstantCode(round(constant*128.0+128.0));
    m_codes.const_val = constant;
    return true;
  }
  else{
    return false;
  }
}

void Fabric::Chip::Tile::Slice::Dac::defaults(){
  m_codes.inv = false;
  m_codes.range = RANGE_MED;
  m_codes.pmos = 0;
  m_codes.nmos = 0;
  m_codes.gain_cal = 0;
  m_codes.const_code = 128;
  m_codes.const_val = 0.0;
  m_codes.enable = false;
	setAnaIrefNmos ();
}
Fabric::Chip::Tile::Slice::Dac::Dac (
	Chip::Tile::Slice * parentSlice
) :
	FunctionUnit(parentSlice, unitDac)
{

	out0 = new DacOut (this);
	tally_dyn_mem <DacOut> ("DacOut");
  defaults();
}

/*Set enable, invert, range, clock select*/
void Fabric::Chip::Tile::Slice::Dac::setParam0 () const {
	unsigned char cfgTile = 0;
  bool external = (m_codes.source == DSRC_EXTERN or m_codes.source == DSRC_MEM);
  bool lut0 = (m_codes.source == DSRC_LUT0);
  bool is_hiRange = (m_codes.range == RANGE_HIGH);
  //bool is_inverse = (m_codes.inv);
  bool is_inverse = !(m_codes.inv);
	cfgTile += m_codes.enable ? 1<<7 : 0;
	cfgTile += (is_inverse) ? 1<<6 : 0;
	cfgTile += (is_hiRange ? dacHi : dacMid) ? 1<<5 : 0;
	cfgTile += (external) ? extDac : ( lut0 ? lutL : lutR )<<0;
	setParamHelper (0, cfgTile);
}

/*Set calDac, input select*/
void Fabric::Chip::Tile::Slice::Dac::setParam1 () const {
	unsigned char calDac =  m_codes.gain_cal;
	if (calDac<0||63<calDac) error ("calDac out of bounds");
	unsigned char cfgTile = 0;
  bool external = (m_codes.source == DSRC_EXTERN or m_codes.source == DSRC_MEM);
  bool lut0 = (m_codes.source == DSRC_LUT0);
	cfgTile += calDac<<2;
  cfgTile += (external) ? extDac : ( lut0 ? lutL : lutR )<<0;
	setParamHelper (1, cfgTile);
}

/*Helper function*/
void Fabric::Chip::Tile::Slice::Dac::setParamHelper (
	unsigned char selLine,
	unsigned char cfgTile
) const {
	if (selLine<0||1<selLine) error ("selLine out of bounds");

	/*DETERMINE SEL_COL*/
	unsigned char selCol;
	switch (parentSlice->sliceId) {
		case slice0: selCol = 6; break;
		case slice1: selCol = 3; break;
		case slice2: selCol = 7; break;
		case slice3: selCol = 4; break;
		default: error ("DAC invalid slice"); break;
	}

	Chip::Vector vec = Vector (
		*this,
		6,
		selCol,
		selLine,
		endian (cfgTile)
	);

	parentSlice->parentTile->parentChip->cacheVec (
		vec
	);
}

bool Fabric::Chip::Tile::Slice::Dac::calibrate (const float max_error)
{
  return true;
}

bool Fabric::Chip::Tile::Slice::Dac::calibrateTarget (const float max_error)
{
  //setConstantCode(round(constant*128.0+128.0));
  if(!m_codes.enable){
    print_log("DAC not enabled");
    return true;
  }
  if(m_codes.source != DSRC_MEM){
    print_log("DAC must have memory as source.");
    return false;
  }
  float constant = m_codes.const_val;
  bool hiRange = (m_codes.range == RANGE_HIGH);

  cutil::calibrate_t calib;
  cutil::initialize(calib);

  mult_code_t user_aux= parentSlice->muls[1].m_codes;
  dac_code_t codes_self = m_codes;
  update(m_codes);

  cutil::buffer_mult_conns(calib,&parentSlice->muls[1]);
  cutil::buffer_tileout_conns(calib,&parentSlice->tileOuts[3]);
  cutil::buffer_dac_conns(calib,this);
  cutil::buffer_chipout_conns(calib,parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput);
  cutil::break_conns(calib);
  // conn0
	Connection mult_to_aux = Connection ( out0, parentSlice->muls[1].in0 );
  //conn1
	Connection aux_to_tile = Connection ( parentSlice->muls[1].out0,
                                         parentSlice->tileOuts[3].in0 );

  // conn2
	Connection mult_to_tile = Connection ( out0, parentSlice->tileOuts[3].in0 );
  // conn3
	Connection tile_to_chip = Connection ( parentSlice->tileOuts[3].out0,
                                         parentSlice->parentTile->parentChip->tiles[3].slices[2].chipOutput->in0 );

  mult_code_t mult_0p1;
	if (hiRange) {
    // feed dac output into scaling down multiplier input
		mult_to_aux.setConn();
		aux_to_tile.setConn();
    mult_0p1 = make_h2m_mult(calib, &parentSlice->muls[1]);
    // feed output of scaledown multiplier to tile output.
	} else {
    // feed dac output into tile output
		mult_to_tile.setConn();
	}
	tile_to_chip.setConn();

	// Serial.println("Dac gain calibration");
	// Serial.flush();
  sprintf(FMTBUF, "this gain: %f %d %d", m_codes.const_val,
          m_codes.const_code,
          m_codes.range);
  print_log(FMTBUF);
  bool succ = false;
  // if we're trying to
  int code = m_codes.const_code;
  int delta = 0;
  // move further away from the selected code
  while(!succ){
    // if we've jumped back and forth a few times,
    // choose the more fruitful direction to shift constants
    // and move in that direction.
    // flip back and forth between negative and positive displacements
    float error = 0.0;
    if(!calib.success){
      break;
    }
    if(code + delta > 255
       || code + delta < 0){
      break;
    }
    setConstantCode(code + delta);
    succ = binsearch::find_bias_and_nmos(
                                         this,
                                         constant,
                                         max_error,
                                         m_codes.gain_cal,
                                         m_codes.nmos,
                                         error,
                                         MEAS_CHIP_OUTPUT);
    sprintf(FMTBUF,"const code=%d target=%f meas=%f",
            code+delta,
            constant,
            constant+error);
    print_debug(FMTBUF);
    // if we haven't succeeded, adjust the code.
    if(!succ){
      // if the magnitude of the measured value is less than we expected
      if(fabs(constant+error) < fabs(constant)){
        // increase the magnitude of the value
        delta += (constant < 0 ? -1 : 1);
      }
      else{
        // decrease the magnitude of the value
        delta += (constant < 0 ? 1 : -1);
      }
    }
  }
  if (hiRange) {
    // feed dac output into scaling down multiplier input
		mult_to_aux.brkConn();
		aux_to_tile.brkConn();
    parentSlice->muls[1].update(user_aux);
    // feed output of scaledown multiplier to tile output.
	} else {
    // feed dac output into tile output
		mult_to_tile.brkConn();
	}
	tile_to_chip.brkConn();

  cutil::restore_conns(calib);
  codes_self.nmos = m_codes.nmos;
  codes_self.gain_cal = m_codes.gain_cal;
  codes_self.const_code = code+delta;
  sprintf(FMTBUF,"const code=%d",codes_self.const_code);
  print_debug(FMTBUF);
  update(codes_self);
	return succ && (calib.success);
}

void Fabric::Chip::Tile::Slice::Dac::setAnaIrefNmos () const {
	unsigned char selRow;
	unsigned char selCol=2;
	unsigned char selLine;
  binsearch::test_iref(m_codes.nmos);
	switch (parentSlice->sliceId) {
		case slice0: selRow=0; selLine=3; break;
		case slice1: selRow=1; selLine=0; break;
		case slice2: selRow=0; selLine=2; break;
		case slice3: selRow=1; selLine=1; break;
		default: error ("DAC invalid slice"); break;
	}
	unsigned char cfgTile = endian(parentSlice->parentTile->parentChip->cfgBuf[parentSlice->parentTile->tileRowId][parentSlice->parentTile->tileColId][selRow][selCol][selLine]);
	cfgTile = (cfgTile & 0b00111000) + (m_codes.nmos & 0b00000111);

	Chip::Vector vec = Vector (
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
