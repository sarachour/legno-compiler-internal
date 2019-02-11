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

class ComplexMult {

  public:
    ComplexMult (
      Fabric::Chip::Tile & tile
    ) :
      tile ( tile ),

      // inputs
      x_real_in ( tile.slices[0].fans[0].in0 ), // a
      x_imag_in ( tile.slices[0].fans[1].in0 ), // bi
      y_real_in ( tile.slices[1].fans[0].in0 ), // c
      y_imag_in ( tile.slices[1].fans[1].in0 ), // di

      // duplicates of input if neeeded
      x_real_out ( tile.slices[0].fans[0].out2 ), // a
      x_imag_out ( tile.slices[0].fans[1].out2 ), // bi
      y_real_out ( tile.slices[1].fans[0].out2 ), // c
      y_imag_out ( tile.slices[1].fans[1].out2 ), // di

      // ac
      conn00 ( tile.slices[0].fans[0].out0, tile.slices[0].muls[0].in0 ), // a
      conn01 ( tile.slices[1].fans[0].out0, tile.slices[0].muls[0].in1 ), // c
      mult_real_out_0 ( tile.slices[0].muls[0].out0 ), // ac

      // adi
      conn10 ( tile.slices[0].fans[0].out1, tile.slices[0].muls[1].in0 ), // a
      conn11 ( tile.slices[1].fans[1].out0, tile.slices[0].muls[1].in1 ), // di
      mult_imag_out_0 ( tile.slices[0].muls[1].out0 ), // adi

      // bic
      conn20 ( tile.slices[0].fans[1].out0, tile.slices[1].muls[0].in0 ), // bi
      conn21 ( tile.slices[1].fans[0].out1, tile.slices[1].muls[0].in1 ), // c
      mult_imag_out_1 ( tile.slices[1].muls[0].out0 ), // bic

      // bidi = -bd
      conn30 ( tile.slices[0].fans[1].out1, tile.slices[1].muls[1].in0 ), // bi
      conn31 ( tile.slices[1].fans[1].out1, tile.slices[1].muls[1].in1 ), // di
      mult_real_out_1 ( tile.slices[1].muls[1].out0 ) // -bd

    {
      tile.slices[0].fans[1].out1->setInv(true);

      tile.slices[0].fans[0].setHiRange(true);
      tile.slices[0].fans[1].setHiRange(true);
      tile.slices[1].fans[0].setHiRange(true);
      tile.slices[1].fans[1].setHiRange(true);

//      tile.slices[0].muls[0].in0->setRange(false, true);
//      tile.slices[0].muls[1].in0->setRange(false, true);
//      tile.slices[1].muls[0].in0->setRange(false, true);
//      tile.slices[1].muls[1].in0->setRange(false, true);
//
//      tile.slices[0].muls[0].out0->setRange(false, true);
//      tile.slices[0].muls[1].out0->setRange(false, true);
//      tile.slices[1].muls[0].out0->setRange(false, true);
//      tile.slices[1].muls[1].out0->setRange(false, true);

      conn00.setConn();
      conn01.setConn();
      conn10.setConn();
      conn11.setConn();
      conn20.setConn();
      conn21.setConn();
      conn30.setConn();
      conn31.setConn();
    }

    ~ComplexMult () {
      conn00.brkConn();
      conn01.brkConn();
      conn10.brkConn();
      conn11.brkConn();
      conn20.brkConn();
      conn21.brkConn();
      conn30.brkConn();
      conn31.brkConn();
    }

    Fabric::Chip::Tile & tile;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_real_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_imag_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * y_real_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * y_imag_in;

    // outputs
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_imag_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * y_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * y_imag_out;

    Fabric::Chip::Connection conn00;
    Fabric::Chip::Connection conn01;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * mult_real_out_0;

    Fabric::Chip::Connection conn10;
    Fabric::Chip::Connection conn11;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * mult_imag_out_0;

    Fabric::Chip::Connection conn20;
    Fabric::Chip::Connection conn21;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * mult_imag_out_1;

    Fabric::Chip::Connection conn30;
    Fabric::Chip::Connection conn31;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * mult_real_out_1;
};
