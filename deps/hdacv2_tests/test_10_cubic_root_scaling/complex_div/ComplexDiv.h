// n/q
// (a+bi)/(c+di)
// (a+bi)(c-di)/(c+di)(c-di)
// (ac+bd+i(bc-ad))/(cc+dd)
// (ac+bd)/(cc+dd) + i(bc-ad)/(cc+dd)

class ComplexDiv {

  public:
    ComplexDiv (
      Fabric::Chip::Tile & tile,
      float initial_real, // initial condition for integrator
      float initial_imag // initial condition for integrator
    ) :
      tile ( tile ),
      complexMult ( tile ),

      numer_real_in ( tile.slices[2].tileInps[0].in0 ),
      numer_imag_in ( tile.slices[2].tileInps[1].in0 ),
      denom_real_in ( tile.slices[2].tileInps[2].in0 ),
      denom_imag_in ( tile.slices[2].tileInps[3].in0 ),

      quoti_real_out ( tile.slices[2].tileOuts[0].out0 ),
      quoti_imag_out ( tile.slices[2].tileOuts[1].out0 ),

      conn00 ( tile.slices[2].tileInps[0].out0, complexMult.x_real_in ),
      conn01 ( tile.slices[2].tileInps[1].out0, complexMult.x_imag_in ),
      conn02 ( tile.slices[2].tileInps[2].out0, complexMult.y_real_in ),
      conn03 ( tile.slices[2].tileInps[3].out0, complexMult.y_imag_in ),

      conn04 ( complexMult.mult_real_out_0, tile.slices[2].integrator->in0 ),
      conn05 ( complexMult.mult_real_out_1, tile.slices[2].integrator->in0 ),
      conn06 ( complexMult.mult_imag_out_0, tile.slices[3].integrator->in0 ),
      conn07 ( complexMult.mult_imag_out_1, tile.slices[3].integrator->in0 ),

      // make cc + dd
      // cc
      conn08 ( complexMult.y_real_out, tile.slices[2].fans[0].in0 ),
      conn09 ( tile.slices[2].fans[0].out0, tile.slices[2].muls[0].in0 ),
      conn10 ( tile.slices[2].fans[0].out1, tile.slices[2].muls[0].in1 ),
      // dd
      conn11 ( complexMult.y_imag_out, tile.slices[2].fans[1].in0 ),
      conn12 ( tile.slices[2].fans[1].out0, tile.slices[2].muls[1].in0 ),
      conn13 ( tile.slices[2].fans[1].out1, tile.slices[2].muls[1].in1 ),
      // cc+dd
      conn14 ( tile.slices[2].muls[0].out0, tile.slices[3].tileOuts[0].in0 ),
      conn15 ( tile.slices[2].muls[1].out0, tile.slices[3].tileOuts[0].in0 ),
      conn16 ( tile.slices[3].tileInps[0].out0, tile.slices[3].muls[0].in0 ),
      conn17 ( tile.slices[3].tileInps[1].out0, tile.slices[3].muls[1].in0 ),

      conn18 ( tile.slices[2].integrator->out0, tile.slices[3].fans[0].in0 ),
      conn19 ( tile.slices[3].integrator->out0, tile.slices[3].fans[1].in0 ),
      conn20 ( tile.slices[3].fans[0].out0, tile.slices[3].muls[0].in1 ),
      conn21 ( tile.slices[3].fans[1].out0, tile.slices[3].muls[1].in1 ),
      conn22 ( tile.slices[3].fans[0].out1, tile.slices[2].tileOuts[0].in0 ),
      conn23 ( tile.slices[3].fans[1].out1, tile.slices[2].tileOuts[1].in0 ),

      conn24 ( tile.slices[3].muls[0].out0, tile.slices[2].integrator->in0 ),
      conn25 ( tile.slices[3].muls[1].out0, tile.slices[3].integrator->in0 )

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
      conn13.setConn();
      conn14.setConn();
      conn15.setConn();
      conn16.setConn();
      conn17.setConn();
      conn18.setConn();
      conn19.setConn();
      conn20.setConn();
      conn21.setConn();
      conn22.setConn();
      conn23.setConn();
      conn24.setConn();
      conn25.setConn();

      tile.slices[2].fans[0].setHiRange(true);
      tile.slices[2].fans[1].setHiRange(true);
      tile.slices[3].fans[0].setHiRange(true);
      tile.slices[3].fans[1].setHiRange(true);

//      tile.slices[3].muls[0].in0->setRange(false, true);
//      tile.slices[3].muls[1].in0->setRange(false, true);
//      tile.slices[3].muls[0].out0->setRange(false, true);
//      tile.slices[3].muls[1].out0->setRange(false, true);

      tile.slices[2].integrator->in0->setRange(false, true);
      tile.slices[3].integrator->in0->setRange(false, true);
      tile.slices[2].integrator->out0->setRange(false, true);
      tile.slices[3].integrator->out0->setRange(false, true);
      tile.slices[2].integrator->setInitial(initial_real);
      tile.slices[3].integrator->setInitial(initial_imag);
      tile.slices[2].integrator->out0->setInv(true);
      tile.slices[3].integrator->out0->setInv(true);

    };

    ~ComplexDiv () {

      tile.slices[2].integrator->setEnable(false);
      tile.slices[3].integrator->setEnable(false);
      tile.slices[2].integrator->out0->setInv(false);
      tile.slices[3].integrator->out0->setInv(false);

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
      conn13.brkConn();
      conn14.brkConn();
      conn15.brkConn();
      conn16.brkConn();
      conn17.brkConn();
      conn18.brkConn();
      conn19.brkConn();
      conn20.brkConn();
      conn21.brkConn();
      conn22.brkConn();
      conn23.brkConn();
      conn24.brkConn();
      conn25.brkConn();

    };

    Fabric::Chip::Tile & tile;
    ComplexMult complexMult;

    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * numer_real_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * numer_imag_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * denom_real_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * denom_imag_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * quoti_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * quoti_imag_out;

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
    Fabric::Chip::Connection conn13;
    Fabric::Chip::Connection conn14;
    Fabric::Chip::Connection conn15;
    Fabric::Chip::Connection conn16;
    Fabric::Chip::Connection conn17;
    Fabric::Chip::Connection conn18;
    Fabric::Chip::Connection conn19;
    Fabric::Chip::Connection conn20;
    Fabric::Chip::Connection conn21;
    Fabric::Chip::Connection conn22;
    Fabric::Chip::Connection conn23;
    Fabric::Chip::Connection conn24;
    Fabric::Chip::Connection conn25;
};
