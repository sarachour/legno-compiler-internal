// x^2
// (a+bi)^2
// (a+bi)(a+bi)
// (a^2-b^2+2abi)

class ComplexSquare {

  public:
    ComplexSquare (
      Fabric::Chip::Tile & tile
    ) :
      tile ( tile ),
      x_real_in ( tile.slices[2].tileInps[0].in0 ),
      x_imag_in ( tile.slices[2].tileInps[1].in0 ),
      square_real_out ( tile.slices[2].tileOuts[0].out0 ), // a^2-b^2
      square_imag_out ( tile.slices[2].tileOuts[1].out0 ), // 2abi
      // a
      conn00 ( tile.slices[2].tileInps[0].out0, tile.slices[2].fans[0].in0 ),
      // b
      conn01 ( tile.slices[2].tileInps[1].out0, tile.slices[2].fans[1].in0 ),
      // a^2
      conn02 ( tile.slices[2].fans[0].out0, tile.slices[2].muls[0].in0 ),
      conn03 ( tile.slices[2].fans[0].out1, tile.slices[2].muls[0].in1 ),
      // b^2
      conn04 ( tile.slices[2].fans[1].out0, tile.slices[2].muls[1].in0 ),
      conn05 ( tile.slices[2].fans[1].out1, tile.slices[2].muls[1].in1 ),
      // be sure to negate
      // for a^2-b^2 summing point
      // abi
      conn06 ( tile.slices[2].fans[0].out2, tile.slices[3].muls[0].in0 ),
      conn07 ( tile.slices[2].fans[1].out2, tile.slices[3].muls[0].in1 ),
      // 2abi
      conn08 ( tile.slices[3].muls[0].out0, tile.slices[3].fans[0].in0 ),

      conn09 ( tile.slices[2].muls[0].out0, tile.slices[2].tileOuts[0].in0 ), // a^2
      conn10 ( tile.slices[2].muls[1].out0, tile.slices[2].tileOuts[0].in0 ), // b^2
      conn11 ( tile.slices[3].fans[0].out0, tile.slices[2].tileOuts[1].in0 ), // abi
      conn12 ( tile.slices[3].fans[0].out1, tile.slices[2].tileOuts[1].in0 )  // abi

    {
      conn00.setConn();
      conn01.setConn();
      conn02.setConn();
      conn03.setConn();
      conn04.setConn();
      conn05.setConn();
      conn06.setConn();
      conn07.setConn();
      conn08.setConn();
      conn09.setConn();
      conn10.setConn();
      conn11.setConn();
      conn12.setConn();
      tile.slices[2].fans[1].out0->setInv(true);
      tile.slices[2].fans[0].setHiRange(true);
      tile.slices[2].fans[1].setHiRange(true);
      tile.slices[3].fans[0].setHiRange(true);
    }

    ~ComplexSquare () {
      tile.slices[2].fans[0].setEnable(false);
      tile.slices[2].fans[1].setEnable(false);
      tile.slices[3].fans[0].setEnable(false);
      tile.slices[2].muls[0].setEnable(false);
      tile.slices[2].muls[1].setEnable(false);
      tile.slices[3].muls[0].setEnable(false);
      conn00.brkConn();
      conn01.brkConn();
      conn02.brkConn();
      conn03.brkConn();
      conn04.brkConn();
      conn05.brkConn();
      conn06.brkConn();
      conn07.brkConn();
      conn08.brkConn();
      conn09.brkConn();
      conn10.brkConn();
      conn11.brkConn();
      conn12.brkConn();
    }

    Fabric::Chip::Tile & tile;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_real_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_imag_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * square_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * square_imag_out;

  private:
    Fabric::Chip::Connection conn00;
    Fabric::Chip::Connection conn01;
    Fabric::Chip::Connection conn02;
    Fabric::Chip::Connection conn03;
    Fabric::Chip::Connection conn04;
    Fabric::Chip::Connection conn05;
    Fabric::Chip::Connection conn06;
    Fabric::Chip::Connection conn07;
    Fabric::Chip::Connection conn08;
    Fabric::Chip::Connection conn09;
    Fabric::Chip::Connection conn10;
    Fabric::Chip::Connection conn11;
    Fabric::Chip::Connection conn12;
};
