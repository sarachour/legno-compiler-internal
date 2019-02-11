// 3(x^2)
// 3(a+bi)^2
// 3(a+bi)(a+bi)
// 3(a^2-b^2+2abi)
// 3(a^2-b^2)+6abi

class Jacobian {

  public:
    Jacobian (
      Fabric::Chip::Tile & tile
    ) :
      tile ( tile ),

      complexSquare ( tile ),
      x_real_in ( complexSquare.x_real_in ), // a
      x_imag_in ( complexSquare.x_imag_in ), // b
      jacob_real_out ( tile.slices[2].tileOuts[2].out0 ),
      jacob_imag_out ( tile.slices[2].tileOuts[3].out0 ),

      // 3(a^2-b^2)
      conn0 ( complexSquare.square_real_out, tile.slices[2].tileInps[2].in0 ),
      conn1 ( tile.slices[2].tileInps[2].out0, tile.slices[1].fans[0].in0 ),
      conn2 ( tile.slices[1].fans[0].out0, tile.slices[2].tileOuts[2].in0 ),
      conn3 ( tile.slices[1].fans[0].out1, tile.slices[2].tileOuts[2].in0 ),
      conn4 ( tile.slices[1].fans[0].out2, tile.slices[2].tileOuts[2].in0 ),

      // 6abi
      conn5 ( complexSquare.square_imag_out, tile.slices[2].tileInps[3].in0 ),
      conn6 ( tile.slices[2].tileInps[3].out0, tile.slices[1].fans[1].in0 ),
      conn7 ( tile.slices[1].fans[1].out0, tile.slices[2].tileOuts[3].in0 ),
      conn8 ( tile.slices[1].fans[1].out1, tile.slices[2].tileOuts[3].in0 ),
      conn9 ( tile.slices[1].fans[1].out2, tile.slices[2].tileOuts[3].in0 )

    {
      tile.slices[1].fans[0].setHiRange(true);
      tile.slices[1].fans[1].setHiRange(true);
      tile.slices[1].fans[1].out0->setInv(true);
      tile.slices[1].fans[1].out1->setInv(true);
      tile.slices[1].fans[1].out2->setInv(true);
      conn0.setConn();
      conn1.setConn();
      conn2.setConn();
      conn3.setConn();
      conn4.setConn();
      conn5.setConn();
      conn6.setConn();
      conn7.setConn();
      conn8.setConn();
      conn9.setConn();
    }

    ~Jacobian () {
      conn0.brkConn();
      conn1.brkConn();
      conn2.brkConn();
      conn3.brkConn();
      conn4.brkConn();
      conn5.brkConn();
      conn6.brkConn();
      conn7.brkConn();
      conn8.brkConn();
      conn9.brkConn();
    }

    Fabric::Chip::Tile & tile;
    ComplexSquare complexSquare;

    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_real_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_imag_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * jacob_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * jacob_imag_out;

  private:
    Fabric::Chip::Connection conn0;
    Fabric::Chip::Connection conn1;
    Fabric::Chip::Connection conn2;
    Fabric::Chip::Connection conn3;
    Fabric::Chip::Connection conn4;
    Fabric::Chip::Connection conn5;
    Fabric::Chip::Connection conn6;
    Fabric::Chip::Connection conn7;
    Fabric::Chip::Connection conn8;
    Fabric::Chip::Connection conn9;
};
