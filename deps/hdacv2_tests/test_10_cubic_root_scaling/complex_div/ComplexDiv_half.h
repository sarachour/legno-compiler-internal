// n/q
// (a+bi)/(c+di)
// (a+bi)(c-di)/(c+di)(c-di)
// (ac+bd+i(bc-ad))/(cc+dd)

class ComplexDiv {

  public:
    ComplexDiv (
      Fabric::Chip::Tile & tile,
      Fabric::Chip::Tile::Slice::Fanout & spareFan,
      unsigned char initial_real, // initial condition for integrator
      unsigned char initial_imag // initial condition for integrator
    ) :
      tile ( tile ),
      complexMult ( tile ),

      numer_real_in ( tile.slices[0].tileInps[0].in0 ),
      numer_imag_in ( tile.slices[0].tileInps[1].in0 ),
      denom_real_in ( tile.slices[0].tileInps[2].in0 ),
      denom_imag_in ( tile.slices[0].tileInps[3].in0 ),

      quoti_real_out ( tile.slices[0].tileOuts[0].out0 ),
      quoti_imag_out ( tile.slices[0].tileOuts[1].out0 ),

      conn00 ( tile.slices[0].tileInps[0].out0, tile.slices[0].integrator->in0 ),
      conn01 ( tile.slices[0].tileInps[1].out0, tile.slices[1].integrator->in0 ),
      conn02 ( tile.slices[0].tileInps[2].out0, complexMult.y_real_in ),
      conn03 ( tile.slices[0].tileInps[3].out0, complexMult.y_imag_in ),

      conn04 ( tile.slices[0].integrator->out0, complexMult.x_real_in ),
      conn05 ( complexMult.x_real_out, tile.slices[0].tileOuts[0].in0 ),
      conn06 ( tile.slices[1].integrator->out0, complexMult.x_imag_in ),
      conn07 ( complexMult.x_imag_out, tile.slices[0].tileOuts[1].in0 ),

      conn08 ( complexMult.mult_real_out_0, tile.slices[0].integrator->in0 ),
      conn09 ( complexMult.mult_real_out_1, tile.slices[0].integrator->in0 ),
      conn10 ( complexMult.mult_imag_out_0, tile.slices[1].integrator->in0 ),
      conn11 ( complexMult.mult_imag_out_1, tile.slices[1].integrator->in0 )

    {
      tile.slices[0].integrator->setInitial(initial_real);
      tile.slices[1].integrator->setInitial(initial_imag);
      tile.slices[0].integrator->out0->setInv(true);
      tile.slices[1].integrator->out0->setInv(true);

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

    };

    ~ComplexDiv () {
      tile.slices[0].integrator->setEnable(false);
      tile.slices[1].integrator->setEnable(false);
      tile.slices[0].integrator->out0->setInv(false);
      tile.slices[1].integrator->out0->setInv(false);

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
};
