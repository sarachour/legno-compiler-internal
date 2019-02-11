// n/d
// (a+bi)/(c+di)

class TestTile {

  public:
    TestTile (
      Fabric::Chip::Tile & tile
    ) :

      tile ( tile ),

      complexDiv ( tile, 0.0, 0.0 ),
      quoti_real_out ( complexDiv.quoti_real_out ),
      quoti_imag_out ( complexDiv.quoti_imag_out ),

      conn0 ( tile.slices[0].dac->out0, tile.slices[0].tileOuts[0].in0 ),
      conn1 ( tile.slices[1].dac->out0, tile.slices[0].tileOuts[1].in0 ),
      conn2 ( tile.slices[2].dac->out0, tile.slices[0].tileOuts[2].in0 ),
      conn3 ( tile.slices[3].dac->out0, tile.slices[0].tileOuts[3].in0 ),

      conn4 ( tile.slices[0].tileOuts[0].out0, complexDiv.numer_real_in ),
      conn5 ( tile.slices[0].tileOuts[1].out0, complexDiv.numer_imag_in ),
      conn6 ( tile.slices[0].tileOuts[2].out0, complexDiv.denom_real_in ),
      conn7 ( tile.slices[0].tileOuts[3].out0, complexDiv.denom_imag_in )

    {
      conn0.setConn();
      conn1.setConn();
      conn2.setConn();
      conn3.setConn();
      conn4.setConn();
      conn5.setConn();
      conn6.setConn();
      conn7.setConn();
      tile.slices[3].dac->out0->setInv(true);
    }

    void setXY (
      float numer_real,
      float numer_imag,
      float denom_real,
      float denom_imag
    ) {
      tile.slices[0].dac->setConstant(numer_real);
      tile.slices[1].dac->setConstant(numer_imag);
      tile.slices[2].dac->setConstant(denom_real);
      tile.slices[3].dac->setConstant(denom_imag);
      tile.slices[3].dac->out0->setInv(true);
    }

    ~TestTile () {
      conn0.brkConn();
      conn1.brkConn();
      conn2.brkConn();
      conn3.brkConn();
      conn4.brkConn();
      conn5.brkConn();
      conn6.brkConn();
      conn7.brkConn();
    }

    Fabric::Chip::Tile & tile;
    ComplexDiv complexDiv;

    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * quoti_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * quoti_imag_out;

  private:
    Fabric::Chip::Connection conn0;
    Fabric::Chip::Connection conn1;
    Fabric::Chip::Connection conn2;
    Fabric::Chip::Connection conn3;
    Fabric::Chip::Connection conn4;
    Fabric::Chip::Connection conn5;
    Fabric::Chip::Connection conn6;
    Fabric::Chip::Connection conn7;
};
