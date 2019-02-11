// tile level test harness

class TestTile {

  public:

    TestTile (
      Fabric::Chip::Tile & tile
    ) :
      tile ( tile ),
      // design under test
      complexMultScaling ( tile ),
      // testing outputs
      // s(ac-bd) summing point
      mult_real_out ( complexMultScaling.mult_real_out ),
      // si(ad+bc) summing point
      mult_imag_out ( complexMultScaling.mult_imag_out ),
      // input generators
      conn0 ( tile.slices[0].dac->out0, tile.slices[2].tileOuts[0].in0 ),
      conn1 ( tile.slices[1].dac->out0, tile.slices[2].tileOuts[1].in0 ),
      conn2 ( tile.slices[2].dac->out0, tile.slices[2].tileOuts[2].in0 ),
      conn3 ( tile.slices[3].dac->out0, tile.slices[2].tileOuts[3].in0 ),

      conn4 ( tile.slices[2].tileOuts[0].out0, complexMultScaling.x_real_in ),
      conn5 ( tile.slices[2].tileOuts[1].out0, complexMultScaling.x_imag_in ),
      conn6 ( tile.slices[2].tileOuts[2].out0, complexMultScaling.y_real_in ),
      conn7 ( tile.slices[2].tileOuts[3].out0, complexMultScaling.y_imag_in )
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

    void setDynRangeXY (
      float dynRange, // s
      float x_real, // a
      float x_imag, // b
      float y_real, // c
      float y_imag  // d
    ) {
      //      Serial.print("complexMultScaling.setDynRange ");
      complexMultScaling.setDynRange ( dynRange );
      //      Serial.print("tile.slices[0].dac->setConstant ");
      tile.slices[0].dac->setConstant( x_real / dynRange );
      //      Serial.print("tile.slices[1].dac->setConstant ");
      tile.slices[1].dac->setConstant( x_imag / dynRange );
      //      Serial.print("tile.slices[2].dac->setConstant ");
      tile.slices[2].dac->setConstant( y_real / dynRange );
      //      Serial.println("tile.slices[3].dac->setConstant ");
      tile.slices[3].dac->setConstant( y_imag / dynRange );
    }

    Fabric::Chip::Tile & tile;
    ComplexMultScaling complexMultScaling;

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
