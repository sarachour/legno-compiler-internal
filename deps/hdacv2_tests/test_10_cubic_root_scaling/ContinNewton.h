class ContinNewton {

  public:
    ContinNewton (
      Fabric::Chip::Tile & tile,
      float probRange,
      float initial_real, // initial condition for integrator
      float initial_imag // initial condition for integrator
    ) :
      tile ( tile ),

      newtonQuotientReal ( tile.slices[0].tileInps[0].in0 ),
      x_jaco_real_out ( tile.slices[0].tileOuts[0].out0 ),
      x_func_real_out ( tile.slices[0].tileOuts[2].out0 ),
      x_chip_real_out ( tile.slices[1].tileOuts[0].out0 ),

      newtonQuotientImag ( tile.slices[0].tileInps[1].in0 ),
      x_jaco_imag_out ( tile.slices[0].tileOuts[1].out0 ),
      x_func_imag_out ( tile.slices[0].tileOuts[3].out0 ),
      x_chip_imag_out ( tile.slices[1].tileOuts[1].out0 ),

      conn0 ( tile.slices[0].tileInps[0].out0, tile.slices[0].integrator->in0 ),
      conn1 ( tile.slices[0].integrator->out0, tile.slices[0].fans[0].in0 ),
      conn2 ( tile.slices[0].fans[0].out0, tile.slices[0].tileOuts[0].in0 ),
      conn3 ( tile.slices[0].fans[0].out1, tile.slices[0].tileOuts[2].in0 ),
      conn4 ( tile.slices[0].fans[0].out2, tile.slices[1].tileOuts[0].in0 ),

      conn5 ( tile.slices[0].tileInps[1].out0, tile.slices[1].integrator->in0 ),
      conn6 ( tile.slices[1].integrator->out0, tile.slices[0].fans[1].in0 ),
      conn7 ( tile.slices[0].fans[1].out0, tile.slices[0].tileOuts[1].in0 ),
      conn8 ( tile.slices[0].fans[1].out1, tile.slices[0].tileOuts[3].in0 ),
      conn9 ( tile.slices[0].fans[1].out2, tile.slices[1].tileOuts[1].in0 )

    {
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
      tile.slices[0].fans[0].setHiRange(true);
      tile.slices[0].fans[1].setHiRange(true);
//      tile.slices[0].integrator->in0->setRange(false, true);
//      tile.slices[1].integrator->in0->setRange(false, true);
//      tile.slices[0].integrator->out0->setRange(false, true);
//      tile.slices[1].integrator->out0->setRange(false, true);
      tile.slices[0].integrator->setInitial(initial_real / probRange);
      tile.slices[1].integrator->setInitial(initial_imag / probRange);
    };

    ~ContinNewton () {
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
    };

    void setInitialReal (
      float probRange,
      float initial_real
    ) {
      tile.slices[0].integrator->setInitial(initial_real / probRange);
    }

    void setInitialImag (
      float probRange,
      float initial_imag
    ) {
      tile.slices[1].integrator->setInitial(initial_imag / probRange);
    }

    Fabric::Chip::Tile & tile;

    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * newtonQuotientReal;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_jaco_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_func_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_chip_real_out;

    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * newtonQuotientImag;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_jaco_imag_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_func_imag_out;
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
};
