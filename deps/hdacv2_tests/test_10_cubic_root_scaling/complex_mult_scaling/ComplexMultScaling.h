/*
  xy
  =(a+bi)(c+di)
  =ac-bd + i(ad+bc)

  we are using variable dynamic range of s
  for example, analog fullscale represents s=2.0
  then the multiplication 1.0*1.0=1.0 will be done in analog as
  1.0/s * 1.0/s => 1,0/s^2 * s
  note the values are scaled back up by s to make multiplication valid
  this is identical to numerical scaling done in fixed-point multiplication

  so in this module we output s(ac-bd) + si(ad+bc)
*/

class ComplexMultScaling {

  public:
    ComplexMultScaling (
      Fabric::Chip::Tile & tile
    ) :
      tile ( tile ),

      // inputs
      x_real_in ( tile.slices[0].tileInps[0].in0 ), // a
      x_imag_in ( tile.slices[0].tileInps[1].in0 ), // bi
      y_real_in ( tile.slices[0].tileInps[2].in0 ), // c
      y_imag_in ( tile.slices[0].tileInps[3].in0 ), // di

      // duplicates of input if neeeded
      x_real_out ( tile.slices[0].tileOuts[2].out0 ), // a
      x_imag_out ( tile.slices[0].tileOuts[3].out0 ), // bi

      conn00 ( tile.slices[0].tileInps[0].out0, tile.slices[0].fans[0].in0 ), // a
      conn01 ( tile.slices[0].tileInps[1].out0, tile.slices[1].fans[0].in0 ), // bi
      conn02 ( tile.slices[0].tileInps[2].out0, tile.slices[2].fans[0].in0 ), // c
      conn03 ( tile.slices[0].tileInps[3].out0, tile.slices[3].fans[0].in0 ), // di

      conn10 ( tile.slices[0].fans[0].out2, tile.slices[0].tileOuts[2].in0 ), // a
      conn11 ( tile.slices[1].fans[0].out2, tile.slices[0].tileOuts[3].in0 ), // bi

      // ac
      conn20 ( tile.slices[0].fans[0].out0, tile.slices[0].muls[0].in0 ), // a
      conn21 ( tile.slices[2].fans[0].out0, tile.slices[0].muls[0].in1 ), // c
      conn22 ( tile.slices[0].muls[0].out0, tile.slices[0].muls[1].in0 ), // sac
      conn23 ( tile.slices[0].muls[1].out0, tile.slices[0].tileOuts[0].in0 ), // sac

      // adi
      conn30 ( tile.slices[0].fans[0].out1, tile.slices[1].muls[0].in0 ), // a
      conn31 ( tile.slices[3].fans[0].out0, tile.slices[1].muls[0].in1 ), // di
      conn32 ( tile.slices[1].muls[0].out0, tile.slices[1].muls[1].in0 ), // sadi
      conn33 ( tile.slices[1].muls[1].out0, tile.slices[0].tileOuts[1].in0 ), // sadi

      // bic
      conn40 ( tile.slices[1].fans[0].out0, tile.slices[2].muls[0].in0 ), // bi
      conn41 ( tile.slices[2].fans[0].out1, tile.slices[2].muls[0].in1 ), // c
      conn42 ( tile.slices[2].muls[0].out0, tile.slices[2].muls[1].in0 ), // sbic
      conn43 ( tile.slices[2].muls[1].out0, tile.slices[0].tileOuts[1].in0 ), // sbic

      // bidi = -bd
      conn50 ( tile.slices[1].fans[0].out1, tile.slices[3].muls[0].in0 ), // bi
      conn51 ( tile.slices[3].fans[0].out1, tile.slices[3].muls[0].in1 ), // di
      conn52 ( tile.slices[3].muls[0].out0, tile.slices[3].muls[1].in0 ), // -sbd
      conn53 ( tile.slices[3].muls[1].out0, tile.slices[0].tileOuts[0].in0 ), // -sbd

      mult_real_out ( tile.slices[0].tileOuts[0].out0 ), // sac-sbd
      mult_imag_out ( tile.slices[0].tileOuts[1].out0 ) // sadi+sbic

    {
      conn00.setConn();
      conn01.setConn();
      conn02.setConn();
      conn03.setConn();

      conn10.setConn();
      conn11.setConn();

      conn20.setConn();
      conn21.setConn();
      conn22.setConn();
      conn23.setConn();

      conn30.setConn();
      conn31.setConn();
      conn32.setConn();
      conn33.setConn();

      conn40.setConn();
      conn41.setConn();
      conn42.setConn();
      conn43.setConn();

      conn50.setConn();
      conn51.setConn();
      conn52.setConn();
      conn53.setConn();

      tile.slices[1].fans[0].out1->setInv(true);

      tile.slices[0].fans[0].setHiRange(true);
      tile.slices[1].fans[0].setHiRange(true);
      tile.slices[2].fans[0].setHiRange(true);
      tile.slices[3].fans[0].setHiRange(true);

      setDynRange ( 0.0 );

    }

    ~ComplexMultScaling () {
      conn00.brkConn();
      conn01.brkConn();
      conn02.brkConn();
      conn03.brkConn();

      conn10.brkConn();
      conn11.brkConn();

      conn20.brkConn();
      conn21.brkConn();
      conn22.brkConn();
      conn23.brkConn();

      conn30.brkConn();
      conn31.brkConn();
      conn32.brkConn();
      conn33.brkConn();

      conn40.brkConn();
      conn41.brkConn();
      conn42.brkConn();
      conn43.brkConn();

      conn50.brkConn();
      conn51.brkConn();
      conn52.brkConn();
      conn53.brkConn();
    }

    void setDynRange (
      float dynRange
    ) {
      tile.slices[0].muls[1].setGain( dynRange );
      tile.slices[1].muls[1].setGain( dynRange );
      tile.slices[2].muls[1].setGain( dynRange );
      tile.slices[3].muls[1].setGain( dynRange );
    }

    Fabric::Chip::Tile & tile;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_real_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_imag_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * y_real_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * y_imag_in;

    // outputs
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_imag_out;

    Fabric::Chip::Connection conn00;
    Fabric::Chip::Connection conn01;
    Fabric::Chip::Connection conn02;
    Fabric::Chip::Connection conn03;

    Fabric::Chip::Connection conn10;
    Fabric::Chip::Connection conn11;

    Fabric::Chip::Connection conn20;
    Fabric::Chip::Connection conn21;
    Fabric::Chip::Connection conn22;
    Fabric::Chip::Connection conn23;

    Fabric::Chip::Connection conn30;
    Fabric::Chip::Connection conn31;
    Fabric::Chip::Connection conn32;
    Fabric::Chip::Connection conn33;

    Fabric::Chip::Connection conn40;
    Fabric::Chip::Connection conn41;
    Fabric::Chip::Connection conn42;
    Fabric::Chip::Connection conn43;

    Fabric::Chip::Connection conn50;
    Fabric::Chip::Connection conn51;
    Fabric::Chip::Connection conn52;
    Fabric::Chip::Connection conn53;

    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * mult_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * mult_imag_out;
};
