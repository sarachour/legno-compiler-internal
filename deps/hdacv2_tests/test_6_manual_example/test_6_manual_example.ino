# define _DUE
//char HCDC_DEMO_BOARD = 2;  this line needs to be included when the manual is v8
# include <HCDC_DEMO_API.h>

void setup() {
  Fabric fab = Fabric ();
  
  fab.calibrate(); 

  Fabric::Chip::Tile::Slice::Fanout * myFan0 = &fab.chips[0].tiles[0].slices[0].fans[1];
  Fabric::Chip::Tile::Slice::Fanout * myFan1 = &fab.chips[0].tiles[3].slices[0].fans[0];
  Fabric::Chip::Tile::Slice::Fanout * myFan2 = &fab.chips[0].tiles[3].slices[0].fans[1];

  Fabric::Chip::Tile::Slice::Multiplier * myVga0 = &fab.chips[0].tiles[0].slices[0].muls[0];
  Fabric::Chip::Tile::Slice::Multiplier * myVga1 = &fab.chips[0].tiles[0].slices[1].muls[0]; 
  Fabric::Chip::Tile::Slice::Multiplier * myVga2 = &fab.chips[0].tiles[3].slices[2].muls[0];   
  Fabric::Chip::Tile::Slice::Multiplier * myMul = &fab.chips[0].tiles[3].slices[0].muls[1];
  
  Fabric::Chip::Tile::Slice::Integrator * myInt0 = fab.chips[0].tiles[0].slices[0].integrator;
  Fabric::Chip::Tile::Slice::Integrator * myInt1 = fab.chips[0].tiles[3].slices[0].integrator;
  Fabric::Chip::Tile::Slice::Dac * myDAC = fab.chips[0].tiles[0].slices[0].dac; 
  Fabric::Chip::Tile::Slice::TileInOut * myTI0 = &fab.chips[0].tiles[0].slices[0].tileInps[0];
  Fabric::Chip::Tile::Slice::TileInOut * myTI1 = &fab.chips[0].tiles[0].slices[1].tileInps[0];
  Fabric::Chip::Tile::Slice::TileInOut * myTI2 = &fab.chips[0].tiles[3].slices[0].tileInps[0];
  Fabric::Chip::Tile::Slice::TileInOut * myTO0 = &fab.chips[0].tiles[0].slices[0].tileOuts[0];
  Fabric::Chip::Tile::Slice::TileInOut * myTO1 = &fab.chips[0].tiles[3].slices[0].tileOuts[0];
  Fabric::Chip::Tile::Slice::TileInOut * myTO2 = &fab.chips[0].tiles[3].slices[1].tileOuts[0];
  Fabric::Chip::Tile::Slice::TileInOut * myTO3 = &fab.chips[0].tiles[3].slices[1].tileOuts[1];
  Fabric::Chip::Tile::Slice::TileInOut * myTO4 = &fab.chips[0].tiles[3].slices[2].tileOuts[1];
  
  myFan0 -> setEnable( true );
  myFan1 -> setEnable( true );
  myFan2 -> setEnable( true );
  myMul  -> setEnable( true );
  myVga0 -> setEnable( true );
  myVga1 -> setEnable( true );
  myVga2 -> setEnable( true );
  myInt0 -> setEnable( true );
  myInt1 -> setEnable( true );
  myDAC  -> setEnable( true );

  myVga0 -> setVga( true );
  myVga0 -> setGainCode( 191 ); // 0.4922
  myVga1 -> setVga( true );
  myVga1 -> setGainCode( 51 );  // -0.60156
  myVga2 -> setVga( true );
  myVga2 -> setGainCode( 83 );  // -0.3516
  
  myInt0 -> setInitial( 128 );  // 0
  myInt1 -> setInitial( 91 );   // -1.012

  myDAC->setConstantCode ( 183 ); // 1.4844
  
  myFan2-> out1 -> setInv ( true );  

  Fabric::Chip::Connection ( myVga0->out0, myInt0->in0 ).setConn();
  Fabric::Chip::Connection ( myInt0->out0, myFan0->in0 ).setConn();
  Fabric::Chip::Connection ( myFan0->out0, myTO0->in0 ).setConn();
  Fabric::Chip::Connection ( myFan0->out1, myVga1->in0 ).setConn();
  Fabric::Chip::Connection ( myVga1->out0, myVga0->in0 ).setConn();
  Fabric::Chip::Connection ( myTO0->out0, myTI2->in0 ).setConn();
  Fabric::Chip::Connection ( myTI2->out0, myInt1->in0 ).setConn();
  Fabric::Chip::Connection ( myInt1->out0, myFan1->in0 ).setConn();
  
  Fabric::Chip::Connection ( myFan1->out0, myMul->in0 ).setConn();
  Fabric::Chip::Connection ( myFan1->out1, myMul->in1 ).setConn();
  Fabric::Chip::Connection ( myFan1->out2, myFan2->in0 ).setConn();
  
  Fabric::Chip::Connection ( myMul->out0, myVga2->in0 ).setConn();
  Fabric::Chip::Connection ( myVga2->out0, myTO2->in0 ).setConn(); 
  
  Fabric::Chip::Connection ( myFan2->out1, myTO1->in0 ).setConn();  // -x
  Fabric::Chip::Connection ( myTO1->out0, myTI0->in0 ).setConn();
  Fabric::Chip::Connection ( myTO2->out0, myTI1->in0 ).setConn();
  Fabric::Chip::Connection ( myTI0->out0, myVga0->in0 ).setConn();
  Fabric::Chip::Connection ( myTI1->out0, myVga0->in0 ).setConn();
  Fabric::Chip::Connection ( myDAC->out0, myVga0->in0 ).setConn();

// output x(t) to board analog output: anaOut1
  Fabric::Chip::Connection ( myFan2->out2, myTO3->in0 ).setConn();  
  Fabric::Chip::Connection ( myTO3->out0, fab.chips[0].tiles[3].slices[3].chipOutput->in0 ).setConn();

  
  fab.cfgCommit();   
  while (true) {
      fab.execStart();
      delay(2);
      fab.execStop();
  }
 }


void loop() { }
