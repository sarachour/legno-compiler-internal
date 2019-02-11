class NewtonChip {

  public:
    NewtonChip (
      Fabric::Chip & chip,
      float probRange,
      float bias_real,
      float bias_imag,
      float initial_real,
      float initial_imag
    ) :

      conti ( chip.tiles[3], probRange, initial_real, initial_imag ),
      funct ( chip.tiles[2], chip.tiles[1], probRange, bias_real, bias_imag ),
      jacob ( chip.tiles[3] ),
      quoti ( chip.tiles[0], 0.0, 0.0 ),

      x_chip_real_out ( conti.x_chip_real_out ),
      x_chip_imag_out ( conti.x_chip_imag_out ),

      conn0 ( quoti.quoti_real_out, conti.newtonQuotientReal ),
      conn1 ( quoti.quoti_imag_out, conti.newtonQuotientImag ),
      conn2 ( conti.x_func_real_out, funct.x_real_in ),
      conn3 ( conti.x_func_imag_out, funct.x_imag_in ),
      conn4 ( conti.x_jaco_real_out, jacob.x_real_in ),
      conn5 ( conti.x_jaco_imag_out, jacob.x_imag_in ),
      conn6 ( jacob.jacob_real_out, quoti.denom_real_in ),
      conn7 ( jacob.jacob_imag_out, quoti.denom_imag_in ),
      conn8 ( funct.funct_real_out, quoti.numer_real_in ),
      conn9 ( funct.funct_imag_out, quoti.numer_imag_in ),

      conn10 ( chip.tiles[0].slices[3].tileOuts[0].out0, chip.tiles[3].slices[3].tileInps[0].in0 ),
      conn11 ( chip.tiles[3].slices[3].tileInps[0].out0, chip.tiles[3].slices[3].fans[1].in0 ),
      conn12 ( chip.tiles[3].slices[3].fans[1].out0, chip.tiles[3].slices[3].tileOuts[0].in0 ),
      conn13 ( chip.tiles[3].slices[3].fans[1].out1, chip.tiles[3].slices[3].tileOuts[1].in0 ),
      conn14 ( chip.tiles[3].slices[3].tileOuts[0].out0, chip.tiles[0].slices[3].tileInps[0].in0 ),
      conn15 ( chip.tiles[3].slices[3].tileOuts[1].out0, chip.tiles[0].slices[3].tileInps[1].in0 )
    {
      chip.tiles[3].slices[3].fans[1].setHiRange(true);
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

      conn10.setConn();
      conn11.setConn();
      conn12.setConn();
      conn13.setConn();
      conn14.setConn();
      conn15.setConn();
    }

    ~NewtonChip () {
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

      conn10.brkConn();
      conn11.brkConn();
      conn12.brkConn();
      conn13.brkConn();
      conn14.brkConn();
      conn15.brkConn();
    }

    void setBias (
      float probRange,
      float bias_real,
      float bias_imag
    ) {
      funct.setBias(probRange, bias_real, bias_imag);
    }

    void setInitialReal (
      float probRange,
      float initial_real
    ) {
      conti.setInitialReal(probRange, initial_real);
    }

    void setInitialImag (
      float probRange,
      float initial_imag
    ) {
      conti.setInitialImag(probRange, initial_imag);
    }

  public:
    ContinNewton conti;
    Function funct;
    Jacobian jacob;
    ComplexDiv quoti;

    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_chip_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_chip_imag_out;

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

    Fabric::Chip::Connection conn10;
    Fabric::Chip::Connection conn11;
    Fabric::Chip::Connection conn12;
    Fabric::Chip::Connection conn13;
    Fabric::Chip::Connection conn14;
    Fabric::Chip::Connection conn15;
};
