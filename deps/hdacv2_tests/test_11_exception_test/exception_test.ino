#define _DUE
#include <HCDC_DEMO_API.h>

char HCDC_DEMO_BOARD = 1;
Fabric * fabric;

void setup() {

  fabric = new Fabric();
  fabric->calibrate();

  for (unsigned char chipIndex = 0; chipIndex < 2; chipIndex++) {
    for (unsigned char tileIndex = 0; tileIndex < 4; tileIndex++) {
      for (unsigned char sliceIndex = 0; sliceIndex < 4; sliceIndex++) {

        Fabric::Chip::Tile::Slice * currSlice = &fabric->chips[chipIndex].tiles[tileIndex].slices[sliceIndex];

        currSlice->dac->setConstant(-0.5);
        Fabric::Chip::Connection conn0 = Fabric::Chip::Connection ( currSlice->dac->out0, currSlice->integrator->in0 );
        currSlice->integrator->out0->setRange(false,true);
        currSlice->integrator->setInitial(5.0);
//        Fabric::Chip::Connection conn1 = Fabric::Chip::Connection ( currSlice->integrator->out0, currSlice->adc->in0 );
        conn0.setConn();
//        conn1.setConn();
        fabric->cfgCommit();

        fabric->execStart();
        for (unsigned char chipIdx = 0; chipIdx < 2; chipIdx++) {
          for (unsigned char tileIdx = 0; tileIdx < 4; tileIdx++) {
            for (unsigned char sliceIdx = 0; sliceIdx < 4; sliceIdx++) {
              Serial.print("chipIndex ");
              Serial.print(chipIndex);
              Serial.print(" tileIndex ");
              Serial.print(tileIndex);
              Serial.print(" sliceIndex ");
              Serial.print(sliceIndex);
              Serial.print(" chipIdx ");
              Serial.print(chipIdx);
              Serial.print(" tileIdx ");
              Serial.print(tileIdx);
              Serial.print(" sliceIdx ");
              Serial.print(sliceIdx);
//              Serial.print(" adc ");
//              Serial.println(fabric->chips[chipIdx].tiles[tileIdx].slices[sliceIdx].adc->getException());
              Serial.print(" integrator ");
              Serial.println(fabric->chips[chipIdx].tiles[tileIdx].slices[sliceIdx].integrator->getException());
            }
          }
        }
        fabric->execStop();
        conn0.brkConn();
//        conn1.brkConn();

      }
    }
  }
}

void loop () {}
