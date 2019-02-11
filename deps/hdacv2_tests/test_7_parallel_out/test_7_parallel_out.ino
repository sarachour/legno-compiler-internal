# define _DUE
//char HCDC_DEMO_BOARD = 2;  this line needs to be included when the manual is v8
# include <HCDC_DEMO_API.h>

void setup() {
  Fabric fab = Fabric ();
  fab.calibrate();

  Fabric::Chip::Tile::Slice::Adc * myADC = fab.chips[0].tiles[0].slices[0].adc; 
  Fabric::Chip::Tile::Slice::TileInOut * myTI = &fab.chips[0].tiles[0].slices[1].tileInps[0]; 

  pinMode(26, OUTPUT);  // this two lines
  digitalWrite(26, HIGH);  // are not needed when the manual is v8
  Fabric::Chip::Connection( fab.chips[0].tiles[3].slices[2].chipInput-> out0, myTI-> in0 ).setConn();
  Fabric::Chip::Connection( myTI-> out0, myADC->in0 ).setConn();

  myADC -> setParallelOut(true);
     
  fab.cfgCommit();
  for (unsigned short rep = 0; rep < 1000; rep++){            // get 1000 values of the parallel output
          unsigned char myPout = fab.chips[0].readParallel();
          Serial.println(myPout); 
          delay(1);                                           // time between each value is at least 1ms
      }
}

void loop() {}
