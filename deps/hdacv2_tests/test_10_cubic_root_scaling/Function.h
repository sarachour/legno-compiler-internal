// x^3-1
// (a+bi)^3-1
// (a+bi)(a+bi)(a+bi)-1
// (aaa+aabi+abia+abibi+biaa+biabi+bibia+bibibi)-1
// (aaa+aabi+aabi-abb+aabi-abb-abb-bbbi)-1
// (aaa+3aabi-3abb-bbbi)-1

class Function {

  public:
    Function (
      Fabric::Chip::Tile & tileSquare,
      Fabric::Chip::Tile & tileMultSq,
      float probRange,
      float bias_real,
      float bias_imag
    ) :
      tileMultSq ( tileMultSq ),
      complexSquare ( tileSquare ),
      complexMultScaling ( tileMultSq ),

      x_real_in ( complexMultScaling.x_real_in ), // a
      x_imag_in ( complexMultScaling.x_imag_in ), // bi

      // a(a^2-b^2)
      // bi(2abi)
      funct_real_out ( complexMultScaling.mult_real_out ),

      // a(2abi)
      // bi(a^2-b^2)
      funct_imag_out ( complexMultScaling.mult_imag_out ),

      conn0 ( complexMultScaling.x_real_out, complexSquare.x_real_in ), // a
      conn1 ( complexMultScaling.x_imag_out, complexSquare.x_imag_in ), // bi

      // summing points
      conn2 ( complexSquare.square_real_out, complexMultScaling.y_real_in ), // a^2-b^2
      conn3 ( complexSquare.square_imag_out, complexMultScaling.y_imag_in ), // 2abi

      conn4 ( tileMultSq.slices[0].dac->out0, tileMultSq.slices[0].tileOuts[0].in0 ), // complexMultScale.mult_real_out
      conn5 ( tileMultSq.slices[1].dac->out0, tileMultSq.slices[0].tileOuts[1].in0 )  // complexMultScale.mult_imag_out )

    {
      conn0.setConn();
      conn1.setConn();
      conn2.setConn();
      conn3.setConn();
      conn4.setConn();
      conn5.setConn();
      complexMultScaling.setDynRange(probRange);
      tileMultSq.slices[0].dac->setConstant(bias_real / probRange / probRange);
      tileMultSq.slices[1].dac->setConstant(bias_imag / probRange / probRange);
    }

    void setBias (
      float probRange,
      float bias_real,
      float bias_imag
    ) {
      tileMultSq.slices[0].dac->setConstant(bias_real / probRange / probRange);
      tileMultSq.slices[1].dac->setConstant(bias_imag / probRange / probRange);
    }

    ~Function () {
      conn0.brkConn();
      conn1.brkConn();
      conn2.brkConn();
      conn3.brkConn();
      conn4.brkConn();
      conn5.brkConn();
    }

    Fabric::Chip::Tile & tileMultSq;
    ComplexSquare complexSquare;
    ComplexMultScaling complexMultScaling;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_real_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * x_imag_in;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * funct_real_out;
    Fabric::Chip::Tile::Slice::FunctionUnit::Interface * funct_imag_out;

  private:
    Fabric::Chip::Connection conn0;
    Fabric::Chip::Connection conn1;
    Fabric::Chip::Connection conn2;
    Fabric::Chip::Connection conn3;
    Fabric::Chip::Connection conn4;
    Fabric::Chip::Connection conn5;
};
