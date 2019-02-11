// x^2
// (a+bi)^2
// (a+bi)(a+bi)
// a^2-b^2+2abi

class TestTile {

  public:
    TestTile (
      Fabric::Chip::Tile & tile
    ) :
      tile ( tile ),

      complexSquare ( tile ),
      // a^2-b^2
      sq_real_out ( complexSquare.square_real_out ),
      // abi
      sq_imag_out ( complexSquare.square_imag_out ),

      conn0 ( tile.slices[2].dac->out0, tile.slices[3].tileOuts[0].in0 ),
      conn1 ( tile.slices[3].tileOuts[0].out0, complexSquare.x_real_in ),
      conn2 ( tile.slices[3].dac->out0, tile.slices[3].tileOuts[1].in0 ),
      conn3 ( tile.slices[3].tileOuts[1].out0, complexSquare.x_imag_in )
    {
      conn0.setConn();
      conn1.setConn();
      conn2.setConn();
      conn3.setConn();
      tile.slices[2].dac->setConstant(0.0);
      tile.slices[3].dac->setConstant(0.0);
    }

    void setX (
      float x_real,
      float x_imag
    ) {
      tile.slices[2].dac->setConstant(x_real);
      tile.slices[3].dac->setConstant(x_imag);
    }

    ~TestTile () {
      conn0.brkConn();
      conn1.brkConn();
      conn2.brkConn();
      conn3.brkConn();
    }

    Fabric::Chip::Tile & tile;
    ComplexSquare complexSquare;

    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * sq_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * sq_imag_out;

  private:
    Fabric::Chip::Connection conn0;
    Fabric::Chip::Connection conn1;
    Fabric::Chip::Connection conn2;
    Fabric::Chip::Connection conn3;
};
