class TestChip {

  public:
    TestChip (
      Fabric::Chip::Tile & tile,
      Fabric::Chip::Tile & spareTile
    ) :
      testTile ( tile ),
      quoti_chip_real_out ( testTile.quoti_real_out ),
      quoti_chip_imag_out ( testTile.quoti_imag_out ),
      conn0 ( tile.slices[3].tileOuts[0].out0, spareTile.slices[0].tileInps[0].in0 ),
      conn1 ( spareTile.slices[0].tileInps[0].out0, spareTile.slices[0].fans[0].in0 ),
      conn2 ( spareTile.slices[0].fans[0].out0, spareTile.slices[0].tileOuts[0].in0 ),
      conn3 ( spareTile.slices[0].fans[0].out1, spareTile.slices[0].tileOuts[1].in0 ),
      conn4 ( spareTile.slices[0].tileOuts[0].out0, tile.slices[3].tileInps[0].in0 ),
      conn5 ( spareTile.slices[0].tileOuts[1].out0, tile.slices[3].tileInps[1].in0 )
    {
      conn0.setConn();
      conn1.setConn();
      conn2.setConn();
      conn3.setConn();
      conn4.setConn();
      conn5.setConn();
    }

    ~TestChip () {
      conn0.brkConn();
      conn1.brkConn();
      conn2.brkConn();
      conn3.brkConn();
      conn4.brkConn();
      conn5.brkConn();
    }

    void setXY (
      float numer_real,
      float numer_imag,
      float denom_real,
      float denom_imag
    ) {
      testTile.setXY ( numer_real, numer_imag, denom_real, denom_imag );
    }

  public:
    TestTile testTile;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * quoti_chip_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * quoti_chip_imag_out;

  private:
    Fabric::Chip::Connection conn0;
    Fabric::Chip::Connection conn1;
    Fabric::Chip::Connection conn2;
    Fabric::Chip::Connection conn3;
    Fabric::Chip::Connection conn4;
    Fabric::Chip::Connection conn5;

};
