#define _DUE
#include <HCDC_DEMO_API.h>

unsigned char HCDC_DEMO_BOARD = 6;

void setup() {

  Fabric fabric = Fabric();

  while (true) {
    for (unsigned char tileIndx = 0; tileIndx < 4; tileIndx++) {
      for (unsigned char sliceIndx = 0; sliceIndx < 4; sliceIndx += 2) {
        Fabric::Chip::Tile::Slice::Dac * DAC_A = fabric.chips[0].tiles[tileIndx].slices[sliceIndx].dac;
        Fabric::Chip::Tile::Slice::ChipAdc * ADC_A = fabric.chips[0].tiles[tileIndx].slices[2].adc;
        Fabric::Chip::Tile::Slice * SLICE = &fabric.chips[0].tiles[tileIndx].slices[sliceIndx];
        Fabric::Chip::Tile::Slice::LookupTable * LUT = fabric.chips[0].tiles[tileIndx].slices[sliceIndx].lut;

        Serial.print("chipIndx=0 ");
        Serial.print("tileIndx="); Serial.print(tileIndx); 
        Serial.print(" sliceIndx="); Serial.println(sliceIndx);
        SLICE->calibrate();
        Serial.println("calibrated");
        DAC_A->setEnable ( true );
        DAC_A->setSource (false,true,  false, false );
        ADC_A->setEnable ( true );
        fabric.chips[0].tiles[tileIndx].setParallelIn(true);
        Fabric::Chip::Connection ( DAC_A->out0, ADC_A->in0).setConn();
        // second analog to digital converter
        fabric.chips[0].tiles[tileIndx].slices[sliceIndx].lut->setSource ( false, false, true );
        byte data[256];
        for (int dataIndx = 0; dataIndx < 256; dataIndx++) {
          data[dataIndx] = dataIndx;
          LUT->setLut (dataIndx, data[dataIndx]);
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

        Fabric::Chip::Connection ( DAC_A->out0, ADC_A->in0).brkConn();
        DAC_A->setEnable ( false );
        ADC_A->setEnable ( false );
        fabric.chips[0].tiles[tileIndx].setParallelIn(false);
        delay(10000);
      }
    }

  }
}

void loop(){}
