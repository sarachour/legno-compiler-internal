// tile level test harness

class TestTile {

  public:

    TestTile (
      Fabric::Chip::Tile & tile
    ) :
      tile ( tile ),
      // design under test
      complexMult ( tile ),
      // testing outputs
      mult_real_out ( tile.slices[0].tileOuts[0].out0 ),
      mult_imag_out ( tile.slices[0].tileOuts[1].out0 ),
      // input generators
      conn0 ( tile.slices[0].dac->out0, complexMult.x_real_in ),
      conn1 ( tile.slices[1].dac->out0, complexMult.x_imag_in ),
      conn2 ( tile.slices[2].dac->out0, complexMult.y_real_in ),
      conn3 ( tile.slices[3].dac->out0, complexMult.y_imag_in ),
      // s(ac-bd) summing point
      conn4 ( complexMult.mult_real_out_0, tile.slices[0].tileOuts[0].in0 ),
      conn5 ( complexMult.mult_real_out_1, tile.slices[0].tileOuts[0].in0 ),
      // si(ad+bc) summing point
      conn6 ( complexMult.mult_imag_out_0, tile.slices[0].tileOuts[1].in0 ),
      conn7 ( complexMult.mult_imag_out_1, tile.slices[0].tileOuts[1].in0 )
    {
      conn0.setConn();
      conn1.setConn();
      conn2.setConn();
      conn3.setConn();
      conn4.setConn();
      conn5.setConn();
      conn6.setConn();
      conn7.setConn();
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

    void setXY (
      float x_real, // a
      float x_imag, // b
      float y_real, // c
      float y_imag  // d
    ) {
      //      Serial.print("tile.slices[0].dac->setConstant ");
      tile.slices[0].dac->setConstant( x_real );
      //      Serial.print("tile.slices[1].dac->setConstant ");
      tile.slices[1].dac->setConstant( x_imag );
      //      Serial.print("tile.slices[2].dac->setConstant ");
      tile.slices[2].dac->setConstant( y_real );
      //      Serial.println("tile.slices[3].dac->setConstant ");
      tile.slices[3].dac->setConstant( y_imag );
    }

    Fabric::Chip::Tile & tile;
    ComplexMult complexMult;

    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * mult_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * mult_imag_out;

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
