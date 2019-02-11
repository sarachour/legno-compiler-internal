#define _DUE
#include <HCDC_DEMO_API.h>

char HCDC_DEMO_BOARD = 2;
float dynamic_range = 1.2;
Fabric * fabric;

void setup() {

  fabric = new Fabric();
  fabric->calibrate();

  for (unsigned char rep = 0; rep < 128; rep++) {
    for (unsigned char chipIndx = 0; chipIndx < 2; chipIndx++) {
      for (unsigned char tileIndx = 0; tileIndx < 4; tileIndx++) {
        for (unsigned char sliceIndx = 0; sliceIndx < 4; sliceIndx++) {

          Serial.print("chipIndx ");
          Serial.print(chipIndx);
          Serial.print(" tileIndx ");
          Serial.print(tileIndx);
          Serial.print(" sliceIndx ");
          Serial.print(sliceIndx);
          Serial.print(" ");

          Fabric::Chip::Tile::Slice * currSlice = &fabric->chips[chipIndx].tiles[tileIndx].slices[sliceIndx];

          float target = -dynamic_range + (float) (rand()) / (float)(RAND_MAX / (dynamic_range - (-dynamic_range)));
          Serial.print(target, 6);
          Serial.print('\t');
          Serial.print(target * target, 6);
          Serial.print('\t');

          currSlice->dac->setConstant(target);
          Fabric::Chip::Connection conn0 = Fabric::Chip::Connection ( currSlice->dac->out0, currSlice->fans[0].in0 );
          Fabric::Chip::Connection conn1 = Fabric::Chip::Connection ( currSlice->fans[0].out2, currSlice->fans[1].in0 );

          Fabric::Chip::Connection conn2 = Fabric::Chip::Connection ( currSlice->fans[0].out0, currSlice->muls[0].in0 );
          Fabric::Chip::Connection conn3 = Fabric::Chip::Connection ( currSlice->fans[0].out1, currSlice->muls[0].in1 );
          Fabric::Chip::Connection conn4 = Fabric::Chip::Connection ( currSlice->muls[0].out0, currSlice->tileOuts[0].in0 );
          Fabric::Chip::Connection conn5 = Fabric::Chip::Connection ( currSlice->tileOuts[0].out0,
                                             fabric->chips[chipIndx].tiles[3].slices[2].chipOutput->in0 );

          Fabric::Chip::Connection conn6 = Fabric::Chip::Connection ( currSlice->fans[1].out0, currSlice->muls[1].in0 );
          Fabric::Chip::Connection conn7 = Fabric::Chip::Connection ( currSlice->fans[1].out1, currSlice->muls[1].in1 );
          Fabric::Chip::Connection conn8 = Fabric::Chip::Connection ( currSlice->muls[1].out0, currSlice->tileOuts[1].in0 );
          Fabric::Chip::Connection conn9 = Fabric::Chip::Connection ( currSlice->tileOuts[1].out0,
                                             fabric->chips[chipIndx].tiles[3].slices[3].chipOutput->in0 );

          currSlice->fans[0].setHiRange(false);
//          currSlice->muls[0].in0->setRange (
//            false, // 0.2uA mode
//            false // 20 uA mode
//          );
//          currSlice->muls[0].in1->setRange (
//            false, // 0.2uA mode
//            true // 20 uA mode
//          );
//          currSlice->muls[0].out0->setRange (
//            false, // 0.2uA mode
//            true // 20 uA mode
//          );

          currSlice->fans[1].setHiRange(true);
//          currSlice->muls[1].in0->setRange (
//            false, // 0.2uA mode
//            true// 20 uA mode
//          );
//          currSlice->muls[1].in1->setRange (
//            false, // 0.2uA mode
//            false // 20 uA mode
//          );
//          currSlice->muls[1].out0->setRange (
//            false, // 0.2uA mode
//            true// 20 uA mode
//          );

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
          fabric->cfgCommit();

          Serial.print  (fabric->chips[chipIndx].tiles[3].slices[2].chipOutput->analogAvg(CAL_REPS) / FULL_SCALE, 6);
          Serial.print('\t');
          Serial.println(fabric->chips[chipIndx].tiles[3].slices[3].chipOutput->analogAvg(CAL_REPS) / FULL_SCALE, 6);

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

          currSlice->dac->setEnable(false);
          currSlice->fans[0].setEnable(false);
          currSlice->fans[1].setEnable(false);
          currSlice->muls[0].setEnable(false);
          currSlice->muls[1].setEnable(false);

        }
      }
    }
  }
}

void loop () {}
