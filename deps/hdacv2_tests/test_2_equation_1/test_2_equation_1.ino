#define _DUE
#include <HCDC_DEMO_API.h>

char HCDC_DEMO_BOARD = 4;

void setup() {

  Fabric fabric = Fabric();
  SerialUSB.println("initialized");
  SerialUSB.println("calibrate");
  fabric.calibrate();
  SerialUSB.println("calibrated");
  unsigned char chipIndx = 0;

  while (true) {

        unsigned char tileIndx = 0;
        unsigned char sliceIndx = 0;
        SerialUSB.println("setup");
        Fabric::Chip::Tile::Slice::Integrator * int0 = fabric.chips[chipIndx].tiles[tileIndx].slices[sliceIndx].integrator;
        Fabric::Chip::Tile::Slice::Integrator * int1 = fabric.chips[chipIndx].tiles[tileIndx + 1].slices[sliceIndx].integrator;
        Fabric::Chip::Tile::Slice::Fanout * fan0 = &fabric.chips[chipIndx].tiles[tileIndx].slices[sliceIndx].fans[1];
        Fabric::Chip::Tile::Slice::Fanout * fan1 = &fabric.chips[chipIndx].tiles[tileIndx + 1].slices[sliceIndx].fans[1];
        Fabric::Chip::Tile::Slice::Multiplier * mul0 = &fabric.chips[chipIndx].tiles[tileIndx].slices[sliceIndx].muls[1];
        Fabric::Chip::Tile::Slice::Multiplier * mul1 = &fabric.chips[chipIndx].tiles[tileIndx + 1].slices[sliceIndx].muls[1];
        Fabric::Chip::Tile::Slice::TileInOut * tileout = &fabric.chips[chipIndx].tiles[tileIndx + 1].slices[sliceIndx].tileOuts[1];
        Fabric::Chip::Tile::Slice::TileInOut * outChan0 = &fabric.chips[chipIndx].tiles[tileIndx].slices[sliceIndx].tileOuts[0];
        Fabric::Chip::Tile::Slice::TileInOut * inpChan0 = &fabric.chips[chipIndx].tiles[tileIndx + 1].slices[sliceIndx].tileInps[0];
        Fabric::Chip::Tile::Slice::TileInOut * outChan1 = &fabric.chips[chipIndx].tiles[tileIndx + 1].slices[sliceIndx].tileOuts[0];
        Fabric::Chip::Tile::Slice::TileInOut * inpChan1 = &fabric.chips[chipIndx].tiles[tileIndx].slices[sliceIndx].tileInps[0];
 
        /*EQUATION 1*/
        int0->setEnable(true);
        int0->setInitialCode(102);
        fan0->setEnable(true);
        Fabric::Chip::Connection conn0 = Fabric::Chip::Connection ( int0->out0, fan0->in0 );
        conn0.setConn();

        int1->setEnable(true);
        int1->setInitialCode(0);
        Fabric::Chip::Connection conn10 = Fabric::Chip::Connection ( fan0->out0, outChan0->in0 );
        Fabric::Chip::Connection conn11 = Fabric::Chip::Connection ( outChan0->out0, inpChan0->in0 );
        Fabric::Chip::Connection conn12 = Fabric::Chip::Connection ( inpChan0->out0, int1->in0 );
        conn10.setConn();
        conn11.setConn();
        conn12.setConn();

        fan1->setEnable(true);
        Fabric::Chip::Connection conn2 = Fabric::Chip::Connection ( int1->out0, fan1->in0 );
        conn2.setConn();

        Fabric::Chip::Connection conn3 = Fabric::Chip::Connection ( fan1->out0, tileout->in0 );
        conn3.setConn();

        mul0->setEnable(true);
        mul0->setVga(true);
        mul0->setGainCode(102);
        Fabric::Chip::Connection conn4 = Fabric::Chip::Connection ( fan0->out1, mul0->in0 );
        conn4.setConn();

        Fabric::Chip::Connection conn5 = Fabric::Chip::Connection ( mul0->out0, int0->in0 );
        conn5.setConn();

        mul1->setEnable(true);
        mul1->setVga(true);
        mul1->setGainCode(26);
        Fabric::Chip::Connection conn6 = Fabric::Chip::Connection ( fan1->out1, mul1->in0 );
        conn6.setConn();

        Fabric::Chip::Connection conn70 = Fabric::Chip::Connection ( mul1->out0, outChan1->in0 );
        Fabric::Chip::Connection conn71 = Fabric::Chip::Connection ( outChan1->out0, inpChan1->in0 );
        Fabric::Chip::Connection conn72 = Fabric::Chip::Connection ( inpChan1->out0, int0->in0 );
        conn70.setConn();
        conn71.setConn();
        conn72.setConn();

        Fabric::Chip::Connection conn8 = Fabric::Chip::Connection ( tileout->out0, fabric.chips[chipIndx].tiles[3].slices[2].chipOutput->in0  );
        conn8.setConn();

        fabric.cfgCommit();

        SerialUSB.println("execute");
        for (unsigned short rep = 0; rep < 1024; rep++) {
          fabric.execStart();
          delay(2);
          fabric.execStop();
          fabric.cfgStart();
          fabric.cfgStop();
        }

        SerialUSB.println("teardown");
        int0->setEnable(false);
        int1->setEnable(false);
        fan0->setEnable(false);
        fan1->setEnable(false);
        mul0->setEnable(false);
        mul1->setEnable(false);
        conn0.brkConn();
        conn10.brkConn();
        conn11.brkConn();
        conn12.brkConn();
        conn2.brkConn();
        conn3.brkConn();
        conn4.brkConn();
        conn5.brkConn();
        conn6.brkConn();
        conn70.brkConn();
        conn71.brkConn();
        conn72.brkConn();
        conn8.brkConn();

  }
}

void loop () {}
