#define _DUE
#include <HCDC_DEMO_API.h>

void setup() {

  Fabric fabric = Fabric();

  while (true) {
    Serial.println("cycle");
    for (unsigned char tileIndx = 0; tileIndx < 4; tileIndx++) {
      for (unsigned char sliceIndx = 0; sliceIndx < 4; sliceIndx += 2) {
        fabric.chips[0].tiles[tileIndx].setParallelIn(true);
        fabric.chips[0].tiles[tileIndx].slices[sliceIndx].lut->setSource ( true, false, false );
        byte data[256];
        for (int dataIndx = 0; dataIndx < 256; dataIndx++) {
          data[dataIndx] = random(256);
          fabric.chips[0].tiles[tileIndx].slices[sliceIndx].lut->setLut (dataIndx, data[dataIndx]);
        }
        fabric.chips[0].tiles[tileIndx].slices[sliceIndx].lut->setParallelOut( true );
        fabric.cfgCommit();

        /*randomly check values*/
        byte randAddr = 255;
        for (unsigned int checkIndx = 0; checkIndx < 1024; checkIndx++) {
          fabric.chips[0].writeParallel(randAddr);
          unsigned char output = fabric.chips[0].readParallel();
          if (data[randAddr] != output) {
            Serial.print("chipIndx=0 ");
            Serial.print("tileIndx="); Serial.print(tileIndx); 
            Serial.print(" sliceIndx="); Serial.print(sliceIndx);
            Serial.print(" addr=");
            Serial.print(randAddr);
            Serial.print(" ");
            Serial.print(data[randAddr]);
            Serial.print(" != ");
            Serial.println(output);
          }
          randAddr = random(256);
        }
      }
    }

    for (unsigned char tileIndx = 0; tileIndx < 4; tileIndx++) {
      for (unsigned char sliceIndx = 0; sliceIndx < 4; sliceIndx += 2) {
        fabric.chips[1].tiles[tileIndx].setParallelIn(true);
        fabric.chips[1].tiles[tileIndx].slices[sliceIndx].lut->setSource ( true, false, false );
        byte data[256];
        for (int dataIndx = 0; dataIndx < 256; dataIndx++) {
          data[dataIndx] = random(256);
          fabric.chips[1].tiles[tileIndx].slices[sliceIndx].lut->setLut (dataIndx, data[dataIndx]);
        }
        fabric.chips[1].tiles[tileIndx].slices[sliceIndx].lut->setParallelOut( true );
        fabric.cfgCommit();

        /*randomly check values*/
        byte randAddr = 255;
        for (unsigned int checkIndx = 0; checkIndx < 1024; checkIndx++) {
          fabric.chips[1].writeParallel(randAddr);
          unsigned char output = fabric.chips[1].readParallel();
          if (data[randAddr] != output) {
            Serial.print("chipIndx=1 ");
            Serial.print(" tileIndx="); Serial.print(tileIndx); 
            Serial.print(" sliceIndx="); Serial.print(sliceIndx);
            Serial.print("addr=");
            Serial.print(randAddr);
            Serial.print(" ");
            Serial.print(data[randAddr]);
            Serial.print(" != ");
            Serial.println(output);
          }
          randAddr = random(256);
        }
      }
    }
  }
}

void loop(){}
